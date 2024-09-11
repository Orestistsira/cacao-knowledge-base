from fastapi import APIRouter
from datetime import datetime
import re
from fastapi import HTTPException, Query, status
from typing import Annotated, List
from bson import ObjectId

from utils.utils import get_current_timestamp, get_datetime_from_timestamp
from pipelines.meta_pipeline import meta_pipeline
from models.playbook import Playbook, PlaybookInDB, PlaybookMeta
from database import db

router = APIRouter(
    prefix="/playbooks",
    tags=["playbooks"],
)

playbooks_collection = db.playbooks
history_collection = db.history

@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_playbook(playbook: Playbook):
    """
    Create a new playbook.

    Arguments:
    - playbook: The Playbook object to be created.

    Returns:
    - A dictionary containing the Mongo ID of the newly created playbook.
    """

    playbook = playbook.model_dump()

    result = await playbooks_collection.insert_one(playbook)
    if result:
        await history_collection.insert_one(playbook)

    return {"_id": str(result.inserted_id)}

@router.get("/", response_model=List[PlaybookInDB], status_code=status.HTTP_200_OK)
async def get_playbooks():
    """
    Retrieve a list of playbooks.

    Returns:
    - A list of playbook objects.
    """

    playbooks = await playbooks_collection.find().sort("_id", -1).to_list(None)
    for playbook in playbooks:
        playbook["_id"] = str(playbook["_id"])
    return playbooks

@router.get("/meta", response_model=List[PlaybookMeta], status_code=status.HTTP_200_OK)
async def get_playbooks_meta():
    """
    Retrieve a list of playbooks metadata.

    Returns:
    - A list of playbook metadata objects.
    """

    playbooks_meta = await playbooks_collection.aggregate(meta_pipeline).to_list(None)
    return playbooks_meta

@router.get("/{id}", response_model=PlaybookInDB, status_code=status.HTTP_200_OK)
async def get_playbook(id: str):
    """
    Retrieve a playbook by its Playbook ID.

    Arguments:
    - id: The Playbook ID of the playbook to retrieve.

    Returns:
    - The playbook object if found.

    Raises:
    - HTTPException: If the playbook is not found.
    """

    playbook = await playbooks_collection.find_one({"id": id})
    if playbook:
        playbook["_id"] = str(playbook["_id"])
        return playbook
    
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playbook not found")

@router.put("/{id}", response_model=dict, status_code=status.HTTP_200_OK)
async def update_playbook(id: str, playbook_update: Playbook):
    """
    Update an existing playbook by its Playbook ID.

    Arguments:
    - id: The Playbook ID of the playbook to update.
    - playbook_update: The updated Playbook object.

    Returns:
    - A message indicating the playbook was updated.

    Raises:
    - HTTPException: If the playbook is not found or is revoked or timestamps are invalid.
    """

    playbook_update = playbook_update.model_dump()

    # Retrieve the existing playbook from the database
    existing_playbook = await playbooks_collection.find_one({"id": id})
    if not existing_playbook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playbook not found."
        )
    
    # Check if the playbook is revoked
    if existing_playbook["revoked"] == True:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot update a revoked playbook."
        )
    
    # Convert string timestamps to datetime objects
    created_time = get_datetime_from_timestamp(playbook_update["created"])
    modified_time = get_datetime_from_timestamp(playbook_update["modified"])
    existing_modified_time = get_datetime_from_timestamp(existing_playbook["modified"])

    # Check if 'modified' timestamp is more recent than 'created' timestamp
    if modified_time <= created_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="'modified' timestamp must be more recent than 'created' timestamp."
        )
    
    # Check if 'modified' timestamp is more recent than the stored 'modified' timestamp
    if modified_time <= existing_modified_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The new 'modified' timestamp must be more recent than the existing 'modified' timestamp."
        )

    # Update playbook
    result = await playbooks_collection.update_one(
        {
            "id": id,
            "created": playbook_update["created"],
            "created_by": playbook_update["created_by"]
        }, 
        {"$set": playbook_update}
    )
    
    if result.modified_count == 1:
        await history_collection.insert_one(playbook_update)
        return {"message": "Playbook updated"}
    
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Playbook not updated")

