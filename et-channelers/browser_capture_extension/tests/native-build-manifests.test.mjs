// Verify the exact files Chrome injects; these offline checks are not source acceptance.
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {dirname,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';

const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const sha=raw=>createHash('sha256').update(raw).digest('hex');

async function verifyFile(base,item,key='path'){
  assert.match(item[key],/^[A-Za-z0-9_.-]+$/,'manifest paths must be local basenames');
  assert.match(item.sha256,/^[a-f0-9]{64}$/);
  assert.ok(Number.isSafeInteger(item.bytes)&&item.bytes>0);
  const raw=await readFile(resolve(base,item[key]));
  assert.equal(raw.length,item.bytes,item[key]+' byte count');
  assert.equal(sha(raw),item.sha256,item[key]+' SHA-256');
}

test('injected native controller and isolated bridge match their exact source manifests',async()=>{
  for(const [name,output,required] of [
    ['native-main.build.json','native-main.iife.js',['native-main.js','native-observer.js','native-finish.js']],
    ['native-isolated-bridge.build.json','native-isolated-bridge.iife.js',['native-isolated-bridge.js','native-rpc.js']]
  ]){
    const manifest=JSON.parse(await readFile(resolve(root,name),'utf8'));
    assert.equal(manifest.schema_version,1);
    assert.deepEqual(manifest.bundler,{name:'esbuild',version:'0.25.12'});
    assert.equal(manifest.network_at_import,false);
    assert.equal(manifest.output.path,output);
    assert.equal(new Set(manifest.inputs.map(x=>x.path)).size,manifest.inputs.length);
    for(const path of required)assert.ok(manifest.inputs.some(x=>x.path===path),path+' missing from manifest');
    for(const item of [...manifest.inputs,manifest.output])await verifyFile(root,item);
  }
});

test('SDK provenance cannot silently omit a required dependency license',async()=>{
  const vendor=resolve(root,'vendor');
  const manifest=JSON.parse(await readFile(resolve(vendor,'bundle-manifest.json'),'utf8'));
  const required=['channeling-native-sabr-v1.iife.js','THIRD_PARTY_NOTICES.txt','LICENSE.googlevideo.MIT.txt',
    'LICENSE.protobuf.Apache-2.0.txt','LICENSE.protobuf.BSD-3-Clause.txt','LICENSE.esbuild.MIT.txt'];
  assert.equal(new Set(manifest.outputs.map(x=>x.name)).size,manifest.outputs.length);
  for(const name of required){
    const item=manifest.outputs.find(x=>x.name===name);
    assert.ok(item,name+' missing from provenance');
    await verifyFile(vendor,item,'name');
  }
});

test('SDK manifest binds every bundled project source, including diagnostic wrappers',async()=>{
  const manifest=JSON.parse(await readFile(resolve(root,'vendor/bundle-manifest.json'),'utf8'));
  assert.equal(new Set(manifest.source_files.map(x=>x.source)).size,manifest.source_files.length);
  const project=manifest.source_files.filter(x=>/^(packaging|project)\//.test(x.source));
  assert.ok(project.some(x=>x.source==='packaging/native-sdk-entry.mjs'));
  assert.ok(project.some(x=>x.source==='project/pipeline/browser_sabr_adapter.mjs'));
  for(const item of project){
    const packaging=item.source.startsWith('packaging/');
    const path=packaging?item.source.slice('packaging/'.length):item.source.slice('project/pipeline/'.length);
    if(!packaging)assert.ok(item.source.startsWith('project/pipeline/'));
    await verifyFile(packaging?root:resolve(root,'../pipeline'),{...item,path});
  }
});
