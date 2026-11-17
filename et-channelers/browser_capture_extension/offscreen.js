import {service,CoverageGuard,LIMITS,MIME} from './core.js';
const workers=new Map();
const tell=value=>chrome.runtime.sendMessage({target:'background',...value}).catch(()=>{});
const safe=error=>/^[a-z0-9_]{1,80}$/.test(error?.message||'')?error.message:'recorder_error';
async function attach(value){
  if(workers.has(value.worker_id)||workers.size>=LIMITS.workers)throw Error('worker_limit');
  let stream,context;
  try{
    stream=await navigator.mediaDevices.getUserMedia({audio:{mandatory:{chromeMediaSource:'tab',chromeMediaSourceId:value.stream_id}},video:false});
    if(stream.getAudioTracks().length!==1||stream.getVideoTracks().length)throw Error('audio_track_unavailable');
    context=new AudioContext();const speaker=context.createMediaStreamSource(stream);speaker.connect(context.destination);
    let resumeTimer;
    try{await Promise.race([context.resume(),new Promise((_,reject)=>{resumeTimer=setTimeout(()=>reject(Error('speaker_playback_unavailable')),10000);})]);}
    finally{clearTimeout(resumeTimer);}
    if(context.state!=='running')throw Error('speaker_playback_unavailable');
    const worker={id:value.worker_id,stream,context,speaker,token:value.token,record:null};workers.set(worker.id,worker);
    stream.getAudioTracks()[0].addEventListener('ended',()=>abort(worker,'capture_track_ended'));
    return {ready:true};
  }catch(error){stream?.getTracks().forEach(track=>track.stop());await context?.close();throw error;}
}
async function release(worker){if(!worker)return;clearInterval(worker.record?.watchdog);worker.speaker.disconnect();worker.stream.getTracks().forEach(track=>track.stop());await worker.context.close();workers.delete(worker.id);}
async function abort(worker,reason){
  const record=worker?.record;if(!record||record.aborted||record.finished)return;
  record.aborted=true;clearInterval(record.watchdog);if(record.recorder.state!=='inactive')record.recorder.stop();
  try{await record.chain;}catch{}
  try{await service('/abort',{token:worker.token,body:{capture_id:record.job.capture_id,video_id:record.job.video_id,reason}});}catch{}
  tell({type:'job_done',worker_id:worker.id,capture_id:record.job.capture_id,state:'held',error:reason});
}
async function finish(worker,state){
  const record=worker.record;if(record.aborted||record.finishing||record.finished)return;record.finishing=true;clearInterval(record.watchdog);
  await new Promise(resolve=>{record.recorder.addEventListener('stop',resolve,{once:true});record.recorder.stop();});
  try{
    await record.chain;if(record.aborted)return;
    await tell({type:'worker_state',worker_id:worker.id,state:'validating'});
    let response=await service('/finish',{token:worker.token,body:{capture_id:record.job.capture_id,video_id:record.job.video_id,
      source_duration:record.job.duration_seconds,source_time:state.source_time,source_ended:true,coverage_intervals:record.guard.intervals,
      ads_detected:false,playback_rate:1,media_mime_type:MIME}});
    if(response.accepted!==true)throw Error('finish_not_accepted');
    const deadline=performance.now()+Math.max(120000,record.job.duration_seconds/3*1000+120000);
    while(response.state==='validating'&&!record.aborted&&performance.now()<deadline){await new Promise(resolve=>setTimeout(resolve,2000));if(record.aborted)return;response=await service('/status',{token:worker.token,body:{capture_id:record.job.capture_id}});}
    if(record.aborted)return;
    if(response.state!=='ready_for_upload')throw Error(response.state==='validating'?'validation_timeout':'capture_held');
    record.finished=true;worker.record=null;
    await tell({type:'job_done',worker_id:worker.id,capture_id:record.job.capture_id,state:'ready_for_upload'});
  }catch(error){await abort(worker,safe(error));}
}
function record(worker,job){
  if(worker.record||!MediaRecorder.isTypeSupported(MIME))throw Error('recorder_not_available');
  const recorder=new MediaRecorder(worker.stream,{mimeType:MIME,audioBitsPerSecond:96000});
  const item={job,recorder,guard:new CoverageGuard(job.video_id,job.duration_seconds),chain:Promise.resolve(),sequence:0,
    pendingBytes:0,pendingChunks:0,started:performance.now(),lastSample:performance.now(),aborted:false,finished:false,finishing:false};
  worker.record=item;
  recorder.addEventListener('dataavailable',event=>{
    if(!event.data.size||item.aborted)return;
    if(event.data.size>LIMITS.chunk||item.pendingBytes+event.data.size>LIMITS.pendingBytes||item.pendingChunks>=LIMITS.pendingChunks){abort(worker,'chunk_backpressure');return;}
    const sequence=item.sequence++;item.pendingBytes+=event.data.size;item.pendingChunks++;
    item.chain=item.chain.then(async()=>{
      if(item.aborted)return;
      const response=await service('/chunk',{token:worker.token,body:event.data,headers:{'Content-Type':'application/octet-stream','X-Capture-Id':job.capture_id,'X-Sequence':String(sequence)}});
      if(response.accepted!==true||response.sequence!==sequence)throw Error('chunk_acknowledgement');
    }).catch(error=>{queueMicrotask(()=>abort(worker,safe(error)));throw error;}).finally(()=>{item.pendingBytes-=event.data.size;item.pendingChunks--;});
    item.chain.catch(()=>{});
  });
  recorder.addEventListener('error',()=>abort(worker,'media_recorder_error'));
  recorder.start(1000);
  item.watchdog=setInterval(()=>{
    const now=performance.now();if(item.aborted||item.finishing)return;
    if(now-item.lastSample>2000&&recorder.state==='recording')recorder.pause();
    if(now-item.lastSample>5000)abort(worker,'source_monitor_stale');
    if(now-item.started>(job.duration_seconds*1.5+300)*1000)abort(worker,'capture_wall_limit');
  },500);
  return {ready:true};
}
function sample(worker,state){
  const item=worker?.record;if(!item||item.aborted||item.finishing)return;
  const wall=performance.now()/1000;item.lastSample=performance.now();
  const result=item.guard.sample(state,wall);
  if(result.action==='abort'){abort(worker,result.reason);return;}
  if(result.action==='complete'){finish(worker,state);return;}
  if(result.action==='pause'&&item.recorder.state==='recording'){item.recorder.pause();tell({type:'worker_state',worker_id:worker.id,state:'buffering'});}
  if(result.action==='record'&&item.recorder.state==='paused'){item.recorder.resume();tell({type:'worker_state',worker_id:worker.id,state:'recording'});}
}
chrome.runtime.onMessage.addListener((value,sender,reply)=>{
  if(sender.id!==chrome.runtime.id||sender.tab||value.target!=='offscreen')return;
  (async()=>{
    const worker=workers.get(value.worker_id);
    if(value.type==='attach')return attach(value);
    if(value.type==='record'){if(!worker)throw Error('worker_missing');if(typeof value.token==='string')worker.token=value.token;if(!worker.token)throw Error('pairing_required');return record(worker,value.job);}
    if(value.type==='sample'){sample(worker,value.state);return {accepted:true};}
    if(value.type==='stop'){if(worker)await abort(worker,value.reason||'user_stopped');return {accepted:true};}
    if(value.type==='release'){await release(worker);return {accepted:true};}
    return {accepted:false};
  })().then(reply).catch(error=>reply({error:safe(error)}));return true;
});
