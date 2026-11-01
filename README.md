# Change Guardian — Week 3 Agentic AI Project

Post-change verification with **one Jenkins pipeline, native Jenkins MCP, and one bounded LangGraph agent**. All services, changes and enterprise-analyser context are synthetic.

Change Guardian helps an engineer review health/smoke/regression results, identify affected services that were not tested, investigate failures, and explicitly approve a diagnostic rerun. Jenkins owns the test outcome; the model supplies advisory findings.

![Cloud dashboard](docs/screenshots/dashboard.png)

## What is implemented

- One parameterized pipeline selects environment (`demo-dev` / `demo-qa`), services (`all` or a comma-separated subset), and suite (`health`, `smoke`, `regression`, `full`).
- Real Postman CLI execution, JUnit assertions, detailed JSON and collection/change provenance.
- Native Jenkins MCP reads for build metadata, test summaries and logs; authenticated REST downloads archived evidence.
- Deterministic verdict and coverage gaps. Untested services never become healthy because another service passed.
- One LangGraph reason/tool loop with three read-only investigation tools, persistent checkpoints, six-call and 120-second budgets. Selected-scope passing runs skip the model; coverage gaps remain visible.
- Exact-payload approval ledger: preview, approve/reject, atomic submission claim, request-ID reconciliation, and no automatic retry of uncertain writes.
- Owner-only dashboard, service/status navigation, and evidence-based failure details. Navigation filters the loaded run; it does not change execution scope or assign severity.

## Architecture

```mermaid
flowchart LR
  User[Engineer] -->|HTTPS owner login| App[Replit UI + backend + one agent]
  App <--> DB[(PostgreSQL state)]
  App -->|Inference| Model[Fireworks AI]
  App -.->|Investigation traces| Tracing[LangSmith]
  App -->|Gateway secret + Jenkins API auth| Edge[ngrok HTTPS edge]
  Mini[ngrok connector on Mac mini] -->|Outbound encrypted connection| Edge
  Edge -->|Established tunnel| Mini
  Mini -->|Loopback| Jenkins[Jenkins + native MCP plugin]
  Jenkins --> Runner[One pipeline + Postman CLI]
  Runner --> APIs[Synthetic service APIs]
```

[C4 diagrams](outputs/Change-Guardian-C4-Architecture.md) · [Architecture decisions](docs/ARCHITECTURE.md) · [Setup](docs/SETUP.md) · [Validation](docs/EVALUATION.md) · [Walkthrough](docs/WALKTHROUGH.md) · [Five-minute demo script](docs/DEMO_SCRIPT.md)

The app is published at **https://change-guardian.replit.app/** on a Replit Reserved VM. Owner sign-in is required; credentials are supplied privately. The Mac mini simulates on-premises execution. No production organization systems are connected. ngrok is a trusted TLS-terminating intermediary; gateway and Jenkins authentication are independent.

## Quick start: no credentials required

Python 3.12 is recommended. The fixture demo uses the standard library:

```sh
python3 -m app.demo --scenario failure
python3 -m app.demo --scenario missing
python3 -m app.demo --scenario healthy
```

Fixture mode is explicitly labelled and makes no Jenkins, Postman or model calls. The healthy selected scope can still show an untested affected service.

For application tests and live integrations:

```sh
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.lock.txt
.venv/bin/python -m unittest discover -s tests -v
cp .env.example .env
```

Set credentials locally as described in [SETUP](docs/SETUP.md), then run:

```sh
.venv/bin/python -m app.live --build <your-completed-build-number>
.venv/bin/python -m app.dashboard
```

Local dashboard: `http://127.0.0.1:8090/`. Build numbers belong to their Jenkins instance; sample IDs in validation notes are not portable. Cloud mode uses `requirements-cloud.txt` and `python -m app.cloud`, requires PostgreSQL and an owner password, and supports Replit Secrets. Never commit `.env`, runtime files, API tokens, or passwords.

## Observed results

