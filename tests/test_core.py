import unittest
from app.core import resolve, report

class CoverageTests(unittest.TestCase):
    def setUp(self):
        self.context={"change_id":"D1","environment":"demo-qa","affected_services":["accounts","payments","positions"]}
        self.plan=resolve("demo-qa","accounts,payments","smoke")
    def evidence(self, checks):
        return {"change_id":"D1","environment":"demo-qa","execution":"completed","checks":checks}
    def test_subset_does_not_pass_untested_service(self):
        r=report(self.context,self.plan,self.evidence([{"id":s,"outcome":"passed"} for s in self.plan["folders"]]))
        self.assertEqual(r["coverage_gaps"],["positions"])
        self.assertEqual(r["selected_scope_verdict"],"CHECKS_PASSED")
    def test_missing_results_inconclusive(self):
        self.assertEqual(report(self.context,self.plan,self.evidence([]))["selected_scope_verdict"],"INCONCLUSIVE")
    def test_failure_not_masked_by_missing_result(self):
        r=report(self.context,self.plan,self.evidence([{"id":"payments/smoke","outcome":"failed"}]))
        self.assertEqual(r["selected_scope_verdict"],"CHECKS_FAILED")
        self.assertIn("accounts",r["coverage_gaps"])
    def test_cross_environment_rejected(self):
        e=self.evidence([]);e["environment"]="demo-dev"
        with self.assertRaises(ValueError): report(self.context,self.plan,e)
    def test_duplicate_evidence_rejected(self):
        with self.assertRaises(ValueError): report(self.context,self.plan,self.evidence([{"id":"accounts/smoke","outcome":"passed"}]*2))
    def test_bad_scope_rejected(self):
        for selection in ["all,accounts","unknown","", "accounts,"]:
            with self.assertRaises(ValueError): resolve("demo-qa",selection,"smoke")
    def test_environment_resolution(self):
        self.assertNotEqual(resolve("demo-dev","all","full")["base_url"],self.plan["base_url"])
    def test_all_expands_inventory(self):
        self.assertEqual(len(resolve("demo-qa","all","full")["folders"]),9)

if __name__=="__main__": unittest.main()
