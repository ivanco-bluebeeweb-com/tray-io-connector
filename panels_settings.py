"""App settings panel (center slot): connection management -- disconnect lives
here ONLY (never in the sidebar), plus a read-only view of saved connection
metadata (never token values). DUI-correct: ui.Form submit_label/defaults."""
from __future__ import annotations

from imperal_sdk import ui

from app import ext
import handlers_connection as h


@ext.panel("tray_settings", title="Tray.io settings", slot="center")
async def tray_settings(ctx) -> ui.UINode:
    conns = await h._load_connections(ctx)
    if not conns:
        return ui.Stack(direction="v", gap=3, children=[
            ui.Text("No Tray.io connections saved yet.", variant="body"),
            ui.Text("Use the left panel to connect a workspace first.", variant="caption"),
        ])

    children: list[ui.UINode] = [
        ui.Text("Saved connections", variant="heading"),
        ui.Text("Token values are never shown here.", variant="caption"),
    ]
    for c in conns:
        label = c.get("label") or "Tray.io workspace"
        children.append(ui.Divider())
        children.append(ui.Stack(direction="v", gap=1, children=[
            ui.Text(label, variant="body"),
            ui.Text(f"token {h._mask(c.get('token', ''))}", variant="caption"),
        ]))
        children.append(ui.Form(
            action="__tool__disconnect_tray",
            submit_label="Disconnect this workspace",
            defaults={"connection_id": c.get("id", "")},
            children=[
                ui.Text("This removes the saved token from Imperal only.", variant="caption"),
            ],
        ))
    return ui.Stack(direction="v", gap=3, children=children)


@ext.panel("tray_secrets", title="Tray.io secrets", slot="right")
async def tray_secrets(ctx) -> ui.UINode:
    conns = await h._load_connections(ctx)
    return ui.Stack(direction="v", gap=2, children=[
        ui.Text("Secret slot: tray_connections", variant="body"),
        ui.Text(f"{len(conns)} connection(s) stored. Values are write-only and never echoed.", variant="caption"),
    ])
