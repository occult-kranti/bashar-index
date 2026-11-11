#!/usr/bin/env python3
"""Package the current draft of the ET-channelers research: CSVs, plots, README, banner report, zip.
No network. Reads only local files produced earlier in this session."""
import re, json, csv, os, shutil, zipfile, collections, unicodedata, datetime

NOTES = '/home/claude/research_notes/ET channelers directory and timeline'
YT_JSON = '/home/claude/etc_site/data/youtube_index.json'
PARTS = '/home/claude/etc_site/data/_parts'
PKG = '/home/claude/work/data_pkg/package'
REPORT_SRC = '/home/claude/reports/ET channelers directory and timeline.md'
OUT = '/mnt/user-data/outputs/et-channelers-draft'
for d in ('csv', 'plots', 'notes', 'data'):
    os.makedirs(f'{OUT}/{d}', exist_ok=True)

NOTE_FILES = ['ra_material_and_prelude.md', 'majors_1985_2015.md', 'anka_bashar.md', 'krol_ashtar_lineage.md',
              'ellison_ryok_and_small_channels.md', 'youtube_era_channelers.md', 'reddit_wizardforums_balg.md',
              'entities_and_criticism.md']
texts = {f: open(f'{NOTES}/{f}', encoding='utf-8').read() for f in NOTE_FILES}
index = json.load(open(YT_JSON, encoding='utf-8'))
channels = index['channels']
stats = {}


# ---------- helpers ----------
def slug(s):
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c)).lower()
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')


def clean_name(n):
    n = re.sub(r'\s*[—–-]\s*(CONTACTEE|Bashar-adjacent|classify|dates and books|non-ET|contactee|NOT|Pleiadians on|the Zetas|origin|Blue Avian|mid-tier|legacy|Ashtar Sheran|Galactic Federation|Spanish|German|Brazil|Japan|Insight).*$', '', n)
    n = re.sub(r'\s*\((?!.*Cosmic Agency)[^)]*\)\s*$', '', n).strip()
    return n.strip('"')


MANUAL = {'Darryl Anka': 'darryl-anka', 'Athina Król': 'athina-krol', 'Tyler Ellison': 'tyler-ellison',
          'チャネラー純子': 'channeler-junko', '@thequantumbarbie': 'thequantumbarbie'}
REMAP = {'gosia-duszak-cosmic-agency-agencia-cosmica': 'cosmic-agency-gosia'}


def skip_heading(n):
    return 'NOT VERIFIED' in n or n.startswith('Names checked') or n.startswith('minor/other')


def person_id(heading):
    n = clean_name(heading)
    sid = MANUAL.get(n) or slug(n)
    return REMAP.get(sid, sid)


canon = {}
sec = None
for line in open(f'{NOTES}/CANONICAL_IDS.md', encoding='utf-8'):
    if line.startswith('## Person ids'):
        sec = 'person'
    elif line.startswith('## Entity ids'):
        sec = 'entity'
    m = re.match(r'- (\S+) \| (.+)$', line.strip())
    if m and sec == 'person':
        canon[m.group(1)] = m.group(2)


def tidy(s, limit=None):
    s = re.sub(r'\[([^\]]+)\]\((https?://[^)\s]+)\)', r'\1 <\2>', s)
    s = s.replace('**', '').replace('__', '')
    s = re.sub(r'\s+', ' ', s).strip()
    if limit and len(s) > limit:
        s = s[:limit - 2].rstrip() + ' […]'
    return s


def blocks(text, kind):
    ms = list(re.finditer(r'^## %s: (.+)$' % kind, text, re.M))
    res = []
    for m in ms:
        start = m.end()
        nxt = re.search(r'^## ', text[start:], re.M)
        end = start + nxt.start() if nxt else len(text)
        res.append((m.group(1).strip(), text[start:end]))
    return res


def make_matcher(labels):
    def match_label(line):
        s = line.rstrip()
        if s.startswith((' ', '\t')):
            return None
        s = re.sub(r'^[-*]\s+', '', s)
        for key, pat in labels:
            m = re.match(r'^\*\*\s*(?:%s)[^*]*\*\*\s*:?\s*(.*)$' % pat, s, re.I)
            if m:
                return key, m.group(1)
            m = re.match(r'^(?:%s)(?:\s*\([^)]*\))?\s*:\s*(.*)$' % pat, s, re.I)
            if m:
                return key, m.group(1)
            m = re.match(r'^(?:%s)(?:\s*\([^)]*\))?\s*$' % pat, s, re.I)
            if m:
                return key, ''
        return None
    return match_label


