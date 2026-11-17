import {validateNativeRpc} from './native-rpc.js';
(() => {
  if(globalThis.__channelNativeBridge)return;
  let config=null;
  chrome.runtime.onMessage.addListener((value,sender,reply)=>{
    if(sender.id!==chrome.runtime.id||value.target!=='native-isolated')return;
    if(value.type==='configure'){config={nonce:value.nonce};reply({ready:true});}
    if(value.type==='clear'){config=null;reply({ready:true});}
  });
  window.addEventListener('message',event=>{
    const value=event.data;
    if(event.source!==window||!config||value?.type!=='channel-native-rpc'||value.nonce!==config.nonce||!Number.isSafeInteger(value.id))return;
    try{validateNativeRpc(value.operation,value.value);}catch{window.postMessage({type:'channel-native-ack',nonce:value.nonce,id:value.id,error:'native_rpc_schema'},location.origin);return;}
    // This bridge carries safe controls/native bytes only. No source URL,
    // browser credential, PO token or raw player response crosses realms.
    chrome.runtime.sendMessage({target:'native-background',nonce:config.nonce,id:value.id,operation:value.operation,value:value.value})
      .then(result=>window.postMessage({type:'channel-native-ack',nonce:value.nonce,id:value.id,...result},location.origin))
      .catch(()=>window.postMessage({type:'channel-native-ack',nonce:value.nonce,id:value.id,error:'native_bridge_unavailable'},location.origin));
  });
  globalThis.__channelNativeBridge=true;
})();
