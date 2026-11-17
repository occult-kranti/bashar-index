import test from 'node:test';
import assert from 'node:assert/strict';
import {readNormalProtection} from '../native-sps.js';
import {umpSdk,sps,umpPart,concat} from './native-ump-fixture.mjs';
const response=bytes=>({status:200,contentType:'application/vnd.yt-ump',bytes});
const run=(raw,options={})=>readNormalProtection({sdk:umpSdk,response:response(raw),admit:()=>{},registerReader:()=>{},checkActive:()=>{},...options});

test('real UMP decoder requires SPS1, rejects SPS2/missing/rejected/truncated controls',async()=>{
  assert.deepEqual(await run(sps(1)),{status:1});
  for(const [raw,reason] of [[sps(2),'normal_protection_pending'],[sps(3),'stream_protection_rejected'],
    [new Uint8Array(),'normal_protection_missing'],[new Uint8Array([58,2,8]),'normal_response_incomplete'],
    [concat(sps(1),sps(3)),'stream_protection_rejected']])await assert.rejects(run(raw),new RegExp(reason));
});
test('fragmented media is discarded incrementally; only bounded SPS bytes reach decoder',async()=>{
  const raw=concat(umpPart(21,new Uint8Array(300000).fill(99)),sps(1));let maxBuffered=0,readBytes=0,decoded=0;
  class Reader extends umpSdk.UmpReader {async feed(bytes){await super.feed(bytes);maxBuffered=Math.max(maxBuffered,this.compositeBuffer.totalLength);}}
  const sdk={UmpReader:Reader,StreamProtectionStatus:{decode:bytes=>{decoded++;assert.equal(bytes.length,2);return umpSdk.StreamProtectionStatus.decode(bytes);}}};
  let offset=0;
  const body=new ReadableStream({pull(controller){if(offset===raw.length){controller.close();return;}const next=Math.min(offset+71,raw.length);controller.enqueue(raw.subarray(offset,next));offset=next;}});
  assert.deepEqual(await run(null,{sdk,response:{status:200,contentType:'application/vnd.yt-ump',body},admit:n=>{readBytes+=n;}}),{status:1});
  assert.equal(decoded,1);assert.equal(readBytes,raw.length);assert.ok(maxBuffered<=10);
});
test('oversized control and aggregate byte denial release only the observed reader',async()=>{
  await assert.rejects(run(umpPart(58,new Uint8Array(65537))),/normal_control_too_large/);
  let disposed=0,cancelled=0,bytes=0;
  const body=new ReadableStream({pull(c){c.enqueue(new Uint8Array([58,2,8,1]));},cancel(){cancelled++;}});
  await assert.rejects(run(null,{response:{status:200,contentType:'application/vnd.yt-ump',body},
    registerReader:(reader,add)=>{if(!add)disposed++;},admit:n=>{bytes+=n;if(bytes>4)throw Error('normal_response_read_limit');}}),/normal_response_read_limit/);
  assert.equal(disposed,1);assert.equal(cancelled,1);assert.equal(body.locked,false);
});
