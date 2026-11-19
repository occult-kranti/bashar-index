"""Canonical mixed-selection inputs only; no live snapshot or generated page."""
from copy import deepcopy
import csv
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from pipeline import dataset_timeline as timeline
from pipeline import ingestion_status as status
from pipeline import collection_coverage, dashboard_local
from pipeline.tests.test_qualified_edition_receipts import receipt_fixture


class MixedDashboardInputTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name);(self.root/'sync').mkdir();(self.root/'jobs').mkdir()
        self.enterContext(patch('socket.socket.connect', side_effect=AssertionError('Source forbidden')))
        self.enterContext(patch('subprocess.Popen', side_effect=AssertionError('process forbidden')))
        self.ids = ['abcdefghijk', 'lmnopqrstuv', 'wxyzABCDEFG', 'ABCDEfghijk', 'zxyABCDEFG1']
        self.tabs = ['videos', 'streams', 'shorts', 'videos', 'shorts']
        self.selection = {'schema_version': 1, 'per_channel': 20, 'channels': [
            {'channel_dir': 'example', 'channel_id': 'UC'+'A'*22, 'scope': 'short_complete_displayed_list', 'selected': 5,
             'items': [{'video_id': video, 'channel_dir': 'example', 'channel_id': 'UC'+'A'*22,
                        'slot': i+1, 'source_position': i, 'title': 'Public '+video, 'tab': self.tabs[i]}
                       for i, video in enumerate(self.ids)]},
            {'channel_dir': 'unobserved', 'channel_id': 'UC'+'B'*22, 'scope': 'unobserved', 'selected': 0, 'items': []}]}
        self.path = self.root/'canonical.json';self.save_selection()

    def save_selection(self):
        self.path.write_text(json.dumps(self.selection), encoding='utf-8')

    def journal(self, name, rows):
        (self.root/'sync'/name).write_text(''.join(json.dumps(r)+'\n' for r in rows), encoding='utf-8')

    def native(self, video, creator='example', folder='Recorded streams'):
        parent = 'etdrive:04 Audio/'+creator+'/'+folder+'/'
        return {'video_id': video, 'channel_dir': creator, 'status': 'deleted', 'path': 'private/'+video+'.webm',
                'remote': parent+video+'.webm', 'bytes': 10, 'md5': 'a'*32, 'sha256': 'b'*64, 'drive_id': 'audio-'+video,
                'metadata': {'bytes': 10, 'md5': 'c'*32, 'sha256': 'd'*64, 'drive_id': 'meta-'+video,
                             'remote': parent+video+'.info.json'}}

    def mirror(self):
        video=self.ids[2];digest='1'*64;parent='etdrive:04 Audio/example/Shorts/'+video+'/PublisherVariants/'+digest
        def obj(name, ident, sha):
            return {'bytes': 20, 'md5': '2'*32, 'sha256': sha, 'drive_id': ident, 'remote': parent+'/'+name}
        return {'schema_version': 1, 'status': 'verified', 'kind': 'publisher_mirror_audio_variant',
                'association_method': 'publisher_rss_exact_youtube_id', 'exact_youtube_crossreference': True,
                'original_youtube_link': 'https://www.youtube.com/watch?v='+video, 'associated_youtube_id': video,
                'channel_dir': 'example', 'source_tab': 'shorts', 'variant_id': digest,
                'native_youtube_bytes': False, 'changes_native_audio_count': False, 'changes_native_asr_count': False,
                'changes_native_caption_count': False, 'human_verified': False,
                'audio': obj('publisher-audio.mp3', 'publisher-audio', digest),
                'provenance': obj('provenance.json', 'publisher-meta', '3'*64)}

    def receipts(self):
        self.journal('drive_ingest_manifest.jsonl', [self.native(self.ids[1]),
            self.native(self.ids[4], 'different-creator', 'Videos'),
            {'video_id': self.ids[3], 'channel_dir': 'example', 'status': 'unavailable', 'error_class': 'unavailable'}])
        self.journal('progressive_audio_extracts_manifest.jsonl', [receipt_fixture(), receipt_fixture()])
        self.journal('publisher_mirror_manifest.jsonl', [self.mirror(), self.mirror()])
        self.journal('publisher_companion_manifest.jsonl', [{'schema_version': 1, 'status': 'verified',
            'artifact_kind': 'related_publisher_episode', 'video_id': self.ids[3], 'changes_selected_audio_count': False}])

    def test_snapshot_uses_chosen_mixed_audio_and_separates_unavailable_and_historical_inventory(self):
        self.receipts()
        data = status.snapshot(self.root, now=1_800_000_000, selection=self.path)
        selected = data['selection'];stage = data['stages'][0]
        self.assertEqual((selected['total'], selected['verified_audio'], selected['unavailable'], selected['remaining_audio']), (5,3,1,2))
        self.assertEqual((stage['total'], stage['verified'], stage['state']), (5,3,'in_progress'))
        self.assertEqual(selected['by_format']['streams']['youtube_native'], 1)
        self.assertEqual(selected['by_format']['videos']['qualified_only'], 1)
        self.assertEqual(selected['by_format']['shorts']['publisher_only'], 1)
        self.assertEqual(data['counts']['selected_native_pairs'], 1)
        self.assertEqual(data['counts']['verified_pairs'], 2)  # Historical inventory remains labeled separately.
        self.assertEqual(selected['creator_count'], 2)
        self.assertEqual(selected['creators'][1]['scope'], 'unobserved')
        self.assertNotIn(str(self.root), json.dumps(data))
        self.assertNotIn(self.ids[0], json.dumps(selected))

    def test_unavailable_only_does_not_mark_current_audio_stage_complete(self):
        self.selection['channels'][0]['items'] = self.selection['channels'][0]['items'][:1]
        self.selection['channels'][0]['selected'] = 1;self.save_selection()
        self.journal('drive_ingest_manifest.jsonl', [{'video_id': self.ids[0], 'channel_dir': 'example',
                     'status': 'unavailable', 'error_class': 'unavailable'}])
        current = status.snapshot(self.root, selection=self.path)
        self.assertEqual(current['selection']['verified_audio'], 0)
        self.assertEqual(current['selection']['unavailable'], 1)
        self.assertEqual(current['stages'][0]['state'], 'in_progress')

    def test_strict_current_creator_blocks_other_creators_publisher_receipt(self):
        self.receipts();self.selection['channels'][0]['channel_dir']='replacement'
        for row in self.selection['channels'][0]['items']:row['channel_dir']='replacement'
        self.save_selection()
        current=status.snapshot(self.root, selection=self.path)
        self.assertEqual(current['selection']['verified_audio'], 0)

    def test_mixed_timeline_cli_dates_csv_formats_and_selection_hash_are_bound(self):
        items=self.selection['channels'][0]['items']
        items[0].update(publication_date='2026-10-01', date_quality='estimated')
        items[1].update(publication_date='2026-11-03', date_quality='exact', exact_date_evidence_sha256='a'*64)
        items[2].update(relative_labels=['1d ago'], date_quality='unknown')
        self.save_selection();original=self.path.read_bytes();out=self.root/'timeline-fixture'
        data=timeline.main(['--selection',str(self.path),'--out-dir',str(out),'--expected-videos','5','--expected-creators','2'])
        self.assertEqual(data['source']['selection_json_sha256'], hashlib.sha256(original).hexdigest())
        self.assertEqual(data['summary']['format_counts'], {'videos':2,'shorts':2,'streams':1,'unknown':0})
        self.assertEqual(data['records'][0]['original_estimate_provenance'], 'canonical_selection_estimated_publication_date')
        self.assertEqual(data['records'][1]['exact_date_provenance']['source_sha256'], 'a'*64)
        self.assertIsNone(data['records'][2]['upload_date'])
        table=list(csv.DictReader(io.StringIO((out/'dataset_timeline_videos.csv').read_text(encoding='utf-8-sig'))))
        self.assertEqual(table[1]['tab'], 'streams')
        self.assertEqual(table[1]['exact_date_source_sha256'], 'a'*64)
        self.assertEqual(data['creators'][1]['record_count'], 0)

    def test_completed_roster_shape_preserves_primary_owner_and_chosen_rank(self):
        rows=[]
        for i,item in enumerate(self.selection['channels'][0]['items']):
            rows.append({**item,'expected_channel_id':item['channel_id'],'selected_position_after_visible_exclusions':i})
        roster={'schema_version':1,'target_limit':20,'row_count':len(rows),'rows':rows,
                'observations':[{'channel_dir':'example','expected_channel_id':'UC'+'A'*22}],
                'creator_coverage':[{'creator':'example','scope':'short_complete_displayed_list'}]}
        self.path.write_text(json.dumps(roster),encoding='utf-8')
        parsed=status.selection_rows(self.path)
        self.assertEqual(len(parsed['rows']),5)
        self.assertEqual(parsed['shape'],'completed_recording_roster_v1')
        roster['rows'][1]['expected_channel_id']='UC'+'B'*22
        with self.assertRaisesRegex(ValueError,'creator identity'):
            status.selection_rows(self.path,content=json.dumps(roster).encode())

    def test_coverage_reuses_validator_for_legacy_unversioned_selection_and_names(self):
        self.selection.pop('schema_version');self.save_selection()
        rows,scopes,digest=collection_coverage.mixed_selection(self.path,{'example':'Creator display name'})
        shared=status.selection_rows(self.path)
        self.assertEqual([r['video_id'] for r in rows],[r['video_id'] for r in shared['rows']])
        self.assertEqual(rows[0]['source_channel_name'],'Creator display name')
        self.assertEqual(scopes['unobserved'],'unobserved')
        self.assertEqual(digest,shared['sha256'])
        self.selection['channels'][0]['items'][1]['source_position']=0;self.save_selection()
        with self.assertRaises(ValueError):collection_coverage.mixed_selection(self.path,{})

    def test_duplicate_video_foreign_owner_and_false_complete_scope_rejected(self):
        for change in ('duplicate','owner','scope'):
            value=deepcopy(self.selection)
            if change=='duplicate':value['channels'][0]['items'][1]['video_id']=self.ids[0]
            elif change=='owner':value['channels'][0]['items'][1]['channel_id']='UC'+'B'*22
            else:value['channels'][0]['scope']='all_requested_positions_observed'
            with self.subTest(change=change),self.assertRaises(ValueError):
                status.selection_rows(self.path,content=json.dumps(value).encode())

    def test_additive_scope_keeps_short_undated_and_old_regular_uploads_and_separates_archived_shorts(self):
        channel_id = 'UC' + 'A' * 22
        def regular(ident, rank):
            member = {'kind':'fresh_public_regular','expected_channel_id':channel_id,'listing_rank':rank,
                      'access_status':'public_listing','title':'A public recording','tab':'videos'}
            return {'channel_dir':'example','video_id':ident,'current_primary_channel_id':channel_id,'tab':'videos',
                    'fresh_regular':True,'fresh_public_regular':True,'public_media_dispatch_excluded':False,
                    'memberships':[member],'duration_s':9 if rank else None}
        older, undated = [regular(self.ids[i], i) for i in (0,1)]
        older.update(publication_date='2011-06-20',publication_date_quality='date',
            publication_date_basis='cached_video_availability_timestamp',publication_date_evidence={
            'overlay':{'sha256':'a'*64},'row_video_id':self.ids[0],'row_channel_dir':'example'})
        rows = [older,undated,{'channel_dir':'example','video_id':self.ids[2],'tab':'shorts'}]
        value = {'schema_version':1,'selection_kind':'additive_latest20plus_videos_v1','latest_regular_per_creator':20,
                 'row_count':len(rows),'rows':rows,'channels':[{'channel_dir':'example','channel_id':channel_id,
                 'public_regular_count':2,'public_listing_complete':True}]}
        original = status.selection_rows(self.path, content=json.dumps(value).encode())
        self.assertEqual(original['basis'], 'latest20plus_public_regular')
        self.assertEqual(original['archive']['formats'], {'videos':2,'shorts':1})
        self.assertEqual([r['video_id'] for r in original['rows']], self.ids[:2])
        self.assertEqual(original['rows'][0]['selected_publication_date'], '2011-06-20')
        self.assertEqual(original['rows'][0]['selected_date_source_sha256'], 'a'*64)
        older['publication_date_evidence']['row_video_id'] = self.ids[2]
        revised = status.selection_rows(self.path, content=json.dumps(value).encode())
        self.assertNotEqual(original['sha256'], revised['sha256'])
        self.assertEqual(original['priority_scope_sha256'], revised['priority_scope_sha256'])
        self.assertEqual(revised['rows'][0]['selected_date_quality'], 'unknown')
        rows[1]['public_media_dispatch_excluded'] = True
        with self.assertRaisesRegex(ValueError, 'Public regular membership'):
            status.selection_rows(self.path, content=json.dumps(value).encode())


class MixedEtaRendererTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('node'), 'Node is needed for the dashboard renderer fixture')
    def test_hero_labels_selected_audio_and_all_time_native_inventory_separately(self):
        prefix = '  async function collectionStatus() {'
        status_renderer = prefix + dashboard_local.HEAD.split(prefix, 1)[1].split('  async function collectionEta(', 1)[0]
        snapshot = {
            'schema_version': 1, 'scope': 'local_youtube_collection', 'generated_at': '2026-11-19T00:00:00Z',
            'operation': {'state': 'ready'}, 'counts': {'verified_pairs': 1108, 'audio_archived_videos': 1108},
            'storage': {'used_bytes': 0, 'ceiling_bytes': 18_000_000_000}, 'stages': [],
            'selection': {'basis': 'canonical_mixed_latest20', 'total': 1458, 'verified_audio': 811},
        }
        script = """
const values = {};
const BASE = 'fixture/';
const document = {getElementById: () => null};
const put = (id, value) => { values[id] = value; };
const date = String, number = String;
const fetch = async () => ({ok: true, json: async () => snapshot});
"""
        script += 'const snapshot = ' + json.dumps(snapshot) + ';\n' + status_renderer
        script += '\ncollectionStatus().then(result => console.log(JSON.stringify({loaded: !!result, values})));'
        result = json.loads(subprocess.run([shutil.which('node'), '-e', script], check=True,
                                           text=True, capture_output=True, timeout=10).stdout)
        self.assertTrue(result['loaded'])
        self.assertEqual(result['values']['cc-verified'], '811')
        self.assertIn('of 1458 selected recordings', result['values']['cc-verified-label'])
        self.assertIn('1108 native YouTube', result['values']['cc-legacy-summary'])
        fragment = Path(dashboard_local.__file__).parents[1] / 'dashboard/collection/page.fragment.html'
        self.assertIn('id="cc-verified-label"', fragment.read_text(encoding='utf-8'))

    @unittest.skipUnless(shutil.which('node'), 'Node is needed for the inert JavaScript renderer fixture')
    def test_actual_eta_renderer_uses_current_counts_without_reusing_historical_rate(self):
        function='  async function collectionEta(statusSnapshot) {'+dashboard_local.HEAD.split(
            '  async function collectionEta(statusSnapshot) {',1)[1].split('  async function collectionCoverage()',1)[0]
        current={'generated_at':'2026-11-01T00:00:00Z','status_snapshot_at':'2026-11-01T00:00:00Z',
            'newest20_items':1420,'measured_service':{'ended_at':'2026-11-01T00:00:00Z',
                'first_pass_decisions':14,'elapsed_seconds':539,'verified_native_pairs':13,'immediate_success_fraction':13/14},
            'next_recovery_batch':{'items':2,'planning_active_hours':[1,2]},
            'untouched_first_pass':{'items':100,'frames':5,'planning_active_hours':[5,10],
                'calendar_hours_at_half_availability':[10,20]},
            'coverage':{'source_audio_available_target_videos':1146,'source_audio_with_text_target_videos':2,
                'verified_pairs':1100,'asr_verified_videos':3}}
        script="const values={};const BASE='fixture/';const put=(k,v)=>values[k]=v;const number=v=>String(v);const date=v=>String(v);\n"
        script+='const fetch=async()=>({ok:true,json:async()=>('+json.dumps({'schema_version':2,'scope':'collection_eta','current':current})+')});\n'
        script+=function+'\n(async()=>{await collectionEta(null);const legacy={...values};await collectionEta('+json.dumps({
            'generated_at':'2026-11-19T00:00:00Z','selection':{'basis':'canonical_mixed_latest20',
                'total':5,'verified_audio':3,'remaining_audio':2,'unavailable':1}})+');console.log(JSON.stringify({legacy,current:values}));})();'
        process=subprocess.run([shutil.which('node'),'-e',script],text=True,capture_output=True,timeout=10)
        self.assertEqual(process.returncode,0,process.stderr)
        value=json.loads(process.stdout)
        self.assertIn('active min',value['legacy']['cc-eta-next-value'])
        self.assertEqual(value['current']['cc-eta-next-value'],'Unknown')
        self.assertEqual(value['current']['cc-eta-first-value'],'Unknown')
        self.assertIn('3 / 5 current',value['current']['cc-eta-coverage'])
        self.assertIn('dated historical',value['current']['cc-eta-evidence'])
        self.assertNotIn('1146',json.dumps(value['current']))

    @unittest.skipUnless(shutil.which('node'), 'Node is needed for the dashboard renderer fixture')
    def test_mixed_rate_needs_the_same_selection_and_completion_count(self):
        prefix = '  async function collectionEta(statusSnapshot) {'
        function = prefix + dashboard_local.HEAD.split(prefix, 1)[1].split('  async function collectionCoverage()', 1)[0]
        pace = {'selection_sha256': '1' * 64, 'total': 20, 'saved': 8, 'remaining': 12, 'new_verified': 4,
                'verified_per_wall_hour': 6.0, 'conditional_hours_at_observed_rate': 2.0}
        initial = {'generated_at': '2026-11-19T11:00:00Z', 'selection': {'sha256': '1' * 64, 'total': 20,
                   'verified_audio': 8, 'remaining_audio': 12, 'basis': 'canonical_mixed_latest20'}}
        data = {'schema_version': 2, 'scope': 'collection_eta', 'current': {'mixed_receipt_pace': pace}}
        script = ("const values={}; const BASE=''; const date=String, number=String; const put=(k,v)=>values[k]=v;\n"
                  + 'const fetch=async()=>({ok:true,json:async()=>(' + json.dumps(data) + ')});\n'
                  + function + '\n(async()=>{const s=' + json.dumps(initial) + '; await collectionEta(s);'
                  + 'const active={...values};s.selection.sha256="different";await collectionEta(s);const stale={...values};'
                  + 's.selection.verified_audio=20;s.selection.remaining_audio=0;await collectionEta(s);'
                  + 'console.log(JSON.stringify({active,stale,done:values}));})();')
        results = json.loads(subprocess.run([shutil.which('node'), '-e', script], check=True, capture_output=True,
                                            text=True, timeout=10).stdout)
        self.assertEqual(results['active']['cc-eta-next-value'], '6.0')
        self.assertEqual(results['active']['cc-eta-first-value'], '2.0 h')
        self.assertEqual(results['stale']['cc-eta-first-value'], 'Unknown')
        self.assertEqual(results['done']['cc-eta-first-value'], 'Complete')


