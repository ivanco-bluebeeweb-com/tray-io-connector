"""Pydantic schemas for every Tray.io Connector tool (V17/V18/V23)."""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------- params ----

class ConnectTrayParams(BaseModel):
    label: str = Field(default="", description="A friendly name for this workspace, e.g. 'Acme production'.")
    api_token: str = Field(description="Tray API token (Settings > Tokens in the Tray dashboard -- master or user token).")


class ConnectionIdParams(BaseModel):
    connection_id: str = Field(default="", description="Saved connection id; empty uses the most recent connection.")


class ListWorkflowsParams(BaseModel):
    connection_id: str = Field(default="", description="Saved connection id; empty uses the most recent connection.")
    limit: int = Field(default=50, ge=1, le=200, description="Max workflows to return (1-200).")
    enabled: Optional[bool] = Field(default=None, description="Optional: only enabled (true) or disabled (false) workflows.")


class WorkflowIdParams(BaseModel):
    connection_id: str = Field(default="", description="Saved connection id; empty uses the most recent connection.")
    workflow_id: str = Field(description="Workflow id from list_workflows.")


class CreateWorkflowParams(BaseModel):
    connection_id: str = Field(default="", description="Saved connection id; empty uses the most recent connection.")
    name: str = Field(description="Workflow name.")
    description: str = Field(default="", description="Optional workflow description.")


class UpdateWorkflowParams(BaseModel):
    connection_id: str = Field(default="", description="Saved connection id; empty uses the most recent connection.")
    workflow_id: str = Field(description="Workflow id to update.")
    name: str = Field(default="", description="New name; only given fields change.")
    description: str = Field(default="", description="New description; only given fields change.")


class SetWorkflowEnabledParams(BaseModel):
    connection_id: str = Field(default="", description="Saved connection id; empty uses the most recent connection.")
    workflow_id: str = Field(description="Workflow id to enable/disable.")
    enabled: bool = Field(description="true = enabled, false = disabled.")


class DuplicateWorkflowParams(BaseModel):
    connection_id: str = Field(default="", description="Saved connection id; empty uses the most recent connection.")
    workflow_id: str = Field(description="Workflow id to copy.")
    name: str = Field(default="", description="Name for the copy; default '<original> (copy)'.")


class ListExecutionsParams(BaseModel):
    connection_id: str = Field(default="", description="Saved connection id; empty uses the most recent connection.")
    workflow_id: str = Field(default="", description="Optional: only executions of this workflow.")
    limit: int = Field(default=25, ge=1, le=100, description="Max executions to return (1-100).")


class ExecutionIdParams(BaseModel):
    connection_id: str = Field(default="", description="Saved connection id; empty uses the most recent connection.")
    execution_id: str = Field(description="Execution (instance) id.")
    workflow_id: str = Field(default="", description="Workflow id the execution belongs to (if required by the endpoint).")


class ListAuthenticationsParams(BaseModel):
    connection_id: str = Field(default="", description="Saved connection id; empty uses the most recent connection.")
    limit: int = Field(default=50, ge=1, le=200, description="Max authentications to return (1-200).")


class AuthenticationIdParams(BaseModel):
    connection_id: str = Field(default="", description="Saved connection id; empty uses the most recent connection.")
    authentication_id: str = Field(description="Authentication id from list_authentications.")


class ReportParams(BaseModel):
    connection_id: str = Field(default="", description="Saved connection id; empty uses the most recent connection.")
    window_executions: int = Field(default=100, ge=10, le=300, description="How many recent executions to scan in reports.")


# --------------------------------------------------------------- results ----

class ConnectionRecord(BaseModel):
    id: str
    label: str
    token_masked: str


class ConnectionList(BaseModel):
    connections: list[ConnectionRecord]
    count: int


class ConnectTrayResult(BaseModel):
    connected: bool
    connection_id: str = ""
    label: str = ""
    workflows_seen: int = 0


class WorkflowRecord(BaseModel):
    id: str = ""
    name: str = ""
    enabled: Optional[bool] = None
    created: Optional[str] = None
    last_updated: Optional[str] = None
    description: Optional[str] = None
    raw: Optional[dict] = None


class WorkflowList(BaseModel):
    workflows: list[WorkflowRecord]
    count: int


class ExecutionRecord(BaseModel):
    id: str = ""
    workflow_id: str = ""
    status: str = ""
    created: Optional[str] = None
    finished: Optional[str] = None
    raw: Optional[dict] = None


class ExecutionList(BaseModel):
    executions: list[ExecutionRecord]
    count: int


class AuthenticationRecord(BaseModel):
    id: str = ""
    name: str = ""
    service: Optional[str] = None
    created: Optional[str] = None
    raw: Optional[dict] = None


class AuthenticationList(BaseModel):
    authentications: list[AuthenticationRecord]
    count: int


class DeleteResult(BaseModel):
    deleted: bool
    id: str = ""


class GenericResult(BaseModel):
    ok: bool
    id: str = ""
    detail: Optional[dict] = None


class OverviewReport(BaseModel):
    label: str = ""
    workflows: int = 0
    enabled: int = 0
    disabled: int = 0
    authentications: int = 0
    executions_scanned: int = 0
    failed_recent: int = 0
    notes: list[str] = []


class FailingWorkflow(BaseModel):
    workflow_id: str = ""
    name: str = ""
    failed: int = 0
    scanned: int = 0


class FailingWorkflowsReport(BaseModel):
    workflows: list[FailingWorkflow]
    scanned: int = 0
    notes: list[str] = []
