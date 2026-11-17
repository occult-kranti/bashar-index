import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash,webcrypto} from 'node:crypto';
import {EventEmitter} from 'node:events';
import {openNativeSabr} from '../browser_sabr_adapter.mjs';
globalThis.crypto ||= webcrypto;

const id='ABCDEFGHIJK';
const hash=x=>createHash('sha256').update(x).digest('hex');
function fixture(mode={}){
  const calls=[],events=[];
  const format={itag:251,lastModified:'123456',xtags:'AQ==',mimeType:'audio/webm; codecs="opus"',
    hasAudio:true,hasVideo:false,hasText:false,isOriginal:true,codecCode:'o',contentLength:4,language:'en'};
  const source={videoId:id,isLive:false,isPostLive:false,noDRM:true,durationMs:10000,audioFormat:format,
    serverAbrStreamingUrl:'https://rr1.googlevideo.com/videoplayback?sabr=1&sig=PRIVATE',
    videoPlaybackUstreamerConfig:'PRIVATE_CONFIG',clientInfo:{clientName:1,clientVersion:'fixture'}};
  const segment=(number,start,end,bytes=number===0?1:mode.large?2*1024*1024:4)=>
    ({number,initialization:number===0,startTimeMs:start,endTimeMs:end,declaredBytes:bytes});
  class FakeSabr extends EventEmitter{
    static current;
    constructor(config){super();this.config=config;this.isAborted=false;this.isErrored=false;FakeSabr.current=this;}
    async abort(){this.isAborted=true;this.controller?.error(Error('cancelled'));}
    async snapshot(){return {playerTimeMs:10000,tracks:[{formatId:{itag:251,lastModified:'123456',xtags:'AQ=='},trackedSegments:[]}]};}
    start(options){
      this.options=options;
      const audioStream=new ReadableStream({start:controller=>{
        this.controller=controller;
        queueMicrotask(async()=>{
          try{
            await this.config.callbacks.onMintPoToken();
            await this.config.fetchFunction(mode.badHost||source.serverAbrStreamingUrl,{method:'POST'});
            if(mode.sdkError)throw Error(mode.sdkError);
            if(mode.protection)this.emit('streamProtectionStatusUpdate',{status:3});
            const segments=mode.resume?[segment(0,0,0),segment(1,0,5000,2),segment(2,5000,10000)]:
              mode.gap?[segment(0,0,0),segment(2,5000,10000)]:[segment(0,0,0),segment(1,0,10000)];
            const trackedSegments=new Map(segments.map(s=>[s.number,{startTimeMs:s.startTimeMs,endTimeMs:s.endTimeMs,
              mediaHeader:{videoId:mode.wrongId?'WRONGID0001':id,isInitializationSegment:s.initialization,
                segmentLengthBytes:String(mode.badLength&&s.number===1?99:s.declaredBytes)}}]));
            this.emit('trackStateUpdate',{audio:{trackedSegments,endOfStreamReached:!mode.noEos,
              endSegmentNum:mode.resume||mode.gap?2:1,endTimeMs:mode.duration||10000}});
            if(!mode.resume)controller.enqueue(new TextEncoder().encode('i'));
            if(!mode.missingMedia)controller.enqueue(mode.large?new Uint8Array(2*1024*1024):new TextEncoder().encode('tail'));
            this.emit('finish');controller.close();
          }catch(error){this.isErrored=true;this.emit('error',error);controller.error(error);}
        });
      }});
      return {audioStream,selectedFormats:{audioFormat:format}};
    }
  }
  let stored=mode.resume?Buffer.from('old'):Buffer.alloc(0);
  const sink={
    async reserve(n){events.push(['reserve',n]);if(mode.storage)throw Error('private disk diagnostic');},
    async write({offset,seq,bytes}){assert.equal(seq,events.filter(e=>e[0]==='write').length);
      assert.equal(offset,stored.length);events.push(['write',bytes.length]);stored=Buffer.concat([stored,bytes]);
      return {acknowledgedBytes:stored.length+(mode.badAck?1:0)};},
    async finish(proof){events.push(['finish',proof]);return {bytes:stored.length,sha256:hash(stored),md5:createHash('md5').update(stored).digest('hex')};},
    async retain(proof){events.push(['retain',proof]);},
    async verifyResume(value){events.push(['resume',value]);return {prefixVerified:!mode.badPrefix,segmentBoundaryVerified:!mode.badPrefix,
      bytes:stored.length,prefixSha256:hash(stored),segments:[
        {...segment(0,0,0),byteOffset:0,emittedBytes:1,sha256:hash('o'),initDiscardedBytes:0},
        {...segment(1,0,5000,2),byteOffset:1,emittedBytes:2,sha256:hash('ld'),initDiscardedBytes:0}]};}
  };
  const sdk={SabrStream:FakeSabr,EnabledTrackTypes:{AUDIO_ONLY:1},version:'5.0.1',
    FormatXTags:{decode:()=>({xtags:mode.defaultTrack?[]:[{key:'acont',value:'original'}]})},
    Logger:{getInstance:()=>({setLogLevels:n=>assert.equal(n,0)})}};
  const args={sdk,source,sink,maxBytes:mode.large?3*1024*1024:100,
    fetchInAcceptedContext:async(input,init)=>{calls.push({input,init});return new Response(new Uint8Array([0]),
      {status:mode.http||200,headers:{'content-type':'application/vnd.yt-ump'}});},
    getCurrentVideoPoToken:async()=>mode.noToken?null:new Uint8Array([1,2,3]),
    assertAcceptedContext:async()=>({accepted:!mode.changedContext,videoId:id})};
  return {args,calls,events,FakeSabr};
}

