import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import vm from 'node:vm';
import {validateNativeRpc} from '../native-rpc.js';
const identity={videoId:'EliqxbbQoRw',itag:140,lastModified:'1234',xtags:'YWJj',mimeType:'audio/mp4; codecs="mp4a.40.2"',durationMs:1570961,language:'en-US',codec:'mp4a.40.2',contentLength:25400000,originalBasis:'published_original',trackId:'en-US.4',noDRM:true,audioOnly:true};
test('public binding/metadata pass while added URL/session fields are rejected before authority',()=>{
  const begin={identity,transportKind:'sabr_reassembled',outputBudgetBytes:64000000,metadata:{id:identity.videoId,title:'Published',thumbnails:[{url:'https://i.ytimg.com/vi/abcdefghijk/default.jpg'}]}};
  assert.equal(validateNativeRpc('begin',begin),begin);
  assert.throws(()=>validateNativeRpc('begin',{...begin,metadata:{...begin.metadata,poToken:'secret'}}),/native_rpc_schema/);
  assert.throws(()=>validateNativeRpc('state',{phase:'downloading_native_audio',identity:{...identity,url:'https://secret'}}),/native_rpc_schema/);
  assert.throws(()=>validateNativeRpc('begin',{...begin,metadata:{...begin.metadata,description:'https://rr1.googlevideo.com/videoplayback?token=x'}}),/native_rpc_schema/);
  assert.throws(()=>validateNativeRpc('chunk',{offset:0,base64:'a'.repeat(1048577)}),/native_rpc_schema/);
});
test('ordinary-response acceptance proof has an exact nonsecret schema and requires SPS1',()=>{
  const proof={basis:'matching_normal_player_sps1',http_status:200,sps_status:1,complete_response:true,
    video_id:identity.videoId,same_video:true,same_configuration:true,request_format_matches_catalog:true,
    observed_at_epoch:1794890000,observer_session_id:'12345678-1234-1234-1234-123456789abc'};
  const begin={identity,transportKind:'sabr_reassembled',outputBudgetBytes:64000000,metadata:{id:identity.videoId,native_source_acceptance:proof}};
  assert.equal(validateNativeRpc('begin',begin),begin);
  for(const change of [{sps_status:2},{complete_response:false},{poToken:'SECRET'},{observer_session_id:'https://private'},
    {video_id:'other_video'}])assert.throws(()=>validateNativeRpc('begin',{...begin,metadata:{...begin.metadata,native_source_acceptance:{...proof,...change}}}),/native_rpc_schema/);
});
test('isolated bridge rejects arbitrary page values and wrong nonce before extension runtime',async()=>{
  let configure,receive;const forwarded=[],replies=[],window={addEventListener:(type,fn)=>{receive=fn;},postMessage:value=>replies.push(value)};
  const context={URL,window,location:{origin:'https://www.youtube.com'},chrome:{runtime:{id:'fixture',onMessage:{addListener:fn=>{configure=fn;}},sendMessage:async value=>{forwarded.push(value);return {value:{accepted:true}};}}}};
  vm.runInNewContext(await readFile(new URL('../native-isolated-bridge.iife.js',import.meta.url),'utf8'),context);
  configure({target:'native-isolated',type:'configure',nonce:'nonce'},{id:'fixture'},()=>{});
  receive({source:window,data:{type:'channel-native-rpc',nonce:'wrong',id:1,operation:'status',value:{}}});
  receive({source:window,data:{type:'channel-native-rpc',nonce:'nonce',id:2,operation:'state',value:{phase:'held',error:'https://private'}}});
  assert.equal(forwarded.length,0);assert.equal(replies.at(-1).error,'native_rpc_schema');
  receive({source:window,data:{type:'channel-native-rpc',nonce:'nonce',id:3,operation:'status',value:{}}});
  await new Promise(resolve=>setImmediate(resolve));assert.equal(forwarded.length,1);assert.equal(replies.at(-1).value.accepted,true);
});
