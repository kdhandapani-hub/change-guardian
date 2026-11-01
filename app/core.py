import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def load_manifest():
    return json.loads((ROOT / "config/manifest.json").read_text())

def resolve(environment, services, suite):
    m = load_manifest()
    if environment not in m["environments"] or suite not in m["suites"] + ["full"]:
        raise ValueError("Unknown environment or suite")
    selected = [x.strip() for x in services.split(",")]
    if not selected or any(not x for x in selected):
        raise ValueError("Select at least one service")
    if "all" in selected:
        if len(selected) != 1:
            raise ValueError("Do not combine all with service IDs")
        selected = m["services"][:]
    selected = list(dict.fromkeys(selected))
    if set(selected) - set(m["services"]):
        raise ValueError("Unknown service")
    suites = m["suites"] if suite == "full" else [suite]
    return {"environment": environment, "services": selected, "suite": suite,
            "base_url": m["environments"][environment],
            "folders": [s + "/" + t for s in selected for t in suites]}

def report(context, plan, evidence):
    registered = set(load_manifest()["services"])
    affected = context["affected_services"]
    if len(affected) != len(set(affected)) or set(affected) - registered:
        raise ValueError("Invalid analyser service mapping")
    if context["environment"] != plan["environment"]:
        raise ValueError("Analyser and run environments differ")
    if evidence["environment"] != plan["environment"] or evidence["change_id"] != context["change_id"]:
        raise ValueError("Evidence belongs to another environment or change")
    observations = evidence["checks"]
    ids = [x["id"] for x in observations]
    if len(ids) != len(set(ids)) or set(ids) - set(plan["folders"]):
        raise ValueError("Duplicate or out-of-scope evidence")
    if any(x["outcome"] not in ("passed", "failed", "error", "skipped") for x in observations):
        raise ValueError("Invalid check outcome")
    by_id = {x["id"]: x for x in observations}
    rows = []
    for service in sorted(set(affected) | set(plan["services"])):
        expected = [x for x in plan["folders"] if x.startswith(service + "/")]
        actual = [by_id[x] for x in expected if x in by_id]
        failed = any(x["outcome"] == "failed" for x in actual)
        complete = len(actual) == len(expected) and all(x["outcome"] in ("passed", "failed") for x in actual)
        status = "NOT_TESTED" if not expected else "CHECKS_FAILED" if failed else "CHECKS_PASSED" if complete and evidence["execution"] == "completed" else "INCONCLUSIVE"
        rows.append({"service_id":service,"affected":service in affected,"status":status,
                     "expected":len(expected),"executed":len(actual),"evidence":actual})
    selected_rows = [x for x in rows if x["service_id"] in plan["services"]]
    verdict = "CHECKS_FAILED" if any(x["status"] == "CHECKS_FAILED" for x in selected_rows) else "CHECKS_PASSED" if all(x["status"] == "CHECKS_PASSED" for x in selected_rows) else "INCONCLUSIVE"
    covered = {x["service_id"] for x in rows if x["status"] in ("CHECKS_PASSED", "CHECKS_FAILED")}
    return {"change_id":context["change_id"],"environment":plan["environment"],
            "mode":evidence.get("mode", "unverified-source"), "selected_scope_verdict":verdict,
            "coverage_gaps": sorted(set(affected) - covered),"services":rows,
            "investigation":"Not connected: this is the deterministic evidence foundation, not an AI diagnosis."}
