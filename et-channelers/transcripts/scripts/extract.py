import json, sys, re, os
# usage: extract.py <firecrawl_tool_result_file> <out_dir> <video_id>
src, outdir, vid = sys.argv[1], sys.argv[2], sys.argv[3]
raw = open(src, encoding='utf-8').read()
try:
    d = json.loads(raw)
except Exception as e:
    # some results are wrapped; try to find the first '{'
    i = raw.find('{')
    d = json.loads(raw[i:])
md = d.get('markdown') or d.get('data', {}).get('markdown') or ''
meta = d.get('metadata', {}) or d.get('data', {}).get('metadata', {})
os.makedirs(outdir, exist_ok=True)
open(os.path.join(outdir, vid + '.txt'), 'w', encoding='utf-8').write(md)
print(vid, 'chars', len(md), 'words', len(md.split()), '| title:', (meta.get('title') or meta.get('ogTitle') or '')[:120])
print('truncation markers:', [m.group(0) for m in re.finditer(r'(?i)content truncated[^\n]{0,60}|truncated due to length', md)][:3])
