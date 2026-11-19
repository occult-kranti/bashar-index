import math
import unittest

from pipeline.publisher_hold_scope import AssetRefusalReview, entry_hash, hold_deadline


class PublisherHoldScopeTests(unittest.TestCase):
    def setUp(self):
        self.entry={'provider':'Example','endpoint':'audio','response_status':403,'retry_not_before_epoch':90000}
        self.review=AssetRefusalReview(entry_hash(self.entry),'a'*64,'show1episode2','show1',False)
        self.current={'enclosure_sha256':'b'*64,'guid':'show2episode4','publisher_account':'show2'}

    def check(self,entry=None,**changes):
        return hold_deadline(self.entry if entry is None else entry,'Example','audio',**{**self.current,**changes},review=self.review)

    def test_independently_identified_publisher_and_item(self):
        self.assertEqual(self.check(),0)
        self.assertEqual(self.check(publisher_account='show1'),90000)
        self.assertTrue(math.isinf(self.check(enclosure_sha256='a'*64)))
        self.assertTrue(math.isinf(self.check(guid='show1episode2')))

    def test_changed_evidence_unidentified_assets_and_provider_rest_are_preserved(self):
        self.assertEqual(self.check({**self.entry,'accepted_api_sha256':'x'}),90000)
        self.assertEqual(self.check(enclosure_sha256=''),90000)
        for change in ({'response_status':429},{'retry_after':'600'},{'retry_after_requires_review':True},{'scope_kind':'provider'}):
            self.assertEqual(self.check({**self.entry,**change}),90000)

    def test_new_asset_refusal_remains_bound_to_the_enclosure_or_episode(self):
        row={**self.entry,'scope_kind':'asset','enclosure_sha256':'a'*64,'guid':'show1episode2','publisher_account':'show1'}
        self.assertEqual(self.check(row),0)
        self.assertTrue(math.isinf(self.check(row,enclosure_sha256='a'*64)))
        self.assertTrue(math.isinf(self.check(row,guid='show1episode2',publisher_account='show1')))
        self.assertEqual(self.check({**row,'response_status':429}),90000)
        self.assertEqual(self.check({**row,'endpoint':'captions'}),0)
