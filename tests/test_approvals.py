import asyncio, tempfile, time, unittest
from pathlib import Path
from app.approvals import Approvals, digest
from app.core import resolve

class ApprovalTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.store=Approvals(Path(self.tmp.name)/"approvals.sqlite")
        self.plan=resolve("demo-qa","accounts,payments","smoke");self.plan.update(change_id="D1",runner_exit=1)
        self.parent=lambda build:(self.plan,{})
    def tearDown(self):self.tmp.cleanup()
    def proposal(self):return self.store.propose(7,"payments","smoke","Confirm failure",self.parent)
    async def test_no_execution_before_approval(self):
        row=self.proposal();self.assertEqual(row["state"],"PENDING")
    async def test_rejection_blocks_submission(self):
        row=self.proposal();self.store.reject(row["id"])
        calls=[]
        async def trigger(p):calls.append(p);return {"id":1}
        result=await self.store.approve(row["id"],row["digest"],trigger,self.parent)
        self.assertEqual(result["state"],"REJECTED");self.assertFalse(calls)
    async def test_duplicate_approval_triggers_once(self):
        row=self.proposal();calls=[]
        async def trigger(p):calls.append(p);return {"id":42}
        for _ in range(2):await self.store.approve(row["id"],row["digest"],trigger,self.parent)
        self.assertEqual(len(calls),1);self.assertEqual(calls[0]["PARENT_BUILD"],"7")
        self.assertEqual(calls[0]["SERVICES"],"payments")
    async def test_concurrent_clicks_trigger_once(self):
        row=self.proposal();calls=[]
        async def trigger(p):calls.append(p);await asyncio.sleep(.02);return {"id":42}
        await asyncio.gather(*[self.store.approve(row["id"],row["digest"],trigger,self.parent) for _ in range(2)])
        self.assertEqual(len(calls),1)
    async def test_changed_digest_rejected(self):
        row=self.proposal()
        with self.assertRaises(ValueError):self.store.claim(row["id"],"tampered",self.parent)
    async def test_payload_tampering_rejected(self):
        row=self.proposal()
        with self.store.connect() as db:db.execute("UPDATE approvals SET payload=replace(payload,'payments','positions') WHERE id=?",(row["id"],))
        with self.assertRaises(ValueError):self.store.claim(row["id"],row["digest"],self.parent)
    async def test_parent_changes_invalidate_approval(self):
        row=self.proposal();self.plan["change_id"]="D2"
        with self.assertRaises(ValueError):self.store.claim(row["id"],row["digest"],self.parent)
    async def test_out_of_scope_service_rejected(self):
        with self.assertRaises(ValueError):self.store.propose(7,"positions","smoke","Scope expansion",self.parent)
    async def test_expired_approval_rejected(self):
        row=self.proposal()
        with self.store.connect() as db:db.execute("UPDATE approvals SET created=? WHERE id=?",(time.time()-1900,row["id"]))
        with self.assertRaises(ValueError):self.store.claim(row["id"],row["digest"],self.parent)
    async def test_unknown_submission_never_retries(self):
        row=self.proposal();calls=[]
        async def trigger(p):calls.append(p);raise TimeoutError("Ambiguous network failure")
        result=await self.store.approve(row["id"],row["digest"],trigger,self.parent)
        self.assertEqual(result["state"],"UNKNOWN")
        await self.store.approve(row["id"],row["digest"],trigger,self.parent)
        self.assertEqual(len(calls),1)
    async def test_pending_survives_process_recreation(self):
        row=self.proposal();new=Approvals(self.store.path)
        self.assertEqual(new.get(row["id"])["digest"],row["digest"])
        self.assertEqual(new.get(row["id"])["state"],"PENDING")

    async def test_approval_cannot_cross_jenkins_hosts(self):
        from unittest.mock import patch
        row=self.proposal()
        with patch("app.approvals.BASE","https://another-executor.invalid"):
            with self.assertRaises(ValueError):self.store.claim(row["id"],row["digest"],self.parent)
