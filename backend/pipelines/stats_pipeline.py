# Aggregation pipeline to calculate the overall average runtime
avg_runtime_pipeline = [
    {
        "$group": {
            "_id": None,  # Group all documents together
            "average_runtime": {"$avg": "$runtime"}  # Calculate the average runtime
        }
    }
]

# Aggregation pipeline to calculate average runtime per playbook
avg_runtime_per_playbook_pipeline = [
    {
        "$group": {
            "_id": "$playbook_id",  # Group by playbook_id
            "average_runtime": {"$avg": "$runtime"}  # Calculate average runtime
        }
    },
    {
        "$sort": {
            "_id": -1
        }
    },
    {
        "$project": {
            "_id": 0,  # Exclude _id from the output
            "playbook_id": "$_id",  # Include playbook_id in the output
            "average_runtime": 1  # Include average_runtime in the output
        }
    }
]

avg_comp_rate_pipeline = [
    # Step 1: Filter out ongoing executions
    {
        "$match": {
            "status": {"$ne": "ongoing"}  # Exclude ongoing executions
        }
    },
    # Step 2: Group by playbook_id to count total and completed executions
    {
        "$group": {
            "_id": "$playbook_id",  # Group by playbook_id
            "total_executions": {"$sum": 1},  # Count total executions
            "completed_executions": {
                "$sum": {
                    "$cond": [
                        {"$eq": ["$status", "successfully_executed"]},  # Check if status is 'successfully_executed'
                        1,  # Count as 1 if true
                        0   # Count as 0 if false
                    ]
                }
            }
        }
    },
    # Step 3: Calculate completion rate for each playbook
    {
        "$project": {
            "playbook_id": "$_id",
            "completion_rate": {
                "$cond": [
                    {"$gt": ["$total_executions", 0]},  # Avoid division by zero
                    {"$divide": ["$completed_executions", "$total_executions"]},  # Calculate rate
                    0  # Set to 0 if no executions
                ]
            }
        }
    },
    # Step 4: Calculate the average completion rate
    {
        "$group": {
            "_id": None,
            "average_completion_rate": {"$avg": "$completion_rate"}  # Compute average rate
        }
    },
    # Step 5: Format the output
    {
        "$project": {
            "_id": 0,
            "average_completion_rate": 1
        }
    }
]

comp_rate_per_playbook_pipeline = [
    # Step 1: Filter out ongoing executions
    {
        "$match": {
            "status": {"$ne": "ongoing"}  # Exclude ongoing executions
        }
    },
    # Step 2: Group by playbook_id to count total and completed executions
    {
        "$group": {
            "_id": "$playbook_id",  # Group by playbook_id
            "total_executions": {"$sum": 1},  # Count total executions
            "successful_executions": {
                "$sum": {
                    "$cond": [
                        {"$eq": ["$status", "successfully_executed"]},  # Check if status is 'successfully_executed'
                        1,  # Count as 1 if true
                        0   # Count as 0 if false
                    ]
                }
            }
        }
    },
    # Step 3: Calculate completion rate for each playbook
    {
        "$project": {
            "playbook_id": "$_id",
            "completion_rate": {
                "$cond": [
                    {"$gt": ["$total_executions", 0]},  # Avoid division by zero
                    {"$divide": ["$successful_executions", "$total_executions"]},  # Calculate rate
                    0  # Set to 0 if no executions
                ]
            }
        }
    },
    # Step 4: Sort the output
    {
        "$sort": {
            "_id": -1
        }
    },
    # Step 5: Format the output
    {
        "$project": {
            "_id": 0,
            "playbook_id": 1,
            "completion_rate": 1
        }
    }
]
