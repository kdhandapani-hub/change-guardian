import argparse, json, subprocess, os, hashlib
from pathlib import Path
from app.core import ROOT, resolve

def main():
    p=argparse.ArgumentParser();p.add_argument("--environment",required=True);p.add_argument("--services",required=True);p.add_argument("--suite",required=True)
    a=p.parse_args();plan=resolve(a.environment,a.services,a.suite)
    out=ROOT/"runtime/reports";out.mkdir(parents=True,exist_ok=True)
    plan["change_id"]=os.environ.get("CHANGE_ID","DEMO-CHG-001")
    plan["collection_sha256"]=hashlib.sha256((ROOT/"postman/verification.postman_collection.json").read_bytes()).hexdigest()
    plan["run_purpose"]=os.environ.get("RUN_PURPOSE","verification")
    plan["parent_build"]=os.environ.get("PARENT_BUILD","")
    plan["request_id"]=os.environ.get("REQUEST_ID","")
    if plan["run_purpose"]=="diagnostic" and (not plan["parent_build"].isdigit() or not plan["request_id"]):
        raise ValueError("Diagnostics require parent build and approval ID")
    plan["runner_exit"]=None
    (out/"plan.json").write_text(json.dumps(plan,indent=2))
    command=["postman","collection","run",str(ROOT/"postman/verification.postman_collection.json"),"-e",str(ROOT/"postman"/(a.environment+".postman_environment.json")),"-r","cli,json,junit","--reporter-json-export",str(out/"results.json"),"--reporter-junit-export",str(out/"results.xml")]
    for folder in plan["folders"]: command.extend(["-i",folder])
    print(json.dumps(plan),flush=True)
    try: code=subprocess.run(command,timeout=180).returncode
    except FileNotFoundError: print("Postman CLI is not installed.");code=2
    except subprocess.TimeoutExpired: print("Runner exceeded timeout; verification incomplete.");code=2
    plan["runner_exit"]=code
    (out/"plan.json").write_text(json.dumps(plan,indent=2))
    return code

if __name__=="__main__": raise SystemExit(main())