test('native full run uses audio-only zero retries and durable ordered sink ACKs',async()=>{
  const f=fixture(),session=await openNativeSabr(f.args),result=await session.run();
  assert.equal(result.state,'native_download_complete_pending_decode_and_drive');
  assert.equal(result.bytes,5);assert.equal(result.reencoded,false);assert.equal(result.container_reassembled,true);
  assert.equal(result.identity.codec,'opus');
  assert.equal(f.FakeSabr.current.options.maxRetries,0);
  assert.equal(f.FakeSabr.current.options.enabledTrackTypes,1);
  assert.equal(f.FakeSabr.current.config.audioHighWaterMark,3*1024*1024);
  assert.equal(f.FakeSabr.current.config.fetch,undefined);
  assert.equal(f.FakeSabr.current.config.stripDuplicateInit,false);
  assert.equal(f.FakeSabr.current.config.poToken,'AQID');
  assert.deepEqual(f.events.map(x=>x[0]),['reserve','write','reserve','write','finish']);
  assert.equal(f.events.at(-1)[1].decodeValidationRequired,true);
  assert.equal(f.events.at(-1)[1].segments[1].sha256,hash('tail'));
  assert.equal(f.events.at(-1)[1].segments[1].byteOffset,1);
  assert.notEqual(result.bytes,result.identity.contentLength);
  assert.ok(!JSON.stringify(result).includes('PRIVATE'));
});
test('SDK chunks split into at most1MiB admitted writes',async()=>{
  const f=fixture({large:true});await(await openNativeSabr(f.args)).run();
  assert.deepEqual(f.events.filter(x=>x[0]==='write').map(x=>x[1]),[1,1024*1024,1024*1024]);
});
test('streamed segment proof is ACKed before finish and bad ledger ACK retains data',async()=>{
  for(const badAck of [false,true]){
    const f=fixture();let chain='0'.repeat(64),count=0;
    f.args.sink.segment=async proof=>{
      assert.equal(proof.byteOffset+proof.emittedBytes,f.events.filter(e=>e[0]==='write').reduce((n,e)=>n+e[1],0));
      chain=hash(chain+'\n'+JSON.stringify(proof,Object.keys(proof).sort()));count++;
      return {segmentCount:count,ledgerSha256:badAck?'0'.repeat(64):chain};
    };
    const session=await openNativeSabr(f.args);
    if(badAck){await assert.rejects(session.run(),{code:'segment_sink_ack_mismatch'});
      assert.ok(!f.events.some(e=>e[0]==='finish'));}
    else{await session.run();const proof=f.events.at(-1)[1];
      assert.equal(proof.segmentCount,2);assert.equal(proof.segmentLedgerSha256,chain);assert.equal(proof.segments,undefined);}
  }
});
test('pilot request allowance is spent before fetch and denial never contacts source',async()=>{
  const missing=fixture();missing.args.requireRequestAuthorization=true;
  await assert.rejects(openNativeSabr(missing.args),{code:'request_authorization_required'});
  for(const mode of ['allowed','denied','wrong_binding','wrong_count','lost_ack']){
    const f=fixture();f.args.requireRequestAuthorization=true;let authorizations=0;
    f.args.sink.authorizeRequest=async request=>{
      assert.equal(f.calls.length,0);authorizations++;assert.equal(request.requestSequence,1);
      if(mode==='lost_ack')throw Error('private response diagnostic');
      return {...request,authorized:mode!=='denied',sourceRequests:mode==='wrong_count'?2:1,
        sourceBindingSha256:mode==='wrong_binding'?'0'.repeat(64):request.sourceBindingSha256};
    };
    const session=await openNativeSabr(f.args);
    if(mode==='allowed'){await session.run();assert.equal(f.calls.length,1);}
    else{await assert.rejects(session.run());assert.equal(f.calls.length,0);assert.equal(f.events.at(-1)[0],'retain');}
    assert.equal(authorizations,1);
  }
});
for(const status of [403,429])test(`HTTP${status} stops afterone request and retains partial data`,async()=>{
  const f=fixture({http:status});await assert.rejects((await openNativeSabr(f.args)).run(),
    {code:status===403?'source_forbidden':'source_rate_limited'});
  assert.equal(f.calls.length,1);assert.equal(f.events.at(-1)[0],'retain');
  assert.ok(!f.events.some(e=>e[0]==='finish'));
});
test('in-body protection rejection stops despiteHTTP200',async()=>{
  const f=fixture({protection:true});await assert.rejects((await openNativeSabr(f.args)).run(),{code:'stream_protection_rejected'});
  assert.equal(f.calls.length,1);assert.ok(f.FakeSabr.current.isAborted);
  assert.equal(f.events.filter(x=>x[0]==='write').length,0);
});