PERSON_LABELS = [('aliases', r'Aliases\s*/\s*handles'), ('entity', r'Entity channeled'), ('began', r'Channeling began'),
                 ('public', r'First public\s*/\s*known'), ('location', r'Location'), ('platforms', r'Platforms'),
                 ('method', r'Method'), ('claims', r'Core claims'), ('quotes', r'Notable quotes?'),
                 ('controversies', r'Verification\s*/\s*controversies'), ('confidence', r'Confidence'),
                 ('sources', r'Sources')]
ENTITY_LABELS = [('type', r'Type'), ('origin', r'Claimed origin'), ('density', r'Claimed density(?:\s*/\s*dimension)?'),
                 ('description', r'Description(?: claimed)?'), ('first', r'First (?:appearance|channeled[^:*]*?)'),
                 ('later', r'(?:Later|Principal later) channel(?:ers|s)'), ('distinct', r'Distinguishing claims'),
                 ('change', r'Change over time|How the portrayal changed[^:*]*|Portrayal change'),
                 ('sources', r'Sources')]
match_person = make_matcher(PERSON_LABELS)
match_entity = make_matcher(ENTITY_LABELS)


def parse_fields(body, matcher):
    cur = None
    fields = collections.defaultdict(list)
    for line in body.split('\n'):
        if line.lstrip().startswith('#'):
            continue
        r = matcher(line)
        if r:
            cur = r[0]
            if r[1].strip():
                fields[cur].append(r[1].strip())
        elif cur and line.strip() and set(line.strip()) != {'-'}:
            fields[cur].append(line.strip())
    return {k: tidy(' '.join(v)) for k, v in fields.items()}


def write_csv(path, header, rows):
    with open(path, 'w', encoding='utf-8-sig', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)
    return len(rows)


def cut(s, n):
    s = s or ''
    return s if len(s) <= n else s[:n - 2].rstrip() + ' […]'


# ---------- YouTube index -> CSVs ----------
yt_by_person = {c['person']: c for c in channels}
rows = []
for c in channels:
    ch = c.get('channel') or {}
    sm = c.get('summary') or {}
    sec_ch = '; '.join(f"{s.get('title')} <{s.get('url')}>" for s in (c.get('secondary_channels') or []))
    rows.append([c['person'], c.get('person_name'), c.get('role'), c['status'], c.get('original_status'),
                 ch.get('title'), ch.get('handle'), ch.get('channel_id'), ch.get('url'), c.get('subscribers'),
                 ch.get('subscriber_count_text'), c.get('video_count'), ch.get('video_count_text'),
                 ch.get('observed_at') or index.get('observed'), ch.get('source'), len(c.get('videos') or []),
                 sm.get('channeling_videos_in_recent') if sm.get('channeling_videos_in_recent') is not None else sm.get('channeling_videos'),
                 '; '.join(sm.get('entities_seen') or []), sec_ch, cut(c.get('status_note'), 300)])
stats['channels'] = write_csv(f'{OUT}/csv/youtube_channels.csv',
    ['person_id', 'person_name', 'role', 'index_status', 'original_status', 'channel_title', 'handle', 'channel_id',
     'channel_url', 'subscribers', 'subscribers_text', 'video_count', 'video_count_text', 'observed', 'data_source',
     'videos_in_sample', 'channeling_videos_in_sample', 'entities_seen', 'secondary_channels', 'status_note'], rows)

rows = []
index_video_ids = set()
for c in channels:
    ch = c.get('channel') or {}
    for v in (c.get('videos') or []):
        if v.get('video_id'):
            index_video_ids.add(v['video_id'])
        rows.append([c['person'], c.get('person_name'), c.get('role'), ch.get('handle'), c['status'], v.get('video_id'),
                     v.get('title'), v.get('url'), v.get('view_count_text'), v.get('published_text'),
                     v.get('published_date'), v.get('length_text'), v.get('is_channeling'), v.get('entity'),
                     v.get('note')])
