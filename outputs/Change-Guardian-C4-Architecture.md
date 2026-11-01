# Change Guardian — C4 architecture, as built

Validated October 31, 2026. Replit workspace preview + PostgreSQL + authenticated ngrok + Mac mini execution. An always-on Replit deployment has not been published. Historical Cloudflare plans are superseded.

## Level 1 — system context

```mermaid
C4Context
  title Change Guardian — System Context
  Person(engineer, "Engineer", "Reviews results and approves diagnostics")
  System(guardian, "Change Guardian", "Verification dashboard and one advisory agent")
  System_Ext(jenkins, "Jenkins on Mac mini", "One Postman verification pipeline and native MCP")
  System_Ext(edge, "ngrok", "Authenticated outbound tunnel; trusted intermediary")
  System_Ext(model, "Fireworks AI", "Tool-calling model inference")
  System_Ext(context, "Synthetic analyser snapshot", "Affected services, change ID and CI mapping")
  Rel(engineer, guardian, "Signs in, filters services, reviews and approves", "HTTPS")
  Rel(guardian, edge, "Authenticated MCP and artifact requests", "HTTPS")
  Rel(jenkins, edge, "Connects outbound through local ngrok agent", "Encrypted tunnel")
  Rel(edge, jenkins, "Relays allowed authenticated requests", "Established tunnel")
  Rel(guardian, model, "Requests advisory investigation", "HTTPS")
  Rel(context, guardian, "Supplies versioned synthetic context", "JSON")
```

## Level 2 — containers

```mermaid
C4Container
  title Change Guardian — Containers and Deployment
  Person(user, "Owner", "Authenticated reviewer")
  System_Boundary(replit, "Replit development workspace") {
    Container(ui, "Dashboard", "HTML / CSS / JavaScript", "Service/status views, evidence and approval review")
    Container(backend, "Backend and one agent", "Python / LangGraph / MCP client", "Evidence gate, investigation and approval executor")
  }
  ContainerDb(db, "Application state", "PostgreSQL", "Approvals, task records and agent checkpoints")
  System_Ext(model, "Fireworks AI", "Inference API")
  System_Ext(edge, "ngrok edge", "Gateway secret and narrow route policy; terminates TLS")
  System_Boundary(mini, "Mac mini — simulated on-premises") {
    Container(connector, "ngrok connector", "User login service", "Initiates outbound encrypted tunnel")
    Container(jenkins, "Jenkins + MCP plugin", "Java", "Scoped identities, one pipeline and artifacts")
    Container(runner, "Test execution", "Postman CLI / Python runner", "Selected environment, services and suite")
    Container(api, "Synthetic APIs", "Python", "Healthy dev and failing QA scenarios")
  }
  Rel(user, ui, "Uses dashboard", "HTTPS owner session")
  Rel(ui, backend, "Reads evidence and submits reviewed actions", "Same-origin HTTP API")
  Rel(backend, db, "Persists state", "PostgreSQL connection")
  Rel(backend, model, "Investigates evidence", "HTTPS")
  Rel(backend, edge, "Uses gateway secret and Jenkins API token", "HTTPS MCP / REST")
  Rel(connector, edge, "Connects outbound", "Encrypted tunnel")
  Rel(edge, connector, "Relays accepted requests", "Established tunnel")
  Rel(connector, jenkins, "Forwards allowed routes", "Loopback HTTP")
  Rel(jenkins, runner, "Runs one parameterized job", "Local execution")
  Rel(runner, api, "Executes selected collection folders", "Local HTTP")
  Rel(runner, jenkins, "Publishes results and provenance", "JSON / JUnit")
```

## Level 3 — backend components

```mermaid
flowchart TD
  HTTP[Owner-authenticated HTTP handler] --> Evidence[Deterministic evidence normalizer]
  HTTP --> Graph[One LangGraph investigation]
  Evidence --> MCP[Scoped MCP client + bounded REST artifacts]
  Graph --> Reason[Model reason node]
  Reason -->|Read tool calls| Tools[Tool node: logs, tests, comparable history]
  Tools --> Reason
  Reason -->|Final answer or budget/error| Advisory[Advisory findings]
  HTTP --> Approval[Exact-payload approval state machine]
  Approval -->|Explicit human approval + atomic claim| Executor[Separate diagnostic executor credential]
  Executor --> MCP
  Approval --> DB[(PostgreSQL / local SQLite)]
  Graph --> Checkpoints[(Persistent LangGraph checkpoints)]
```

Human review is implemented outside the model loop. The model never receives triggerBuild. This is a single-agent design; tool nodes and the approval executor are not additional agents.

## Diagnostic sequence

```mermaid
sequenceDiagram
  actor Owner
  participant App as Replit backend
  participant DB as PostgreSQL
  participant Edge as ngrok
  participant Jenkins as Mac mini Jenkins MCP
  Owner->>App: Prepare selected diagnostic
  App->>DB: Persist exact payload and parent evidence digest
  App-->>Owner: Show scope and reason
  Owner->>App: Approve exact digest
  App->>DB: Atomically claim PENDING as SUBMITTING
  App->>Edge: triggerBuild with gateway + executor credentials
  Note over Edge,Jenkins: Outbound mini tunnel already established
  Edge->>Jenkins: Allowed MCP request; Jenkins checks permissions
  Jenkins-->>App: Queue reference
  App->>DB: Save queue/request ID
  App->>Edge: Read registered-job status
  Edge->>Jenkins: Authenticated read
  Jenkins-->>App: Diagnostic build and parent linkage
  App-->>Owner: Diagnostic outcome; original verdict preserved
```

Uncertain submissions are marked UNKNOWN and only reconciled. The edge, app authentication and Jenkins authorization are independent boundaries. No browser receives gateway, Jenkins or model keys.
