import asyncio
from datetime import datetime
import os
from dotenv import load_dotenv
from fastapi import HTTPException, status, APIRouter, BackgroundTasks
from typing import List

import httpx

from models.models import Playbook
from database import db


load_dotenv()

router = APIRouter(
    prefix="/soarca",
    tags=["soarca"],
)

playbook_executions = db.executions

soarca_url = os.getenv("SOARCA_URI")

@router.post("/trigger/playbook", response_model=dict, status_code=status.HTTP_200_OK)
async def trigger_playbook(playbook: dict, background_tasks: BackgroundTasks):
    """
    Execute a playbook.

    Arguments:
    - playbook: The Playbook object to be executed.

    Returns:
    - A dictionary containing the execution-id and the playbook-id.
    """

    print(soarca_url)

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

            # Start agent on background to monitor playbook execution
            background_tasks.add_task(monitor_playbook_execution, execution_id, start_time)

            return {"playbook_id": playbook_id, "execution_id": execution_id}

    except httpx.HTTPError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
async def monitor_playbook_execution(execution_id: str, start_time: datetime, timeout_seconds: int = 3600):
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

                await asyncio.sleep(poll_interval_seconds)  

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

@router.get("/executions/", response_model=List[dict])
async def get_executions():
    """
    Retrieve all executions.

    Returns:
    - A list of executions.
    """

    executions = list(playbook_executions.find())
    for execution in executions:
        execution["_id"] = str(execution["_id"])
    return executions

@router.get("/executions/ongoing", response_model=List[dict])
async def get_ongoing_executions():
    """
    Retrieve ongoing executions.

    Returns:
    - A list of ongoing executions.
    """

    ongoing_executions = list(playbook_executions.find({"status": "ongoing"}))
    for execution in ongoing_executions:
        execution["_id"] = str(execution["_id"])
    return ongoing_executions

# @router.get("/reporters", response_model=List[dict], status_code=status.HTTP_200_OK)
# async def get_reporters():
#     """
#     Retrieve all the reporters from SOARCA.

#     Returns:
#     - A list of reporter objects.
#     """

#     raise NotImplementedError

# @router.get("/reporters/{id}", response_model=dict, status_code=status.HTTP_200_OK)
# async def get_reporter(id: str):
#     """
#     Retrieve a reporter from SOARCA by its ID.

#     Arguments:
#     - id: The reporter ID.

#     Returns:
#     - A reporter object.
#     """

#     raise NotImplementedError