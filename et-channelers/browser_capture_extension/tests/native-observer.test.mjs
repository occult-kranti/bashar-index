import assert from 'node:assert/strict';
import test from 'node:test';
import {createAcceptedSabrObserver} from '../native-observer.js';
import {umpSdk,sps} from './native-ump-fixture.mjs';
const ID='EliqxbbQoRw',URL='https://rr1.googlevideo.com/videoplayback?id=source-id&n=already-deciphered';
const tags=btoa('original');
function setup({original=true,selectedTags=tags,status=200,protection=1}={}){
  let calls=0,decodes=0;const token=new Uint8Array([7,8,9]),config=new Uint8Array([1,2,3]);
  const format={itag:251,lastModified:'1234',xtags:tags,mimeType:'audio/webm; codecs="opus"',audioQuality:'AUDIO_QUALITY_MEDIUM',hasAudio:true,hasVideo:false,hasText:false,approxDurationMs:10000};
  const request={videoPlaybackUstreamerConfig:config,streamerContext:{poToken:token,clientInfo:{clientName:1,clientVersion:'2.20261116.00.00'}},selectedAudioFormatIds:[{itag:251,lastModified:'1234',xtags:selectedTags}]};
  const response={videoDetails:{videoId:ID,title:'Public title'},playabilityStatus:{status:'OK'},streamingData:{serverAbrStreamingUrl:URL,adaptiveFormats:[format]},playerConfig:{mediaCommonConfig:{mediaUstreamerRequestConfig:{videoPlaybackUstreamerConfig:btoa(String.fromCharCode(...config))}}}};
  const video={duration:10,paused:false,pause(){this.paused=true;}};
  const player={getVideoData:()=>({video_id:ID}),getPlayerResponse:()=>response,querySelector:()=>video,classList:{contains:()=>false}};
  class XHR extends EventTarget{withCredentials=true;responseType='arraybuffer';open(){}send(){calls++;this.status=status;this.response=sps(protection).buffer;queueMicrotask(()=>this.dispatchEvent(new Event('loadend')));}getResponseHeader(){return 'application/vnd.yt-ump';}}
  const scope={location:{href:`https://www.youtube.com/watch?v=${ID}`},document:{getElementById:()=>player},XMLHttpRequest:XHR,
    fetch(){calls++;return Promise.resolve(new Response(sps(protection),{status,headers:{'content-type':'application/vnd.yt-ump'}}));}};
  const sdk={UmpReader:umpSdk.UmpReader,StreamProtectionStatus:umpSdk.StreamProtectionStatus,VideoPlaybackAbrRequest:{decode(){decodes++;return request;}},FormatXTags:{decode:()=>({xtags:[{key:'acont',value:original?'original':'dubbed-auto'}]})},buildSabrFormat:x=>x};
  return {scope,sdk,request,response,video,token,calls:()=>calls,decodes:()=>decodes};
}
test('passive fetch binds full format/config/current video and restores wrappers without replay',async()=>{
  const h=setup(),fetch=h.scope.fetch,open=h.scope.XMLHttpRequest.prototype.open;
  const observer=createAcceptedSabrObserver({...h,videoId:ID});
  const returned=h.scope.fetch(URL,{method:'POST',body:new Uint8Array([1]),credentials:'include'});await returned;
  const context=await observer.ready;assert.equal(h.calls(),1);assert.equal(context.source.audioFormat.xtags,tags);assert.equal(context.credentialsMode,'include');
  assert.equal(context.metadata.native_source_acceptance.sps_status,1);assert.equal(context.metadata.native_source_acceptance.complete_response,true);
  assert.match(context.metadata.native_source_acceptance.observer_session_id,/^[a-f0-9-]{36}$/);
  assert.equal(h.scope.fetch,fetch);assert.equal(h.scope.XMLHttpRequest.prototype.open,open);assert.deepEqual(await context.getCurrentVideoPoToken(ID),h.token);
  context.close();await assert.rejects(context.getCurrentVideoPoToken(ID),/source_changed/);
});
test('same itag with different xtags and inferred original never establishes a source',async()=>{
  for(const settings of [{selectedTags:btoa('other')},{original:false}]){
    const h=setup(settings),observer=createAcceptedSabrObserver({...h,videoId:ID,timeoutMs:15});
    await h.scope.fetch(URL,{method:'POST',body:new Uint8Array([1])});
    await assert.rejects(observer.ready,/observer_(original_format_unproven|selected_format_mismatch)/);assert.equal(h.calls(),1);
  }
});
test('oversized body is never decoded and original request still runs once',async()=>{
  const h=setup(),observer=createAcceptedSabrObserver({...h,videoId:ID,timeoutMs:15});
  await h.scope.fetch(URL,{method:'POST',body:new Uint8Array(65537)});
  await assert.rejects(observer.ready,/observer_body_too_large/);assert.equal(h.decodes(),0);assert.equal(h.calls(),1);
});
test('XHR keeps ordinary credentials mode and original open/send behavior',async()=>{
  const h=setup(),observer=createAcceptedSabrObserver({...h,videoId:ID});const xhr=new h.scope.XMLHttpRequest();xhr.open('POST',URL);xhr.send(new Uint8Array([1]));
  const context=await observer.ready;assert.equal(context.credentialsMode,'include');assert.equal(h.calls(),1);context.close();
});
test('caption/telemetry refusal is unrelated; source403 stops without replay',async()=>{
  const h=setup({status:429}),observer=createAcceptedSabrObserver({...h,videoId:ID,timeoutMs:15});
  await h.scope.fetch('https://www.youtube.com/api/timedtext',{method:'GET'});
  await assert.rejects(observer.ready,/normal_request_not_observed/);assert.equal(h.decodes(),0);
  const source=setup({status:403}),blocked=createAcceptedSabrObserver({...source,videoId:ID});
  await source.scope.fetch(URL,{method:'POST',body:new Uint8Array([1])});
  await assert.rejects(blocked.ready,/source_forbidden/);assert.equal(source.calls(),1);
});
test('source change or config mismatch cannot bind observed session',async()=>{
  const h=setup(),observer=createAcceptedSabrObserver({...h,videoId:ID,timeoutMs:15});h.request.videoPlaybackUstreamerConfig=new Uint8Array([9]);
  await h.scope.fetch(URL,{method:'POST',body:new Uint8Array([1])});await assert.rejects(observer.ready,/observer_config_mismatch/);
  const changed=setup(),pending=createAcceptedSabrObserver({...changed,videoId:ID,timeoutMs:600});changed.scope.location.href='https://www.youtube.com/watch?v=abcdefghijk';
  await assert.rejects(pending.ready,/source_changed/);
});
test('HTTP200/SPS2 is not accepted; a fresh matching request SPS1 supplies only its own token',async()=>{
  const pending=setup({protection:2}),held=createAcceptedSabrObserver({...pending,videoId:ID,timeoutMs:30});
  await pending.scope.fetch(URL,{method:'POST',body:new Uint8Array([1])});
  await assert.rejects(held.ready,/normal_protection_pending/);assert.equal(pending.calls(),1);
  const h=setup();let count=0;
  h.scope.fetch=function(){count++;return Promise.resolve(new Response(sps(count===1?2:1),{headers:{'content-type':'application/vnd.yt-ump'}}));};
  const observer=createAcceptedSabrObserver({...h,videoId:ID,timeoutMs:200});let resolved=false;observer.ready.then(()=>{resolved=true;});
  await h.scope.fetch(URL,{method:'POST',body:new Uint8Array([1])});await new Promise(resolve=>setTimeout(resolve,10));assert.equal(resolved,false);
  h.request.streamerContext.poToken=new Uint8Array([10,11,12]);
  await h.scope.fetch(URL,{method:'POST',body:new Uint8Array([2])});const accepted=await observer.ready;
  assert.deepEqual(await accepted.getCurrentVideoPoToken(ID),new Uint8Array([10,11,12]));assert.equal(count,2);accepted.close();
});
test('ordinary SPS3 stops without replay and original fetch promise/body stay usable',async()=>{
  const h=setup({protection:3}),original=h.scope.fetch;let originalPromise;
  h.scope.fetch=function(){originalPromise=original.apply(this,arguments);return originalPromise;};
  const observer=createAcceptedSabrObserver({...h,videoId:ID});
  const returned=h.scope.fetch(URL,{method:'POST',body:new Uint8Array([1])});assert.equal(returned,originalPromise);
  assert.deepEqual(new Uint8Array(await (await returned).arrayBuffer()),sps(3));
  await assert.rejects(observer.ready,/stream_protection_rejected/);assert.equal(h.calls(),1);
});
test('configuration changed while reading an accepted response is not adopted',async()=>{
  const h=setup();let body;
  h.scope.fetch=()=>Promise.resolve(new Response(new ReadableStream({start(c){body=c;}}),{headers:{'content-type':'application/vnd.yt-ump'}}));
  const observer=createAcceptedSabrObserver({...h,videoId:ID,timeoutMs:50});
  const original=await h.scope.fetch(URL,{method:'POST',body:new Uint8Array([1])});
  await new Promise(resolve=>setImmediate(resolve));
  h.response.playerConfig.mediaCommonConfig.mediaUstreamerRequestConfig.videoPlaybackUstreamerConfig=btoa('new');
  body.enqueue(sps(1));body.close();await original.arrayBuffer();
  await assert.rejects(observer.ready,/observer_config_mismatch/);
});
test('stopping a pending clone restores wrappers without cancelling the player response',async()=>{
  const h=setup();let body,cancelled=0;
  h.scope.fetch=()=>Promise.resolve(new Response(new ReadableStream({start(c){body=c;},cancel(){cancelled++;}}),{headers:{'content-type':'application/vnd.yt-ump'}}));
  const originalFetch=h.scope.fetch,observer=createAcceptedSabrObserver({...h,videoId:ID});
  const original=await h.scope.fetch(URL,{method:'POST',body:new Uint8Array([1])});
  await new Promise(resolve=>setImmediate(resolve));observer.stop('fixture_stop');
  await assert.rejects(observer.ready,/fixture_stop/);assert.equal(h.scope.fetch,originalFetch);assert.equal(cancelled,0);
  body.enqueue(sps(1));body.close();assert.deepEqual(new Uint8Array(await original.arrayBuffer()),sps(1));assert.equal(cancelled,0);
});
test('unowned streaming init.body is never read, locked, or cancelled by observer',async()=>{
  const h=setup();let consumed=0,cancelled=0;
  const body=new ReadableStream({start(c){c.enqueue(new Uint8Array([1,2,3]));c.close();},cancel(){cancelled++;}});
  h.scope.fetch=async(input,init)=>{await new Promise(resolve=>setTimeout(resolve,15));assert.equal(init.body.locked,false);
    const reader=init.body.getReader();for(;;){const part=await reader.read();if(part.done)break;consumed+=part.value.length;}reader.releaseLock();
    return new Response(sps(1),{headers:{'content-type':'application/vnd.yt-ump'}});};
  const observer=createAcceptedSabrObserver({...h,videoId:ID,timeoutMs:40});await h.scope.fetch(URL,{method:'POST',body});
  await assert.rejects(observer.ready,/observer_body_unsupported/);assert.equal(consumed,3);assert.equal(cancelled,0);
});
test('owned Request clone can be inspected without consuming original request bytes',async()=>{
  const h=setup();let originalBytes;
  h.scope.fetch=async request=>{originalBytes=new Uint8Array(await request.arrayBuffer());return new Response(sps(1),{headers:{'content-type':'application/vnd.yt-ump'}});};
  const observer=createAcceptedSabrObserver({...h,videoId:ID});await h.scope.fetch(new Request(URL,{method:'POST',body:new Uint8Array([4,5,6])}));
  const accepted=await observer.ready;assert.deepEqual(originalBytes,new Uint8Array([4,5,6]));accepted.close();
});
test('detached XHR response and public-metadata errors hold safely without page callback errors or hanging',async()=>{
  const detached=setup(),send=detached.scope.XMLHttpRequest.prototype.send;
  detached.scope.XMLHttpRequest.prototype.send=function(body){send.call(this,body);structuredClone(this.response,{transfer:[this.response]});};
  const observer=createAcceptedSabrObserver({...detached,videoId:ID,timeoutMs:20});
  const xhr=new detached.scope.XMLHttpRequest();xhr.open('POST',URL);xhr.send(new Uint8Array([1]));
  await assert.rejects(observer.ready,/normal_request_not_accepted/);
  const h=setup();Object.defineProperty(h.response.videoDetails,'title',{get(){throw Error('PRIVATE');}});
  const badMetadata=createAcceptedSabrObserver({...h,videoId:ID});await h.scope.fetch(URL,{method:'POST',body:new Uint8Array([1])});
  await assert.rejects(badMetadata.ready,/observer_metadata_unavailable/);
});
test('stop detaches a pending XHR observer immediately without aborting the player request',async()=>{
  const h=setup(),proto=h.scope.XMLHttpRequest.prototype;let listeners=0,aborts=0;
  const add=proto.addEventListener,remove=proto.removeEventListener;
  proto.addEventListener=function(...args){listeners++;return add.apply(this,args);};
  proto.removeEventListener=function(...args){listeners--;return remove.apply(this,args);};
  proto.send=function(){};proto.abort=()=>{aborts++;};
  const observer=createAcceptedSabrObserver({...h,videoId:ID}),xhr=new h.scope.XMLHttpRequest();xhr.open('POST',URL);xhr.send(new Uint8Array([1]));
  await new Promise(resolve=>setImmediate(resolve));assert.equal(listeners,1);observer.stop('fixture_stop');
  await assert.rejects(observer.ready,/fixture_stop/);assert.equal(listeners,0);assert.equal(aborts,0);
  assert.deepEqual(h.token,new Uint8Array([7,8,9]));
});
