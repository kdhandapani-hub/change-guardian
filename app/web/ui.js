let csrf='',report=null,view='all',selectedService='';
const $=id=>document.getElementById(id);
function notice(text){$('notice').textContent=text;}
function el(tag,text,cls){const x=document.createElement(tag);if(text!==undefined)x.textContent=text;if(cls)x.className=cls;return x;}
async function post(path,data){const response=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':csrf},body:JSON.stringify(data)});const value=await response.json();if(!response.ok)throw Error(value.error||'Request failed');if(value.task)return poll(value.task);return value;}
async function poll(id){for(let i=0;i<160;i++){await new Promise(r=>setTimeout(r,1000));const x=await(await fetch('/api/task?id='+encodeURIComponent(id))).json();if(x.status==='complete')return x.result;if(x.status==='error')throw Error(x.error);}throw Error('Operation is still running. Refresh status; do not submit again.');}
async function state(){const x=await(await fetch('/api/state')).json();csrf=x.csrf;$("executionLabel").textContent="Post-change verification · "+x.execution_label;renderApprovals(x.approvals);}
function render(x){report=x;$('overview').hidden=false;$('change').textContent=x.change_id+' · Build #'+x.build_number;$('scope').textContent=x.environment+' · '+x.plan.suite+' · '+x.plan.services.join(', ')+(x.plan.run_purpose==='diagnostic'?' · Diagnostic of #'+x.plan.parent_build:'');$('verdict').textContent=x.selected_scope_verdict.replaceAll('_',' ');$('affected').textContent=x.services.filter(s=>s.affected).length;$('gaps').textContent=x.coverage_gaps.length;$('buildLink').href=x.build_url;
renderNavigation();renderServices();
const inv=x.investigation;$('findings').textContent=inv?.text||'Results loaded. Click Investigate with AI for advisory findings.';$('aiMeta').textContent=inv?inv.status+' · '+(inv.model_calls||0)+' model calls · '+(inv.elapsed_seconds||0)+' seconds':'One agent · read-only Jenkins tools';$('environment').value=x.environment;$('services').value=x.services.filter(s=>s.status==='CHECKS_FAILED').map(s=>s.service_id).join(',')||x.plan.services.join(',');$('suite').value=x.plan.suite;}

const viewNames={all:'All services',attention:'Needs attention',passed:'Passed services',failed:'Failed services',untested:'Not tested',recent:'Recent failures'};
function matches(service,filter){
 if(filter==='passed')return service.status==='CHECKS_PASSED';
 if(filter==='failed'||filter==='recent')return service.status==='CHECKS_FAILED';
 if(filter==='untested')return service.status==='NOT_TESTED';
 if(filter==='attention')return service.status!=='CHECKS_PASSED';
 return true;
}
function renderNavigation(){
 if(selectedService&&!report.services.some(s=>s.service_id===selectedService))selectedService='';
 $('navScope').textContent='Build #'+report.build_number+' · '+report.environment;
 for(const filter of Object.keys(viewNames))$('count-'+filter).textContent=report.services.filter(s=>matches(s,filter)).length;
 $('serviceNav').replaceChildren();
 for(const service of report.services){
  const b=el('button');b.dataset.service=service.service_id;b.append(el('span',service.service_id),el('span',service.status==='CHECKS_PASSED'?'Passed':service.status==='CHECKS_FAILED'?'Failed':service.status==='NOT_TESTED'?'Not tested':'Review','service-state '+service.status));
  b.onclick=()=>selectView('all',service.service_id);$('serviceNav').append(b);
 }
}
function selectView(filter,service=''){view=filter;selectedService=service;if(report)renderServices();}
function renderServices(){
 const visible=report.services.filter(s=>matches(s,view)&&(!selectedService||s.service_id===selectedService));
 $('filterTitle').textContent=selectedService||viewNames[view];
 $('filterSummary').textContent=visible.length+' of '+report.services.length+' services shown · build #'+report.build_number+(view==='recent'?' · failures in this loaded run; severity is not classified':'');
 $('clearFilter').hidden=view==='all'&&!selectedService;
 for(const b of $('resultNav').querySelectorAll('button'))b.setAttribute('aria-pressed',String(!selectedService&&b.dataset.view===view));
 for(const b of $('serviceNav').querySelectorAll('button'))b.setAttribute('aria-pressed',String(b.dataset.service===selectedService));
 $('emptyServices').hidden=visible.length!==0;
 $('recentFailures').hidden=view!=='recent';$('recentFailures').replaceChildren();
 if(view==='recent')for(const service of visible){
  const card=el('article',undefined,'failure-card');card.append(el('strong',service.service_id),el('span','Build #'+report.build_number+' · '+report.environment,'hint'));
  for(const check of service.evidence.filter(c=>c.outcome==='failed')){
   card.append(el('p',check.id+' · HTTP '+(check.http_status||'unavailable')));
   for(const assertion of (check.assertions||[]).filter(a=>a.status==='failed'))card.append(el('p',assertion.message||assertion.name,'hint'));
  }
  card.append(el('p','Observed test failure. Impact and severity need human review.','hint'));$('recentFailures').append(card);
 }
 $('rows').replaceChildren();for(const service of visible){const tr=el('tr');const td=el('td',service.service_id);const ci=report.analyser.services.find(s=>s.service_id===service.service_id);if(ci)td.append(el('small',ci.parentCI+' / '+ci.altCI));tr.append(td);const status=el('td');status.append(el('span',service.status.replaceAll('_',' '),'badge '+service.status));tr.append(status,el('td',service.executed+' / '+service.expected));const evidence=el('td');for(const check of service.evidence){const a=el('a',check.id+' · HTTP '+(check.http_status||'—'));a.href=check.source;a.target='_blank';a.rel='noopener';evidence.append(a,el('br'));}if(!service.evidence.length)evidence.textContent='No tests in selected scope';tr.append(evidence);$('rows').append(tr);}

}
for(const b of $('resultNav').querySelectorAll('button'))b.onclick=()=>selectView(b.dataset.view);
$('clearFilter').onclick=()=>selectView('all');
function renderApprovals(rows){$('approvals').replaceChildren();if(!rows.length){$('approvals').append(el('p','No diagnostic requests yet.','hint'));return;}for(const row of rows){const card=el('article',undefined,'approval');const p=row.payload;card.append(el('span',row.state,'badge '+row.state),el('h3','Parent build #'+p.parent_build+' → '+p.services.join(', ')));card.append(el('pre',JSON.stringify({environment:p.environment,services:p.services,suite:p.suite,change_id:p.change_id,parent_build:p.parent_build,reason:p.reason,request_id:p.request_id},null,2)),el('p',row.detail,'hint'));if(row.build){const a=el('a','Open diagnostic build #'+row.build+' ↗');a.href='/?build='+row.build;a.target='_blank';a.rel='noopener';card.append(a);}
if(row.state==='PENDING'){const actions=el('div',undefined,'actions');for(const [label,path,cls] of [['Approve & run','/api/approve',''],['Reject','/api/reject','danger']]){const b=el('button',label,cls);b.onclick=async()=>{if(path.endsWith('approve')&&!confirm('Approve this exact diagnostic run in '+p.environment+' for '+p.services.join(', ')+' ('+p.suite+')?'))return;b.disabled=true;try{await post(path,{id:row.id,digest:row.digest});notice(path.endsWith('approve')?'Approval processed. Refresh Jenkins status to track the diagnostic.':'Request rejected; no build triggered.');}catch(e){notice(e.message);}finally{await state();}};actions.append(b);}card.append(actions);}$('approvals').append(card);}}
async function load(investigate){const button=investigate?$('investigate'):$('load');button.disabled=true;notice(investigate?'Agent investigating real Jenkins evidence…':'Loading actual Jenkins evidence…');try{render(await post(investigate?'/api/investigate':'/api/load',{build:Number($('build').value)}));notice('Loaded real Jenkins/Postman evidence. Original verification stays unchanged.');}catch(e){notice(e.message);}finally{button.disabled=false;}}
$('load').onclick=()=>load(false);$('investigate').onclick=()=>load(true);$('proposal').onsubmit=async e=>{e.preventDefault();if(!report)return notice('Load a build first.');$('propose').disabled=true;try{await post('/api/propose',{parent_build:report.build_number,services:$('services').value,suite:$('suite').value,reason:$('reason').value});notice('Diagnostic prepared. Review the exact parameters below before approving.');await state();}catch(e){notice(e.message);}finally{$('propose').disabled=false;}};
$('refresh').onclick=async()=>{try{await post('/api/reconcile',{});await state();notice('Diagnostic status refreshed from Jenkins.');}catch(e){notice(e.message);}};
const requestedBuild=new URLSearchParams(location.search).get('build');if(requestedBuild&&/^[1-9][0-9]*$/.test(requestedBuild))$('build').value=requestedBuild;
state().then(()=>load(false));
