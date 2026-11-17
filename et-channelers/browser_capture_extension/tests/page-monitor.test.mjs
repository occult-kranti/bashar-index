import assert from 'node:assert/strict';
import test from 'node:test';
import {readFile} from 'node:fs/promises';
import vm from 'node:vm';

const ID='abcdefghijk';
async function page(responseId=ID){
  const video={currentTime:0,duration:60,playbackRate:1,paused:false,ended:false,readyState:4,seeking:false,muted:false,volume:1,error:null,mediaKeys:null,pause(){this.paused=true;}};
  const player={getVideoData:()=>({video_id:ID,title:'Current title',author:'Current source',isLive:false}),classList:{contains:()=>false}};
  const marker={querySelector:selector=>selector==='a[href]'?{href:`https://www.youtube.com/watch?v=${ID}&t=15s`}:{textContent:'Chapter one'}};
  const document={querySelector:selector=>selector.includes('video')?video:player,
    querySelectorAll:selector=>selector==='video,audio'?[video]:[marker]};
  const context=vm.createContext({document,location:{href:`https://www.youtube.com/watch?v=${ID}`,origin:'https://www.youtube.com'},
    URL,setTimeout,clearTimeout,setInterval,clearInterval,postMessage(){},
    ytInitialPlayerResponse:{videoDetails:{videoId:responseId,title:'Matching published title',shortDescription:'Public description',author:'Published author',
      defaultAudioLanguage:'en',viewCount:'123',thumbnail:{thumbnails:[{url:'https://i.ytimg.com/vi/abcdefghijk/default.jpg'},
        {url:'https://rr1.googlevideo.com/videoplayback?token=DO_NOT_EXPORT'}]},streamingData:{url:'SECRET_TRANSPORT'},cookies:'PRIVATE_COOKIE'},
      microformat:{playerMicroformatRenderer:{publishDate:'2026-11-16',category:'Education'}}}});
  vm.runInContext(await readFile(new URL('../page-monitor.js',import.meta.url),'utf8'),context);
  return context.__researchAudioPage.prepare({video_id:ID});
}
test('metadata exports only matching public fields and static thumbnails, never transport material',async()=>{
  const result=await page();const text=JSON.stringify(result.source_metadata);
  assert.equal(result.source_metadata.title,'Matching published title');assert.equal(result.source_metadata.language,'en');
  assert.equal(result.source_metadata.chapters[0].start_time,15);
  assert.equal(result.source_metadata.thumbnail_urls.length,1);
  assert(!text.includes('SECRET'));assert(!text.includes('PRIVATE_COOKIE'));assert(!text.includes('DO_NOT_EXPORT'));
  assert.equal(result.state.source_time,0);assert.equal(result.state.paused,true);
});
test('stale initial player response cannot attribute another video metadata to the live source',async()=>{
  const result=await page('ABCDEFGHIJK');
  assert.equal(result.source_metadata.title,'Current title');assert.equal(result.source_metadata.description,'');
  assert.equal(result.source_metadata.language,'');assert.equal(result.source_metadata.thumbnail_urls.length,0);
});
test('stale cleanup nonce cannot stop the replacement page monitor',async()=>{
  const cleared=[];const video={addEventListener(){},removeEventListener(){},currentTime:0,duration:60,readyState:4};
  const player={getVideoData:()=>({video_id:ID}),classList:{contains:()=>false}};
  const context=vm.createContext({document:{querySelector:selector=>selector.includes('video')?video:player,querySelectorAll:()=>[video]},
    location:{href:`https://www.youtube.com/watch?v=${ID}`,origin:'https://www.youtube.com'},URL,postMessage(){},
    setInterval:()=>7,clearInterval:id=>cleared.push(id)});
  context.window=context;
  vm.runInContext(await readFile(new URL('../page-monitor.js',import.meta.url),'utf8'),context);
  context.__researchAudioPage.monitor({nonce:'new',video_id:ID});const before=cleared.length;
  assert.equal(context.__researchAudioPage.stop({nonce:'old'}).skipped,true);assert.equal(cleared.length,before);
  assert.equal(context.__researchAudioPage.stop({nonce:'new'}).stopped,true);assert.equal(cleared.at(-1),7);
});
