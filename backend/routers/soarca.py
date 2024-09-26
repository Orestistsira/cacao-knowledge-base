import asyncio
from datetime import datetime, timezone
import os
from dotenv import load_dotenv
from fastapi import HTTPException, status, APIRouter, BackgroundTasks
from tenacity import retry, stop_after_attempt, wait_fixed
from typing import List

import httpx

from models.playbook import Playbook
from models.execution import ExecutionInDB, StatusType
from database import db


load_dotenv()

router = APIRouter(
    prefix="/soarca",
    tags=["soarca"],
)

playbook_executions = db.executions

soarca_url = os.getenv("SOARCA_URI")

if not soarca_url:
    raise ValueError("SOARCA_URI environment variable not set")

@router.post("/trigger/playbook", response_model=dict, status_code=status.HTTP_200_OK)
async def trigger_playbook(playbook: Playbook, background_tasks: BackgroundTasks):
    """
    Execute a playbook.

    Arguments:
    - playbook: The Playbook object to be executed.

    Returns:
    - A dictionary containing the execution-id and the playbook-id.
    """

    # Serialize playbook object excluding none values
    playbook = playbook.model_dump(exclude_none=True)

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{soarca_url}/trigger/playbook", json=playbook)
            response.raise_for_status()
            result = response.json()

            execution_id = result.get("execution_id")
            playbook_id = result.get("payload")

            start_time = datetime.now(timezone.utc)

            await playbook_executions.insert_one({
                "playbook_id": playbook_id,
                "execution_id": execution_id,
                "status": StatusType.ongoing,
                "start_time": start_time
            })

            # Start agent on background to monitor playbook execution
            background_tasks.add_task(monitor_execution, execution_id, start_time)

            return {"playbook_id": playbook_id, "execution_id": execution_id}

    except httpx.HTTPError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
@retry(stop=stop_after_attempt(3), wait=wait_fixed(5), reraise=True)
async def fetch_report(client: httpx.AsyncClient, execution_id: str):
    """
    Fetches the playbook report for a given execution_id with retries.

    Arguments:
    - client: The httpx client instance to use for the request.
    - execution_id: The execution_id of the playbook to monitor.

    Returns:
    - The JSON response of the playbook status.
    """

    response = await client.get(f"{soarca_url}/reporter/{execution_id}")
    response.raise_for_status()
    return response.json()    

async def update_execution(execution_id: str, status: str, end_time: datetime, runtime: float):
    """
    Updates the playbook execution object in the database.

    Arguments:
    - execution_id: The ID of the playbook execution.
    - status: The status to set for the playbook execution.
    - end_time: The time the execution ended.
    - runtime: The total runtime of the execution in seconds.
    """

    update_data = {
        "status": status,
        "end_time": end_time,
        "runtime": runtime
    }

    # Assuming playbook_executions is a MongoDB collection
    await playbook_executions.update_one({"execution_id": execution_id}, {"$set": update_data})
    
async def monitor_execution(execution_id: str, start_time: datetime, timeout_seconds: int = 3600):
    """
    Monitors a playbook execution.

    Arguments:
    - execution_id: The execution_id of the execution to monitor.
    - start_time: The start time of the execution.
    - timeout_seconds: The maximum time (in seconds) to monitor the execution before timing out.
    """

    poll_interval_seconds = 5 # Poll every X seconds

    try:
        # Define a coroutine that performs the monitoring loop
        async def monitoring_loop():
            while True:
                async with httpx.AsyncClient() as client:
                    reporter_info = await fetch_report(client, execution_id)
                    end_time = datetime.now(timezone.utc)

                    # Check if the playbook execution has completed
                    if reporter_info["status"] != StatusType.ongoing:
                        await update_execution(
                            execution_id, 
                            reporter_info["status"], 
                            end_time, 
                            (end_time - start_time).total_seconds()
                        )
                        break

                await asyncio.sleep(poll_interval_seconds)  

        # Run the monitoring loop with a timeout
        await asyncio.wait_for(monitoring_loop(), timeout=timeout_seconds)

    except asyncio.TimeoutError:
        # Handle the case where the monitoring times out
        end_time = datetime.now(timezone.utc)

        await update_execution(
            execution_id,
            StatusType.timeout_error,
            end_time, 
            (end_time - start_time).total_seconds()
        )

    except httpx.HTTPError:
        # Handle the case where an http error occures
        end_time = datetime.now(timezone.utc)

        await update_execution(
            execution_id,
            StatusType.server_side_error,
            end_time, 
            (end_time - start_time).total_seconds()
        )

    except Exception:
        # Handle the case where a client exception occures
        end_time = datetime.now(timezone.utc)

        await update_execution(
            execution_id,
            StatusType.client_side_error,
            end_time, 
            (end_time - start_time).total_seconds()
        )

@router.get("/executions", response_model=List[ExecutionInDB], status_code=status.HTTP_200_OK)
async def get_executions(status: str | None = None):
    """
    Retrieve executions based on status.
    - If no status is provided, retrieve all executions.
    - If a status is provided, retrieve executions with this status.
    - If 'completed' is provided as status, retrieve all completed (not ongoing) executions.
    
    Returns:
    - A list of executions based on the status.
    """

    # MongoDB filter based on status
    query = {}
    
    if status == "completed":
        query = {"status": {"$ne": "ongoing"}}
    else:
        query = {"status": status}
    
    # Find executions based on the query and sort them
    executions = await playbook_executions.find(query).sort("_id", -1).to_list(None)
    
    # Convert MongoDB ObjectId to string for each execution
    for execution in executions:
        execution["_id"] = str(execution["_id"])
    
    return executions

@router.delete("/executions", response_model=dict, status_code=status.HTTP_200_OK)
async def delete_all_executions():
    """
    Delete all executions from the database.

    Returns:
    - A message indicating the executions were deleted successfully.
    """

    # Perform the deletion
    result = await playbook_executions.delete_many({})

    if result.deleted_count > 0:
        return {"message": "Executions deleted successfully"}
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No executions found to delete.")

@router.get("/executions/{execution_id}", response_model=ExecutionInDB, status_code=status.HTTP_200_OK)
async def get_execution(execution_id: str):
    """
    Retrieve an execution object by its execution ID.

    Returns:
    - An execution object.
    """

    execution = await playbook_executions.find_one({"execution_id": execution_id})
    if execution:
        execution["_id"] = str(execution["_id"])
        return execution
    
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Execution not found")

@router.delete("/executions/{execution_id}", response_model=dict, status_code=status.HTTP_200_OK)
async def delete_playbook(execution_id: str):
    """
    Delete an execution by its execution ID.

    Arguments:
    - execution_id: The execution ID of the execution to delete.

    Returns:
    - A message indicating the execution was deleted successfully.
    """

    result = await playbook_executions.delete_one({"execution_id": execution_id})
    if result.deleted_count == 1:
        return {"message": "Execution deleted successfully"}
    
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Execution not found")
