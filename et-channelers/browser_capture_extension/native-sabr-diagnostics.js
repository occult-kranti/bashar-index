/** Bounded, value-allowlisted diagnostics for the pinned googlevideo 5.0.1.
 * No request bodies, URLs, credentials, client configuration or error text
 * leave this module. Observers never throw into the transport they observe.
 */
export const SABR_ERROR_KINDS=Object.freeze(['none','sdk_stalled','sdk_request_timeout',
  'sdk_reload_handler_missing','sdk_reload_failed','sdk_sabr_error','sdk_protection_rejected',
  'sdk_format_selection_failed','sdk_unknown_error']);
const fields=Object.freeze({
  request:{playerTimeMs:'n',elapsedWallTimeMs:'n',timeSinceLastSeek:'n',timeSinceLastActionMs:'n',
    enabledTrackTypesBitfield:'n',audioTrackIdPresent:'b',selectedAudioCount:'n',selectedVideoCount:'n',
    initializationCount:'n',selectedAudioMatches:'b',bufferedRangeCount:'n',bufferedStartMs:'n',
    bufferedDurationMs:'n',bufferedStartSegment:'n',bufferedEndSegment:'n',tokenPresent:'b',
    cookiePresent:'b',contextCount:'n'},
  policy:{backoffTimeMs:'n',targetAudioReadaheadMs:'n',targetVideoReadaheadMs:'n',
    maxTimeSinceLastRequestMs:'n',minAudioReadaheadMs:'n',minVideoReadaheadMs:'n',cookiePresent:'b'},
  seek:{timeMs:'n',source:['client','server','unknown']},
  reload:{},protection:{status:'n',maxRetries:'n'},
  format:{type:['audio','video','unknown'],itag:'n',matchesOutput:'b'},
  track:{segmentCount:'n',bufferedMs:'n',endOfStream:'b'},
  response:{status:'n'},error:{code:'n'},observer_error:{}
});
const number=x=>typeof x==='number'&&Number.isFinite(x)&&x>=0&&x<=1e12;
const exact=(x,names)=>x&&typeof x==='object'&&!Array.isArray(x)&&Object.keys(x).every(k=>names.includes(k));
function eventValid(e){
  if(!exact(e,['kind','sequence',...Object.keys(fields[e?.kind]||{})])||!Object.hasOwn(fields,e.kind)||
    !Number.isSafeInteger(e.sequence)||e.sequence<1||e.sequence>1e9)return false;
  return Object.entries(e).every(([k,v])=>k==='kind'||k==='sequence'||
    (fields[e.kind][k]==='n'?number(v):fields[e.kind][k]==='b'?typeof v==='boolean':fields[e.kind][k]?.includes(v)));
}
export function validateSabrDiagnostics(x){
  const kinds=Object.keys(fields);
  if(!exact(x,['schemaVersion','errorKind','counts','latest','events'])||x.schemaVersion!==1||
    !SABR_ERROR_KINDS.includes(x.errorKind)||!exact(x.counts,kinds)||Object.keys(x.counts).length!==kinds.length||
    !Object.values(x.counts).every(n=>Number.isSafeInteger(n)&&n>=0&&n<=1e9)||!exact(x.latest,kinds)||
    !Object.entries(x.latest).every(([k,v])=>v.kind===k&&eventValid(v))||
    !Array.isArray(x.events)||x.events.length>16||!x.events.every(eventValid)||JSON.stringify(x).length>16000)
    throw Error('native_diagnostics_schema');
  return x;
}
export function classifySabrError(error){
  let message;try{message=error?.message;}catch{return {kind:'sdk_unknown_error'};}
  if(typeof message!=='string'||message.length>1024)return {kind:'sdk_unknown_error'};
  if(/^Stream stalled [1-9]\d? times\. Aborting$/.test(message))return {kind:'sdk_stalled'};
  if(message==='Request timed out')return {kind:'sdk_request_timeout'};
  if(message==='Streaming data reload requested but no handler was found')return {kind:'sdk_reload_handler_missing'};
  if(message.startsWith('An error occurred while reloading streaming data: '))return {kind:'sdk_reload_failed'};
  if(/^Stream protection attestation rejected after \d{1,4} attempts$/.test(message))return {kind:'sdk_protection_rejected'};
  if(message.startsWith('Could not select formats: '))return {kind:'sdk_format_selection_failed'};
  const sabr=message.match(/^SABR Error: [A-Za-z0-9_]{1,64} - (\d{1,8})$/);
  return sabr?{kind:'sdk_sabr_error',code:Number(sabr[1])}:{kind:'sdk_unknown_error'};
}
export function createSabrDiagnostics(identity){
  const state={schemaVersion:1,errorKind:'none',counts:Object.fromEntries(Object.keys(fields).map(k=>[k,0])),latest:{},events:[]};
  let sequence=0;
  const record=(kind,input={})=>{
    try{
      if(!Object.hasOwn(fields,kind))return;
      const event={kind,sequence:++sequence};
      for(const [key,type] of Object.entries(fields[kind])){
        const raw=input[key];
        // The generated protobuf decoder represents several int64 times as
        // decimal strings. Convert only bounded unsigned numeric fields.
        const value=type==='n'&&typeof raw==='string'&&/^\d{1,13}$/.test(raw)?Number(raw):raw;
        if(type==='n'?number(value):type==='b'?typeof value==='boolean':type.includes(value))event[key]=value;
      }
      state.counts[kind]++;state.latest[kind]=event;state.events.push(event);if(state.events.length>16)state.events.shift();
    }catch{/* Diagnostics must never affect the media path. */}
  };
  const matches=f=>!!f&&f.itag===identity.itag&&f.lastModified===identity.lastModified&&(f.xtags||'')===identity.xtags;
  return Object.freeze({record,matches,
    error(error){const result=classifySabrError(error);if(state.errorKind==='none')state.errorKind=result.kind;record('error',result);return result.kind;},
    request(value){
      const a=value.clientAbrState||{},ranges=value.bufferedRanges||[],range=ranges.find(r=>matches(r.formatId)),ctx=value.streamerContext||{};
      record('request',{playerTimeMs:a.playerTimeMs,elapsedWallTimeMs:a.elapsedWallTimeMs,timeSinceLastSeek:a.timeSinceLastSeek,
        timeSinceLastActionMs:a.timeSinceLastActionMs,enabledTrackTypesBitfield:a.enabledTrackTypesBitfield,
        audioTrackIdPresent:!!a.audioTrackId,selectedAudioCount:value.selectedAudioFormatIds?.length,
        selectedVideoCount:value.selectedVideoFormatIds?.length,initializationCount:value.initializationFormatIds?.length,
        selectedAudioMatches:value.selectedAudioFormatIds?.length===1&&matches(value.selectedAudioFormatIds[0]),
        bufferedRangeCount:ranges.length,bufferedStartMs:range?.startTimeMs,bufferedDurationMs:range?.durationMs,
        bufferedStartSegment:range?.startSegmentIndex,bufferedEndSegment:range?.endSegmentIndex,
        tokenPresent:!!ctx.poToken?.length,cookiePresent:!!ctx.playbackCookie,
        contextCount:ctx.sabrContexts?.length});
    },
    snapshot(){return validateSabrDiagnostics(JSON.parse(JSON.stringify(state)));}
  });
}
export function observeSabrInternals(stream,diagnostics,decoder){
  const observe=fn=>{try{fn();}catch{diagnostics.record('observer_error');}};
  // These are ordinary methods/own fields in pinned 5.0.1, not #private.
  // Preserve every argument, receiver, returned value, promise and exception.
  for(const [name,before,after] of [
    ['buildRequestBody',null,body=>{
      if(!(body instanceof Uint8Array)||body.byteLength>65536||!decoder?.decode)throw Error('diagnostic_body_bound');
      diagnostics.request(decoder.decode(body));}],
    ['seekTo',(timeMs,source)=>diagnostics.record('seek',{timeMs,source:['client','server'].includes(source)?source:'unknown'}),null],
    ['tryReloadStreamingData',()=>diagnostics.record('reload'),null]
  ]){
    if(typeof stream[name]!=='function')continue;
    const original=stream[name];
    stream[name]=function(...args){if(before)observe(()=>before(...args));const result=Reflect.apply(original,this,args);if(after)observe(()=>after(result));return result;};
  }
  const descriptor=Object.getOwnPropertyDescriptor(stream,'nextRequestPolicy');
  if(descriptor?.configurable&&Object.hasOwn(descriptor,'value')){
    let policy=descriptor.value;
    Object.defineProperty(stream,'nextRequestPolicy',{configurable:true,enumerable:descriptor.enumerable,
      get:()=>policy,set:value=>{policy=value;if(value)observe(()=>diagnostics.record('policy',{
        ...Object.fromEntries(Object.keys(fields.policy).filter(k=>k!=='cookiePresent').map(k=>[k,value[k]])),cookiePresent:!!value.playbackCookie}));}});
  }
}
