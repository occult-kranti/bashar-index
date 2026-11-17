import {service,validateJob,videoFromUrl,LIMITS} from './core.js';
import {cleanupWorker} from './lifecycle.js';
import {outcome,diagnostic,retainDiagnostic} from './diagnostics.js';
import {nativeBrowserProbe} from './native-inspector.js';

const workers=new Map();let offscreenCreation,diagnostics=[],inspections=[];
const boot=chrome.storage.session.get(['researchWorkers','researchDiagnostics','researchInspections']).then(value=>{
  for(const worker of value.researchWorkers||[])workers.set(worker.tab_id,worker);
  diagnostics=(value.researchDiagnostics||[]).slice(-16);
  inspections=(value.researchInspections||[]).slice(-4);
});
const safe=error=>/^[a-z0-9_]{1,80}$/.test(error?.message||'')?error.message:'operation_failed';
let persistence=Promise.resolve();
const persist=()=>{const snapshot=structuredClone({researchWorkers:[...workers.values()],researchDiagnostics:diagnostics,researchInspections:inspections});persistence=persistence.catch(()=>{}).then(()=>chrome.storage.session.set(snapshot));return persistence;};
const message=value=>chrome.runtime.sendMessage({target:'offscreen',...value});
async function badge(tabId,text,title){try{await chrome.action.setBadgeText({tabId,text});await chrome.action.setBadgeBackgroundColor({tabId,color:text==='ERR'?'#9e3d35':'#1f554b'});await chrome.action.setTitle({tabId,title});}catch{}}
async function ensureOffscreen(){
  if(await chrome.offscreen.hasDocument())return;
  if(!offscreenCreation)offscreenCreation=chrome.offscreen.createDocument({url:'offscreen.html',reasons:['USER_MEDIA'],justification:'Record explicitly activated tab audio and preserve its speaker playback.'}).finally(()=>{offscreenCreation=null;});
  await offscreenCreation;
}
async function token(refresh=false){
  const stored=await chrome.storage.session.get('researchPairToken');if(!refresh&&stored.researchPairToken)return stored.researchPairToken;
  await service('/health',{method:'GET'});const pair=await service('/pair',{body:{}});
  if(typeof pair.token!=='string'||pair.token.length<20||pair.token.length>512)throw Error('invalid_pair_response');
  await chrome.storage.session.set({researchPairToken:pair.token});return pair.token;
}
async function inPage(tabId,command,args){
  const output=await chrome.scripting.executeScript({target:{tabId},world:'MAIN',func:async(command,args)=>{
    try{return {ok:true,value:await window.__researchAudioPage[command](args)};}
    catch(error){return {ok:false,error:/^[a-z0-9_]{1,80}$/.test(error?.message||'')?error.message:'page_operation_failed'};}
  },args:[command,args||{}]});
  if(!output?.[0]?.result?.ok)throw Error(output?.[0]?.result?.error||'page_unavailable');return output[0].result.value;
}
async function release(worker,{error,done=false}={}){
  const result=outcome(worker,{error,done});
  // Record once, before cleanup can race with a second completion callback.
  if(!worker.diagnostic_recorded){worker.diagnostic_recorded=true;diagnostics=retainDiagnostic(diagnostics,diagnostic(worker,result));await persist();}
  await cleanupWorker(worker,workers,{
    releaseStream:()=>message({type:'release',worker_id:worker.worker_id}),
    stopPage:nonce=>inPage(worker.tab_id,'stop',{nonce}),persist,
    badge:()=>badge(worker.tab_id,result.badge,result.title)});
}
async function fail(worker,error){
  worker.state='held';worker.error=worker.stop_reason||safe(error);if(workers.get(worker.tab_id)===worker)await persist();
  try{await message({type:'stop',worker_id:worker.worker_id,reason:worker.error});}catch{}
  if(worker.job){try{await service('/abort',{token:await token(),body:{capture_id:worker.job.capture_id,video_id:worker.job.video_id,reason:worker.error}});}catch{}}
  await release(worker,{error:worker.error});
}
async function stop(worker,reason){
  worker.state='stopping';worker.stopping=true;worker.stop_reason=reason;await persist();
  try{await message({type:'stop',worker_id:worker.worker_id,reason});}catch{}
  // A lease may exist before offscreen recording begins, so report that stop too.
  if(worker.job){try{await service('/abort',{token:await token(),body:{capture_id:worker.job.capture_id,video_id:worker.job.video_id,reason}});}catch{}}
  await release(worker);
}
async function next(worker,preferredVideo){
  const active=()=>{if(worker.stopping||workers.get(worker.tab_id)!==worker)throw Error('user_stopped');};
  active();
  worker.state='leasing';await persist();
  const auth=await token();const reply=await service('/next',{token:auth,body:{worker_id:worker.worker_id,...(preferredVideo?{video_id:preferredVideo}:{})}});
  if(!reply.job){await release(worker,{done:true});return;}
  const job=validateJob(reply.job);worker.job=job;worker.nonce=crypto.randomUUID();worker.state='preparing';await persist();
  active();
  const tab=await chrome.tabs.get(worker.tab_id);
  if(!tab.url?.startsWith('https://www.youtube.com/'))throw Error('tab_origin_changed');
  if(videoFromUrl(tab.url)!==job.video_id||new URL(tab.url).pathname!=='/watch'){
    await chrome.tabs.update(worker.tab_id,{url:job.watch_url});
    let loaded=false;
    for(let i=0;i<100;i++){active();const current=await chrome.tabs.get(worker.tab_id);if(current.status==='complete'&&videoFromUrl(current.url)===job.video_id){loaded=true;break;}await new Promise(resolve=>setTimeout(resolve,250));}
    if(!loaded)throw Error('navigation_timeout');
  }
  await chrome.scripting.executeScript({target:{tabId:worker.tab_id},files:['bridge.js']});
  await chrome.tabs.sendMessage(worker.tab_id,{target:'bridge',type:'configure',nonce:worker.nonce,worker_id:worker.worker_id});
  await chrome.scripting.executeScript({target:{tabId:worker.tab_id},world:'MAIN',files:['page-monitor.js']});
  const prepared=await inPage(worker.tab_id,'prepare',{video_id:job.video_id});
  active();
  const accepted=await service('/start',{token:auth,body:{capture_id:job.capture_id,video_id:job.video_id,
    duration_seconds:prepared.state.duration,source_time:prepared.state.source_time,playback_rate:1,
    ads_detected:false,is_live:false,source_metadata:prepared.source_metadata}});
  if(accepted.accepted!==true)throw Error('start_not_accepted');
  active();
  await inPage(worker.tab_id,'monitor',{nonce:worker.nonce,video_id:job.video_id});
  const armed=await message({type:'record',worker_id:worker.worker_id,job:{...job,duration_seconds:prepared.state.duration},token:auth});
  if(!armed?.ready)throw Error(armed?.error||'recorder_not_ready');
  active();
  worker.state='recording';await persist();await badge(worker.tab_id,'REC','Recording research audio. Click this extension to stop.');
  await inPage(worker.tab_id,'play');
}
chrome.action.onClicked.addListener(tab=>{(async()=>{
  await boot;
  const existing=workers.get(tab.id);
  if(existing){await stop(existing,'user_stopped');return;}
  if(!videoFromUrl(tab.url))throw Error('open_youtube_video');
  // Native inspection is the current product mode. Legacy recording is parked;
  // this explicit fixture-only switch is not exposed by any user interface.
  const setting=await chrome.storage.session.get('researchMode');
  if(setting.researchMode!=='capture_legacy'){
    await badge(tab.id,'LOOK','Inspecting this accepted tab; no audio is recorded or downloaded.');
    const output=await chrome.scripting.executeScript({target:{tabId:tab.id},world:'MAIN',func:nativeBrowserProbe,args:['inspect',videoFromUrl(tab.url)]});
    const result=output?.[0]?.result;if(!result)throw Error('inspection_unavailable');
    inspections=[...inspections.filter(x=>x.tab_id!==tab.id),{...result,tab_id:tab.id,at:new Date().toISOString()}].slice(-4);await persist();
    await badge(tab.id,result.state==='held'?'ERR':'INFO',result.state==='held'?`Native inspection held: ${safe({message:result.error})}. Open extension options.`:'Native format inspection ready. Open extension options; no audio was recorded or downloaded.');
    await chrome.runtime.openOptionsPage();return;
  }
  if(tab.mutedInfo?.muted)throw Error('unmute_tab_before_capture');
  if(workers.size>=LIMITS.workers)throw Error('four_worker_limit');
  const worker={tab_id:tab.id,worker_id:crypto.randomUUID(),state:'activating'};workers.set(tab.id,worker);await persist();
  try{
    await ensureOffscreen();
    const streamId=await chrome.tabCapture.getMediaStreamId({targetTabId:tab.id});
    const attached=await message({type:'attach',worker_id:worker.worker_id,stream_id:streamId});
    if(!attached?.ready)throw Error(attached?.error||'tab_stream_unavailable');
    await token(true); // Explicit activation refreshes a token invalidated by a service restart.
    await next(worker,videoFromUrl(tab.url));
  }catch(error){await fail(worker,error);}
})().catch(async error=>{const result=outcome({},{error:safe(error)});diagnostics=retainDiagnostic(diagnostics,diagnostic({tab_id:tab.id,worker_id:crypto.randomUUID(),job:{video_id:videoFromUrl(tab.url)}},result));await persist();await badge(tab.id,result.badge,result.title);});});

