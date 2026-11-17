import test from 'node:test';
import assert from 'node:assert/strict';
import {NativeGatewayClient,decodeMedia} from '../native-gateway-client.js';
const binding='a'.repeat(64),job='native-'+'b'.repeat(24);
test('browser global fetch receiver is retained when the gateway client stores it',async()=>{
  const client=new NativeGatewayClient(function(){assert.equal(this,globalThis);return Promise.resolve({ok:true,json:async()=>({token:'c'.repeat(40)})});});
  assert.deepEqual(await client.pair(),{paired:true});
});
function harness(badChunk=false){const calls=[];const client=new NativeGatewayClient(async(url,options)=>{
  calls.push({url,options});const op=url.split('/').at(-1);
  const body=op==='pair'?{token:'c'.repeat(40)}:op==='begin'?{jobId:job,sourceBindingSha256:binding,acknowledgedBytes:0,nextSequence:0}:
    op==='chunk'?{acknowledgedBytes:badChunk?99:Number(options.headers['X-Native-Offset'])+options.body.length,nextSequence:Number(options.headers['X-Native-Seq'])+1}:{retained:true};
  return {ok:true,json:async()=>body};});return {client,calls};}
test('extension decodes bounded JSON media to binary with strict offset/sequence ACKs',async()=>{
  const {client,calls}=harness();await client.pair();await client.call('begin',{});
  assert.equal((await client.call('chunk',{offset:0,base64:btoa('abc')})).acknowledgedBytes,3);
  await client.call('chunk',{offset:3,base64:btoa('def')});
  assert.deepEqual([...calls[2].options.body],[97,98,99]);assert.equal(calls[3].options.headers['X-Native-Seq'],'1');
  for(const call of calls){assert(call.url.startsWith('http://127.0.0.1:8781/'));assert.equal(call.options.credentials,'omit');assert.equal(call.options.redirect,'error');}
  assert.equal(calls[2].options.headers['Content-Type'],'application/octet-stream');
});
test('ambiguous chunk ACK holds job, never retries; retain remains available',async()=>{
  const {client,calls}=harness(true);await client.pair();await client.call('begin',{});
  await assert.rejects(client.call('chunk',{offset:0,base64:btoa('abc')}),/native_chunk_ack/);
  await assert.rejects(client.call('chunk',{offset:0,base64:btoa('abc')}),/native_job_held/);
  await client.call('retain',{error_class:'integrity'});assert.equal(calls.filter(x=>x.url.endsWith('/chunk')).length,1);
});
test('oversized/base64-invalid media and unapproved endpoint operations are rejected',async()=>{
  assert.throws(()=>decodeMedia('a'.repeat(1024*1024+4)),/native_chunk_encoding/);
  assert.throws(()=>decodeMedia('https://secret'),/native_chunk_encoding/);
  const {client,calls}=harness();await client.pair();await client.call('begin',{});
  await assert.rejects(client.call('arbitrary_url',{url:'https://example.com'}),/native_rpc_operation/);assert.equal(calls.length,2);
});
test('lost finish response keeps status available and permits only one identical finish retry',async()=>{
  const {client,calls}=harness();await client.pair();await client.call('begin',{});
  const original=client.fetcher;let finish=0;
  client.fetcher=async(url,options)=>{if(url.endsWith('/finish')&&++finish===1)throw Error('lost_ack');return original(url,options);};
  const body={sourceBindingSha256:binding,bytes:3};await assert.rejects(client.call('finish',body),/lost_ack/);
  await client.call('status');await assert.rejects(client.call('finish',{...body,bytes:4}),/native_finish_changed/);
  await client.call('finish',body);await assert.rejects(client.call('finish',body),/native_finish_changed/);assert.equal(finish,2);
});
