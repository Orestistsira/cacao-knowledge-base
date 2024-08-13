import asyncio
from datetime import datetime
from fastapi import HTTPException, status, APIRouter, BackgroundTasks
from typing import List

import httpx

from models.models import Playbook
from database import db


router = APIRouter(
    prefix="/soarca",
    tags=["soarca"],
)

playbook_executions = db.executions

soarca_url = "http://localhost:8080"

@router.post("/trigger/playbook", response_model=dict, status_code=status.HTTP_200_OK)
async def trigger_playbook(playbook: dict, background_tasks: BackgroundTasks):
    """
    Execute a playbook.

    Args:
    - playbook: The Playbook object to be executed.

    Returns:
    - A dictionary containing the execution-id and the playbook-id.
    """

    try:
        async with httpx.AsyncClient() as client:
            # TODO: Set playbook dict to Playbook object - serialize datetime and remove null values
            response = await client.post(f"{soarca_url}/trigger/playbook", json=playbook)
            response.raise_for_status()
            result = response.json()

            execution_id = result.get("execution_id")
            playbook_id = result.get("payload")

            start_time = datetime.now()

            playbook_executions.insert_one({
                "playbook_id": playbook_id,
                "execution_id": execution_id,
                "status": "ongoing",
                "start_time": start_time
            })

            background_tasks.add_task(monitor_playbook_execution, execution_id, start_time)

            return {"playbook_id": playbook_id, "execution_id": execution_id}

    except httpx.HTTPError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
async def monitor_playbook_execution(execution_id: str, start_time: datetime, timeout_seconds: int = 3600):
    """
    Monitors a playbook execution.

    Args:
    - execution_id: The execution_id of the execution to monitor.
    - start_time: The start time of the execution.
    """

    polling_interval = 5 # Poll every X seconds

    try:
        # Define a coroutine that performs the monitoring loop
        async def monitoring_loop():
            while True:
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{soarca_url}/reporter/{execution_id}")
                    response.raise_for_status()

                    reporter_info = response.json()
                    end_time = datetime.now()

                    # Check if the playbook execution has completed
                    if reporter_info["status"] != "ongoing":
                        playbook_executions.update_one(
                            {"execution_id": execution_id},
                            {
                                "$set": {
                                    "status": reporter_info["status"], 
                                    "end_time": end_time, 
                                    "runtime": (end_time - start_time).total_seconds()
                                }
                            }
                        )
                        break

                await asyncio.sleep(polling_interval)  

        # Run the monitoring loop with a timeout
        await asyncio.wait_for(monitoring_loop(), timeout=timeout_seconds)

    except asyncio.TimeoutError:
        # Handle the case where the monitoring times out
        end_time = datetime.now()

        playbook_executions.update_one(
            {"execution_id": execution_id},
            {
                "$set": {
                    "status": "timeout_error", 
                    "end_time": end_time,
                    "runtime": (end_time - start_time).total_seconds()
                }
            }
        )

@router.get("/executions/currently-running", response_model=List[dict])
async def get_currently_running_executions():
    """
    Retrieve currently running executions.

    Returns:
    - A list of currently running executions.
    """

    running_playbooks = list(playbook_executions.find({"status": "ongoing"}))
    for playbook_exe in running_playbooks:
        playbook_exe["_id"] = str(playbook_exe["_id"])
    return running_playbooks

@router.get("/reporters", response_model=List[dict], status_code=status.HTTP_200_OK)
async def get_reporters():
    """
    Retrieve all the reporters from SOARCA.

    Returns:
    - A list of reporter objects.
    """

    raise NotImplementedError

@router.get("/reporters/{id}", response_model=dict, status_code=status.HTTP_200_OK)
async def get_reporter(id: str):
    """
    Retrieve a reporter from SOARCA by its ID.

    Args:
    - id: The reporter ID.

    Returns:
    - A reporter object.
    """

    raise NotImplementedError