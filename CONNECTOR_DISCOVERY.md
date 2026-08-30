# Tray.io Connector — CONNECTOR_DISCOVERY

Researched 2026-08-30 against tray.ai public docs (developer/getting-started,
developer/platform-apis, developer/embedded-apis) and the community OpenAPI
mirror (api-evangelist/tray-io). Task #2149.

## Product surfaces (there are TWO, pick one)

1. **Classic Tray Platform REST API** — `https://api.tray.io/core/v1`
   - Auth: `Authorization: Bearer <token>`. Token types:
     - **Master token** (org-wide; created in Tray dashboard → Settings → Tokens).
     - **User token** (scoped to one workspace user).
   - Resources: `/workflows`, `/workflows/{id}`, `/workflows/{id}/instances`
     (executions), `/authentications`, workflow import/export.
   - This is the surface every Tray customer has. **SELECTED.**

2. **Embedded / Merlin GraphQL API** — `https://api.tray.io/graphql` (and the
   `/embeddedapi` OpenAPI surface): end-users, solutions, solution instances,
   per-user tokens. Only relevant to Tray *Embedded* customers building
   integrations for THEIR end users — same relationship as Pipedream's Connect
   surface. **OUT OF SCOPE for v0.1.0** (documented as future work).

## Confirmed facts

- Bearer token is a long-lived static token (no refresh flow) — simpler than
  Pipedream's OAuth client_credentials.
- Workflow enable/disable is a property of the workflow (`enabled` flag),
  changed via update.
- Executions (called "instances" in the classic API) are per-workflow run
  records with status (running/succeeded/failed).
- Authentications = saved third-party credentials the workspace's workflows
  use. We never expose their secret values — only id/name/service metadata.
- Import/export round-trips a workflow definition JSON — the cleanest way to
  implement "duplicate workflow" client-side.

## Rate limits / errors (defensive handling)

- Standard HTTP semantics; 401 = bad/expired token, 403 = token lacks scope,
  404 = unknown workflow id, 429 = rate limited (back off with jitter),
  5xx = upstream (retryable, bounded).
- App-declared structured error codes (V32): `TR_AUTH_FAILED`, `TR_FORBIDDEN`,
  `TR_NOT_FOUND`, `TR_RATE_LIMITED`, `TR_UPSTREAM`, `TR_VALIDATION`,
  `TR_NO_CONNECTION`, `TR_UNEXPECTED`.

## Sources

- tray.ai/documentation/developer/getting-started/prerequisites/master-and-user-tokens
- tray.ai/documentation/developer/platform-apis/authentications (`/core/v1/authentications`)
- tray.ai/documentation/developer/embedded-apis/workflows
- developer.tray.io/openapi/embeddedapi/tag/workflows/
- github.com/api-evangelist/tray-io (OpenAPI mirror)
