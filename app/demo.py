import argparse, json
from pathlib import Path
from app.core import ROOT, resolve, report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--environment",default="demo-qa")
    p.add_argument("--services",default="accounts,payments")
    p.add_argument("--suite",default="smoke")
    p.add_argument("--scenario",choices=["healthy","failure","missing"],default="failure")
    p.add_argument("--context",default=str(ROOT/"fixtures/analyser-context.json"))
    a=p.parse_args(); plan=resolve(a.environment,a.services,a.suite)
    context=json.loads(Path(a.context).read_text())
    checks=[{"id":x,"outcome":"failed" if a.scenario=="failure" and x.startswith("payments/") else "passed", "source":"synthetic-fixture"} for x in plan["folders"]]
    if a.scenario=="missing": checks=checks[:-1]
    evidence={"change_id":context["change_id"],"environment":a.environment,"execution":"completed","checks":checks,"mode":"SYNTHETIC FIXTURE — no Jenkins or Postman execution"}
    print(json.dumps(report(context,plan,evidence),indent=2))

if __name__=="__main__": main()
