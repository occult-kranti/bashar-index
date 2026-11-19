from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from pipeline import ingestion_status as status


class SharedPublisherAudio(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);(self.root/'sync').mkdir()
        self.remote='archive:Audio';self.video='YsSEFz__Rqg';self.original='O2Pf891igG0';self.channel='dallisa-hocking'

    def receipts(self):
        def art(video,name,digest):
            return dict(bytes=256,md5=digest*32,sha256=digest*64,drive_id=digest,
                remote=f'{self.remote}/{self.channel}/Videos/{video}/PublisherVariants/'+ 'a'*64+'/'+name)
        audio=art(self.original,'publisher-audio.mp3','a')
        payload=dict(creator=self.channel,feed_sha256='e'*64,qualified_source={'guid':'show/episode-9'},
                     audio={k:audio[k] for k in ('bytes','md5','sha256')})
        raw=(json.dumps(payload,sort_keys=True,ensure_ascii=False,separators=(',',':'))+'\n').encode()
        provenance={**art(self.original,'provenance.json','b'),'bytes':len(raw),
            'sha256':hashlib.sha256(raw).hexdigest(),'md5':hashlib.md5(raw).hexdigest()}
        flags=dict(native_youtube_bytes=False,changes_native_audio_count=False,changes_native_asr_count=False,
            changes_native_caption_count=False,human_verified=False)
        anchor=dict(schema_version=1,status='verified',kind='publisher_mirror_audio_variant',
            associated_youtube_id=self.original,channel_dir=self.channel,source_tab='videos',variant_id=audio['sha256'],
            association_method='publisher_rss_exact_youtube_id',exact_youtube_crossreference=True,
            original_youtube_link='https://youtu.be/'+self.original,provider='Podbean',audio=audio,
            provenance=provenance,accepted_api_sha256='e'*64,caption_bundles=[],**flags)
        pointer={**art(self.video,'publisher-audio.ref.json','d'),'points_to_drive_id':audio['drive_id'],
            'source_audio_sha256':audio['sha256'],'source_audio_bytes':audio['bytes']}
        alias=dict(schema_version=1,status='verified',kind='shared_publisher_audio_association',
            associated_youtube_id=self.video,channel_dir=self.channel,source_tab='videos',variant_id=audio['sha256'],
            association_method='publisher_owner_title_date_duration',exact_youtube_crossreference=False,
            recording_equivalence_verified=False,youtube_edit_equivalence_verified=False,publisher_source_reused=True,
            provider='Podbean',audio=deepcopy(audio),provenance=art(self.video,'provenance.json','c'),audio_reference=pointer,
            canonical_provenance=deepcopy(provenance),canonical_associated_youtube_id=self.original,
            canonical_receipt_sha256=status.publisher_receipt_digest(anchor),canonical_provenance_payload=payload,
            canonical_provenance_encoding='sorted_compact_utf8_json_newline_v1',source_episode_guid='show/episode-9',
            accepted_api_sha256='e'*64,source_tab_evidence=dict(video_id=self.video,channel_dir=self.channel,tab='videos',roster_sha256='f'*64),
            caption_bundles=[],**flags)
        return anchor,alias

    def view(self,records,ids=None):
        ids=ids or {self.video}
        (self.root/'sync/publisher_mirror_manifest.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in records),encoding='utf-8')
        return status.publisher_mirror_evidence(self.root,ids,self.remote,
            [dict(video_id=v,channel_dir=self.channel,tab='videos') for v in ids])

    def test_one_file_two_listing_associations_and_anchor_outside_requested_set(self):
        anchor,alias=self.receipts()
        self.assertEqual(self.view([alias,anchor]),({self.video},set(),set(),set()))
        self.assertEqual(self.view([anchor,alias],{self.video,self.original}),({self.video,self.original},set(),set(),set()))
        self.assertEqual(self.view([anchor],{self.original}),({self.original},set(),set(),set()))
        self.assertEqual((alias['audio']['sha256'],alias['audio']['bytes']),(anchor['audio']['sha256'],anchor['audio']['bytes']))
        self.assertNotEqual(status.publisher_receipt_digest(anchor),status.publisher_receipt_digest(alias))

    def test_missing_changed_foreign_or_alias_anchor_cannot_count(self):
        anchor,alias=self.receipts()
        self.assertEqual(self.view([alias]),(set(),set(),set(),set()))
        for key,value in [('canonical_receipt_sha256','f'*64),('canonical_associated_youtube_id','foreign0000'),
                          ('channel_dir','foreign'),('publisher_source_reused',False),
                          ('youtube_edit_equivalence_verified',True),('source_episode_guid','different/episode')]:
            wrong=deepcopy(alias);wrong[key]=value
            with self.subTest(key=key):self.assertEqual(self.view([anchor,wrong]),(set(),set(),set(),set()))
        chained=deepcopy(alias);chained['canonical_receipt_sha256']=status.publisher_receipt_digest(alias)
        self.assertEqual(self.view([alias,chained]),(set(),set(),set(),set()))

    def test_every_audio_field_pointer_and_provenance_payload_is_bound(self):
        anchor,alias=self.receipts()
        for key,value in [('remote',alias['audio']['remote']+'-different'),('drive_id','foreign'),
                          ('bytes',257),('md5','f'*32),('sha256','f'*64)]:
            wrong=deepcopy(alias);wrong['audio'][key]=value
            with self.subTest(key=key):self.assertEqual(self.view([anchor,wrong]),(set(),set(),set(),set()))
        wrong=deepcopy(alias);wrong['audio_reference']['drive_id']=anchor['audio']['drive_id']
        self.assertEqual(self.view([anchor,wrong]),(set(),set(),set(),set()))
        wrong=deepcopy(alias);wrong['canonical_provenance_payload']['qualified_source']['guid']='other'
        self.assertEqual(self.view([anchor,wrong]),(set(),set(),set(),set()))

    def test_malformed_reference_does_not_raise_or_change_legacy_coverage(self):
        anchor,alias=self.receipts()
        for value in ({},[],None):
            wrong=deepcopy(alias);wrong['canonical_receipt_sha256']=value
            self.assertEqual(self.view([anchor,wrong],{self.original,self.video}),({self.original},set(),set(),set()))


if __name__=='__main__':unittest.main()