test('SDK stall retains a safe specific failure and bounded diagnostic without another source request',async()=>{
  const f=fixture({sdkError:'Stream stalled 3 times. Aborting'}),session=await openNativeSabr(f.args);
  await assert.rejects(session.run(),error=>error.code==='sdk_stalled'&&error.diagnostics.errorKind==='sdk_stalled');
  assert.equal(f.calls.length,1);assert.equal(f.events.at(-1)[0],'retain');
  assert.equal(f.events.at(-1)[1].diagnostics.counts.response,1);
  assert.equal(session.diagnostics().latest.response.status,200);
  assert.ok(!JSON.stringify(f.events.at(-1)).includes('PRIVATE'));
});
test('token and accepted-context gates run before any media fetch',async()=>{
  for(const mode of [{noToken:true},{changedContext:true}]){
    const f=fixture(mode);await assert.rejects(openNativeSabr(f.args));assert.equal(f.calls.length,0);
  }
});
test('default track and unknown DRM cannot substitute for source evidence',async()=>{
  const inferred=fixture({defaultTrack:true});await assert.rejects(openNativeSabr(inferred.args),{code:'original_audio_unproven'});
  assert.equal(inferred.calls.length,0);
  for(const change of [source=>{source.audioFormat.xtags='';source.selectionBasis='published_default_no_original_flag';},
    source=>{delete source.noDRM;},source=>{source.durationMs=10.5;}]){
    const f=fixture();change(f.args.source);await assert.rejects(openNativeSabr(f.args));assert.equal(f.calls.length,0);
  }
});
test('foreign media host, alternate variants and wrongidentity fail closed',async()=>{
  const foreign=fixture({badHost:'https://example.invalid/videoplayback'});
  await assert.rejects((await openNativeSabr(foreign.args)).run());assert.equal(foreign.calls.length,0);
  const variant=fixture();variant.args.source.audioFormat.isVb=true;
  await assert.rejects(openNativeSabr(variant.args),{code:'nonoriginal_audio_variant'});
  const wrong=fixture({wrongId:true});await assert.rejects((await openNativeSabr(wrong.args)).run());
  assert.ok(!wrong.events.some(e=>e[0]==='finish'));
});
test('lastsegment alone andduration alone do not establish completecontent',async()=>{
  for(const mode of [{gap:true},{noEos:true},{duration:30000},{badLength:true},{missingMedia:true}]){
    const f=fixture(mode);await assert.rejects((await openNativeSabr(f.args)).run());
    assert.ok(!f.events.some(e=>e[0]==='finish'));
  }
});
test('storage denial and mismatched ACK retain without finalproof',async()=>{
  for(const mode of [{storage:true},{badAck:true}]){
    const f=fixture(mode);await assert.rejects((await openNativeSabr(f.args)).run());
    assert.equal(f.events.at(-1)[0],'retain');assert.ok(!f.events.some(e=>e[0]==='finish'));
    assert.ok(!JSON.stringify(f.events.at(-1)).includes('private disk'));
  }
});
test('SDK snapshot alone is explicitly not a resumable filecheckpoint',async()=>{
  const f=fixture(),session=await openNativeSabr(f.args);await session.run();
  const candidate=await session.checkpointCandidate();assert.equal(candidate.resumable,false);
  assert.equal(candidate.acknowledgedBytes,5);assert.ok(!JSON.stringify(candidate).includes('PRIVATE'));
});
test('resume requires same fullformat and separately verified persistedprefix',async()=>{
  const first=fixture(),binding=(await openNativeSabr(first.args)).sourceBinding;
  const snapshot={playerTimeMs:5000,tracks:[{formatId:{itag:251,lastModified:'123456',xtags:'AQ=='},trackedSegments:[]}]};
  const resume={sourceBinding:binding,bytes:3,prefixSha256:hash('old'),snapshot};
  const bad=fixture({resume:true,badPrefix:true});bad.args.resume=resume;
  await assert.rejects(openNativeSabr(bad.args),{code:'resume_prefix_unproven'});assert.equal(bad.calls.length,0);
  const good=fixture({resume:true});good.args.resume=resume;
  const completed=await(await openNativeSabr(good.args)).run();assert.equal(completed.bytes,7);
  assert.equal(good.events[0][0],'resume');assert.deepEqual(good.FakeSabr.current.options.snapshot,snapshot);
  const wrong=fixture({resume:true});wrong.args.resume={...resume,sourceBinding:'0'.repeat(64)};
  await assert.rejects(openNativeSabr(wrong.args),{code:'resume_binding_mismatch'});assert.equal(wrong.calls.length,0);
});
