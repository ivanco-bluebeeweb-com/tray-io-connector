"""Workflow tools (classic Platform REST API): CRUD, enable/disable, duplicate,
and execution (instance) reads."""
from __future__ import annotations

from imperal_sdk import ActionResult

import tray_client as tc
from app import chat
from handlers_connection import resolve_or_error
from schemas import (
    CreateWorkflowParams, DeleteResult, DuplicateWorkflowParams,
    ExecutionIdParams, ExecutionList, ExecutionRecord,
    ListExecutionsParams, ListWorkflowsParams, SetWorkflowEnabledParams,
    UpdateWorkflowParams, WorkflowIdParams, WorkflowList, WorkflowRecord,
)


def _wf(raw: dict) -> WorkflowRecord:
    return WorkflowRecord(
        id=str(raw.get("id") or raw.get("workflow_id") or ""),
        name=raw.get("name") or "",
        enabled=raw.get("enabled"),
        created=raw.get("created") or raw.get("created_at"),
        last_updated=raw.get("last_updated") or raw.get("updated_at"),
        description=raw.get("description"),
        raw=raw,
    )


def _exec(raw: dict) -> ExecutionRecord:
    return ExecutionRecord(
        id=str(raw.get("id") or ""),
        workflow_id=str(raw.get("workflow_id") or ""),
        status=raw.get("status") or "",
        created=raw.get("created") or raw.get("created_at"),
        finished=raw.get("finished") or raw.get("finished_at"),
        raw=raw,
    )


def _items(data) -> list:
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get("data") or data.get("workflows") or data.get("instances") or data.get("executions") or []
    return []


@chat.function(
    "list_workflows",
    "List workflows in the connected Tray.io workspace, optionally filtered by enabled state.",
    action_type="read", chain_callable=True, data_model=WorkflowList,
)
async def list_workflows(ctx, params: ListWorkflowsParams) -> ActionResult:
    """List workflows (optionally only enabled/disabled)."""
    conn, err = await resolve_or_error(ctx, params.connection_id)
    if err:
        return err
    try:
        data = await tc.request(conn, "GET", "/workflows", params={"limit": params.limit})
    except tc.TrayError as exc:
        return ActionResult.error(exc.code, exc.message)
    items = [w for w in (_wf(r) for r in _items(data) if isinstance(r, dict))
             if params.enabled is None or w.enabled == params.enabled]
    return ActionResult.success(WorkflowList(workflows=items, count=len(items)), summary="Workflows listed.")


@chat.function(
    "get_workflow",
    "Read one Tray.io workflow in full by id.",
    action_type="read", chain_callable=True, data_model=WorkflowRecord,
)
async def get_workflow(ctx, params: WorkflowIdParams) -> ActionResult:
    """Read one workflow by id."""
    conn, err = await resolve_or_error(ctx, params.connection_id)
    if err:
        return err
    try:
        data = await tc.request(conn, "GET", f"/workflows/{params.workflow_id}")
    except tc.TrayError as exc:
        return ActionResult.error(exc.code, exc.message)
    return ActionResult.success(_wf(data if isinstance(data, dict) else {}), summary="Workflow retrieved.")


@chat.function(
    "create_workflow",
    "Create a new Tray.io workflow (name + optional description).",
    action_type="write", chain_callable=True, data_model=WorkflowRecord,
    event="tray-io-connector.workflow.created", effects=["tray.workflow.created"],
)
async def create_workflow(ctx, params: CreateWorkflowParams) -> ActionResult:
    """Create a workflow."""
    conn, err = await resolve_or_error(ctx, params.connection_id)
    if err:
        return err
    body: dict = {"name": params.name.strip()}
    if params.description:
        body["description"] = params.description
    try:
        data = await tc.request(conn, "POST", "/workflows", json_body=body)
    except tc.TrayError as exc:
        return ActionResult.error(exc.code, exc.message)
    return ActionResult.success(_wf(data if isinstance(data, dict) else {}), summary="Workflow created.")


@chat.function(
    "update_workflow",
    "Update selected fields of an existing Tray.io workflow (name/description). Only given fields change.",
    action_type="write", chain_callable=True, data_model=WorkflowRecord,
    event="tray-io-connector.workflow.updated", effects=["tray.workflow.updated"],
)
async def update_workflow(ctx, params: UpdateWorkflowParams) -> ActionResult:
    """Update a workflow's name and/or description."""
    conn, err = await resolve_or_error(ctx, params.connection_id)
    if err:
        return err
    body: dict = {}
    if params.name:
        body["name"] = params.name
    if params.description:
        body["description"] = params.description
    if not body:
        return ActionResult.error(tc.TR_VALIDATION, "Nothing to update: pass name and/or description.")
    try:
        data = await tc.request(conn, "PATCH", f"/workflows/{params.workflow_id}", json_body=body)
    except tc.TrayError as exc:
        return ActionResult.error(exc.code, exc.message)
    return ActionResult.success(_wf(data if isinstance(data, dict) else {}), summary="Workflow updated.")


