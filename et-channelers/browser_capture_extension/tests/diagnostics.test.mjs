import assert from 'node:assert/strict';
import test from 'node:test';
import {outcome,diagnostic,retainDiagnostic} from '../diagnostics.js';

test('explicit stop remains stopped when a held completion races cleanup',()=>{
  const result=outcome({stop_reason:'user_stopped'},{error:'capture_held'});
  assert.equal(result.state,'stopped');assert.equal(result.badge,'');assert.equal(result.code,'user_stopped');
  assert.equal(outcome({},{error:'user_stopped'}).badge,'');
  assert.equal(outcome({stop_reason:'tab_closed'},{error:'operation_failed'}).state,'stopped');
});
test('actual failures retain only bounded constant reasons and no transport data',()=>{
  const result=outcome({},{error:'content_clock_gap'});assert.equal(result.badge,'ERR');
  const record=diagnostic({worker_id:'w',tab_id:4,job:{video_id:'abcdefghijk',capture_id:'c',watch_url:'private'},token:'secret'},result);
  assert.equal(record.code,'content_clock_gap');assert(!JSON.stringify(record).includes('private'));assert(!JSON.stringify(record).includes('secret'));
  assert.equal(outcome({},{error:'https://example.com/token=secret'}).code,'operation_failed');
});
test('history keeps at most sixteen attempts and replaces duplicate worker completions',()=>{
  let history=[];for(let i=0;i<20;i++)history=retainDiagnostic(history,{worker_id:String(i),code:'capture_stopped'});
  assert.equal(history.length,16);assert.equal(history[0].worker_id,'4');
  history=retainDiagnostic(history,{worker_id:'19',code:'user_stopped'});
  assert.equal(history.length,16);assert.equal(history.at(-1).code,'user_stopped');
});
