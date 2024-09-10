to_share_pipeline = [
    # Perform a lookup to join with sharings collection
    {
        "$lookup": {
            "from": "sharings",
            "localField": "id",  # Assuming playbook_id is 'id' in playbooks collection
            "foreignField": "playbook_id",
            "as": "sharings"
        }
    },
    # Unwind the sharings array
    {
        "$unwind": {
            "path": "$sharings",
            "preserveNullAndEmptyArrays": True  # Keep playbooks without shared data
        }
    },
    # Add 'shared' field based on whether the 'modified' exists in shared_versions
    {
        "$addFields": {
            "shared": {
                "$cond": {
                    "if": {
                        "$in": [
                            "$modified", 
                            { "$ifNull": ["$sharings.shared_versions", []] }
                        ]
                    },
                    "then": True,
                    "else": False
                }
            }
        }
    },
    # Sort by _id
    {
        "$sort": {
            "_id": -1
        }
    },
    # Project the desired fields along with 'shared'
    {
        "$project": {
            "_id": 0,
            "spec_version": 1,
            "id": 1,
            "name": 1,
            "description": 1,
            "playbook_types": 1,
            "playbook_activities": 1,
            "playbook_processing_summary": 1,
            "created_by": 1,
            "created": 1,
            "modified": 1,
            "revoked": 1,
            "valid_from": 1,
            "valid_until": 1,
            "derived_from": 1,
            "related_to": 1,
            "priority": 1,
            "severity": 1,
            "impact": 1,
            "industry_sectors": 1,
            "labels": 1,
            "external_references": 1,
            "markings": 1,
            "data_marking_definitions": 1,
            "shared": 1
        }
    }
]

    # # Retrieve all shared playbooks data
    # shared_playbooks = list(
    #     sharings_collection.find(
    #         {}, 
    #         {"playbook_id": 1, "shared_versions": 1, "_id": 0}
    #     )
    # )
    
    # # Build a dictionary to map playbook_id to shared versions
    # shared_versions_map = {
    #     pb["playbook_id"]: pb["shared_versions"] for pb in shared_playbooks
    # }
    
    # # Retrieve all playbooks
    # playbooks = list(playbooks_collection.find({}))
    
    # # Filter out playbooks where 'modified' exists in the corresponding shared_versions
    # unshared_playbooks = []
    # for playbook in playbooks:
    #     playbook_id = playbook["id"]
    #     modified_value = playbook["modified"]
        
    #     # Check if the current modified value is in the shared versions
    #     if playbook_id in shared_versions_map:
    #         if modified_value not in shared_versions_map[playbook_id]:
    #             unshared_playbooks.append(playbook)
    #     else:
    #         # If no shared versions exist, consider it as unshared
    #         unshared_playbooks.append(playbook)
    
    # # Convert ObjectId to string for JSON serialization
    # for playbook in unshared_playbooks:
    #     playbook["_id"] = str(playbook["_id"])
    
    # return unshared_playbooks