stats['videos'] = write_csv(f'{OUT}/csv/youtube_videos.csv',
    ['person_id', 'person_name', 'role', 'channel_handle', 'index_status', 'video_id', 'title', 'url', 'views_as_displayed',
     'published_relative_as_of_2026-10-23', 'published_date', 'length', 'is_channeling', 'entity_named_in_title', 'note'], rows)

er = index.get('entity_rollup') or {}
rows = []
for k, v in (er.get('canonical') or {}).items():
    rows.append(['canonical', k, v.get('name'), v.get('videos'), v.get('channeling_videos'), '; '.join(v.get('people') or []),
                 '; '.join(v.get('raw_names') or [])])
canon_raw = {n for v in (er.get('canonical') or {}).values() for n in (v.get('raw_names') or [])}
for k, v in (er.get('raw') or {}).items():
    rows.append(['raw' + (' (also folded into a canonical id)' if k in canon_raw else ''), '', k, v.get('videos'),
                 v.get('channeling_videos'), '; '.join(v.get('people') or []), ''])
stats['entity_rollup'] = write_csv(f'{OUT}/csv/youtube_entity_rollup.csv',
    ['kind', 'entity_id', 'entity_name', 'videos', 'channeling_videos', 'people', 'raw_names'], rows)

# ---------- Bashar repo videos ----------
vids = json.load(open(f'{PKG}/videos.json', encoding='utf-8'))
cnt = collections.Counter(v.get('channel') for v in vids)
rows = sorted([[v.get('channel'), cnt[v.get('channel')], v.get('official'), v.get('content_type'), v.get('year'),
                v.get('year_reliable'), v.get('title'), v.get('url'), v.get('video_id'), v.get('format'),
                cut(v.get('session_date_or_event'), 220)] for v in vids],
              key=lambda r: (-r[1], r[0] or '', str(r[4])))
stats['bashar_repo'] = write_csv(f'{OUT}/csv/bashar_videos_in_repo_by_channel.csv',
    ['channel', 'videos_from_channel_in_repo', 'official', 'content_type', 'year', 'year_reliable', 'title', 'url',
     'video_id', 'format', 'session_date_or_event'], rows)
stats['bashar_channels'] = len(cnt)

# ---------- people directory ----------
people = {}
for f in NOTE_FILES:
    for heading, body in blocks(texts[f], 'Person'):
        if skip_heading(heading):
            continue
        pid = person_id(heading)
        fl = parse_fields(body, match_person)
        size = sum(len(v) for k, v in fl.items() if k != 'sources')
        rec = people.setdefault(pid, {'files': [], 'best': None, 'size': -1, 'heading': heading})
        rec['files'].append(f)
        if size > rec['size']:
            rec.update(best=fl, size=size, heading=heading)
rows = []
for pid, rec in sorted(people.items()):
    fl = rec['best']
    yt = yt_by_person.get(pid) or {}
    ch = yt.get('channel') or {}
    rows.append([pid, canon.get(pid) or clean_name(rec['heading']), rec['heading'], '; '.join(sorted(set(rec['files']))),
                 pid in canon, cut(fl.get('entity'), 700), cut(fl.get('began'), 450), cut(fl.get('public'), 450),
                 cut(fl.get('location'), 250), cut(fl.get('platforms'), 600), cut(fl.get('method'), 250),
                 cut(fl.get('confidence'), 350), cut(fl.get('aliases'), 500), yt.get('status'), ch.get('handle'),
                 ch.get('url'), yt.get('subscribers'), yt.get('video_count')])
stats['people'] = write_csv(f'{OUT}/csv/people_directory.csv',
    ['person_id', 'name', 'heading_in_notes', 'source_notes', 'id_in_canonical_list', 'entity_channeled',
     'channeling_began', 'first_public_or_known', 'location', 'platforms', 'method', 'confidence_and_gaps',
     'aliases_handles', 'youtube_index_status', 'youtube_handle', 'youtube_url', 'youtube_subscribers',
     'youtube_video_count'], rows)
empty_people = sum(1 for pid, rec in people.items() if not any(rec['best'].get(k) for k in ('entity', 'began', 'public')))
stats['people_empty_fields'] = empty_people

# ---------- entities (raw, unmerged) ----------
rows = []
for f in NOTE_FILES:
    for heading, body in blocks(texts[f], 'Entity'):
        fl = parse_fields(body, match_entity)
        empty = not any(fl.get(k) for k in ('type', 'origin', 'density', 'first'))
        rows.append([heading, f, cut(fl.get('type'), 160), cut(fl.get('origin'), 400), cut(fl.get('density'), 300),
                     cut(fl.get('first'), 450), cut(fl.get('later'), 450), cut(fl.get('distinct'), 500),
                     cut(tidy(body), 320) if empty else ''])
