import os
from fastapi import APIRouter
from datetime import datetime
import re
from fastapi import HTTPException, Query, status
from typing import Annotated, List
from pymongo import MongoClient
from bson import ObjectId

from models.models import Playbook, PlaybookInDB


router = APIRouter(
    prefix="/playbooks",
    tags=["playbooks"],
)

client = MongoClient(os.getenv("MONGODB_URI"))
db = client['cacao_knowledge_base']
collection = db.playbooks

@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_playbook(playbook: Playbook):
    playbook = playbook.model_dump()
    result = collection.insert_one(playbook)
    return {"_id": str(result.inserted_id)}

@router.get("/", response_model=List[PlaybookInDB], status_code=status.HTTP_200_OK)
async def get_playbooks(limit: int=50):
    playbooks = list(collection.find().limit(limit))
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
    
    playbooks = list(collection.find(query).limit(limit))
    for playbook in playbooks:
        playbook["_id"] = str(playbook["_id"])
    return playbooks

@router.get("/{id}", response_model=PlaybookInDB, status_code=status.HTTP_200_OK)
async def get_playbook(id: str):    
    playbook = collection.find_one({"_id": ObjectId(id)})
    if playbook is not None:
        playbook["_id"] = str(playbook["_id"])
        return playbook
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playbook not found")

@router.put("/{id}", response_model=dict, status_code=status.HTTP_200_OK)
async def update_playbook(id: str, playbook_update: Playbook):
    playbook_update = playbook_update.model_dump()
    result = collection.update_one({"_id": ObjectId(id)}, {"$set": playbook_update})
    if result.modified_count == 1:
        return {"message": "Playbook updated"}
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playbook not found")

@router.delete("/{id}", status_code=status.HTTP_200_OK)
async def delete_playbook(id: str):
    result = db.playbooks.delete_one({"_id": ObjectId(id)})
    if result.deleted_count == 1:
        return {"message": "Playbook deleted successfully"}
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playbook not found")