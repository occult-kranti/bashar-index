export const SERVICE = 'http://127.0.0.1:8768/capture/v1';
export const MIME = 'audio/webm;codecs=opus';
export const LIMITS = Object.freeze({workers:4,chunk:1024*1024,pendingBytes:4*1024*1024,pendingChunks:8});
export const VIDEO_ID = /^[A-Za-z0-9_-]{11}$/;
export function videoFromUrl(value) {
  try { const url=new URL(value); if(url.protocol!=='https:'||url.hostname!=='www.youtube.com'||url.port)return null;
    const id=url.pathname==='/watch'?url.searchParams.get('v'):url.pathname.startsWith('/shorts/')?url.pathname.split('/')[2]:null;
    return VIDEO_ID.test(id||'')?id:null;
  } catch { return null; }
}
export function validateJob(job) {
  if(!job||typeof job.capture_id!=='string'||!/^[A-Za-z0-9_-]{1,128}$/.test(job.capture_id)||!VIDEO_ID.test(job.video_id||''))throw Error('invalid_job');
  if(videoFromUrl(job.watch_url)!==job.video_id)throw Error('invalid_watch_url');
  if(job.duration_seconds!=null&&(!Number.isFinite(job.duration_seconds)||job.duration_seconds<0))throw Error('invalid_duration');
  return {...job,watch_url:`https://www.youtube.com/watch?v=${job.video_id}`};
}
export function coverageComplete(intervals,duration) {
  if(!Number.isFinite(duration)||duration<=0||!Array.isArray(intervals)||!intervals.length)return false;
  let end=0;
  for(const pair of intervals){if(!Array.isArray(pair)||pair.length!==2||!pair.every(Number.isFinite)||pair[0]<0||pair[1]<pair[0]||pair[0]>end+.20||pair[0]<end-.20||pair[1]>duration+.25)return false;end=pair[1];}
  return intervals[0][0]<=.15&&end>=duration-.20;
}
export class CoverageGuard {
  constructor(videoId,duration){this.videoId=videoId;this.duration=duration;this.last=null;this.intervals=[];this.open=0;this.done=false;}
  sample(state,wall) {
    if(this.done)return {action:'ignore'};
    const abort=reason=>({action:'abort',reason});
    if(!state||state.video_id!==this.videoId||state.url_video_id!==this.videoId)return abort('source_changed');
    if(state.ad)return abort('ad_detected');
    if(state.protected_media)return abort('protected_media');
    if(state.is_live)return abort('live_source');
    if(state.media_error)return abort('player_error');
    if(state.active_media_count!==1)return abort('additional_media');
    if(state.muted||state.volume<=0)return abort('muted_source');
    if(state.playback_rate!==1)return abort('playback_rate_changed');
    if(!Number.isFinite(state.duration)||Math.abs(state.duration-this.duration)>Math.max(.5,this.duration*.001))return abort('duration_changed');
    const t=state.source_time;
    if(!Number.isFinite(t)||t<0||t>this.duration+.25)return abort('invalid_source_clock');
    if(state.seeking)return abort('unexpected_seek');
    if(this.last&&(t+.12<this.last.t||t-this.last.t>(wall-this.last.wall)*1.2+.35))return abort('content_clock_gap');
    if(!this.last&&t>.20)return abort('start_alignment');
    this.last={t,wall};
    if(state.ended){this.close(t);this.done=true;return coverageComplete(this.intervals,this.duration)?{action:'complete',intervals:this.intervals}:{action:'abort',reason:'incomplete_coverage'};}
    if(state.paused||state.ready_state<3){this.close(t);return {action:'pause'};}
    if(this.open===null){const prior=this.intervals.at(-1)?.[1]??0;if(t>prior+.20)return abort('buffering_clock_gap');this.open=prior;}
    return {action:'record'};
  }
  close(t){if(this.open!==null){if(t>this.open)this.intervals.push([this.open,t]);this.open=null;}}
}
export async function service(path,{token,body,headers={},method='POST'}={}) {
  const response=await fetch(SERVICE+path,{method,credentials:'omit',cache:'no-store',redirect:'error',
    signal:AbortSignal.timeout(15000),headers:{...(token?{Authorization:`Bearer ${token}`}:{ }),
    ...(body&&!(body instanceof Blob)&&!(body instanceof ArrayBuffer)?{'Content-Type':'application/json'}:{}),...headers},
    body:body===undefined?undefined:body instanceof Blob||body instanceof ArrayBuffer?body:JSON.stringify(body)});
  let value;try{value=await response.json();}catch{throw Error('local_service_response');}
  if(!response.ok)throw Error(/^[a-z0-9_]{1,80}$/.test(value?.error||'')?value.error:'local_service_error');
  return value;
}
