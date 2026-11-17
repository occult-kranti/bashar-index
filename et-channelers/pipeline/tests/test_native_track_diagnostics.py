import copy
import json
import unittest
from urllib.parse import urlencode

from pipeline import native_track_policy as new
def raw(extra=None):
    base={'itag':140,'mimeType':'audio/mp4; codecs="mp4a.40.2"','contentLength':'100','url':'https://media.example.invalid/videoplayback?opaque=PRIVATE_SENTINEL'}
    drc=dict(base,isDrc=True,contentLength='101')
    if extra:drc.update(extra)
    return [{'videoDetails':{'videoId':'abcdefghijk'},'playabilityStatus':{'status':'OK'},'streamingData':{'__yt_dlp_client':'mweb','adaptiveFormats':[base,drc]}}]
class Diagnostics(unittest.TestCase):
    def assert_unchanged(self,response):
        saved=copy.deepcopy(response);new.legacy_track_inventory('abcdefghijk',response)
        self.assertEqual(response,saved)
    def test_known_processing_tag_is_diagnostic_only(self):
        response=raw({'url':'https://media.example.invalid/videoplayback?'+urlencode({'xtags':'drc=1','opaque':'PRIVATE_SENTINEL'})})
        self.assert_unchanged(response);result=new.legacy_track_inventory('abcdefghijk',response)
        self.assertFalse(result['eligible']);self.assertEqual(result['reason'],'track_labels_present')
        d=result['audio_representations'][1]['label_diagnostics'];self.assertEqual(d['xtags_state'],'exact_drc_only')
        self.assertNotIn('PRIVATE_SENTINEL',json.dumps(result));self.assertNotIn('https:',json.dumps(result))
    def test_compound_language_default_and_opaque_remain_held(self):
        for value in ('drc=1&lang=en','drc=1&acont=original','drc=1&drc=1','opaque-base64','drc=1;lang=en','drc=0'):
            response=raw({'url':'https://media.example.invalid/v?'+urlencode({'xtags':value})})
            self.assert_unchanged(response);result=new.legacy_track_inventory('abcdefghijk',response)
            self.assertFalse(result['eligible']);self.assertEqual(result['audio_representations'][1]['label_diagnostics']['xtags_state'],'other_or_unreadable')
    def test_direct_drc_existing_admission_unchanged(self):
        response=raw({'url':'https://media.example.invalid/v?drc=1'})
        self.assert_unchanged(response);result=new.legacy_track_inventory('abcdefghijk',response)
        self.assertTrue(result['eligible']);self.assertEqual(result['audio_representations'][1]['label_diagnostics']['transport_known_keys'],['drc'])
    def test_track_values_never_exported(self):
        response=raw({'audioTrack':{'id':'PRIVATE_SENTINEL','displayName':'PRIVATE_SENTINEL','attacker_key_PRIVATE_SENTINEL':True},'language':'PRIVATE_SENTINEL'})
        self.assert_unchanged(response);result=new.legacy_track_inventory('abcdefghijk',response)
        d=result['audio_representations'][1]['label_diagnostics']
        self.assertEqual(d['label_fields_present'],['language']);self.assertEqual(d['audio_track_known_keys'],['displayName','id'])
        self.assertTrue(d['audio_track_unknown_key_present']);self.assertNotIn('PRIVATE_SENTINEL',json.dumps(result))
    def test_cipher_parsed_in_memory_only(self):
        fmt=raw()[0]['streamingData']['adaptiveFormats'][1];fmt.pop('url')
        fmt['signatureCipher']=urlencode({'s':'PRIVATE_SENTINEL','url':'https://media.example.invalid/v?'+urlencode({'xtags':'drc=1'})})
        d=new.label_diagnostics(fmt);self.assertEqual(d['xtags_state'],'exact_drc_only');self.assertNotIn('PRIVATE_SENTINEL',json.dumps(d))
    def test_diagnostic_budget_holds_without_exception(self):
        d=new.label_diagnostics({'url':'https://media.example.invalid/v?'+('x='+'a'*40000)})
        self.assertFalse(d['transport_diagnostic_complete']);self.assertLess(len(json.dumps(d)),1200)
    def test_duplicate_top_and_url_projections_are_exact_and_equal_without_admission(self):
        response=raw({'xtags':'drc=1','url':'https://media.example.invalid/v?'+urlencode({'xtags':'drc=1'})})
        result=new.legacy_track_inventory('abcdefghijk',response);d=result['audio_representations'][1]['label_diagnostics']
        self.assertFalse(result['eligible']);self.assertEqual(result['reason'],'track_labels_present')
        self.assertEqual(d['xtags_projection_count'],2);self.assertTrue(d['xtags_projections_equal']);self.assertTrue(d['all_exact_drc_only'])
        self.assertEqual(d['xtags_by_origin']['top_level'],'exact_drc_only');self.assertEqual(d['xtags_by_origin']['url'],'exact_drc_only')
    def test_compound_opaque_and_mismatched_projection_origins_remain_unresolved(self):
        for value in ('drc=1&lang=en','opaque-private-value','drc=0'):
            response=raw({'xtags':'drc=1','url':'https://media.example.invalid/v?'+urlencode({'xtags':value})})
            result=new.legacy_track_inventory('abcdefghijk',response);d=result['audio_representations'][1]['label_diagnostics']
            self.assertFalse(result['eligible']);self.assertFalse(d['all_exact_drc_only']);self.assertFalse(d['xtags_projections_equal'])
            self.assertEqual(d['xtags_by_origin']['top_level'],'exact_drc_only');self.assertEqual(d['xtags_by_origin']['url'],'other_or_unreadable')
            self.assertNotIn(value,json.dumps(d))
    def test_cipher_field_and_nested_url_projections_are_separate(self):
        d=new.label_diagnostics({'signatureCipher':urlencode({'s':'PRIVATE_SENTINEL','xtags':'drc=1','url':'https://media.example.invalid/v?'+urlencode({'xtags':'drc=1'})})})
        self.assertEqual(d['xtags_projection_counts'],{'top_level':0,'url':0,'cipher':1,'cipher_url':1})
        self.assertTrue(d['all_exact_drc_only']);self.assertTrue(d['xtags_projections_equal']);self.assertNotIn('PRIVATE_SENTINEL',json.dumps(d))
    def test_projection_count_is_bounded_and_truncation_never_claims_equal(self):
        d=new.label_diagnostics({'url':'https://media.example.invalid/v?'+urlencode([('xtags','drc=1')]*9)})
        self.assertEqual(d['xtags_projection_count'],8);self.assertTrue(d['xtags_projection_limit_reached'])
        self.assertFalse(d['transport_diagnostic_complete']);self.assertFalse(d['all_exact_drc_only']);self.assertIsNone(d['xtags_projections_equal'])
        self.assertLess(len(json.dumps(d)),1200)
if __name__=='__main__':unittest.main()
