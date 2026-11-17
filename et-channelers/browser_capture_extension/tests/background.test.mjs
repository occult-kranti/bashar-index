import assert from 'node:assert/strict';
import test from 'node:test';

async function harness(name,initial=[],mode='capture_legacy'){
  let clicked,receive;const badges=[],requests=[],stored={researchWorkers:initial,researchPairToken:'old-service-token-value',researchMode:mode};let optionsOpened=0;
  globalThis.chrome={storage:{session:{get:async keys=>typeof keys==='string'?{[keys]:stored[keys]}:stored,set:async value=>Object.assign(stored,value)}},
    runtime:{id:'fixture',getURL:path=>`chrome-extension://fixture/${path}`,openOptionsPage:async()=>{optionsOpened++;},onMessage:{addListener:fn=>{receive=fn;}},sendMessage:async value=>{
      if(value.type==='stop')await new Promise(resolve=>receive({target:'background',type:'job_done',worker_id:value.worker_id,capture_id:'capture',state:'held',error:value.reason},{id:'fixture',url:'chrome-extension://fixture/offscreen.html'},resolve));
      return {ready:true,accepted:true};}},
    action:{onClicked:{addListener:fn=>{clicked=fn;}},setBadgeText:async value=>badges.push(value.text),setBadgeBackgroundColor:async()=>{},setTitle:async()=>{}},
    tabs:{onRemoved:{addListener(){}},get:async()=>({url:'https://www.youtube.com/watch?v=abcdefghijk'})},
    offscreen:{hasDocument:async()=>true},tabCapture:{getMediaStreamId:async()=>'memory-only'}};
  globalThis.fetch=async(url,options)=>{const path=new URL(url).pathname.split('/').at(-1);requests.push({path,options});return {ok:true,json:async()=>path==='pair'?{token:'new-service-token-value-12345'}:path==='next'?{job:null}:{accepted:true}};};
  await import(`../service-worker.js?background=${name}`);
  return {click:()=>clicked({id:5,url:'https://www.youtube.com/watch?v=abcdefghijk'}),stored,badges,requests,optionsOpened:()=>optionsOpened};
}
async function settle(until){for(let i=0;i<100;i++){if(until())return;await new Promise(resolve=>setTimeout(resolve,5));}throw Error('fixture_timeout');}

test('explicit toolbar stop racing held callback clears badge and persists user stop reason',async()=>{
  const h=await harness('stop-race',[{tab_id:5,worker_id:'old',state:'recording',job:{capture_id:'capture',video_id:'abcdefghijk'}}]);
  h.click();await settle(()=>h.stored.researchWorkers.length===0&&h.badges.length>0);
  assert(!h.badges.includes('ERR'));assert.equal(h.stored.researchDiagnostics.at(-1).code,'user_stopped');
  await settle(()=>h.requests.some(x=>x.path==='abort'));
  assert.equal(JSON.parse(h.requests.find(x=>x.path==='abort').options.body).reason,'user_stopped');
});
test('new explicit activation refreshes stale token before leasing and never retries mutations',async()=>{
  const h=await harness('re-pair');h.click();await settle(()=>h.badges.includes('DONE'));
  assert.deepEqual(h.requests.map(x=>x.path),['health','pair','next']);
  assert.equal(h.requests.at(-1).options.headers.Authorization,'Bearer new-service-token-value-12345');
});
test('default toolbar activation inspects MAIN world only, without local service, capture stream or media request',async()=>{
  const h=await harness('native-inspection',[],undefined);delete h.stored.researchMode;
  chrome.scripting={executeScript:async request=>{assert.equal(request.world,'MAIN');assert.deepEqual(request.args,['inspect','abcdefghijk']);return [{result:{schema_version:1,video_id:'abcdefghijk',formats:[],has_sabr:true}}];}};
  chrome.tabCapture.getMediaStreamId=async()=>{throw Error('recording_must_not_start');};
  h.click();await settle(()=>h.optionsOpened()===1);
  assert.deepEqual(h.requests,[]);assert.deepEqual(h.badges,['LOOK','INFO']);assert.equal(h.stored.researchWorkers.length,0);assert.equal(h.stored.researchInspections[0].has_sabr,true);
});
