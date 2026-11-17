import {NativeGatewayClient,safeNativeError} from './native-gateway-client.js';
import {validateNativeRpc} from './native-rpc.js';
const sessions=new Map();
const safeState=value=>{
  const result={phase:/^[a-z0-9_]{1,80}$/.test(value.phase||'')?value.phase:'held',updated_at:new Date().toISOString()};
  for(const key of ['video_id','source_binding_sha256','bytes','token_present','credentials_mode','identity','error','diagnostics'])if(value[key]!==undefined)result[key]=value[key];
  return result;
};
async function show(tabId,text,title){try{await chrome.action.setBadgeText({tabId,text});await chrome.action.setTitle({tabId,title});}catch{}}
export async function startNativeInTab(tab){
  const existing=sessions.get(tab.id);
  if(existing){await chrome.scripting.executeScript({target:{tabId:tab.id},world:'MAIN',func:()=>globalThis.ChannelingNativePilotV1?.stop()});return;}
  if(sessions.size)throw Error('native_pilot_already_active');
  const videoId=new URL(tab.url).searchParams.get('v');if(videoId!=='EliqxbbQoRw')throw Error('native_pilot_video_scope');
  const client=new NativeGatewayClient();await client.pair();
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
