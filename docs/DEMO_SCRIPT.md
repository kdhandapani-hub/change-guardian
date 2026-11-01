# Five-minute demo recording plan

Target length: 4 minutes 30 seconds. Record synthetic data only; keep Secrets, browser password prompts and personal tabs out of frame.

| Time | Show and explain |
|---|---|
| 0:00–0:35 | Problem: manual post-change verification. State one pipeline, native MCP and one agent; synthetic data. |
| 0:35–1:05 | C4 deployment: Replit app, PostgreSQL, ngrok, private Mac mini/Jenkins/Postman. Explain reader vs executor. |
| 1:05–1:50 | Load mini QA build 3. Show accounts passing, payments failing, positions untested. Use sidebar filters; keep build/environment visible. |
| 1:50–2:35 | Investigate with AI or show the saved completed investigation. Explain actual tool choices, evidence, uncertainty, 2 calls and about 16 seconds observed. |
| 2:35–3:35 | Prepare payments/smoke diagnostic. Show exact parameters; approve one synthetic rerun and refresh status. Show parent/request linkage and original verdict unchanged. Use an existing approved result if recording time is tight and label it accurately. |
| 3:35–4:05 | Explain failure handling: incomplete evidence, model unavailable, budgets, no automatic retry of unknown submissions. Show validation summary. |
| 4:05–4:30 | How Claude/Codex helped, one lesson, scope limits and GitHub/report links. |

Do not say this is an always-on published app, real enterprise integration or statistically proven accuracy. If a live dependency is down, explain that and show clearly labelled saved acceptance evidence; do not pass a fixture off as live execution.

Within the existing five-minute limit, briefly show the LangSmith trace tree after the AI findings: two Fireworks model calls and logs/tests/history tools. Explain that timings/tokens are observed and provider billing is separate. Do not expose secrets or enable public trace sharing.
