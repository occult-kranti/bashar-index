"""Versioned additive 'Latest 20+ videos' selection and receipt reconciliation.

Reads metadata only. No discovery, media/Drive requests, ASR or GPU activity.
Fresh regular Videos membership never removes a previous recording or fills a
short grid using Shorts. Retained uploader uncertainty stays explicit.
"""
from __future__ import annotations
import argparse
from collections import Counter,defaultdict
from copy import deepcopy
import csv,datetime as dt,hashlib,io,json,re,sys
from pathlib import Path

ID=re.compile(r'[A-Za-z0-9_-]{11}');CHANNEL=re.compile(r'UC[A-Za-z0-9_-]{22}')
SLUG=re.compile(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,119}')
KINDS={'retained_mixed','retained_regular','retained_addition','fresh_regular','fresh_public_regular'}
TABS={'videos','shorts','streams','unknown'}
LABEL='Latest 20+ videos'

def require(value,reason):
    if not value:raise ValueError(reason)

def artifact(path):
    path=Path(path);raw=path.read_bytes()
    return {'path':str(path.resolve()),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}

def timestamp(value):
    if not isinstance(value,str):return None
    try:
        result=dt.datetime.fromisoformat(value.replace('Z','+00:00'))
        return result.astimezone(dt.timezone.utc) if result.tzinfo else None
    except ValueError:return None

def canonical_id(value):
    # The legacy public CSV uses a spreadsheet-safe quote before leading '-'.
    if isinstance(value,str) and value.startswith("'") and ID.fullmatch(value[1:]):return value[1:]
    return value

def read_retained(path,kind):
    require(kind in {'retained_mixed','retained_regular','retained_addition'},'Invalid retained membership')
    path=Path(path);raw=path.read_bytes();proof=artifact(path)
    if path.suffix.lower()=='.csv':
        rows=list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))));observed=None
    else:
        document=json.loads(raw.decode('utf-8-sig'))
        require(isinstance(document,dict),'Invalid retained selection')
        rows=document.get('rows');observed=document.get('observed_at',document.get('created_at',document.get('created')))
        if rows is None:
            rows=[]
            for group in document.get('channels',[]):
                for item in group.get('items',[]):
                    rows.append(dict(item,channel_dir=group['channel_dir'],expected_channel_id=item.get('expected_channel_id',item.get('channel_id',group.get('channel_id')))))
        require(isinstance(rows,list),'Retained selection has no recording rows')
        if 'row_count' in document:require(document['row_count']==len(rows),'Retained row count mismatch')
    require(len(rows)<=25_000,'Retained metadata scope too large')
    return {'kind':kind,'artifact':proof,'observed_at':observed,'rows':rows}

def _rank(row,fallback):
    value=row.get('listing_rank',row.get('selected_position_after_visible_exclusions',fallback))
    if isinstance(value,str) and value.isdigit():value=int(value)
    require(type(value) is int and value>=0,'Invalid source rank')
    return value

def _membership(row,kind,proof,observed,rank):
    channel=row.get('expected_channel_id',row.get('channel_id')) or None
    require(channel is None or isinstance(channel,str) and CHANNEL.fullmatch(channel),'Invalid retained uploader ID')
    tab=row.get('tab') or ('videos' if kind=='retained_regular' else 'unknown')
    require(tab in TABS,'Invalid source format')
    return {'kind':kind,'source':proof,'listing_rank':rank,
        'source_position':row.get('primary_grid_position',row.get('observed_playlist_position',row.get('source_position'))),
        'expected_channel_id':channel,'tab':tab,'title':row.get('title',''),
        'observed_at':row.get('observed_at') or observed,
        'publication_date':row.get('publication_date'),'published_at':row.get('published_at'),
        'date_quality':row.get('date_quality','unknown'),'date_display':row.get('date_display',row.get('publication_display')),
        'source_url':row.get('source_url'),'page_sha256':row.get('page_sha256',row.get('exact_date_evidence_sha256')),
        'access_status':row.get('access_status','unproven'),'regular_listing_rank':row.get('regular_listing_rank'),
        'duration_s':row.get('duration_s'),'duration_as_shown':row.get('duration_as_shown'),'publication_status':row.get('publication_status'),
        'prior_memberships':deepcopy(row.get('memberships',[])),'prior_scope_memberships':deepcopy(row.get('scope_memberships',[]))}