chrome.tabs.onRemoved.addListener(tabId=>{(async()=>{await boot;const worker=workers.get(tabId);if(worker)await stop(worker,'tab_closed');})().catch(()=>{});});
chrome.runtime.onMessage.addListener((value,sender,reply)=>{
  if(sender.id!==chrome.runtime.id||value.target!=='background')return;
  (async()=>{
    await boot;const worker=[...workers.values()].find(x=>x.worker_id===value.worker_id);
    if(value.type==='sample'){
      if(!worker||sender.tab?.id!==worker.tab_id||value.nonce!==worker.nonce)return {accepted:false};
      await message({type:'sample',worker_id:worker.worker_id,state:value.state});return {accepted:true};
    }
    if(value.type==='status')return {workers:[...workers.values()].map(x=>({tab_id:x.tab_id,worker_id:x.worker_id,video_id:x.job?.video_id,state:x.state,error:x.error})),diagnostics,inspections};
    if(value.type==='stop_all'){for(const current of [...workers.values()])await stop(current,'user_stopped');return {accepted:true};}
    if(sender.tab||!sender.url?.startsWith(chrome.runtime.getURL('')))return {accepted:false};
    if(!worker)return {accepted:false};
    if(value.type==='worker_state'){if(worker.stopping)return {accepted:false};worker.state=value.state;await persist();await badge(worker.tab_id,value.state==='buffering'?'BUF':value.state==='validating'?'CHECK':'REC',`Research capture: ${value.state}. Click to stop.`);return {accepted:true};}
    if(value.type==='job_done'){
      if(value.capture_id!==worker.job?.capture_id)return {accepted:false};
      if(worker.stop_reason){await release(worker);return {accepted:true};}
      if(value.state!=='ready_for_upload'){await release(worker,{error:value.error||'capture_held'});return {accepted:true};}
      worker.job=null;await persist();next(worker).catch(error=>fail(worker,error));return {accepted:true};
    }
    return {accepted:false};
  })().then(reply).catch(error=>reply({error:safe(error)}));return true;
});
