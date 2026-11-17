import {validateSabrDiagnostics} from './native-sabr-diagnostics.js';
// Validate before any page-supplied message crosses into extension authority.
const need=(ok)=>{if(!ok)throw Error('native_rpc_schema');};
const integer=(x,max=64000000)=>Number.isSafeInteger(x)&&x>=0&&x<=max;
const hash=x=>typeof x==='string'&&/^[a-f0-9]{64}$/.test(x);
const code=x=>typeof x==='string'&&/^[a-z0-9_]{1,80}$/.test(x);
const keys=(x,required,optional=[])=>{need(x&&typeof x==='object'&&!Array.isArray(x));need(required.every(k=>Object.hasOwn(x,k))&&Object.keys(x).every(k=>required.includes(k)||optional.includes(k)));};
const text=(x,max)=>x===null||typeof x==='string'&&x.length<=max&&!/(googlevideo\.com|\/videoplayback|\/timedtext|\bbearer\s)/i.test(x);
function identity(x){
  keys(x,['videoId','itag','lastModified','xtags','mimeType','durationMs','language','codec','contentLength','originalBasis','trackId','noDRM','audioOnly']);
  need(/^[A-Za-z0-9_-]{11}$/.test(x.videoId)&&integer(x.itag,9999)&&x.itag>0&&/^\d{1,30}$/.test(x.lastModified));
  need(typeof x.xtags==='string'&&x.xtags.length<=4096&&/^[A-Za-z0-9_+/=%-]+$/.test(x.xtags));
  need(/^audio\/(mp4|webm)(?:;\s*codecs="[A-Za-z0-9., -]{1,100}")?$/.test(x.mimeType));
  need(integer(x.durationMs,1e10)&&x.durationMs>0&&(x.contentLength===null||integer(x.contentLength,1e10)&&x.contentLength>0));
  need((x.language===null||/^[A-Za-z0-9_.-]{1,32}$/.test(x.language))&&/^[A-Za-z0-9_.-]{1,64}$/.test(x.codec));
  need((x.trackId===null||/^[A-Za-z0-9_.=,; -]{1,200}$/.test(x.trackId))&&x.originalBasis==='published_original'&&x.noDRM===true&&x.audioOnly===true);
}
function metadata(x,videoId){
  keys(x,['id'],['webpage_url','title','description','channel_id','channel','duration','language','upload_date','release_date','tags','thumbnails','acquisition_context','native_source_language_basis']);
  need(x.id===videoId&&(!x.webpage_url||x.webpage_url===`https://www.youtube.com/watch?v=${videoId}`));
  for(const [key,max] of [['title',1000],['description',32000],['channel_id',128],['channel',500],['language',32],['upload_date',32],['release_date',32],['acquisition_context',80],['native_source_language_basis',80]])if(x[key]!==undefined)need(text(x[key],max));
  if(x.duration!==undefined)need(typeof x.duration==='number'&&Number.isFinite(x.duration)&&x.duration>0&&x.duration<=1e7);
  if(x.tags!==undefined)need(Array.isArray(x.tags)&&x.tags.length<=100&&x.tags.every(s=>text(s,200)));
  if(x.thumbnails!==undefined){need(Array.isArray(x.thumbnails)&&x.thumbnails.length<=10);for(const thumb of x.thumbnails){
    keys(thumb,['url'],['width','height']);const u=new URL(thumb.url);need(u.protocol==='https:'&&!u.username&&!u.password&&!u.port&&!u.search&&!u.hash&&/(^|\.)ytimg\.com$/.test(u.hostname));
    for(const key of ['width','height'])if(thumb[key]!==undefined)need(integer(thumb[key],20000));}}
}
export function validateNativeRpc(operation,value){
  try{
    need(typeof operation==='string');
    if(operation==='state'){
      keys(value,['phase'],['video_id','source_binding_sha256','bytes','token_present','credentials_mode','identity','error','diagnostics']);
      need(['observing_normal_request','downloading_native_audio','validating_native_audio','uploading_verified_native_audio','drive_verified','held'].includes(value.phase));
      if(value.video_id!==undefined)need(/^[A-Za-z0-9_-]{11}$/.test(value.video_id));
      if(value.source_binding_sha256!==undefined)need(hash(value.source_binding_sha256));
      if(value.bytes!==undefined)need(integer(value.bytes));if(value.error!==undefined)need(code(value.error));
      if(value.token_present!==undefined)need(typeof value.token_present==='boolean');
      if(value.credentials_mode!==undefined)need(['omit','include','same-origin'].includes(value.credentials_mode));
      if(value.identity!==undefined)identity(value.identity);
      if(value.diagnostics!==undefined)validateSabrDiagnostics(value.diagnostics);
    }else if(operation==='begin'){
      keys(value,['identity','transportKind','outputBudgetBytes','metadata']);identity(value.identity);metadata(value.metadata,value.identity.videoId);
      need(value.transportKind==='sabr_reassembled'&&value.outputBudgetBytes===64000000);
    }else if(operation==='request'){
      keys(value,['sourceBindingSha256','requestSequence']);need(hash(value.sourceBindingSha256)&&integer(value.requestSequence,1000)&&value.requestSequence>0);
    }else if(operation==='chunk'){
      keys(value,['offset','base64']);need(integer(value.offset)&&typeof value.base64==='string'&&value.base64.length>0&&value.base64.length<=1048576&&/^[A-Za-z0-9+/]*={0,2}$/.test(value.base64));
    }else if(operation==='segment'){
      keys(value,['number','initialization','startTimeMs','endTimeMs','declaredBytes','byteOffset','emittedBytes','sha256','initDiscardedBytes']);
      need(integer(value.number,1e6)&&typeof value.initialization==='boolean'&&hash(value.sha256)&&value.initDiscardedBytes===0);
      for(const key of ['startTimeMs','endTimeMs'])need(integer(value[key],1e10));
      for(const key of ['declaredBytes','byteOffset','emittedBytes'])need(integer(value[key]));
      need(value.declaredBytes>0&&value.emittedBytes===value.declaredBytes&&value.endTimeMs>=value.startTimeMs);
    }else if(operation==='finish'){
      keys(value,['sourceBinding','sourceBindingSha256','bytes','identity','nativeProtocol','transportKind','container_reassembled','encoded_audio_not_reencoded','reencoded','isLive','stripDuplicateInit','protocolEos','endSegmentNum','endTimeMs','segmentCount','segmentLedgerSha256','decodeValidationRequired','driveVerificationRequired']);
      identity(value.identity);need(hash(value.sourceBinding)&&value.sourceBinding===value.sourceBindingSha256&&hash(value.segmentLedgerSha256)&&integer(value.bytes)&&value.bytes>0);
      need(value.nativeProtocol==='sabr'&&value.transportKind==='sabr_reassembled'&&value.reencoded===false&&value.isLive===false&&value.stripDuplicateInit===false);
      for(const key of ['container_reassembled','encoded_audio_not_reencoded','protocolEos','decodeValidationRequired','driveVerificationRequired'])need(value[key]===true);
      need(integer(value.endSegmentNum,1e6)&&integer(value.segmentCount,1e6)&&integer(value.endTimeMs,1e10));
    }else if(operation==='retain'){keys(value,['error_class']);need(['forbidden','rate_limited','bot_check','network','aborted','protocol','integrity'].includes(value.error_class));}
    else if(operation==='status')keys(value,[]);
    else need(false);
    need(JSON.stringify(value).length<=(operation==='chunk'?1050000:262144));return value;
  }catch{throw Error('native_rpc_schema');}
}
