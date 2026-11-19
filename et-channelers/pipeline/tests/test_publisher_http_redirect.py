"""Publisher zero-wait redirect behavior, without any network request."""
from email.message import Message
import unittest
from pipeline.publisher_http_redirect import PublisherRedirectHold, redirect_wait_satisfied


def headers(*values):
    result=Message()
    for value in values:result['Retry-After']=value
    return result


class PublisherRedirectTests(unittest.TestCase):
    def test_zero_on_normal_302_is_satisfied(self):
        self.assertEqual(redirect_wait_satisfied(302, headers('0')),
            {'retry_after_state':'zero_delay_satisfied','minimum_delay_seconds':0})
        for code in (301,302,303,307,308):
            self.assertEqual(redirect_wait_satisfied(code,headers())['retry_after_state'],'absent')
            self.assertEqual(redirect_wait_satisfied(code,headers(' 00\t'))['minimum_delay_seconds'],0)

    def test_wait_invalid_duplicates_and_final_statuses_hold(self):
        for value in ('1','60','-0','0.0','+0','','zero','Thu, 19 Nov 2026 00:00:00 GMT','0, 0','\u0660'):
            with self.subTest(value=value),self.assertRaises(PublisherRedirectHold):
                redirect_wait_satisfied(302,headers(value))
        for values in (('0','0'),('0','1')):
            with self.assertRaises(PublisherRedirectHold):redirect_wait_satisfied(302,headers(*values))
        for status in (200,206,401,403,429,True):
            with self.assertRaises(PublisherRedirectHold):redirect_wait_satisfied(status,headers('0'))
        with self.assertRaises(PublisherRedirectHold):redirect_wait_satisfied(302,{'Retry-After':'0'})


if __name__=='__main__':unittest.main()
