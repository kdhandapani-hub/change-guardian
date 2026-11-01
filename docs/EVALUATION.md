# Validation and limits

Acceptance observations from October 31, 2026. Data and endpoints are synthetic; Jenkins/Postman/MCP/Fireworks execution was real.

| Scenario | Evidence / result |
|---|---|
| Healthy all-service verification | Mini #2: 18 assertions passed |
| Selected-service failure | Mini #3: accounts,payments smoke; 3 assertions passed, payments HTTP 200 assertion failed against HTTP 500 |
| Coverage gap | positions affected but not selected; shown NOT_TESTED |
| Approved diagnostic | Mini #4 via SSH and #5 via ngrok: payments/smoke only; parent #3 and unique request IDs; expected failure reproduced |
| Native MCP authorization | Reader attempts to trigger builds denied |
| Gateway protection | No credentials, wrong gateway secret, Jenkins-only and gateway-only requests denied; administration route blocked with both credentials |
| Cloud state | Replit PostgreSQL connectivity, persisted rejected approval, task storage and checkpoint schema verified |
| Cloud inference | Build #3 AI_COMPLETE: 2 model calls, 4,172 reported tokens, 15.65 seconds; logs/tests/history tools |
| Local inference | Same mini build: 2 calls, 4,080 tokens, 13.92 seconds; variability expected |
| Application tests | 31 pass: scope, evidence completeness, skipped tests, provenance, approval duplication/races/expiry, host binding, checkpoint loop and model failures |
| Owner authentication checks | Missing auth/tampered session denied; correct owner accepted; wrong Host and cross-origin writes rejected |

Unit graph tests use scripted model doubles. They do not prove live model quality. Live model calls above are separate acceptance evidence. Mini #1 was a setup seed failure, not a passing acceptance run. Jenkins build IDs are instance-specific.

## Cost, latency and reliability

The selected-scope passing fast path makes zero model calls. Investigation limits are six model calls, 120 seconds, 60 log lines and at most five prior builds. Fireworks retries are disabled; unavailable tools produce explicit error observations. Jenkins has a five-minute timeout and disables concurrent builds. Writes are never automatically retried after ambiguous submission.

Reported token counts and elapsed times are observed values, not billing records. Dollar cost, p50/p95 latency, large-scale concurrency and a statistically meaningful success rate have not been established. No 90% accuracy or production SLA claim is made. The current background task mechanism assumes one server process.

## Known failures and uncertainty

A single synthetic 500 cannot prove root cause or rule out flakiness. Comparable history must match environment, services, suite, change ID and collection revision. A passing run never establishes health for untested affected services. Failure severity and enterprise-wide recent incidents are not inferred by the navigation UI.

Before real organizational use, replace synthetic inventories and CI context, validate assertion schemas, add organizational identity, production network review, durable job workers and broader evaluation.

## Sidebar acceptance checks

Live browser checks against mini build 3 verified Passed → accounts; Failed → payments; Not tested → positions; Needs attention → payments and positions; Recent failures → payments with HTTP 500/assertion detail; positions service selection → one matching row. The original CHECKS_FAILED verdict remained unchanged across filters. A synthetic exact-scope request was captured pending and rejected without execution. Screenshots show the running Replit app.

## LangSmith acceptance

A real Replit investigation of Jenkins build #3 (demo-qa, accounts/payments, smoke) completed with AI_COMPLETE: 2 model calls, 4,154 reported tokens and 19.38 seconds. LangSmith read-back confirmed the completed root run, no root/child errors, two model spans and all three read-tool spans (logs, tests, comparable history), with matching scope metadata. The immutable verdict remained CHECKS_FAILED and positions remained NOT_TESTED.

The LangSmith API returned end_time and error=null; all 11 recorded spans, including the root, had no errors. This acceptance trace was run from the Replit shell against the same backend investigation code and real mini evidence. The managed dashboard workflow was restarted separately with the saved tracing secret enabled. Trace export is not an approval/execution permission or a new agent. Missing automatic Fireworks pricing is not evidence of zero billing.

## Published app validation

On November 1, 2026, the published Reserved VM app passed its public health check (HTTP 200), rejected unauthenticated API access, accepted owner form sign-in with a Secure session cookie, and loaded real Jenkins build #3 through the authenticated mini connection. A production AI investigation completed with AI_COMPLETE in 2 model calls, 4,277 reported tokens and 22.32 seconds. The verdict remained CHECKS_FAILED and positions remained NOT_TESTED. LangSmith read-back confirmed a completed root trace with no root error and nested spans. No diagnostic was approved or triggered during publishing validation.

Published URL: https://change-guardian.replit.app/ . Provider billing is separate from observed token usage.
