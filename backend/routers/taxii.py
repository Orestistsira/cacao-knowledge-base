import base64
import json
import os
import uuid
from dotenv import load_dotenv
from fastapi import HTTPException, status, APIRouter

import httpx

from routers.playbooks import create_playbook
from utils.utils import get_current_datetime_str
from models.stix import Envelope, StixPlaybook
from models.playbook import Playbook
from database import db


load_dotenv()

router = APIRouter(
    prefix="/taxii",
    tags=["taxii"],
)

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

taxii_api_root = 'cacao-taxii'
taxii_collection_id = '365fed99-08fa-fdcd-a1b3-fb247eb41d01'

def playbook_to_stix(playbook: Playbook) -> StixPlaybook:
    # Generate the ID and filename for the COA object
    coa_id = f"course-of-action--{str(uuid.uuid4())}"

    # Create the STIX 2.1 COA object with Playbook extension
    stix_playbook = create_stix_coa_with_playbook_extension(playbook, coa_id)
    
    return stix_playbook

def create_stix_coa_with_playbook_extension(playbook: Playbook, coa_id: str) -> StixPlaybook:
    return {
        "type": "course-of-action",
        "spec_version": "2.1",
        "id": coa_id,
        "created_by_ref": playbook.created_by,
        "created": get_current_datetime_str(),
        "modified": get_current_datetime_str(),
        "name": "playbook",
        "description": playbook.description,
        "extensions": {
            f"extension-definition--{str(uuid.uuid4())}": {
                "extension_type": "property-extension",
                "playbook_id": playbook.id,
                "created": playbook.created,
                "modified": playbook.modified,
                "playbook_creator": playbook.created_by,
                "revoked": playbook.revoked,
                "labels": playbook.labels,
                "description": playbook.description,
                "playbook_valid_from": playbook.valid_from,
                "playbook_valid_until": playbook.valid_until,
                "playbook_creation_time": playbook.created,
                "playbook_impact": playbook.impact,
                "playbook_severity": playbook.severity,
                "playbook_priority": playbook.priority,
                "playbook_type": playbook.playbook_types,
                "playbook_standard": "cacao",
                "playbook_abstraction": "template",
                "playbook_base64": base64.b64encode(
                    json.dumps(playbook.model_dump(exclude_none=True)).encode()
                ).decode()
            }
        }
    }

def stix_to_playbook(stix_playbook: StixPlaybook) -> Playbook:
    # Extract the extension definition (assuming only one extension is present)
    extensions = stix_playbook.get('extensions')
    extension_key = next(iter(extensions))  # Get the first (and presumably only) extension key
    extension = extensions.get(extension_key, {})

    # Decode the base64 encoded playbook data
    playbook_base64 = extension.get("playbook_base64", "")
    playbook_json = base64.b64decode(playbook_base64).decode()
    playbook_data = json.loads(playbook_json)

    # Create and return a Playbook object
    return Playbook(
        type=playbook_data.get("type"),
        spec_version=playbook_data.get("spec_version"),
        id=extension.get("playbook_id"),
        name=stix_playbook.get("name"),
        description=stix_playbook.get("description"),
        playbook_types=extension.get("playbook_type"),
        created_by=extension.get("playbook_creator"),
        created=extension.get("created"),
        modified=extension.get("modified"),
        revoked=extension.get("revoked"),
        valid_from=extension.get("playbook_valid_from"),
        valid_until=extension.get("playbook_valid_until"),
        playbook_processing_summary=None,  # Adjust this if necessary
        derived_from=None,  # Adjust this if necessary
        related_to=None,  # Adjust this if necessary
        priority=extension.get("playbook_priority"),
        severity=extension.get("playbook_severity"),
        impact=extension.get("playbook_impact"),
        industry_sectors=None,  # Adjust this if necessary
        labels=extension.get("labels"),
        external_references=None,  # Adjust this if necessary
        markings=None,  # Adjust this if necessary
        playbook_variables=None,  # Adjust this if necessary
        workflow_start=playbook_data.get("workflow_start"),
        workflow_exception=playbook_data.get("workflow_exception"),
        workflow=playbook_data.get("workflow"),
        playbook_extensions=playbook_data.get("playbook_extensions"),
        authentication_info_definitions=playbook_data.get("authentication_info_definitions"),
        agent_definitions=playbook_data.get("agent_definitions"),
        target_definitions=playbook_data.get("target_definitions"),
        extension_definitions=playbook_data.get("extension_definitions"),
        data_marking_definitions=playbook_data.get("data_marking_definitions"),
        signatures=playbook_data.get("signatures")
    )

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

    try:
        stix_playbook = playbook_to_stix(playbook)
        return await add_object({"objects": [stix_playbook]})
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
        stix_playbook = stix_playbook_envelope.get('objects')[0]

        # Convert STIX object to Playbook
        playbook = stix_to_playbook(stix_playbook)

        # Create Playbook
        return await create_playbook(playbook)
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
    - An envelope objects with all the object.
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
