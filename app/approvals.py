"""Durable exact-payload approval with at-most-once submission and fail-closed recovery."""
import asyncio, hashlib, json, sqlite3, time, uuid
from app.core import ROOT, resolve
from app.jenkins import JOB, BASE, artifacts, fetch_json, session, unwrap

DB=ROOT/"runtime/approvals.sqlite"

def canonical(x): return json.dumps(x,sort_keys=True,separators=(",",":"))
def digest(x):return hashlib.sha256(canonical(x).encode()).hexdigest()

class Approvals:
    def __init__(self,path=DB):
        self.path=path;path.parent.mkdir(parents=True,exist_ok=True)
        with self.connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS approvals (id TEXT PRIMARY KEY, payload TEXT NOT NULL, digest TEXT NOT NULL, state TEXT NOT NULL, created REAL NOT NULL, queue_id INTEGER, build INTEGER, detail TEXT)")
    def connect(self):
        from app.database import connect
        return connect(self.path, cloud=self.path==DB)
    def list(self):
        with self.connect() as db: rows=db.execute("SELECT * FROM approvals ORDER BY created DESC LIMIT 50").fetchall()
        return [dict(x)|{"payload":json.loads(x["payload"])} for x in rows]
    def get(self,id):
        with self.connect() as db: row=db.execute("SELECT * FROM approvals WHERE id=?",(id,)).fetchone()
        if row is None:raise ValueError("Approval request not found")
        d=dict(row);d["payload"]=json.loads(d["payload"]);return d
    def propose(self,parent,services,suite,reason,parent_loader=artifacts):
        plan,_=parent_loader(parent)
        target=resolve(plan["environment"],services,suite)
        if not set(target["services"])<=set(plan["services"]):raise ValueError("Diagnostic cannot expand parent service scope")
        if not plan.get("change_id") or plan.get("runner_exit") is None:raise ValueError("Parent run must have completed evidence")
        if not reason.strip() or len(reason)>500:raise ValueError("Provide a reason of 1–500 characters")
        id=str(uuid.uuid4())
        payload={"jenkins_base_url":BASE,"parent_build":parent,"parent_digest":digest(plan),"environment":plan["environment"],"services":target["services"],"suite":suite,"change_id":plan["change_id"],"reason":reason.strip(),"request_id":id,"job":JOB}
        with self.connect() as db:db.execute("INSERT INTO approvals VALUES (?,?,?,?,?,?,?,?)",(id,canonical(payload),digest(payload),"PENDING",time.time(),None,None,"Awaiting explicit human approval"))
        return self.get(id)
    def reject(self,id):
        with self.connect() as db:
            updated=db.execute("UPDATE approvals SET state='REJECTED',detail='Rejected by local operator' WHERE id=? AND state='PENDING'",(id,)).rowcount
        if not updated:raise ValueError("Only pending requests can be rejected")
        return self.get(id)
    def claim(self,id,expected_digest,parent_loader=artifacts):
        row=self.get(id);payload=row["payload"]
        if row["digest"]!=expected_digest or digest(payload)!=expected_digest:raise ValueError("Approval payload changed; create a new request")
        if row["state"]!="PENDING":return False
        if payload.get("jenkins_base_url")!=BASE:raise ValueError("Approval belongs to another Jenkins host")
        if time.time()-row["created"]>1800:raise ValueError("Approval expired; create a new request")
        plan,_=parent_loader(payload["parent_build"])
        if digest(plan)!=payload["parent_digest"]:raise ValueError("Parent evidence changed; create a new request")
        target=resolve(payload["environment"],",".join(payload["services"]),payload["suite"])
        if plan["environment"]!=payload["environment"] or plan["change_id"]!=payload["change_id"] or not set(target["services"])<=set(plan["services"]):raise ValueError("Diagnostic outside parent scope")
        with self.connect() as db:
            changed=db.execute("UPDATE approvals SET state='SUBMITTING',detail='Approved locally; submission reserved, never automatically retried' WHERE id=? AND state='PENDING'",(id,)).rowcount
        return bool(changed)
    def update(self,id,state,detail,queue_id=None,build=None):
        with self.connect() as db:db.execute("UPDATE approvals SET state=?,detail=?,queue_id=COALESCE(?,queue_id),build=COALESCE(?,build) WHERE id=?",(state,detail[:500],queue_id,build,id))
    async def approve(self,id,expected_digest,trigger=None,parent_loader=artifacts):
        if not await asyncio.to_thread(self.claim,id,expected_digest,parent_loader):return self.get(id)
        row=self.get(id);p=row["payload"]
        parameters={"ENVIRONMENT":p["environment"],"SERVICES":",".join(p["services"]),"SUITE":p["suite"],"CHANGE_ID":p["change_id"],"RUN_PURPOSE":"diagnostic","PARENT_BUILD":str(p["parent_build"]),"REQUEST_ID":id}
        try:
            if trigger is None:
                async with session(writer=True) as client:
                    response=unwrap(await client.call_tool("triggerBuild",{"jobFullName":JOB,"parameters":parameters}))
            else:response=await trigger(parameters)
            queue_id=response.get("id") if isinstance(response,dict) else None
            self.update(id,"QUEUED","Approved diagnostic submitted; original verification unchanged",queue_id=queue_id)
        except Exception:
            self.update(id,"UNKNOWN","Submission outcome uncertain. Reconcile Jenkins by request ID; do not resubmit.")
        return self.get(id)
    def reconcile(self):
        # Read-only reconciliation; never resubmits an ambiguous/crash-interrupted approval.
        active=[r for r in self.list() if r["state"] in {"SUBMITTING","UNKNOWN","QUEUED","RUNNING"} and r["payload"].get("jenkins_base_url")==BASE]
        if not active:return
        data=fetch_json(f"/job/{JOB}/api/json?tree=builds[number,building,result,actions[parameters[name,value]]]{{0,50}}&depth=2")
        for row in active:
            for build in data.get("builds",[]):
                params={p["name"]:p.get("value") for a in build.get("actions",[]) for p in a.get("parameters",[])}
                if params.get("REQUEST_ID")==row["id"]:
                    state="RUNNING" if build["building"] else "COMPLETED"
                    self.update(row["id"],state,"Diagnostic outcome: "+str(build.get("result") or "running"),build=build["number"])
                    break