def build_selection(retained,fresh,*,fresh_artifact=None,primary_channels=None,earlier_cutoff=None,expected_creators=None):
    require(isinstance(fresh,dict) and fresh.get('schema_version')==1 and fresh.get('per_channel')==20,'Expected actual regular Videos crawl')
    groups=fresh.get('channels')
    if expected_creators is None and primary_channels is not None:
        expected_creators=len(primary_channels['channels'])
    require(isinstance(groups,list) and groups and (expected_creators is None or len(groups)==expected_creators),'Canonical creator count mismatch')
    primary={};order=[];observations={};uploader_owners={}
    for group in groups:
        slug=group.get('channel_dir');channel=group.get('channel_id')
        require(isinstance(slug,str) and SLUG.fullmatch(slug) and slug not in primary and group.get('creator',slug)==slug,'Invalid or duplicate canonical creator')
        require(isinstance(channel,str) and CHANNEL.fullmatch(channel) and channel not in uploader_owners,'Invalid or duplicate primary channel')
        require(group.get('state') in {'observed','absent','partial','unavailable'} and type(group.get('listing_complete')) is bool,'Missing observed grid completeness')
        primary[slug]=channel;uploader_owners[channel]=slug;order.append(slug)
        observations[slug]={k:deepcopy(group.get(k)) for k in ('state','listing_complete','observed_at','url')}
    if primary_channels is not None:
        mapping={r['creator']:r for r in primary_channels['channels']}
        require(set(mapping)==set(primary) and all(mapping[s]['channel_id']==primary[s] for s in primary),'Fresh grid differs from canonical primary creator map')
    rows={};source_counts=Counter();source_members=defaultdict(set)
    def add(row,kind,proof,observed,rank):
        slug=row.get('channel_dir');video=canonical_id(row.get('video_id'))
        require(slug in primary and isinstance(video,str) and ID.fullmatch(video),'Recording/creator identity mismatch')
        key=(slug,video);member=_membership(row,kind,proof,observed,rank)
        value=rows.setdefault(key,{'channel_dir':slug,'video_id':video,'memberships':[]})
        require(not any(m['kind']==kind and m['source']==proof for m in value['memberships']),'Duplicate recording in one source snapshot')
        value['memberships'].append(member);source_counts[kind]+=1;source_members[kind].add(key)
    for source in retained:
        require(source['kind'] in {'retained_mixed','retained_regular','retained_addition'},'Invalid retained source kind')
        by_creator=Counter()
        for row in source['rows']:
            slug=row.get('channel_dir');rank=_rank(row,by_creator[slug]);by_creator[slug]+=1
            add(row,source['kind'],source['artifact'],source.get('observed_at'),rank)
    retained_keys=set(rows)
    for group in groups:
        source=fresh.get('listing_sources_by_channel',{}).get(group['channel_dir'],fresh_artifact)
        items=group.get('items');require(isinstance(items,list) and len(items)<=20,'Fresh regular grid exceeds latest20')
        seen_positions=set();seen_ranks=set()
        for fallback,item in enumerate(items):
            require(item.get('channel_dir')==group['channel_dir'] and item.get('expected_channel_id')==group['channel_id'] and item.get('tab')=='videos','Fresh row is not from the canonical Videos grid')
            rank=_rank(item,fallback);position=item.get('primary_grid_position',rank)
            require(type(position) is int and position>=0 and position not in seen_positions and rank not in seen_ranks,'Duplicate/invalid fresh grid position')
            seen_positions.add(position);seen_ranks.add(rank)
            add(item,'fresh_regular',source,group.get('observed_at',fresh.get('observed_at')),rank)
        observations[group['channel_dir']]['fresh_regular_count']=len(items)
        public=group.get('public_items',[]);require(isinstance(public,list) and len(public)<=20,'Public regular grid exceeds latest20')
        for rank,item in enumerate(public):
            require(item.get('channel_dir')==group['channel_dir'] and item.get('expected_channel_id')==group['channel_id'] and item.get('tab')=='videos' and item.get('access_status')=='public_listing','Invalid public regular priority row')
            add(item,'fresh_public_regular',source,group.get('observed_at',fresh.get('observed_at')),_rank(item,rank))
        observations[group['channel_dir']].update(public_regular_count=len(public),public_listing_complete=group.get('public_listing_complete'))
    access={}
    for group in groups:
        for item in group.get('observed_items',group['items']):
            if item.get('access_status') in {'members_only','public_listing'}:
                access[(group['channel_dir'],item['video_id'])]={'status':item['access_status'],'source':fresh_artifact,'page_sha256':item.get('page_sha256'),'observed_at':item.get('observed_at',group.get('observed_at')),'primary_grid_position':item.get('primary_grid_position')}
    cutoff=timestamp(earlier_cutoff);kinds_order={'fresh_public_regular':0,'fresh_regular':1,'retained_mixed':2,'retained_regular':3,'retained_addition':4}
    by_creator=defaultdict(list)
    for key,value in rows.items():
        members=value['memberships'];ordered=sorted(members,key=lambda m:(kinds_order[m['kind']],m['listing_rank']))
        selected=next((m for m in ordered if m['tab']!='unknown'),ordered[0])
        known_ids=sorted({m['expected_channel_id'] for m in members if m['expected_channel_id']})
        observed=sorted({m['observed_at'] for m in members if timestamp(m['observed_at'])},key=timestamp)
        fresh_members=[m for m in members if m['kind'] in {'fresh_regular','fresh_public_regular'}]
        posted=None;posting_basis=None
        for m in fresh_members:
            published=timestamp(m['published_at'])
            if cutoff and published:posted=published>cutoff;posting_basis='literal_absolute_publication_timestamp'
            elif cutoff and m['date_quality'] in {'exact','absolute','literal_absolute'} and isinstance(m['publication_date'],str):
                try:day=dt.date.fromisoformat(m['publication_date'])
                except ValueError:continue
                if day!=cutoff.date():posted=day>cutoff.date();posting_basis='literal_absolute_publication_date'
        flags={kind:any(m['kind']==kind for m in members) for kind in KINDS}
        current_access=access.get(key,{'status':'unproven'});restricted=current_access['status']=='members_only'
        band=4 if restricted else 0 if flags['fresh_public_regular'] or flags['fresh_regular'] else 1 if flags['retained_regular'] else 2 if selected['tab']=='videos' else 3
        rank=min(m['listing_rank'] for m in members if m['kind']==('fresh_public_regular' if flags['fresh_public_regular'] else 'fresh_regular' if flags['fresh_regular'] else 'retained_regular' if flags['retained_regular'] else selected['kind']))
        value.update(expected_channel_id=known_ids[0] if len(known_ids)==1 else None,known_source_channel_ids=known_ids,current_primary_channel_id=primary[value['channel_dir']],uploader_identity_conflict=len(known_ids)>1,
            tab=selected['tab'],tabs_observed=sorted({m['tab'] for m in members}),title=selected['title'],listing_rank=rank,source_channel_name=value['channel_dir'],
            duration_s=selected['duration_s'],duration_as_shown=selected['duration_as_shown'],publication_status=selected['publication_status'],
            scope_memberships=sorted({m['kind'] for m in members}),newly_observed=bool(fresh_members) and key not in retained_keys,
            demonstrably_newly_posted_after_cutoff=posted,new_posting_evidence_basis=posting_basis,
            earliest_known_observed_at=observed[0] if observed else None,latest_known_observed_at=observed[-1] if observed else None,
            earlier_posting_cutoff=earlier_cutoff,priority_band=band,priority_reason=('fresh_public_regular_videos' if band==0 and flags['fresh_public_regular'] else 'fresh_regular_videos' if band==0 else 'retained_regular_videos' if band==1 else 'retained_other_videos' if band==2 else 'retained_supplementary_recording' if band==3 else 'retained_members_only_not_public_dispatch'),
            access_status=current_access['status'],current_access_evidence=current_access,public_media_dispatch_excluded=restricted,
            url='https://www.youtube.com/watch?v='+value['video_id'],fresh_selection_still_required=True,source_ready=False,**flags)
        by_creator[value['channel_dir']].append(value)
    # Fair rounds within each priority band; retained Shorts/streams remain queued.
    ordered=[]
    for band in range(5):
        queues={s:sorted([r for r in by_creator[s] if r['priority_band']==band],key=lambda r:(r['listing_rank'],r['video_id'])) for s in order}
        for rank in range(max((len(q) for q in queues.values()),default=0)):
            for slug in order:
                if rank<len(queues[slug]):ordered.append(queues[slug][rank])
    for rank,row in enumerate(ordered):row['priority_position']=rank
    channels=[]
    for slug in order:
        count=observations[slug]['fresh_regular_count'];channels.append(dict(channel_dir=slug,channel_id=primary[slug],selected=len(by_creator[slug]),fresh_regular_shortfall=max(0,20-count),**observations[slug]))
    return {'schema_version':1,'selection_kind':'additive_latest20plus_videos_v1','label':LABEL,'Source_authorized':False,'Drive_authorized':False,'latest_regular_per_creator':20,'row_count':len(ordered),'creator_count':len(primary),
        'channels':channels,'rows':ordered,'observed_primary_grid_index':[deepcopy(item) for group in groups for item in group.get('observed_items',group['items'])],
        'sources':[{'kind':s['kind'],'artifact':s['artifact'],'observed_at':s.get('observed_at')} for s in retained]+[{'kind':'fresh_regular','artifact':fresh_artifact,'observed_at':fresh.get('observed_at')}],
        'summary':{'unique_recordings':len(ordered),'fresh_regular_recordings':len(source_members['fresh_regular']),'retained_regular_recordings':len(source_members['retained_regular']),'retained_mixed_recordings':len(source_members['retained_mixed']),
            'public_regular_priority_recordings':len(source_members['fresh_public_regular']),'public_regular_fill_ins':sum(r['fresh_public_regular'] and not r['fresh_regular'] for r in ordered),
            'literal_latest20_members_only':sum(r['fresh_regular'] and r['public_media_dispatch_excluded'] for r in ordered),'retained_members_only_in_union':sum(r['public_media_dispatch_excluded'] for r in ordered),'visible_members_only_in_index':sum(v['status']=='members_only' for v in access.values()),
            'retained_additional_recordings':len(source_members['retained_addition']),'newly_observed_recordings':sum(r['newly_observed'] for r in ordered),'demonstrably_newly_posted_after_cutoff':sum(r['demonstrably_newly_posted_after_cutoff'] is True for r in ordered),'fresh_posting_time_unproven':sum(r['fresh_regular'] and r['demonstrably_newly_posted_after_cutoff'] is None for r in ordered),
            'format_counts':dict(Counter(r['tab'] for r in ordered)),'fresh_grid_shortfalls_never_filled_from_shorts':sum(20-c['fresh_regular_count'] for c in channels),'uploader_unknown_or_conflicting':sum(not r['expected_channel_id'] for r in ordered)},
        'completion_policy':'verified chosen native, qualified or independent publisher audio only; unavailable remains separate'}

