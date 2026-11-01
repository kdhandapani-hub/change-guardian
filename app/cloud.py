"""Owner-only cloud entrypoint; requires HTTPS origin, password and durable database."""
import base64, json, os, secrets, time, re, hmac, hashlib
from http.cookies import SimpleCookie
from urllib.parse import urlparse, parse_qs
from http.server import ThreadingHTTPServer
from pathlib import Path

# Configuration is validated before importing code that initializes storage.
ORIGIN=os.environ.get("GUARDIAN_PUBLIC_ORIGIN", "https://"+os.environ["REPLIT_DEV_DOMAIN"] if os.environ.get("REPLIT_DEV_DOMAIN") else "").rstrip("/")
PASSWORD=os.environ.get("GUARDIAN_APP_PASSWORD", "")
if not ORIGIN.startswith("https://") or urlparse(ORIGIN).path not in {"", "/"}:
    raise SystemExit("Set GUARDIAN_PUBLIC_ORIGIN to the exact HTTPS app URL")
if len(PASSWORD)<24: raise SystemExit("Set a unique GUARDIAN_APP_PASSWORD of at least 24 characters")
if not os.environ.get("DATABASE_URL"): raise SystemExit("A durable PostgreSQL DATABASE_URL is required")
if not os.environ.get("GUARDIAN_GATEWAY_SECRET"): raise SystemExit("Gateway secret required")
from app import dashboard as dashboard
from app.database import connect
from app.core import ROOT

dashboard.ORIGIN=ORIGIN
class PersistentTasks:
    def __init__(self):
        with connect(ROOT/"runtime/cloud.sqlite") as db:
            db.execute("CREATE TABLE IF NOT EXISTS guardian_tasks (id TEXT PRIMARY KEY, value TEXT NOT NULL, created DOUBLE PRECISION NOT NULL)")
    def __setitem__(self,key,value):
        with connect(ROOT/"runtime/cloud.sqlite") as db:
            db.execute("INSERT INTO guardian_tasks VALUES (?,?,?) ON CONFLICT (id) DO UPDATE SET value=EXCLUDED.value",(key,json.dumps(value),time.time()))
    def get(self,key,default=None):
        with connect(ROOT/"runtime/cloud.sqlite") as db:
            row=db.execute("SELECT value,created FROM guardian_tasks WHERE id=?",(key,)).fetchone()
        if not row:return default
        value=json.loads(row["value"])
        if value.get("status")=="running" and time.time()-row["created"]>240:
            return {"status":"error","error":"Work interrupted or timed out. Reload evidence; reconcile approvals before any new request."}
        return value

dashboard.TASKS=PersistentTasks()
class CloudHandler(dashboard.Handler):
    def redirect(self,path,cookie=None):
        self.send_response(303);self.send_header("Location",path)
        if cookie:self.send_header("Set-Cookie",cookie)
        self.send_header("Cache-Control","no-store");self.send_header("Content-Length","0");self.end_headers()
    def authorized(self):
        wanted="Basic "+base64.b64encode(("karthik:"+PASSWORD).encode()).decode()
        if secrets.compare_digest(self.headers.get("Authorization", ""),wanted): return True
        try:
            cookies=SimpleCookie();cookies.load(self.headers.get("Cookie",""))
            value=cookies["guardian_session"].value
            expiry,nonce,signature=value.split(".")
            expected=hmac.new(PASSWORD.encode(),(expiry+"."+nonce).encode(),hashlib.sha256).hexdigest()
            if time.time()<int(expiry)<=time.time()+28800 and secrets.compare_digest(signature,expected):return True
        except (KeyError,ValueError):pass
        if self.command=="GET" and self.path=="/":self.redirect("/login")
        else:self.response(401,{"error":"Sign in to Change Guardian"})
        return False
    def login_page(self,status=200):
        return self.response(status,'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Sign in · Change Guardian</title><body><main><h1>Change Guardian</h1><p>Sign in to view verification results and approve diagnostic runs.</p><form method="post" action="/login"><p><label>Username <input name="username" value="karthik" autocomplete="username" required></label></p><p><label>Password <input name="password" type="password" autocomplete="current-password" required></label></p><button type="submit">Sign in</button></form></main></body></html>''',"text/html; charset=utf-8")
    def valid_host(self):return self.headers.get("Host")==urlparse(ORIGIN).netloc
    def response(self,status,body,ctype="application/json"):
        if isinstance(body,str) and ctype.startswith("text/html"):
            body=body.replace("LOCAL / SYNTHETIC","CLOUD / SYNTHETIC").replace("Local single-operator approval.","Owner-only approval.")
            body=re.sub(r'<a href="http://127[.]0[.]0[.]1:8088/job/change-guardian-verification/"[^>]*>Open Jenkins ↗</a>',"",body)
        def rewrite(value):
            if isinstance(value,dict):
                result={k:rewrite(v) for k,v in value.items()}
                for key in ("source","build_url"):
                    link=result.get(key,"")
                    match=re.fullmatch(re.escape(dashboard.BASE)+r"/job/change-guardian-verification/([0-9]+)/(?:artifact/runtime/reports/(plan|results)[.]json)?",link)
                    if match:result[key]="/api/evidence?build="+match[1]+"&file="+(match[2] or "plan")+".json"
                return result
            if isinstance(value,list):return [rewrite(v) for v in value]
            return value
        return super().response(status,rewrite(body),ctype)
    def do_GET(self):
        if self.path=="/healthz":return self.response(200,{"status":"ok"})
        if self.path=="/login":
            if not self.valid_host():return self.response(403,{"error":"Invalid host"})
            return self.login_page()
        if not self.authorized():return
        if not self.valid_host():return self.response(403,{"error":"Invalid host"})
        route=urlparse(self.path)
        if route.path=="/api/evidence":
            query=parse_qs(route.query)
            try:
                build=int(query.get("build",[""])[0]);name=query.get("file",[""])[0]
                if build<1 or name not in {"plan.json","results.json"}:raise ValueError()
                value=dashboard.artifacts(build)[0 if name=="plan.json" else 1]
                return self.response(200,value)
            except Exception:return self.response(502,{"error":"Evidence unavailable"})
        return super().do_GET()
    def do_POST(self):
        if self.path=="/login":
            if not self.valid_host() or self.headers.get("Origin")!=ORIGIN:return self.response(403,{"error":"Invalid sign-in origin"})
            try:
                size=int(self.headers.get("Content-Length","0"))
                if not 0<size<=2048:raise ValueError()
                fields=parse_qs(self.rfile.read(size).decode())
                valid=secrets.compare_digest(fields.get("username",[""])[0],"karthik") and secrets.compare_digest(fields.get("password",[""])[0],PASSWORD)
            except (ValueError,UnicodeError):valid=False
            if not valid:return self.login_page(401)
            value=str(int(time.time())+28790)+"."+secrets.token_urlsafe(24)
            signature=hmac.new(PASSWORD.encode(),value.encode(),hashlib.sha256).hexdigest()
            return self.redirect("/","guardian_session="+value+"."+signature+"; Path=/; Secure; HttpOnly; SameSite=Strict; Max-Age=28790")
        if not self.authorized():return
        return super().do_POST()

if __name__=="__main__":
    print("Change Guardian cloud server: authenticated owner access required",flush=True)
    ThreadingHTTPServer(("0.0.0.0",int(os.environ.get("PORT","8090"))),CloudHandler).serve_forever()