rows.sort(key=lambda r: r[0].lower())
stats['entities'] = write_csv(f'{OUT}/csv/entities_catalogue_raw.csv',
    ['entity_heading_in_notes', 'source_note', 'type', 'claimed_origin', 'claimed_density_or_dimension',
     'first_appearance_or_first_channeled', 'later_channelers', 'distinguishing_claims', 'excerpt_if_fields_unparsed'], rows)
stats['entities_unparsed'] = sum(1 for r in rows if r[-1])

# ---------- timeline ----------
FOCUS = [('ra', r"\bRa\b|Law of One|L/L|Elkins|Rueckert|McCarty|Q'uo"),
         ('bashar', r'Bashar|Anka|Essassani|Sassani'),
         ('ashtar', r'Ashtar|Kr[oó]l|Van Tassel'),
         ('ryok', r'Ryok|Ellison|Galactic Guide')]


def bucket(y):
    if y < 1981: return '1 before the Ra contact (pre-1981)'
    if y <= 1990: return '2 1981-1990'
    if y <= 2000: return '3 1991-2000'
    if y <= 2011: return '4 2001-2011'
    if y <= 2019: return '5 2012-2019'
    return '6 2020-2026'


tl = {}
for f in NOTE_FILES:
    m = re.search(r'^## Timeline events\s*$', texts[f], re.M)
    if not m:
        continue
    seg = texts[f][m.end():]
    n = re.search(r'^## ', seg, re.M)
    if n:
        seg = seg[:n.start()]
    for line in seg.split('\n'):
        l = line.strip()
        if not l.startswith(('- ', '* ')):
            continue
        parts = [p.strip() for p in l[2:].strip().split(' | ')]
        if len(parts) < 3 or not re.match(r'^(?:c\.?\s*|~|circa\s*)?\d{3,4}', parts[0]):
            continue
        if len(parts) >= 4:
            ev, url, conf = ' | '.join(parts[1:-2]), parts[-2], parts[-1]
        elif parts[2].startswith('http'):
            ev, url, conf = parts[1], parts[2], ''
        else:
            ev, url, conf = parts[1], '', parts[2]
        dm = re.search(r'(\d{3,4})(?:-(\d{2}))?(?:-(\d{2}))?', parts[0])
        key = (int(dm.group(1)), int(dm.group(2) or 0), int(dm.group(3) or 0))
        dk = (key, re.sub(r'\W+', ' ', ev.lower())[:70])
        if dk in tl:
            tl[dk]['files'].add(f)
            continue
        tags = ';'.join(t for t, pat in FOCUS if re.search(pat, ev))
        tl[dk] = dict(key=key, date=parts[0], event=tidy(ev), url=url, conf=conf, files={f}, tags=tags)
rows = [[v['date'], v['event'], v['url'], v['conf'], bucket(v['key'][0]), v['tags'], '; '.join(sorted(v['files']))]
        for v in sorted(tl.values(), key=lambda v: v['key'])]
stats['timeline'] = write_csv(f'{OUT}/csv/timeline_draft.csv',
    ['date', 'event', 'source_url', 'confidence', 'era_bucket', 'focus_tags', 'source_notes'], rows)
stats['timeline_span'] = (rows[0][0], rows[-1][0]) if rows else None

# ---------- YouTube link harvest from notes ----------
URL_RE = re.compile(r'https?://[^\s<>\]\)"\'`]+')


