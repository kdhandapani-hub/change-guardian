from pathlib import Path
import urllib.request,http.cookiejar,json,base64,time
r=Path(__file__).resolve().parents[1];rt=r/'runtime';c=json.loads((rt/'jenkins-admin.json').read_text());auth='Basic '+base64.b64encode((c['username']+':'+c['password']).encode()).decode();base='http://127.0.0.1:8088'
op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
def req(path,data=None,ctype=None):
 headers={'Authorization':auth}
 if data is not None:
  cr=json.loads(op.open(urllib.request.Request(base+'/crumbIssuer/api/json',headers=headers)).read());headers[cr['crumbRequestField']]=cr['crumb']
 if ctype:headers['Content-Type']=ctype
 return op.open(urllib.request.Request(base+path,data=data,headers=headers),timeout=60).read()
source_copy="python3 -c 'import os,shutil; from pathlib import Path; r=Path(\""+str(r)+"\"); w=Path.cwd(); [shutil.copytree(r/n,w/n,dirs_exist_ok=True) for n in [\"app\",\"scripts\",\"config\",\"postman\"]]'"
pipeline=(r/'jenkins/Jenkinsfile').read_text().replace("stage('Checkout') { steps { deleteDir(); checkout scm } }", "stage('Local demo source') { steps { deleteDir(); sh '''"+source_copy+"\n''' } }")
pipeline=pipeline.replace('  options {','  environment { PATH = "'+str(rt/'tools/bin')+':/usr/bin:/bin:/usr/sbin:/sbin" }\n  options {')
encoded=base64.b64encode(pipeline.encode()).decode()
groovy='''import jenkins.model.Jenkins
import org.jenkinsci.plugins.workflow.job.WorkflowJob
import org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition
def j=Jenkins.get()
def job=j.getItem("change-guardian-verification") ?: j.createProject(WorkflowJob,"change-guardian-verification")
job.setDefinition(new CpsFlowDefinition(new String("%s".decodeBase64(),"UTF-8"),true))
job.save()
println("Local verification pipeline configured")
'''%encoded
import urllib.parse
print(req('/scriptText',urllib.parse.urlencode({'script':groovy}).encode(),'application/x-www-form-urlencoded').decode(),flush=True)
print(req('/job/change-guardian-verification/buildWithParameters',urllib.parse.urlencode({'ENVIRONMENT':'demo-qa','SERVICES':'accounts,payments','SUITE':'smoke','CHANGE_ID':'DEMO-CHG-001'}).encode(),'application/x-www-form-urlencoded').decode(),flush=True)
print('First pipeline build queued',flush=True)
