// Inspect an ordinary response copy. Only SPS is decoded; media is discarded
// incrementally by the maintained UmpReader, never concatenated or exported.
export async function readNormalProtection({sdk,response,admit,registerReader,checkActive}){
  const need=(ok,code)=>{if(!ok)throw Error(code);};
  need(sdk?.UmpReader&&sdk?.StreamProtectionStatus?.decode,'observer_sdk_missing');
  need(response.status===200&&response.contentType==='application/vnd.yt-ump','normal_request_not_accepted');
  let status=null,partial=null,reader=null;
  const decode=data=>{
    const result=sdk.StreamProtectionStatus.decode(data);
    need(Number.isSafeInteger(result.status)&&[1,2,3].includes(result.status),'normal_protection_invalid');
    status=result.status;need(status!==3,'stream_protection_rejected');
  };
  const copy=(data,target,offset=0)=>{for(const chunk of data.chunks){target.set(chunk,offset);offset+=chunk.length;}return offset;};
  const parser=new sdk.UmpReader({
    onPart(type,data){if(type!==58)return;need(data.totalLength<=65536,'normal_control_too_large');decode(copyBytes(data));},
    onPartialPart(type,data,offset,total){
      if(type!==58)return true; // Drop partial MEDIA and all unrelated controls.
      need(Number.isSafeInteger(total)&&total>0&&total<=65536,'normal_control_too_large');
      if(offset===0)partial={bytes:new Uint8Array(total),offset:0};
      need(partial&&partial.offset===offset&&offset+data.totalLength<=total,'normal_control_fragment');
      partial.offset=copy(data,partial.bytes,offset);
      if(partial.offset===total){decode(partial.bytes);partial=null;}return true;
    }
  });
  function copyBytes(data){const result=new Uint8Array(data.totalLength);copy(data,result);return result;}
  async function feed(raw){
    checkActive();need(raw instanceof Uint8Array,'normal_response_bytes');admit(raw.byteLength);
    // Bound parser retained fragments independently of a large browser chunk.
    for(let offset=0;offset<raw.length;offset+=16384){checkActive();await parser.feed(raw.subarray(offset,offset+16384));}
  }
  try{
    if(response.body){
      reader=response.body.getReader();registerReader(reader,true);
      for(;;){checkActive();const part=await reader.read();checkActive();if(part.done)break;await feed(part.value);}
    }else{
      need(response.bytes instanceof Uint8Array,'normal_response_unreadable');await feed(response.bytes);
    }
    checkActive();need(parser.pendingType===undefined&&parser.compositeBuffer.totalLength===0&&!partial,'normal_response_incomplete');
    need(status===1,status===2?'normal_protection_pending':'normal_protection_missing');
    return {status:1};
  }finally{
    if(partial)partial.bytes.fill(0);parser.dispose();
    if(reader){registerReader(reader,false);void reader.cancel().catch(()=>{});try{reader.releaseLock();}catch{}}
  }
}
