"""Value-add reports: workspace overview + failing-workflows scan over recent
executions."""
from __future__ import annotations

from imperal_sdk import ActionResult

import tray_client as tc
from app import chat
from handlers_connection import resolve_or_error
from handlers_workflows import _items, _wf, _exec
from schemas import (
    FailingWorkflow, FailingWorkflowsReport, OverviewReport, ReportParams,
)


@chat.function(
    "get_workspace_overview",
    "Value-add report: one-glance Tray.io workspace health snapshot -- workflow counts by enabled state, "
    "authentication count, and how many of the most recent executions failed.",
    action_type="read", chain_callable=True, data_model=OverviewReport,
)
async def get_workspace_overview(ctx, params: ReportParams) -> ActionResult:
    """Aggregated workspace snapshot: workflows, authentications, recent execution health."""
    conn, err = await resolve_or_error(ctx, params.connection_id)
    if err:
        return err
    notes: list[str] = []
    try:
        wf_data = await tc.request(conn, "GET", "/workflows", params={"limit": 200})
    except tc.TrayError as exc:
        return ActionResult.error(exc.code, exc.message)
    workflows = [_wf(w) for w in _items(wf_data) if isinstance(w, dict)]
    enabled = sum(1 for w in workflows if w.enabled)
    try:
        auth_data = await tc.request(conn, "GET", "/authentications", params={"limit": 200})
        auths = _items(auth_data) if not isinstance(auth_data, list) else auth_data
        auth_count = len(auths)
    except tc.TrayError:
        auth_count = 0
        notes.append("Authentications endpoint not reachable with this token; count omitted.")
    try:
        ex_data = await tc.request(conn, "GET", "/workflow-instances", params={"limit": params.scan_limit})
        executions = [_exec(e) for e in _items(ex_data) if isinstance(e, dict)]
    except tc.TrayError:
        executions = []
        notes.append("Executions endpoint not reachable with this token; recent failure count omitted.")
    failed = sum(1 for e in executions if (e.status or "").lower() in ("failed", "error", "aborted"))
    return ActionResult.success(OverviewReport(
        label=conn.get("label", "Tray.io workspace"),
        workflows=len(workflows),
        enabled=enabled,
        disabled=len(workflows) - enabled,
        authentications=auth_count,
        executions_scanned=len(executions),
        failed_recent=failed,
        notes=notes,
    ), summary="Workspace overview retrieved.")


@chat.function(
    "get_failing_workflows_report",
    "Value-add report: scan the most recent workflow executions and rank the workflows with the most failures -- "
    "the fastest way to find the automations that keep breaking.",
    action_type="read", chain_callable=True, data_model=FailingWorkflowsReport,
)
async def get_failing_workflows_report(ctx, params: ReportParams) -> ActionResult:
    """Rank workflows by failures within the recent execution window."""
    conn, err = await resolve_or_error(ctx, params.connection_id)
    if err:
        return err
    notes: list[str] = []
    try:
        wf_data = await tc.request(conn, "GET", "/workflows", params={"limit": 200})
        workflows = [_wf(w) for w in _items(wf_data) if isinstance(w, dict)]
    except tc.TrayError as exc:
        return ActionResult.error(exc.code, exc.message)
    try:
        ex_data = await tc.request(conn, "GET", "/workflow-instances", params={"limit": params.scan_limit})
        executions = [_exec(e) for e in _items(ex_data) if isinstance(e, dict)]
    except tc.TrayError as exc:
        return ActionResult.error(exc.code, exc.message)
    if not executions:
        notes.append("No recent executions returned; nothing to rank.")
    names = {w.id: w.name for w in workflows}
    scanned: dict[str, int] = {}
    failed: dict[str, int] = {}
    for e in executions:
        if not e.workflow_id:
            continue
        scanned[e.workflow_id] = scanned.get(e.workflow_id, 0) + 1
        if (e.status or "").lower() in ("failed", "error", "aborted"):
            failed[e.workflow_id] = failed.get(e.workflow_id, 0) + 1
    rows = [
        FailingWorkflow(
            workflow_id=wf_id,
            name=names.get(wf_id, "(deleted or unknown workflow)"),
            failed=n,
            scanned=scanned.get(wf_id, 0),
        )
        for wf_id, n in failed.items() if n > 0
    ]
    rows.sort(key=lambda r: r.failed, reverse=True)
    return ActionResult.success(FailingWorkflowsReport(
        workflows=rows, scanned=len(executions), notes=notes,
    ), summary="Failing workflows report retrieved.")
