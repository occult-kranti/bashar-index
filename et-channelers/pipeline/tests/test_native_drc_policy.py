import base64
import json
import unittest
from urllib.parse import urlencode

from pipeline import native_track_policy as p
ID = 'aaaaaaaaaaa'


def encoded(*pairs):
    raw = b''
    for key, value in pairs:
        key, value = key.encode(), value.encode()
        nested = bytes([10, len(key)]) + key + bytes([18, len(value)]) + value
        raw += bytes([10, len(nested)]) + nested
    return base64.urlsafe_b64encode(raw).decode()


def fixture():
    normal = {'itag':140,'mimeType':'audio/mp4; codecs="mp4a.40.2"','contentLength':'1234',
              'url':'https://r1.googlevideo.com/videoplayback?itag=140'}
    drc = dict(normal, isDrc=True, xtags=encoded(('drc','1')),
               url='https://r1.googlevideo.com/videoplayback?itag=140&xtags=drc%3D1')
    return [{'videoDetails':{'videoId':ID},'playabilityStatus':{'status':'OK'},
             'streamingData':{'__yt_dlp_client':'mweb','adaptiveFormats':[normal,drc]}}]


class PolicyTests(unittest.TestCase):
    def result(self, value):
        return p.legacy_track_inventory(ID,value)

    def test_exact_schema_bound_drc_processing_proof_keeps_inferred_unknown_language(self):
        result = self.result(fixture())
        self.assertTrue(result['eligible']); self.assertIsNone(result['source_language'])
        self.assertTrue(result['origin_inferred']); self.assertFalse(result['original_explicitly_verified'])
        self.assertTrue(result['audio_representations'][1]['decoded_drc_processing_only'])
        self.assertFalse(result['audio_representations'][1]['semantic_labels_present'])
        rendered = json.dumps(result)
        for private in ('https://','googlevideo',encoded(('drc','1'))): self.assertNotIn(private, rendered)

    def test_selects_only_normal_exact_size_codec_and_numeric_preference(self):
        inventory = self.result(fixture())
        info={'id':ID,'format_id':'140','acodec':'mp4a.40.2','filesize':1234,'language_preference':-1,'language':'en'}
        proof=p.legacy_selection_proof(info,inventory)
        self.assertIsNone(proof['source_language']); self.assertFalse(proof['normalized_language_used_as_audio_evidence'])
        for change in ({'isDrc':True},{'format_id':'140-drc'},{'filesize':1235},{'acodec':'opus'},{'language_preference':5}):
            self.assertIsNone(p.legacy_selection_proof(dict(info,**change),inventory))

    def test_language_dub_voice_boost_or_unknown_proto_tag_never_relaxes(self):
        for key in ('lang','acont','vb','unknown'):
            raw=fixture();raw[0]['streamingData']['adaptiveFormats'][1]['xtags']=encoded(('drc','1'),(key,'private-value'))
            self.assertFalse(self.result(raw)['eligible'])

    def test_any_semantic_transport_tag_case_or_compound_xtags_rejects(self):
        for tag in ('lang=en','LANG=en','acont=dubbed','vb=1','drc=0','xtags=lang%3Den'):
            raw=fixture();fmt=raw[0]['streamingData']['adaptiveFormats'][1];fmt['url'] += '&'+tag
            self.assertFalse(self.result(raw)['eligible'],tag)

    def test_raw_track_labels_defaults_drm_and_voiceboost_still_reject(self):
        for change in ({'audioTrack':{'id':'en.1'}},{'audioIsDefault':True},{'language':'en'},
                       {'has_drm':True},{'isVb':True},{'displayName':'original'}):
            raw=fixture();raw[0]['streamingData']['adaptiveFormats'][1].update(change)
            self.assertFalse(self.result(raw)['eligible'])

    def test_false_semantic_declarations_are_not_unlabeled_original_evidence(self):
        for key in ('isOriginal', 'isDubbed', 'isAutoDubbed', 'audioIsDefault'):
            for index in (0,1):
                raw=fixture();raw[0]['streamingData']['adaptiveFormats'][index][key]=False
                result=self.result(raw);self.assertFalse(result['eligible'])
                self.assertIn(key,result['audio_representations'][index]['declared_semantic_fields'])
        raw=fixture();raw[0]['streamingData']['adaptiveFormats'][0]['isDrc']=False
        self.assertTrue(self.result(raw)['eligible'])

    def test_other_semantic_transport_keys_never_become_processing_only(self):
        for key in ('vlang','isVb','audioIsDefault','audio_track_id','atrack','isOriginal'):
            raw=fixture();fmt=raw[0]['streamingData']['adaptiveFormats'][1];fmt['url'] += '&'+key+'=false'
            self.assertFalse(self.result(raw)['eligible'])

    def test_unmatched_drc_or_missing_isdrc_and_normal_xtags_reject(self):
        for change in ({'itag':251},{'mimeType':'audio/webm; codecs="opus"'},{'isDrc':False}):
            raw=fixture();raw[0]['streamingData']['adaptiveFormats'][1].update(change)
            self.assertFalse(self.result(raw)['eligible'])
        raw=fixture();raw[0]['streamingData']['adaptiveFormats'][0]['xtags']=encoded(('drc','1'))
        self.assertFalse(self.result(raw)['eligible'])

    def test_malformed_base64_proto_and_disagreeing_url_reject(self):
        for top in ('bad','CggKA2RyYxIBMR==',encoded(('drc','0')),encoded(('drc','1'),('drc','1'))):
            raw=fixture();raw[0]['streamingData']['adaptiveFormats'][1]['xtags']=top
            self.assertFalse(self.result(raw)['eligible'])
        raw=fixture();raw[0]['streamingData']['adaptiveFormats'][1]['url']='https://r1.googlevideo.com/videoplayback?xtags=vb%3D1'
        self.assertFalse(self.result(raw)['eligible'])

    def test_cipher_projection_is_bound_and_unknown_outer_semantics_reject(self):
        raw=fixture();fmt=raw[0]['streamingData']['adaptiveFormats'][1];url=fmt.pop('url')
        fmt['signatureCipher']=urlencode({'url':url,'s':'private-signature-not-retained'})
        self.assertTrue(self.result(raw)['eligible'])
        fmt['signatureCipher'] += '&LANG=en'
        self.assertFalse(self.result(raw)['eligible'])


if __name__ == '__main__': unittest.main()
