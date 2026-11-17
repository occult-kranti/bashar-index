// Build from an explicitly supplied private dependency installation. This
// script installs nothing, fetches nothing and embeds no local source paths.
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {resolve,relative,dirname,isAbsolute} from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
const here=dirname(fileURLToPath(import.meta.url));
const options=new Map();
for(let i=2;i<process.argv.length;i+=2){
  if(!['--sdk-node-modules','--esbuild-module'].includes(process.argv[i])||!process.argv[i+1])throw Error('build_option');
  options.set(process.argv[i],resolve(process.argv[i+1]));
}
const dependencies=options.get('--sdk-node-modules');
if(!dependencies)throw Error('sdk_node_modules_required');
const esbuildModule=options.get('--esbuild-module')||resolve(dependencies,'esbuild/lib/main.js');
const esbuild=await import(pathToFileURL(esbuildModule));
if(esbuild.version!=='0.25.12')throw Error('bundler_version_mismatch');
const bundlerIntegrity='sha512-bbPBYYrtZbkt6Os6FiTLCTFxvq4tt3JKall1vRwshA3fdVztsLAatFaZobhkBC8/BrPetoa0oksYoKXoG4ryJg==';
const bundlerLock=JSON.parse(await readFile(resolve(dirname(esbuildModule),'../../../package-lock.json'),'utf8'));
if(bundlerLock.packages['node_modules/esbuild']?.integrity!==bundlerIntegrity)throw Error('bundler_integrity_pin_mismatch');
const pins=[
  {name:'googlevideo',version:'5.0.1',registry_tarball:'https://registry.npmjs.org/googlevideo/-/googlevideo-5.0.1.tgz',
   registry_integrity:'sha512-jbQtretPuwNXUJzjUUaIap6z8cFGMu1tnUi02bhCgcENPoAUQvi4KRRVKFvseZSiDVJ0ocU7gCY2cAfWrwDS9g==',license:'MIT'},
  {name:'@bufbuild/protobuf',version:'2.17.0',registry_tarball:'https://registry.npmjs.org/@bufbuild/protobuf/-/protobuf-2.17.0.tgz',
   registry_integrity:'sha512-hcPkSz6D7MiTU/5VBBhK+kxaYDoOdQ6yJRFJ3kS8Nydp+VZXfg1vrpABKPNod8bXMufsVCmiUJVIKFzCzta4uw==',license:'(Apache-2.0 AND BSD-3-Clause)'}];
const lock=JSON.parse(await readFile(resolve(dependencies,'../package-lock.json'),'utf8'));
for(const pin of pins){
  const installed=JSON.parse(await readFile(resolve(dependencies,pin.name,'package.json'),'utf8'));
  const recorded=lock.packages['node_modules/'+pin.name];
  if(installed.version!==pin.version||recorded?.integrity!==pin.registry_integrity||recorded?.resolved!==pin.registry_tarball)
    throw Error('sdk_dependency_pin_mismatch');
}
const output=resolve(here,'vendor'),adapter=resolve(here,'../pipeline/browser_sabr_adapter.mjs');
await mkdir(output,{recursive:true});
const result=await esbuild.build({absWorkingDir:here,entryPoints:[resolve(here,'native-sdk-entry.mjs')],
  outfile:resolve(output,'channeling-native-sabr-v1.iife.js'),bundle:true,platform:'browser',format:'iife',target:['chrome120'],
  nodePaths:[dependencies],alias:{'native-sabr-project-adapter':adapter},minifyWhitespace:true,minifySyntax:true,
  minifyIdentifiers:false,legalComments:'external',metafile:true,sourcemap:false,charset:'utf8',logLevel:'silent',
  banner:{js:'/*! googlevideo 5.0.1 (MIT), protobuf 2.17.0 (Apache-2.0 AND BSD-3-Clause). See THIRD_PARTY_NOTICES.txt. */'}});
const hash=raw=>createHash('sha256').update(raw).digest('hex');
const sources=[];
for(const name of Object.keys(result.metafile.inputs)){
  const full=resolve(here,name),raw=await readFile(full),packageRelative=relative(dependencies,full);
  const key=full===adapter?'project/pipeline/browser_sabr_adapter.mjs':
    !packageRelative.startsWith('..')&&!isAbsolute(packageRelative)?'dependencies/'+packageRelative.replaceAll('\\','/'):
    'packaging/'+relative(here,full).replaceAll('\\','/');
  if(key.includes('/../'))throw Error('unexpected_build_input');
  sources.push({source:key,bytes:raw.length,sha256:hash(raw)});
}
sources.sort((a,b)=>a.source.localeCompare(b.source));
const names=['channeling-native-sabr-v1.iife.js','THIRD_PARTY_NOTICES.txt','LICENSE.googlevideo.MIT.txt',
  'LICENSE.protobuf.Apache-2.0.txt','LICENSE.protobuf.BSD-3-Clause.txt','LICENSE.esbuild.MIT.txt'];
const outputs=[];
for(const name of names){const raw=await readFile(resolve(output,name));outputs.push({name,bytes:raw.length,sha256:hash(raw)});}
const manifest={schema_version:1,namespace:'ChannelingNativeSabrV1',created_at:new Date().toISOString(),
  network_behavior:'Loading the bundle starts no requests; accepted-context producer must be explicitly invoked.',
  logger_policy:'Bundled Logger.prototype.log is disabled; signed transport diagnostics cannot be enabled through the exposed logger.',
  dependencies:pins,bundler:{name:'esbuild',version:'0.25.12',registry_integrity:bundlerIntegrity},
  build_options:{format:'iife',platform:'browser',target:'chrome120',sourcemap:false,
    minifyWhitespace:true,minifySyntax:true,minifyIdentifiers:false,legalComments:'external'},
  adapter_sha256:hash(await readFile(adapter)),source_files:sources,outputs};
await writeFile(resolve(output,'bundle-manifest.json'),JSON.stringify(manifest,null,2)+'\n');
console.log(JSON.stringify({bundle_bytes:outputs[0].bytes,bundle_sha256:outputs[0].sha256,source_files:sources.length}));
