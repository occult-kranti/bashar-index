import assert from 'node:assert/strict';
import test from 'node:test';

async function harness(name,badAck=false){
  const listeners=[],messages=[],requests=[];
  const track=new EventTarget();track.stop=()=>track.dispatchEvent(new Event('ended'));
  const stream={getAudioTracks:()=>[track],getVideoTracks:()=>[],getTracks:()=>[track]};
  globalThis.chrome={runtime:{id:'fixture',onMessage:{addListener:fn=>listeners.push(fn)},sendMessage:async value=>{messages.push(value);return {accepted:true};}}};
  Object.defineProperty(globalThis,'navigator',{configurable:true,value:{mediaDevices:{getUserMedia:async()=>stream}}});
  globalThis.AudioContext=class{state='running';createMediaStreamSource(){return {connect(){},disconnect(){}};}resume(){return Promise.resolve();}close(){this.state='closed';return Promise.resolve();}};
  globalThis.MediaRecorder=class extends EventTarget{
    static isTypeSupported(){return true;}state='inactive';
    start(){this.state='recording';}pause(){this.state='paused';}resume(){this.state='recording';}
    stop(){this.state='inactive';queueMicrotask(()=>{const event=new Event('dataavailable');event.data=new Blob(['fixture-audio']);this.dispatchEvent(event);this.dispatchEvent(new Event('stop'));});}
  };
  globalThis.fetch=async(url,options)=>{
    const path=new URL(url).pathname.split('/').at(-1);requests.push({path,options});
    return {ok:true,json:async()=>path==='chunk'?{accepted:true,sequence:badAck?99:Number(options.headers['X-Sequence'])}:path==='finish'?{accepted:true,state:'ready_for_upload'}:{accepted:true}};
  };
  await import(`../offscreen.js?case=${name}`);
  const send=value=>new Promise(resolve=>listeners[0]({target:'offscreen',...value},{id:'fixture'},resolve));
  await send({type:'attach',worker_id:'w',stream_id:'private-memory-only',token:'test-token'});
  return {send,messages,requests};
}
const ID='abcdefghijk';
const state=(t,ended=false)=>({video_id:ID,url_video_id:ID,source_time:t,duration:.2,playback_rate:1,paused:false,ended,ready_state:4,seeking:false,muted:false,volume:1,media_error:null,protected_media:false,is_live:false,ad:false,active_media_count:1});
async function settle(until){for(let i=0;i<100;i++){if(until())return;await new Promise(resolve=>setTimeout(resolve,10));}throw Error('fixture_timeout');}
test('offscreen sends final ordered chunk before complete coverage receipt; output is re-encoded Opus',async()=>{
  const h=await harness('complete');
  await h.send({type:'record',worker_id:'w',job:{capture_id:'capture',video_id:ID,duration_seconds:.2}});
  await h.send({type:'sample',worker_id:'w',state:state(0)});
  await h.send({type:'sample',worker_id:'w',state:state(.2,true)});
  await settle(()=>h.messages.some(x=>x.type==='job_done'));
  assert.deepEqual(h.requests.map(x=>x.path),['chunk','finish']);
  const body=JSON.parse(h.requests[1].options.body);
  assert.equal(body.source_ended,true);assert.equal(body.media_mime_type,'audio/webm;codecs=opus');
  assert.deepEqual(body.coverage_intervals,[[0,.2]]);
  await h.send({type:'release',worker_id:'w'});
});
test('uncertain chunk acknowledgement holds capture and never finishes or retries that chunk',async()=>{
  const h=await harness('bad-ack',true);
  await h.send({type:'record',worker_id:'w',job:{capture_id:'capture',video_id:ID,duration_seconds:.2}});
  await h.send({type:'sample',worker_id:'w',state:state(0)});
  await h.send({type:'sample',worker_id:'w',state:state(.2,true)});
  await settle(()=>h.messages.some(x=>x.type==='job_done'));
  assert.equal(h.requests.filter(x=>x.path==='chunk').length,1);assert(!h.requests.some(x=>x.path==='finish'));
  assert(h.requests.some(x=>x.path==='abort'));assert.equal(h.messages.at(-1).state,'held');
  await h.send({type:'release',worker_id:'w'});
});
