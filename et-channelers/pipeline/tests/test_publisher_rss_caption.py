"""Validate RSS episode, language evidence and publisher-timebase caption bundles offline."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile

from pipeline import corpus_publisher_variant_view as reader, ingestion_status, publisher_caption_batch as batch
from pipeline import publisher_mirror, youtube_captions
from pipeline.tests.test_corpus_publisher_variant_view import CREATOR, OWNER, REMOTE, VIDEO, digest


class DeclaredRssCaptions(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        (self.root/'sync').mkdir()
        cues = [f'00:00:{2*i:02d}.000 --> 00:00:{2*i+1:02d}.000\n'
                f'You and I have the time to do what we can with our work for your day {i}.'
                for i in range(7)]
        self.raw = ('WEBVTT\n\n'+'\n\n'.join(cues)+'\n').encode()
        self.cues = youtube_captions.normalize_caption(self.raw, 'vtt')
        self.row = {'video_id':VIDEO, 'channel_dir':CREATOR, 'tab':'videos', 'expected_channel_id':OWNER}
        url = 'https://www.buzzsprout.com/12345/771/transcript.vtt'
        self.item = dict(self.row, provider='Buzzsprout', selected_channel_id=OWNER,
                         publisher_feed_sha256='f'*64, selection_sha256='e'*64, episode_guid='Buzzsprout-771',
                         show_id='12345', show_name='Test publisher', show_language='en-gb', feed_track_language_label=None,
                         declared_mime_type='text/vtt', source_url=url, source_format='vtt', source_bytes=len(self.raw),
                         source_sha256=digest(self.raw)['sha256'], raw_http_proof={'origin_url':url,'status':200,
                             'observed_eof':True,'proof':digest(self.raw),'declared_content_length':str(len(self.raw))},
                         language='en', language_evidence=batch.cue_language_evidence(self.cues['text']),
                         caption_kind='publisher_provided_unspecified', translation_status='not_declared',
                         source_timebase='publisher_episode_seconds', original_clock_retained=True, source_audio_sha256=None,
                         native_youtube_caption=False, youtube_edit_equivalence_verified=False, youtube_time_alignment_verified=False,
                         speech_coverage_verified=False, publisher_duration_s=30, youtube_duration_s=29, difference_seconds=1,
                         first_cue_start=0., last_cue_end=13., segment_count=7, episode_youtube_references=[],
                         association_method='publisher_owner_title_date_duration', exact_youtube_crossreference=False,
                         same_normalized_title=True, youtube_title='Recorded Interview', episode_title='Recorded Interview',
                         youtube_publication_date='2026-11-19', publisher_date='2026-11-18')

    def build(self, *, change_segments=False):
        items=deepcopy(self.cues['segments'])
        if change_segments:
            items[0]['text']='Unrelated words'
        p=VIDEO+'/'
        parts={p+'publisher.vtt':self.raw, p+'provenance.json':publisher_mirror.encoded(self.item),
               p+'segments.json':publisher_mirror.encoded(items),p+'transcript.txt':(self.cues['text']+'\n').encode()}
        parts['manifest.json']=publisher_mirror.encoded({k:digest(v) for k,v in parts.items()})
        out=self.root/'archive.zip'
        with ZipFile(out,'w') as z:
            for name,raw in parts.items():
                z.writestr(name,raw)
        proof=digest(out.read_bytes())
        proof.update(drive_id='fixture-object',remote=f"{REMOTE}/{CREATOR}/PublisherCaptions/Batches/{proof['sha256']}/publisher-captions.zip")
        record={'schema_version':1,'artifact_kind':batch.RSS_ENGLISH_BATCH,'status':'verified','channel_dir':CREATOR,
                'items':[self.item],'proof':proof,'changes_native_audio_count':False,'changes_native_caption_count':False,
                'changes_full_asr_count':False}
        (self.root/'sync/publisher_caption_manifest.jsonl').write_bytes(publisher_mirror.encoded(record))
        return out,record

    def test_verified_publisher_timeline_and_english_cues(self):
        path,record=self.build()
        (job,)=reader.input_rows(self.root,[self.row],REMOTE)
        view=reader.text_views(path,job,REMOTE)['caption']
        self.assertEqual(ingestion_status.publisher_timed_text_coverage(self.root,{VIDEO},REMOTE,[self.row]),{VIDEO})
        self.assertEqual(view['source_timebase'],'publisher_caption_seconds')
        self.assertTrue(batch.confirmed_english_cues(view['language_evidence']))
        self.assertEqual(view['raw_sha256'],digest(self.raw)['sha256'])
        self.assertEqual(len(view['segments']),7)
        self.assertIsNone(view['source_audio_sha256'])
        self.assertFalse(view['native_youtube_alignment_verified'])
        self.assertEqual(list(reader.input_rows(self.root,[dict(self.row,expected_channel_id='UC'+'z'*22)],REMOTE)),[])
        self.assertEqual(batch.verified_videos(record,{VIDEO},REMOTE,{VIDEO:(CREATOR,'streams')}),set())

    def test_changed_title_feed_language_or_mislabeled_text_does_not_qualify(self):
        for changes in ({'episode_title':'Unrelated episode'},{'publisher_date':'2026-11-10'},
                        {'source_url':'https://example.org/771/transcript.vtt'},
                        {'youtube_duration_s':45,'difference_seconds':15},{'show_language':'fr'},
                        {'language_evidence':batch.cue_language_evidence('Episode introduction')},
                        {'native_youtube_caption':True},{'raw_http_proof':{'status':200}}):
            with self.subTest(changes=changes):
                self.assertFalse(batch.rss_edition(dict(self.item,**changes)))

    def test_publisher_link_supports_separate_longer_edition(self):
        row=dict(self.item,exact_youtube_crossreference=True, episode_youtube_references=[VIDEO],
                 association_method='publisher_episode_exact_youtube_reference',youtube_duration_s=98,difference_seconds=68)
        self.assertTrue(batch.rss_edition(row))
        self.assertFalse(batch.rss_edition(dict(row,episode_youtube_references=[])))

    def test_checksummed_but_rewritten_archive_cues_fail_raw_reproduction(self):
        path,_=self.build(change_segments=True)
        (job,)=reader.input_rows(self.root,[self.row],REMOTE)
        with self.assertRaisesRegex(ValueError,'cue content or language proof'):
            reader.text_views(path,job,REMOTE)


if __name__=='__main__':
    unittest.main()
