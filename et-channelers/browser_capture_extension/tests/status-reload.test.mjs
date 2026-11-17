import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import vm from 'node:vm';
import {createSabrDiagnostics,validateSabrDiagnostics} from '../native-sabr-diagnostics.js';
async function fixture({workers=[],native={phase:'held'},error=false}={}){
  const elements=new Map(),messages=[];let reloads=0;
  const element=()=>({textContent:'',disabled:false,listeners:{},addEventListener(k,fn){this.listeners[k]=fn;},replaceChildren(){},append(){}});
  const get=id=>{if(!elements.has(id))elements.set(id,element());return elements.get(id);};
  const state={workers,inspections:[],diagnostics:[]};
  const context={document:{querySelector:get,createElement:element},setInterval:()=>{},navigator:{},validateSabrDiagnostics,
    chrome:{runtime:{getManifest:()=>({version:'0.3.0',host_permissions:['https://www.youtube.com/*']}),
      sendMessage:async value=>{messages.push(value);if(error)throw Error('offline');
        if(value.target==='background'){assert.equal(value.type,'status');return state;}
        assert.equal(value.target,'native-controls');
        if(value.operation==='activity')return {value:{active:false}};
        assert.equal(value.operation,'reload_helper');reloads++;return {value:{reload:true}};},
      reload:()=>{reloads++;}},storage:{session:{get:async()=>({researchNativeStatus:native})}}},
    fetch:()=>{throw Error('reload_must_not_fetch');}};
  const script=(await readFile(new URL('../status.js',import.meta.url),'utf8')).replace("import {validateSabrDiagnostics} from './native-sabr-diagnostics.js';",'');
  vm.runInNewContext(script,context);
  await new Promise(resolve=>setImmediate(resolve));
  return {get,state,messages,click:()=>get('#reload-helper').listeners.click(),reloads:()=>reloads};
}
test('owned status Reload helper reloads idle extension once without activation or network',async()=>{
  const f=await fixture();assert.equal(f.get('#reload-helper').disabled,false);
  assert.match(f.get('#helper-version').textContent,/0\.3\.0.*permission declaration present/);
  await f.click();await f.click();assert.equal(f.reloads(),1);assert.equal(f.messages.length,4);
});
test('reload rechecks active work and fails closed when status is unavailable',async()=>{
  for(const mode of [{workers:[{}]},{native:{phase:'downloading_native_audio'}},{error:true}]){
    const f=await fixture(mode);assert.equal(f.get('#reload-helper').disabled,true);await f.click();assert.equal(f.reloads(),0);
  }
  const changed=await fixture();changed.state.workers.push({});await changed.click();assert.equal(changed.reloads(),0);
});
test('protocol display exports only bounded validated diagnostics and safe outcome binding',async()=>{
  const diag=createSabrDiagnostics({itag:140,lastModified:'1',xtags:'x'});diag.record('protection',{status:2,maxRetries:0});
  const native={phase:'held',bytes:1133713,source_binding_sha256:'a'.repeat(64),error:'sdk_stalled',diagnostics:diag.snapshot(),
    privateURL:'https://private/token',poToken:'SECRET'};
  const good=await fixture({native}),text=good.get('#native-protocol-diagnostics').textContent,report=JSON.parse(text);
  assert.equal(report.diagnostics.latest.protection.status,2);assert.equal(report.bytes,1133713);
  assert.equal(report.source_binding_sha256,'a'.repeat(64));assert.ok(!/private|SECRET|token/.test(text));
  const bad=await fixture({native:{...native,diagnostics:{...native.diagnostics,poToken:'SECRET'}}});
  assert.equal(bad.get('#native-protocol-diagnostics').textContent,'Protocol diagnostics withheld: invalid bounded report.');
});
