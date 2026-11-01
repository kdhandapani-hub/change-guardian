from app.core import resolve

def fixtures():
    plan=resolve("demo-qa","payments","smoke");plan.update(change_id="D1",runner_exit=1,collection_sha256="test")
    raw={"run":{"executions":[{"requestExecuted":{"name":"payments/smoke"},"tests":[{"name":"HTTP 200","status":"failed"},{"name":"Synthetic response","status":"passed"}],"response":{"code":500},"errors":[]}]}}
    return plan,raw,{"number":10,"building":False,"result":"FAILURE"},{"change_id":"D1","environment":"demo-qa","affected_services":["accounts","payments","positions"]}
