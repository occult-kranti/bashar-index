import {createAcceptedSabrObserver} from './native-observer.js';
import {finishNativeWithProof} from './native-finish.js';
let active=null;
const need=(ok,code)=>{if(!ok)throw Error(code);};
const safe=error=>/^[a-z0-9_]{1,80}$/.test(error?.message||'')?error.message:'native_operation_failed';
const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
function classify(code){return /forbidden/.test(code)?'forbidden':/rate_limited/.test(code)?'rate_limited':/protection_rejected/.test(code)?'bot_check':/user_stopped|cancelled/.test(code)?'aborted':/checksum|mismatch|gap|integrity|ack/.test(code)?'integrity':/fetch|bridge|timeout/.test(code)?'network':'protocol';}
export function startNativePilot({nonce,videoId,maxBytes=64000000}){
  need(!active,'native_pilot_already_active');need(/^[a-f0-9-]{36}$/.test(nonce)&&videoId==='EliqxbbQoRw'&&maxBytes===64000000,'native_pilot_scope');
  const sdk=globalThis.ChannelingNativeSabrV1;need(sdk?.sdkVersion==='5.0.1','native_sdk_missing');
  const controller=new AbortController(),pending=new Map();let sequence=0,observer,context,session,jobStarted=false,sourceTimer,bootstrapVideo,resumedPlayback=false;
  const acknowledge=event=>{const data=event.data;if(event.source!==window||data?.type!=='channel-native-ack'||data.nonce!==nonce)return;const item=pending.get(data.id);if(!item)return;pending.delete(data.id);clearTimeout(item.timer);data.error?item.reject(Error(safe({message:data.error}))):item.resolve(data.value);};
  window.addEventListener('message',acknowledge);
  const rpc=(operation,value={})=>new Promise((resolve,reject)=>{
    if(pending.size>=8){reject(Error('native_bridge_backpressure'));return;}
    const id=sequence++,timer=setTimeout(()=>{pending.delete(id);reject(Error('native_bridge_timeout'));},20000);
    pending.set(id,{resolve,reject,timer});window.postMessage({type:'channel-native-rpc',nonce,id,operation,value},location.origin);
  });
  const state=(phase,extra={})=>rpc('state',{phase,...extra});
  const close=()=>{clearTimeout(sourceTimer);observer?.stop();context?.close();if(resumedPlayback&&bootstrapVideo&&!bootstrapVideo.paused)bootstrapVideo.pause();window.removeEventListener('message',acknowledge);for(const item of pending.values()){clearTimeout(item.timer);item.reject(Error('native_bridge_closed'));}pending.clear();active=null;};
  const run=async()=>{
    try{
      await state('observing_normal_request');
      observer=createAcceptedSabrObserver({sdk,videoId});
      const video=document.getElementById('movie_player')?.querySelector('video');need(video,'source_not_ready');bootstrapVideo=video;
      if(video.paused){resumedPlayback=true;try{await video.play();}catch{throw Error('normal_playback_required');}}
      context=await observer.ready;video.pause();
      const sink={
        reserve:async n=>{need(Number.isSafeInteger(n)&&n>0&&n<=1024*1024,'native_chunk_size');},
        authorizeRequest:proof=>rpc('request',proof),
        write:async({offset,bytes})=>{
          let last;
          for(let position=0;position<bytes.length;position+=768*1024){
            const piece=bytes.subarray(position,position+768*1024);let binary='';
            for(let i=0;i<piece.length;i+=8192)binary+=String.fromCharCode(...piece.subarray(i,i+8192));
            last=await rpc('chunk',{offset:offset+position,base64:btoa(binary)});
            need(last.acknowledgedBytes===offset+position+piece.length,'native_chunk_ack');
          }
          return last;
        },
        segment:proof=>rpc('segment',proof),
        finish:async proof=>{
          await state('validating_native_audio');
          return finishNativeWithProof({rpc,proof,binding:session.sourceBinding,durationMs:context.source.durationMs});
        },
        retain:async proof=>{if(jobStarted)await rpc('retain',{error_class:classify(proof.error)});}
      };
      session=await sdk.openNativeSabr({sdk:sdk.sdk,source:context.source,fetchInAcceptedContext:context.fetchInAcceptedContext,
        getCurrentVideoPoToken:context.getCurrentVideoPoToken,assertAcceptedContext:context.assertAcceptedContext,sink,maxBytes,
        maxRequests:1000,requireRequestAuthorization:true,signal:controller.signal});
      // Only public identity/metadata and hashes cross into the extension.
      const begin=await rpc('begin',{identity:session.identity,transportKind:'sabr_reassembled',outputBudgetBytes:maxBytes,metadata:context.metadata});
      need(begin.sourceBindingSha256===session.sourceBinding,'native_begin_binding');jobStarted=true;
      await state('downloading_native_audio',{video_id:videoId,source_binding_sha256:session.sourceBinding,identity:session.identity,token_present:true,credentials_mode:context.credentialsMode});
      sourceTimer=setTimeout(()=>controller.abort(),20*60*1000);
      const result=await session.run();clearTimeout(sourceTimer);context.close();
      await state('uploading_verified_native_audio',{bytes:result.bytes});
      const deadline=Date.now()+20*60*1000;
      while(Date.now()<deadline){const status=await rpc('status');need(!status.error,'native_upload_retained');
        if(status.driveVerified){await state('drive_verified',{bytes:result.bytes});return;}await sleep(2000);}
      throw Error('native_upload_status_timeout');
    }catch(error){
      if(session&&!session.complete){try{await session.abort(safe(error));}catch{}}
      if(jobStarted){try{await rpc('retain',{error_class:classify(safe(error))});}catch{}}
      try{await state('held',{error:safe(error),...(session?{source_binding_sha256:session.sourceBinding,bytes:session.acknowledgedBytes,diagnostics:session.diagnostics()}:{} )});}catch{}
    }finally{close();}
  };
  active={stop:()=>{controller.abort();observer?.stop('user_stopped');void session?.abort('user_stopped');}};void run();return {started:true,mode:'native_sabr_single_pilot',reencoded:false};
}
Object.defineProperty(globalThis,'ChannelingNativePilotV1',{value:Object.freeze({start:startNativePilot,stop:()=>active?.stop()}),configurable:false});
