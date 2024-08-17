
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class StatusType(str, Enum):
    successfully_executed = "successfully_executed"
    failed = "failed"
    ongoing = "ongoing"
    server_side_error = "server_side_error"
    client_side_error = "client_side_error"
    timeout_error = "timeout_error"
    exception_condition_error = "exception_condition_error"
    await_user_input = "await_user_input"


class Execution(BaseModel):
    playbook_id: str
    execution_id: str
    status: StatusType
    start_time: datetime
    end_time: datetime | None = None
    runtime: float | None = None


class ExecutionInDB(Execution):
    mongo_id: str = Field(..., alias="_id")
