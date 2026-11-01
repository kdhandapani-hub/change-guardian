# LangSmith investigation tracing

LangSmith is the selected observability platform. Langfuse is not integrated. This records the single investigation graph, its reason/tool steps and model calls; it does not add another agent or grant execution permission.

## Configuration

Set LANGSMITH_API_KEY privately in Replit Secrets. Configure LANGSMITH_TRACING=true, LANGSMITH_PROJECT=change-guardian and the API endpoint for the account region (US: https://api.smith.langchain.com). Set LANGSMITH_WORKSPACE_ID if required by the key. The validated Replit account is agent-based: LANGSMITH_AGENT_ID=change-guardian and LANGSMITH_AGENT_ENVIRONMENT=local (an account routing label also used by the published app; it does not describe the host location). LANGSMITH_PROJECT is a legacy project-workspace setting; agent addressing routes this account. Use your own actual agent/environment in another account. Restart the Guardian workflow after changing environment secrets.

The LangChain/LangGraph integration records nested spans automatically. The graph has an explicit run ID/name and tags: change-guardian, synthetic, read-only-investigation. Scope metadata contains build number, environment, selected services/suite, change ID and collection SHA. The response includes the candidate trace ID when tracing is configured; the ID alone does not prove successful ingestion.

## Data boundary

Traces contain synthetic investigation prompts, model responses and bounded tool evidence, including build logs. Gateway, Jenkins, Fireworks, owner-password and database credentials are not added to trace metadata or tool outputs. Do not put real enterprise or personal data in this demo. Traces remain private in the account; do not publish shared traces without reviewing payloads.

The existing operational controls remain unchanged: deterministic verdict, read-only model tools, human-approved executor, six model-call/120-second investigation budget, explicit unavailable evidence and no automatic retry of uncertain writes.

## Validation status

A real Replit investigation of Jenkins build #3 (demo-qa, accounts/payments, smoke) completed with AI_COMPLETE: 2 model calls, 4,154 reported tokens and 19.38 seconds. LangSmith read-back confirmed the completed root run, no root/child errors, two model spans and all three read-tool spans (logs, tests, comparable history), with matching scope metadata. The immutable verdict remained CHECKS_FAILED and positions remained NOT_TESTED.

Validated October 31, 2026 (America/New_York). Trace ID: `3bff4133-0c2a-468e-9a6b-ce09f0585a37`. Trace access remains private to the LangSmith account; this ID is not a public sharing link. Screenshot: [investigation trace](screenshots/langsmith-trace.png).

## Interpreting metrics

LangSmith supplies trace timings, token usage and errors. Provider billing is authoritative for cost. An OpenAI-compatible Fireworks model may not have automatic pricing configured, so an absent/zero cost field is not evidence of free inference. One trace is acceptance evidence, not a p95 latency or reliability benchmark.

References: https://docs.langchain.com/langsmith/trace-with-langgraph and https://docs.langchain.com/langsmith/create-account-api-key .

## Published app validation

On November 1, 2026, the published Reserved VM app passed its public health check (HTTP 200), rejected unauthenticated API access, accepted owner form sign-in with a Secure session cookie, and loaded real Jenkins build #3 through the authenticated mini connection. A production AI investigation completed with AI_COMPLETE in 2 model calls, 4,277 reported tokens and 22.32 seconds. The verdict remained CHECKS_FAILED and positions remained NOT_TESTED. LangSmith read-back confirmed a completed root trace with no root error and nested spans. No diagnostic was approved or triggered during publishing validation.

Published URL: https://change-guardian.replit.app/ . Provider billing is separate from observed token usage.

## Published trace evidence and cost estimate

The November 1 trace (`263d069b-f68c-42e4-9338-d922da206edf`) is now documented with [the expanded graph](screenshots/langsmith-production-trace.png), [returned JUnit evidence](screenshots/langsmith-tool-result.png), and [investigation history](screenshots/langsmith-runs.png). The graph root took 21.89 seconds; the application measured 22.32 seconds over a wider boundary. The two model spans took 7.55 and 12.79 seconds, with 1,451 and 2,826 tokens respectively. The three read tools took 0.21, 0.16 and 0.64 seconds.

LangSmith displays an estimated $0.0239259 for this trace. This is a platform estimate, not a reconciled Fireworks bill. Do not treat the single-thread summary's P50 as a benchmark for the application. No LangSmith evaluation datasets, judges or experiments have been configured; tracing and application tests do not establish model accuracy scores.
