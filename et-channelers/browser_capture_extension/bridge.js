(() => {
  if(globalThis.__researchAudioBridge)return;
  let config=null;
  chrome.runtime.onMessage.addListener((message,sender,reply)=>{
    if(sender.id!==chrome.runtime.id||message.target!=='bridge')return;
    if(message.type==='configure'){config={nonce:message.nonce,worker_id:message.worker_id};reply({ready:true});}
    if(message.type==='clear'){config=null;reply({ready:true});}
  });
  window.addEventListener('message',event=>{
    const value=event.data;
    if(event.source!==window||!config||value?.type!=='research-audio-state'||value.nonce!==config.nonce)return;
    chrome.runtime.sendMessage({target:'background',type:'sample',worker_id:config.worker_id,nonce:config.nonce,state:value.state}).catch(()=>{});
  });
  globalThis.__researchAudioBridge=true;
})();
