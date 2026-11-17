import {readNormalProtection} from './native-sps.js';
// Observe only the player's own request. Secrets never leave this MAIN-world closure.
export function createAcceptedSabrObserver({scope=window,sdk,videoId,timeoutMs=45000,observerSessionId=crypto.randomUUID()}){
  const need=(ok,code)=>{if(!ok)throw Error(code);};
  need(/^[A-Za-z0-9_-]{11}$/.test(videoId),'invalid_video_id');
  need(Number.isFinite(timeoutMs)&&timeoutMs>0&&timeoutMs<=45000&&/^[a-f0-9-]{36}$/.test(observerSessionId),'observer_limits');
  const deadline=Date.now()+timeoutMs;
  need(sdk?.VideoPlaybackAbrRequest?.decode&&sdk?.FormatXTags?.decode&&sdk?.buildSabrFormat&&sdk?.UmpReader&&sdk?.StreamProtectionStatus?.decode,'observer_sdk_missing');
  const originalFetch=scope.fetch,proto=scope.XMLHttpRequest?.prototype,originalOpen=proto?.open,originalSend=proto?.send;
  const xhrs=new WeakMap(),readers=new Set(),copies=new Set(),tokens=new Set(),xhrListeners=new Set();let finished=false,secret=null,timer,watcher,resolveReady,rejectReady,inspecting=0,observations=0,lastReason=null,responseBytes=0,cancelPending;
  const cancelled=new Promise((_,reject)=>{cancelPending=reject;});cancelled.catch(()=>{});
  const ready=new Promise((resolve,reject)=>{resolveReady=resolve;rejectReady=reject;});ready.catch(()=>{});
  const bytes=value=>{
    if(value instanceof Uint8Array)return value;
    if(value instanceof ArrayBuffer)return new Uint8Array(value);
    if(ArrayBuffer.isView(value))return new Uint8Array(value.buffer,value.byteOffset,value.byteLength);
    return null;
  };
  const base64=value=>Uint8Array.from(atob(decodeURIComponent(value).replace(/-/g,'+').replace(/_/g,'/')),x=>x.charCodeAt(0));
  const equal=(a,b)=>a.length===b.length&&a.every((x,i)=>x===b[i]);
  const formatKey=f=>JSON.stringify([f.itag,String(f.lastModified),f.xtags||'']);
  function context(){
    const url=new URL(scope.location.href),player=scope.document.getElementById('movie_player'),video=player?.querySelector('video');
    need(url.origin==='https://www.youtube.com'&&url.pathname==='/watch'&&url.searchParams.get('v')===videoId&&player?.getVideoData?.().video_id===videoId,'source_changed');
    need(video&&!video.mediaKeys&&!video.error&&!player.classList.contains('ad-showing')&&!player.classList.contains('ad-interrupting'),'source_not_eligible');
    need(Number.isFinite(video.duration)&&video.duration>0,'source_duration_unknown');
    const response=player.getPlayerResponse?.()||scope.ytInitialPlayerResponse;
    need(response?.videoDetails?.videoId===videoId&&response.playabilityStatus?.status==='OK','response_identity_changed');
    need(response.videoDetails.isLive!==true&&!response.videoDetails.isPostLiveDvr,'live_source_unsupported');
    return {player,video,response};
  }
  function restore(){
    clearTimeout(timer);clearInterval(watcher);
    if(scope.fetch===wrappedFetch)scope.fetch=originalFetch;
    if(proto?.open===wrappedOpen)proto.open=originalOpen;
    if(proto?.send===wrappedSend)proto.send=originalSend;
  }
  function stop(code='observer_stopped'){
    restore();if(!finished){finished=true;rejectReady(Error(code));}
    cancelPending(Error('observer_stopped'));for(const token of tokens)token.fill(0);tokens.clear();
    for(const remove of xhrListeners)remove();xhrListeners.clear();
    for(const reader of readers)void reader.cancel().catch(()=>{});readers.clear();
    for(const body of copies)if(!body.locked)void body.cancel().catch(()=>{});copies.clear();
    if(secret){secret.token.fill(0);secret=null;}
  }
  async function bodyBytes(body,owned){
    const value=bytes(body);if(value){need(value.byteLength<=65536,'observer_body_too_large');return value.slice();}
    if(body instanceof Blob){need(body.size<=65536,'observer_body_too_large');return new Uint8Array(await body.arrayBuffer());}
    if(body?.getReader){need(owned,'observer_body_unsupported');const reader=body.getReader(),parts=[];readers.add(reader);let total=0;
      try{for(;;){const result=await reader.read();if(result.done)break;total+=result.value.byteLength;need(total<=65536,'observer_body_too_large');parts.push(result.value);}const out=new Uint8Array(total);let offset=0;for(const part of parts){out.set(part,offset);offset+=part.length;}return out;}
      finally{readers.delete(reader);void reader.cancel().catch(()=>{});try{reader.releaseLock();}catch{}}}
    throw Error('observer_body_unsupported');
  }
  async function observe(rawUrl,method,body,credentials,acceptedResponse,owned=false){
    if(finished||method!=='POST'){if(owned){copies.delete(body);if(!body.locked)void body.cancel().catch(()=>{});}return;}
    let url;try{url=new URL(rawUrl);}catch{return;}
    if(url.protocol!=='https:'||url.username||url.password||url.port||url.hash||!/(^|\.)googlevideo\.com$/.test(url.hostname)||url.pathname!=='/videoplayback')return;
    inspecting++;
    let candidateToken=null;
    try{
      need(Date.now()<=deadline,'normal_request_deadline');
      need(++observations<=16,'normal_request_observation_limit');
      need(inspecting<=4,'normal_observer_concurrency');
      const before=context(),published=new URL(before.response.streamingData?.serverAbrStreamingUrl);
      // The real player has already deciphered this URL; never reconstruct it.
      need(url.origin===published.origin&&url.pathname===published.pathname&&!!published.searchParams.get('id')&&url.searchParams.get('id')===published.searchParams.get('id'),'observer_server_mismatch');
      const request=sdk.VideoPlaybackAbrRequest.decode(await Promise.race([bodyBytes(body,owned),cancelled]));if(finished)return;
      const current=context(),config=current.response.playerConfig?.mediaCommonConfig?.mediaUstreamerRequestConfig?.videoPlaybackUstreamerConfig;
      need(typeof config==='string'&&equal(base64(config),request.videoPlaybackUstreamerConfig||new Uint8Array()),'observer_config_mismatch');
      const token=request.streamerContext?.poToken,client=request.streamerContext?.clientInfo;
      need(token instanceof Uint8Array&&token.length>0&&token.length<16384,'observer_token_missing');
      candidateToken=token.slice();tokens.add(candidateToken);
      need(client&&Number.isInteger(client.clientName)&&typeof client.clientVersion==='string','observer_client_missing');
      const selected=request.selectedAudioFormatIds||[],formats=current.response.streamingData?.adaptiveFormats||[];
      const matches=new Map();let observedFormatMatched=false;
      for(const raw of formats){
        if(!/^audio\/(webm|mp4)(;|$)/.test(raw.mimeType||''))continue;
        let normalized;try{normalized=sdk.buildSabrFormat(raw);}catch{continue;}
        if(selected.some(x=>formatKey(x)===formatKey(normalized)))observedFormatMatched=true;
        if(normalized.isDrc||normalized.isVb||normalized.isDubbed||normalized.isAutoDubbed||normalized.isDescriptive||normalized.isSecondary)continue;
        let tags;try{tags=sdk.FormatXTags.decode(base64(normalized.xtags)).xtags;}catch{continue;}
        if(!tags.some(x=>x.key==='acont'&&x.value==='original')||tags.some(x=>(x.key==='acont'&&x.value!=='original')||(['drc','vb'].includes(x.key)&&x.value==='1')))continue;
        matches.set(formatKey(normalized),normalized);
      }
      need(observedFormatMatched,'observer_selected_format_mismatch');
      need(matches.size>0,'observer_original_format_unproven');
      // Attestation is video-bound. The normal player may use a DRC/voice-boost
      // variant; our output is separately bound to explicit original/no-DSP.
      const candidates=[...matches.values()].sort((a,b)=>Number(b.itag===140)-Number(a.itag===140)||(b.bitrate||0)-(a.bitrate||0)||formatKey(a).localeCompare(formatKey(b)));
      const audioFormat=candidates[0];need(audioFormat.hasAudio&&!audioFormat.hasVideo&&!audioFormat.hasText,'observer_audio_only_required');
      const durationMs=Number(audioFormat.approxDurationMs)||Math.round(current.video.duration*1000);
      need(Number.isSafeInteger(durationMs)&&durationMs>0&&Math.abs(durationMs-current.video.duration*1000)<=2000,'observer_duration_mismatch');
      need(['omit','same-origin','include'].includes(credentials),'observer_credentials_mode');
      const accepted=await Promise.race([acceptedResponse,cancelled]);if(finished)return;context();
      await readNormalProtection({sdk,response:accepted,
        admit:n=>{responseBytes+=n;need(responseBytes<=8*1024*1024,'normal_response_read_limit');},
        registerReader:(reader,add)=>add?readers.add(reader):readers.delete(reader),
        checkActive:()=>{need(!finished,'observer_stopped');need(Date.now()<=deadline,'normal_request_deadline');context();}});
      if(finished)return;
      const after=context(),afterConfig=after.response.playerConfig?.mediaCommonConfig?.mediaUstreamerRequestConfig?.videoPlaybackUstreamerConfig;
      need(afterConfig===config&&Math.abs(after.video.duration*1000-durationMs)<=2000,'observer_config_mismatch');
      const acceptance={basis:'matching_normal_player_sps1',http_status:200,sps_status:1,complete_response:true,
        video_id:videoId,same_video:true,same_configuration:true,request_format_matches_catalog:true,
        observed_at_epoch:Math.floor(Date.now()/1000),observer_session_id:observerSessionId};
      let metadata;try{metadata={...publicMetadata(after.response,audioFormat),native_source_acceptance:acceptance};}
      catch{throw Error('observer_metadata_unavailable');}
      secret={token:candidateToken.slice(),source:{videoId,isLive:false,isPostLive:false,noDRM:true,durationMs,audioFormat,
        serverAbrStreamingUrl:url.href,videoPlaybackUstreamerConfig:config,clientInfo:client},credentials};
      finished=true;restore();cancelPending(Error('observer_stopped'));
      for(const token of tokens)token.fill(0);tokens.clear();for(const remove of xhrListeners)remove();xhrListeners.clear();
      for(const reader of readers)void reader.cancel().catch(()=>{});readers.clear();
      for(const body of copies)if(!body.locked)void body.cancel().catch(()=>{});copies.clear();
      resolveReady(Object.freeze({source:secret.source,credentialsMode:credentials,
        getCurrentVideoPoToken:async id=>{context();need(secret&&id===videoId,'source_changed');return secret.token.slice();},
        assertAcceptedContext:async()=>{context();need(secret,'observer_closed');return {accepted:true,videoId};},
        fetchInAcceptedContext:(input,init)=>{context();need(secret,'observer_closed');const target=new URL(String(input));need(target.origin===url.origin&&target.pathname==='/videoplayback','source_server_changed');return originalFetch.call(scope,input,{...init,credentials:secret.credentials,redirect:'error'});},
        metadata,close:()=>stop('observer_closed')}));
    }catch(error){
      // Ignore unrelated/initial incomplete player control requests. A matching
      // accepted request is required before any downloader can be constructed.
      lastReason=/^[a-z0-9_]{1,80}$/.test(error.message||'')?error.message:'normal_request_unusable';
      if(['source_changed','response_identity_changed','source_not_eligible','observer_metadata_unavailable','normal_request_deadline','normal_request_observation_limit','normal_observer_concurrency','normal_response_read_limit','normal_control_too_large','stream_protection_rejected','source_forbidden','source_rate_limited'].includes(lastReason))stop(lastReason);
    }finally{
      if(candidateToken){candidateToken.fill(0);tokens.delete(candidateToken);}inspecting--;
      if(owned){copies.delete(body);if(!body.locked)void body.cancel().catch(()=>{});}
      // Metadata may be rejected before the ordinary response arrives. Dispose
      // its clone when it does arrive, without waiting or touching the original.
      void Promise.resolve(acceptedResponse).then(response=>{if(response.body){copies.delete(response.body);if(!response.body.locked)void response.body.cancel().catch(()=>{});}}).catch(()=>{});
    }
  }
  function wrappedFetch(input,init){
    const request=typeof Request!=='undefined'&&input instanceof Request?input:null;
    const method=String(init?.method||request?.method||'GET').toUpperCase();
    const rawUrl=request?.url||String(input),candidate=isCandidate(rawUrl,method);let body=init?.body,owned=false;
    if(candidate&&body===undefined&&request){try{body=request.clone().body;owned=!!body;if(owned)copies.add(body);}catch{}}
    let result;try{result=originalFetch.apply(this,arguments);}catch(error){if(owned){copies.delete(body);void body.cancel().catch(()=>{});}throw error;}
    if(!candidate)return result;
    // Return the original promise/body immediately. Consume only a cancellable
    // response clone, with a shared byte cap; never replay the player's request.
    const accepted=Promise.resolve(result).then(response=>{
      if(response.status===403||response.status===429){stop(response.status===403?'source_forbidden':'source_rate_limited');throw Error('normal_request_not_accepted');}
      const contentType=(response.headers.get('content-type')||'').split(';')[0];
      const body=!finished&&response.status===200&&contentType==='application/vnd.yt-ump'?response.clone().body:null;
      if(body)copies.add(body);return {status:response.status,contentType,body};
    });accepted.catch(()=>{});
    void observe(rawUrl,method,body,init?.credentials||request?.credentials||'same-origin',accepted,owned);
    return result;
  }
  function wrappedOpen(method,url){xhrs.set(this,{method:String(method).toUpperCase(),url:String(url)});return originalOpen.apply(this,arguments);}
  function isCandidate(rawUrl,method){try{const url=new URL(rawUrl),published=new URL(context().response.streamingData?.serverAbrStreamingUrl);
    return !finished&&method==='POST'&&url.protocol==='https:'&&!url.username&&!url.password&&!url.port&&!url.hash&&/(^|\.)googlevideo\.com$/.test(url.hostname)&&url.pathname==='/videoplayback'&&url.origin===published.origin&&!!published.searchParams.get('id')&&url.searchParams.get('id')===published.searchParams.get('id');}catch{return false;}}
  function wrappedSend(body){const request=xhrs.get(this);if(request&&isCandidate(request.url,request.method)){const accepted=new Promise(resolve=>{
    const remove=()=>{this.removeEventListener('loadend',handler);xhrListeners.delete(remove);};
    const handler=()=>{remove();try{
      if(this.status===403||this.status===429)stop(this.status===403?'source_forbidden':'source_rate_limited');
      const value=this.responseType==='arraybuffer'&&this.response instanceof ArrayBuffer?new Uint8Array(this.response):null;
      resolve({status:this.status,contentType:(this.getResponseHeader('content-type')||'').split(';')[0],bytes:value});
    }catch{resolve({status:0,contentType:'',bytes:null});}};
    xhrListeners.add(remove);this.addEventListener('loadend',handler,{once:true});});
    void observe(request.url,request.method,body,this.withCredentials?'include':'omit',accepted);}return originalSend.apply(this,arguments);}
  function publicMetadata(response,format){
    const d=response.videoDetails,m=response.microformat?.playerMicroformatRenderer||{};
    const text=(value,max=32000)=>typeof value==='string'?value.slice(0,max):null;
    return {id:videoId,webpage_url:`https://www.youtube.com/watch?v=${videoId}`,title:text(d.title,1000),description:text(d.shortDescription),
      channel_id:text(d.channelId,128),channel:text(d.author,500),duration:Math.round(Number(format.approxDurationMs)||context().video.duration*1000)/1000,
      language:text(format.language,32),upload_date:text(m.uploadDate,32),release_date:text(m.publishDate,32),
      tags:Array.isArray(d.keywords)?d.keywords.filter(x=>typeof x==='string').slice(0,100).map(x=>x.slice(0,200)):[],
      thumbnails:(d.thumbnail?.thumbnails||[]).filter(x=>{try{const u=new URL(x.url);return u.protocol==='https:'&&!u.username&&!u.password&&!u.port&&/(^|\.)ytimg\.com$/.test(u.hostname);}catch{return false;}}).slice(0,10).map(x=>{const u=new URL(x.url);return {url:u.origin+u.pathname,width:x.width,height:x.height};}),
      acquisition_context:'browser_native_sabr',native_source_language_basis:'published_original_format'};
  }
  context();scope.fetch=wrappedFetch;if(proto){proto.open=wrappedOpen;proto.send=wrappedSend;}
  timer=setTimeout(()=>stop(lastReason||'normal_request_not_observed'),timeoutMs);
  watcher=setInterval(()=>{try{context();}catch(error){stop(error.message);}},250);
  return Object.freeze({ready,stop});
}
