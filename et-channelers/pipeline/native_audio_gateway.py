"""Authenticated loopback bridge for admitted native audio bytes; inert on import.

The extension keeps source URLs, browser session material and PO tokens in its
accepted browser context. Only safe format identity, public metadata, bounded
binary chunks and segment proofs cross this interface. There is no capture API.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import hashlib
import os
from pathlib import Path
import re
import secrets
import sys
import threading
from urllib.parse import urlsplit

if __name__=='__main__':sys.path.insert(0,str(Path(__file__).resolve().parent))
import native_audio_sink as native

MAX_JSON=1_048_576
JOB=re.compile(r'/v1/jobs/(native-[a-f0-9]{24})/(request|chunk|segment|finish|retain|publish|status)\Z')
FORBIDDEN_KEYS={'url','serverabrstreamingurl','server_abr_streaming_url','po_token','potoken','pot','visitor_data','visitordata',
    'cookie','cookies','authorization','headers','http_headers','request_headers','profile','browser_profile','config','ustreamerconfig','streamingconfig',
    'token','access_token','refresh_token','session','sessionid','visitorid','signature','client_secret','credentials'}


def public_payload(value,path=()):
    if isinstance(value,dict):
        for key,item in value.items():
            if key=='url' and len(path)==3 and path[:2]==('metadata','thumbnails') and type(path[2]) is int:
                try:
                    url=urlsplit(item)
                    allowed=url.scheme=='https' and bool(url.hostname) and url.hostname.lower().endswith('.ytimg.com') and \
                        not url.username and not url.password and url.port is None and not url.query and not url.fragment
                except (ValueError,TypeError,AttributeError):allowed=False
                native.need(allowed,'public_thumbnail_url_required')
                continue
            native.need(str(key).lower() not in FORBIDDEN_KEYS,'transport_material_forbidden')
            public_payload(item,path+(key,))
    elif isinstance(value,list):
        for index,item in enumerate(value):public_payload(item,path+(index,))
    elif isinstance(value,str):
        native.need(not re.search(r'(?i)(googlevideo\.com|/videoplayback|/timedtext|/youtubei/|\bbearer\s+[A-Za-z0-9])',value),'transport_material_forbidden')


def json_object(pairs):
    result={}
    for key,value in pairs:
        native.need(key not in result,'duplicate_json_key');result[key]=value
    return result


class Gateway:
    def __init__(self,coordinator,*,origin,token=None,drive,port=0):
        token=token or secrets.token_urlsafe(32)
        native.need(re.fullmatch(r'chrome-extension://[a-p]{32}',origin),'extension_origin')
        native.need(isinstance(token,str) and re.fullmatch(r'[A-Za-z0-9_-]{32,256}',token),'memory_token_policy')
        self.coordinator=coordinator;self.origin=origin;self._token=token;self.drive=drive
        self.pair_lock=threading.Lock();self.paired=False
        self.uploads=ThreadPoolExecutor(max_workers=2,thread_name_prefix='native-pair-upload')
        self.validations=ThreadPoolExecutor(max_workers=2,thread_name_prefix='native-validate')
        self.upload_lock=threading.RLock();self.pending={};self.validating={};self.errors={}
        gateway=self

        class Server(ThreadingHTTPServer):
            daemon_threads=True
            allow_reuse_address=False
            def __init__(self,*args):self.slots=threading.BoundedSemaphore(8);super().__init__(*args)
            def process_request(self,request,address):
                if not self.slots.acquire(blocking=False):request.close();return
                try:super().process_request(request,address)
                except BaseException:self.slots.release();raise
            def process_request_thread(self,request,address):
                try:super().process_request_thread(request,address)
                finally:self.slots.release()

        class Handler(BaseHTTPRequestHandler):
            protocol_version='HTTP/1.0'
            def log_message(self,*args):pass  # never log headers, payloads, tokens or source metadata
            def setup(self):super().setup();self.connection.settimeout(10)
            def reply(self,code,value):
                raw=native.raw_json(value)
                self.send_response(code);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)))
                self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff')
                if self.headers.get('Origin')==gateway.origin:self.send_header('Access-Control-Allow-Origin',gateway.origin)
                self.send_header('Vary','Origin');self.end_headers()
                try:self.wfile.write(raw)
                except (BrokenPipeError,ConnectionResetError):pass
            def authenticate(self,preflight=False):
                native.need(len(self.headers.get_all('Host',[]))==1,'request_origin')
                native.need(self.client_address[0]=='127.0.0.1' and self.headers['Host']==gateway.host,'request_origin')
                origins=self.headers.get_all('Origin',[]);native.need(len(origins)<=1,'request_origin')
                if origins:
                    native.need(origins[0]==gateway.origin,'request_origin')
                else:
                    route=JOB.fullmatch(self.path)
                    native.need(not preflight and self.command=='GET' and route is not None and route.group(2)=='status','request_origin')
                if not preflight:
                    native.need(len(self.headers.get_all('Authorization',[]))==1,'unauthorized')
                    native.need(secrets.compare_digest(self.headers['Authorization'],'Bearer '+gateway._token),'unauthorized')
            def body(self,binary=False):
                native.need(not self.headers.get('Transfer-Encoding') and self.headers.get('Content-Encoding','identity')=='identity','request_encoding')
                lengths=self.headers.get_all('Content-Length',[]);native.need(len(lengths)==1 and lengths[0].isdigit(),'request_length')
                size=int(lengths[0]);native.need(0<size<=(native.MAX_CHUNK if binary else MAX_JSON),'request_too_large')
                need_type='application/octet-stream' if binary else 'application/json'
                native.need(self.headers.get('Content-Type','').split(';')[0]==need_type,'request_content_type')
                raw=self.rfile.read(size);native.need(len(raw)==size,'request_truncated')
                if binary:return raw
                value=json.loads(raw.decode('utf-8'),object_pairs_hook=json_object,parse_constant=lambda _:(_ for _ in ()).throw(native.SinkError('nonfinite_json')))
                native.need(isinstance(value,dict),'json_object_required');public_payload(value);return value
            def handle_call(self):
                try:
                    if self.command=='GET' and self.path=='/health':
                        self.authenticate(preflight=True)
                        return self.reply(200,{'status':'native_gateway_ready','protocolVersion':1,'maxChunkBytes':native.MAX_CHUNK,'paired':gateway.paired})
                    if self.command=='POST' and self.path=='/v1/pair':
                        self.authenticate(preflight=True);value=self.body()
                        native.need(value=={'explicitUserActivation':True},'explicit_activation_required')
                        with gateway.pair_lock:
                            gateway.paired=True
                            return self.reply(200,{'token':gateway._token,'storage':'extension_memory_or_storage_session_only','protocolVersion':1})
                    self.authenticate();match=JOB.fullmatch(self.path)
                    if self.command=='POST' and self.path=='/v1/begin':
                        value=self.body();native.need(set(value)=={'identity','transportKind','outputBudgetBytes','metadata'},'begin_fields')
                        selected={**value['identity'],'transportKind':value['transportKind']}
                        sink=gateway.coordinator.begin(selected,value['metadata'],output_budget_bytes=value['outputBudgetBytes'])
                        state=sink.state();return self.reply(201,{'jobId':sink.job_id,'sourceBindingSha256':state['binding_sha256'],'acknowledgedBytes':0,'nextSequence':0,'maxChunkBytes':native.MAX_CHUNK,'segmentBoundaryVerified':False})
                    native.need(match is not None,'unknown_route');job,action=match.groups();sink=gateway.get_sink(job)
                    if self.command=='GET' and action=='status':return self.reply(200,gateway.status(job))
                    native.need(self.command=='POST' and action!='status','unknown_route')
                    if action=='chunk':
                        for name in ('X-Native-Offset','X-Native-Seq'):
                            values=self.headers.get_all(name,[]);native.need(len(values)==1 and values[0].isdigit(),'chunk_headers')
                        return self.reply(200,sink.write({'offset':int(self.headers['X-Native-Offset']),'seq':int(self.headers['X-Native-Seq']),'bytes':self.body(binary=True)}))
                    value=self.body()
                    if action=='request':return self.reply(200,sink.authorize_request(value))
                    if action=='segment':return self.reply(200,sink.segment(value))
                    if action=='finish':
                        gateway.submit_finish(job,value)
                        return self.reply(202,{'jobId':job,'sourceBindingSha256':sink.state()['binding_sha256'],'status':'validation_or_upload_queued','driveVerified':False})
                    if action=='retain':
                        native.need(set(value)=={'error_class'},'retain_fields');result=sink.retain(value['error_class'])
                        return self.reply(200,{**result,'stopAllSourceWorkers':gateway.coordinator.source_stop.is_set()})
                    if action=='publish':
                        native.need(value=={},'publish_fields');gateway.submit(job);return self.reply(202,{'uploadQueued':True})
                    raise native.SinkError('unknown_route')
                except native.SinkError as error:self.reply(403 if error.code in {'unauthorized','request_origin'} else 409,{'error':error.code})
                except (json.JSONDecodeError,UnicodeDecodeError,ValueError,TypeError,KeyError):self.reply(400,{'error':'invalid_request'})
                except TimeoutError:self.reply(408,{'error':'request_timeout'})
                except Exception:self.reply(503,{'error':'retained_internal_error'})
            def do_POST(self):self.handle_call()
            def do_GET(self):self.handle_call()
            def do_OPTIONS(self):
                try:
                    self.authenticate(preflight=True)
                    native.need(self.headers.get('Access-Control-Request-Method') in {'GET','POST'},'cors_method')
                    requested={x.strip().lower() for x in self.headers.get('Access-Control-Request-Headers','').split(',') if x.strip()}
                    native.need(requested<={'authorization','content-type','x-native-offset','x-native-seq'},'cors_headers')
                    self.send_response(204);self.send_header('Access-Control-Allow-Origin',gateway.origin)
                    self.send_header('Access-Control-Allow-Methods','GET, POST');self.send_header('Access-Control-Allow-Headers','Authorization, Content-Type, X-Native-Offset, X-Native-Seq')
                    self.send_header('Access-Control-Max-Age','0');self.send_header('Content-Length','0');self.end_headers()
                except native.SinkError:self.reply(403,{'error':'request_origin'})

        self.server=Server(('127.0.0.1',port),Handler);self.port=self.server.server_address[1];self.host='127.0.0.1:'+str(self.port)

    def get_sink(self,job):
        native.need(re.fullmatch(r'native-[a-f0-9]{24}',job),'unknown_job')
        path=self.coordinator.spool/'jobs'/job/'state.json';native.need(path.exists(),'unknown_job')
        state=native.read(path)
        native.need(state.get('owner')==self.coordinator.owner and state.get('queue_sha256')==native.digest(self.coordinator.queue_path)['sha256'],'job_owner_changed')
        return self.coordinator.live.get(job) or native.Sink(self.coordinator,job)

    def submit(self,job):
        with self.upload_lock:
            old=self.pending.get(job);native.need(old is None or old.done(),'upload_already_claimed')
            sink=self.get_sink(job);native.need(sink.state()['state'] in {'local_validated','verified_cleanup','publishing'},'not_validated')
            def publish():
                try:sink.publish(self.drive);self.errors.pop(job,None)
                except Exception as error:self.errors[job]=getattr(error,'kind','upload_failed_retained')
            self.pending[job]=self.uploads.submit(publish)

    def submit_finish(self,job,completion):
        with self.upload_lock:
            sink=self.get_sink(job);state=sink.state();raw=native.raw_json(completion)
            native.need(len(raw)<=16384,'finish_control_too_large')
            native.need(completion.get('sourceBindingSha256')==state['binding_sha256'] and completion.get('bytes')==state['offset'],'completion_identity')
            request=sink.folder/'completion.pending.json';fingerprint=hashlib.sha256(raw).hexdigest()
            if request.exists():native.need(native.read(request)==completion,'finish_request_changed')
            else:
                with self.coordinator.lock:
                    self.coordinator.inventory(extra=len(raw));state['reservation_bytes']+=len(raw)
                    native.atomic(request,completion);state['completion_request_sha256']=fingerprint;native.atomic(sink.folder/'state.json',state)
            if state['state']=='deleted':return
            if state['state'] in {'local_validated','publishing','verified_cleanup'}:
                old=self.pending.get(job)
                if old is None or old.done():self.submit(job)
                return
            old=self.validating.get(job)
            if old is not None and not old.done():return
            native.need(state['state'] in {'receiving','retained','validation_queued','validating'},'finish_state')
            state['state']='validation_queued';native.atomic(sink.folder/'state.json',state)
            def validate():
                try:sink.finish(completion);self.errors.pop(job,None);self.submit(job)
                except Exception as error:self.errors[job]=getattr(error,'kind','validation_failed_retained')
            self.validating[job]=self.validations.submit(validate)

    def status(self,job):
        state=self.get_sink(job).state()
        result={'jobId':job,'state':state['state'],'sourceBindingSha256':state['binding_sha256'],'acknowledgedBytes':state['offset'],'driveVerified':state['state']=='deleted',
                'sourceRequests':state.get('source_requests',0),'error':self.errors.get(job),'stopAllSourceWorkers':self.coordinator.source_stop.is_set()}
        if state['state'] in {'local_validated','publishing','verified_cleanup','deleted'} and state.get('record'):
            result['nativeProof']={key:state['record'][key] for key in ('bytes','md5','sha256')}
        return result

    def close(self):
        self.server.server_close();self.validations.shutdown(wait=True,cancel_futures=False);self.uploads.shutdown(wait=True,cancel_futures=False);self._token=''


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True);parser.add_argument('--queue',type=Path,required=True)
    parser.add_argument('--managed-root',action='append',type=Path,required=True);parser.add_argument('--owner',required=True)
    parser.add_argument('--lease-id',required=True);parser.add_argument('--remote',required=True);parser.add_argument('--ffprobe',required=True)
    parser.add_argument('--rclone',required=True);parser.add_argument('--origin',required=True);parser.add_argument('--port',type=int,default=8781)
    parser.add_argument('--token-env',default='NATIVE_SINK_TOKEN',help='Existing memory-only bearer environment variable; never printed or saved')
    args=parser.parse_args(argv);native.need(re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{0,79}',args.token_env),'token_env_name')
    token=os.environ.pop(args.token_env,None) or secrets.token_urlsafe(32)
    import drive_ingest as core
    from media_metadata import build_metadata
    drive=core.Rclone(args.rclone,cooldown_path=args.root/'sync/drive_ingest_cooldown.json')
    with native.Coordinator(args.root,owner=args.owner,lease_id=args.lease_id,queue_path=args.queue,managed_roots=args.managed_root,
            remote=args.remote,ffprobe=args.ffprobe,core=core,metadata_builder=build_metadata) as coordinator:
        gateway=Gateway(coordinator,origin=args.origin,token=token,drive=drive,port=args.port);token=None
        try:
            print(json.dumps({'status':'native_gateway_ready','port':gateway.port,'source_requests_started':False}),flush=True)
            gateway.server.serve_forever(poll_interval=.5)
        finally:gateway.close()

if __name__=='__main__':
    try:main()
    except KeyboardInterrupt:pass
    except Exception as error:
        print(json.dumps({'status':'not_started_or_retained','error':getattr(error,'kind','internal_error')}),flush=True);raise SystemExit(3)
