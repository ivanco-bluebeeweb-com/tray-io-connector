"""Connection lifecycle: connect (verify token against GET /workflows?limit=1),
list, disconnect, and shared connection resolution helpers."""
from __future__ import annotations

import json
import uuid

from imperal_sdk import ActionResult

import tray_client as tc
from app import chat
from schemas import (
    ConnectTrayParams, ConnectTrayResult, ConnectionIdParams,
    ConnectionList, ConnectionRecord, DeleteResult,
)

_SECRET = "tray_connections"


def _mask(token: str) -> str:
    return token[:4] + "…" + token[-4:] if len(token) > 10 else "***"


async def _load_connections(ctx) -> list[dict]:
    raw = await ctx.secrets.get(_SECRET)
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except (TypeError, ValueError):
        return []
    return data if isinstance(data, list) else []


async def _save_connections(ctx, conns: list[dict]) -> None:
    await ctx.secrets.set(_SECRET, json.dumps(conns))


async def resolve_connection(ctx, connection_id: str = "") -> dict | None:
    conns = await _load_connections(ctx)
    if not conns:
        return None
    if connection_id:
        return next((c for c in conns if c.get("id") == connection_id), None)
    return conns[0]


async def resolve_or_error(ctx, connection_id: str = ""):
    conn = await resolve_connection(ctx, connection_id)
    if not conn:
        return None, ActionResult.error(
            tc.TR_NO_CONNECTION,
            "No Tray.io connection saved (or unknown connection_id) — run connect_tray first.",
        )
    return conn, None


@chat.function(
    "connect_tray",
    "Connect a Tray.io workspace by saving its API token (Settings > Tokens in the Tray dashboard -- master or "
    "user token), after checking it actually works against GET /workflows.",
    action_type="write",
    chain_callable=True,
    data_model=ConnectTrayResult,
    event="tray-io-connector.connection.created",
    effects=["tray.connection.created"],
)
async def connect_tray(ctx, params: ConnectTrayParams) -> ActionResult:
    """Verify the token live (list one workflow), then save the connection."""
    token = params.api_token.strip()
    try:
        data = await tc.request({"token": token}, "GET", "/workflows", params={"limit": 1})
    except tc.TrayError as exc:
        return ActionResult.error(exc.code, f"Connection NOT saved: {exc.message}")
    wf_count = 0
    if isinstance(data, list):
        wf_count = len(data)
    elif isinstance(data, dict):
        wf_count = len(data.get("data") or data.get("workflows") or [])

    conns = await _load_connections(ctx)
    label = (params.label or "Tray.io workspace").strip()
    if any(c.get("token") == token for c in conns):
        return ActionResult.error(tc.TR_VALIDATION, "A connection with this token already exists.")
    record = {
        "id": f"tray_{uuid.uuid4().hex[:12]}",
        "label": label,
        "token": token,
    }
    conns.append(record)
    await _save_connections(ctx, conns)
    return ActionResult.ok(ConnectTrayResult(
        connected=True, connection_id=record["id"], label=label, workflows_seen=wf_count,
    ))


@chat.function(
    "list_connections",
    "List the connected Tray.io workspaces (masked token ids; secret values are never shown).",
    action_type="read",
    chain_callable=True,
    data_model=ConnectionList,
)
async def list_connections(ctx, params: ConnectionIdParams) -> ActionResult:
    """List saved Tray.io connections without exposing tokens."""
    conns = await _load_connections(ctx)
    records = [
        ConnectionRecord(id=c["id"], label=c.get("label", "Tray.io workspace"), token_masked=_mask(c.get("token", "")))
        for c in conns
    ]
    return ActionResult.ok(ConnectionList(connections=records, count=len(records)))


@chat.function(
    "disconnect_tray",
    "Disconnect a Tray.io workspace: deletes the saved API token from Imperal. Nothing in Tray itself is changed; "
    "the token can be revoked in the Tray dashboard at any time.",
    action_type="write",
    chain_callable=True,
    data_model=DeleteResult,
    event="tray-io-connector.connection.deleted",
    effects=["tray.connection.deleted"],
)
async def disconnect_tray(ctx, params: ConnectionIdParams) -> ActionResult:
    """Delete a saved Tray connection by id; nothing in Tray itself changes."""
    conns = await _load_connections(ctx)
    if not conns:
        return ActionResult.error(tc.TR_NO_CONNECTION, "No Tray.io connections saved.")
    target_id = params.connection_id or conns[0]["id"]
    remaining = [c for c in conns if c.get("id") != target_id]
    if len(remaining) == len(conns):
        return ActionResult.error(tc.TR_NOT_FOUND, f"No saved connection with id '{target_id}'.")
    await _save_connections(ctx, remaining)
    return ActionResult.ok(DeleteResult(deleted=True, id=target_id))
