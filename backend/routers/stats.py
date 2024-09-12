from fastapi import APIRouter, HTTPException, status
from typing import List
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

    try:
        total_count = await count_playbooks()
        active_count = await count_active_playbooks()
        return {**total_count, **active_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving playbook stats: {str(e)}")


@router.get("/playbooks/completion-rate/per-playbook", response_model=List[dict], status_code=status.HTTP_200_OK)
async def get_completion_rate_per_playbook():
    """
    Retrieve the completion rate for each playbook.

    Returns:
    - A list of dictionaries, each containing:
        - The ID of the playbook.
        - The completion rate for that playbook.
    """

    try:
        results = await playbook_executions.aggregate(comp_rate_per_playbook_pipeline).to_list(None)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving completion rates: {str(e)}")


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

    try:
        total_executions = await count_executions()
        ongoing_executions = await count_ongoing_executions()
        average_runtime = await get_average_runtime()
        average_completion_rate = await get_average_completion_rate()

        return {
            **total_executions,
            **ongoing_executions,
            **average_runtime,
            **average_completion_rate
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving execution stats: {str(e)}")


@router.get("/executions/average-runtime/per-playbook", response_model=List[dict], status_code=status.HTTP_200_OK)
async def get_average_runtime_per_playbook():
    """
    Retrieve the average runtime per playbook.

    Returns:
    - A list of dictionaries, each containing:
        - The ID of the playbook.
        - The average runtime for that playbook.
    """

    try:
        results = await playbook_executions.aggregate(avg_runtime_per_playbook_pipeline).to_list(None)
        playbook_averages = [
            {"playbook_id": result["playbook_id"], "avg_runtime": result["average_runtime"]}
            for result in results
        ]
        return playbook_averages
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving average runtime per playbook: {str(e)}")


# Helper functions without unnecessary 404 exceptions

async def count_playbooks():
    """
    Retrieve the total number of playbooks in the database.

    Returns:
    - The total count of playbooks.
    """

    try:
        playbook_count = await playbooks_collection.count_documents({})
        return {"playbook_count": playbook_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error counting playbooks: {str(e)}")


async def count_active_playbooks():
    """
    Retrieve the number of active playbooks (not revoked).

    Returns:
    - The count of active playbooks.
    """

    try:
        active_playbooks_count = await playbooks_collection.count_documents({"revoked": False})
        return {"active_playbooks_count": active_playbooks_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error counting active playbooks: {str(e)}")


async def count_executions():
    """
    Retrieve the total number of executions in the database.

    Returns:
    - The total count of executions.
    """

    try:
        executions_count = await playbook_executions.count_documents({})
        return {"executions_count": executions_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error counting executions: {str(e)}")


async def count_ongoing_executions():
    """
    Retrieve the number of ongoing executions.

    Returns:
    - The count of ongoing executions.
    """

    try:
        ongoing_count = await playbook_executions.count_documents({"status": "ongoing"})
        return {"ongoing_executions": ongoing_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error counting ongoing executions: {str(e)}")


async def get_average_runtime():
    """
    Retrieve the average runtime of all playbook executions.

    Returns:
    - The average runtime of all executions, or None if no executions are found.
    """

    try:
        result = await playbook_executions.aggregate(avg_runtime_pipeline).to_list(None)
        average_runtime = result[0]["average_runtime"] if result else None
        return {"average_runtime": average_runtime}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving average runtime: {str(e)}")


async def get_average_completion_rate():
    """
    Retrieve the average completion rate of all playbooks.

    Returns:
    - The average completion rate across all playbooks, or None if no executions are found.
    """

    try:
        results = await playbook_executions.aggregate(avg_comp_rate_pipeline).to_list(None)
        average_completion_rate = results[0]["average_completion_rate"] if results else None
        return {"average_completion_rate": average_completion_rate}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving average completion rate: {str(e)}")