class MixedIsolatedCliTests(unittest.TestCase):
    def test_isolated_status_and_timeline_use_the_same_selection_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);private=root/'private';(private/'sync').mkdir(parents=True);(private/'jobs').mkdir()
            selection={'schema_version':1,'per_channel':20,'channels':[{'channel_dir':'creator','channel_id':'UC'+'A'*22,
                'scope':'short_complete_displayed_list','selected':1,'items':[{'video_id':'abcdefghijk','channel_dir':'creator',
                    'channel_id':'UC'+'A'*22,'slot':1,'source_position':5,'tab':'streams','title':'Public title'}]}]}
            path=root/'selection.json';path.write_text(json.dumps(selection),encoding='utf-8')
            output=root/'status.json';outdir=root/'timeline'
            commands=[(status,['--root',str(private),'--selection',str(path),'--out',str(output)]),
                      (timeline,['--selection',str(path),'--out-dir',str(outdir)])]
            for module,arguments in commands:
                process=subprocess.run([sys.executable,'-I','-B',str(Path(module.__file__).resolve()),*arguments],
                    cwd=root,text=True,capture_output=True,timeout=20)
                self.assertEqual(process.returncode,0,process.stderr)
            snapshot=json.loads(output.read_text(encoding='utf-8'))
            dates=json.loads((outdir/'dataset_timeline.json').read_text(encoding='utf-8'))
            self.assertEqual(snapshot['selection']['sha256'],dates['source']['selection_json_sha256'])
            self.assertEqual(snapshot['selection']['by_format']['streams']['total'],1)
            self.assertEqual(snapshot['selection']['verified_audio'],0)
            self.assertEqual(dates['records'][0]['listing_rank'],0)
            self.assertNotIn(str(root),json.dumps(snapshot))


if __name__=='__main__':unittest.main()
