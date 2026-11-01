# Reproduce Change Guardian

## 1. Offline fixture walkthrough

From the repository root, Python 3.12 can run `python3 -m app.demo --scenario failure` without credentials. Try `healthy` and `missing` too. These are labelled fixtures, not proof of Jenkins execution.

## 2. Real Postman collection

Install the official Postman CLI and make `postman` available on PATH. Run the synthetic APIs in two terminals:

```sh
python3 demo_services/server.py --port 8091 --scenario healthy
python3 demo_services/server.py --port 8092 --scenario failure
```

Run a real selected collection:

```sh
python3 -m scripts.run_collection --environment demo-qa --services accounts,payments --suite smoke
```

The injected QA payments failure deliberately produces a nonzero exit. Results are written to ignored `runtime/reports/`. Select demo-dev with all/full for a healthy run. No real services or credentials are in this collection.

## 3. Jenkins and MCP

Install Jenkins with a supported Java runtime, Pipeline, JUnit, the MCP Server plugin and an authorization plugin suitable for scoped accounts. Keep it private. Create one Pipeline-from-SCM job named `change-guardian-verification`, pointing at this repository and `jenkins/Jenkinsfile`. The worker needs Python, Postman CLI and access to the synthetic APIs. For a remote worker, update the manifest/environment base URLs deliberately.

Create separate non-admin API identities: a reader with only job/read evidence access and a diagnostic executor with read/build access to the registered job. Do not grant the model administrator or build permissions. Validate attempted reader writes are denied. The local demo configuration helper is optional, expects a private local administrator file and queues a synthetic QA build; read it before use.

```sh
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.lock.txt
cp .env.example .env
```

Supply `GUARDIAN_JENKINS_BASE_URL` and private JSON files with `username` and `token` for GUARDIAN_JENKINS_READER_FILE / WRITER_FILE. Files belong in ignored runtime/. Cloud equivalents are GUARDIAN_JENKINS_READER_JSON / WRITER_JSON in environment secrets. Keep their values out of source.

Set the Fireworks endpoint, an account-available tool-calling model and your private GUARDIAN_MODEL_API_KEY. The tested model is `accounts/fireworks/models/kimi-k3`; availability may vary by account. With a completed provenance-bearing QA build, run `python -m app.live --build <number>`, then `python -m app.dashboard` for loopback access on 8090.

## 4. Replit and private execution host

Import the repository; install `requirements-cloud.txt`. Replit runs `python -m app.cloud` through the Guardian workflow on port 8090. Use a dedicated synthetic execution host for Jenkins/Postman. The demo Mac mini is an example, not a required architecture dependency.

Configure an outbound ngrok connector with a random gateway secret, a fail-closed policy, and only the MCP, registered-job metadata and numbered plan/results artifact paths. Keep admin routes blocked. Set GUARDIAN_GATEWAY_SECRET in Replit Secrets, independent of Jenkins API credentials. ngrok terminates TLS; it is trusted with those dedicated credentials and synthetic payloads. No router forwarding is needed.

Cloud secrets: DATABASE_URL (PostgreSQL), GUARDIAN_APP_PASSWORD (unique 24+ characters), GUARDIAN_GATEWAY_SECRET, Jenkins reader/writer JSON and model API key. During preview the HTTPS origin defaults to REPLIT_DEV_DOMAIN. Before any production publish, set GUARDIAN_PUBLIC_ORIGIN to the exact deployment origin and verify production database/storage and one-instance hosting. Login username in this owner-only demo is `karthik`; choose your own password. /healthz returns only static status, while dashboard/API/evidence routes require authentication.

The workspace preview requires the workspace to keep running. Autoscaling, multi-user production access and always-on deployment are not validated. LangSmith tracing is optional and defaults off.
