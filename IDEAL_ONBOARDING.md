# Tray.io Connector — IDEAL_ONBOARDING

The user's first 5 minutes with the app, judged step by step.

## What the user has

A Tray.io workspace and permission to create an API token
(Settings → Tokens in the Tray dashboard — a master token for org-wide
management, or a personal user token).

## Happy path

1. User opens the app → left sidebar shows a connect form: Label, API token.
2. Clicks "How do I set this up?" → modal explains exactly where in the Tray
   dashboard the token is created (Settings → Tokens) and which kind to pick.
3. Pastes token, submits → we verify it LIVE (GET /core/v1/workflows?limit=1)
   before saving anything. Bad token = clear error, nothing stored.
4. Saved connection appears in the sidebar list with a masked token id.
5. From chat: "list my Tray workflows" → works immediately.

## Failure handling

- Invalid/expired token → `TR_AUTH_FAILED`, message says the token was
  rejected by Tray and where to mint a new one. Nothing is saved.
- Token without workflow-read scope → `TR_FORBIDDEN` with a plain-language
  explanation.
- No connection saved yet → every tool answers `TR_NO_CONNECTION` and names
  connect_tray as the next step.

## Trust rules

- Token stored only in the app's secret slot (`tray_connections`); panel
  shows a masked form, never the value.
- Authentications list shows metadata (id/name/service) — NEVER credential
  values.
- Disconnect deletes only the saved record in Imperal; the token itself can
  be revoked in the Tray dashboard by the user at any time.
