import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {dirname,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash,webcrypto} from 'node:crypto';
import vm from 'node:vm';
import {createSabrDiagnostics,observeSabrInternals} from '../native-sabr-diagnostics.js';
const here=resolve(dirname(fileURLToPath(import.meta.url)),'..'),vendor=resolve(here,'vendor');
const sha=raw=>createHash('sha256').update(raw).digest('hex');

test('vendored SDK, adapter source and complete licenses match their manifest',async()=>{
  const manifest=JSON.parse(await readFile(resolve(vendor,'bundle-manifest.json'),'utf8'));
  assert.equal(manifest.namespace,'ChannelingNativeSabrV1');
  assert.deepEqual(manifest.dependencies.map(x=>[x.name,x.version]),[['googlevideo','5.0.1'],['@bufbuild/protobuf','2.17.0']]);
  assert.ok(!/[A-Z]:[\\/]|file:\/\//.test(JSON.stringify(manifest)));
  for(const item of manifest.outputs){
    assert.match(item.name,/^[A-Za-z0-9_.-]+$/);
    const raw=await readFile(resolve(vendor,item.name));assert.equal(raw.length,item.bytes);assert.equal(sha(raw),item.sha256);
  }
  assert.equal(sha(await readFile(resolve(here,'../pipeline/browser_sabr_adapter.mjs'))),manifest.adapter_sha256);
  const entry=manifest.source_files.find(x=>x.source==='packaging/native-sdk-entry.mjs');
  assert.equal(sha(await readFile(resolve(here,'native-sdk-entry.mjs'))),entry.sha256);
  assert.ok((await readFile(resolve(vendor,'THIRD_PARTY_NOTICES.txt'),'utf8')).includes('Apache License'));
});

test('real packaged SDK loads offline and cannot enable transport diagnostics',async()=>{
  const logs=[],requests=[];
  const context=vm.createContext({URL,URLSearchParams,ReadableStream,ByteLengthQueuingStrategy,Uint8Array,ArrayBuffer,
    DataView,TextEncoder,TextDecoder,AbortController,Response,Request,Headers,crypto:webcrypto,btoa,atob,performance,
    setTimeout,clearTimeout,queueMicrotask,createSabrDiagnostics,observeSabrInternals,fetch:()=>{requests.push(true);throw Error('offline');},
    console:Object.fromEntries(['log','warn','info','error','debug'].map(k=>[k,(...args)=>logs.push(args)]))});
  vm.runInContext(await readFile(resolve(vendor,'channeling-native-sabr-v1.iife.js'),'utf8'),context,{timeout:1000});
  const result=vm.runInContext(`(()=>{const api=ChannelingNativeSabrV1;
    api.Logger.getInstance().setLogLevels(99);api.Logger.getInstance().debug('fixture','must-not-log');
    const value=api.FormatXTags.decode(api.FormatXTags.encode({xtags:[{key:'acont',value:'original'}]}).finish());
    return {tag:value.xtags[0].value,version:api.sdk.version,audioOnly:api.EnabledTrackTypes.AUDIO_ONLY,
      exports:['SabrStream','buildSabrFormat','VideoPlaybackAbrRequest','openNativeSabr','UmpReader','StreamProtectionStatus'].every(k=>typeof api[k]==='function'||typeof api[k]==='object')};})()`,context);
  assert.equal(result.version,'5.0.1');assert.equal(result.tag,'original');assert.equal(result.audioOnly,1);assert.equal(result.exports,true);
  assert.equal(logs.length,0);assert.equal(requests.length,0);
  const codec=await vm.runInContext(`(async()=>{
    const api=ChannelingNativeSabrV1;
    const tags=btoa(String.fromCharCode(...api.FormatXTags.encode({xtags:[{key:'acont',value:'original'}]}).finish()));
    const format=api.buildSabrFormat({itag:140,lastModified:'123456',xtags:tags,
      mimeType:'audio/mp4; codecs="mp4a.40.2"',audioQuality:'AUDIO_QUALITY_MEDIUM',contentLength:'1234',approxDurationMs:'10000'});
    const session=await api.openNativeSabr({sdk:api.sdk,maxBytes:64000000,
      source:{videoId:'ABCDEFGHIJK',isLive:false,isPostLive:false,noDRM:true,durationMs:10000,audioFormat:format,
        serverAbrStreamingUrl:'https://fixture.googlevideo.com/videoplayback',videoPlaybackUstreamerConfig:'AA==',
        clientInfo:{clientName:1,clientVersion:'offline'}},
      fetchInAcceptedContext:()=>{throw Error('must_not_fetch');},getCurrentVideoPoToken:async()=>new Uint8Array([1]),
      assertAcceptedContext:async()=>({accepted:true,videoId:'ABCDEFGHIJK'}),
      sink:{reserve:async()=>{},write:async()=>{},finish:async()=>{},retain:async()=>{}}});
    const raw=new api.SabrStream({videoId:'ABCDEFGHIJK',formats:[format],poToken:'AQ==',
      serverAbrStreamingUrl:'https://fixture.googlevideo.com/videoplayback',videoPlaybackUstreamerConfig:'AA==',
      clientInfo:{clientName:1,clientVersion:'offline'}});
    const diag=createSabrDiagnostics(session.identity);observeSabrInternals(raw,diag,api.VideoPlaybackAbrRequest);
    const policy={backoffTimeMs:0,targetAudioReadaheadMs:25000};raw.nextRequestPolicy=policy;
    raw.seekTo(69892,'server');raw.buildRequestBody({playerTimeMs:69892,enabledTrackTypesBitfield:1},format);
    const result={sdkAlias:format.codecCode,boundCodec:session.identity.codec,diagnostics:diag.snapshot(),
      samePolicy:raw.nextRequestPolicy===policy,ownAccessor:typeof Object.getOwnPropertyDescriptor(raw,'nextRequestPolicy').set==='function'};
    await session.abort();return result;
  })()`,context);
  assert.equal(codec.sdkAlias,'a');assert.equal(codec.boundCodec,'aac');assert.equal(requests.length,0);
  assert.equal(codec.samePolicy,true);assert.equal(codec.ownAccessor,true);
  assert.equal(codec.diagnostics.latest.policy.backoffTimeMs,0);
  assert.equal(codec.diagnostics.latest.request.playerTimeMs,69892);
  assert.equal(codec.diagnostics.latest.request.selectedAudioMatches,true);
  assert.equal(codec.diagnostics.latest.seek.source,'server');
});
