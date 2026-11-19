from collections import Counter
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from pipeline import corpus_group_lexical as lexical


def sha(raw):return hashlib.sha256(raw).hexdigest()


class GroupLexicalTests(unittest.TestCase):
    def setUp(self):
        self.temp=TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.roster=[];self.views={};self.selection='a'*64

    def row(self,video,creator,text=None,*,kind='published',audio=None,family=None):
        selected=None
        if text is not None:
            view={'video_id':video,'channel_dir':creator,'text':text,'source_kind':kind,'language':'en',
                'offset_unit':'unicode_codepoint','text_version_id':sha((text+kind).encode()),
                'bundle_sha256':'b'*64,'raw_sha256':'c'*64,'text_sha256':sha(text.encode()),
                'speech_coverage_verified':False,'segments':[{'source_segment_id':'fixture:0',
                    'char_start':0,'char_end':len(text),'time_start':0.,'time_end':1.}]}
            if audio:view.update(source_audio_sha256=audio,source_edition_id='sha256:'+audio)
            folder=self.root/'analysis/caption_views'/video;folder.mkdir(parents=True)
            path=folder/'view.json';raw=lexical.encoded(view);path.write_bytes(raw);self.views[video]=path
            selected={k:view[k] for k in ('video_id','text_version_id','source_kind','language','bundle_sha256')}
            selected.update(path=path.relative_to(self.root).as_posix(),file_sha256=sha(raw))
        row={'video_id':video,'channel_dir':creator,'tab':'videos','selected_primary':selected,'other_eligible_views':[],
            'recording_family_id':family,'recording_family_evidence_sha256':'f'*64 if family else None}
        self.roster.append(row);return row

    def freeze(self):
        raw=lexical.encoded(self.roster)+b'\n';methods={'fixture':'d'*64};method=sha(lexical.encoded(methods))
        revision=sha(lexical.encoded([self.selection,method,self.roster,False]))
        folder=self.root/'analysis/candidate_runs'/revision;folder.mkdir(parents=True)
        (folder/'view-inventory.json').write_bytes(raw)
        observed=sum(r['selected_primary'] is not None for r in self.roster)
        manifest={'revision':revision,'selection_sha256':self.selection,'methods':methods,'phase':'candidate_retrieval',
            'selected_audio':len(self.roster),'creators':len({r['channel_dir'] for r in self.roster}),
            'eligible_primary_texts':observed,'missing_primary_texts':len(self.roster)-observed,
            'files':{'view-inventory.json':len(raw)}}
        raw=lexical.encoded(manifest);(folder/'manifest.json').write_bytes(raw)
        self.folder=folder;self.manifest_sha=sha(raw)
        return folder,self.manifest_sha

    def review(self,entities):
        evidence=self.root/'reviewed-episode-evidence.txt';evidence.write_bytes(b'Invented episode-specific claim review.\n')
        proof={'path':evidence.relative_to(self.root).as_posix(),'bytes':evidence.stat().st_size,'sha256':sha(evidence.read_bytes())}
        items=[]
        for row in self.roster:
            if row['video_id'] in entities:
                items.append({'video_id':row['video_id'],'channel_dir':row['channel_dir'],
                    'text_version_id':(row['selected_primary'] or {}).get('text_version_id'),
                    'claimed_entity_id':entities[row['video_id']],'review_state':'episode_specific_reviewed',
                    'scope':'whole_recording_claimed_source','evidence':proof})
        value={'schema_version':1,'selection_sha256':self.selection,
            'view_inventory_sha256':sha((self.folder/'view-inventory.json').read_bytes()),'assignments':items}
        path=self.root/'episode-claims.json';raw=lexical.encoded(value);path.write_bytes(raw)
        return path,sha(raw)

    def load(self,review=None):
        kwargs={'assignments':review[0],'assignments_sha256':review[1]} if review else {}
        return lexical.load_inventory(self.root,self.folder,self.manifest_sha,**kwargs)

    def test_frozen_primary_only_missingness_and_repertoire_does_not_attribute_entity(self):
        row=self.row('aaaaaaaaaaa','creator-a','Galaxies and stars.')
        row['atlas_repertoire']=['council-a','council-b']
        self.row('bbbbbbbbbbb','creator-a',None)
        self.row('ccccccccccc','creator-b','Ocean water.',kind='original_asr')
        self.freeze();data=self.load()
        with patch.object(lexical,'cuda_math',side_effect=AssertionError('GPU must stay dormant')):
            result=lexical.assemble(data,backend='cpu_fixture',fixture_only=True)
        self.assertEqual((result['selected_recordings'],result['observed_primary_texts']), (3,2))
        self.assertEqual(len(result['missing_primary_texts']),1)
        self.assertEqual(result['unassigned_claimed_source_video_ids'],['aaaaaaaaaaa','bbbbbbbbbbb','ccccccccccc'])
        self.assertTrue(all(g['kind']=='creator' for g in result['groups']))
        self.assertEqual(result['source_kind_units'],{'published':1,'original_asr':1})
        self.assertFalse(result['speaker_identity_attributed'])

    def test_review_is_episode_specific_view_bound_and_missing_assignment_text_stays_unknown(self):
        self.row('aaaaaaaaaaa','creator-a','Galaxies and stars.')
        self.row('bbbbbbbbbbb','creator-a','Ocean water.')
        self.row('ccccccccccc','creator-b',None);self.freeze()
        review=self.review({'aaaaaaaaaaa':'council-a','ccccccccccc':'council-b'})
        result=lexical.assemble(self.load(review),backend='cpu_fixture',fixture_only=True)
        groups={g['id']:g for g in result['groups']}
        self.assertEqual(groups['claimed_entity:council-a']['observed_recordings'],1)
        self.assertEqual(groups['claimed_entity:council-b']['missing_primary_texts'],1)
        self.assertEqual(result['unassigned_claimed_source_video_ids'],['bbbbbbbbbbb'])
        raw=json.loads(review[0].read_bytes());raw['assignments'][0]['scope']='creator_repertoire'
        review[0].write_bytes(lexical.encoded(raw))
        with self.assertRaisesRegex(ValueError,'episode_specific'):
            self.load((review[0],sha(review[0].read_bytes())))

    def test_shared_audio_text_aliases_and_reviewed_families_do_not_double_vote(self):
        self.row('aaaaaaaaaaa','creator-a','Galaxies and stars.',audio='e'*64,family='work-a')
        self.row('bbbbbbbbbbb','creator-a','Galaxies and stars.',audio='e'*64,family='work-a')
        self.row('ccccccccccc','creator-a','Different stars.',family='work-a')
        self.row('ddddddddddd','creator-a','Ocean water.',family='work-b');self.freeze()
        data=self.load();order,units,groups,_=lexical.groups_for(data)
        self.assertEqual(len(order),3)
        self.assertEqual(sorted(groups[0]['weights'].values()),[.25,.25,.5])
        result=lexical.assemble(data,backend='cpu_fixture',fixture_only=True)
        self.assertEqual(result['collapsed_exact_audio_text_aliases'],1)
        self.assertEqual(result['groups'][0]['observed_recordings'],4)

    def test_fixture_tfidf_matches_existing_formula_and_cpu_real_fallback_is_forbidden(self):
        docs=[Counter(x=2,y=1),Counter(y=1,z=1)]
        groups=[{'weights':{0:1.}},{'weights':{1:1.}}]
        result=lexical.cpu_fixture_math(docs,groups,fixture_only=True)
        idf=math.log(3/2)+1
        expected=1/(math.sqrt(((1+math.log(2))*idf)**2+1)*math.sqrt(idf*idf+1))
        self.assertAlmostEqual(result['cosine'][0][1],expected,places=12)
        self.assertAlmostEqual(result['cosine'][0][0],1.,places=12)
        with self.assertRaisesRegex(ValueError,'fixture_only'):lexical.cpu_fixture_math(docs,groups)

    def test_no_terms_are_unassessed_similarity_not_zero_and_CUDA_budget_preflight_is_lazy(self):
        self.row('aaaaaaaaaaa','creator-a','the and');self.row('bbbbbbbbbbb','creator-b',None);self.freeze()
        result=lexical.assemble(self.load(),backend='cpu_fixture',fixture_only=True)
        self.assertIsNone(result['cosine_overlap'][0]['cosine']);self.assertFalse(result['clusters']['components'])
        with self.assertRaisesRegex(ValueError,'working_budget_deferred'):
            lexical.cuda_math([Counter(star=1)],[{'weights':{0:1.}}],gpu_memory_budget=1)

    def test_threshold_clusters_are_descriptive_and_shared_inputs_are_disclosed(self):
        self.row('aaaaaaaaaaa','creator-a','Galaxies stars oceans.')
        self.row('bbbbbbbbbbb','creator-b','Galaxies stars oceans.');self.freeze()
        review=self.review({'aaaaaaaaaaa':'council-a'})
        result=lexical.assemble(self.load(review),backend='cpu_fixture',fixture_only=True,threshold=.9)
        self.assertIn(['creator:creator-a','creator:creator-b'],result['clusters']['components'])
        shared=[p for p in result['cosine_overlap'] if p['shared_text_units']]
        self.assertEqual(len(shared),1);self.assertTrue(shared[0]['overlap_is_not_independent'])
        self.assertTrue(all(edge['left'].startswith('creator:') for edge in result['clusters']['edges']))

    def test_tampered_view_inventory_and_review_evidence_are_rejected(self):
        self.row('aaaaaaaaaaa','creator-a','Stars.');self.freeze();review=self.review({'aaaaaaaaaaa':'council-a'})
        evidence=self.root/'reviewed-episode-evidence.txt';evidence.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'frozen_artifact_changed'):self.load(review)
        self.views['aaaaaaaaaaa'].write_bytes(b'{}')
        with self.assertRaisesRegex(ValueError,'frozen_artifact_changed'):self.load()
        raw=(self.folder/'view-inventory.json').read_bytes().replace(b'creator-a',b'creator-b')
        (self.folder/'view-inventory.json').write_bytes(raw)
        with self.assertRaisesRegex(ValueError,'revision_changed'):self.load()

    def test_explicit_describe_does_not_open_inputs_or_initialize_CUDA(self):
        with patch.object(lexical,'run',side_effect=AssertionError('real run forbidden')):
            self.assertEqual(lexical.main(['--root',str(self.root),'--generation',str(self.root/'missing'),
                '--manifest-sha256','a'*64,'--describe']),0)

    def test_normal_CLI_calls_real_completed_generation_path(self):
        with patch.object(lexical,'run',return_value=self.root/'output') as run:
            self.assertEqual(lexical.main(['--root',str(self.root),'--generation',str(self.root/'generation'),
                '--manifest-sha256','a'*64]),0)
        self.assertEqual(run.call_args.args,(self.root,self.root/'generation','a'*64))


if __name__=='__main__':unittest.main()
