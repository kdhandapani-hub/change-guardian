"""Normalize actual Postman CLI 1.83 report schema, failing closed on missing assertions."""
from app.core import resolve, report
from app.jenkins import BASE, JOB

EXPECTED_TESTS = {"HTTP 200", "Synthetic response"}

def normalize(plan,raw,build):
    resolved=resolve(plan["environment"],",".join(plan["services"]),plan["suite"])
    if resolved != {k:plan[k] for k in resolved}: raise ValueError("Archived plan differs from registered manifest")
    if not plan.get("change_id"): raise ValueError("Legacy run has no change ID; rerun with updated pipeline")
    if type(build.get("number")) is not int: raise ValueError("Missing build number")
    if build.get("building"): raise ValueError("Build is still running")
    if build.get("result") not in {"SUCCESS","FAILURE","UNSTABLE","ABORTED"}: raise ValueError("Unknown build result")
    run=raw.get("run",{}); executions=run.get("executions",[])
    if not isinstance(executions,list): raise ValueError("Invalid execution list")
    checks=[];seen=set()
    for execution in executions:
        name=execution.get("requestExecuted",{}).get("name")
        if name not in resolved["folders"] or name in seen: raise ValueError("Unexpected or duplicate executed request")
        seen.add(name);tests=execution.get("tests",[])
        names=[t.get("name") for t in tests]
        failed=any(t.get("status")=="failed" for t in tests)
        complete=set(names)==EXPECTED_TESTS and len(names)==len(EXPECTED_TESTS) and all(t.get("status") in {"passed","failed"} for t in tests)
        outcome="failed" if failed else "passed" if complete and not execution.get("errors") else "error"
        checks.append({"id":name,"outcome":outcome,"http_status":execution.get("response",{}).get("code"),
          "response_ms":execution.get("response",{}).get("responseTime"),
          "assertions":[{"name":t.get("name"),"status":t.get("status"),"message":t.get("error",{}).get("message","")[:512]} for t in tests],
          "source":f"{BASE}/job/{JOB}/{build['number']}/artifact/runtime/reports/results.json"})
    fatal=bool(run.get("runError")) or build["result"]=="ABORTED" or plan.get("runner_exit") not in (0,1)
    # A nonzero runner exit or failed Jenkins result cannot become green with all-passing evidence.
    if (plan.get("runner_exit")!=0 or build["result"]!="SUCCESS") and not any(c["outcome"]=="failed" for c in checks): fatal=True
    return {"change_id":plan["change_id"],"environment":plan["environment"],"execution":"error" if fatal else "completed",
      "checks":checks,"mode":"REAL_JENKINS_POSTMAN","build_number":build["number"]}

def build_report(context,plan,raw,build):
    result=report(context,plan,normalize(plan,raw,build))
    result.update(build_number=build["number"],build_url=f"{BASE}/job/{JOB}/{build['number']}/",collection_sha256=plan.get("collection_sha256"))
    result.pop("investigation",None)
    return result
