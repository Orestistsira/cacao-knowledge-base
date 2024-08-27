import base64
from datetime import datetime, timezone
import json
import uuid

from models.playbook import Playbook
from models.stix import StixPlaybook


def get_current_datetime_str() -> str:
    return datetime.now(timezone.utc).isoformat("T").replace("+00:00", "Z")

def playbook_to_stix(playbook: Playbook) -> StixPlaybook:
    # Generate the ID and filename for the COA object
    coa_id = f"course-of-action--{str(uuid.uuid4())}"

    # Create the STIX 2.1 COA object with Playbook extension
    stix_playbook = create_stix_coa_with_playbook_extension(playbook, coa_id)
    
    return stix_playbook

def create_stix_coa_with_playbook_extension(playbook: Playbook, coa_id: str) -> StixPlaybook:
    return {
        "type": "course-of-action",
        "spec_version": "2.1",
        "id": coa_id,
        "created_by_ref": playbook.created_by,
        "created": get_current_datetime_str(),
        "modified": get_current_datetime_str(),
        "name": "playbook",
        "description": playbook.description,
        "extensions": {
            f"extension-definition--{str(uuid.uuid4())}": {
                "extension_type": "property-extension",
                "playbook_id": playbook.id,
                "created": playbook.created,
                "modified": playbook.modified,
                "playbook_creator": playbook.created_by,
                "revoked": playbook.revoked,
                "labels": playbook.labels,
                "description": playbook.description,
                "playbook_valid_from": playbook.valid_from,
                "playbook_valid_until": playbook.valid_until,
                "playbook_creation_time": playbook.created,
                "playbook_impact": playbook.impact,
                "playbook_severity": playbook.severity,
                "playbook_priority": playbook.priority,
                "playbook_type": playbook.playbook_types,
                "playbook_standard": "cacao",
                "playbook_abstraction": "template",
                "playbook_base64": base64.b64encode(
                    json.dumps(playbook.model_dump(exclude_none=True)).encode()
                ).decode()
            }
        }
    }

def stix_to_playbook(stix_playbook: StixPlaybook) -> Playbook:
    # Extract the extension definition (assuming only one extension is present)
    extensions = stix_playbook.get('extensions')
    extension_key = next(iter(extensions))  # Get the first (and presumably only) extension key
    extension = extensions.get(extension_key, {})

    # Decode the base64 encoded playbook data
    playbook_base64 = extension.get("playbook_base64", "")
    playbook_json = base64.b64decode(playbook_base64).decode('utf-8')
    playbook_data = json.loads(playbook_json)

    # Create and return a Playbook object
    return Playbook(
        type=playbook_data.get("type"),
        spec_version=playbook_data.get("spec_version"),
        id=extension.get("playbook_id"),
        name=stix_playbook.get("name"),
        description=stix_playbook.get("description"),
        playbook_types=extension.get("playbook_type"),
        created_by=extension.get("playbook_creator"),
        created=extension.get("created"),
        modified=extension.get("modified"),
        revoked=extension.get("revoked"),
        valid_from=extension.get("playbook_valid_from"),
        valid_until=extension.get("playbook_valid_until"),
        playbook_processing_summary=None,  # Adjust this if necessary
        derived_from=None,  # Adjust this if necessary
        related_to=None,  # Adjust this if necessary
        priority=extension.get("playbook_priority"),
        severity=extension.get("playbook_severity"),
        impact=extension.get("playbook_impact"),
        industry_sectors=None,  # Adjust this if necessary
        labels=extension.get("labels"),
        external_references=None,  # Adjust this if necessary
        markings=None,  # Adjust this if necessary
        playbook_variables=None,  # Adjust this if necessary
        workflow_start=playbook_data.get("workflow_start"),
        workflow_exception=playbook_data.get("workflow_exception"),
        workflow=playbook_data.get("workflow"),
        playbook_extensions=playbook_data.get("playbook_extensions"),
        authentication_info_definitions=playbook_data.get("authentication_info_definitions"),
        agent_definitions=playbook_data.get("agent_definitions"),
        target_definitions=playbook_data.get("target_definitions"),
        extension_definitions=playbook_data.get("extension_definitions"),
        data_marking_definitions=playbook_data.get("data_marking_definitions"),
        signatures=playbook_data.get("signatures")
    )