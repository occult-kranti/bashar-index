import {service} from './core.js';
const list=document.querySelector('#workers'),stop=document.querySelector('#stop-all'),health=document.querySelector('#health');
async function refresh(){
  try{const state=await chrome.runtime.sendMessage({target:'background',type:'status'});list.replaceChildren();
    for(const worker of state.workers||[]){const row=document.createElement('div');row.className='worker';
      const source=document.createElement('strong');source.textContent=worker.video_id||'Preparing tab';
      const status=document.createElement('span');status.className='state';status.textContent=(worker.state||'waiting').replaceAll('_',' ');row.append(source,status);list.append(row);}
    if(!state.workers?.length){const empty=document.createElement('p');empty.textContent='No tabs activated. Open a YouTube video, then click the extension button.';list.append(empty);}
    stop.disabled=!state.workers?.length;
  }catch{list.textContent='Extension status unavailable. Reload this page.';}
}
stop.addEventListener('click',async()=>{stop.disabled=true;await chrome.runtime.sendMessage({target:'background',type:'stop_all'});await refresh();});
service('/health',{method:'GET'}).then(()=>{health.textContent='Local archive service is available at 127.0.0.1:8768.';}).catch(()=>{health.textContent='Start the local archive service before activating a tab.';});
refresh();setInterval(refresh,2000);
