(() => {
  globalThis.__researchAudioPage?.stop();
  let timer=null,nonce=null,expected=null,video=null,listeners=[];
  const current=()=>({v:document.querySelector('video.html5-main-video'),p:document.querySelector('#movie_player')});
  const live=(p,details,micro)=>p?.getVideoData?.().isLive===true||details?.isLive===true||micro?.liveBroadcastDetails?.isLiveNow===true;
  function state(){const {v,p}=current(),data=p?.getVideoData?.()||{},raw=globalThis.ytInitialPlayerResponse;
    const details=raw?.videoDetails?.videoId===data.video_id?raw.videoDetails:{};
    const micro=raw?.videoDetails?.videoId===data.video_id?raw?.microformat?.playerMicroformatRenderer:{};
    return {video_id:data.video_id||null,url_video_id:new URL(location.href).searchParams.get('v'),source_time:v?.currentTime,
      duration:v?.duration,playback_rate:v?.playbackRate,paused:v?.paused,ended:v?.ended,ready_state:v?.readyState,
      seeking:!!v?.seeking,muted:!!v?.muted,volume:v?.volume,media_error:v?.error?.code||null,protected_media:!!v?.mediaKeys,
      is_live:live(p,details,micro),ad:!!p&&(p.classList.contains('ad-showing')||p.classList.contains('ad-interrupting')),
      active_media_count:[...document.querySelectorAll('video,audio')].filter(x=>x===v||(!x.paused&&!x.ended&&x.readyState>0)).length};}
  function emit(){if(nonce)window.postMessage({type:'research-audio-state',nonce,state:state()},location.origin);}
  function stop(config){if(config?.nonce&&config.nonce!==nonce)return {skipped:true};clearInterval(timer);timer=null;for(const [event,handler] of listeners)video?.removeEventListener(event,handler);listeners=[];nonce=null;return {stopped:true};}
  function metadata(){const {p}=current(),data=p?.getVideoData?.()||{},raw=globalThis.ytInitialPlayerResponse;
    const details=raw?.videoDetails?.videoId===expected?raw.videoDetails:{};
    const micro=raw?.videoDetails?.videoId===expected?raw?.microformat?.playerMicroformatRenderer||{}:{};
    const text=(value,max)=>typeof value==='string'?value.slice(0,max):'';
    const images=(details.thumbnail?.thumbnails||[]).map(x=>x.url).filter(value=>{
      try{const u=new URL(value);return u.protocol==='https:'&&['i.ytimg.com','yt3.ggpht.com','yt3.googleusercontent.com'].includes(u.hostname)&&!u.username&&!u.password;}catch{return false;}}).slice(0,20);
    const chapters=[];
    for(const marker of [...document.querySelectorAll('ytd-macro-markers-list-item-renderer')].slice(0,500)){
      try{const link=marker.querySelector('a[href]'),url=new URL(link.href,location.origin);if(url.searchParams.get('v')!==expected)continue;
        const stamp=url.searchParams.get('t')||url.searchParams.get('start')||'';let seconds;
        if(/^\d+(?:\.\d+)?s?$/.test(stamp))seconds=Number(stamp.replace(/s$/,''));
        else{const match=stamp.match(/^(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?$/);if(match&&stamp)seconds=Number(match[1]||0)*3600+Number(match[2]||0)*60+Number(match[3]||0);}
        const title=text(marker.querySelector('#title')?.textContent?.trim(),500);
        if(title&&Number.isFinite(seconds)&&seconds>=0&&seconds<current().v.duration&&!chapters.some(x=>x.start_time===seconds))chapters.push({start_time:seconds,title});
      }catch{}}
    chapters.sort((a,b)=>a.start_time-b.start_time);
    return {title:text(details.title||data.title,2000),description:text(details.shortDescription,150000),
      channel_id:text(details.channelId||data.channel_id,200),channel_name:text(details.author||data.author,1000),author:text(details.author||data.author,1000),
      upload_date:text(micro.uploadDate,40),publish_date:text(micro.publishDate,40),
      language:text(details.defaultAudioLanguage||details.defaultLanguage,80),keywords:(details.keywords||[]).filter(x=>typeof x==='string').slice(0,300).map(x=>x.slice(0,300)),
      categories:typeof micro.category==='string'?[micro.category.slice(0,200)]:[],chapters,thumbnail_urls:images,
      view_count:/^\d+$/.test(details.viewCount||'')?Number(details.viewCount):null,
      capture_route:'chrome_tab_capture',artifact_kind:'browser_recorded_audio',reencoded:true,native_source_audio:false};}
  async function prepare(config){expected=config.video_id;
    for(let i=0;i<80;i++){const s=state();if(s.video_id===expected&&s.url_video_id===expected&&Number.isFinite(s.duration)&&s.duration>0&&s.ready_state>=2)break;await new Promise(r=>setTimeout(r,250));}
    const before=state();
    if(before.video_id!==expected||before.url_video_id!==expected)throw Error('source_not_ready');
    if(before.ad)throw Error('ad_detected');if(before.is_live)throw Error('live_source');if(before.protected_media)throw Error('protected_media');
    if(before.muted||before.volume<=0)throw Error('muted_source');if(before.active_media_count!==1)throw Error('additional_media');
    ({v:video}=current());video.pause();video.playbackRate=1;
    if(video.currentTime>.02){await new Promise((resolve,reject)=>{const done=()=>{clearTimeout(timeout);resolve();};const timeout=setTimeout(()=>{video.removeEventListener('seeked',done);reject(Error('seek_timeout'));},8000);video.addEventListener('seeked',done,{once:true});video.currentTime=0;});}
    const prepared=state();if(prepared.source_time>.15||prepared.ad||prepared.video_id!==expected)throw Error('start_alignment');
    return {state:prepared,source_metadata:metadata()};}
  function monitor(config){stop();nonce=config.nonce;expected=config.video_id;({v:video}=current());
    for(const event of ['ended','waiting','playing','pause','seeking','seeked','emptied','error','durationchange','ratechange','volumechange']){video.addEventListener(event,emit);listeners.push([event,emit]);}
    timer=setInterval(emit,250);emit();return {ready:true};}
  async function play(){const s=state();if(s.video_id!==expected||s.ad||s.source_time>.15)throw Error('start_alignment');await video.play();return {playing:true};}
  globalThis.__researchAudioPage={prepare,monitor,play,stop};
})();
