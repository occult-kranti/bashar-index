// Bounded, non-sensitive diagnostics survive worker cleanup until Chrome exits.
export const safeCode=value=>/^[a-z0-9_]{1,80}$/.test(value||'')?value:'operation_failed';
export function outcome(worker,{error,done=false}={}){
  const reason=worker.stop_reason||error;
  if(reason==='user_stopped'||reason==='tab_closed')return {state:'stopped',code:reason,badge:'',title:reason==='tab_closed'?'Capture stopped because the tab closed':'Capture stopped by you; click to start again'};
  if(reason)return {state:'held',code:safeCode(reason),badge:'ERR',title:`Capture held: ${safeCode(reason)}. Open extension options for details.`};
  if(done)return {state:'done',code:'queue_complete',badge:'DONE',title:'Queue complete for this worker'};
  return {state:'stopped',code:'capture_stopped',badge:'',title:'Capture stopped; click to start again'};
}
export function diagnostic(worker,result){
  return {worker_id:worker.worker_id,tab_id:worker.tab_id,video_id:worker.job?.video_id||null,
    capture_id:worker.job?.capture_id||null,state:result.state,code:result.code,at:new Date().toISOString()};
}
export function retainDiagnostic(existing,record){
  return [...existing.filter(x=>x.worker_id!==record.worker_id),record].slice(-16);
}
