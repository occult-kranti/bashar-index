export const NATIVE_GATEWAY='http://127.0.0.1:8781';
const LIMIT=768*1024;
const need=(ok,code)=>{if(!ok)throw Error(code);};
export const safeNativeError=error=>/^[a-z0-9_]{1,80}$/.test(error?.message||'')?error.message:'native_operation_failed';
export function decodeMedia(value){
  need(typeof value==='string'&&value.length<=LIMIT/3*4&&/^[A-Za-z0-9+/]*={0,2}$/.test(value),'native_chunk_encoding');
  const raw=atob(value);need(raw.length>0&&raw.length<=LIMIT,'native_chunk_size');return Uint8Array.from(raw,x=>x.charCodeAt(0));
}
export class NativeGatewayClient{
  constructor(fetcher=fetch){this.fetcher=fetcher.bind(globalThis);this.token=null;this.job=null;this.binding=null;this.offset=0;this.seq=0;this.failed=false;this.writing=false;this.finishBody=null;this.finishAttempts=0;}
  async request(path,{body,method='POST',binary=false,headers={},timeout=15000}={}){
    const response=await this.fetcher(NATIVE_GATEWAY+path,{method,credentials:'omit',redirect:'error',cache:'no-store',signal:AbortSignal.timeout(timeout),
      headers:{...(this.token?{Authorization:`Bearer ${this.token}`}:{ }),...(body!==undefined?{'Content-Type':binary?'application/octet-stream':'application/json'}:{}),...headers},
      body:body===undefined?undefined:binary?body:JSON.stringify(body)});
    let result;try{result=await response.json();}catch{throw Error('native_gateway_response');}
    if(!response.ok)throw Error(safeNativeError({message:result.error}));
    if(result.stopAllSourceWorkers)throw Error('native_source_stopped');return result;
  }
  async pair(){
    const result=await this.request('/v1/pair',{body:{explicitUserActivation:true}});
    need(typeof result.token==='string'&&/^[A-Za-z0-9_-]{32,256}$/.test(result.token),'native_pair_response');this.token=result.token;
    return {paired:true};
  }
  async call(operation,value={}){
    need(this.token,'native_pairing_required');
    if(operation==='begin'){
      need(!this.job&&!this.failed,'native_job_already_started');
      try{const result=await this.request('/v1/begin',{body:value});need(/^native-[a-f0-9]{24}$/.test(result.jobId)&&/^[a-f0-9]{64}$/.test(result.sourceBindingSha256)&&result.acknowledgedBytes===0&&result.nextSequence===0,'native_begin_ack');
        this.job=result.jobId;this.binding=result.sourceBindingSha256;return result;
      }catch(error){this.failed=true;throw error;}
    }
    need(this.job,'native_job_missing');
    const path='/v1/jobs/'+this.job+'/';
    if(operation==='status')return this.request(path+'status',{method:'GET'});
    if(operation==='retain')return this.request(path+'retain',{body:{error_class:value.error_class}});
    need(!this.failed,'native_job_held');
    if(operation==='chunk'){
      need(!this.writing&&Number.isSafeInteger(value.offset)&&value.offset===this.offset,'native_chunk_offset');this.writing=true;
      try{const bytes=decodeMedia(value.base64);const result=await this.request(path+'chunk',{body:bytes,binary:true,headers:{'X-Native-Offset':String(this.offset),'X-Native-Seq':String(this.seq)}});
        need(result.acknowledgedBytes===this.offset+bytes.length&&result.nextSequence===this.seq+1,'native_chunk_ack');this.offset=result.acknowledgedBytes;this.seq++;return result;
      }catch(error){this.failed=true;throw error;}finally{this.writing=false;}
    }
    need(['request','segment','finish'].includes(operation),'native_rpc_operation');
    if(operation==='finish'){
      const body=JSON.stringify(value);need((this.finishBody===null||body===this.finishBody)&&this.finishAttempts<2,'native_finish_changed');
      this.finishBody=body;this.finishAttempts++;
      // Lost finish response can be recovered by status or this identical body.
      return this.request(path+operation,{body:value});
    }
    try{return await this.request(path+operation,{body:value});}catch(error){this.failed=true;throw error;}
  }
}
