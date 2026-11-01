import unittest
from app.core import resolve
from app.evidence import normalize, build_report

class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.plan=resolve("demo-qa","accounts,payments","smoke")
        self.plan.update(change_id="D1",runner_exit=0,collection_sha256="fixture-version")
        self.build={"number":10,"building":False,"result":"SUCCESS"}
        self.raw={"run":{"executions":[self.execution("accounts/smoke"),self.execution("payments/smoke")]}}
        self.context={"change_id":"D1","environment":"demo-qa","affected_services":["accounts","payments","positions"]}
    def execution(self,name):
        return {"requestExecuted":{"name":name},"tests":[{"name":"HTTP 200","status":"passed"},{"name":"Synthetic response","status":"passed"}],"response":{"code":200},"errors":[]}
    def test_actual_schema_passes_and_preserves_coverage_gap(self):
        result=build_report(self.context,self.plan,self.raw,self.build)
        self.assertEqual(result["selected_scope_verdict"],"CHECKS_PASSED")
        self.assertEqual(result["coverage_gaps"],["positions"])
    def test_missing_assertion_never_passes(self):
        self.raw["run"]["executions"][0]["tests"].pop()
        self.assertEqual(build_report(self.context,self.plan,self.raw,self.build)["selected_scope_verdict"],"INCONCLUSIVE")
    def test_skipped_assertion_never_passes(self):
        self.raw["run"]["executions"][0]["tests"][0]["status"]="skipped"
        self.assertEqual(normalize(self.plan,self.raw,self.build)["checks"][0]["outcome"],"error")
    def test_infrastructure_failure_never_passes(self):
        self.plan["runner_exit"]=2
        self.assertEqual(build_report(self.context,self.plan,self.raw,self.build)["selected_scope_verdict"],"INCONCLUSIVE")
    def test_failed_jenkins_with_passing_tests_is_inconclusive(self):
        self.build["result"]="FAILURE"
        self.assertEqual(build_report(self.context,self.plan,self.raw,self.build)["selected_scope_verdict"],"INCONCLUSIVE")
    def test_assertion_failure_is_preserved(self):
        self.raw["run"]["executions"][1]["tests"][0]["status"]="failed"
        self.build["result"]="FAILURE";self.plan["runner_exit"]=1
        self.assertEqual(build_report(self.context,self.plan,self.raw,self.build)["selected_scope_verdict"],"CHECKS_FAILED")
    def test_legacy_run_rejected(self):
        self.plan.pop("change_id")
        with self.assertRaises(ValueError):normalize(self.plan,self.raw,self.build)
    def test_duplicate_execution_rejected(self):
        self.raw["run"]["executions"].append(self.raw["run"]["executions"][0])
        with self.assertRaises(ValueError):normalize(self.plan,self.raw,self.build)
    def test_plan_tampering_rejected(self):
        self.plan["base_url"]="https://example.invalid"
        with self.assertRaises(ValueError):normalize(self.plan,self.raw,self.build)
