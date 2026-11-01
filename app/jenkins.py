"""Narrow authenticated Jenkins evidence access; never loads admin credentials."""
import base64, json, urllib.request, os
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client, create_mcp_http_client
from app.core import ROOT

load_dotenv(ROOT/".env", override=False)
BASE = os.environ.get("GUARDIAN_JENKINS_BASE_URL", "http://127.0.0.1:8088").rstrip("/")
JOB = "change-guardian-verification"
MAX_BYTES = 2_000_000

def headers(writer=False):
    setting="GUARDIAN_JENKINS_WRITER_FILE" if writer else "GUARDIAN_JENKINS_READER_FILE"
    default="runtime/jenkins-writer.json" if writer else "runtime/jenkins-reader.json"
    credential_env="GUARDIAN_JENKINS_WRITER_JSON" if writer else "GUARDIAN_JENKINS_READER_JSON"
    c=json.loads(os.environ[credential_env]) if os.environ.get(credential_env) else json.loads((ROOT/os.environ.get(setting,default)).read_text())
    result={"Authorization":"Basic "+base64.b64encode((c["username"]+":"+c["token"]).encode()).decode()}
    gateway=os.environ.get("GUARDIAN_GATEWAY_SECRET", "")
    gateway_file=os.environ.get("GUARDIAN_GATEWAY_SECRET_FILE", "")
    if gateway_file:
        gateway=(ROOT/gateway_file).read_text().strip()
    if gateway:
        result["X-Guardian-Gateway"]=gateway
        result["ngrok-skip-browser-warning"]="change-guardian"
    return result

def fetch_json(path):
    if not path.startswith("/job/"+JOB+"/") or ".." in path:
        raise ValueError("Only the registered verification job is allowed")
    request=urllib.request.Request(BASE+path,headers=headers())
    with urllib.request.urlopen(request,timeout=20) as response:
        if response.geturl()!=BASE+path:
            raise ValueError("Redirected evidence is not allowed")
        raw=response.read(MAX_BYTES+1)
    if len(raw)>MAX_BYTES: raise ValueError("Evidence exceeds size limit")
    return json.loads(raw)

def artifacts(build):
    if type(build) is not int or build<1: raise ValueError("Invalid build number")
    prefix=f"/job/{JOB}/{build}/artifact/runtime/reports/"
    return fetch_json(prefix+"plan.json"), fetch_json(prefix+"results.json")

def unwrap(result):
    if result.is_error: raise RuntimeError("Jenkins MCP tool failed")
    blocks=[x.text for x in result.content if getattr(x,"type",None)=="text"]
    data=json.loads("".join(blocks))
    if data.get("status")=="FAILED": raise RuntimeError("Jenkins MCP operation failed")
    return data.get("result",data)

@asynccontextmanager
async def session(writer=False):
    async with create_mcp_http_client(headers=headers(writer)) as http:
        async with streamable_http_client(BASE+"/mcp-server/mcp",http_client=http) as (read,write):
            async with ClientSession(read,write) as client:
                await client.initialize()
                yield client

async def read_tool(client,name,build):
    if name not in {"getBuild","getTestResults","getBuildLog"}: raise ValueError("Read tool not permitted")
    if type(build) is not int or build<1: raise ValueError("Invalid build number")
    args={"jobFullName":JOB,"buildNumber":build}
    if name=="getBuildLog": args["limit"]=60
    return unwrap(await client.call_tool(name,args))
