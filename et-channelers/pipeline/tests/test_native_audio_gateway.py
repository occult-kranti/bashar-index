"""Only local HTTP fixture calls; no browsers, sources, Drive or GPU are used."""
import http.client
import json
import threading
import time
import unittest
from unittest.mock import patch

import test_native_audio_sink as f
import native_audio_gateway as g

ORIGIN='chrome-extension://'+'a'*32
TOKEN='offline-fixture-'+'x'*32

class HTTP(f.Fixtures):
    # Inherit real temp-root/resource/queue fixtures; run these gateway tests separately.
    def setUp(self):
        super().setUp();self.context=self.coordinator();self.c=self.context.__enter__()
        self.drive=f.Drive();self.gateway=g.Gateway(self.c,origin=ORIGIN,token=TOKEN,drive=self.drive)
        self.thread=threading.Thread(target=self.gateway.server.serve_forever,daemon=True);self.thread.start()
    def tearDown(self):
        self.gateway.server.shutdown();self.thread.join(2);self.gateway.close();self.context.__exit__(None,None,None);super().tearDown()
    def request(self,path,value=None,*,method='POST',headers=None,raw=None):
        body=raw if raw is not None else json.dumps(value or {}).encode()
        h={'Origin':ORIGIN,'Authorization':'Bearer '+TOKEN,'Content-Type':'application/json','Content-Length':str(len(body))}
        h.update(headers or {})
        conn=http.client.HTTPConnection('127.0.0.1',self.gateway.port,timeout=3)
        conn.request(method,path,body=body if method!='GET' else None,headers=h);response=conn.getresponse();data=response.read();conn.close()
        return response.status,json.loads(data) if data else {}
    def admission(self):
        identity=f.selected();identity.pop('transportKind')
        return {'identity':identity,'transportKind':'direct_http','outputBudgetBytes':8,'metadata':{'id':f.VIDEO,'title':'Invented fixture'}}
    def test_http_origin_host_and_bearer_fail_closed(self):
        for headers in ({'Origin':'https://example.com'},{'Host':'localhost:'+str(self.gateway.port)},{'Authorization':'Bearer incorrect'}):
            try:
                status,_=self.request('/v1/begin',self.admission(),headers=headers);self.assertEqual(status,403)
            except ConnectionError:
                pass  # Windows may reset a denied connection with an unread body.
        self.assertEqual(self.c.states(),[])
    def test_http_idempotent_activation_pair_and_minimal_health(self):
        status,value=self.request('/health',method='GET',headers={'Authorization':''})
        self.assertEqual(status,200);self.assertNotIn('token',value)
        status,value=self.request('/v1/pair',{'explicitUserActivation':False},headers={'Authorization':''})
        self.assertEqual(status,409)
        status,value=self.request('/v1/pair',{'explicitUserActivation':True},headers={'Authorization':''})
        self.assertEqual(status,200);self.assertEqual(value['token'],TOKEN)
        status,value=self.request('/v1/pair',{'explicitUserActivation':True},headers={'Authorization':''})
        self.assertEqual(status,200);self.assertEqual(value['token'],TOKEN)
    def test_http_pairing_wrong_origin_cannot_get_token(self):
        status,value=self.request('/v1/pair',{'explicitUserActivation':True},headers={'Authorization':'','Origin':'https://evil.example'})
        self.assertEqual(status,403);self.assertNotIn('token',value);self.assertFalse(self.gateway.paired)
    def test_authenticated_status_only_may_omit_origin(self):
        _,begin=self.request('/v1/begin',self.admission());path='/v1/jobs/'+begin['jobId']+'/status'
        def call(route=path,method='GET',headers=None):
            conn=http.client.HTTPConnection('127.0.0.1',self.gateway.port,timeout=3)
            h={'Authorization':'Bearer '+TOKEN,'Content-Length':'0'};h.update(headers or {})
            conn.request(method,route,headers=h);response=conn.getresponse();status=response.status;body=json.loads(response.read());conn.close()
            return status,body
        status,body=call();self.assertEqual(status,200);self.assertEqual(body['sourceBindingSha256'],begin['sourceBindingSha256'])
        for headers in ({'Authorization':'Bearer incorrect'},{'Origin':'null'},{'Origin':'https://wrong.example'},
                        {'Host':'localhost:'+str(self.gateway.port)}):
            self.assertEqual(call(headers=headers)[0],403)
        self.assertEqual(call('/v1/pair',method='POST')[0],403)
        self.assertEqual(call('/health')[0],403)
        self.assertEqual(call(method='OPTIONS',headers={'Access-Control-Request-Method':'GET'})[0],403)
    def test_http_rejects_transport_secrets_without_job(self):
        value=self.admission();value['metadata']['url']='https://googlevideo.com/videoplayback?pot=secret'
        status,result=self.request('/v1/begin',value);self.assertEqual(status,409);self.assertEqual(result['error'],'transport_material_forbidden')
        self.assertEqual(self.c.states(),[])
    def test_public_thumbnail_url_requires_exact_structure_and_static_host(self):
        g.public_payload({'metadata':{'thumbnails':[{'url':'https://i.ytimg.com/vi/abcdefghijk/default.jpg','width':120,'height':90}]}})
        for value in ({'url':'https://i.ytimg.com/default.jpg'}, {'metadata':{'url':'https://i.ytimg.com/default.jpg'}},
                {'metadata':{'thumbnails':[{'url':'https://rr.googlevideo.com/videoplayback'}]}},
                {'metadata':{'thumbnails':[{'url':'https://i.ytimg.com/default.jpg?signature=secret'}]}},
                {'metadata':{'thumbnails':[{'url':'https://user@i.ytimg.com/default.jpg'}]}},
                {'metadata':{'thumbnails':[{'url':'https://i.ytimg.com:443/default.jpg'}]}},
                {'metadata':{'thumbnails':[{'url':'https://i.ytimg.com/default.jpg#fragment'}]}}):
            with self.assertRaises(f.n.SinkError):g.public_payload(value)
    def test_http_duplicate_json_keys_rejected(self):
        status,result=self.request('/v1/begin',raw=b'{"identity":{},"identity":{}}')
        self.assertEqual(status,409);self.assertEqual(result['error'],'duplicate_json_key')
    def test_http_chunk_limit_and_sequence(self):
        status,result=self.request('/v1/begin',self.admission());self.assertEqual(status,201);job=result['jobId']
        headers={'Content-Type':'application/octet-stream','X-Native-Offset':'0','X-Native-Seq':'1'}
        status,result=self.request('/v1/jobs/'+job+'/chunk',raw=b'12345678',headers=headers);self.assertEqual(status,409)
        headers['X-Native-Seq']='0'
        status,result=self.request('/v1/jobs/'+job+'/chunk',raw=b'12345678',headers=headers);self.assertEqual(status,200);self.assertEqual(result['acknowledgedBytes'],8)
    def test_http_finish_queues_proof_and_status_only_completes_after_drive(self):
        _,result=self.request('/v1/begin',self.admission());job=result['jobId'];binding=result['sourceBindingSha256']
        self.request('/v1/jobs/'+job+'/chunk',raw=b'12345678',headers={'Content-Type':'application/octet-stream','X-Native-Offset':'0','X-Native-Seq':'0'})
        status,result=self.request('/v1/jobs/'+job+'/finish',{'sourceBindingSha256':binding,'bytes':8,'protocolEos':True,'reencoded':False})
        self.assertEqual(status,202);self.assertFalse(result['driveVerified'])
        self.gateway.validating[job].result(timeout=2)
        self.gateway.pending[job].result(timeout=2)
        status,result=self.request('/v1/jobs/'+job+'/status',method='GET')
        self.assertTrue(result['driveVerified']);self.assertEqual(self.drive.copy_calls,1)
    def test_http_lost_finish_ack_repost_does_not_validate_or_upload_twice(self):
        _,result=self.request('/v1/begin',self.admission());job=result['jobId'];binding=result['sourceBindingSha256']
        self.request('/v1/jobs/'+job+'/chunk',raw=b'12345678',headers={'Content-Type':'application/octet-stream','X-Native-Offset':'0','X-Native-Seq':'0'})
        completion={'sourceBindingSha256':binding,'bytes':8,'protocolEos':True,'reencoded':False}
        started,release=threading.Event(),threading.Event();calls=[];original=self.c.probe
        def slow(*args):calls.append(1);started.set();release.wait(2);return original(*args)
        self.c.probe=slow
        self.assertEqual(self.request('/v1/jobs/'+job+'/finish',completion)[0],202);self.assertTrue(started.wait(1))
        self.assertEqual(self.request('/v1/jobs/'+job+'/finish',completion)[0],202)
        _,status=self.request('/v1/jobs/'+job+'/status',method='GET');self.assertFalse(status['driveVerified']);self.assertNotIn('nativeProof',status)
        release.set();self.gateway.validating[job].result(timeout=2);self.gateway.pending[job].result(timeout=2)
        self.assertEqual(calls,[1]);self.assertEqual(self.drive.copy_calls,1)
        changed={**completion,'protocolEos':False}
        self.assertEqual(self.request('/v1/jobs/'+job+'/finish',changed)[0],409)
    def test_http_wrong_video_binding_does_not_start_source(self):
        value=self.admission();value['identity']['videoId']='zzzzzzzzzzz'
        status,result=self.request('/v1/begin',value);self.assertEqual(status,409);self.assertEqual(result['error'],'not_in_queue')
    def test_http_binary_oversize_is_rejected_before_sink(self):
        _,result=self.request('/v1/begin',self.admission());job=result['jobId']
        headers={'Content-Type':'application/octet-stream','X-Native-Offset':'0','X-Native-Seq':'0','Content-Length':str(f.n.MAX_CHUNK+1)}
        status,result=self.request('/v1/jobs/'+job+'/chunk',raw=b'x',headers=headers)
        self.assertEqual(status,409);self.assertEqual(result['error'],'request_too_large')

# Reuse setup/helpers without rerunning the parent's tests inside this HTTP server fixture.
for name in list(vars(f.Fixtures)):
    if name.startswith('test_') and name not in HTTP.__dict__:setattr(HTTP,name,None)

if __name__=='__main__':unittest.main()
