# Tray.io Connector — UI_COMPONENT_PLAN

Per `~/UI_INTERFACE_STANDARD.md` + `concepts/panels.md`. Written BEFORE
panels.py (per NEW_APP_TASK_STANDARD).

## Left sidebar (`panels.py`, slot left, entry `tray_connect`)

- Connect form (only when nothing is connected yet):
  - Label input — its own visible label, placeholder "e.g. Acme production
    workspace" (contextual, never generic).
  - API token input — visible label "API token", placeholder "Paste a Tray
    master or user token".
  - Form stretched to full sidebar width; inner content stretched inside it.
  - Submit via `submit_label` (DUI-correct — the Pipedream DUI lesson:
    no `align=`, no `submit=` on Button, no `hidden=` on Input).
- "How do I set this up?" ghost button → Modal with the 3-step Tray token
  guide. Instructions live ONLY in the modal — never duplicated as static
  sidebar text.
- Connected state: list of saved connections (label + masked token id,
  separated by dividers), no decorated cards.
- "App settings" secondary button, ALWAYS the last element at the bottom.

## Center slot (`panels_settings.py`, entry `tray_settings`)

- Saved connections with masked metadata.
- Disconnect per connection — disconnect lives HERE ONLY, never in the sidebar.
  Uses ui.Form `defaults={"connection_id": ...}` (DUI-correct), not a hidden
  Input.

## Secrets panel

- Standard `secrets` panel entry — shows the declared secret slot exists;
  never echoes values.

## Icon

- Unique `icon.svg`: rounded-square tray gradient (indigo→violet), a
  3-node pipeline with connector dots + a small gear spark. NOT the shared
  677-byte icon (Bitwarden lesson).