@router.delete("/{id}", response_model=dict, status_code=status.HTTP_200_OK)
async def delete_playbook(id: str):
    """
    Delete a playbook by its Playbook ID.

    Arguments:
    - id: The Playbook ID of the playbook to delete.

    Returns:
    - A message indicating the playbook was deleted successfully.

    Raises:
    - HTTPException: If the playbook is not found.
    """

    result = await playbooks_collection.delete_one({"id": id})
    if result.deleted_count == 1:
        return {"message": "Playbook deleted successfully"}
    
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playbook not found")

@router.get("/{id}/history", response_model=List[PlaybookInDB], status_code=status.HTTP_200_OK)
async def get_playbook_history(id: str):
    """
    Retrieve the history of a playbook by its Playbook ID property.

    Arguments:
    - playbook_id: The Playbook ID of the playbook to retrieve history for.

    Returns:
    - A list of playbook history objects.

    Raises:
    - HTTPException: If the playbook is not found.
    """

    playbook_history = await history_collection.find({"id": id}).sort("_id", -1).to_list(None)
    if len(playbook_history) > 0:
        # Delete first playbook which is the current
        del playbook_history[0]
        for playbook in playbook_history:
            playbook["_id"] = str(playbook["_id"])
        return playbook_history
    
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="History playbooks not found for the given Playbook ID")

@router.delete("/{id}/history", response_model=dict, status_code=status.HTTP_200_OK)
async def delete_playbook_history(id: str):
    """
    Delete all history playbooks associated with a specific playbook ID.

    Arguments:
    - playbook_id: The Playbook ID of the playbook whose history is to be deleted.

    Returns:
    - A message indicating the history playbooks were deleted successfully.

    Raises:
    - HTTPException: If no history playbooks are found.
    """

    result = await history_collection.delete_many({"id": id})
    if result.deleted_count > 0:
        return {"message": f"History playbooks deleted successfully"}
    
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="History playbooks not found for the given Playbook ID")

@router.get("/history/{history_id}", response_model=PlaybookInDB, status_code=status.HTTP_200_OK)
async def get_history_playbook(history_id: str):
    """
    Retrieve a history playbook by its Mongo ID.

    Arguments:
    - id: The Mongo ID of the history playbook to retrieve.

    Returns:
    - The playbook object if found.

    Raises:
    - HTTPException: If the playbook is not found.
    """

    playbook = await history_collection.find_one({"_id": ObjectId(history_id)})
    if playbook:
        playbook["_id"] = str(playbook["_id"])
        return playbook
    
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playbook not found")

@router.post("/rollback/{history_id}", response_model=dict, status_code=status.HTTP_200_OK)
async def rollback_playbook(history_id: str):
    """
    Rollback to a specific playbook from history by its Mongo ID.

    Arguments:
    - id: The Mongo ID of the history playbook to restore.

    Returns:
    - A message indicating the playbook was restored successfully.

    Raises:
    - HTTPException: If the history playbook is not found or is revoked.
    """

    history_playbook = await history_collection.find_one({"_id": ObjectId(history_id)})
    if history_playbook is not None:
        playbook_id = history_playbook["id"]

        # Retrieve the existing playbook from the database
        existing_playbook = await playbooks_collection.find_one({"id": playbook_id})
        if not existing_playbook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Playbook not found."
            )
        
        # Check if the playbook is revoked
        if existing_playbook["revoked"] == True:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot update a revoked playbook."
            )

        # Remove _id to avoid duplicate key error
        history_playbook.pop("_id")
        history_playbook["modified"] = get_current_timestamp()
        
        result = await playbooks_collection.update_one({"id": playbook_id}, {"$set": history_playbook})
        if result.modified_count == 1:
            await history_collection.insert_one(history_playbook)
            return {"message": "Playbook restored successfully"}
        
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playbook not found")
    
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="History playbook not found")
  