@chat.function(
    "set_workflow_enabled",
    "Enable or disable a Tray.io workflow without deleting it.",
    action_type="write", chain_callable=True, data_model=WorkflowRecord,
    event="tray-io-connector.workflow.toggled", effects=["tray.workflow.toggled"],
)
async def set_workflow_enabled(ctx, params: SetWorkflowEnabledParams) -> ActionResult:
    """Set the workflow's enabled flag."""
    conn, err = await resolve_or_error(ctx, params.connection_id)
    if err:
        return err
    try:
        data = await tc.request(
            conn, "PATCH", f"/workflows/{params.workflow_id}", json_body={"enabled": params.enabled},
        )
    except tc.TrayError as exc:
        return ActionResult.error(exc.code, exc.message)
    return ActionResult.success(_wf(data if isinstance(data, dict) else {}), summary="Workflow enabled updated.")


@chat.function(
    "duplicate_workflow",
    "Duplicate a Tray.io workflow by exporting its definition and re-importing it under a new name.",
    action_type="write", chain_callable=True, data_model=WorkflowRecord,
    event="tray-io-connector.workflow.duplicated", effects=["tray.workflow.duplicated"],
)
async def duplicate_workflow(ctx, params: DuplicateWorkflowParams) -> ActionResult:
    """Export a workflow's definition and re-import it as a copy."""
    conn, err = await resolve_or_error(ctx, params.connection_id)
    if err:
        return err
    try:
        original = await tc.request(conn, "GET", f"/workflows/{params.workflow_id}")
    except tc.TrayError as exc:
        return ActionResult.error(exc.code, exc.message)
    if not isinstance(original, dict):
        return ActionResult.error(tc.TR_UNEXPECTED, "unexpected workflow payload from Tray API")
    src_name = original.get("name") or "Workflow"
    new_name = (params.name or f"{src_name} (copy)").strip()
    definition = {k: v for k, v in original.items()
                  if k not in ("id", "created", "last_updated", "created_at", "updated_at", "creator")}
    definition["name"] = new_name
    try:
        created = await tc.request(conn, "POST", "/workflows", json_body=definition)
    except tc.TrayError as exc:
        return ActionResult.error(exc.code, exc.message)
    return ActionResult.success(_wf(created if isinstance(created, dict) else {}), summary="Duplicate workflow done.")


@chat.function(
    "delete_workflow",
    "Permanently delete a Tray.io workflow by id. Cannot be undone.",
    action_type="write", chain_callable=True, data_model=DeleteResult,
    event="tray-io-connector.workflow.deleted", effects=["tray.workflow.deleted"],
)
async def delete_workflow(ctx, params: WorkflowIdParams) -> ActionResult:
    """Permanently delete a workflow."""
    conn, err = await resolve_or_error(ctx, params.connection_id)
    if err:
        return err
    try:
        await tc.request(conn, "DELETE", f"/workflows/{params.workflow_id}")
    except tc.TrayError as exc:
        return ActionResult.error(exc.code, exc.message)
    return ActionResult.success(DeleteResult(deleted=True, id=params.workflow_id), summary="Workflow deleted.")


@chat.function(
    "list_workflow_executions",
    "List workflow executions (instances), newest first -- optionally restricted to one workflow.",
    action_type="read", chain_callable=True, data_model=ExecutionList,
)
async def list_workflow_executions(ctx, params: ListExecutionsParams) -> ActionResult:
    """List executions across the workspace or for one workflow."""
    conn, err = await resolve_or_error(ctx, params.connection_id)
    if err:
        return err
    if params.workflow_id:
        path = f"/workflows/{params.workflow_id}/instances"
        q: dict = {"limit": params.limit}
    else:
        path = "/workflow-instances"
        q = {"limit": params.limit}
    try:
        data = await tc.request(conn, "GET", path, params=q)
    except tc.TrayError as exc:
        return ActionResult.error(exc.code, exc.message)
    items = [_exec(r) for r in _items(data) if isinstance(r, dict)]
    return ActionResult.success(ExecutionList(executions=items, count=len(items)), summary="Workflow executions listed.")


@chat.function(
    "get_workflow_execution",
    "Read one workflow execution (instance) in full by id -- status, timing, and any error info.",
    action_type="read", chain_callable=True, data_model=ExecutionRecord,
)
async def get_workflow_execution(ctx, params: ExecutionIdParams) -> ActionResult:
    """Read one execution by id."""
    conn, err = await resolve_or_error(ctx, params.connection_id)
    if err:
        return err
    path = f"/workflow-instances/{params.execution_id}"
    try:
        data = await tc.request(conn, "GET", path)
    except tc.TrayError as exc:
        return ActionResult.error(exc.code, exc.message)
    return ActionResult.success(_exec(data if isinstance(data, dict) else {}), summary="Workflow execution retrieved.")