def yt_kind(u):
    u = u.rstrip('.,;:)]')
    m = re.match(r'https?://(?:www\.|m\.)?youtube\.com/watch\?(.*)$', u)
    if m:
        v = re.search(r'(?:^|&)v=([A-Za-z0-9_-]{11})', m.group(1))
        if v:
            return 'video', v.group(1), f'https://www.youtube.com/watch?v={v.group(1)}'
    m = re.match(r'https?://youtu\.be/([A-Za-z0-9_-]{11})', u)
    if m:
        return 'video', m.group(1), f'https://www.youtube.com/watch?v={m.group(1)}'
    m = re.match(r'https?://(?:www\.)?youtubetotranscript\.com/transcript\?v=([A-Za-z0-9_-]{11})', u)
    if m:
        return 'video', m.group(1), f'https://www.youtube.com/watch?v={m.group(1)}'
    m = re.match(r'https?://(?:www\.)?youtube\.com/shorts/([A-Za-z0-9_-]{11})', u)
    if m:
        return 'short', m.group(1), f'https://www.youtube.com/shorts/{m.group(1)}'
    m = re.match(r'https?://(?:www\.|m\.)?youtube\.com/playlist\?list=([A-Za-z0-9_-]+)', u)
    if m:
        return 'playlist', m.group(1), f'https://www.youtube.com/playlist?list={m.group(1)}'
    m = re.match(r'https?://(?:www\.|m\.)?youtube\.com/(@[^/?#\s]+|channel/UC[A-Za-z0-9_-]{22}|c/[^/?#\s]+|user/[^/?#\s]+)', u)
    if m:
        return 'channel', m.group(1), f'https://www.youtube.com/{m.group(1)}'
    return None


harvest = {}
for f in NOTE_FILES:
    owner = f'section:{f}'
    for line in texts[f].split('\n'):
        h = re.match(r'^## (Person|Entity): (.+)$', line)
        if h:
            owner = person_id(h.group(2)) if h.group(1) == 'Person' else f'entity:{h.group(2).strip()}'
            continue
        h2 = re.match(r'^## (.+)$', line)
        if h2:
            owner = f'section:{h2.group(1).strip()}'
            continue
        for um in URL_RE.finditer(line):
            k = yt_kind(um.group(0))
            if not k:
                continue
            kind, vid, url = k
            key = (owner, kind, vid)
            if key in harvest:
                continue
            ctx = tidy(URL_RE.sub('', line))
            ctx = re.sub(r'^[-*]\s*', '', ctx)
            harvest[key] = [owner, kind, vid, url, (vid in index_video_ids) if kind in ('video', 'short') else '',
                            cut(ctx, 240), f]
hrows = sorted(harvest.values(), key=lambda r: (r[0], r[1], r[2]))
stats['links'] = write_csv(f'{OUT}/csv/youtube_links_harvest.csv',
    ['owner_person_or_section', 'type', 'id_or_handle', 'url', 'video_also_in_youtube_videos_csv', 'context_line_in_notes',
     'source_note'], hrows)
stats['links_by_type'] = dict(collections.Counter(r[1] for r in hrows))

# playlists
pl_known = {
    'PLJ_6TGCsXE7c': ('Ashtar Live Trance Channelings', 5),
    'PL9npZE0Wd3b-OhJ17g9G4MArL3uagp30i': ('SpiritCode Transmissions', 5),
    'PL9npZE0Wd3b_gc0b2LyGJPXLqXY9qo94l': ('Masterclasses (podcast playlist)', 71),
}
prow = []
seen = set()
for r in hrows:
    if r[1] == 'playlist':
        t, n = pl_known.get(r[2], ('', ''))
        prow.append([r[2], r[3], r[0], t, n, r[5], r[6]])
        seen.add(r[2])
for pid, (t, n) in pl_known.items():
    if pid not in seen:
        prow.append([pid, f'https://www.youtube.com/playlist?list={pid}', 'athina-krol', t, n,
                     'listed on the channel page of @AthinaKrol, read 2026-10-23', 'channel page scrape'])
stats['playlists'] = write_csv(f'{OUT}/csv/youtube_playlists.csv',
    ['playlist_id', 'url', 'owner_person_or_section', 'title_if_known', 'video_count_if_known', 'context', 'source'], prow)

# ---------- plots ----------
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# Inter first, Japanese-capable fallback so channel names such as チャネラー純子 render instead of boxes
plt.rcParams['font.family'] = ['Inter', 'Noto Sans CJK JP', 'DejaVu Sans']

SURF, INK, INK2, GRID, BLUE, ORANGE, STEM = '#fcfcfb', '#0b0b0b', '#52514e', '#e8e7e3', '#2a78d6', '#eb6834', '#d6d5d0'


def fmt(n):
    return f'{n/1e6:.2f}M'.replace('.00M', 'M') if n >= 1e6 else (f'{n/1e3:.0f}K' if n >= 1e4 else (f'{n/1e3:.1f}K' if n >= 1e3 else str(n)))