def verified_counts(selection,root,remote='etdrive:04 Audio'):
    """Reuse the established strict paired receipt readers; no ownership probes."""
    try:from . import ingestion_status as status,drive_ingest as storage
    except ImportError:
        sys.path.insert(0,str(Path(__file__).resolve().parent))
        import ingestion_status as status
        import drive_ingest as storage
    root=Path(root);rows=selection['rows'];targets={r['video_id'] for r in rows};native=status.latest_records(root/'sync/drive_ingest_manifest.jsonl')
    native_keys={(r['channel_dir'],r['video_id']) for r in rows if r['video_id'] in native and native[r['video_id']].get('channel_dir')==r['channel_dir'] and status.proof(storage.receipt_complete,native[r['video_id']],r,remote)}
    qualified=set()
    path=root/'sync/progressive_audio_extracts_manifest.jsonl'
    if path.exists():
        require(path.stat().st_size<=64_000_000,'Qualified receipt inventory exceeds bound')
        owners={(r['channel_dir'],r['video_id']):r for r in rows}
        with path.open(encoding='utf-8-sig') as handle:
            for line in handle:
                require(len(line)<=2_000_000,'Qualified receipt line exceeds bound')
                try:
                    record=json.loads(line);reader=status.qualified_direct_audio_receipts if record.get('source_format_id')=='140' else status.qualified_edition_receipts
                    edition=reader.validate(record,remote_base=remote);key=(edition.channel_dir,edition.video_id)
                    if key in owners and record.get('tab') in owners[key]['tabs_observed']:qualified.add(key)
                except (ValueError,KeyError,TypeError,OverflowError):continue
    publisher=set()
    # Tab membership is retained, so a proven existing edition cannot be lost
    # merely because a later canonical Videos grid changes the display category.
    for tab in ('videos','shorts','streams','unknown'):
        subset=[dict(r,tab=tab) for r in rows if tab in r['tabs_observed']]
        if not subset:continue
        subset_ids={r['video_id'] for r in subset}
        _,_,variants,_,_=status.publisher_coverage(root,subset_ids,remote,target_rows=subset)
        mirrors,*_=status.publisher_mirror_evidence(root,subset_ids,remote,target_rows=subset)
        publisher.update((r['channel_dir'],r['video_id']) for r in subset if r['video_id'] in variants|mirrors)
    available=native_keys|qualified|publisher
    unavailable={(r['channel_dir'],r['video_id']) for r in rows if r['video_id'] in native and native[r['video_id']].get('channel_dir')==r['channel_dir'] and status.terminal_unavailable(native[r['video_id']])}-available
    values=[];creator_counts=[]
    for r in rows:
        key=(r['channel_dir'],r['video_id']);values.append(dict(channel_dir=key[0],video_id=key[1],verified_audio=key in available,native_audio=key in native_keys,qualified_audio=key in qualified,independent_publisher_audio=key in publisher,unavailable=key in unavailable,fresh_regular=r['fresh_regular'],fresh_public_regular=r['fresh_public_regular'],members_only=r['public_media_dispatch_excluded']))
    for channel in selection['channels']:
        own=[r for r in values if r['channel_dir']==channel['channel_dir']];fresh=[r for r in own if r['fresh_regular']]
        public=[r for r in own if r['fresh_public_regular']]
        creator_counts.append(dict(channel_dir=channel['channel_dir'],target=len(own),verified_audio=sum(r['verified_audio'] for r in own),remaining=sum(not r['verified_audio'] for r in own),fresh_regular_target=len(fresh),fresh_regular_verified=sum(r['verified_audio'] for r in fresh),public_regular_target=len(public),public_regular_verified=sum(r['verified_audio'] for r in public),restricted_remaining=sum(r['members_only'] and not r['verified_audio'] for r in own),unavailable=sum(r['unavailable'] for r in own)))
    return {'schema_version':1,'label':LABEL,'rows':values,'channels':creator_counts,'summary':{'target':len(rows),'verified_audio':len(available),'remaining':len(rows)-len(available),'unavailable_not_completion':len(unavailable),'native_audio':len(native_keys),'qualified_only':len(qualified-native_keys-publisher),'publisher_only':len(publisher-native_keys),'fresh_regular_target':sum(r['fresh_regular'] for r in rows),'fresh_regular_verified':sum(r['verified_audio'] and r['fresh_regular'] for r in values),'public_regular_target':sum(r['fresh_public_regular'] for r in rows),'public_regular_verified':sum(r['verified_audio'] and r['fresh_public_regular'] for r in values),'restricted_remaining':sum(r['members_only'] and not r['verified_audio'] for r in values)},'Source_calls':0,'Drive_calls':0}

