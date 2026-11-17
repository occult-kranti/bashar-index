import {readFile,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {dirname,resolve,relative} from 'node:path';
const here=dirname(fileURLToPath(import.meta.url));
const option=process.argv.indexOf('--esbuild-module');
const modulePath=option>=0?pathToFileURL(resolve(process.argv[option+1])).href:'esbuild';
const {build,version}=await import(modulePath);
if(version!=='0.25.12')throw Error('bundler_version_mismatch');
const result=await build({absWorkingDir:here,entryPoints:['native-main.js'],outfile:'native-main.iife.js',bundle:true,
  format:'iife',platform:'browser',target:['chrome120'],minify:false,sourcemap:false,metafile:true,logLevel:'silent'});
const hash=raw=>createHash('sha256').update(raw).digest('hex');
const inputs=[];
for(const name of Object.keys(result.metafile.inputs)){const raw=await readFile(resolve(here,name));inputs.push({path:relative(here,resolve(here,name)).replaceAll('\\','/'),bytes:raw.length,sha256:hash(raw)});}
const output=await readFile(resolve(here,'native-main.iife.js'));
await writeFile(resolve(here,'native-main.build.json'),JSON.stringify({schema_version:1,bundler:{name:'esbuild',version},
  inputs,output:{path:'native-main.iife.js',bytes:output.length,sha256:hash(output)},network_at_import:false},null,2)+'\n');
console.log(JSON.stringify({bytes:output.length,sha256:hash(output)}));
const bridge=await build({absWorkingDir:here,entryPoints:['native-isolated-bridge.js'],outfile:'native-isolated-bridge.iife.js',bundle:true,
  format:'iife',platform:'browser',target:['chrome120'],minify:false,sourcemap:false,metafile:true,logLevel:'silent'});
const bridgeInputs=[];for(const name of Object.keys(bridge.metafile.inputs)){const raw=await readFile(resolve(here,name));bridgeInputs.push({path:relative(here,resolve(here,name)).replaceAll('\\','/'),bytes:raw.length,sha256:hash(raw)});}
const bridgeOutput=await readFile(resolve(here,'native-isolated-bridge.iife.js'));
await writeFile(resolve(here,'native-isolated-bridge.build.json'),JSON.stringify({schema_version:1,bundler:{name:'esbuild',version},inputs:bridgeInputs,
  output:{path:'native-isolated-bridge.iife.js',bytes:bridgeOutput.length,sha256:hash(bridgeOutput)},network_at_import:false},null,2)+'\n');