def short(s, n=38):
    return s if len(s) <= n else s[:n - 1] + '…'


sub_rows = sorted([(c.get('person_name') or c['person'], c['subscribers'], c['status'], c.get('role', '')) for c in channels if c.get('subscribers')],
                  key=lambda r: -r[1])
n = len(sub_rows)
X0 = 4  # axis floor: the smallest channel has 8 subscribers, so the floor sits below 10
fig, ax = plt.subplots(figsize=(10, max(6, 0.27 * n + 2.6)), dpi=170)
fig.patch.set_facecolor(SURF)
ax.set_facecolor(SURF)
ys = list(range(n))[::-1]
for y, (name, subs, st, role) in zip(ys, sub_rows):
    col = BLUE if st == 'ok' else ORANGE
    ax.plot([X0, subs], [y, y], color=STEM, lw=1, zorder=1)
    ax.scatter([subs], [y], s=48, color=col, edgecolor=SURF, linewidth=1.3, zorder=3)
    ax.text(subs * 1.12, y, fmt(subs), va='center', ha='left', fontsize=7.5, color=INK2)
ax.set_yticks(ys)
ax.set_yticklabels([short(r[0], 34) + (f' ({r[3]})' if r[3] and r[3] != 'channeler' else '') for r in sub_rows], fontsize=8, color=INK)
ax.set_xscale('log')
ax.set_xlim(X0, 2.2e6)
ax.set_ylim(-0.8, n - 0.2)
ax.set_xticks([10, 1e2, 1e3, 1e4, 1e5, 1e6])
ax.set_xticklabels(['10', '100', '1K', '10K', '100K', '1M'], color=INK2, fontsize=8)
ax.minorticks_off()
ax.xaxis.grid(True, color=GRID, lw=0.8)
ax.set_axisbelow(True)
for s_ in ('top', 'right', 'left'):
    ax.spines[s_].set_visible(False)
ax.spines['bottom'].set_color(GRID)
ax.tick_params(axis='y', length=0)
ax.tick_params(axis='x', length=0)
leg = ax.legend(handles=[Line2D([0], [0], marker='o', color='w', markerfacecolor=BLUE, markersize=7, label='latest 30 uploads indexed from the channel page'),
                         Line2D([0], [0], marker='o', color='w', markerfacecolor=ORANGE, markersize=7, label='size copied from the research notes (channel page not read)')],
                loc='lower right', frameon=False, fontsize=8)
for t in leg.get_texts():
    t.set_color(INK2)
fig.subplots_adjust(left=0.30, right=0.97, top=1 - 1.30 / fig.get_figheight(), bottom=0.55 / fig.get_figheight())
fig.text(0.02, 1 - 0.30 / fig.get_figheight(), f'YouTube audience of the {n} channels with a known subscriber count', fontsize=12.5, color=INK, weight='bold', va='top')
fig.text(0.02, 1 - 0.62 / fig.get_figheight(), 'One snapshot from the 2026-10-23 research session, log scale. Draft: unaudited. Orange counts were copied from the notes, not re-read.', fontsize=8.5, color=INK2, va='top')
fig.text(0.02, 1 - 0.84 / fig.get_figheight(), 'Rows tagged (context), (contactee) or (organisation) are not trance channelers; they are listed for comparison.', fontsize=8.5, color=INK2, va='top')
fig.savefig(f'{OUT}/plots/plot_youtube_audience.png', facecolor=SURF)
plt.close(fig)

# plot 2: entity named in channeling videos among fully indexed channels
pair = collections.Counter()
for c in channels:
    if c['status'] != 'ok':
        continue
    for v in (c.get('videos') or []):
        if v.get('is_channeling') and v.get('entity'):
            pair[(v['entity'], c.get('person_name') or c['person'])] += 1
top = pair.most_common(18)
top = sorted(top, key=lambda kv: kv[1])
fig, ax = plt.subplots(figsize=(10, max(4.5, 0.36 * len(top) + 2.4)), dpi=170)
fig.patch.set_facecolor(SURF)
ax.set_facecolor(SURF)
for i, ((ent, who), k) in enumerate(top):
    ax.barh(i, k, height=0.58, color=BLUE, zorder=3)
    ax.text(k + 0.35, i, str(k), va='center', ha='left', fontsize=8.5, color=INK2)
