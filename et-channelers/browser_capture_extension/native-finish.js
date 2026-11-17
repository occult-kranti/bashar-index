// Finish is idempotent on the server. Chunk/request ACKs are deliberately not.
export async function finishNativeWithProof({rpc,proof,binding,durationMs,now=Date.now,sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms))}){
  let uncertain=false,reposted=false;
  try{await rpc('finish',proof);}catch{uncertain=true;}
  const deadline=now()+Math.max(120000,durationMs/3+120000);
  while(now()<deadline){
    const status=await rpc('status');
    if(status.sourceBindingSha256!==binding)throw Error('native_status_binding');
    if(status.error)throw Error('native_validation_failed');
    if(status.nativeProof)return status.nativeProof;
    if(uncertain&&!reposted&&status.state==='receiving'){
      reposted=true;try{await rpc('finish',proof);}catch{} // same object/body; one bounded repeat
    }
    await sleep(2000);
  }
  throw Error('native_validation_timeout');
}
