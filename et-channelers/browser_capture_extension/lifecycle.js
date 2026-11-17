// An old asynchronous operation may release its stream, but never a replacement tab worker.
export async function cleanupWorker(worker,registry,operations){
  worker.stopping=true;
  try{await operations.releaseStream();}catch{}
  if(registry.get(worker.tab_id)!==worker)return false;
  if(worker.nonce){try{await operations.stopPage(worker.nonce);}catch{}}
  if(registry.get(worker.tab_id)!==worker)return false;
  registry.delete(worker.tab_id);await operations.persist();
  if(!registry.has(worker.tab_id))await operations.badge();
  return true;
}
