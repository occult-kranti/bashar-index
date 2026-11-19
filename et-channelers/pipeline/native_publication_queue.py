"""Archive independently validated native Sinks and expose per-recording outcomes."""
from types import SimpleNamespace

try:
    from . import grouped_publication as grouped, native_grouped_publication as native
except ImportError:
    import grouped_publication as grouped
    import native_grouped_publication as native


def _prior_verified(member):
    """Read a real canonical pair if local cleanup failed after journal commit."""
    sink=member.sink
    expected=member.record
    with sink.c.lock:
        old=sink.c.core.load_state(sink.c.root/'sync/drive_ingest_manifest.jsonl').get(expected['video_id'],{})
    if old.get('status') not in ('verified','deleted'):
        return None
    roles=((old,expected),(old.get('metadata',{}),expected['metadata']))
    required=('bytes','md5','sha256','path','remote')
    return old if (all(all(actual.get(k)==wanted.get(k) for k in required) for actual,wanted in roles)
                   and all(old.get(k)==expected.get(k) for k in ('queue_row','native_format_binding_sha256','native_validation'))
                   and all(isinstance(a.get('drive_id'),str) and a['drive_id'] for a,_ in roles)
                   and roles[0][0]['drive_id']!=roles[1][0]['drive_id']) else None


class _Publisher:
    def __init__(self,sink,record,drive):
        self.group_member=native.Member(sink,record)
        self.drive=drive

    def __call__(self,trace,*,group_evidence=None,group_error=None):
        sink=self.group_member.sink
        video=self.group_member.record['video_id']
        if not group_error:
            try:
                rec=sink.publish(self.drive,group_evidence=group_evidence)
                return {'video_id':video,'status':'paired_verified_deleted','canonical_pair':rec}
            except Exception as error:
                group_error=getattr(error,'kind',None) or getattr(error,'code',None) or type(error).__name__
        prior=_prior_verified(self.group_member)
        if prior is not None:
            return {'video_id':video,'status':'paired_verified_cleanup_held','canonical_pair':prior,'cleanup_error':group_error}
        return {'video_id':video,'status':'local_native_retained_publication_held','error_class':group_error}


def publish_ready(coordinator,sinks,drive,*,headroom,additional_guard=None):
    sinks=tuple(sinks)
    if (not 1<=len(sinks)<=6 or any(s.c is not coordinator for s in sinks)
            or len({s.job_id for s in sinks})!=len(sinks)):
        raise ValueError('expected one to six distinct validated Sinks from the same coordinator')
    def guard():
        coordinator.guard()
        if additional_guard is not None:additional_guard()
    guard()
    callbacks=[]
    no_trace=SimpleNamespace(mark=lambda phase:None)
    for s in sinks:
        state=s.state()
        if state['state'] not in ('local_validated','publishing','verified_cleanup'):
            raise ValueError('native Sink is not ready for upload')
        record=state['record']
        item=SimpleNamespace(key=record['video_id'])
        callbacks.append((item,SimpleNamespace(value=_Publisher(s,record,drive)),no_trace))

    def finish(item,result):
        return SimpleNamespace(verified=result['status'] in ('paired_verified_deleted','paired_verified_cleanup_held'),
                               proof=result)
    def single(item,acquired,trace):
        guard();return finish(item,acquired.value(trace))

    results=native.publish_callbacks(callbacks,once=single,finish=finish,drive=drive,guard=guard,
                                     staging=coordinator.spool/'publisher-ready',remote=coordinator.remote,headroom=headroom)
    return [grouped.PairPublication(i.key,'verified_cleanup_held' if result.proof['status']=='paired_verified_cleanup_held'
                else 'verified' if result.verified else 'retained',result.proof.get('canonical_pair'),
                result.proof.get('group_cleanup_error') or result.proof.get('cleanup_error') or result.proof.get('error_class'))
            for (i,_,_),result in zip(callbacks,results)]
