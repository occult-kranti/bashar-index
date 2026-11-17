// Observe only the player's own request. Secrets never leave this MAIN-world closure.
export function createAcceptedSabrObserver({scope=window,sdk,videoId,timeoutMs=45000}){
  const need=(ok,code)=>{if(!ok)throw Error(code);};
  need(/^[A-Za-z0-9_-]{11}$/.test(videoId),'invalid_video_id');
  need(sdk?.VideoPlaybackAbrRequest?.decode&&sdk?.FormatXTags?.decode&&sdk?.buildSabrFormat,'observer_sdk_missing');
  const originalFetch=scope.fetch,proto=scope.XMLHttpRequest?.prototype,originalOpen=proto?.open,originalSend=proto?.send;
  const xhrs=new WeakMap();let finished=false,secret=null,timer,watcher,resolveReady,rejectReady,inspecting=false,observations=0,lastReason=null,activeReader=null;
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
    if(activeReader){void activeReader.cancel().catch(()=>{});activeReader=null;}
    if(secret){secret.token.fill(0);secret=null;}
  }
  async function bodyBytes(body){
    const value=bytes(body);if(value){need(value.byteLength<=65536,'observer_body_too_large');return value.slice();}
    if(body instanceof Blob){need(body.size<=65536,'observer_body_too_large');return new Uint8Array(await body.arrayBuffer());}
    if(body?.getReader){const reader=body.getReader(),parts=[];activeReader=reader;let total=0;
      try{for(;;){const result=await reader.read();if(result.done)break;total+=result.value.byteLength;need(total<=65536,'observer_body_too_large');parts.push(result.value);}const out=new Uint8Array(total);let offset=0;for(const part of parts){out.set(part,offset);offset+=part.length;}return out;}
      finally{if(activeReader===reader)activeReader=null;void reader.cancel().catch(()=>{});}}
    throw Error('observer_body_unsupported');
  }
  async function observe(rawUrl,method,body,credentials,acceptedResponse){
    if(finished||inspecting||method!=='POST')return;
    let url;try{url=new URL(rawUrl);}catch{return;}
    if(url.protocol!=='https:'||url.username||url.password||url.port||url.hash||!/(^|\.)googlevideo\.com$/.test(url.hostname)||url.pathname!=='/videoplayback')return;
    inspecting=true;
    try{
      need(++observations<=16,'normal_request_observation_limit');
      const before=context(),published=new URL(before.response.streamingData?.serverAbrStreamingUrl);
      // The real player has already deciphered this URL; never reconstruct it.
      need(url.origin===published.origin&&url.pathname===published.pathname&&!!published.searchParams.get('id')&&url.searchParams.get('id')===published.searchParams.get('id'),'observer_server_mismatch');
      const request=sdk.VideoPlaybackAbrRequest.decode(await bodyBytes(body));if(finished)return;
      const current=context(),config=current.response.playerConfig?.mediaCommonConfig?.mediaUstreamerRequestConfig?.videoPlaybackUstreamerConfig;
      need(typeof config==='string'&&equal(base64(config),request.videoPlaybackUstreamerConfig||new Uint8Array()),'observer_config_mismatch');
      const token=request.streamerContext?.poToken,client=request.streamerContext?.clientInfo;
      need(token instanceof Uint8Array&&token.length>0&&token.length<16384,'observer_token_missing');
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
      const accepted=await acceptedResponse;if(finished)return;context();
      need(accepted.status===200&&accepted.contentType==='application/vnd.yt-ump','normal_request_not_accepted');
      secret={token:token.slice(),source:{videoId,isLive:false,isPostLive:false,noDRM:true,durationMs,audioFormat,
        serverAbrStreamingUrl:url.href,videoPlaybackUstreamerConfig:config,clientInfo:client},credentials};
      finished=true;restore();
      resolveReady(Object.freeze({source:secret.source,credentialsMode:credentials,
        getCurrentVideoPoToken:async id=>{context();need(secret&&id===videoId,'source_changed');return secret.token.slice();},
        assertAcceptedContext:async()=>{context();need(secret,'observer_closed');return {accepted:true,videoId};},
        fetchInAcceptedContext:(input,init)=>{context();need(secret,'observer_closed');const target=new URL(String(input));need(target.origin===url.origin&&target.pathname==='/videoplayback','source_server_changed');return originalFetch.call(scope,input,{...init,credentials:secret.credentials,redirect:'error'});},
        metadata:publicMetadata(current.response,audioFormat),close:()=>stop('observer_closed')}));
    }catch(error){
      // Ignore unrelated/initial incomplete player control requests. A matching
      // accepted request is required before any downloader can be constructed.
      lastReason=/^[a-z0-9_]{1,80}$/.test(error.message||'')?error.message:'normal_request_unusable';
      if(['source_changed','response_identity_changed','source_not_eligible','normal_request_observation_limit','source_forbidden','source_rate_limited'].includes(lastReason))stop(lastReason);
    }finally{inspecting=false;}
  }
  function wrappedFetch(input,init){
    const request=typeof Request!=='undefined'&&input instanceof Request?input:null;
    const method=String(init?.method||request?.method||'GET').toUpperCase();
    const rawUrl=request?.url||String(input),candidate=isCandidate(rawUrl,method);let body=init?.body;
    if(candidate&&body===undefined&&request){try{body=request.clone().body;}catch{}}
    const result=originalFetch.apply(this,arguments);
    if(!candidate)return result;
    // Return the original promise and body untouched. Only status/type are inspected.
    const accepted=Promise.resolve(result).then(response=>{
      if(response.status===403||response.status===429){stop(response.status===403?'source_forbidden':'source_rate_limited');throw Error('normal_request_not_accepted');}
      return {status:response.status,contentType:(response.headers.get('content-type')||'').split(';')[0]};
    });accepted.catch(()=>{});
    void observe(rawUrl,method,body,init?.credentials||request?.credentials||'same-origin',accepted);
    return result;
  }
  function wrappedOpen(method,url){xhrs.set(this,{method:String(method).toUpperCase(),url:String(url)});return originalOpen.apply(this,arguments);}
  function isCandidate(rawUrl,method){try{const url=new URL(rawUrl),published=new URL(context().response.streamingData?.serverAbrStreamingUrl);
    return !finished&&method==='POST'&&url.protocol==='https:'&&/(^|\.)googlevideo\.com$/.test(url.hostname)&&url.pathname==='/videoplayback'&&url.origin===published.origin&&!!published.searchParams.get('id')&&url.searchParams.get('id')===published.searchParams.get('id');}catch{return false;}}
  function wrappedSend(body){const request=xhrs.get(this);if(request&&isCandidate(request.url,request.method)){const accepted=new Promise(resolve=>this.addEventListener('loadend',()=>{
      if(this.status===403||this.status===429)stop(this.status===403?'source_forbidden':'source_rate_limited');
      resolve({status:this.status,contentType:(this.getResponseHeader('content-type')||'').split(';')[0]});},{once:true}));
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
