from pathlib import Path
import json,sys,tempfile,unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import additive_video_selection as selection

A='UC'+'A'*22;B='UC'+'B'*22
def row(video,creator='alpha',tab='videos',channel=A,rank=0,**extra):
    return dict(video_id=video,channel_dir=creator,expected_channel_id=channel,tab=tab,title=video,listing_rank=rank,primary_grid_position=rank,**extra)
def source(kind,rows):return dict(kind=kind,rows=rows,artifact={'path':kind,'bytes':1,'sha256':'a'*64},observed_at='2026-11-18T12:00:00Z')
def fresh(items,beta=()):
    return dict(schema_version=1,per_channel=20,observed_at='2026-11-19T16:30:00Z',channels=[dict(creator='alpha',channel_dir='alpha',channel_id=A,state='observed',listing_complete=True,items=items),dict(creator='beta',channel_dir='beta',channel_id=B,state='partial',listing_complete=False,items=list(beta))])
def build(retained,document,**kwargs):return selection.build_selection(retained,document,expected_creators=2,**kwargs)

class AdditiveSelection(unittest.TestCase):
    def test_union_keeps_displaced_regular_and_supplementary_memberships(self):
        mixed=[row('short______',tab='shorts'),row('common_____',rank=1)]
        regular=[row('old________',channel=None),row('common_____',rank=1)]
        result=build([source('retained_mixed',mixed),source('retained_regular',regular)],fresh([row('common_____'),row('new________',rank=1)]))
        by_id={r['video_id']:r for r in result['rows']}
        self.assertEqual(set(by_id),{'short______','old________','common_____','new________'})
        self.assertEqual(set(by_id['common_____']['scope_memberships']),{'retained_mixed','retained_regular','fresh_regular'})
        self.assertEqual(len(by_id['common_____']['memberships']),3)
        self.assertEqual(by_id['short______']['tab'],'shorts')
        self.assertIsNone(by_id['old________']['expected_channel_id'])
        self.assertTrue(by_id['new________']['newly_observed']);self.assertFalse(by_id['common_____']['newly_observed'])
        self.assertEqual(result['summary']['fresh_regular_recordings'],2)
        self.assertEqual(result['summary']['fresh_grid_shortfalls_never_filled_from_shorts'],38)

    def test_case_sensitive_identity_fair_priority_and_strict_fresh_grid(self):
        result=build([],fresh([row('Video______'),row('video______',rank=1)],[row('beta_______','beta',channel=B)]))
        self.assertEqual([r['video_id'] for r in result['rows']],['Video______','beta_______','video______'])
        with self.assertRaisesRegex(ValueError,'Videos grid'):build([],fresh([row('short______',tab='shorts')]))
        with self.assertRaisesRegex(ValueError,'identity mismatch'):build([source('retained_regular',[row('video______','ALPHA')])],fresh([]))
        duplicate=fresh([row('one________'),row('two________')])
        with self.assertRaisesRegex(ValueError,'position'):build([],duplicate)

    def test_observed_is_not_posted_and_exact_cutoff_evidence(self):
        document=fresh([row('relative___',date_display='1 hour ago'),row('absolute___',rank=1,published_at='2026-11-19T12:30:00Z'),row('same_day___',rank=2,publication_date='2026-11-19',date_quality='exact')])
        result=build([],document,earlier_cutoff='2026-11-19T12:00:00Z');by_id={r['video_id']:r for r in result['rows']}
        self.assertIsNone(by_id['relative___']['demonstrably_newly_posted_after_cutoff'])
        self.assertIsNone(by_id['same_day___']['demonstrably_newly_posted_after_cutoff'])
        self.assertTrue(by_id['absolute___']['demonstrably_newly_posted_after_cutoff'])
        self.assertEqual(result['summary']['newly_observed_recordings'],3)
        self.assertEqual(result['summary']['demonstrably_newly_posted_after_cutoff'],1)

    def test_conflicting_uploader_is_retained_conditional(self):
        result=build([source('retained_mixed',[row('conflict___',channel=B)])],fresh([row('conflict___')]))
        record=result['rows'][0]
        self.assertIsNone(record['expected_channel_id']);self.assertTrue(record['uploader_identity_conflict'])
        self.assertEqual(record['known_source_channel_ids'],[A,B])
        with tempfile.TemporaryDirectory() as tmp:
            paths=selection.write_artifacts(result,Path(tmp)/'new-version')
            runtime=json.loads(Path(paths['runtime']['path']).read_bytes())
            self.assertEqual(runtime['conditional_uploader_rows'][0]['eligibility'],'uploader_identity_evidence_required')
            self.assertFalse(runtime['Source_authorized'])

    def test_legacy_csv_unquotes_id_and_preserves_previous_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'queue.csv';path.write_text("video_id,channel_dir,tab,listing_rank\n'-abcdefghi_,alpha,videos,0\n",encoding='utf-8')
            retained=selection.read_retained(path,'retained_regular')
            result=build([retained],fresh([]))
            self.assertEqual(result['rows'][0]['video_id'],'-abcdefghi_')
            self.assertIsNone(result['rows'][0]['earliest_known_observed_at'])

    def test_verified_counts_use_actual_native_gate_not_text_or_owner_mismatch(self):
        result=build([],fresh([row('native_____'),row('text_______',rank=1),row('wrong______',rank=2)]))
        def native(video,owner='alpha'):
            remote='etdrive:04 Audio/'+owner+'/Videos/'+video
            return dict(video_id=video,channel_dir=owner,status='deleted',tab='videos',path='audio/'+owner+'/Videos/'+video+'.webm',remote=remote+'.webm',drive_id='audio-'+video,bytes=100,md5='a'*32,sha256='b'*64,metadata=dict(remote=remote+'.info.json',drive_id='metadata-'+video,md5='c'*32,sha256='d'*64))
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'sync').mkdir()
            rows=[native('native_____'),native('wrong______','beta'),dict(video_id='text_______',channel_dir='alpha',status='verified',artifact_kind='publisher_transcript',changes_selected_audio_count=False)]
            (root/'sync/drive_ingest_manifest.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows),encoding='utf-8')
            counts=selection.verified_counts(result,root)
            self.assertEqual(counts['summary']['verified_audio'],1)
            self.assertEqual(counts['summary']['fresh_regular_verified'],1)
            self.assertEqual(counts['summary']['remaining'],2)

    def test_literal_members_only_is_retained_public_fill_in_is_separate(self):
        member=row('member_____',access_status='members_only')
        public=row('public_____',rank=1,access_status='public_listing')
        older=row('older______',rank=2,access_status='public_listing')
        document=fresh([member,public]);document['channels'][0].update(observed_items=[member,public,older],public_items=[dict(public,listing_rank=0,regular_listing_rank=1),dict(older,listing_rank=1,regular_listing_rank=2)],public_listing_complete=True)
        result=build([],document);by_id={r['video_id']:r for r in result['rows']}
        self.assertTrue(by_id['member_____']['fresh_regular'])
        self.assertTrue(by_id['member_____']['public_media_dispatch_excluded'])
        self.assertTrue(by_id['older______']['fresh_public_regular'])
        self.assertFalse(by_id['older______']['fresh_regular'])
        self.assertEqual(result['summary']['fresh_regular_recordings'],2)
        self.assertEqual(result['summary']['public_regular_priority_recordings'],2)
        self.assertEqual(result['summary']['literal_latest20_members_only'],1)
        with tempfile.TemporaryDirectory() as tmp:
            paths=selection.write_artifacts(result,Path(tmp)/'access-aware')
            runtime=json.loads(Path(paths['runtime']['path']).read_bytes())
            self.assertEqual({r['video_id'] for r in runtime['candidates']},{'public_____','older______'})
            self.assertEqual([r['video_id'] for r in runtime['held_members_only_rows']],['member_____'])

    def test_years_old_and_undated_top20_remain_dispatch_candidates(self):
        document=fresh([row('years_old__',published_at='2010-01-01T00:00:00Z'),row('undated____',rank=1)])
        result=build([],document,earlier_cutoff='2026-11-17T03:27:16Z')
        overlay=[dict(channel_dir='alpha',channel_id=A,video_id='years_old__',publication_or_upload=dict(precision='instant',value='2010-01-01T00:00:00Z'),date_quality='instant',date_basis='cached_metadata_publication',cutoff_class='at_or_before_cutoff',fresh_latest20=True,distinct_vs_prior_regular=True,in_retained_nov19_mixed_latest20=False,display_cutoff_evidence='display_indicates_older')]
        decorated=selection.apply_publication_overlay(result,overlay,{'sha256':'a'*64},'2026-11-17T03:27:16Z')
        annotated=selection.apply_publication_overlay(result,overlay,{'sha256':'a'*64})
        self.assertNotIn('publication_change_audit',annotated)
        self.assertEqual([r['video_id'] for r in annotated['rows']], [r['video_id'] for r in result['rows']])
        self.assertEqual(next(r for r in annotated['rows'] if r['video_id']=='years_old__')['publication_date'],'2010-01-01')
        with tempfile.TemporaryDirectory() as tmp:
            paths=selection.write_artifacts(decorated,Path(tmp)/'dates-are-not-eligibility')
            runtime=json.loads(Path(paths['runtime']['path']).read_bytes());main=json.loads(Path(paths['selection']['path']).read_bytes())
            self.assertEqual({r['video_id'] for r in runtime['candidates']},{'years_old__','undated____'})
            self.assertFalse(main['eligibility_date_or_duration_cutoff'])
            self.assertNotIn('demonstrably_newly_posted_after_cutoff',main['summary'])
            self.assertTrue((Path(tmp)/'dates-are-not-eligibility/publication-change-audit.json').exists())

if __name__=='__main__':unittest.main()
