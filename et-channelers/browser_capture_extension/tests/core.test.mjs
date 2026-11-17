import assert from 'node:assert/strict';
import test from 'node:test';
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {CoverageGuard,coverageComplete,validateJob,videoFromUrl,service,SERVICE} from '../core.js';

const ID='abcdefghijk';
const sample=(time,extra={})=>({video_id:ID,url_video_id:ID,source_time:time,duration:2,playback_rate:1,
  paused:false,ended:false,ready_state:4,seeking:false,muted:false,volume:1,media_error:null,
  protected_media:false,is_live:false,ad:false,active_media_count:1,...extra});
test('public key produces pinned service Origin, permissions contain no account or network interception access',async()=>{
  const manifest=JSON.parse(await readFile(new URL('../manifest.json',import.meta.url)));
  const id=createHash('sha256').update(Buffer.from(manifest.key,'base64')).digest('hex').slice(0,32).replace(/[0-9a-f]/g,x=>String.fromCharCode(97+parseInt(x,16)));
  assert.equal(id,'egndajoiodmfaakhopchlaikhpdjdcnb');
  assert.deepEqual(manifest.host_permissions,['http://127.0.0.1:8768/*','http://127.0.0.1:8781/*','https://www.youtube.com/*']);
  assert(!manifest.permissions.some(x=>/cookies|webRequest|debugger|tabs/.test(x)));
});
test('navigation is bound to exact public video and origin',()=>{
  assert.equal(videoFromUrl(`https://www.youtube.com/watch?v=${ID}`),ID);
  assert.equal(videoFromUrl(`https://www.youtube.com.evil.invalid/watch?v=${ID}`),null);
  assert.throws(()=>validateJob({capture_id:'x',video_id:ID,watch_url:'https://evil.invalid'}),/invalid_watch_url/);
  assert.equal(validateJob({capture_id:'x',video_id:ID,watch_url:`https://www.youtube.com/watch?v=${ID}&feature=share`,duration_seconds:null}).watch_url,`https://www.youtube.com/watch?v=${ID}`);
});
test('buffering pauses and complete source-end coverage resumes without silently accepting a prefix',()=>{
  const guard=new CoverageGuard(ID,2);
  assert.equal(guard.sample(sample(0),0).action,'record');
  assert.equal(guard.sample(sample(1,{ready_state:2}),1).action,'pause');
  assert.equal(guard.sample(sample(1,{ready_state:2}),20).action,'pause');
  assert.equal(guard.sample(sample(1),20.01).action,'record');
  const done=guard.sample(sample(2,{ended:true}),21.01);
  assert.equal(done.action,'complete');assert(coverageComplete(done.intervals,2));
  assert.equal(coverageComplete([[0,1]],2),false);
  assert.equal(coverageComplete([[0,1],[1.5,2]],2),false);
});
test('ads, source changes, seeking, rate changes, extra media and DRM all abort',()=>{
  for(const [change,reason] of [[{ad:true},'ad_detected'],[{video_id:'ABCDEFGHIJK'},'source_changed'],
    [{url_video_id:'ABCDEFGHIJK'},'source_changed'],[{seeking:true},'unexpected_seek'],[{playback_rate:2},'playback_rate_changed'],
    [{protected_media:true},'protected_media'],[{active_media_count:2},'additional_media'],[{muted:true},'muted_source']]){
    const guard=new CoverageGuard(ID,2);guard.sample(sample(0),0);
    assert.deepEqual(guard.sample(sample(.2,change),.2),{action:'abort',reason});
  }
});
test('clock resets and invalid duration are not accepted as complete',()=>{
  const guard=new CoverageGuard(ID,2);guard.sample(sample(0),0);guard.sample(sample(1),1);
  assert.equal(guard.sample(sample(0),1.1).reason,'content_clock_gap');
  assert.equal(new CoverageGuard(ID,2).sample(sample(0,{duration:NaN}),0).reason,'duration_changed');
  assert.equal(new CoverageGuard(ID,2).sample(sample(.5),0).reason,'start_alignment');
});
test('local API never includes browser cookies and never follows redirects',async()=>{
  const previous=globalThis.fetch;let seen;
  globalThis.fetch=async(url,options)=>{seen={url,options};return {ok:true,json:async()=>({accepted:true})};};
  try{await service('/start',{token:'test-token',body:{capture_id:'test'}});
    assert.equal(seen.url,SERVICE+'/start');assert.equal(seen.options.credentials,'omit');
    assert.equal(seen.options.redirect,'error');assert.equal(seen.options.headers.Authorization,'Bearer test-token');
  }finally{globalThis.fetch=previous;}
});
