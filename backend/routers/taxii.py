import os
from typing import List
from dotenv import load_dotenv
from fastapi import HTTPException, status, APIRouter

import httpx

from routers.playbooks import create_playbook, update_playbook
from utils.utils import playbook_to_stix, stix_to_playbook
from pipelines.sharings_pipeline import to_share_pipeline
from models.stix import Envelope, SharingInDB
from models.playbook import Playbook, PlaybookMeta, PlaybookWithStixId
from database import db


load_dotenv()

router = APIRouter(
    prefix="/taxii",
    tags=["taxii"],
)

playbooks_collection = db.playbooks
sharings_collection = db.sharings

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

   
    sharing_object = await sharings_collection.find_one({"playbook_id": playbook.id})

    if sharing_object:
        if sharing_object["shared_versions"]:
            if playbook.modified in sharing_object["shared_versions"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="You cannot share this version of the Playbook again."
                )

    try:
        stix_playbook = playbook_to_stix(playbook)

        result = await add_object({"objects": [stix_playbook]})

        # Update the playbook's 'shared_versions' property in the sharing collection
        await sharings_collection.update_one(
            {"playbook_id": playbook.id},
            {"$addToSet": {"shared_versions": playbook.modified}},
            upsert=True
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
@router.post("/save/playbook/{object_id}", response_model=dict, status_code=status.HTTP_201_CREATED)
async def save_playbook(object_id: str):
    """
    Save a playbook from the TAXII Server.

    Arguments:
    - object_id: The id of the envelope object to get from the collection.

    Returns:
    - A dictionary containing the Mongo ID of the newly created playbook.
    """

    try:
        # Get envelope from TAXII server
        stix_playbook_envelope = await get_object(object_id)

        # Get STIX object from envelope
        stix_playbook = stix_playbook_envelope.get("objects")[0]

        # Convert STIX object to Playbook
        playbook = stix_to_playbook(stix_playbook)
        existing_playbook = await playbooks_collection.find_one({"id": playbook.id})

        result = None
        if existing_playbook:
            # Update Playbook
            result = await update_playbook(playbook.id, playbook)
        else:
            # Create Playbook
            result = await create_playbook(playbook)

        await sharings_collection.update_one(
            {"playbook_id": playbook.id},
            {"$addToSet": {"shared_versions": playbook.modified}},
            upsert=True
        )

        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
@router.get("/playbooks/to-share", response_model=List[PlaybookMeta], status_code=status.HTTP_200_OK)
async def get_playbooks_to_share():
    """
    Retrieve a list of playbooks to share.

    Returns:
    - A list of playbooks with the shared property marked accordingly.
    """

    playbooks_to_share = await playbooks_collection.aggregate(to_share_pipeline).to_list(None)
    
    return playbooks_to_share

@router.get("/playbooks/to-save", response_model=List[PlaybookWithStixId], status_code=status.HTTP_200_OK)
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

            playbook = playbook.model_dump()
            playbook["stix_id"] = stix_playbook["id"]
            playbook = PlaybookWithStixId(**playbook)

            sharing_object = await sharings_collection.find_one({"playbook_id": playbook.id})

            if sharing_object:
                # Set 'shared' field based on whether 'modified' is in 'shared_versions'
                playbook.shared = playbook.modified in sharing_object.get("shared_versions", [])
            else:
                # If no sharing object exists, it's not shared
                playbook.shared = False

            playbooks_to_save.append(playbook)

        return reversed(playbooks_to_save)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
@router.get("/sharings/", response_model=List[SharingInDB], status_code=status.HTTP_200_OK)
async def get_sharings():
    """
    Retrieve all sharings.

    Returns:
    - A list of sharings.
    """

    sharings = await sharings_collection.find().sort("_id", -1).to_list(None)
    for sharing in sharings:
        sharing["_id"] = str(sharing["_id"])
    return sharings

@router.get("/sharings/{playbook_id}", response_model=SharingInDB, status_code=status.HTTP_200_OK)
async def get_sharing(playbook_id: str):
    """
    Retrieve a sharing by its Playbook ID.

    Returns:
    - A sharing object.
    """

    sharing = await sharings_collection.find_one({"playbook_id": playbook_id})
    if sharing:
        sharing["_id"] = str(sharing["_id"])
        return sharing
    
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sharing not found")

@router.delete("/sharings/{playbook_id}", response_model=dict, status_code=status.HTTP_200_OK)
async def delete_sharing(playbook_id: str):
    """
    Delete a sharing by its Playbook ID.

    Returns:
    - A message indicating the playbook was deleted successfully.
    """

    result = await sharings_collection.delete_one({"playbook_id": playbook_id})
    if result.deleted_count == 1:
        return {"message": "Sharing deleted successfully"}
    
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sharing not found")

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

async def get_object(object_id: str):
    """
    Get an object from the cacao collection.

    Arguments:
    - object_id: The id of the envelope object to get from the collection.

    Returns:
    - An envelope object.
    """

    try:
        async with httpx.AsyncClient(auth=auth, headers=headers) as client:
            response = await client.get(f"{taxii_url}/{taxii_api_root}/collections/{taxii_collection_id}/objects/{object_id}/")
            response.raise_for_status()
            result = response.json()

            return result

    except httpx.HTTPError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
