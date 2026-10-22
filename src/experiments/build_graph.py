# build_graph.py: merge the AI-lab paper graph with the physics/engineering literature into one node-link JSON
import re, json
import os
RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data', 'experiments', 'frequency-of-place')
s = open(f'{RES}/ai_lab_papers.md').read()
G = json.loads(re.search(r"```json\s*(\{.*?\})\s*```", s, re.S).group(1))
lit = json.loads(re.search(r"```json\s*(\[.*?\])\s*```", open(f'{RES}/literature.md').read(), re.S).group(1))
byid = {x['id']: x for x in lit}

# physics/engineering topic nodes feeding the experiment
TOPICS = {
    't-sphere-modes': ('Free vibration of an elastic sphere', 'A1 A2 A3 A6 A7 A8 A9 A13 A14 I1 I2'),
    't-thin-shells': ('Thin spherical shell vibration', 'I3 I4 I5 I7 I8 I10 I11 I14 I16'),
    't-rus': ('Resonant ultrasound spectroscopy', 'B1 B2 B3 B4 B7 B13 A12 I42 I44'),
    't-copper': ('Copper elastic constants and their temperature dependence', 'B9 B11 B12'),
    't-noncontact': ('Non-contact excitation and detection (LDV, EMAT, air-coupled)', 'C1 C2 C4 C6 C8'),
    't-modal': ('Experimental modal analysis of plates', 'D1 D2 D3 D5 D6 D8'),
    't-contact': ('Contact mechanics and rolling of a ball on a flat', 'E6 E7 I18 I20 I22 I34 I36'),
    't-location': ('Location effects: gravity, redshift, NMR, air', 'F1 F2 F3 F5 F6 F8'),
    't-inverse-spectral': ('Inverse spectral problems ("hearing the shape")', 'G1 G2 G4 G5 H7 H8'),
    't-ml-eigen': ('Learned PDE and eigenvalue solvers', 'H1 H2 H3 H4 H5 H6'),
    't-ml-rus': ('Machine learning for RUS inversion', 'H10 H11 H12'),
    't-exp-design': ('AI-assisted experimental design and symbolic regression', 'H13 H14 H15'),
    't-bench': ('Flat-table bench: surface plates, levels, DAQ, software', 'I28 I30 I32 I33 I37 I38 I40 I42 I45'),
}
nodes = list(G['nodes']); edges = list(G['edges'])
ids = {n['id'] for n in nodes}
nodes.append(dict(id='experiment', label='This experiment: the frequency of a place', kind='experiment', org='', date='2026-10', url='#design', field='experimental acoustics', verified='design only',
                  summary='Complete vibration spectrum of a thin hollow copper sphere at two places on a flat table; the spectrum of each place; a drive test with controls.'))
for tid, (lab, srcs) in TOPICS.items():
    nodes.append(dict(id=tid, label=lab, kind='topic', org='', date='', url='', field='physics', verified='', summary='', side='physics'))
    edges.append(dict(source=tid, target='experiment', rel='feeds_experiment'))
    for sid in srcs.split():
        x = byid.get(sid)
        if not x: continue
        nid = 'lit-' + sid
        if nid not in ids:
            ids.add(nid)
            nodes.append(dict(id=nid, label=x['title'][:90], kind='literature', org=x.get('venue', ''), date=str(x.get('year', '')), url=x.get('url', ''),
                              field=x.get('topic', ''), verified=x.get('verified', ''), summary=f"{x.get('authors', '')} · {x.get('venue', '')} {x.get('year', '')}", side='physics'))
        edges.append(dict(source=nid, target=tid, rel='about'))
# the AI-lab graph already carried an 'EXPERIMENT' topic placeholder: merge it into the experiment node
_old = [n['id'] for n in nodes if n['kind'] == 'topic' and n['label'].startswith('EXPERIMENT')]
for oid in _old:
    nodes = [n for n in nodes if n['id'] != oid]
    for e in edges:
        if e['source'] == oid: e['source'] = 'experiment'
        if e['target'] == oid: e['target'] = 'experiment'
_seen = set(); _E = []
for e in edges:
    if e['source'] == e['target']: continue
    k = (e['source'], e['target'], e['rel'])
    if k in _seen: continue
    _seen.add(k); _E.append(e)
edges = _E
# make sure every edge resolves
ids = {n['id'] for n in nodes}
edges = [e for e in edges if e['source'] in ids and e['target'] in ids]
# connect the AI-lab adjacency edges to the experiment node explicitly
for e in edges:
    if e['rel'] == 'adjacent_to_experiment': e['target'] = 'experiment'
for n in nodes: n.setdefault('side', 'lab')
out = dict(nodes=nodes, edges=edges)
json.dump(out, open(os.path.join(RES, 'graph.json'), 'w'), indent=0)
from collections import Counter
print(len(nodes), len(edges), Counter(n['kind'] for n in nodes), Counter(e['rel'] for e in edges))