| Acceptance run | Observed result |
|---|---|
| Mini build 2: dev / all / full | 18 assertions passed |
| Mini build 3: QA / accounts,payments / smoke | 3 assertions passed, 1 intentionally failed; positions NOT_TESTED |
| Mini build 5: approved payments diagnostic, parent 3 | Expected failure reproduced; request ID linked |
| LangSmith persisted trace, build 3 | 2 model spans + 3 read tools; 4,154 tokens; 19.38 seconds; no trace errors |
| Fireworks investigation from Replit, build 3 | AI_COMPLETE; 2 calls, 4,172 reported tokens, 15.65 seconds |
| Published app investigation, November 1 | AI_COMPLETE; 2 calls, 4,277 tokens, 22.32 seconds; health/login/Jenkins access verified |
| Application tests | 31 passing tests; model doubles are separate from live inference |

These are individual acceptance observations, not a statistical reliability benchmark. Provider-billed dollar cost and p95 latency were not measured. The LangSmith estimate below is separate from provider billing. [Full evaluation and limitations](docs/EVALUATION.md).

## Walk through the evidence

These are captures of the working app and actual LangSmith traces using synthetic data. Click an image for a larger view.

| Review a failure | Review a diagnostic request |
|---|---|
| ![Payments failure detail](docs/screenshots/failure-detail.png) | ![Human approval review](docs/screenshots/approval-review.png) |
| Payments returned HTTP 500; the assertion evidence explains the deterministic failure. | Exact environment, service, suite and parent build are shown before approval. This pictured request was rejected without execution. |

### LangSmith: see the agent's decisions and evidence

Clicking **Investigate with AI** starts the traced graph. The model first receives the selected run context, chooses from three read-only tools, receives their results as tool messages, and then writes its advisory findings. Jenkins execution is a separate, human-approved application action; this trace does not grant the model a build-trigger tool.

![Published investigation with two model calls and three tools](docs/screenshots/langsmith-production-trace.png)

The November 1 published-app investigation shows the two model calls around the tool step. LangSmith labels the OpenAI-compatible client span `ChatOpenAI`; inference is served by **Fireworks AI**.

| Measurement from this investigation | Observed value |
|---|---|
| Model calls / reported tokens | 2 / 4,277 |
| LangSmith graph duration | 21.89 seconds |
| Application-reported investigation duration | 22.32 seconds (a wider measurement boundary) |
| Model span durations | 7.55 and 12.79 seconds |
| Read-tool durations: logs / test results / comparable history | 0.21 / 0.16 / 0.64 seconds |
| LangSmith estimated model cost | $0.02393; an estimate, not a reconciled Fireworks bill |

![JUnit result returned by the read-only tool](docs/screenshots/langsmith-tool-result.png)

The selected tool result reports four assertions and one failure. The second model call receives this evidence before producing findings; the model cannot replace the test verdict or mark the untested positions service healthy.

<details>
<summary>More trace evidence: investigation history and earlier preview run</summary>

![Investigation trace history](docs/screenshots/langsmith-runs.png)

The history helps locate investigations and compare individual executions. A completed trace alone does not prove a correct answer or successful diagnostic run.

![Earlier workspace investigation trace](docs/screenshots/langsmith-trace.png)

</details>

LangSmith is used for **tracing**, with prompts, responses, tool evidence, tokens and timing. No LangSmith evaluation dataset, judge or experiment scores have been configured. The 31 application tests are a separate validation layer. These individual runs do not establish statistical accuracy, reliability or p95 latency. See [observability and data boundaries](docs/OBSERVABILITY.md) and [evaluation coverage](docs/EVALUATION.md).

## Scope and limitations

No A2A, additional specialist agents, automated remediation, Slack/Jira writes, real ServiceNow integration, or severity classifier. The normalizer expects this synthetic collection's versioned test inventory. Human approval is an application state machine, not a claim that LangGraph `interrupt()` was implemented. Interactive checkpoint resume, production SSO, durable background job workers, and broader evaluation remain future work. LangSmith records the Replit investigation graph, model calls and read tools. Local tracing defaults off; see [observability](docs/OBSERVABILITY.md). Local SQLite and cloud PostgreSQL are alternate state backends.