ax.set_yticks(range(len(top)))
ax.set_yticklabels([short(f'{e} — {w}', 52) for (e, w), _ in top], fontsize=8.5, color=INK)
ax.set_xlim(0, 33)
ax.set_xticks([0, 10, 20, 30])
ax.tick_params(axis='x', colors=INK2, labelsize=8, length=0)
ax.tick_params(axis='y', length=0)
ax.xaxis.grid(True, color=GRID, lw=0.8)
ax.set_axisbelow(True)
for s_ in ('top', 'right', 'left'):
    ax.spines[s_].set_visible(False)
ax.spines['bottom'].set_color(GRID)
nok = sum(1 for c in channels if c['status'] == 'ok')
fig.subplots_adjust(left=0.40, right=0.97, top=1 - 1.45 / fig.get_figheight(), bottom=0.5 / fig.get_figheight())
fig.text(0.02, 1 - 0.30 / fig.get_figheight(), 'Beings named in the titles of channeling videos (latest uploads of indexed channels)', fontsize=12.5, color=INK, weight='bold', va='top')
fig.text(0.02, 1 - 0.62 / fig.get_figheight(), f'Videos per entity–channeler pair; at most 30 latest uploads for each of the {nok} channels indexed from the channel page. Draft.', fontsize=8.5, color=INK2, va='top')
fig.savefig(f'{OUT}/plots/plot_entities_in_video_titles.png', facecolor=SURF)
plt.close(fig)
stats['plot_rows'] = (n, len(top))

# ---------- copy notes/data ----------
for f in NOTE_FILES + ['CANONICAL_IDS.md']:
    shutil.copy(f'{NOTES}/{f}', f'{OUT}/notes/{f}')
for f in ('group_A.json', 'group_B.json', 'group_C.json', 'SCHEMA.md'):
    shutil.copy(f'{NOTES}/youtube_index/{f}', f'{OUT}/data/youtube_index_{f}')
shutil.copy(YT_JSON, f'{OUT}/data/youtube_index_merged.json')
shutil.copy(f'{PARTS}/people_part1.json', f'{OUT}/data/people_part1_PARTIAL.json')
shutil.copy('/home/claude/etc_site/data/DATA_SCHEMAS.md', f'{OUT}/data/planned_dataset_schemas.md')

# ---------- report with draft banner and appendix ----------
cov = index['coverage']
rep = open(REPORT_SRC, encoding='utf-8').read()
first, rest = rep.split('\n', 1)
banner = (
    '\n> **DRAFT — not reviewed.** Compiled on 2026-10-23 from eight research passes. The synthesis ends after the '
    'occult-forums and Reddit section: the skeptics-and-scholars section, a consolidated "what could not be verified" '
    'section and a sources list were not written because the writing agent was cut off. Claims are reported as claims. '
    'No independent verification pass has been run on any date or figure. The research notes in `notes/` hold every '
    'source URL, and `notes/entities_and_criticism.md` ("Criticism dossier") holds the skeptical and scholarly material.\n'
)
appendix = f"""

---

## What this draft does not cover yet

**Skeptics and scholars.** Not synthesised here. `notes/entities_and_criticism.md` has the dated table of failed or revised predictions, the psychological and academic explanations, the journalism and commercial-model data and the harm cases, each attributed to its author with a URL.

**Reddit.** No thread bodies were retrieved: reddit.com blocked every fetch route and the search credits ran out before the dedicated Reddit queries ran. The Reddit mentions in this report come from search-result snippets gathered in other passes.

**YouTube coverage.** {cov['fully_indexed']} of {cov['total_channels']} indexed entries have their 30 most recent uploads read from the channel page ({cov['total_videos']} video rows in all, {cov['channeling_videos']} flagged as channeling). {cov['metadata_only']} have channel details copied from the research notes only and were not live-checked, {cov['no_youtube']} have no YouTube channel found or applicable, and {cov['not_found']} could not be found. Playlists were not collected systematically; `csv/youtube_playlists.csv` lists only those that turned up incidentally.

**Not built.** The website and its timeline page, the dashboard update and the repository branch. `csv/timeline_draft.csv` is the raw, lightly de-duplicated union of every dated event in the notes ({stats['timeline']} rows), not a curated timeline.
"""
open(f'{OUT}/ET channelers directory and timeline.md', 'w', encoding='utf-8').write(first + '\n' + banner + '\n' + rest.rstrip('\n') + appendix)

