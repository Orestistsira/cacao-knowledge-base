from fastapi import APIRouter
from fastapi import status
from database import db

from pipelines.stats_pipeline import avg_runtime_pipeline, avg_runtime_per_playbook_pipeline, avg_comp_rate_pipeline


router = APIRouter(
    prefix="/stats",
    tags=["stats"],
)

playbooks_collection = db.playbooks
playbook_executions = db.executions

@router.get("/playbooks/count", response_model=dict, status_code=status.HTTP_200_OK)
async def count_playbooks():
    playbook_count = playbooks_collection.count_documents({})
    return {"playbook_count": playbook_count}

@router.get("/playbooks/active-count", response_model=dict, status_code=status.HTTP_200_OK)
async def count_active_playbooks():
    active_playbooks_count = playbooks_collection.count_documents({"revoked": False})
    return {"active_playbooks_count": active_playbooks_count}

@router.get("/executions/average-runtime/all")
async def get_overall_average_runtime():
    # Execute the pipeline
    result = list(playbook_executions.aggregate(avg_runtime_pipeline))

    # Check if we have a result and return it, otherwise return None
    overall_average_runtime = result[0]["overall_average_runtime"] if result else None

    return {"overall_average_runtime": overall_average_runtime}

@router.get("/executions/average-runtime/per_playbook")
async def get_average_runtime_per_playbook():
    # Execute the aggregation pipeline
    results = list(playbook_executions.aggregate(avg_runtime_per_playbook_pipeline))

    # Prepare the response
    playbook_averages = [
        {"playbook_id": result["playbook_id"], "avg_runtime": result["average_runtime"]}
        for result in results
    ]

    return {"playbook_averages": playbook_averages}

@router.get("/executions/average-completion-rate")
async def get_average_completion_rate():
    

    # Execute the aggregation pipeline
    results = list(playbook_executions.aggregate(avg_comp_rate_pipeline))

    # Prepare the response
    average_completion_rate = results[0]["average_completion_rate"] if results else None

    return {"average_completion_rate": average_completion_rate}

