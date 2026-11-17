import {validateSabrDiagnostics} from './native-sabr-diagnostics.js';
const list=document.querySelector('#workers'),stop=document.querySelector('#stop-all'),health=document.querySelector('#health'),history=document.querySelector('#diagnostics');
const inspections=document.querySelector('#inspections'),copy=document.querySelector('#copy-inspection');let latest=[];
const reload=document.querySelector('#reload-helper'),reloadStatus=document.querySelector('#reload-status');
const checkTarget=document.querySelector('#check-normal-target'),startTrial=document.querySelector('#start-normal-trial'),normalReport=document.querySelector('#normal-context');
const manifest=chrome.runtime.getManifest();
document.querySelector('#helper-version').textContent=`Installed version ${manifest.version} · YouTube batch permission declaration ${manifest.host_permissions?.includes('https://www.youtube.com/*')?'present':'absent'}. Use Check target tab to verify the actual grant.`;
const idle=(state,native)=>Array.isArray(state?.workers)&&state.workers.length===0&&
  (!native||['held','drive_verified'].includes(native.phase));
let reloading=false;
function protocolReport(native){
  if(!native)return 'No native protocol report in this Chrome session.';
  try{
    const report={phase:/^[a-z0-9_]{1,80}$/.test(native.phase||'')?native.phase:'unknown'};
    if(Number.isSafeInteger(native.bytes)&&native.bytes>=0&&native.bytes<=64000000)report.bytes=native.bytes;
    if(typeof native.source_binding_sha256==='string'&&/^[a-f0-9]{64}$/.test(native.source_binding_sha256))report.source_binding_sha256=native.source_binding_sha256;
    if(typeof native.error==='string'&&/^[a-z0-9_]{1,80}$/.test(native.error))report.error=native.error;
    if(native.diagnostics!==undefined)report.diagnostics=validateSabrDiagnostics(native.diagnostics);
    return JSON.stringify(report,null,2);
  }catch{return 'Protocol diagnostics withheld: invalid bounded report.';}
}
let checkingTarget=false;
async function targetControl(operation){
  if(checkingTarget)return;checkingTarget=true;checkTarget.disabled=true;startTrial.disabled=true;
  reload.disabled=true;
  try{
    const result=await chrome.runtime.sendMessage({target:'native-controls',operation});
    if(result?.error){normalReport.textContent=`Held: ${/^[a-z0-9_]{1,80}$/.test(result.error)?result.error:'normal_context_failed'}.`;return;}
    const value=result?.value;if(!value)throw Error('normal_context_unavailable');
    const lines=[];
    for(const key of ['permission_granted','target_count','active_job','video_id','target_matches','duration_seconds','current_time','paused','ads_detected','media_keys_present','is_live','playability_status','eligible','error','started']){
      if(value[key]!==undefined)lines.push(`${key}: ${value[key]}`);
    }
    normalReport.textContent=lines.join('\n');startTrial.disabled=operation!=='inspect_target'||value.eligible!==true;
  }catch{normalReport.textContent='Target check unavailable. Reload the helper; no source request was started.';}
  finally{checkingTarget=false;checkTarget.disabled=false;}
}
checkTarget.addEventListener('click',()=>targetControl('inspect_target'));
startTrial.addEventListener('click',()=>targetControl('start_target'));
async function refresh(){
  try{const state=await chrome.runtime.sendMessage({target:'background',type:'status'});list.replaceChildren();
    for(const worker of state.workers||[]){const row=document.createElement('div');row.className='worker';
      const source=document.createElement('strong');source.textContent=worker.video_id||'Preparing tab';
      const status=document.createElement('span');status.className='state';status.textContent=(worker.state||'waiting').replaceAll('_',' ');row.append(source,status);list.append(row);}
    if(!state.workers?.length){const empty=document.createElement('p');empty.textContent='No recording workers active.';list.append(empty);}
    stop.disabled=!state.workers?.length;
    const native=(await chrome.storage.session.get('researchNativeStatus')).researchNativeStatus;
    document.querySelector('#native-protocol-diagnostics').textContent=protocolReport(native);
    const activity=await chrome.runtime.sendMessage({target:'native-controls',operation:'activity'});
    reload.disabled=reloading||checkingTarget||activity?.value?.active!==false||!idle(state,native);
    document.querySelector('#native-progress').textContent=native?`${native.video_id||'Native pilot'} · ${native.phase.replaceAll('_',' ')}${native.error?` · ${native.error}`:''}${native.bytes?` · ${(native.bytes/1048576).toFixed(2)} MiB`:''}`:'No native pilot started in this Chrome session.';
    latest=state.inspections||[];inspections.replaceChildren();copy.disabled=!latest.length;
    for(const item of [...latest].reverse()){
      const heading=document.createElement('h3');heading.textContent=item.video_id||'Tab inspection';inspections.append(heading);
      const summary=document.createElement('p');summary.textContent=item.state==='held'?`Held: ${item.error}`:
        `${item.formats.length} audio formats · SABR ${item.has_sabr?'present':'absent'} · streaming configuration ${item.has_ustreamer_config?'present':'absent'} · client ${item.client_name||'unknown'}`;
      inspections.append(summary);
      for(const format of item.formats||[]){const row=document.createElement('p');row.className='note';row.textContent=`Format ${format.itag}: ${format.mime_type}; ${format.bytes?`${(format.bytes/1048576).toFixed(2)} MiB`:'size unknown'}; ${format.direct_url_available?'direct URL present':format.cipher_only?'ciphered URL only':'SABR/other transport required'}`;inspections.append(row);}
    }
    if(!latest.length){const empty=document.createElement('p');empty.textContent='Earlier inspection results appear here when available. No new inspection report is needed for the pilot.';inspections.append(empty);}
    history.replaceChildren();
    for(const entry of [...(state.diagnostics||[])].reverse()){
      const row=document.createElement('div');row.className='worker';
      const source=document.createElement('strong');source.textContent=entry.video_id||'Tab activation';
      const detail=document.createElement('span');detail.className='state';
      detail.textContent=`${entry.state==='stopped'?'Stopped':entry.state==='done'?'Done':'Held'}: ${entry.code} · ${new Date(entry.at).toLocaleTimeString()}`;
      row.append(source,detail);history.append(row);
    }
    if(!state.diagnostics?.length){const empty=document.createElement('p');empty.textContent='No completed or stopped attempts in this Chrome session.';history.append(empty);}
  }catch{reload.disabled=true;list.textContent='Extension status unavailable. Reload this page.';}
}
reload.addEventListener('click',async()=>{
  if(reloading||checkingTarget)return;reloading=true;reload.disabled=true;
  try{
    // Recheck at activation, so an old options page cannot interrupt a worker.
    const state=await chrome.runtime.sendMessage({target:'background',type:'status'});
    const native=(await chrome.storage.session.get('researchNativeStatus')).researchNativeStatus;
    if(!idle(state,native)){reloadStatus.textContent='Reload held: a worker is active or its state is unavailable.';reloading=false;return;}
    reloadStatus.textContent='Reloading helper. Reopen this status page after the extension reloads.';
    const result=await chrome.runtime.sendMessage({target:'native-controls',operation:'reload_helper'});
    if(result?.value?.reload!==true){reloadStatus.textContent='Reload held: the helper is active or has not loaded the new controls.';reloading=false;}
  }catch{reloading=false;reloadStatus.textContent='Reload unavailable. No source request was started.';}
});
stop.addEventListener('click',async()=>{stop.disabled=true;await chrome.runtime.sendMessage({target:'background',type:'stop_all'});await refresh();});
copy.addEventListener('click',async()=>{try{await navigator.clipboard.writeText(JSON.stringify(latest,null,2));copy.textContent='Copied';}catch{copy.textContent='Copy unavailable';}});
health.textContent='Native pilot gateway: 127.0.0.1:8781. The resource owner must arm the one-video lease before activation.';
refresh();setInterval(refresh,2000);
