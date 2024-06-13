from fastapi import APIRouter
from datetime import datetime
import re
from fastapi import HTTPException, Query, status
from typing import Annotated, List
from bson import ObjectId

from models.models import Playbook, PlaybookInDB
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

    Args:
    - playbook: The Playbook object to be created.

    Returns:
    - A dictionary containing the Mongo ID of the newly created playbook.
    """

    playbook = playbook.model_dump()

    result = playbooks_collection.insert_one(playbook)
    if result is not None:
        history_collection.insert_one(playbook)

    return {"_id": str(result.inserted_id)}

@router.get("/", response_model=List[PlaybookInDB], status_code=status.HTTP_200_OK)
async def get_playbooks(limit: int=50):
    """
    Retrieve a list of playbooks.

    Args:
    - limit: The maximum number of playbooks to retrieve (default is 50).

    Returns:
    - A list of playbook objects.
    """

    playbooks = list(playbooks_collection.find().limit(limit))
    for playbook in playbooks:
        playbook["_id"] = str(playbook["_id"])
    return playbooks

@router.get("/search", response_model=List[PlaybookInDB], status_code=status.HTTP_200_OK)
async def search_playbooks(
    name: str | None = None,
    created_by: str | None = None,
    created_after: datetime | None = None,
    created_until: datetime | None = None,
    revoked: bool | None = None,
    labels: Annotated[list[str] | None, Query()] = None,
    limit: int = 50
):
    """
    Search for playbooks based on various criteria.

    Args:
    - name: Search by playbook name.
    - created_by: Search by the creator of the playbook.
    - created_after: Search for playbooks created after a certain date.
    - created_until: Search for playbooks created until a certain date.
    - revoked: Search for playbooks that are revoked.
    - labels: Search for playbooks with specific labels.
    - limit: The maximum number of playbooks to retrieve (default is 50).

    Returns:
    - A list of playbook objects that match the search criteria.
    """

    query = {}
    if name:
        query["name"] = {"$regex": name, "$options": "i"}
    if created_by:
        query["created_by"] = created_by
    if created_after:
        query["created"] = {"$gte": created_after}
    if created_after:
        query["created"] = {"$lte": created_until}
    if revoked:
        query["revoked"] = revoked
    if labels:
        regex_labels = [f"^{re.escape(label)}" for label in labels]
        query["labels"] = {"$regex": "|".join(regex_labels)}
    
    playbooks = list(playbooks_collection.find(query).limit(limit))
    for playbook in playbooks:
        playbook["_id"] = str(playbook["_id"])
    return playbooks

@router.get("/{id}", response_model=PlaybookInDB, status_code=status.HTTP_200_OK)
async def get_playbook(id: str):
    """
    Retrieve a playbook by its Mongo ID.

    Args:
    - id: The Mongo ID of the playbook to retrieve.

    Returns:
    - The playbook object if found.

    Raises:
    - HTTPException: If the playbook is not found.
    """

    playbook = playbooks_collection.find_one({"_id": ObjectId(id)})
    if playbook is not None:
        playbook["_id"] = str(playbook["_id"])
        return playbook
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playbook not found")

@router.put("/{id}", response_model=dict, status_code=status.HTTP_200_OK)
async def update_playbook(id: str, playbook_update: Playbook):
    """
    Update an existing playbook by its Mongo ID.

    Args:
    - id: The Mongo ID of the playbook to update.
    - playbook_update: The updated Playbook object.

    Returns:
    - A message indicating the playbook was updated.

    Raises:
    - HTTPException: If the playbook is not found.
    """

    playbook_update = playbook_update.model_dump()
    result = playbooks_collection.update_one({"_id": ObjectId(id)}, {"$set": playbook_update})
    
    if result.modified_count == 1:
        history_collection.insert_one(playbook_update)
        return {"message": "Playbook updated"}
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playbook not found")

@router.delete("/{id}", response_model=dict, status_code=status.HTTP_200_OK)
async def delete_playbook(id: str):
    """
    Delete a playbook by its Mongo ID.

    Args:
    - id: The Mongo ID of the playbook to delete.

    Returns:
    - A message indicating the playbook was deleted successfully.

    Raises:
    - HTTPException: If the playbook is not found.
    """

    result = playbooks_collection.delete_one({"_id": ObjectId(id)})
    if result.deleted_count == 1:
        return {"message": "Playbook deleted successfully"}
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playbook not found")

@router.get("/{playbook_id}/history", response_model=List[PlaybookInDB], status_code=status.HTTP_200_OK)
async def get_playbook_history(playbook_id: str, limit: int=50):
    """
    Retrieve the history of a playbook by its Playbook ID property.

    Args:
    - id: The Playbook ID of the playbook to retrieve history for.
    - limit: The maximum number of history entries to retrieve (default is 50).

    Returns:
    - A list of playbook history objects.

    Raises:
    - HTTPException: If the playbook is not found.
    """

    playbook_history = list(history_collection.find({"id": playbook_id}).limit(limit))
    if len(playbook_history) > 0:
        for playbook in playbook_history:
            playbook["_id"] = str(playbook["_id"])
        return playbook_history
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playbook not found")

@router.delete("/{playbook_id}/history", response_model=dict, status_code=status.HTTP_200_OK)
async def delete_playbook_history(playbook_id: str):
    """
    Delete all history playbooks associated with a specific playbook ID.

    Args:
    - playbook_id: The Playbook ID of the playbook whose history is to be deleted.

    Returns:
    - A message indicating the history playbooks were deleted successfully.

    Raises:
    - HTTPException: If no history playbooks are found.
    """

    result = history_collection.delete_many({"id": playbook_id})
    if result.deleted_count > 0:
        return {"message": f"History playbooks deleted successfully"}
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No history playbooks found for the given Playbook ID")

@router.post("/rollback/{history_id}", response_model=dict, status_code=status.HTTP_200_OK)
async def rollback_playbook(history_id: str):
    """
    Rollback to a specific playbook from history by its Mongo ID.

    Args:
    - history_id: The Mongo ID of the history playbook to restore.

    Returns:
    - A message indicating the playbook was restored successfully.

    Raises:
    - HTTPException: If the history playbook is not found.
    """

    history_playbook = history_collection.find_one({"_id": ObjectId(history_id)})
    if history_playbook is not None:
        playbook_id = history_playbook["id"]

        # Remove _id to avoid duplicate key error
        history_playbook.pop("_id")
        history_playbook["modified"] = datetime.now()
        
        result = playbooks_collection.update_one({"id": playbook_id}, {"$set": history_playbook})
        if result.modified_count == 1:
            history_collection.insert_one(history_playbook)
            return {"message": "Playbook restored successfully"}
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playbook not found")
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="History playbook not found")
  