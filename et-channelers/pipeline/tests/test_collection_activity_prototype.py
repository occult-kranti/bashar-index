"""Bound prototype scope must reach the creator table and its activity export."""
import csv
from copy import deepcopy
import datetime as dt
import io
import json
from pathlib import Path
import shutil
import subprocess
import unittest
from unittest.mock import patch

from pipeline import collection_coverage as coverage, dashboard_local
from pipeline.tests import test_native_bulk_status as fixtures


class BoundPrototypeActivityTests(unittest.TestCase):
    def setUp(self):
        self.fixture=fixtures.BulkStatusTests(methodName='runTest')
        self.fixture.setUp();self.addCleanup(self.fixture.doCleanups)
        self.f=self.fixture;self.root=self.f.root
        self.namespace='stock_wpc_batch_v5_bulk_recovery6_prototype'
        self.bind(self.namespace,'stock_headful_wpc_native_batch_v5_bulk_recovery6_prototype')
        self.ids=['v'+str(i).zfill(10) for i in range(6)]
        self.rows=[{'video_id':ident,'channel_dir':'creator','source_channel_name':'Creator'} for ident in self.ids]
        members=self.ids[:5]
        manifest=self.f.put('manifest.json',{'allowed_video_ids':members})
        mapping=self.f.put('map.json',{'frames':[{'frame_index':0,'plan_sha256':'9'*64,'video_ids':members}]})
        settings=self.f.put('settings.json',{'root_admission_path':str(self.f.grant_path),'owner':'root',
            'lease_id':'bulk-test','cohort_manifest':manifest,'frame_map':mapping})
        changes={'allowed_video_ids':members,'controller_settings_sha256':settings['sha256'],
            'cohort_manifest_sha256':manifest['sha256'],'frame_map_sha256':mapping['sha256']}
        self.f.grant.update(changes);self.f.write(self.f.grant_path,self.f.grant)
        self.f.lease.update(changes,root_admission_sha256=self.f.pin(self.f.grant_path)['sha256'])
        self.f.write(self.root/'sync'/(self.namespace+'_lease.json'),self.f.lease)
        self.f.put('root-review-packet.json',{'controller_settings':settings,'private_code':self.f.codes})
        bindings={k:self.f.grant[k] for k in ['controller_settings_sha256','cohort_manifest_sha256','frame_map_sha256']}
        bindings['root_grant_sha256']=self.f.lease['root_admission_sha256']
        self.f.invoked.update(bindings);self.f.state.update(bindings)
        self.f.write(self.f.live/'source-invocation.json',self.f.invoked);self.f.save_state()
        for index,phase in [(1,'native_transfer'),(2,'bootstrap')]:
            folder=self.folder(self.ids[index])
            self.f.write(folder/'child-owner.json',{'owned_child':{'pid':100+index,'process_creation_filetime':'123'}})
            self.f.write(folder/'progress.json',{'phase':phase})
        self.f.write(self.folder(self.ids[3])/'result.json',{'status':'local_complete'})
        self.enterContext(patch('socket.socket.connect',side_effect=AssertionError('network forbidden')))

    def bind(self,namespace,profile):
        self.f.rebind_namespace(namespace,profile);self.namespace=namespace

    def folder(self,ident):
        path=self.root/self.namespace/'jobs'/('9'*16)/ident;path.mkdir(parents=True)
        self.f.write(path/'attempt.json',{'video_id':ident,'plan_sha256':'9'*64})
        return path

    def activity(self,command_alive=True):
        with patch.object(coverage.status,'owned_native_batch_command',return_value=command_alive), \
                patch.object(coverage.status,'owned_process_alive',side_effect=lambda identity:identity.get('pid') in {101,102}), \
                patch('subprocess.Popen',side_effect=AssertionError('Source process forbidden')):
            return coverage.channel_activity(self.root,self.rows,{self.ids[0]},dt.datetime.fromtimestamp(1000,dt.timezone.utc))

    def test_real_bound_prototype_partitions_saved_live_ready_and_queued(self):
        data=self.activity()
        self.assertEqual(('running',5),(data['state'],data['cohort_items']))
        self.assertEqual({key:1 for key in coverage.ACTIVITY_FIELDS},data['summary'])
        self.assertEqual(6,sum(data['summary'].values()))
        self.assertNotIn(str(self.root),json.dumps(data))
        self.assertNotIn('process_creation_filetime',json.dumps(data))
        for ident in self.ids:self.assertNotIn(ident,json.dumps(data))

    def test_unowned_or_unrelated_prototype_cannot_claim_queued_or_active(self):
        self.assertEqual(0,self.activity(False)['cohort_items'])
        self.bind('stock_wpc_batch_v5_bulk_recovery7_prototype',
                  'stock_headful_wpc_native_batch_v5_bulk_recovery7_prototype')
        data=self.activity()
        self.assertEqual(0,data['cohort_items']);self.assertEqual(0,data['summary']['queued'])
        self.assertEqual(5,data['summary']['other_pending'])

    @unittest.skipUnless(shutil.which('node'),'Node is required to exercise the actual dashboard renderer')
    def test_actual_dashboard_active_filter_aria_and_csv_keep_bound_activity(self):
        activity=self.activity()
        public={'schema_version':1,'scope':'newest20_receipt_coverage','generated_at':activity['generated_at'],
            'activity':activity,'channels':[{'channel':'Creator','channel_dir':'creator','target':6,
                'youtube_audio':1,'publisher_only_audio':0,'audio_total':1,'with_saved_text':0,'remaining_audio':5}],
            'summary':{'audio_available':1,'latest20_target':6,'youtube_native_audio':1,
                       'publisher_only_audio':0,'audio_with_saved_text':0}}
        html=dashboard_local.build('', './plan/')
        start=html.index('  async function collectionCoverage()')
        finish=html.index('  const loadCollection',start)
        payload={'source':html[start:finish],'data':public}
        program=r'''
const vm=require('node:vm');const fs=require('node:fs');const input=JSON.parse(fs.readFileSync(0,'utf8'));
class Element {constructor(){this.children=[];this.textContent='';this.value='';this.attrs={};this.handlers={};}
 append(value){this.children.push(value);} replaceChildren(){this.children=[];} setAttribute(k,v){this.attrs[k]=v;}
 addEventListener(k,v){this.handlers[k]=v;}}
const elements=new Map();const get=id=>{if(!elements.has(id))elements.set(id,new Element());return elements.get(id);};
get('cc-coverage-filter').value='all';let csv;
const context={BASE:'./plan/',document:{getElementById:get,querySelectorAll:()=>[],createElement:()=>new Element()},
 fetch:async()=>({ok:true,json:async()=>input.data}),number:value=>String(value),date:value=>value,
 put:(id,value)=>{get(id).textContent=String(value);},Blob,URL:{createObjectURL:value=>{csv=value;return 'blob:fixture';},revokeObjectURL:()=>{}},
 window:{addEventListener:()=>{}}};
vm.createContext(context);vm.runInContext(input.source+'\nglobalThis.run=collectionCoverage;',context);
(async()=>{await context.run();const row=get('cc-coverage-body').children[0];
 const first={cells:row.children.map(x=>x.textContent),aria:row.children[2].attrs['aria-label']};
 get('cc-coverage-filter').value='active';get('cc-coverage-filter').handlers.change();
 process.stdout.write(JSON.stringify({first,activeRows:get('cc-coverage-body').children.length,
 message:get('cc-coverage-activity').textContent,summary:get('cc-coverage-summary').textContent,csv:await csv.text()}));})().catch(e=>{console.error(e);process.exit(1);});
'''
        for qualified in (0,1):
            with self.subTest(qualified_youtube_edition=qualified):
                current=deepcopy(payload)
                if qualified:
                    current['data']['channels'][0].update(qualified_youtube_only_audio=1,audio_total=2,remaining_audio=4)
                    current['data']['summary'].update(qualified_youtube_only_audio=1,audio_available=2)
                    current['data']['activity']['channels'][0].update(saved=2,other_pending=0)
                result=subprocess.run([shutil.which('node'),'-e',program],input=json.dumps(current),
                    capture_output=True,text=True,timeout=15)
                self.assertEqual(0,result.returncode,result.stderr)
                rendered=json.loads(result.stdout)
                self.assertEqual(['Creator',str(1+qualified)+' / 6','3','1'],rendered['first']['cells'][:4])
                self.assertEqual(str(qualified),rendered['first']['cells'][6])
                self.assertEqual(9,len(rendered['first']['cells']))
                self.assertEqual(1,rendered['activeRows'])
                self.assertIn('1 downloading, 1 preparing or validating, 1 awaiting upload',rendered['first']['aria'])
                self.assertIn('1 are queued in the running batch',rendered['message'])
                self.assertEqual(bool(qualified),'unverified track and language' in rendered['summary'])
                rows=list(csv.reader(io.StringIO(rendered['csv'].lstrip('\ufeff'))))
                self.assertEqual(['Creator','6',str(1+qualified),'1','1','1','1',str(1-qualified)],rows[1])


if __name__=='__main__':unittest.main()
