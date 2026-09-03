"""Panel UI -- connect form + connection list, per ~/UI_INTERFACE_STANDARD.md:
every Input has its own visible label + contextual placeholder, the form
stretches full sidebar width with its content stretched inside, and the
"How do I set this up?" text lives ONLY in the help modal (never duplicated
as static sidebar text). The "App settings" button is always LAST.
DUI-correct kwargs: ui.Form submit_label/defaults only (Pipedream lesson)."""
from __future__ import annotations

from imperal_sdk import ui

from app import ext
import handlers_connection as h


def _settings_button() -> ui.UINode:
    return ui.Button(
        "App settings", variant="secondary", size="sm", icon="settings", on_click=ui.Call("__panel__tray_settings"),
    )


def _help_modal() -> ui.UINode:
    return ui.Modal(
        trigger=ui.Button("How do I set this up?", variant="ghost", size="sm"),
        title="Connecting Tray.io",
        children=[
            ui.Text(
                "1. In the Tray dashboard, open Settings > Tokens and create a master token "
                "(org-wide) or use a personal user token.",
                variant="body",
            ),
            ui.Text(
                "2. Paste the token here and connect. We verify it live by listing one workflow "
                "before anything is saved.",
                variant="body",
            ),
            ui.Text(
                "3. The token stays only in this app's secret store -- panels show a masked form, "
                "never the value. Revoke it anytime in the Tray dashboard.",
                variant="body",
            ),
        ],
    )


def _connect_form() -> ui.UINode:
    ui.Button("Authorize Tray.io (OAuth 2.0)", variant="primary", size="sm", icon="login"),
    ui.Divider(),
    ui.Text("Or connect via API Access Token", variant="caption"),
    return ui.Form(
        action="__tool__connect_tray",
        submit_label="Connect Tray.io",
        children=[
            ui.Text("Label", variant="label"),
            ui.Input(param_name="label", placeholder="e.g. Acme production workspace"),
            ui.Text("API token", variant="label"),
            ui.Input(param_name="api_token", placeholder="Paste a Tray master or user token"),
        ],
    )


def _connection_row(c: dict) -> ui.UINode:
    return ui.Stack(direction="v", gap=1, children=[
        ui.Text(c.get("label") or "Tray.io workspace", variant="body"),
        ui.Text(f"token {h._mask(c.get('token', ''))}", variant="caption"),
    ])


def _connections_section(connections: list[dict]) -> ui.UINode:
    if not connections:
        return ui.Text("No Tray.io workspaces connected yet.", variant="caption")
    children: list[ui.UINode] = []
    for i, c in enumerate(connections):
        if i > 0:
            children.append(ui.Divider())
        children.append(_connection_row(c))
    return ui.Stack(direction="v", gap=2, children=children)


@ext.panel("tray_connect", title="Tray.io", slot="left")
async def tray_connect(ctx) -> ui.UINode:
    connections = await h._load_connections(ctx)
    children: list[ui.UINode] = []
    if not connections:
        children.append(_connect_form())
        children.append(_help_modal())
    else:
        children.append(_connections_section(connections))
    children.append(_settings_button())
    return ui.Stack(direction="v", gap=3, children=children)