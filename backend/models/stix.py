from pydantic import BaseModel
from typing import Dict, List

from models.playbook import Timestamp


class PlaybookExtension(BaseModel):
    extension_type: str
    playbook_id: str
    created: Timestamp
    modified: Timestamp
    playbook_creator: str
    revoked: bool | None = None
    labels: List[str] | None = None
    description: str | None = None
    playbook_valid_from: Timestamp | None = None
    playbook_valid_until: Timestamp | None = None
    playbook_creation_time: Timestamp
    playbook_impact: int | None = None
    playbook_severity: int | None = None
    playbook_priority: int | None = None
    playbook_type: List[str] | None = None
    playbook_standard: str
    playbook_abstraction: str
    playbook_base64: str


class StixPlaybookExtensions(BaseModel):
    extension_definition: Dict[str, PlaybookExtension]


class StixPlaybook(BaseModel):
    type: str
    spec_version: str
    id: str
    created_by_ref: str
    created: Timestamp
    modified: Timestamp
    name: str
    description: str | None = None
    extensions: StixPlaybookExtensions

class Envelope(BaseModel):
    more: bool | None = None
    next: str | None = None
    objects: List[StixPlaybook]
