import os
from typing import List
from dotenv import load_dotenv
from fastapi import HTTPException, status, APIRouter

import httpx

from routers.playbooks import create_playbook, update_playbook
from utils.utils import playbook_to_stix, stix_to_playbook
from models.stix import Envelope
from models.playbook import Playbook, PlaybookInDB
from database import db


load_dotenv()

router = APIRouter(
    prefix="/taxii",
    tags=["taxii"],
)

playbooks_collection = db.playbooks

taxii_url = os.getenv("TAXII_URI")
taxii_username = os.getenv("TAXII_USERNAME")
taxii_password = os.getenv("TAXII_PASSWORD")

if not taxii_url:
    raise ValueError("TAXII_URI environment variable not set")

if not taxii_username or not taxii_password:
    raise ValueError("TAXII_USERNAME and TAXII_PASSWORD environment variables must be set")

# Set up basic authentication
auth = httpx.BasicAuth(taxii_username, taxii_password)

# Set up headers with Accept media type and Content-Type
headers = {
    "Accept": "application/taxii+json;version=2.1",
    "Content-Type": "application/taxii+json;version=2.1"
}

taxii_api_root = "cacao-taxii"
taxii_collection_id = "365fed99-08fa-fdcd-a1b3-fb247eb41d01"

@router.get("/discovery", response_model=dict, status_code=status.HTTP_200_OK)
async def get_discovery():
    """
    Get information about the TAXII Server and any advertised API Roots.

    Returns:
    - A discovery object.
    """

    try:
        async with httpx.AsyncClient(auth=auth, headers=headers) as client:
            response = await client.get(f"{taxii_url}/taxii2/")
            response.raise_for_status()
            result = response.json()

            return result

    except httpx.HTTPError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
@router.get("/api-root", response_model=dict, status_code=status.HTTP_200_OK)
async def get_api_root():
    """
    Get information about the 'cacao-taxii' API Root.

    Returns:
    - An api-root object.
    """

    try:
        async with httpx.AsyncClient(auth=auth, headers=headers) as client:
            response = await client.get(f"{taxii_url}/{taxii_api_root}/")
            response.raise_for_status()
            result = response.json()

            return result

    except httpx.HTTPError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
@router.post("/share/playbook", response_model=dict, status_code=status.HTTP_200_OK)
async def share_playbook(playbook: Playbook):
    """
    Share a playbook to the TAXII Server.

    Arguments:
    - playbook: The playbook to be shared.

    Returns:
    - A status object.
    """
    
    if playbook.shared_versions:
        if playbook.modified in playbook.shared_versions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot share this version of the Playbook again."
            )

    try:
        stix_playbook = playbook_to_stix(playbook)

        result = await add_object({"objects": [stix_playbook]})

        # Update the playbook's 'shared_versions' property in the database
        playbooks_collection.update_one(
            {"id": playbook.id},
            {"$addToSet": {"shared_versions": playbook.modified}}
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
@router.post("/save/playbook/{id}", response_model=dict, status_code=status.HTTP_201_CREATED)
async def save_playbook(id: str):
    """
    Save a playbook from the TAXII Server.

    Arguments:
    - id: The id of the envelope object to get from the collection.

    Returns:
    - A dictionary containing the Mongo ID of the newly created playbook.
    """

    try:
        # Get envelope from TAXII server
        stix_playbook_envelope = await get_object(id)

        # Get STIX object from envelope
        stix_playbook = stix_playbook_envelope.get("objects")[0]

        # Convert STIX object to Playbook
        playbook = stix_to_playbook(stix_playbook)
        playbook.shared_versions.append(playbook.modified)

        existing_playbook = playbooks_collection.find_one({"id": playbook.id})

        if existing_playbook:
            # Update Playbook
            return await update_playbook(playbook)
        else:
            # Create Playbook
            return await create_playbook(playbook)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
@router.get("/playbooks/to-share", response_model=List[PlaybookInDB], status_code=status.HTTP_200_OK)
async def get_playbooks_to_share():
    """
    List playbooks that have not been shared to the TAXII server.

    Returns:
    - A list of playbooks that have not been shared to the TAXII server.
    """

    playbooks = list(playbooks_collection.find({"$or": [
        {"shared_versions": {"$exists": False}},
        {"$expr": {"$not": {"$in": ["$modified", "$shared_versions"]}}}
    ]}))
    for playbook in playbooks:
        playbook["_id"] = str(playbook["_id"])
    return playbooks

@router.get("/playbooks/to-save", response_model=List[Playbook], status_code=status.HTTP_200_OK)
async def get_playbooks_to_save():
    """
    List playbooks that have not been saved from the TAXII server.
    Returns:
    - A list of playbooks that have not been saved from the TAXII server.
    """

    # Get all STIX objects from TAXII server
    try:
        envelope_objects = await get_objects()
        playbooks_to_save = []

        for stix_playbook in envelope_objects["objects"]:
            playbook = stix_to_playbook(stix_playbook)

            existing_playbook = playbooks_collection.find_one({"id": playbook.id})

            if not existing_playbook:
                playbooks_to_save.append(playbook)
            else:
                if playbook.modified not in existing_playbook.get("shared_versions", []):
                    playbooks_to_save.append(playbook)

        return playbooks_to_save
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
@router.post("/objects", response_model=dict, status_code=status.HTTP_201_CREATED)
async def add_object(object: Envelope):
    """
    Add an envelope object to the cacao collection.

    Arguments:
    - object: The envelope object to be added to the collection.

    Returns:
    - A status object.
    """

    try:
        async with httpx.AsyncClient(auth=auth, headers=headers) as client:
            response = await client.post(
                f"{taxii_url}/{taxii_api_root}/collections/{taxii_collection_id}/objects/", 
                json=object
            )
            response.raise_for_status()
            result = response.json()

            return result

    except httpx.HTTPError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
@router.get("/objects", response_model=Envelope, status_code=status.HTTP_200_OK)
async def get_objects():
    """
    Get all objects from the cacao collection.

    Returns:
    - An envelope objects with all the objects.
    """

    try:
        async with httpx.AsyncClient(auth=auth, headers=headers) as client:
            response = await client.get(f"{taxii_url}/{taxii_api_root}/collections/{taxii_collection_id}/objects/")
            response.raise_for_status()
            result = response.json()

            return result

    except httpx.HTTPError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
@router.get("/objects/{id}", response_model=Envelope, status_code=status.HTTP_200_OK)
async def get_object(id: str):
    """
    Get an object from the cacao collection.

    Arguments:
    - id: The id of the envelope object to get from the collection.

    Returns:
    - An envelope object.
    """

    try:
        async with httpx.AsyncClient(auth=auth, headers=headers) as client:
            response = await client.get(f"{taxii_url}/{taxii_api_root}/collections/{taxii_collection_id}/objects/{id}/")
            response.raise_for_status()
            result = response.json()

            return result

    except httpx.HTTPError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
