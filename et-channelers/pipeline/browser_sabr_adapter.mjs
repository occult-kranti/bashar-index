/** Native SABR prototype for an already accepted browser context.
 *
 * Inject googlevideo 5.0.1; this module neither creates a session nor generates
 * attestation. Keep source URL/config/token and fetch inside the accepted page.
 * The sink must reserve bytes before writing, durably ACK exact offsets, and
 * verify persisted prefixes before resume. A raw SDK snapshot is NOT a safe
 * file checkpoint: received segments can still be waiting for a sink ACK.
 *
 * SDK imports: SabrStream from googlevideo/sabr-stream, FormatXTags from
 * googlevideo/protos, EnabledTrackTypes and Logger from googlevideo/utils.
 * The bridge can use session.identity/sourceBinding to begin a bounded sink
 * before run(). Required sink calls: reserve(n), write({offset,seq,bytes}),
 * finish(proof), retain(proof). Optional segment(proof) returns a durable
 * {segmentCount,ledgerSha256} ACK for the sorted-JSON SHA256 chain below.
 * Local segment and duration checks are not Drive verification or proof that
 * a new accepted-context session will be accepted by the source server.
 *
 * Audited upstream: github.com/LuanRT/googlevideo/blob/main/src/core/SabrStream.ts
 * and src/utils/SabrSegmentBuffer.ts, src/utils/Track.ts, src/utils/formatUtils.ts.
 * This VOD adapter disables duplicate-init stripping; encoded audio is not
 * reencoded, but output is a reassembled container, not a direct-file copy.
 */
import {createSabrDiagnostics,observeSabrInternals} from '../browser_capture_extension/native-sabr-diagnostics.js';
const AUDIO_HWM=3*1024*1024;
const VIDEO_ID=/^[A-Za-z0-9_-]{11}$/;
const HASH=/^[a-f0-9]{64}$/;
const MD5=/^[a-f0-9]{32}$/;
export class NativeSabrError extends Error {
  constructor(code){super(code);this.name='NativeSabrError';this.code=code;}
}
const need=(ok,code)=>{if(!ok)throw new NativeSabrError(code);};
const finite=x=>typeof x==='number'&&Number.isFinite(x)&&x>=0;
const counter=x=>Number.isSafeInteger(x)&&x>=0;
const canonical=value=>JSON.stringify(value,Object.keys(value).sort());
async function sha(value){
  const raw=await crypto.subtle.digest('SHA-256',typeof value==='string'?new TextEncoder().encode(value):value);
  return [...new Uint8Array(raw)].map(x=>x.toString(16).padStart(2,'0')).join('');
}
function mediaURL(value){
  let u;try{u=new URL(value);}catch{throw new NativeSabrError('invalid_media_url');}
  need(u.protocol==='https:'&&!u.username&&!u.password&&!u.port&&!u.hash&&
    /(^|\.)googlevideo\.com$/.test(u.hostname)&&u.pathname==='/videoplayback','invalid_media_url');
  return u;
}
function sourceIdentity(source,decodeXtags){
  const f=source?.audioFormat;
  need(VIDEO_ID.test(source?.videoId||'')&&source.isLive===false&&source.isPostLive===false,'invalid_vod_identity');
  need(source.noDRM===true,'drm_state_unproven');
  need(counter(source.durationMs)&&source.durationMs>0,'unknown_duration');
  need(f&&f.hasAudio===true&&f.hasVideo===false&&f.hasText===false&&
    /^audio\/(webm|mp4)(;|$)/.test(f.mimeType||'')&&Number.isInteger(f.itag)&&f.itag>0&&
    typeof f.lastModified==='string'&&/^\d+$/.test(f.lastModified),'invalid_audio_format');
  // SDK codecCode is its compact enum ('a'/'o'), not a native codec name.
  // Bind the actual published MIME codec that the local audio validator reads.
  const mimeCodec=f.mimeType.match(/;\s*codecs="(opus|vorbis|mp4a\.40\.2)"(?:;|$)/)?.[1];
  const codec={opus:'opus',vorbis:'vorbis','mp4a.40.2':'aac'}[mimeCodec];
  need(codec,'native_codec_unproven');
  need(!f.isDubbed&&!f.isAutoDubbed&&!f.isDescriptive&&!f.isSecondary&&!f.isVb&&!f.isDrc,'nonoriginal_audio_variant');
  // googlevideo's buildSabrFormat infers isOriginal when alternate tags are
  // absent. Require the actual published original tag instead of that default.
  let tags;
  try{
    need(typeof f.xtags==='string'&&f.xtags.length>0&&f.xtags.length<16384,'original_audio_unproven');
    const encoded=decodeURIComponent(f.xtags).replace(/-/g,'+').replace(/_/g,'/');
    tags=decodeXtags(Uint8Array.from(atob(encoded),c=>c.charCodeAt(0))).xtags;
  }catch{throw new NativeSabrError('original_audio_unproven');}
  need(Array.isArray(tags)&&tags.some(t=>t.key==='acont'&&t.value==='original')&&
    !tags.some(t=>t.key==='acont'&&t.value!=='original'),'original_audio_unproven');
  need(!tags.some(t=>['drc','vb'].includes(t.key)&&t.value==='1'),'nonoriginal_audio_variant');
  need(source.clientInfo&&Number.isInteger(source.clientInfo.clientName)&&
    typeof source.clientInfo.clientVersion==='string'&&source.clientInfo.clientVersion.length<100,'missing_client_identity');
  need(typeof source.videoPlaybackUstreamerConfig==='string'&&source.videoPlaybackUstreamerConfig.length>0,'missing_stream_config');
  mediaURL(source.serverAbrStreamingUrl);
  need(!['yt_premiere_broadcast','yt_live_broadcast'].includes(new URL(source.serverAbrStreamingUrl).searchParams.get('source')),
    'broadcast_source_unsupported');
  return {videoId:source.videoId,itag:f.itag,lastModified:f.lastModified,xtags:f.xtags||'',
    mimeType:f.mimeType,durationMs:source.durationMs,language:f.language||null,
    codec,contentLength:Number.isSafeInteger(f.contentLength)&&f.contentLength>0?f.contentLength:null,
    originalBasis:'published_original',trackId:f.audioTrackId||f.audioTrack?.id||null,noDRM:true,audioOnly:true};
}
function safeSnapshot(value){
  // SDK v5.0.1 TrackState snapshots contain only media identity/timing. Reject
  // unexpected transport material rather than accidentally exporting secrets.
  need(value&&finite(value.playerTimeMs)&&Array.isArray(value.tracks)&&value.tracks.length===1,'invalid_resume_snapshot');
  const raw=JSON.stringify(value);
  need(raw.length<=1024*1024&&!/"(?:url|token|poToken|cookie|headers|authorization|videoPlaybackUstreamerConfig)"\s*:/i.test(raw),
    'unsafe_resume_snapshot');
  return JSON.parse(raw);
}

