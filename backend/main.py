from fastapi import FastAPI, HTTPException, status
from typing import List
from pymongo import MongoClient
from bson import ObjectId
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

client = MongoClient(os.getenv("MONGODB_URI"))
db = client['cacao_knowledge_base']
collection = db.playbooks
    

def get_object_id(playbook_id: str):
    try:
        # Convert the string ID to a MongoDB ObjectId
        return ObjectId(playbook_id)
    except:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid input data")
   

@app.post("/playbooks", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_playbook(playbook: dict):
    result = collection.insert_one(playbook)
    return {"_id": str(result.inserted_id)}

@app.get("/playbooks", response_model=List[dict], status_code=status.HTTP_200_OK)
async def get_playbooks(limit: int=50):
    playbooks = list(collection.find().limit(limit))
    for playbook in playbooks:
        playbook["_id"] = str(playbook["_id"])
    return playbooks

@app.get("/playbooks/search", response_model=List[dict], status_code=status.HTTP_200_OK)
async def search_playbooks(
    name: str | None = None,
    created_by: str | None = None,
    limit: int = 50
):
    query = {}
    if name:
        query["name"] = {"$regex": name, "$options": "i"}
    if created_by:
        query["created_by"] = {"$regex": created_by, "$options": "i"}
    
    playbooks = list(collection.find(query).limit(limit))
    for playbook in playbooks:
        playbook["_id"] = str(playbook["_id"])
    return playbooks

@app.get("/playbooks/{id}", response_model=dict, status_code=status.HTTP_200_OK)
async def get_playbook(id: str):    
    playbook = collection.find_one({"_id": ObjectId(id)})
    if playbook is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playbook not found")
    playbook["_id"] = str(playbook["_id"])
    return playbook

@app.put("/playbooks/{id}", response_model=dict, status_code=status.HTTP_200_OK)
async def update_playbook(id: str, playbook_update: dict):
    result = collection.update_one({"_id": ObjectId(id)}, {"$set": playbook_update})
    if result.modified_count == 1:
        return {"message": "Playbook updated"}
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playbook not found")

@app.delete("/playbooks/{id}", status_code=status.HTTP_200_OK)
async def delete_playbook(id: str):
    result = db.playbooks.delete_one({"_id": ObjectId(id)})
    if result.deleted_count == 1:
        return {"message": "Playbook deleted successfully"}
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playbook not found")
