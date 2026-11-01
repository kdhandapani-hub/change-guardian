# Architecture decisions — as built

The working system uses one pipeline and one agent. The UI/backend runs in a Replit development workspace; Jenkins, its native MCP Server plugin, Postman CLI and synthetic APIs run on an M4 Mac mini. The mini initiates an ngrok tunnel. Cloudflare was considered earlier and is not the deployed connector.

## Ownership and boundaries

| Component | Owns |
|---|---|
| Jenkins + Postman | Execution and authoritative JSON/JUnit artifacts |
| Evidence normalizer | Collection/change provenance, expected checks, immutable outcomes and coverage |
| One LangGraph agent | Read-only advisory investigation with bounded tools |
| Approval executor | Exact human-approved diagnostic, same pipeline and parent linkage |
| PostgreSQL | Cloud approvals, task records and LangGraph checkpoints |
| Browser | Display and review; never receives service/API secrets |

Three model tools read selected logs, selected test results and comparable prior runs. Build metadata/artifacts are deterministic prerequisite reads. MCP runs inside Jenkins, not in the browser. The native plugin lacks an artifact download tool, so bounded REST reads complement MCP.

The agent uses a reader identity; a separate non-admin executor can start the registered job only through the approval handler. A conditional database update claims a pending request before any write. Unknown submissions are reconciled by request ID rather than automatically retried. The parent verification result is unchanged by diagnostics.

## State and failure handling

Local mode uses SQLite. Cloud mode uses PostgreSQL for approval records, task results and AsyncPostgresSaver checkpoints. Report cache files are disposable. The small background worker is designed for one running process; this is not a production distributed job queue. Restart-interrupted tasks surface as interrupted rather than silently re-executing writes.

Missing, skipped, unexpected or mismatched evidence cannot silently pass. Tool errors become explicit unavailable evidence in the model loop. The model has a six-call/120-second budget and bounded tool results. A missing model key returns MODEL_NOT_CONFIGURED; Jenkins evidence remains available.

## Secure connectivity

A random gateway header is required at ngrok before upstream routing. The edge allowlist permits the native MCP path, registered-job read metadata and numbered plan/results artifacts. Jenkins administration routes remain blocked even with gateway credentials. Jenkins independently verifies API credentials. No router port forwarding is used; the local inspection interface is disabled.

ngrok terminates HTTPS and is trusted with synthetic payloads and dedicated API tokens. This is not end-to-end TLS directly to Jenkins. Owner login uses a signed Secure/HttpOnly/SameSite=Strict cookie; API writes also require the exact origin and CSRF token. Evidence links are served through the authenticated backend.

## UI decisions

Service and status filters operate on the selected build. Overview metrics retain the whole run's context. Needs attention includes failed and unverified services. Recent failures shows failures in the loaded run, not an enterprise incident stream; severity is not classified. This keeps failures and coverage gaps visible without inventing criticality.

See the [C4 diagrams](../outputs/Change-Guardian-C4-Architecture.md). Production publishing, SSO, rate-limited multi-user access and durable worker queues are future work.
