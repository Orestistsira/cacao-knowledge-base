from __future__ import annotations
from datetime import datetime
from typing_extensions import Annotated
from pydantic import BaseModel, Field, model_validator
from typing import List, Dict, Any
from enum import Enum


# Custom timestamp data type
datetime_regex = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$"
Timestamp = Annotated[str, Field(pattern=datetime_regex)]


class Playbook(BaseModel):
    type: str
    spec_version: str
    id: str
    name: str
    description: str | None = None
    playbook_types: List[str] | None = None
    playbook_activities: List[str] | None = None
    playbook_processing_summary: PlaybookProcessingSummary | None = None
    created_by: str
    created: Timestamp
    modified: Timestamp
    revoked: bool | None = None
    valid_from: Timestamp | None = None
    valid_until: Timestamp | None = None
    derived_from: List[str] | None = None
    related_to: List[str] | None = None
    priority: int | None = None
    severity: int | None = None
    impact: int | None = None
    industry_sectors: List[str] | None = None
    labels: List[str] | None = None
    external_references: List[ExternalReference] | None = None
    markings: List[str] | None = None
    playbook_variables: Dict[str, Variable] | None = None
    workflow_start: str
    workflow_exception: str | None = None
    workflow: Dict[str, WorkflowStep] | None = None
    playbook_extensions: Dict[str, Any] | None = None
    authentication_info_definitions: Dict[str, AuthenticationInfo] | None = None
    agent_definitions: Dict[str, AgentTarget] | None = None
    target_definitions: Dict[str, AgentTarget] | None = None
    extension_definitions: Dict[str, ExtensionDefinition] | None = None
    data_marking_definitions: Dict[str, DataMarking] | None = None
    signatures: List[Signature] | None = None

    @model_validator(mode='before')
    def check_timestamps(cls, data: Any) -> Any:
        created = data.get("created")
        modified = data.get("modified")

        # Ensure both fields are provided
        if not created or not modified:
            raise ValueError("Both 'created' and 'modified' timestamps must be provided.")

        # Convert string timestamps to datetime objects
        created_time = datetime.strptime(created, "%Y-%m-%dT%H:%M:%S.%fZ")
        modified_time = datetime.strptime(modified, "%Y-%m-%dT%H:%M:%S.%fZ")

        # Check if 'created' timestamp is older than 'modified' timestamp
        if modified_time < created_time:
            raise ValueError("'created' timestamp must be older than 'modified' timestamp.")

        return data


class PlaybookInDB(Playbook):
    mongo_id: str = Field(..., alias="_id")


class PlaybookMeta(BaseModel):
    spec_version: str
    id: str
    name: str
    description: str | None = None
    playbook_types: List[str] | None = None
    playbook_activities: List[str] | None = None
    playbook_processing_summary: PlaybookProcessingSummary | None = None
    created_by: str
    created: datetime
    modified: datetime
    revoked: bool | None = None
    valid_from: Timestamp | None = None
    valid_until: Timestamp | None = None
    derived_from: List[str] | None = None
    related_to: List[str] | None = None
    priority: int | None = None
    severity: int | None = None
    impact: int | None = None
    industry_sectors: List[str] | None = None
    labels: List[str] | None = None
    external_references: List[ExternalReference] | None = None
    markings: List[str] | None = None
    last_executed: datetime | None = None
    is_active: bool


class ExternalReference(BaseModel):
    name: str
    description: str | None = None
    source: str | None = None
    url: str | None = None
    external_id: str | None = None
    reference_id: str | None = None


class PlaybookProcessingSummary(BaseModel):
    manual_playbook: bool | None = None
    external_playbooks: bool | None = None
    parallel_processing: bool | None = None
    if_logic: bool | None = None
    while_logic: bool | None = None
    switch_logic: bool | None = None
    temporal_logic: bool | None = None
    data_markings: bool | None = None
    digital_signatures: bool | None = None
    countersigned_signature: bool | None = None
    extensions: bool | None = None


class Variable(BaseModel):
    type: str
    description: str | None = None
    value: str | None = None
    constant: bool | None = None
    external: bool | None = None


class WorkflowStepType(str, Enum):
    start = "start"
    end = "end"
    action = "action"
    playbook_action = "playbook-action"
    parallel = "parallel"
    if_condition = "if-condition"
    while_condition = "while-condition"
    switch_condition = "switch-condition"


class Command(BaseModel):
    type: str
    description: str | None = None
    version: str | None = None
    playbook_activity: str | None = None
    external_references: List[ExternalReference] | None = None

    command: str | None = None
    command_b64: str | None = None
    headers: Dict[str, str] | None = None
    content: str | None = None
    content_b64: str | None = None


