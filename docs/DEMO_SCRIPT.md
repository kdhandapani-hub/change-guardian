# Change Guardian five minute demo walkthrough

Target recording length: 4 minutes 45 seconds, leaving 15 seconds below the five-minute limit. The narration below is approximately 470 words; actions and brief waits are included in the timeline. Rehearse once and trim narration rather than speeding through the approval review.

## Before recording

- Keep the Mac mini signed in and Jenkins, synthetic services and ngrok running. Open the published app at https://change-guardian.replit.app/ and sign in before starting the recording.
- Load build 3 on this validated Jenkins instance. Confirm demo-qa, accounts/payments, smoke; accounts passes, payments fails, positions is not tested. Never assume sample build numbers exist in another installation.
- Open these tabs: published dashboard, repository C4 architecture, private LangSmith Change Guardian tracing page and GitHub README. Keep account/Secrets/password tabs out of the recording.
- Use a wide browser window so the Service health navigation stays on the left. Reset to All services and leave build 3 selected.
- Have a completed, clearly labelled prior diagnostic available as a fallback. If a live dependency is unavailable, say so; do not present cached or fixture evidence as a new live run.
- Record screen and microphone; do not record entering credentials. Use a stopwatch. The owner approves the diagnostic during the recording.

## 0:00 to 0:30 Introduce the problem

Show: dashboard with build 3 loaded.

Say: “I'm Karthik, and this is Change Guardian, my Week 3 agentic AI project. After a maintenance window, an engineer needs to know what passed, what failed, and what was never tested. I built one Jenkins pipeline, native MCP integration, and one LangGraph agent to help investigate those results. All services and enterprise change context in this demo are synthetic.”

## 0:30 to 0:55 Explain the distributed architecture

Show: repository C4 container diagram, then return to dashboard.

Say: “The UI and Python backend run on a Replit Reserved VM, with PostgreSQL for workflow state. Jenkins and Postman run privately on my Mac mini, representing on-premises execution. An authenticated outbound ngrok tunnel connects them. Fireworks provides inference, and LangSmith traces the investigation. The model's Jenkins reader cannot start builds; the approved executor uses separate credentials.”

## 0:55 to 1:35 Load and inspect evidence

Do: enter 3, click Load results; click Failed, then Not tested, then All services.

Say: “This is a real Jenkins and Postman run for demo-qa. Accounts passed, payments returned HTTP 500, and positions was affected by the change but was outside this run's selected scope. Notice that the overall result remains checks failed, and the coverage gap remains visible. The filters only change what I see. They do not change the test scope or turn an untested service green.”

## 1:35 to 2:25 Investigate with AI

Do: click Investigate with AI. While it runs, explain the loop; when complete, show findings and uncertainty. Briefly show the matching new trace in LangSmith if available within the time box.

Say: “Now the agent decides whether it needs logs, test details or comparable history. LangGraph runs the requested Python tools through Jenkins MCP and returns tool messages to the model. The recorded production acceptance run took two model calls and about 22 seconds. Here I check that the report cites the HTTP 500, acknowledges missing positions coverage, and avoids claiming an unsupported root cause. LangSmith makes the model and tool steps inspectable. The AI cannot change the test verdict or trigger a rerun.”

Do not describe 22 seconds as the current run's timing unless the displayed result matches it. If the live call is slow, describe the previously measured value and show the saved acceptance trace as historical evidence.

## 2:25 to 3:40 Review and approve a diagnostic

Do: set payments, smoke, reason “Check whether payments HTTP 500 reproduces.” Click Prepare for approval. Show the PENDING payload and parent 3. Review it, then click Approve once. Click Refresh Jenkins status as needed.

Say: “I prepare a payments smoke diagnostic in the same QA environment. Preparing it only creates a pending database record. I review the exact scope and parent build before approving. The backend atomically claims that request, then triggers the same Jenkins pipeline with a unique request ID. Jenkins does not read PostgreSQL. Refresh Jenkins status checks Jenkins on demand and updates the database. Because the synthetic endpoint deliberately fails, a completed diagnostic may still report FAILURE. Completion describes execution, not test success. The original verification stays unchanged.”

If the diagnostic is still running at 3:25, show its real queued/running state and a previously completed parent-linked diagnostic, explicitly labelled as earlier. Do not claim this new run has finished. Keep the original build 3 report visible for the verdict comparison.

## 3:40 to 4:15 Explain reliability and memory

Show: approval record and LangSmith tree or evaluation table.

Say: “Current messages are the agent's working memory. PostgreSQL retains approvals, task records and graph checkpoints; Jenkins retains execution history. The investigation has call and time limits. Missing evidence stays inconclusive, and an uncertain build submission is reconciled instead of retried automatically. These controls are implemented in code, not just instructions to the model.”

## 4:15 to 4:45 Close with evidence and learning

Show: GitHub README, evaluation and submission links.

Say: “The application has 31 passing tests, plus real Jenkins, Postman, MCP and model acceptance runs. This is a synthetic demo, not an enterprise SLA or a statistical accuracy claim. Claude helped brainstorm the use case, and Codex helped implement and validate it. My main learning was to use the model for investigation while keeping scope, test outcomes and execution authority deterministic. The repository includes the code, collection, pipeline, architecture and reproduction instructions.”

## After recording

Check that the video is no longer than 5:00, audio is clear and no credentials are visible. If you shortened waits, label the edit. Add the recording URL to docs/SUBMISSION.md and the Google Doc; confirm viewer access before submitting the cohort form. Do not include the dashboard password in either public artifact.
