import json, glob, os, re, sys, time
# usage: ingest_all.py <tool_results_dir> <out_dir> <min_mtime_epoch>
trd, outdir, since = sys.argv[1], sys.argv[2], float(sys.argv[3])
os.makedirs(outdir, exist_ok=True)
added, skipped = [], []
for fn in sorted(glob.glob(os.path.join(trd, 'mcp-Firecrawl-firecrawl_scrape-*.txt')), key=os.path.getmtime):
    if os.path.getmtime(fn) < since: continue
    raw = open(fn, encoding='utf-8', errors='replace').read()
    try:
        d = json.loads(raw[raw.find('{'):])
    except Exception as e:
        skipped.append((fn, 'json:'+str(e)[:60])); continue
    md = d.get('markdown') or d.get('data', {}).get('markdown') or ''
    meta = d.get('metadata') or d.get('data', {}).get('metadata') or {}
    blob = ' '.join(str(meta.get(k, '')) for k in ('sourceURL','url','ogUrl','og:url','canonical'))
    m = re.search(r'[?&]v=([A-Za-z0-9_-]{11})', blob) or re.search(r'youtu\.be/([A-Za-z0-9_-]{11})', md[:4000])
    if not m:
        skipped.append((fn, 'no id')); continue
    vid = m.group(1)
    out = os.path.join(outdir, vid + '.txt')
    if os.path.exists(out) and os.path.getsize(out) >= len(md.encode('utf-8')):
        continue
    open(out, 'w', encoding='utf-8').write(md)
    added.append((vid, len(md.split())))
print('added', len(added), added)
print('skipped', skipped)