# ---------- README ----------
readme = f"""# ET channelers — current draft (2026-10-23)

Status: **draft, unreviewed.** This folder packages what the research passes produced before work was stopped. Nothing here was independently verified, and the website, timeline page, dashboard update and repository branch were not built.

## Files

| File | What it is |
|---|---|
| `ET channelers directory and timeline.md` | Draft synthesis report (about 7,000 words). Stops after the occult-forums and Reddit section; see the last section for what is missing. |
| `csv/youtube_channels.csv` | {stats['channels']} people and organisations with their YouTube channel (handle, id, URL, subscribers, video count, entities seen). `index_status` says how deep each row goes. |
| `csv/youtube_videos.csv` | {stats['videos']} video rows: title, URL, views and relative publish date as displayed on 2026-10-23, length, whether it is a channeling session, entity named in the title. |
| `csv/youtube_links_harvest.csv` | {stats['links']} YouTube links pulled from the research notes ({', '.join(f'{v} {k}' for k, v in sorted(stats['links_by_type'].items()))}), each with the person or section it was cited under and the line it came from. |
| `csv/youtube_playlists.csv` | {stats['playlists']} playlists that turned up incidentally. Not a systematic playlist census. |
| `csv/youtube_entity_rollup.csv` | Beings named in video titles, with video counts and which channelers voice them. |
| `csv/bashar_videos_in_repo_by_channel.csv` | The 75 Bashar videos already digested in the Bashar index repo, grouped by the {stats['bashar_channels']} channels that post them. |
| `csv/people_directory.csv` | {stats['people']} people parsed from the research notes (entity, start, first public, location, platforms, method, confidence), joined to the YouTube index. |
| `csv/entities_catalogue_raw.csv` | {stats['entities']} entity blocks from the notes. Duplicates across notes are not merged. |
| `csv/timeline_draft.csv` | {stats['timeline']} dated entries from {stats['timeline_span'][0]} to {stats['timeline_span'][1]}, with source URL, confidence and focus tags (ra, bashar, ashtar, ryok). Raw union of the notes, lightly de-duplicated. A few entries are scheduled items or claimed predictions (for example the 2027 row), flagged in the confidence column. |
| `plots/` | Audience of channels with a known subscriber count; beings named in video titles. |
| `notes/` | The eight research notes (about 67,000 words) and the canonical id list. |
| `data/` | Merged YouTube index JSON, its three source group files, the partly compiled people dataset (23 of about 129) and the planned dataset schemas. |

## How to read the YouTube files

- `index_status` is `ok` when the channel page and up to 30 recent uploads were read on 2026-10-23, `metadata-only` when the channel details come from the research notes and the video list was not read, `no_youtube` when no channel was found or applies, and `not_found` when a search found nothing.
- Subscriber and view counts are as displayed on that date. Publish dates are relative ("3 weeks ago") because the source only gave relative times.
- The structured YouTube data provider ran out of credits partway through, so most `metadata-only` rows still need one provider call each to fill their video lists.

## Known gaps

- Reddit: nothing retrieved. Wizard Forums: two site searches only. BALG: eleven threads read.
- Reported but unmerged conflicts between notes are left visible: duplicate timeline events with different wording, duplicate entity blocks, and dates marked low confidence.
- `people_directory.csv` was parsed from free-text notes by label matching, so a cell can be blank where a note used an unusual label: {stats['people_empty_fields']} of {stats['people']} rows have no parsed entity, start date or first-public value at all, and others have single blanks (Tyler Ellison's first-public and confidence cells, for example). The full text is always in `notes/`. All {stats['entities']} blocks in `entities_catalogue_raw.csv` parsed without fallback.
"""
open(f'{OUT}/README.md', 'w', encoding='utf-8').write(readme)

# ---------- zip ----------
zpath = f'{OUT}/../et-channelers-draft.zip'
with zipfile.ZipFile(zpath, 'w', zipfile.ZIP_DEFLATED) as z:
    for root, _, files in os.walk(OUT):
        for fn in files:
            full = os.path.join(root, fn)
            z.write(full, os.path.join('et-channelers-draft', os.path.relpath(full, OUT)))
stats['zip_bytes'] = os.path.getsize(zpath)
print(json.dumps(stats, ensure_ascii=False, indent=1, default=str))
