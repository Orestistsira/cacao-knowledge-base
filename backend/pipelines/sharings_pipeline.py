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
