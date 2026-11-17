import test from 'node:test';
import assert from 'node:assert/strict';
import {classifySabrError,createSabrDiagnostics,observeSabrInternals,validateSabrDiagnostics} from '../native-sabr-diagnostics.js';
import {validateNativeRpc} from '../native-rpc.js';
const identity={itag:140,lastModified:'123',xtags:'published'};

test('SDK failures map to finite causes without exporting raw errors',()=>{
  for(const [text,kind] of [
    ['Stream stalled 3 times. Aborting','sdk_stalled'],['Request timed out','sdk_request_timeout'],
    ['Streaming data reload requested but no handler was found','sdk_reload_handler_missing'],
    ['An error occurred while reloading streaming data: https://private/secret','sdk_reload_failed'],
    ['SABR Error: STREAM_ERROR - 42','sdk_sabr_error'],
    ['Stream protection attestation rejected after 5 attempts','sdk_protection_rejected'],
    ['Could not select formats: private context','sdk_format_selection_failed'],
    ['URL https://private/token and Stream stalled 3 times. Aborting','sdk_unknown_error']]){
    const result=classifySabrError(Error(text));assert.equal(result.kind,kind);
    assert.ok(!JSON.stringify(result).includes('private'));
  }
  assert.deepEqual(classifySabrError(Error('SABR Error: STREAM_ERROR - 42')),{kind:'sdk_sabr_error',code:42});
});

test('instrumentation preserves original requests, returns, failures and own-field semantics',async()=>{
  const diag=createSabrDiagnostics(identity),body=new Uint8Array([1,2]),calls=[],originalError=Error('unchanged');
  class Fake {
    nextRequestPolicy;
    buildRequestBody(...args){calls.push(args);return body;}
    seekTo(...args){calls.push(args);return 123;}
    tryReloadStreamingData(){throw originalError;}
  }
  const stream=new Fake();observeSabrInternals(stream,diag,{decode:raw=>{
    assert.equal(raw,body);return {clientAbrState:{playerTimeMs:69892},selectedAudioFormatIds:[identity],
      selectedVideoFormatIds:[],initializationFormatIds:[identity],bufferedRanges:[{formatId:identity,startTimeMs:0,durationMs:69892}],
      streamerContext:{poToken:new Uint8Array([1]),playbackCookie:{SECRET:'must not export'},sabrContexts:[]}};
  }});
  assert.equal(stream.buildRequestBody('original',5),body);assert.deepEqual(calls[0],['original',5]);
  const policy={backoffTimeMs:100,targetAudioReadaheadMs:25000,playbackCookie:'SECRET'};
  stream.nextRequestPolicy=policy;assert.equal(stream.nextRequestPolicy,policy);
  assert.equal(stream.seekTo(69892,'server'),123);assert.throws(()=>stream.tryReloadStreamingData(),error=>error===originalError);
  const snapshot=diag.snapshot();assert.equal(snapshot.latest.request.playerTimeMs,69892);
  assert.equal(snapshot.latest.request.selectedAudioMatches,true);assert.equal(snapshot.latest.request.bufferedDurationMs,69892);
  assert.equal(snapshot.counts.reload,1);assert.equal(snapshot.latest.seek.source,'server');assert.equal(snapshot.latest.policy.backoffTimeMs,100);
  assert.ok(!JSON.stringify(snapshot).includes('SECRET'));
  const broken=createSabrDiagnostics(identity);observeSabrInternals(stream,broken,{decode:()=>{throw Error('secret');}});
  assert.equal(stream.buildRequestBody('same'),body);assert.equal(broken.snapshot().counts.observer_error,1);
});

test('bounded telemetry rejects unknown/nested/credential fields at RPC boundary',()=>{
  const diag=createSabrDiagnostics(identity);for(let i=0;i<100;i++)diag.record('protection',{status:2,maxRetries:0,poToken:'SECRET'});
  diag.error(Error('Stream stalled 3 times. Aborting'));
  const value=diag.snapshot();assert.equal(value.events.length,16);assert.equal(value.counts.protection,100);
  assert.equal(value.latest.protection.maxRetries,0);assert.equal(value.errorKind,'sdk_stalled');
  assert.equal(value.latest.protection.poToken,undefined);assert.equal(value.latest.request,undefined);
  assert.equal(validateNativeRpc('state',{phase:'held',diagnostics:value}).diagnostics,value);
  for(const mutate of [x=>{x.poToken='secret';},x=>{x.events[0].url='https://private';},
    x=>{x.events[0].status='private';},x=>{x.errorKind='server raw text';},x=>{x.counts.protection=Infinity;},
    x=>{x.events.push(...x.events);},x=>{x.latest.protection.maxRetries=-1;}]){
    const bad=structuredClone(value);mutate(bad);assert.throws(()=>validateSabrDiagnostics(bad));
    assert.throws(()=>validateNativeRpc('state',{phase:'held',diagnostics:bad}),/native_rpc_schema/);
  }
});
