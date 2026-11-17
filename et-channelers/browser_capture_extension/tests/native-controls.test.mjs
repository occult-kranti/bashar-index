import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readNormalTarget} from '../native-background.js';
let index=0;
const target='EliqxbbQoRw';
const ready={video_id:target,target_matches:true,duration_seconds:1570.961,current_time:100,paused:true,
  ads_detected:false,media_keys_present:false,is_live:false,playability_status:'OK'};
async function fixture(mode={}){
  const listeners=[],events=[];let releasePair;
  const pairGate=new Promise(resolve=>{releasePair=resolve;});
  globalThis.chrome={permissions:{contains:async request=>{assert.deepEqual(request,{origins:['https://www.youtube.com/*']});events.push('permission');return mode.granted!==false;}},
    storage:{session:{get:async()=>({researchWorkers:[],researchNativeStatus:mode.active?{phase:'downloading_native_audio'}:{phase:'held'}}),set:async()=>{}}},
    runtime:{id:'fixture',getURL:path=>'chrome-extension://fixture/'+path,onMessage:{addListener:fn=>listeners.push(fn)},openOptionsPage:async()=>{},reload:()=>events.push('reload')},
    tabs:{query:async query=>{assert.deepEqual(query,{url:'https://www.youtube.com/watch*'});events.push('query');return mode.wrongTarget?[{id:7,url:'https://www.youtube.com/watch?v=AAAAAAAAAAA'}]:[{id:7,url:`https://www.youtube.com/watch?feature=share&v=${target}`}];},sendMessage:async()=>{},onRemoved:{addListener(){}}},
    scripting:{executeScript:async request=>{if(request.func?.name==='readNormalTarget'){events.push('read');return [{result:{...ready,...mode.scalar}}];}
      events.push('inject');return [{result:{started:true}}];}},action:{setBadgeText:async()=>{},setTitle:async()=>{}}};
  globalThis.fetch=async()=>{events.push('pair');if(mode.pairWait)await pairGate;if(mode.pairFail)throw Error('receiver_unavailable');return {ok:true,json:async()=>({token:'A'.repeat(40)})};};
  const module=await import(`../native-background.js?controls=${++index}`);module.installNativeBackground();
  const call=(operation,sender={id:'fixture',url:'chrome-extension://fixture/status.html'})=>new Promise(resolve=>{
    const accepted=listeners[0]({target:'native-controls',operation},sender,resolve);if(!accepted)resolve(undefined);
  });
  return {call,events,releasePair,module};
}
test('normal-context check uses actual permission and read-only scalar inspection, never pair or activation',async()=>{
  const f=await fixture(),result=await f.call('inspect_target');
  assert.equal(result.value.permission_granted,true);assert.equal(result.value.eligible,true);
  assert.deepEqual(f.events,['permission','query','read']);assert.ok(!JSON.stringify(result).includes('https://'));
});
test('denied grant, wrong target, active job and ineligible media never activate',async()=>{
  for(const mode of [{granted:false},{wrongTarget:true},{active:true},{scalar:{ads_detected:true}},
    {scalar:{media_keys_present:true}},{scalar:{target_matches:false}},{scalar:{duration_seconds:null}}]){
    const f=await fixture(mode),result=await f.call('start_target');assert.ok(result.error);
    assert.ok(!f.events.includes('pair'));assert.ok(!f.events.includes('inject'));
  }
});
test('start repeats readiness and successful pairing precedes all native injection; pair failure stops',async()=>{
  const f=await fixture();await f.call('inspect_target');const result=await f.call('start_target');
  assert.equal(result.value.started,true);assert.deepEqual(f.events.slice(0,7),['permission','query','read','permission','query','read','pair']);
  assert.ok(f.events.indexOf('inject')>f.events.indexOf('pair'));
  const failed=await fixture({pairFail:true});assert.equal((await failed.call('start_target')).error,'receiver_unavailable');
  assert.ok(!failed.events.includes('inject'));
});
test('options controls reject content scripts, another extension and non-options pages',async()=>{
  const f=await fixture();
  for(const sender of [{id:'fixture',url:'https://www.youtube.com/watch?v='+target},{id:'other',url:'chrome-extension://fixture/status.html'},
    {id:'fixture',url:'chrome-extension://fixture/offscreen.html'}])assert.equal(await f.call('start_target',sender),undefined);
  assert.deepEqual(f.events,[]);
});
test('MAIN readiness function returns only source scalars and never plays or reads transport material',()=>{
  const video={duration:1570.961,currentTime:100,paused:true,mediaKeys:null,play:()=>{throw Error('must_not_play');}};
  const response={videoDetails:{videoId:target},playabilityStatus:{status:'OK'}};
  Object.defineProperty(response,'streamingData',{get:()=>{throw Error('must_not_read_streams');}});
  const player={querySelector:()=>video,getVideoData:()=>({video_id:target}),getPlayerResponse:()=>response,classList:{contains:()=>false}};
  const result=vm.runInNewContext(`(${readNormalTarget.toString()})('${target}')`,{
    document:{getElementById:()=>player},location:{href:`https://www.youtube.com/watch?v=${target}`},URL,
    fetch:()=>{throw Error('must_not_fetch');}});
  assert.equal(result.target_matches,true);assert.deepEqual(JSON.parse(JSON.stringify(result)),ready);
});
test('second options-page reload is denied during pairing; idle reload locks out a new start',async()=>{
  const f=await fixture({pairWait:true}),starting=f.call('start_target');
  for(let i=0;i<10&&!f.events.includes('pair');i++)await new Promise(resolve=>setImmediate(resolve));
  assert.equal((await f.call('activity')).value.active,true);
  assert.equal((await f.call('reload_helper')).error,'native_pilot_already_active');
  assert.ok(!f.events.includes('reload'));f.releasePair();assert.equal((await starting).value.started,true);
  const idle=await fixture();assert.equal((await idle.call('reload_helper')).value.reload,true);
  await new Promise(resolve=>setImmediate(resolve));assert.ok(idle.events.includes('reload'));
  assert.equal((await idle.call('start_target')).error,'native_pilot_already_active');assert.ok(!idle.events.includes('pair'));
});
test('direct toolbar pairing also protects against an options-page reload',async()=>{
  const f=await fixture({pairWait:true}),starting=f.module.startNativeInTab({id:7,url:`https://www.youtube.com/watch?v=${target}`});
  await new Promise(resolve=>setImmediate(resolve));assert.equal((await f.call('reload_helper')).error,'native_pilot_already_active');
  f.releasePair();await starting;assert.ok(!f.events.includes('reload'));
});
