# Tray.io Connector — PREPARATION

Follows `/Users/vladivanco/Documents/Imperal OS/Docs/session-notes/NEW_APP_TASK_STANDARD.md`
(same split-handler layout as Pipedream/Bitwarden). Task #2149.

## Layout

- `app.py` — Extension decl (`tray-io-connector`), `chat` ChatExtension, secret
  `tray_connections`, health check.
- `main.py` — sys.path setup, module-cache purge, imports ext/chat + handlers + panels.
- `tray_client.py` — Bearer-token client, `https://api.tray.io/core/v1`,
  typed `TrayError`, 429/5xx bounded retry with jitter.
- `schemas.py` — Pydantic params + result models for every tool.
- `handlers_connection.py` — connect (verify token via GET /workflows?limit=1),
  list_connections, disconnect_tray, resolve helpers.
- `handlers_workflows.py` — list/get/create/update/enable/disable/delete,
  list executions (instances).
- `handlers_authentications.py` — list/get authentications (metadata only,
  never secret values).
- `handlers_reports.py` — get_workspace_overview, get_failing_workflows_report.
- `panels.py` (left sidebar connect form + connections), `panels_settings.py`
  (center slot, disconnect only here), unique `icon.svg` (tray/pipeline motif,
  NOT the shared 677-byte icon — Bitwarden lesson).
- `imperal.json` via `imperal build`; `tool-prices.json` BEFORE deploy;
  `requirements.txt`, `.gitignore` (no __pycache__/.pyc committed).

## Tool inventory (target ~20 functions)

Connection: connect_tray, list_connections, disconnect_tray
Workflows: list_workflows, get_workflow, create_workflow, update_workflow,
  set_workflow_enabled, delete_workflow, duplicate_workflow (export+import),
  list_workflow_executions, get_workflow_execution
Authentications: list_authentications, get_authentication
Reports: get_workspace_overview, get_failing_workflows_report

## Pricing plan (before deploy — standing rule)

0: connect/list_connections/disconnect · 8: list/get reads · 16: create/update/
  enable/duplicate · 24: deletes + failing-workflows report · 40: workspace
  overview.
