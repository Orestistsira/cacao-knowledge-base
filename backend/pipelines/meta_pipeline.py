meta_pipeline = [
    {
        "$lookup": {
            "from": "executions",
            "localField": "id",
            "foreignField": "playbook_id",
            "as": "executions"
        }
    },
    {
        "$unwind": {
            "path": "$executions",
            "preserveNullAndEmptyArrays": True
        }
    },
    {
        "$sort": {
            "executions.start_time": -1
        }
    },
    {
        "$group": {
            "_id": "$_id",  # Group by the MongoDB ObjectId to retain uniqueness
            "spec_version": {"$first": "$spec_version"},
            "id": {"$first": "$id"},
            "name": {"$first": "$name"},
            "description": {"$first": "$description"},
            "playbook_types": {"$first": "$playbook_types"},
            "playbook_activities": {"$first": "$playbook_activities"},
            "playbook_processing_summary": {"$first": "$playbook_processing_summary"},
            "created_by": {"$first": "$created_by"},
            "created": {"$first": "$created"},
            "modified": {"$first": "$modified"},
            "revoked": {"$first": "$revoked"},
            "valid_from": {"$first": "$valid_from"},
            "valid_until": {"$first": "$valid_until"},
            "derived_from": {"$first": "$derived_from"},
            "related_to": {"$first": "$related_to"},
            "priority": {"$first": "$priority"},
            "severity": {"$first": "$severity"},
            "impact": {"$first": "$impact"},
            "industry_sectors": {"$first": "$industry_sectors"},
            "labels": {"$first": "$labels"},
            "external_references": {"$first": "$external_references"},
            "markings": {"$first": "$markings"},
            "data_marking_definitions": {"$first": "$data_marking_definitions"},
            "last_executed": {"$first": "$executions.start_time"},
            "is_active": {
                "$first": {
                    "$cond": {
                        "if": {"$eq": ["$executions.status", "ongoing"]},
                        "then": True,
                        "else": False
                    }
                }
            }
        }
    },
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
            "last_executed": 1,
            "is_active": 1
        }
    }
]