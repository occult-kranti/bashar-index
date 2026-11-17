const list=document.querySelector('#workers'),stop=document.querySelector('#stop-all'),health=document.querySelector('#health'),history=document.querySelector('#diagnostics');
const inspections=document.querySelector('#inspections'),copy=document.querySelector('#copy-inspection');let latest=[];
async function refresh(){
  try{const state=await chrome.runtime.sendMessage({target:'background',type:'status'});list.replaceChildren();
    for(const worker of state.workers||[]){const row=document.createElement('div');row.className='worker';
      const source=document.createElement('strong');source.textContent=worker.video_id||'Preparing tab';
      const status=document.createElement('span');status.className='state';status.textContent=(worker.state||'waiting').replaceAll('_',' ');row.append(source,status);list.append(row);}
    if(!state.workers?.length){const empty=document.createElement('p');empty.textContent='No recording workers active.';list.append(empty);}
    stop.disabled=!state.workers?.length;
    latest=state.inspections||[];inspections.replaceChildren();copy.disabled=!latest.length;
    for(const item of [...latest].reverse()){
      const heading=document.createElement('h3');heading.textContent=item.video_id||'Tab inspection';inspections.append(heading);
      const summary=document.createElement('p');summary.textContent=item.state==='held'?`Held: ${item.error}`:
        `${item.formats.length} audio formats · SABR ${item.has_sabr?'present':'absent'} · streaming configuration ${item.has_ustreamer_config?'present':'absent'} · client ${item.client_name||'unknown'}`;
      inspections.append(summary);
      for(const format of item.formats||[]){const row=document.createElement('p');row.className='note';row.textContent=`Format ${format.itag}: ${format.mime_type}; ${format.bytes?`${(format.bytes/1048576).toFixed(2)} MiB`:'size unknown'}; ${format.direct_url_available?'direct URL present':format.cipher_only?'ciphered URL only':'SABR/other transport required'}`;inspections.append(row);}
    }
    if(!latest.length){const empty=document.createElement('p');empty.textContent='No tab inspected yet. Use the extension button on a playing YouTube watch page.';inspections.append(empty);}
    history.replaceChildren();
    for(const entry of [...(state.diagnostics||[])].reverse()){
      const row=document.createElement('div');row.className='worker';
      const source=document.createElement('strong');source.textContent=entry.video_id||'Tab activation';
      const detail=document.createElement('span');detail.className='state';
      detail.textContent=`${entry.state==='stopped'?'Stopped':entry.state==='done'?'Done':'Held'}: ${entry.code} · ${new Date(entry.at).toLocaleTimeString()}`;
      row.append(source,detail);history.append(row);
    }
    if(!state.diagnostics?.length){const empty=document.createElement('p');empty.textContent='No completed or stopped attempts in this Chrome session.';history.append(empty);}
  }catch{list.textContent='Extension status unavailable. Reload this page.';}
}
stop.addEventListener('click',async()=>{stop.disabled=true;await chrome.runtime.sendMessage({target:'background',type:'stop_all'});await refresh();});
copy.addEventListener('click',async()=>{try{await navigator.clipboard.writeText(JSON.stringify(latest,null,2));copy.textContent='Copied';}catch{copy.textContent='Copy unavailable';}});
health.textContent='Inspection only. No playback recording, media download, or local archive service connection.';
refresh();setInterval(refresh,2000);
