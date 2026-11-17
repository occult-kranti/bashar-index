import {readFile} from 'node:fs/promises';
import vm from 'node:vm';
const context=vm.createContext({URL,URLSearchParams,ReadableStream,ByteLengthQueuingStrategy,Uint8Array,ArrayBuffer,DataView,
  TextEncoder,TextDecoder,AbortController,Response,Request,Headers,btoa,atob,performance,setTimeout,clearTimeout,queueMicrotask});
vm.runInContext(await readFile(new URL('../vendor/channeling-native-sabr-v1.iife.js',import.meta.url),'utf8'),context);
export const umpSdk=context.ChannelingNativeSabrV1;
export const sps=status=>new Uint8Array([58,2,8,status]);
export function umpPart(type,payload){
  const varint=n=>n<128?[n]:n<16384?[128|(n&63),n>>>6]:n<2097152?[192|(n&31),(n>>>5)&255,n>>>13]:[224|(n&15),(n>>>4)&255,(n>>>12)&255,n>>>20];
  const header=new Uint8Array([...varint(type),...varint(payload.length)]),result=new Uint8Array(header.length+payload.length);
  result.set(header);result.set(payload,header.length);return result;
}
export const concat=(...parts)=>{const result=new Uint8Array(parts.reduce((n,x)=>n+x.length,0));let offset=0;for(const p of parts){result.set(p,offset);offset+=p.length;}return result;};
