from typing import List
from fastapi import APIRouter
from fastapi import status
from database import db

from pipelines.stats_pipeline import avg_runtime_pipeline, avg_runtime_per_playbook_pipeline
from pipelines.stats_pipeline import avg_comp_rate_pipeline, comp_rate_per_playbook_pipeline


router = APIRouter(
    prefix="/stats",
    tags=["stats"],
)

playbooks_collection = db.playbooks
playbook_executions = db.executions

@router.get("/playbooks/general", response_model=dict, status_code=status.HTTP_200_OK)
async def get_playbooks_general_stats():
    """
    Retrieve the total number of playbooks and the number of active playbooks (not revoked).

    Returns:
    - A JSON object with both the total count and the active count of playbooks.
    """

    # Call the existing functions to get the data
    total_count = await count_playbooks()
    active_count = await count_active_playbooks()

    return {**total_count, **active_count}

@router.get("/playbooks/completion-rate/per-playbook", response_model=List[dict], status_code=status.HTTP_200_OK)
async def get_completion_rate_per_playbook():
    """
    Retrieve the completion rate for each playbook.

    Returns:
    - A list of dictionaries, each containing:
        - The ID of the playbook.
        - The completion rate for that playbook.
    """

    # Execute the aggregation pipeline
    results = await playbook_executions.aggregate(comp_rate_per_playbook_pipeline).to_list(None)

    return results

@router.get("/executions/general", response_model=dict, status_code=status.HTTP_200_OK)
async def get_executions_general():
    """
    Retrieve a summary of all execution metrics including:
    - Total number of executions
    - Number of ongoing executions
    - Average runtime of all executions
    - Average completion rate of all executions

    Returns:
    - A JSON object with the combined results from the other execution-related endpoints.
    """

    # Call the existing functions to get their results
    total_executions = await count_executions()
    ongoing_executions = await count_ongoing_executions()
    average_runtime = await get_average_runtime()
    average_completion_rate = await get_average_completion_rate()

    # Combine the results into a single response dictionary
    return {
        **total_executions,
        **ongoing_executions,
        **average_runtime,
        **average_completion_rate
    }

@router.get("/executions/average-runtime/per-playbook", response_model=List[dict], status_code=status.HTTP_200_OK)
async def get_average_runtime_per_playbook():
    """
    Retrieve the average runtime per playbook.

    Returns:
    - A list of dictionaries, each containing:
        - The ID of the playbook.
        - The average runtime for that playbook.
    """

    # Execute the aggregation pipeline
    results = await playbook_executions.aggregate(avg_runtime_per_playbook_pipeline).to_list(None)

    # Prepare the response
    playbook_averages = [
        {"playbook_id": result["playbook_id"], "avg_runtime": result["average_runtime"]}
        for result in results
    ]

    return playbook_averages

@router.get("/playbooks/count", response_model=dict, status_code=status.HTTP_200_OK)
async def count_playbooks():
    """
    Retrieve the total number of playbooks in the database.

    Returns:
    - The total count of playbooks.
    """

    playbook_count = await playbooks_collection.count_documents({})
    return {"playbook_count": playbook_count}

@router.get("/playbooks/active-count", response_model=dict, status_code=status.HTTP_200_OK)
async def count_active_playbooks():
    """
    Retrieve the number of active playbooks (not revoked).

    Returns:
    - The count of active playbooks.
    """

    active_playbooks_count = await playbooks_collection.count_documents({"revoked": False})
    return {"active_playbooks_count": active_playbooks_count}

@router.get("/executions/count", response_model=dict, status_code=status.HTTP_200_OK)
async def count_executions():
    """
    Retrieve the total number of executions in the database.

    Returns:
    - The total count of executions.
    """

    executions_count = await playbook_executions.count_documents({})
    return {"executions_count": executions_count}

@router.get("/executions/count/ongoing", response_model=dict, status_code=status.HTTP_200_OK)
async def count_ongoing_executions():
    """
    Retrieve the number of ongoing executions.

    Returns:
    - The count of ongoing executions.
    """

    # Query to count the number of ongoing executions
    ongoing_count = await playbook_executions.count_documents({"status": "ongoing"})
    
    return {"ongoing_executions": ongoing_count}

@router.get("/executions/average-runtime/all", response_model=dict, status_code=status.HTTP_200_OK)
async def get_average_runtime():
    """
    Retrieve the average runtime of all playbook executions.

    Returns:
    - The average runtime of all executions, or None if no executions are found.
    """

    # Execute the pipeline
    result = await playbook_executions.aggregate(avg_runtime_pipeline).to_list(None)

    # Check if we have a result and return it, otherwise return None
    average_runtime = result[0]["average_runtime"] if result else None

    return {"average_runtime": average_runtime}

@router.get("/executions/average-completion-rate/all", response_model=dict, status_code=status.HTTP_200_OK)
async def get_average_completion_rate():
    """
    Retrieve the average completion rate of all playbooks.

    Returns:
    - The average completion rate across all playbooks, or None if no executions are found.
    """

    # Execute the aggregation pipeline
    results = await playbook_executions.aggregate(avg_comp_rate_pipeline).to_list(None)

    # Prepare the response
    average_completion_rate = results[0]["average_completion_rate"] if results else None

    return {"average_completion_rate": average_completion_rate}