export async function openNativeSabr({sdk,source,fetchInAcceptedContext,getCurrentVideoPoToken,
  assertAcceptedContext,sink,maxBytes,maxRequests=10000,resume=null,signal=null,requireRequestAuthorization=false}){
  need(sdk?.SabrStream&&sdk.version==='5.0.1'&&typeof sdk.Logger?.getInstance==='function'&&
    typeof sdk.FormatXTags?.decode==='function'&&
    Number.isInteger(sdk?.EnabledTrackTypes?.AUDIO_ONLY),'invalid_sdk');
  sdk.Logger.getInstance().setLogLevels(0); // Upstream debug output can contain signed transport URLs.
  need(typeof fetchInAcceptedContext==='function'&&typeof assertAcceptedContext==='function'&&
    typeof getCurrentVideoPoToken==='function','accepted_context_callbacks_required');
  need(sink&&['reserve','write','finish','retain'].every(k=>typeof sink[k]==='function'),'invalid_sink');
  need(typeof requireRequestAuthorization==='boolean'&&(!requireRequestAuthorization||
    typeof sink.authorizeRequest==='function'),'request_authorization_required');
  need(Number.isSafeInteger(maxBytes)&&maxBytes>0&&Number.isSafeInteger(maxRequests)&&maxRequests>0,'invalid_budget');
  const identity=sourceIdentity(source,value=>sdk.FormatXTags.decode(value)), binding=await sha(canonical(identity));
  const diagnostics=createSabrDiagnostics(identity);
  let offset=0,stream,reader,finished=false,eos=false,refusal=null,started=false,requests=0;
  let lastTrack=null,runDone=false,writeSequence=0,ledgerSha256='0'.repeat(64);
  const segments=new Map(),emittedSegments=new Map();
  const context=async()=>{
    need(!signal?.aborted&&!refusal,'source_cancelled');
    const proof=await assertAcceptedContext();
    need(proof?.accepted===true&&proof.videoId===identity.videoId,'accepted_context_changed');
  };
  await context();
  if(resume){
    need(resume.sourceBinding===binding&&Number.isSafeInteger(resume.bytes)&&resume.bytes>0&&
      resume.bytes<maxBytes&&HASH.test(resume.prefixSha256||'')&&typeof sink.verifyResume==='function','resume_binding_mismatch');
    const snapshot=safeSnapshot(resume.snapshot);
    need(snapshot.tracks[0]?.formatId?.itag===identity.itag&&
      snapshot.tracks[0]?.formatId?.lastModified===identity.lastModified&&
      (snapshot.tracks[0]?.formatId?.xtags||'')===identity.xtags,'resume_format_mismatch');
    const checked=await sink.verifyResume({sourceBinding:binding,bytes:resume.bytes,prefixSha256:resume.prefixSha256,snapshot});
    need(checked?.prefixVerified===true&&checked?.segmentBoundaryVerified===true&&
      checked.bytes===resume.bytes&&checked.prefixSha256===resume.prefixSha256,'resume_prefix_unproven');
    need(Array.isArray(checked.segments)&&checked.segments.length>0,'resume_segment_proof_missing');
    let prefixBytes=0;
    for(const segment of checked.segments){
      need(segment.number===emittedSegments.size&&segment.byteOffset===prefixBytes&&
        Number.isSafeInteger(segment.emittedBytes)&&segment.emittedBytes>0&&segment.declaredBytes===segment.emittedBytes&&
        segment.initDiscardedBytes===0&&HASH.test(segment.sha256||'')&&counter(segment.startTimeMs)&&counter(segment.endTimeMs)&&
        segment.endTimeMs>=segment.startTimeMs&&segment.initialization===(segment.number===0),'resume_segment_proof_missing');
      prefixBytes+=segment.emittedBytes;emittedSegments.set(segment.number,segment);
      ledgerSha256=await sha(ledgerSha256+'\n'+canonical(segment));
      const {number,initialization,startTimeMs,endTimeMs,declaredBytes}=segment;
      segments.set(number,{number,initialization,startTimeMs,endTimeMs,declaredBytes});
    }
    need(prefixBytes===resume.bytes,'resume_segment_proof_missing');
    offset=resume.bytes;
  }
  const abort=async(code='user_stopped')=>{
    refusal ||= new NativeSabrError(code);
    if(stream){try{await stream.abort();}catch{}}
  };
  const onAbort=()=>{void abort('user_stopped');};
  const fetchBound=async(input,init)=>{
    await context();mediaURL(String(input));
    need(++requests<=maxRequests,'request_budget_exceeded');
    if(requireRequestAuthorization||typeof sink.authorizeRequest==='function'){
      let granted;
      try{granted=await sink.authorizeRequest({sourceBindingSha256:binding,requestSequence:requests});}
      catch{throw new NativeSabrError('request_authorization_denied');}
      need(granted?.authorized===true&&granted.sourceBindingSha256===binding&&
        granted.requestSequence===requests&&granted.sourceRequests===requests,'request_authorization_denied');
      // Stop/context can change while the server durably spends this request.
      await context();
    }
    let response;
    try{response=await fetchInAcceptedContext(input,{...init,redirect:'error'});}
    catch{throw refusal||new NativeSabrError('browser_fetch_failed');}
    diagnostics.record('response',{status:response.status});
    if(response.status===403||response.status===429){
      await abort(response.status===403?'source_forbidden':'source_rate_limited');throw refusal;
    }
    need(response.ok,'source_response_failed');
    need((response.headers.get('content-type')||'').split(';')[0]==='application/vnd.yt-ump','unexpected_source_content');
    return response;
  };
  // The callback must only return the legitimate current video's already
  // available token. Generating/refreshing attestation is outside this adapter.
  await context();
  let token;
  try{token=await getCurrentVideoPoToken(identity.videoId);}catch{throw new NativeSabrError('current_video_token_unavailable');}
  need(token instanceof Uint8Array&&token.length>0&&token.length<16384,'current_video_token_unavailable');
  const currentToken=async()=>{await context();return token.slice();};
  stream=new sdk.SabrStream({videoId:identity.videoId,fetchFunction:fetchBound,
    serverAbrStreamingUrl:source.serverAbrStreamingUrl,videoPlaybackUstreamerConfig:source.videoPlaybackUstreamerConfig,
    poToken:btoa(String.fromCharCode(...token)),
    clientInfo:source.clientInfo,formats:[source.audioFormat],audioHighWaterMark:AUDIO_HWM,videoHighWaterMark:1,
    stripDuplicateInit:false,
    callbacks:{onMintPoToken:currentToken}});
  observeSabrInternals(stream,diagnostics,sdk.VideoPlaybackAbrRequest);
  stream.on('streamProtectionStatusUpdate',status=>{
    diagnostics.record('protection',status);
    if(status?.status===3){void abort('stream_protection_rejected');throw refusal;}
  });
  stream.on('error',error=>{const code=error instanceof NativeSabrError?error.code:diagnostics.error(error);refusal ||= new NativeSabrError(code);});
  stream.on('finish',()=>{finished=true;});
  const captureTrack=track=>{
    if(track){
      lastTrack=track;eos=track.endOfStreamReached===true;
      for(const [number,segment] of track.trackedSegments||[]){
        need(Number.isInteger(number)&&number>=0&&segment.mediaHeader?.videoId===identity.videoId,'segment_identity_mismatch');
        const safe={number,initialization:segment.mediaHeader.isInitializationSegment===true,
          startTimeMs:segment.startTimeMs,endTimeMs:segment.endTimeMs,
          declaredBytes:Number(segment.mediaHeader.segmentLengthBytes)};
        need(Number.isSafeInteger(safe.declaredBytes)&&safe.declaredBytes>0,'segment_length_unproven');
        need(counter(safe.startTimeMs)&&counter(safe.endTimeMs)&&safe.endTimeMs>=safe.startTimeMs,'invalid_segment_timing');
        const old=segments.get(number);
        need(!old||JSON.stringify(old)===JSON.stringify(safe),'segment_revision_conflict');
        segments.set(number,safe);
      }
    }
  };
  stream.on('formatInitialization',track=>{
    diagnostics.record('format',{type:['audio','video'].includes(track?.type)?track.type:'unknown',
      itag:track?.formatId?.itag,matchesOutput:diagnostics.matches(track?.formatId)});
    if(track?.type==='audio')lastTrack=track;
  });
  stream.on('trackStateUpdate',tracks=>{
    diagnostics.record('track',{segmentCount:tracks?.audio?.trackedSegments?.size,bufferedMs:tracks?.buffered,
      endOfStream:tracks?.audio?.endOfStreamReached===true});captureTrack(tracks?.audio);
  });

  const checkpointCandidate=async()=>{
    // Call while run() is draining, never while its reader/sink is paused.
    const snapshot=safeSnapshot(await stream.snapshot());
    return {schemaVersion:1,sourceBinding:binding,acknowledgedBytes:offset,snapshot,segments:[...emittedSegments.values()],
      resumable:false,reason:'requires_independent_spool_prefix_and_segment_boundary_verification'};
  };
  const run=async()=>{
    need(!started,'session_already_started');started=true;
    try{
      await context();
      need(stream.isLive!==true,'broadcast_source_unsupported');
      const result=stream.start({enabledTrackTypes:sdk.EnabledTrackTypes.AUDIO_ONLY,audioFormat:source.audioFormat,
        maxRetries:0,isPostLiveDvr:false,...(resume?{snapshot:safeSnapshot(resume.snapshot)}:{})});
      const chosen=result.selectedFormats?.audioFormat;
      need(chosen?.itag===identity.itag&&chosen.lastModified===identity.lastModified&&
        (chosen.xtags||'')===identity.xtags&&!result.selectedFormats?.videoFormat,'selected_format_changed');
      reader=result.audioStream.getReader();
      while(true){
        const {done,value}=await reader.read();if(done)break;
        need(!refusal&&!signal?.aborted,'source_cancelled');
        need(ArrayBuffer.isView(value)&&value.byteLength>0&&value.byteLength<=AUDIO_HWM,'invalid_media_chunk');
        need(offset+value.byteLength<=maxBytes,'byte_budget_exceeded');
        captureTrack(lastTrack);
        const segment=segments.get(emittedSegments.size),byteOffset=offset;
        need(segment&&segment.declaredBytes===value.byteLength,'segment_payload_mismatch');
        const segmentSha256=await sha(new Uint8Array(value.buffer,value.byteOffset,value.byteLength));
        for(let position=0;position<value.byteLength;position+=1024*1024){
          const bytes=new Uint8Array(value.buffer,value.byteOffset+position,Math.min(1024*1024,value.byteLength-position));
          await sink.reserve(bytes.byteLength);
          const ack=await sink.write({offset,seq:writeSequence,bytes});
          need(ack?.acknowledgedBytes===offset+bytes.byteLength,'sink_ack_mismatch');offset=ack.acknowledgedBytes;
          writeSequence++;
        }
        const emitted={...segment,byteOffset,emittedBytes:value.byteLength,sha256:segmentSha256,initDiscardedBytes:0};
        emittedSegments.set(segment.number,emitted);
        ledgerSha256=await sha(ledgerSha256+'\n'+canonical(emitted));
        if(typeof sink.segment==='function'){
          const segmentAck=await sink.segment(emitted);
          need(segmentAck?.segmentCount===emittedSegments.size&&segmentAck?.ledgerSha256===ledgerSha256,
            'segment_sink_ack_mismatch');
        }
      }
      need(!refusal&&finished&&eos&&!stream.isAborted&&!stream.isErrored,'native_eos_unproven');
      need(finite(lastTrack?.endTimeMs)&&Math.abs(lastTrack.endTimeMs-identity.durationMs)<=Math.max(2000,identity.durationMs*.002),
        'native_duration_mismatch');
      need(segments.get(0)?.initialization===true&&Number.isInteger(lastTrack.endSegmentNum)&&lastTrack.endSegmentNum>0,
        'native_initialization_unproven');
      let edge=0;
      for(let n=1;n<=lastTrack.endSegmentNum;n++){
        const segment=segments.get(n);
        need(segment&&!segment.initialization&&Math.abs(segment.startTimeMs-edge)<=250,'native_segment_gap');
        edge=segment.endTimeMs;
      }
      need(Math.abs(edge-identity.durationMs)<=Math.max(2000,identity.durationMs*.002),'native_coverage_mismatch');
      need(emittedSegments.size===lastTrack.endSegmentNum+1&&
        [...emittedSegments.values()].reduce((n,s)=>n+s.emittedBytes,0)===offset,'native_byte_coverage_mismatch');
      const proof=await sink.finish({sourceBinding:binding,sourceBindingSha256:binding,bytes:offset,identity,
        nativeProtocol:'sabr',transportKind:'sabr_reassembled',container_reassembled:true,encoded_audio_not_reencoded:true,
        reencoded:false,isLive:false,stripDuplicateInit:false,protocolEos:true,endSegmentNum:lastTrack.endSegmentNum,endTimeMs:lastTrack.endTimeMs,
        segmentCount:emittedSegments.size,segmentLedgerSha256:ledgerSha256,
        ...(typeof sink.segment==='function'?{}:{segments:[...emittedSegments.values()]}),
        decodeValidationRequired:true,driveVerificationRequired:true});
      need(proof?.bytes===offset&&HASH.test(proof.sha256||'')&&MD5.test(proof.md5||''),'local_artifact_proof_missing');
      runDone=true;
      return {state:'native_download_complete_pending_decode_and_drive',sourceBinding:binding,bytes:offset,
        sha256:proof.sha256,md5:proof.md5,requests,identity,reencoded:false,container_reassembled:true};
    }catch(error){
      await abort(error instanceof NativeSabrError?error.code:'native_download_failed');
      refusal.diagnostics=diagnostics.snapshot();
      await sink.retain({sourceBinding:binding,acknowledgedBytes:offset,error:refusal.code,resumable:false,diagnostics:refusal.diagnostics});
      throw refusal;
    }finally{
      reader?.releaseLock();signal?.removeEventListener('abort',onAbort);
    }
  };
  signal?.addEventListener('abort',onAbort,{once:true});
  return Object.freeze({run,abort,checkpointCandidate,diagnostics:()=>diagnostics.snapshot(),sourceBinding:binding,identity:Object.freeze({...identity}),
    get acknowledgedBytes(){return offset;},get complete(){return runDone;}});
}
