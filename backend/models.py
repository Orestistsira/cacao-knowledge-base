from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from datetime import datetime
from enum import Enum


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
    created: datetime
    modified: datetime
    revoked: bool | None = None
    valid_from: datetime | None = None
    valid_until: datetime | None = None
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


class PlaybookInDB(Playbook):
    mongo_id: str = Field(..., alias='_id')


class PlaybookMeta(BaseModel):
    type: str
    spec_version: str
    id: str
    name: str
    description: str | None = None
    playbook_types: List[str] | None = None
    playbook_activities: List[str] | None = None
    playbook_processing_summary: PlaybookProcessingSummary | None = None
    created: datetime
    modified: datetime
    revoked: bool | None = None
    priority: int | None = None
    severity: int | None = None
    impact: int | None = None
    industry_sectors: List[str] | None = None
    labels: List[str] | None = None


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
    start = 'start'
    end = 'end'
    action = 'action'
    playbook_action = 'playbook-action'
    parallel = 'parallel'
    if_condition = 'if-condition'
    while_condition = 'while-condition'
    switch_condition = 'switch-condition'


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
    dname = 'dname',
    ipv4 = 'ipv4',
    ipv6 = 'ipv6',
    l2mac = 'l2mac',
    vlan = 'vlan',
    url = 'url',


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
    my_schema: str = Field(..., alias='schema')
    version: str
    external_references: List[ExternalReference] | None = None


class DataMarkingType(str, Enum):
    marking_statement = 'marking-statement'
    marking_tlp= 'marking-tlp'
    marking_iep = 'marking-iep'


class DataMarking(BaseModel):
    type: DataMarkingType
    id: str
    name: str | None = None
    description: str | None = None
    created_by: str
    created: datetime
    revoked: bool | None = None
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    labels: List[str] | None = None
    external_references: List[ExternalReference] | None = None
    marking_extensions: Dict[str, Any] | None = None


class Signature(BaseModel):
    type: str
    id: str
    created_by: str | None = None
    created: datetime
    modified: datetime
    revoked: bool | None = None
    signee: str
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    related_to: str
    related_version: datetime
    hash_algorithm: str
    algorithm: str
    public_key: str | None = None
    public_cert_chain: List[str] | None = None
    cert_url: str | None = None
    thumbprint: str | None = None
    value: str
    signature: Signature | None = None
