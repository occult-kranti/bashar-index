import {NativeGatewayClient,safeNativeError} from './native-gateway-client.js';
import {validateNativeRpc} from './native-rpc.js';
const sessions=new Map();
const NORMAL_TARGET='EliqxbbQoRw';
let controlStarting=false;
let reloadPending=false;
let pairing=false;
// Runs read-only in the existing target's MAIN world. Never returns a URL,
// response object, format, token, header or account data, and never plays media.
export function readNormalTarget(videoId){
  const player=document.getElementById('movie_player'),video=player?.querySelector('video');
  const data=player?.getVideoData?.(),response=player?.getPlayerResponse?.();
  const liveId=data?.video_id,locationId=new URL(location.href).searchParams.get('v');
  const status=response?.playabilityStatus?.status;
  const bounded=value=>typeof value==='number'&&Number.isFinite(value)&&value>=0&&value<=1e7?value:null;
  return {video_id:liveId===videoId?videoId:null,
    target_matches:liveId===videoId&&locationId===videoId&&response?.videoDetails?.videoId===videoId,
    duration_seconds:bounded(video?.duration),current_time:bounded(video?.currentTime),
    paused:typeof video?.paused==='boolean'?video.paused:null,
    ads_detected:!!player?.classList?.contains('ad-showing'),media_keys_present:!!video?.mediaKeys,
    is_live:response?.videoDetails?.isLive===true||response?.videoDetails?.isLiveContent===true,
    playability_status:['OK','UNPLAYABLE','LOGIN_REQUIRED','LIVE_STREAM_OFFLINE','ERROR'].includes(status)?status:'UNKNOWN'};
}
async function inspectNormalTarget(){
  const granted=await chrome.permissions.contains({origins:['https://www.youtube.com/*']});
  const report={permission_granted:granted===true,target_count:0,active_job:sessions.size>0||controlStarting||pairing||reloadPending,eligible:false};
  if(!granted)return {report:{...report,error:'youtube_permission_not_granted'}};
  const stored=await chrome.storage.session.get(['researchWorkers','researchNativeStatus']);
  report.active_job ||= !!stored.researchWorkers?.length||!!(stored.researchNativeStatus&&!['held','drive_verified'].includes(stored.researchNativeStatus.phase));
  const tabs=(await chrome.tabs.query({url:'https://www.youtube.com/watch*'})).filter(tab=>{
    try{const u=new URL(tab.url);return u.origin==='https://www.youtube.com'&&u.pathname==='/watch'&&u.searchParams.get('v')===NORMAL_TARGET;}catch{return false;}
  });
  report.target_count=tabs.length;
  if(report.active_job)return {report:{...report,error:'native_pilot_already_active'}};
  if(tabs.length!==1)return {report:{...report,error:tabs.length?'multiple_target_tabs':'target_tab_missing'}};
  const results=await chrome.scripting.executeScript({target:{tabId:tabs[0].id},world:'MAIN',func:readNormalTarget,args:[NORMAL_TARGET]});
  const raw=results?.[0]?.result;
  if(!raw||Object.keys(raw).length!==9)throw Error('normal_context_response');
  const number=x=>x===null||typeof x==='number'&&Number.isFinite(x)&&x>=0&&x<=1e7;
  if(![null,NORMAL_TARGET].includes(raw.video_id)||!number(raw.duration_seconds)||!number(raw.current_time)||
    ![null,true,false].includes(raw.paused)||!['target_matches','ads_detected','media_keys_present','is_live'].every(k=>typeof raw[k]==='boolean')||
    !['OK','UNPLAYABLE','LOGIN_REQUIRED','LIVE_STREAM_OFFLINE','ERROR','UNKNOWN'].includes(raw.playability_status))throw Error('normal_context_response');
  for(const key of ['video_id','target_matches','duration_seconds','current_time','paused','ads_detected','media_keys_present','is_live','playability_status'])report[key]=raw[key];
  report.eligible=report.target_matches&&report.duration_seconds>0&&!report.ads_detected&&!report.media_keys_present&&!report.is_live&&report.playability_status==='OK';
  if(!report.eligible)report.error='target_not_ready';
  return {report,tab:tabs[0]};
}
const safeState=value=>{
  const result={phase:/^[a-z0-9_]{1,80}$/.test(value.phase||'')?value.phase:'held',updated_at:new Date().toISOString()};
  for(const key of ['video_id','source_binding_sha256','bytes','token_present','credentials_mode','identity','error','diagnostics'])if(value[key]!==undefined)result[key]=value[key];
  return result;
};
async function show(tabId,text,title){try{await chrome.action.setBadgeText({tabId,text});await chrome.action.setTitle({tabId,title});}catch{}}
export async function startNativeInTab(tab){
  if(reloadPending)throw Error('native_reload_pending');
  if(pairing)throw Error('native_pilot_already_active');
  const existing=sessions.get(tab.id);
  if(existing){await chrome.scripting.executeScript({target:{tabId:tab.id},world:'MAIN',func:()=>globalThis.ChannelingNativePilotV1?.stop()});return;}
  if(sessions.size)throw Error('native_pilot_already_active');
  const videoId=new URL(tab.url).searchParams.get('v');if(videoId!=='EliqxbbQoRw')throw Error('native_pilot_video_scope');
  const client=new NativeGatewayClient();pairing=true;
  try{await client.pair();}finally{pairing=false;}
  const nonce=crypto.randomUUID(),session={tabId:tab.id,nonce,client,videoId};sessions.set(tab.id,session);
  try{
    await chrome.scripting.executeScript({target:{tabId:tab.id},files:['native-isolated-bridge.iife.js']});
    await chrome.tabs.sendMessage(tab.id,{target:'native-isolated',type:'configure',nonce});
    await chrome.scripting.executeScript({target:{tabId:tab.id},world:'MAIN',files:['vendor/channeling-native-sabr-v1.iife.js','native-main.iife.js']});
    const result=await chrome.scripting.executeScript({target:{tabId:tab.id},world:'MAIN',func:value=>globalThis.ChannelingNativePilotV1.start(value),args:[{nonce,videoId,maxBytes:64000000}]});
    if(!result?.[0]?.result?.started)throw Error('native_pilot_not_started');
    await chrome.runtime.openOptionsPage();
  }catch(error){sessions.delete(tab.id);await chrome.storage.session.set({researchNativeStatus:{phase:'held',error:safeNativeError(error),video_id:videoId,updated_at:new Date().toISOString()}});throw error;}
}
export function installNativeBackground(){
  chrome.runtime.onMessage.addListener((value,sender,reply)=>{
    if(sender.id!==chrome.runtime.id||sender.url!==chrome.runtime.getURL('status.html')||value?.target!=='native-controls')return;
    (async()=>{
      if(Object.keys(value).length!==2||!['inspect_target','start_target','activity','reload_helper'].includes(value.operation))throw Error('native_control_schema');
      if(value.operation==='activity')return {active:sessions.size>0||controlStarting||pairing||reloadPending};
      if(value.operation==='reload_helper'){
        // Reserve the idle state before awaiting storage; another options page
        // or toolbar activation cannot start pairing during this check.
        if(sessions.size||controlStarting||pairing||reloadPending)throw Error('native_pilot_already_active');
        reloadPending=true;
        try{
          const stored=await chrome.storage.session.get(['researchWorkers','researchNativeStatus']);
          if(stored.researchWorkers?.length||(stored.researchNativeStatus&&!['held','drive_verified'].includes(stored.researchNativeStatus.phase)))throw Error('native_pilot_already_active');
          return {reload:true};
        }catch(error){reloadPending=false;throw error;}
      }
      const {report,tab}=await inspectNormalTarget();
      if(value.operation==='inspect_target')return report;
      if(!report.eligible)throw Error(report.error||'target_not_ready');
      if(controlStarting||sessions.size||reloadPending)throw Error('native_pilot_already_active');
      controlStarting=true;
      try{await startNativeInTab(tab);return {...report,started:true};}finally{controlStarting=false;}
    })().then(result=>{reply({value:result});if(result.reload)chrome.runtime.reload();}).catch(error=>reply({error:safeNativeError(error)}));return true;
  });
  chrome.runtime.onMessage.addListener((value,sender,reply)=>{
    if(sender.id!==chrome.runtime.id||value.target!=='native-background')return;
    (async()=>{
      const session=sessions.get(sender.tab?.id);
      if(!session||value.nonce!==session.nonce)throw Error('native_worker_missing');
      validateNativeRpc(value.operation,value.value);
      if(value.operation==='state'){
        const status=safeState(value.value);status.video_id=session.videoId;
        await chrome.storage.session.set({researchNativeStatus:status});
        const badge=status.phase==='held'?'ERR':status.phase==='drive_verified'?'DONE':status.phase==='observing_normal_request'?'WAIT':status.phase.includes('download')?'NATIVE':'CHECK';
        await show(session.tabId,badge,status.phase==='held'?`Native audio held: ${status.error||'operation_failed'}`:`Native audio: ${status.phase.replaceAll('_',' ')}`);
        if(['held','drive_verified'].includes(status.phase))sessions.delete(session.tabId);
        return {accepted:true};
      }
      if(!['begin','request','chunk','segment','finish','retain','status'].includes(value.operation))throw Error('native_rpc_operation');
      return session.client.call(value.operation,value.value);
    })().then(result=>reply({value:result})).catch(error=>reply({error:safeNativeError(error)}));return true;
  });
  chrome.tabs.onRemoved.addListener(tabId=>{const session=sessions.get(tabId);if(!session)return;sessions.delete(tabId);
    void session.client.call('retain',{error_class:'aborted'}).catch(()=>{});
    void chrome.storage.session.set({researchNativeStatus:{phase:'held',error:'source_tab_closed',video_id:session.videoId,updated_at:new Date().toISOString()}});
  });
}
