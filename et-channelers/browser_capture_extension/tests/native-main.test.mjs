import test from 'node:test';
import assert from 'node:assert/strict';
import {startNativePilot} from '../native-main.js';
import {umpSdk,sps} from './native-ump-fixture.mjs';

test('one-click MAIN bootstrap forwards native bytes/public proofs only and waits for Drive status',async()=>{
  const id='EliqxbbQoRw',binding='a'.repeat(64),calls=[],states=[],listeners=new Set();let normalRequests=0,played=0,paused=0,acknowledged=0;
  const token=new Uint8Array([111,112,113]),config=new Uint8Array([1,2,3]),xtags=btoa('original');
  const format={itag:140,lastModified:'123',xtags,mimeType:'audio/mp4; codecs="mp4a.40.2"',audioQuality:'AUDIO_QUALITY_MEDIUM',hasAudio:true,hasVideo:false,hasText:false,approxDurationMs:10000};
  const response={videoDetails:{videoId:id,title:'Published source'},playabilityStatus:{status:'OK'},streamingData:{serverAbrStreamingUrl:'https://rr1.googlevideo.com/videoplayback?id=private-id&n=private-signature',adaptiveFormats:[format]},playerConfig:{mediaCommonConfig:{mediaUstreamerRequestConfig:{videoPlaybackUstreamerConfig:btoa(String.fromCharCode(...config))}}}};
  const video={duration:10,paused:true,async play(){played++;this.paused=false;
    await window.fetch(response.streamingData.serverAbrStreamingUrl,{method:'POST',body:new Uint8Array([1]),credentials:'include'});
    await new Promise(resolve=>setTimeout(resolve,10));assert.equal(paused,0);assert.ok(!calls.some(x=>x.operation==='begin'));
    await window.fetch(response.streamingData.serverAbrStreamingUrl,{method:'POST',body:new Uint8Array([2]),credentials:'include'});
  },pause(){paused++;this.paused=true;}};
  globalThis.location={href:`https://www.youtube.com/watch?v=${id}`,origin:'https://www.youtube.com'};
  globalThis.document={getElementById:()=>({getVideoData:()=>({video_id:id}),getPlayerResponse:()=>response,querySelector:()=>video,classList:{contains:()=>false}})};
  globalThis.window={location,document,fetch:async()=>{normalRequests++;return new Response(sps(normalRequests===1?2:1),{status:200,headers:{'content-type':'application/vnd.yt-ump'}});},
    addEventListener:(type,fn)=>listeners.add(fn),removeEventListener:(type,fn)=>listeners.delete(fn),
    postMessage(value){calls.push(value);const op=value.operation;let result;
      if(op==='state'){states.push(value.value.phase);result={accepted:true};}
      else if(op==='begin'){result={sourceBindingSha256:binding};}
      else if(op==='request'){result={...value.value,sourceRequests:1,authorized:true};}
      else if(op==='chunk'){assert.equal(value.value.offset,acknowledged);const count=atob(value.value.base64).length;assert(count<=768*1024);acknowledged+=count;result={acknowledgedBytes:acknowledged};}
      else if(op==='status'){result={sourceBindingSha256:binding,nativeProof:{bytes:acknowledged,sha256:'b'.repeat(64),md5:'c'.repeat(32)},driveVerified:true};}
      else result={accepted:true};
      queueMicrotask(()=>{for(const fn of listeners)fn({source:window,data:{type:'channel-native-ack',nonce:value.nonce,id:value.id,value:result}});});
    }};
  globalThis.ChannelingNativeSabrV1={sdkVersion:'5.0.1',sdk:{},
    UmpReader:umpSdk.UmpReader,StreamProtectionStatus:umpSdk.StreamProtectionStatus,
    VideoPlaybackAbrRequest:{decode:()=>({videoPlaybackUstreamerConfig:config,streamerContext:{poToken:token,clientInfo:{clientName:1,clientVersion:'2.0'}},selectedAudioFormatIds:[format]})},
    FormatXTags:{decode:()=>({xtags:[{key:'acont',value:'original'}]})},buildSabrFormat:x=>x,
    async openNativeSabr(options){assert.deepEqual(await options.getCurrentVideoPoToken(id),token);assert.equal(options.requireRequestAuthorization,true);assert.equal(options.maxRequests,1000);
      return {sourceBinding:binding,identity:{videoId:id},complete:false,async abort(){},async run(){
        await options.sink.authorizeRequest({sourceBindingSha256:binding,requestSequence:1});
        await options.sink.reserve(1024*1024);await options.sink.write({offset:0,seq:0,bytes:new Uint8Array(1024*1024)});
        await options.sink.segment({number:0});await options.sink.finish({sourceBindingSha256:binding,bytes:1024*1024});this.complete=true;return {bytes:1024*1024};}};
    }};
  const result=startNativePilot({nonce:'12345678-1234-1234-1234-123456789abc',videoId:id});assert.equal(result.reencoded,false);
  for(let i=0;i<100&&!states.includes('drive_verified');i++)await new Promise(resolve=>setTimeout(resolve,5));
  assert.deepEqual(states,['observing_normal_request','downloading_native_audio','validating_native_audio','uploading_verified_native_audio','drive_verified']);
  assert.equal(normalRequests,2);assert.equal(played,1);assert.equal(paused,1);assert.equal(acknowledged,1024*1024);
  assert.equal(calls.filter(x=>x.operation==='chunk').length,2);assert(!JSON.stringify(calls).includes('private-signature'));assert(!JSON.stringify(calls).includes('private-id'));
  const acceptance=calls.find(x=>x.operation==='begin').value.metadata.native_source_acceptance;
  assert.equal(acceptance.sps_status,1);assert.notEqual(acceptance.observer_session_id,'12345678-1234-1234-1234-123456789abc');
});
