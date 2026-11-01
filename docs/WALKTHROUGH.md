# Reviewer walkthrough

All services and change records are synthetic. Jenkins/Postman execution, MCP access and model calls in the recorded acceptance runs were real. The app requires its backend, Jenkins and connector to be running; fixture mode is available without credentials.

## No-credentials review

Run `python3 -m app.demo --scenario failure`, then try `missing` and `healthy`. These are labelled fixture runs and make no external calls. Read the C4 architecture and evaluation notes before trying a live deployment.

## Live dashboard flow

1. Sign in using credentials supplied privately by the owner. Never include the password in public submission assets.
2. Load a completed QA verification build. In the validated instance, build 3 shows accounts passed, payments failed with HTTP 500, and positions not tested. Build numbers differ between installations.
3. Try service/status navigation. Filters do not change execution scope or approve actions.
4. Click **Investigate with AI**. For failed/inconclusive evidence, one agent can request selected logs, test summaries and comparable history. Passing selected scopes skip inference while preserving coverage gaps. The model cannot alter the deterministic verdict or trigger a build.
5. Prepare a diagnostic: demo-qa, payments, smoke, reason: check whether HTTP 500 reproduces. This creates a PENDING record without submitting to Jenkins.
6. Review the exact parent build, environment, service and suite, then approve once. The backend atomically claims the request and calls Jenkins MCP triggerBuild using its separate executor identity.
7. Click **Refresh Jenkins status** to reconcile progress. Jenkins is checked on demand; browser background-task polling is a separate mechanism. There is no scheduled Jenkins polling or completion webhook.
8. Expect the synthetic QA diagnostic to fail again. COMPLETED means execution finished, not that tests passed. The request ID and parent build link the diagnostic to its approval; the original verification remains unchanged.
9. Optionally prepare another request and reject it. Rejection must not create a Jenkins build.

## Where each record lives

| System | Record |
|---|---|
| Jenkins | Pipeline execution, console logs, JSON/JUnit artifacts |
| PostgreSQL in cloud mode | Approval ledger, background task records, LangGraph checkpoints |
| LangSmith | Private investigation graph, model/tool spans, timing and token usage |

The model receives evidence only during AI investigation. Ordinary loading, approval and reconciliation use deterministic Python code. Tool results are returned as ToolMessages; LangGraph loops them back to the model. Human approval is an application state machine outside the model loop.

## Code reading order

- `app/jenkins.py`: authenticated MCP session, allowed read tools and REST artifacts.
- `app/evidence.py`: actual Postman schema normalization and completeness checks.
- `app/dashboard.py`: load/investigate/propose/approve/reconcile routes.
- `app/investigate.py`: one bounded reason/tool graph and LangSmith metadata.
- `app/approvals.py`: exact payload, conditional DB claim, triggerBuild and reconciliation.
- `app/database.py` and `app/cloud.py`: PostgreSQL adapter, persistent task records and owner authentication.

See EVALUATION.md for measured acceptance results and limits. Recording should remain under five minutes using DEMO_SCRIPT.md. Saved screenshots are supporting evidence, not substitutes for live access or the required video.
