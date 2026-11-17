import assert from 'node:assert/strict';
import test from 'node:test';
import {createAcceptedSabrObserver} from '../native-observer.js';
const ID='EliqxbbQoRw',URL='https://rr1.googlevideo.com/videoplayback?id=source-id&n=already-deciphered';
const tags=btoa('original');
function setup({original=true,selectedTags=tags,status=200}={}){
  let calls=0,decodes=0;const token=new Uint8Array([7,8,9]),config=new Uint8Array([1,2,3]);
  const format={itag:251,lastModified:'1234',xtags:tags,mimeType:'audio/webm; codecs="opus"',audioQuality:'AUDIO_QUALITY_MEDIUM',hasAudio:true,hasVideo:false,hasText:false,approxDurationMs:10000};
  const request={videoPlaybackUstreamerConfig:config,streamerContext:{poToken:token,clientInfo:{clientName:1,clientVersion:'2.20261116.00.00'}},selectedAudioFormatIds:[{itag:251,lastModified:'1234',xtags:selectedTags}]};
  const response={videoDetails:{videoId:ID,title:'Public title'},playabilityStatus:{status:'OK'},streamingData:{serverAbrStreamingUrl:URL,adaptiveFormats:[format]},playerConfig:{mediaCommonConfig:{mediaUstreamerRequestConfig:{videoPlaybackUstreamerConfig:btoa(String.fromCharCode(...config))}}}};
  const video={duration:10,paused:false,pause(){this.paused=true;}};
  const player={getVideoData:()=>({video_id:ID}),getPlayerResponse:()=>response,querySelector:()=>video,classList:{contains:()=>false}};
  class XHR extends EventTarget{withCredentials=true;open(){}send(){calls++;this.status=status;queueMicrotask(()=>this.dispatchEvent(new Event('loadend')));}getResponseHeader(){return 'application/vnd.yt-ump';}}
  const scope={location:{href:`https://www.youtube.com/watch?v=${ID}`},document:{getElementById:()=>player},XMLHttpRequest:XHR,
    fetch(){calls++;return Promise.resolve(new Response(null,{status,headers:{'content-type':'application/vnd.yt-ump'}}));}};
  const sdk={VideoPlaybackAbrRequest:{decode(){decodes++;return request;}},FormatXTags:{decode:()=>({xtags:[{key:'acont',value:original?'original':'dubbed-auto'}]})},buildSabrFormat:x=>x};
  return {scope,sdk,request,response,video,token,calls:()=>calls,decodes:()=>decodes};
}
test('passive fetch binds full format/config/current video and restores wrappers without replay',async()=>{
  const h=setup(),fetch=h.scope.fetch,open=h.scope.XMLHttpRequest.prototype.open;
  const observer=createAcceptedSabrObserver({...h,videoId:ID});
  const returned=h.scope.fetch(URL,{method:'POST',body:new Uint8Array([1]),credentials:'include'});await returned;
  const context=await observer.ready;assert.equal(h.calls(),1);assert.equal(context.source.audioFormat.xtags,tags);assert.equal(context.credentialsMode,'include');
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
