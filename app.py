"""Extension declaration, secrets, lifecycle hooks.

WHY BYOK: the user's own Tray.io workspace (workflows, executions,
authentications) is managed via their own Tray API token -- nothing is
hosted or proxied by Imperal beyond the request itself.

WHY STATIC BEARER TOKEN, CONFIRMED against tray.ai public docs
(developer/getting-started > master-and-user-tokens) and the community
OpenAPI mirror, 2026-08-30: the classic Tray Platform REST API at
https://api.tray.io/core/v1 authenticates with a long-lived
`Authorization: Bearer <token>` (master token = org-wide, user token =
scoped to one workspace user). No OAuth exchange, no refresh flow --
simpler than Pipedream. The Embedded/Merlin GraphQL surface is a
separate product and out of scope for v0.1.0 (see CONNECTOR_DISCOVERY.md).
"""
from __future__ import annotations

from imperal_sdk import ChatExtension, Extension

ext = Extension(
    "tray-io-connector",
    version="0.1.0",
    display_name="Tray.io",
    icon="icon.svg",
    capabilities=["tray:read", "tray:write"],
    description=(
        "Connect your own Tray.io workspace (classic Platform REST API, static Bearer token) to manage "
        "workflows (list/get/create/update/enable/disable/delete/duplicate), workflow executions, and "
        "authentications (metadata only, never secret values) -- plus workspace health reports."
    ),
)

chat = ChatExtension(ext, tool_name="tray")

ext.secret(
    "tray_connections", "JSON array of saved Tray.io connections (label + API token).",
    required=False, write_mode="extension", max_bytes=65536, rotation_hint_days=365,
)


@ext.health_check
async def health_check(ctx) -> dict:
    """Report connector health: how many saved connections exist (token liveness is verified on use)."""
    from handlers_connection import _load_connections  # local import keeps boot cheap

    conns = await _load_connections(ctx)
    return {"ok": True, "status": "healthy" if conns else "no_connections", "connections": len(conns)}
