"""Authentications tools (classic Platform REST API): list/get saved
third-party credentials the workspace's workflows use. METADATA ONLY --
the API is never asked for, and we never return, credential values."""
from __future__ import annotations

from imperal_sdk import ActionResult

import tray_client as tc
from app import chat
from handlers_connection import resolve_or_error
from schemas import (
    AuthenticationIdParams, AuthenticationList, AuthenticationRecord,
    ListAuthenticationsParams,
)


def _auth(raw: dict) -> AuthenticationRecord:
    service = raw.get("service") or raw.get("service_name") or {}
    if isinstance(service, dict):
        service = service.get("name") or service.get("title")
    return AuthenticationRecord(
        id=str(raw.get("id") or ""),
        name=raw.get("name") or "",
        service=service if isinstance(service, str) else None,
        created=raw.get("created") or raw.get("created_at"),
        raw={k: v for k, v in raw.items() if k not in ("data", "values", "credentials", "secrets")},
    )


@chat.function(
    "list_authentications",
    "List authentications (saved third-party credentials) in the connected Tray.io workspace -- id, name, and "
    "service only, NEVER credential values.",
    action_type="read", chain_callable=True, data_model=AuthenticationList,
)
async def list_authentications(ctx, params: ListAuthenticationsParams) -> ActionResult:
    """List authentications metadata (never secret values)."""
    conn, err = await resolve_or_error(ctx, params.connection_id)
    if err:
        return err
    try:
        data = await tc.request(conn, "GET", "/authentications", params={"limit": params.limit})
    except tc.TrayError as exc:
        return ActionResult.error(exc.code, exc.message)
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        items = data.get("data") or data.get("authentications") or []
    else:
        items = []
    records = [_auth(a) for a in items if isinstance(a, dict)]
    return ActionResult.success(AuthenticationList(authentications=records, count=len(records)), summary="Authentications listed.")


@chat.function(
    "get_authentication",
    "Read one Tray.io authentication's metadata by id -- name, service, created date. Credential values are never "
    "exposed.",
    action_type="read", chain_callable=True, data_model=AuthenticationRecord,
)
async def get_authentication(ctx, params: AuthenticationIdParams) -> ActionResult:
    """Read one authentication's metadata by id."""
    conn, err = await resolve_or_error(ctx, params.connection_id)
    if err:
        return err
    try:
        data = await tc.request(conn, "GET", f"/authentications/{params.authentication_id}")
    except tc.TrayError as exc:
        return ActionResult.error(exc.code, exc.message)
    return ActionResult.success(_auth(data if isinstance(data, dict) else {}), summary="Authentication retrieved.")