class WorkflowStep(BaseModel):
    type: WorkflowStepType
    name: str | None = None
    description: str | None = None
    external_references: List[ExternalReference] | None = None
    delay: int | None = None
    timeout: int | None = None
    step_variables: Dict[str, Variable] | None = None
    owner: str | None = None
    on_completion: str | None = None
    on_success: str | None = None
    on_failure: str | None = None
    commands: List[Command] | None = None
    agent: str | None = None
    targets: List[str] | None = None
    in_args: List[str] | None = None
    out_args: List[str] | None = None
    playbook_id: str | None = None
    playbook_version: str | None = None
    next_steps: List[str] | None = None
    condition: str | None = None
    on_true: str | None = None
    on_false: str | None = None
    switch: str | None = None
    cases: Dict[str, str] | None = None
    step_extensions: Dict[str, Any] | None = None


class AuthenticationInfo(BaseModel):
    type: str
    name: str | None = None
    description: str | None = None
    authentication_info_extensions: Dict[str, Any] | None = None

    username: str | None = None
    user_id: str | None = None
    password: str | None = None
    oauth_header: str | None = None
    token: str | None = None
    kms: bool | None = None
    kms_key_identifier: str | None = None
	

class CivicLocation(BaseModel):
    name: str | None = None
    description: str | None = None
    building_details: str | None = None
    network_details: str | None = None
    region: str | None = None
    country: str | None = None
    administrative_area: str | None = None
    city: str | None = None
    street_address: str | None = None
    postal_code: str | None = None
    latitude: str | None = None
    longitude: str | None = None
    precision: str | None = None


class Contact(BaseModel):
    email: Dict[str, str] | None = None
    phone: Dict[str, str] | None = None
    contact_details: str | None = None


class AddressType(str, Enum):
    dname = "dname",
    ipv4 = "ipv4",
    ipv6 = "ipv6",
    l2mac = "l2mac",
    vlan = "vlan",
    url = "url",


class AgentTarget(BaseModel):
    type: str
    name: str
    description: str | None = None
    location: CivicLocation | None = None
    agent_target_extensions: Dict[str, Any] | None = None

    contact: Contact | None = None
    logical: List[str] | None = None
    sector: str | None = None
    address: Dict[AddressType, list[str]] | None = None
    port: str | None = None
    authentication_info: str | None = None
    category: List[str] | None = None


class ExtensionDefinition(BaseModel):
    type: str
    name: str
    description: str | None = None
    created_by: str
    my_schema: str = Field(..., alias="schema")
    version: str
    external_references: List[ExternalReference] | None = None


class DataMarkingType(str, Enum):
    marking_statement = "marking-statement"
    marking_tlp = "marking-tlp"
    marking_iep = "marking-iep"


class DataMarkingTlpLevel(str, Enum):
    tlp_red = "TLP:RED"
    tlp_amber = "TLP:AMBER"
    tlp_amber_strict = "TLP:AMBER+STRICT"
    tlp_green = "TLP:GREEN"
    tlp_clear = "TLP:CLEAR"


class DataMarking(BaseModel):
    type: DataMarkingType
    id: str
    name: str | None = None
    description: str | None = None
    created_by: str
    created: str
    revoked: bool | None = None
    valid_from: Timestamp | None = None
    valid_until: Timestamp | None = None
    labels: List[str] | None = None
    external_references: List[ExternalReference] | None = None
    marking_extensions: Dict[str, Any] | None = None
    statement: str | None = None
    tlpv2_level: DataMarkingTlpLevel | None = None
    tlp: str | None = None
    iep_version: int | None = None
    start_date: Timestamp | None = None
    end_date: Timestamp | None = None
    encrypt_in_transit: str | None = None
    permitted_actions: str | None = None
    affected_party_notifications: str | None = None
    attribution: str | None = None
    unmodified_resale: str | None = None


class Signature(BaseModel):
    type: str
    id: str
    created_by: str | None = None
    created: Timestamp
    modified: Timestamp
    revoked: bool | None = None
    signee: str
    valid_from: Timestamp | None = None
    valid_until: Timestamp | None = None
    related_to: str
    related_version: Timestamp
    hash_algorithm: str
    algorithm: str
    public_key: str | None = None
    public_cert_chain: List[str] | None = None
    cert_url: str | None = None
    thumbprint: str | None = None
    value: str
    signature: Signature | None = None
