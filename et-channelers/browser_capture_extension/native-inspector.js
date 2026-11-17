// Explicit chrome.scripting.executeScript({world:'MAIN',func:nativeBrowserProbe,args:[...]}) only.
// No automatic activation, URL export, URL rewriting, token acquisition or source retry.
export async function nativeBrowserProbe(mode,videoId,itag=null){
  const fail=code=>{throw Error(code);};
  const number=value=>{const n=Number(value);return Number.isFinite(n)&&n>0?n:null;};
  const safeTrack=value=>typeof value==='string'&&/^[a-zA-Z0-9_.-]{1,48}$/.test(value)?value:null;
  try{
    if(!['inspect','probe'].includes(mode)||!/^[A-Za-z0-9_-]{11}$/.test(videoId))fail('invalid_request');
    const page=new URL(location.href),player=document.getElementById('movie_player'),video=player?.querySelector('video');
    if(page.origin!=='https://www.youtube.com'||page.pathname!=='/watch'||page.searchParams.get('v')!==videoId||player?.getVideoData?.().video_id!==videoId)fail('source_identity_mismatch');
    if(!video||video.mediaKeys||player.classList.contains('ad-showing')||player.classList.contains('ad-interrupting'))fail('source_not_eligible');
    if(video.error||video.readyState<3||!number(video.duration))fail('source_not_ready');
    let response=player.getPlayerResponse?.();
    if(!response||typeof response!=='object')response=window.ytInitialPlayerResponse;
    if(response?.videoDetails?.videoId!==videoId)fail('player_response_identity_mismatch');
    if(response.playabilityStatus?.status!=='OK'||response.videoDetails.isLive===true)fail('source_not_playable_vod');
    const streaming=response.streamingData||{};
    const formats=(streaming.adaptiveFormats||[]).filter(x=>/^audio\/(webm|mp4)(?:;\s*codecs="[A-Za-z0-9., _-]{1,100}")?$/.test(x.mimeType||'')&&!x.width&&!x.height&&Number.isInteger(x.itag)).slice(0,64);
    const direct=format=>{
      if(typeof format.url!=='string')return false;
      try{const url=new URL(format.url);return url.protocol==='https:'&&!url.username&&!url.password&&!url.port&&/^(?:[a-z0-9-]+\.)+googlevideo\.com$/i.test(url.hostname)&&url.pathname==='/videoplayback';}catch{return false;}
    };
    const client=window.ytcfg?.get?.('INNERTUBE_CONTEXT')?.client;
    const inventory={schema_version:1,video_id:videoId,source_duration:video.duration,source_time:video.currentTime,
      mode:'accepted_browser_native_inspection',reencoded:false,has_sabr:typeof streaming.serverAbrStreamingUrl==='string',
      has_hls:typeof streaming.hlsManifestUrl==='string',
      has_ustreamer_config:typeof response.playerConfig?.mediaCommonConfig?.mediaUstreamerRequestConfig?.videoPlaybackUstreamerConfig==='string',
      has_client_info:!!client&&typeof client==='object',client_name:safeTrack(client?.clientName),client_version:safeTrack(client?.clientVersion),
      has_published_po_token:typeof response.serviceIntegrityDimensions?.poToken==='string',
      formats:formats.map(x=>({itag:x.itag,mime_type:x.mimeType,
        bytes:number(x.contentLength),duration_seconds:number(x.approxDurationMs)?Number(x.approxDurationMs)/1000:null,
        bitrate:number(x.bitrate),audio_sample_rate:number(x.audioSampleRate),audio_channels:number(x.audioChannels),
        direct_url_available:direct(x),cipher_only:!x.url&&!!(x.signatureCipher||x.cipher),
        audio_track_id:safeTrack(x.audioTrack?.id),audio_is_default:x.audioTrack?.audioIsDefault===true}))};
    if(mode==='inspect')return inventory;
    const format=formats.find(x=>x.itag===itag&&direct(x));if(!format)fail('direct_audio_format_unavailable');
    const expected=number(format.contentLength);if(!Number.isSafeInteger(expected)||expected>100*1024*1024)fail('unbounded_source_size');
    const key=`${videoId}:${itag}`;
    const registry=window.__researchNativeProbeAttempts||(window.__researchNativeProbeAttempts=new Set());
    if(!(registry instanceof Set)||registry.has(key))fail('probe_already_attempted');
    registry.add(key); // Includes errors: no same-source retry in this page lifetime.
    const length=Math.min(65536,expected),end=length-1,controller=new AbortController();
    const timer=setTimeout(()=>controller.abort(),20000);let reader;
    try{
      // Browser-default credentials and transport. No synthetic headers, tokens or client identities.
      const result=await fetch(format.url,{method:'GET',credentials:'same-origin',mode:'cors',cache:'no-store',redirect:'error',
        headers:{Range:`bytes=0-${end}`},signal:controller.signal});
      if(result.status===403||result.status===429){controller.abort();fail(`source_http_${result.status}`);}
      if(result.status!==206){controller.abort();fail('partial_response_required');}
      const range=result.headers.get('Content-Range')||'',match=/^bytes 0-(\d+)\/(\d+)$/.exec(range);
      if(!match||Number(match[1])!==end||Number(match[2])!==expected){controller.abort();fail('range_proof_mismatch');}
      if(Number(result.headers.get('Content-Length'))!==length){controller.abort();fail('response_size_mismatch');}
      const type=(result.headers.get('Content-Type')||'').split(';')[0];
      if(!['audio/webm','audio/mp4','application/octet-stream'].includes(type)){controller.abort();fail('response_type_mismatch');}
      reader=result.body?.getReader();if(!reader)fail('response_body_missing');
      const data=new Uint8Array(length);let bytes=0;
      for(;;){const chunk=await reader.read();if(chunk.done)break;if(bytes+chunk.value.byteLength>length){controller.abort();fail('response_body_oversized');}data.set(chunk.value,bytes);bytes+=chunk.value.byteLength;}
      if(bytes!==length)fail('response_body_truncated');
      const container=data[0]===0x1a&&data[1]===0x45&&data[2]===0xdf&&data[3]===0xa3?'webm':
        new TextDecoder().decode(data.subarray(4,8))==='ftyp'?'mp4':null;
      if(!container)fail('audio_container_unrecognized');
      const digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',data)),x=>x.toString(16).padStart(2,'0')).join('');
      return {schema_version:1,video_id:videoId,itag,source_duration:video.duration,reencoded:false,
        state:'bounded_native_prefix_verified',http_status:206,bytes,expected_total_bytes:expected,container,
        prefix_sha256:digest,complete:false};
    }finally{clearTimeout(timer);controller.abort();if(reader){try{await reader.cancel();}catch{}}}
  }catch(error){return {schema_version:1,video_id:/^[A-Za-z0-9_-]{11}$/.test(videoId)?videoId:null,
    state:'held',error:/^[a-z0-9_]{1,80}$/.test(error?.message||'')?error.message:'browser_fetch_failed',complete:false};}
}
