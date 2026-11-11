import re, sys, os
# usage: grep_ctx.py <regex> <context_chars> <file> [<file> ...]
pat = re.compile(sys.argv[1], re.I)
ctx = int(sys.argv[2])
for fn in sys.argv[3:]:
    t = open(fn, encoding='utf-8', errors='replace').read()
    # drop everything before the transcript body marker, if present
    i = t.find('Translate')
    if i != -1: t = t[i+9:]
    t = re.sub(r'\s+', ' ', t)
    spans = []
    for m in pat.finditer(t):
        a, b = max(0, m.start()-ctx), min(len(t), m.end()+ctx)
        if spans and a <= spans[-1][1]:
            spans[-1][1] = max(spans[-1][1], b)
        else:
            spans.append([a, b])
    print(f'##### {os.path.basename(fn)}  ({len(t.split())} words, {len(spans)} passages)')
    for a, b in spans:
        pos = int(100 * a / max(1, len(t)))
        print(f'--- [{pos}% in] ...{t[a:b]}...')
        print()
