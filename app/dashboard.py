"""Local single-operator UI. No authentication claim beyond loopback/CSRF isolation."""
import asyncio, json, os, secrets, threading, time, uuid
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv
from app.core import ROOT
from app.approvals import Approvals
from app.jenkins import artifacts, session, read_tool, BASE
from app.evidence import build_report
from app.investigate import run_investigation

ORIGIN="http://127.0.0.1:8090"
TOKEN=secrets.token_urlsafe(32)
STORE=Approvals()
TASKS={};LOCK=threading.Lock()

def context_for(plan):
    name="analyser-context-dev.json" if plan["environment"]=="demo-dev" else "analyser-context.json"
    context=json.loads((ROOT/"fixtures"/name).read_text())
    if context["change_id"]!=plan["change_id"]:raise ValueError("No matching analyser change snapshot")
    return context

async def load_report(build,investigate=False):
    plan,raw=await asyncio.to_thread(artifacts,build);context=context_for(plan)
    async with session() as client:
        if investigate: report=await run_investigation(client,build,context,str(uuid.uuid4()))
        else:
            report=build_report(context,plan,raw,await read_tool(client,"getBuild",build))
            report["mcp_test_summary"]=await read_tool(client,"getTestResults",build)
            cached=ROOT/f"runtime/investigations/build-{build}.json"
            if cached.exists():
                saved=json.loads(cached.read_text())
                if saved.get("collection_sha256")==report["collection_sha256"] and saved.get("environment")==report["environment"] and saved.get("build_url")==report["build_url"]:report["investigation"]=saved.get("investigation")
    report["plan"]=plan;report["analyser"]=context
    path=ROOT/f"runtime/investigations/build-{build}.json";path.parent.mkdir(exist_ok=True,parents=True)
    temporary=path.with_suffix('.tmp-'+uuid.uuid4().hex);temporary.write_text(json.dumps(report,indent=2));os.replace(temporary,path)
    return report

def task(action):
    id=uuid.uuid4().hex
    with LOCK:TASKS[id]={"status":"running","started":time.time()}
    def work():
        try:
            result=action()
            with LOCK:TASKS[id]={"status":"complete","result":result}
        except Exception as e:
            with LOCK:TASKS[id]={"status":"error","error":str(e)[:300] if isinstance(e,ValueError) else type(e).__name__+": local operation failed; inspect Jenkins/runtime"}
    threading.Thread(target=work,daemon=True).start();return id

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def response(self,status,body,ctype="application/json"):
        raw=body.encode() if isinstance(body,str) else json.dumps(body).encode()
        self.send_response(status);self.send_header("Content-Type",ctype);self.send_header("Content-Length",str(len(raw)))
        self.send_header("Cache-Control","no-store");self.send_header("X-Content-Type-Options","nosniff")
        self.send_header("Content-Security-Policy","default-src 'self'; script-src 'self'; style-src 'self'; frame-ancestors 'none'; base-uri 'none'")
        self.end_headers();self.wfile.write(raw)
    def valid_host(self):return self.headers.get("Host")=="127.0.0.1:8090"
    def do_GET(self):
        if not self.valid_host():return self.response(403,{"error":"Invalid host"})
        route=urlparse(self.path)
        if route.path in {"/","/ui.js","/style.css"}:
            name={"/":"index.html","/ui.js":"ui.js","/style.css":"style.css"}[route.path]
            return self.response(200,(ROOT/"app/web"/name).read_text().replace("__DEFAULT_BUILD__",str(int(os.environ.get("GUARDIAN_DEFAULT_BUILD","7")))),{"index.html":"text/html; charset=utf-8","ui.js":"text/javascript","style.css":"text/css"}[name])
        if route.path=="/api/state":return self.response(200,{"csrf":TOKEN,"execution_label":os.environ.get("GUARDIAN_EXECUTION_LABEL","Local Jenkins"),"approvals":[a for a in STORE.list() if a["payload"].get("jenkins_base_url")==BASE]})
        if route.path=="/api/task":
            id=parse_qs(route.query).get("id",[""])[0]
            with LOCK:value=TASKS.get(id,{"status":"error","error":"Task not found; reload the report"})
            return self.response(200,value)
        return self.response(404,{"error":"Not found"})
    def do_POST(self):
        if not self.valid_host() or self.headers.get("Origin")!=ORIGIN or not secrets.compare_digest(self.headers.get("X-CSRF-Token",""),TOKEN):return self.response(403,{"error":"Reload the local dashboard to authorize this request"})
        try:
            size=int(self.headers.get("Content-Length","0"))
            if not 0<size<=8192:raise ValueError("Invalid request size")
            data=json.loads(self.rfile.read(size))
            if self.path in {"/api/load","/api/investigate"}:
                build=data["build"]
                if type(build) is not int or build<1:raise ValueError("Invalid build")
                investigate=self.path=="/api/investigate"
                id=task(lambda:asyncio.run(load_report(build,investigate)))
                return self.response(202,{"task":id})
            if self.path=="/api/propose":
                return self.response(200,STORE.propose(data["parent_build"],data["services"],data["suite"],data["reason"]))
            if self.path=="/api/reject":return self.response(200,STORE.reject(data["id"]))
            if self.path=="/api/approve":
                id=task(lambda:asyncio.run(STORE.approve(data["id"],data["digest"])))
                return self.response(202,{"task":id})
            if self.path=="/api/reconcile":
                id=task(lambda:(STORE.reconcile(),STORE.list())[1]);return self.response(202,{"task":id})
            return self.response(404,{"error":"Not found"})
        except (ValueError,KeyError,TypeError) as e:return self.response(400,{"error":str(e)[:200]})
        except Exception:return self.response(502,{"error":"Jenkins evidence unavailable; no run submitted. Check the selected build and local services."})

if __name__=="__main__":
    load_dotenv(ROOT/".env",override=False)
    print("Change Guardian dashboard: "+ORIGIN,flush=True)
    ThreadingHTTPServer(("127.0.0.1",8090),Handler).serve_forever()
