import test from 'node:test';
import assert from 'node:assert/strict';
import {finishNativeWithProof} from '../native-finish.js';
const binding='a'.repeat(64),proof={sourceBindingSha256:binding,bytes:3},nativeProof={bytes:3,md5:'b'.repeat(32),sha256:'c'.repeat(64)};
test('lost finish ACK follows existing validation and never restarts source or begin',async()=>{
  const calls=[];let status=0,clock=0;
  const result=await finishNativeWithProof({proof,binding,durationMs:10000,now:()=>clock,sleep:async ms=>{clock+=ms;},rpc:async(op,value)=>{
    calls.push(op);if(op==='finish')throw Error('lost_ack');return {sourceBindingSha256:binding,state:'validating',...(status++?{nativeProof}:{})};}});
  assert.deepEqual(result,nativeProof);assert.deepEqual(calls,['finish','status','status']);
});
test('receiving after uncertain finish allows exactly one identical finish body',async()=>{
  const bodies=[];let attempts=0,clock=0;
  const result=await finishNativeWithProof({proof,binding,durationMs:10000,now:()=>clock,sleep:async ms=>{clock+=ms;},rpc:async(op,value)=>{
    if(op==='finish'){bodies.push(value);if(++attempts===1)throw Error('lost_ack');return {};}
    return {sourceBindingSha256:binding,state:attempts===1?'receiving':'local_validated',...(attempts>1?{nativeProof}:{})};}});
  assert.equal(bodies.length,2);assert.equal(bodies[0],bodies[1]);assert.deepEqual(result,nativeProof);
});
