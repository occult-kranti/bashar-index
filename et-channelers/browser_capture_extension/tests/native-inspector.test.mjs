import test from 'node:test';
import assert from 'node:assert/strict';
import {nativeBrowserProbe} from '../native-inspector.js';
const id='abcdefghijk';
function setup({cipher=false,wrongId=false,ad=false}={}){
  const response={playabilityStatus:{status:'OK'},videoDetails:{videoId:wrongId?'mnopqrstuvw':id},streamingData:{serverAbrStreamingUrl:'private-control-token',adaptiveFormats:[{itag:251,mimeType:'audio/webm; codecs="opus"',contentLength:'100000',approxDurationMs:'10000',audioChannels:2,...(cipher?{signatureCipher:'private-cipher'}:{url:'https://rr1.googlevideo.com/videoplayback?private=secret'})}]}};
  globalThis.window={};globalThis.location={href:`https://www.youtube.com/watch?v=${id}`};
  globalThis.document={getElementById:()=>({getVideoData:()=>({video_id:id}),getPlayerResponse:()=>response,classList:{contains:()=>ad},querySelector:()=>({duration:10,currentTime:3,readyState:4})})};
  return response;
}
test('inspection makes no request and exports no signed URL, control URL or cipher',async()=>{
  setup();globalThis.fetch=()=>{throw Error('network_must_not_run');};
  const result=await nativeBrowserProbe('inspect',id);assert.equal(result.formats[0].direct_url_available,true);assert.equal(result.has_sabr,true);
  assert(!JSON.stringify(result).includes('private'));assert(!JSON.stringify(result).includes('secret'));
  setup({cipher:true});const cipher=await nativeBrowserProbe('inspect',id);assert.equal(cipher.formats[0].cipher_only,true);assert.equal(cipher.formats[0].direct_url_available,false);
});
test('ad or stale response fails before any source access',async()=>{
  setup({wrongId:true});assert.equal((await nativeBrowserProbe('probe',id,251)).error,'player_response_identity_mismatch');
  setup({ad:true});assert.equal((await nativeBrowserProbe('probe',id,251)).error,'source_not_eligible');
});
test('valid exact range produces only prefix proof, never a full-file claim',async()=>{
  setup();const data=new Uint8Array(65536);data.set([0x1a,0x45,0xdf,0xa3]);let calls=0;
  globalThis.fetch=async(url,options)=>{calls++;assert.equal(options.credentials,'same-origin');assert.equal(options.headers.Range,'bytes=0-65535');return new Response(data,{status:206,headers:{'Content-Range':'bytes 0-65535/100000','Content-Length':'65536','Content-Type':'audio/webm'}});};
  const result=await nativeBrowserProbe('probe',id,251);assert.equal(result.state,'bounded_native_prefix_verified');assert.equal(result.complete,false);assert.equal(result.prefix_sha256.length,64);assert.equal(calls,1);
});
test('403 is terminal for this format in page lifetime, with no retry or endpoint substitution',async()=>{
  setup();let calls=0;globalThis.fetch=async()=>{calls++;return new Response('',{status:403});};
  assert.equal((await nativeBrowserProbe('probe',id,251)).error,'source_http_403');
  assert.equal((await nativeBrowserProbe('probe',id,251)).error,'probe_already_attempted');assert.equal(calls,1);
});
test('ignored or mismatched range is rejected without reading body',async()=>{
  for(const status of [200,206]){setup();globalThis.fetch=async()=>({status,headers:new Headers({'Content-Range':'bytes 1-65536/100000','Content-Length':'65536'}),get body(){throw Error('body_must_not_be_read');}});
    assert.equal((await nativeBrowserProbe('probe',id,251)).error,status===200?'partial_response_required':'range_proof_mismatch');}
});