def apply_publication_overlay(selection,records,proof,cutoff=None):
    """Attach existing verified metadata dates; target/order/eligibility do not change."""
    result=deepcopy(selection);creators={r['channel_dir']:r['channel_id'] for r in result['channels']}
    by_key={};boundary=timestamp(cutoff)
    if cutoff is not None:
        require(boundary is not None,'Historical comparison timestamp must include a timezone')
    for entry in records:
        key=(entry.get('channel_dir'),entry.get('video_id'))
        require(key not in by_key and key[0] in creators and entry.get('channel_id')==creators[key[0]] and ID.fullmatch(str(key[1])),'Publication overlay identity mismatch')
        by_key[key]=entry
    def annotate(row):
        entry=by_key.get((row.get('channel_dir'),row.get('video_id')))
        if entry is None:return
        published=entry.get('publication_or_upload') or {};value=published.get('value');precision=published.get('precision')
        watch=entry.get('public_watch_evidence') or {}
        reference={'overlay':proof,'row_channel_dir':entry['channel_dir'],'row_video_id':entry['video_id'],'public_watch_file':watch.get('file'),'public_watch_sha256':watch.get('sha256')}
        row.update(publication_date=value[:10] if isinstance(value,str) else None,published_at=value if precision=='instant' else None,publication_date_quality=entry.get('date_quality','unknown'),publication_date_basis=entry.get('date_basis','unknown'),publication_date_evidence=reference,publication_display=entry.get('displayed_age'))
        row['publication_display_conflict']=bool(entry.get('display_cutoff_evidence')=='display_indicates_recent' and entry.get('cutoff_class')=='at_or_before_cutoff')
    for row in result['rows']:annotate(row)
    for row in result['observed_primary_grid_index']:annotate(row)
    result['date_overlay']=proof
    if boundary is None:
        return result
    delta=[r for r in records if r.get('fresh_latest20') is True and r.get('distinct_vs_prior_regular') is True]
    for row in delta:
        instant=timestamp((row.get('publication_or_upload') or {}).get('value'))
        require(instant is not None and row.get('cutoff_class')==('after_cutoff' if instant>boundary else 'at_or_before_cutoff'),'Publication change annotation disagrees with exact timestamp')
    added=[r for r in delta if r.get('in_retained_nov19_mixed_latest20') is False]
    result['publication_change_audit']={'schema_version':1,'purpose':'ancillary prior-snapshot comparison only; never an eligibility or completion rule','overlay':proof,'prior_snapshot_boundary':cutoff,'delta_rows':delta,'summary':{'different_from_prior_regular':len(delta),'confirmed_after_prior_snapshot':sum(r['cutoff_class']=='after_cutoff' for r in delta),'older_than_prior_snapshot':sum(r['cutoff_class']=='at_or_before_cutoff' for r in delta),'new_to_both_prior_snapshots':len(added),'new_to_both_confirmed_after_snapshot':sum(r['cutoff_class']=='after_cutoff' for r in added)}}
    return result

