import assert from 'node:assert/strict';
import test from 'node:test';
import {cleanupWorker} from '../lifecycle.js';

test('late cleanup releases only its old stream and preserves replacement tab worker',async()=>{
  const old={tab_id:5,worker_id:'old',nonce:'old-nonce'},replacement={tab_id:5,worker_id:'new',nonce:'new-nonce'};
  const registry=new Map([[5,old]]),calls=[];let unblock;
  const pending=cleanupWorker(old,registry,{releaseStream:()=>new Promise(resolve=>{calls.push('release-old');unblock=resolve;}),
    stopPage:async()=>calls.push('stop-page'),persist:async()=>calls.push('persist'),badge:async()=>calls.push('badge')});
  registry.set(5,replacement);unblock();assert.equal(await pending,false);
  assert.equal(registry.get(5),replacement);assert.deepEqual(calls,['release-old']);
});
test('replacement during page cleanup is not deleted or relabelled; stop is nonce-scoped',async()=>{
  const old={tab_id:5,worker_id:'old',nonce:'old-nonce'},replacement={tab_id:5,worker_id:'new',nonce:'new-nonce'};
  const registry=new Map([[5,old]]),calls=[];
  await cleanupWorker(old,registry,{releaseStream:async()=>{},stopPage:async nonce=>{assert.equal(nonce,'old-nonce');registry.set(5,replacement);},
    persist:async()=>calls.push('persist'),badge:async()=>calls.push('badge')});
  assert.equal(registry.get(5),replacement);assert.deepEqual(calls,[]);
});
test('tab closure sends both stop and release, freeing the offscreen worker slot',async()=>{
  const messages=[];let removed;
  const old={tab_id:5,worker_id:'old',state:'activating'};
  globalThis.chrome={storage:{session:{get:async()=>({researchWorkers:[old]}),set:async()=>{}}},
    runtime:{sendMessage:async message=>{messages.push(message);return {accepted:true};},onMessage:{addListener(){}}},
    action:{onClicked:{addListener(){}},setBadgeText:async()=>{},setBadgeBackgroundColor:async()=>{},setTitle:async()=>{}},
    tabs:{onRemoved:{addListener:fn=>{removed=fn;}}}};
  await import('../service-worker.js?closed-tab-fixture');removed(5);
  for(let i=0;i<30&&!messages.some(x=>x.type==='release');i++)await new Promise(resolve=>setTimeout(resolve,5));
  assert.deepEqual(messages.filter(x=>['stop','release'].includes(x.type)).map(x=>x.type),['stop','release']);
});
