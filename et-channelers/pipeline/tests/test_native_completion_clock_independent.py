from copy import deepcopy
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from pipeline import native_completion_clock_independent as clock
from pipeline.tests import test_native_completion_clock as fixtures


class IndependentClocks(unittest.TestCase):
    def test_launcher_exception_import_is_the_unchanged_strict_class(self):
        from pipeline.native_completion_clock_independent import CompletionClockHold, later_verified_native_pairs
        self.assertIs(CompletionClockHold, clock.strict.CompletionClockHold)
        self.assertTrue(callable(later_verified_native_pairs))

    def write(self,path,value):
        path.parent.mkdir(parents=True,exist_ok=True);raw=json.dumps(value).encode();path.write_bytes(raw)
        return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}

    def test_bad_pair_cannot_discard_an_independent_later_direct_pair_but_global_closure_still_holds(self):
        transfer,receipt=fixtures.NativeCompletionClockTests().fixture()
        with TemporaryDirectory() as temp:
            home=Path(temp);pairs=[];results=[]
            for video,redirect in (('example1234',False),('other123456',True)):
                rec=deepcopy(receipt);tr=deepcopy(transfer)
                rec['video_id']=video;rec['native_format_binding']['videoId']=video
                if redirect:tr['Native_HTTP_positive_equality_eligible']=False;tr['redirects']=[{'approved':True}]
                obs=home/'runtime/observations'/video
                tp=self.write(obs/'range-transfer.json',tr);rp=self.write(obs/'publication-receipt.json',rec)
                pairs.append({'video_id':video,'range_transfer':tp,'canonical_receipt':rp,'audio_Drive_ID':rec['drive_id'],
                    'metadata_Drive_ID':rec['metadata']['drive_id'],'audio_bytes':8,'audio_md5':rec['md5'],
                    'native_format_binding':rec['native_format_binding']})
                results.append({'video_id':video,'status':'paired_verified_deleted'})
            result=self.write(home/'runtime/result.json',{'root_grant_sha256':'e'*64,'all_source_threads_returned':True,
                'all_publisher_threads_returned':True,'results':results})
            release=self.write(home/'runtime/release.json',{'status':'released',
                'released_owned_resource_row':{'state':'released','root_grant_sha256':'e'*64}})
            hand=self.write(home/'handoff/final.json',{'owned_closure':{'closed':True,'owned_job_empty':True,'errors':[]},
                'root_grant':{'sha256':'e'*64},'actual_release':release,'actual_batch_result':result,'pairs':pairs,'paired_count':2})
            value=clock.independent_later_verified_native_pairs(hand,16)
            self.assertEqual([r['video_id'] for r in value['pairs']],['example1234'])
            self.assertEqual(value['direct_pairs_validated'],1);self.assertEqual(len(value['unsupported_or_invalid_pairs']),1)
            self.assertEqual(clock.independent_later_verified_native_pairs(hand,18)['pairs'],[])
            (home/'runtime/observations/other123456/range-transfer.json').write_bytes(b'{}')
            self.assertEqual(len(clock.independent_later_verified_native_pairs(hand,16)['pairs']),1)
            (home/'runtime/release.json').write_bytes(b'{}')
            with self.assertRaises(clock.strict.CompletionClockHold):clock.independent_later_verified_native_pairs(hand,16)


if __name__=='__main__':unittest.main()