def write_artifacts(selection,directory,counts=None):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=False)
    def emit(name,value):
        path=directory/name;path.write_text(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8');return artifact(path)
    selection=deepcopy(selection)
    audit=selection.pop('publication_change_audit',None)
    for row in selection['rows']:
        for key in ('earlier_posting_cutoff','demonstrably_newly_posted_after_cutoff','new_posting_evidence_basis'):row.pop(key,None)
    for key in ('demonstrably_newly_posted_after_cutoff','fresh_posting_time_unproven'):selection['summary'].pop(key,None)
    selection['primary_priority_label']='latest 20 regular uploads by sorted Videos-tab rank'
    selection['eligibility_date_or_duration_cutoff']=False
    selected=emit('selection.json',selection);coverage={(r['channel_dir'],r['video_id']):r for r in (counts or {}).get('rows',[])}
    index=emit('recording-index.json',{'schema_version':1,'selection':selected,'by_creator_video':{r['channel_dir']+'/'+r['video_id']:i for i,r in enumerate(selection['rows'])},'observed_primary_grid_index':selection['observed_primary_grid_index'],'extra_observations_not_automatically_selected_or_Source_ready':True})
    fields=['priority_position','priority_reason','channel_dir','expected_channel_id','video_id','url','title','tab','listing_rank','fresh_regular','fresh_public_regular','access_status','public_media_dispatch_excluded','duration_s','publication_date','published_at','publication_date_quality','publication_date_basis','publication_display_conflict','retained_regular','retained_mixed','retained_addition','newly_observed','earliest_known_observed_at','verified_audio','scope_memberships']
    with (directory/'priority.csv').open('w',encoding='utf-8',newline='') as out:
        writer=csv.DictWriter(out,fieldnames=fields);writer.writeheader()
        for row in selection['rows']:
            value={k:row.get(k) for k in fields};value['scope_memberships']='|'.join(row['scope_memberships']);value['verified_audio']=coverage.get((row['channel_dir'],row['video_id']),{}).get('verified_audio','');writer.writerow(value)
    runtime=[];conditional=[];held=[]
    for row in selection['rows']:
        if coverage.get((row['channel_dir'],row['video_id']),{}).get('verified_audio'):continue
        entry=dict(row,eligibility='members_only_not_public_dispatch' if row['public_media_dispatch_excluded'] else 'fresh_metadata_required' if row['expected_channel_id'] else 'uploader_identity_evidence_required',Source_authorized=False,Drive_authorized=False)
        (held if row['public_media_dispatch_excluded'] else conditional if not row['expected_channel_id'] else runtime).append(entry)
    registry=emit('runtime-intake.DISABLED.json',{'schema_version':1,'origin_kind':'additive_latest20plus_selection','selection':selected,'Source_authorized':False,'Drive_authorized':False,'source_ready':False,'item_count':len(runtime),'candidates':runtime,'conditional_uploader_rows':conditional,'held_members_only_rows':held,'total_missing':len(runtime)+len(conditional)+len(held),'provider_holds_and_fresh_dedup_are_external_mandatory_gates':True})
    summary={'schema_version':1,'label':LABEL,'primary_priority_label':selection['primary_priority_label'],'all_dates_and_durations_eligible':True,**selection['summary'],'verified_counts':counts['summary'] if counts else None,'channels':counts['channels'] if counts else selection['channels'],'selection_sha256':selected['sha256']}
    public=emit('summary.json',summary)
    if counts:emit('verified-counts.json',counts)
    if audit:emit('publication-change-audit.json',audit)
    return {'selection':selected,'index':index,'priority':artifact(directory/'priority.csv'),'runtime':registry,'summary':public}

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--retained-mixed', required=True)
    p.add_argument('--retained-regular', required=True)
    p.add_argument('--retain', action='append', default=[])
    p.add_argument('--fresh-videos', required=True)
    p.add_argument('--primary-channels', required=True)
    p.add_argument('--compare-to-snapshot-at', dest='earlier_cutoff', help='Optional dated comparison against an earlier inventory for the change-audit export')
    p.add_argument('--earlier-cutoff', dest='earlier_cutoff', help=argparse.SUPPRESS)
    p.add_argument('--retained-regular-observed-at')
    p.add_argument('--date-overlay', help='Optional recorded date evidence for the selected videos')
    p.add_argument('--root')
    p.add_argument('--output', required=True)
    a=p.parse_args(argv)
    retained=[read_retained(a.retained_mixed,'retained_mixed'),read_retained(a.retained_regular,'retained_regular')]+[read_retained(path,'retained_addition') for path in a.retain]
    if a.retained_regular_observed_at:
        require(timestamp(a.retained_regular_observed_at) is not None,'Explicit retained observation timestamp must include timezone')
        retained[1]['observed_at']=a.retained_regular_observed_at
    fresh=json.loads(Path(a.fresh_videos).read_bytes());primary=json.loads(Path(a.primary_channels).read_bytes())
    selection=build_selection(retained,fresh,fresh_artifact=artifact(a.fresh_videos),primary_channels=primary,earlier_cutoff=a.earlier_cutoff)
    if a.date_overlay:
        records=[json.loads(line) for line in Path(a.date_overlay).read_text(encoding='utf-8').splitlines() if line.strip()]
        selection=apply_publication_overlay(selection,records,artifact(a.date_overlay),a.earlier_cutoff)
    counts=verified_counts(selection,a.root) if a.root else None
    print(json.dumps(write_artifacts(selection,a.output,counts),sort_keys=True))
if __name__=='__main__':main()
