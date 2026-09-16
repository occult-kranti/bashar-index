#!/usr/bin/env python3
"""Assemble The Bashar Index (single-file artifact) from research + analysis data."""
import json, re, html, math, collections, os, sys
sys.path.insert(0, '/home/claude/bashar/site')
from css import CSS
from js import JS

R = '/home/claude/bashar/research'; A = '/home/claude/bashar/analysis'; S = '/home/claude/bashar/site'
def L(p): return json.load(open(p))
videos = L(f'{A}/videos.json'); an = L(f'{A}/analysis.json')
diagrams = L(f'{R}/diagrams.json'); svgs = L(f'{S}/diagrams_svg.json')
glossary = L(f'{R}/glossary.json'); timeline = L(f'{R}/timeline.json')
catalog = L(f'{R}/catalog_sessions.json'); podcasts = L(f'{R}/manifests/podcasts.json')
works = L(f'{R}/anka_works.json'); events = L(f'{R}/events_upcoming.json'); dlv = L(f'{R}/manifests/divine_light_vibes_channel.json')
TAGL = {t['tag']: t['label'] for t in an['tags']}

def esc(s): return html.escape(str(s if s is not None else ''), quote=True)
def slug(s): return re.sub(r'^-+|-+$', '', re.sub(r'[^a-z0-9]+', '-', str(s).lower().replace('’', '').replace("'", '')))
def dom(u): return re.sub(r'^https?://(www\.)?', '', u).split('/')[0]
def short_url(u):
    m = re.sub(r'^https?://(www\.)?', '', u).split('?')[0].rstrip('/')
    parts = m.split('/')
    if len(parts) == 1: return parts[0]
    seg = parts[-1] if len(parts[-1]) <= 28 else parts[-1][:26] + '…'
    return parts[0] + '/' + ('…/' if len(parts) > 2 else '') + seg
def src_links(urls, n=6):
    seen=set(); out=[]
    for u in urls:
        if not u: continue
        k = short_url(u)
        if k in seen: continue
        seen.add(k); out.append(f'<a href="{esc(u)}" target="_blank" rel="noopener">{esc(k)}</a>')
        if len(out)>=n: break
    return '<p class="srcs">Sources: ' + ' · '.join(out) + '</p>' if out else ''
def cut(t, n):
    t = (t or '').strip()
    if len(t) <= n: return t
    return t[:n].rsplit(' ', 1)[0].rstrip(',;:—-') + '…'
SHORT = {"formula_excitement":"The Formula","beliefs_emotions_fear":"Beliefs & fear","parallel_realities_shifting":"Parallel realities","physical_vs_higher_mind":"Physical vs higher mind","permission_slips_tools":"Permission slips","et_contact_disclosure_2027":"ET contact & 2027","essassani_hybrids_other_civilizations":"Essassani & hybrids","earth_shift_timelines_ascension":"Earth's shift","abundance_money_career":"Money & career","relationships_family_sexuality":"Relationships","health_body_healing_death":"Health & death","time_simultaneity_reincarnation":"Time & reincarnation","channeling_mechanics_darryl":"Channeling & Darryl","consciousness_oversoul_higherself":"Consciousness & oversoul","synchronicity_dreams_meditation":"Synchronicity & dreams","politics_society_economy_ai":"Politics & AI","physics_energy_frequency_dimensions":"Energy & frequency","spirituality_god_love_service":"Spirituality & love","ancient_history_atlantis_orion_sirius":"Ancient history","misc_life_guidance":"Life guidance"}
def clean_title2(t):
    t = re.sub(r'\s*\|\s*Bashar\b.*$', '', t, flags=re.I)
    t = re.sub(r'\s*\|\|.*$', '', t)
    return t.strip(' |-')
def json_block(id_, obj):
    s = json.dumps(obj, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    return f'<script type="application/json" id="{id_}">{s}</script>'

# ------------------------------------------------------------------ charts
def hbars(rows, unit='%', maxv=None, tipf=None, muted_from=None, dec=1):
    """rows: list of (label, value, tip). HTML bar chart."""
    maxv = maxv or max(v for _, v, _ in rows) or 1
    out = ['<div class="bars">']
    for i, (lab, v, tip) in enumerate(rows):
        w = 100 * v / maxv
        cls = 'bar muted' if (muted_from is not None and i >= muted_from) else 'bar'
        val = f'{v:.{dec}f}{unit}' if dec else f'{int(v)}{unit}'
        out.append(f'<div class="row-hit" data-tip="{esc(tip or lab)}"><div class="lab">{esc(lab)}</div><div class="track"><div class="{cls}" style="width:{w:.1f}%"></div></div><div class="val">{esc(val)}</div></div>')
    out.append('</div>')
    return ''.join(out)
def table_toggle(cols, rows, label='Show as table'):
    th = ''.join(f'<th class="{"num" if c.endswith("#") else ""}">{esc(c.rstrip("#"))}</th>' for c in cols)
    trs = ''.join('<tr>' + ''.join(f'<td class="{"num" if cols[j].endswith("#") else ""}">{esc(c)}</td>' for j, c in enumerate(r)) + '</tr>' for r in rows)
    return f'<details class="tbl"><summary>{label}</summary><div class="tscroll"><table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table></div></details>'
def chart(title, cap, body, cols=None, rows=None):
    return f'<div class="chart"><header><h3>{title}</h3><p class="cap">{cap}</p></header>{body}{table_toggle(cols, rows) if cols else ""}</div>'

H = an['headline']; share = an['share_overall']
N = H['n_docs']
c1_rows = [(s['label'], s['weighted_pct'], f"{s['label']}: {s['weighted_pct']}% of analysed airtime (weighted); present at ≥10% in {s['docs_with_10pct']} of {N} recordings") for s in share]
C1 = chart('What Bashar talks about most', f'Share of analysed airtime across {N} recordings (~{H["approx_words_analyzed"]/1e6:.2f}M transcript words), weighted by transcript length so full sessions count more than clips. Topic percentages are model estimates from auto-transcripts.',
           hbars(c1_rows), ['Topic', 'Weighted %#', 'Unweighted %#', 'Recordings ≥10%#'], [(s['label'], s['weighted_pct'], s['unweighted_pct'], s['docs_with_10pct']) for s in share])
C1_hero = chart('What Bashar talks about most', f'Top 10 of 20 topics · share of analysed airtime across {N} recordings, weighted by length. <a href="#analysis">Full analysis ↓</a>', hbars(c1_rows[:10], maxv=c1_rows[0][1]))

# by content type small multiples
order_types = ['Full session (re-upload)', 'Interview with Darryl Anka', 'Official highlight clip', 'Clip / excerpt']
mm = ['<div class="multi">']
tbl_rows = []
for t in order_types:
    v = an['share_by_type'].get(t)
    if not v: continue
    top = sorted(v['share'].items(), key=lambda x: -x[1])[:6]
    mm.append(f'<div class="mini"><h4>{esc(t)}</h4><span class="n">n = {v["n"]} recordings</span>' + hbars([(SHORT[k], p, f'{TAGL[k]}: {p}% in {t.lower()}s') for k, p in top], maxv=25) + '</div>')
    for k, p in top: tbl_rows.append((t, TAGL[k], p))
mm.append('</div>')
C2 = chart('The same message, four packagings', 'Top six topics by kind of recording. Full sessions lead with belief work and the Formula; contact talk leads only when Darryl Anka is being interviewed. Bars share one scale (0–25%).', ''.join(mm), ['Kind', 'Topic', 'Weighted %#'], tbl_rows)

# archetype maps (small multiples, one highlighted cluster each)
clusters = an['clusters']
vid_by = {v['video_id']: v for v in videos}
maps = ['<div class="maps">']
for c in sorted(clusters, key=lambda c: -c['size']):
    mem = set(c['members'])
    pts = []
    for v in videos:
        x, y = v['map_xy']; X = 8 + x * 184; Y = 8 + (1 - y) * 134
        if v['video_id'] in mem:
            pts.append(f'<circle class="pt hi" cx="{X:.1f}" cy="{Y:.1f}" r="4.5" data-vid="{v["video_id"]}" data-tip="{esc(v["title"][:80])}"><title>{esc(v["title"])}</title></circle>')
        else:
            pts.insert(0, f'<circle class="pt" cx="{X:.1f}" cy="{Y:.1f}" r="3"/>')
    TSHORT = {'Full session (re-upload)': 'full sessions', 'Interview with Darryl Anka': 'interviews', 'Official highlight clip': 'official clips', 'Clip / excerpt': 'clips'}
    types = ', '.join(f'{n} {TSHORT[k]}' for k, n in sorted(c['content_types'].items(), key=lambda x: -x[1]))
    maps.append(f'<div class="map"><svg viewBox="0 0 200 150" role="img" aria-label="Map highlighting {esc(c["name"])}">{"".join(pts)}</svg><h4><a data-go="#/cluster/{c["id"]}">{esc(c["name"])}</a></h4><span class="n">{c["size"]} recordings · {esc(types)}</span><div class="tags">{" · ".join(esc(SHORT[t["tag"]]) + " " + str(t["mean_pct"]) + "%" for t in c["top_tags"][:3])}</div></div>')
maps.append('</div>')
C3 = chart('Five session archetypes on one vocabulary map', f'Each panel is the same map of all {N} recordings (t-SNE over TF-IDF vocabulary; nearby = similar wording) with one archetype highlighted. Archetypes come from k-means on each recording\'s topic mix (k=5, silhouette {H["silhouette"]}). Tap a highlighted point to open its digest.', ''.join(maps),
           ['Archetype', 'Recordings#', 'Dominant topics', 'Top vocabulary'], [(c['name'], c['size'], '; '.join(f'{t["label"]} {t["mean_pct"]}%' for t in c['top_tags'][:3]), ', '.join(c['top_terms'][:8])) for c in clusters])

terms = an['terms'][:25]
C4 = chart('The vocabulary that carries the teaching', f'Key terms by the number of recordings in which the digest flagged them (of {N}). Bar length = recordings; hover for the weighted frequency score.',
           hbars([(t['term'], t['docs'], f'“{t["term"]}” flagged in {t["docs"]} recordings · weighted frequency {t["weighted"]}') for t in terms], unit='', dec=0),
           ['Term', 'Recordings#', 'Weighted freq#'], [(t['term'], t['docs'], t['weighted']) for t in an['terms'][:40]])

# dates strip
preds = [p for p in an['predictions'] if 1970 <= p['year'] <= 2080]
strip = ['<div class="strip"><div class="axis"></div>']
for yr in range(1970, 2081, 10):
    strip.append(f'<div class="tick" style="left:{(yr-1970)/110*100:.2f}%"><span>{yr}</span></div>')
lab_i = 0
for p in sorted(preds, key=lambda p: p['year']):
    left = (p['year'] - 1970) / 110 * 100; d = 6 + 3.2 * math.sqrt(p['docs'])
    ex = '; '.join(e['text'][:90] for e in p['examples'][:2])
    strip.append(f'<div class="dot" style="left:{left:.2f}%;width:{d:.0f}px;height:{d:.0f}px" data-tip="{p["year"]}: mentioned in {p["docs"]} recording{"s" if p["docs"]!=1 else ""}. {esc(ex)}"></div>')
    if p['docs'] >= 7:
        top = 64 - (lab_i % 3) * 24
        strip.append(f'<div class="dlab" style="left:{left:.2f}%;top:{top}px;--h:{96-top-16}px">{p["year"]} <span style="color:var(--muted)">×{p["docs"]}</span></div>'); lab_i += 1
strip.append('</div>')
C5 = chart('The dates that keep coming back', 'Every year mentioned in a digest\'s "predictions & dates", sized by how many recordings mention it. 2027 (the "Contact Fulcrum") and 2026 ("the year of disclosure") dominate; 2050 marks the end of the claimed 2020–2050 "reset".', ''.join(strip),
           ['Year', 'Recordings#', 'Example context'], [(p['year'], p['docs'], (p['examples'][0]['text'][:120] if p['examples'] else '')) for p in sorted(preds, key=lambda p: -p['docs'])])

qs = an['questions']
C6 = chart('What the audience actually asks', f'{H["n_questions"]} paraphrased audience questions across the digests, classified by keyword into the same 20 themes. Life guidance and contact dominate; the metaphysics Bashar leads with (mind, time, parallel realities) is rarely what people ask about.',
           hbars([(q['label'], q['pct'], f'{q["label"]}: {q["count"]} questions ({q["pct"]}%). e.g. “{q["examples"][0]["question"] if q["examples"] else ""}”') for q in qs if q['count'] > 0]),
           ['Theme', 'Questions#', '%#', 'Example'], [(q['label'], q['count'], q['pct'], (q['examples'][0]['question'] if q['examples'] else '')) for q in qs])

pairs = an['tag_pairs'][:10]
C7 = '<div class="chart"><header><h3>Which themes get taught together</h3><p class="cap">Lift = how much more often two themes co-occur (each ≥10% of a recording) than chance would predict. Lift above 1 means they travel together.</p></header><div class="tscroll"><table><thead><tr><th>Theme A</th><th>Theme B</th><th class="num">Co-occur</th><th class="num">Lift</th></tr></thead><tbody>' + ''.join(f'<tr><td>{esc(p["a"])}</td><td>{esc(p["b"])}</td><td class="num">{p["co_docs"]}</td><td class="num">{p["lift"]}</td></tr>' for p in pairs) + '</tbody></table></div></div>'

tools_rows = an['tools'][:14]
C8 = chart('Tools & practices referenced', 'Named techniques, exercises and games mentioned in the digests (grouped into families).', hbars([(t['tool'], t['docs'], f'{t["tool"]}: referenced in {t["docs"]} recordings') for t in tools_rows], unit='', dec=0), ['Tool family', 'Recordings#'], [(t['tool'], t['docs']) for t in an['tools']])
ents = an['entities'][:16]
C9 = chart('Beings, civilizations and places named', 'Named entities across the digests (aliases merged: Sassani/Essassani, Greys/Zeta, etc.).', hbars([(e['entity'], e['docs'], f'{e["entity"]}: named in {e["docs"]} recordings') for e in ents], unit='', dec=0), ['Entity', 'Recordings#'], [(e['entity'], e['docs']) for e in an['entities']])

# ------------------------------------------------------------------ HOME
top3 = H['top3']
findings = [
 ('12.3%', 'Belief work, not aliens, is the core', f'“Beliefs, emotions & fear” is the largest topic ({top3[0]["weighted_pct"]}% of analysed airtime) and appears at ≥10% in {top3[0]["docs_with_10pct"]} of {N} recordings. The Formula ({top3[1]["weighted_pct"]}%) and ET contact ({top3[2]["weighted_pct"]}%) follow. Together the top three cover {H["top3_combined_pct"]}%.'),
 ('47 of 75', 'One stable long-form mix', 'Nearly two-thirds of recordings — every full session and most long interviews — fall into a single archetype whose topic mix barely moves between a 2016 re-upload and a 2026 livestream. Short clips are the only place a single topic dominates.'),
 ('28', 'Recordings that name 2027', f'2027 (the “Contact Fulcrum”) is mentioned in {H["docs_mentioning_2027"]} of {N} digests, 2026 in {H["docs_mentioning_2026"]}, 2050 in 15 and 2033 in {H["docs_mentioning_2033"]}. Interviews with Darryl Anka lead with contact; full sessions rank it fifth.'),
 ('10 terms', 'A compact private vocabulary', 'synchronicity (47 recordings), permission slip (45), definition (44), parallel reality (38), highest excitement (37), physical mind (33), higher mind (32), open contact (31), frequency (27), hybrid children (25).'),
 ('25% / 17%', 'Audiences ask about life, then contact', f'Of {H["n_questions"]} paraphrased questions, a quarter are practical life guidance and 17% are about ETs, disclosure or 2027; relationships (7.6%) and health (7.5%) come next. Parallel realities and the higher mind — Bashar\'s favourite subjects — are under 3% of questions.'),
 ('0.01–0.05', 'Wording alone cannot tell sessions apart', 'Clustering on vocabulary only gives silhouettes of 0.01–0.05 — the same words recur in nearly every recording. Only the proportions change, which is why the archetypes are built from topic mix, not wording.'),
]
find_html = ''.join(f'<div class="card finding"><b class="num">{esc(n)}</b><h4>{esc(t)}</h4><p>{esc(d)}</p></div>' for n, t, d in findings)
stats = [(f'{len(catalog):,}', 'sessions catalogued, 1984–2027'), (str(N), 'recordings digested & analysed'), (f'{H["approx_words_analyzed"]/1e6:.2f}M', 'transcript words behind the analysis'), (f'{H["n_questions"]}', 'audience questions paraphrased'), (str(len(diagrams)), 'diagrams redrawn'), (str(len(glossary)), 'glossary terms')]
stats_html = ''.join(f'<div class="stat"><b>{esc(a)}</b><span>{esc(b)}</span></div>' for a, b in stats)
jumps = [('#who', 'Who is Bashar', 'Darryl Anka, Essassani, how a session works'), ('#timeline', 'Timeline & predictions', '1951 → 2027 and what was claimed when'), ('#teachings', 'Teachings', 'The Formula, five laws, permission slips, parallel realities'), ('#diagrams', 'Diagram collection', '56 handouts and models, redrawn'), ('#analysis', 'Topic analysis', 'What he talks about most, and how it clusters'), ('#library', 'Library', '75 digests · 684 sessions · 48 podcasts'), ('#glossary', 'Glossary', '104 terms of art'), ('#skeptics', 'Skeptics', 'Critiques, failed dates, academic reading')]
jump_html = '<div class="jump">' + ''.join(f'<a href="{h}">{esc(t)}<small>{esc(s)}</small></a>' for h, t, s in jumps) + '</div>'

HOME = f'''<section class="sec" id="home"><div class="wrap">
<div class="hero">
 <p class="eyebrow">Independent reference · not affiliated with Bashar Communications · claims are reported, not endorsed</p>
 <h1>Bashar, indexed.</h1>
 <p class="lede">Forty-two years of a channeled voice, treated as a corpus: {len(catalog)} catalogued sessions, {N} transcript digests, {len(diagrams)} redrawn diagrams and {len(glossary)} terms of art — counted, clustered and sourced, with the skeptics given the same room as the believers.</p>
 <div class="notice"><b>What this is.</b> Bashar is the entity that Darryl Anka says he has channeled since 1983. This site describes what Bashar and Anka say, what fans record and what critics argue. Full recordings are © Bashar Communications and are sold on BasharTV; this site publishes structured digests, quotes of ≤30 words, and original redrawings of the concepts behind the copyrighted handouts.</div>
 <div class="stats">{stats_html}</div>
</div>
{C1_hero}
<h3 style="margin-top:34px">Headline findings</h3>
<div class="grid c3f" style="margin-top:12px">{find_html}</div>
{jump_html}
</div></section>'''

# ------------------------------------------------------------------ WHO
books = works.get('books', []); films = works.get('films_and_video', [])
book_rows = ''.join(f'<tr><td class="t">{esc(b.get("title"))}</td><td class="num">{esc(b.get("year") or "")}</td><td class="desc">{esc(cut(b.get("description"), 210))}</td></tr>' for b in books)
film_rows = ''.join(f'<tr><td class="t">{esc(b.get("title"))}</td><td class="num">{esc(b.get("year") or "")}</td><td class="desc">{esc(cut(b.get("description"), 210))}</td></tr>' for b in films)
ev_rows = ''.join(f'<tr><td class="d">{esc(e.get("date") or "—")}</td><td class="t">{esc(e["title"])}</td><td class="desc">{esc((e.get("location") or e.get("format") or "")[:120])}</td></tr>' for e in events if e.get('date') and str(e['date']) >= '2026-09')
WHO = f'''<section class="sec" id="who"><div class="wrap">
<div class="sec-head"><p class="eyebrow">Who</p><h2>The channel, the entity, the world</h2><div class="ruler"></div></div>
<div class="twocol">
<div class="prose">
<h3>Bashar, as Bashar Communications describes him</h3>
<p>“A physical E.T, a friend from the future who has spoken since 1984” through Darryl Anka; the material “is based on the laws of physics and is not just a nice New-Age philosophy.” Event copy calls Bashar a “first contact specialist” preparing Earth for extraterrestrial contact; Anka says Bashar presents himself as Darryl's own future incarnation, about 300 years ahead, in a parallel reality vibrating faster and roughly 3,000 years further along. The official “Message from Bashar” insists no belief system is “more valid than any other” — “all truths are true and the truth is made of all truths.”</p>
{src_links(['https://www.bashar.org/about','https://www.bashar.org/message','https://expo.consciouslifeexpo.com/bashar-channeled-by-darryl-anka-1','https://batgap.com/darryl-anka-bashar-transcript/'])}
<h3>Darryl Anka</h3>
<p>Born 12 October 1951 in Ottawa; long-time resident of Woodland Hills, Los Angeles. Before and alongside channeling he worked in film effects — model maker on <i>Star Trek: The Motion Picture</i>, prop maker on <i>Star Trek II</i>, miniatures crew on <i>Iron Man</i>, <i>Star Trek: Nemesis</i> and <i>Pirates of the Caribbean: At World's End</i>, concept modeler on <i>I, Robot</i>, VFX storyboards on <i>The Time Machine</i> and <i>Flags of Our Fathers</i>. In 1973, twice in one week and in daylight, he says he saw “an equilateral, black, triangular ship” over Los Angeles. About ten years later, six weeks into a channeling class taught by Thomas Massari, he received the telepathic “hit” identifying Bashar; the first sessions were five friends in a living room, then twenty, then forty, then twice-weekly rented auditoriums as tapes circulated. Bashar Communications, Inc. was formed with April Rochelle (CEO). There was a hiatus — “RSVP” (October 2001) is billed as the first channeling since 1998. With his wife Erica Jordan he runs Zia Films (<i>Dearly Departed</i>, 2012; <i>First Contact</i>, 2016) and, on the side, Los Angeles escape rooms.</p>
<p>On proof, in his own words: “I can't prove any of this”; the value, he says, is that the information “does actually make a difference when you apply it.” He describes channeling as locking “like two tuning forks,” with himself as “a translation device.”</p>
{src_links(['https://www.bashar.org/darryl-anka','https://www.bashar.org/bashar-comm','https://www.tvguide.com/celebrities/darryl-anka/credits/3030271022/','https://awakenedmagazine.com/channeling-bashar-the-key-to-life-is-acting-on-your-passion-an-interview-with-darryl-anka/','https://batgap.com/darryl-anka-bashar-transcript/','https://valley.labusinessjournal.com/media/cinema-film/close-encounters-valley/'])}
<h3>How a session works</h3>
<p>Anka sits, closes his eyes and, after visible jaw and head movements, speaks rapidly as Bashar. Format: an opening transmission on the evening's theme → “Ask Bashar” questions from the audience, chosen by raffle → a closing meditation or exercise (often the Holotope image). Tickets include a livestream and encore; private sessions run 60 minutes on Zoom with health, predictions and politics off-limits. BasharTV streams “sessions from the 1980's to today” at $4.99–$39.99 a month.</p>
{src_links(['https://www.bashar.org/event-faqs','https://www.bashar.org/private-sessions','https://www.bashar.org/bashartv','https://maximumfun.org/transcripts/oh-no-ross-and-carrie/transcript-oh-no-ross-and-carrie-ep-377-ross-and-carrie-transmit-bashar-part-1-very-telling-edition/'])}
</div>
<div class="prose">
<h3>Essassani, “the place of living light”</h3>
<p>Bashar's world is said to lie about 500 light-years away toward Orion, in a parallel reality invisible to us; the people are the Sassani. Early sessions describe them as “the children of the Greys and humans” — a hybrid race engineered from Zeta Reticuli and human genetics — and later sessions place them third in a ladder of five hybrid civilizations, with humanity “becoming the sixth.” Descriptions vary by source: humanoid, about five feet tall, grey-white skin, large eyes, telepathic; three artificially intelligent spheres — Epsilon, Eclipse and Epiphany — orbit the planet and, with it, form a tetrahedron. An “Earth–Essassani–Sirius” triad recurs, and Anka has also channeled Willa Hillicrissing, “a parallel reality specialist” from 700 years in our future, and a character named Cybo. The name Bashar, per the official biography, is Arabic for “messenger” or “bringer of good news.”</p>
{src_links(['https://batgap.com/darryl-anka-bashar-transcript/','https://www.cesnur.org/2012/el-baroni.htm','https://ethealing.nl/en/our-media/library-of-human-et/bashar-event-overview/civilizations-open-contact/the-legacy','https://www.ethealing.nl/en/library-for-human-et/17-the-five-hybrid-races','https://www.bashar.org/willa','https://teleportation.co.nz/e-t-wiki/essassani-yahyel/'])}
<h3>Reach</h3>
<p>The official YouTube channel (“Bashar Channeled by Darryl Anka”, created 2017) had roughly 229,000 subscribers and 9.7 million views in April 2026 and posts only short “Highlights” clips — full sessions are sold, not posted. A far larger volume of Bashar on YouTube comes from third-party clip and re-upload channels, many with invented titles and dates. Regular venues: Los Angeles, Sedona weekends, San Diego, Palm Springs, New York, the Conscious Life Expo and Gaia's Emersion conference.</p>
<div class="tscroll"><table class="cat"><thead><tr><th>Date</th><th>Upcoming</th><th>Where</th></tr></thead><tbody>{ev_rows}</tbody></table></div>
{src_links(['https://us.youtubers.me/bashar-channeled-by-darryl-anka/youtuber-stats','https://www.bashar.org/event-calendar','https://www.bashar.org/AZ2026'])}
</div>
</div>
<details class="frame" style="margin-top:22px"><summary><span class="k">works</span>Books and films by Darryl Anka ({len(books)} books · {len(films)} films)</summary><div class="body"><div class="twocol" style="padding-top:14px">
<div><div class="tscroll"><table class="cat"><thead><tr><th>Book</th><th class="num">Year</th><th>Notes</th></tr></thead><tbody>{book_rows}</tbody></table></div>
</div><div><div class="tscroll"><table class="cat"><thead><tr><th>Film / video</th><th class="num">Year</th><th>Notes</th></tr></thead><tbody>{film_rows}</tbody></table></div>
{src_links([b.get('source_url') for b in books + films if b.get('source_url')], 5)}
</div></div></div></details>
</div></section>'''

# ------------------------------------------------------------------ TIMELINE
def dec_of(s):
    m = re.search(r'(19|20)\d\d', str(s)); return (int(m.group(0)) // 10 * 10) if m else None
tl_groups = collections.OrderedDict()
for t in timeline:
    d = dec_of(t['year_or_date'])
    tl_groups.setdefault(d, []).append(t)
tl_html = ''; k = 0
for d, items in tl_groups.items():
    lis = ''
    for i in items:
        k += 1
        hid = ' class="tl-more" hidden' if k > 14 else ''
        lis += f'<li{hid}><span class="when">{esc(i["year_or_date"])}</span><p>{esc(i["event"])}</p>' + (f'<p class="src"><a href="{esc(i["source_url"])}" target="_blank" rel="noopener">{esc(short_url(i["source_url"]))}</a></p>' if i.get('source_url') else '') + '</li>'
    dec_hidden = ' hidden' if (k - len(items)) >= 14 else ''
    tl_html += f'<p class="decade tl-more"{dec_hidden}>{d}s</p><ol class="tl">{lis}</ol>'
tl_html += '<button class="more" id="tlmore" type="button">Show all ' + str(len(timeline)) + ' events</button>'
ledger = [
 ('c. 1990', 'World government emerging 2011–2013; a US–Soviet–Chinese tripartite alliance', 'Did not happen — named by Baroni (2012) as failed predictions.', 'https://www.cesnur.org/2012/el-baroni.htm'),
 ('c. 1998', 'A terrorist attack in New York “somewhere around the year 2001”', 'Claimed hit by Anka (2014); the 1998 recording was not located independently.', 'https://batgap.com/darryl-anka-bashar-transcript/'),
 ('2009 / 2011', '2012 as the end of the “hands-off quarantine”, a pivotal vibrational shift', 'No observable public event; reframed as an internal threshold (“Crossing the Bridge to 2013”).', 'https://ethealing.nl/en/our-media/library-of-human-et/bashar-event-overview/civilizations-open-contact/the-span-2010-2015'),
 ('2014', '“In your upcoming fall of 2016 EVERYTHING will change”', 'No discrete event; re-described in Dec 2017 as the start of a three-year “Window of Discovery”.', 'https://ethealing.nl/en/our-media/library-of-human-et/bashar-event-overview/transformation-new-earth/window-of-discovery-2018'),
 ('2014', 'Earth’s “full involvement” with ET civilizations within 30–50 years', 'Pending (2044–2064).', 'https://ethealing.nl/en/our-media/library-of-human-et/bashar-event-overview/civilizations-open-contact/interstellar-civilizations'),
 ('2015', 'Sedona Vortex Array “to further the acceleration of ET contact”; fan wiki: a major sighting promised for 2016', 'No widely reported event; the “promise” is fan-wiki hearsay.', 'https://ethealing.nl/en/our-media/library-of-human-et/bashar-event-overview/civilizations-open-contact/sedona-vortex-array'),
 ('Dec 2017', 'Window of Discovery 2018–2020', 'Bashar Communications later points to the U.S. UAP news cycle; skeptics note “beginning of the window” wording as an escape hatch.', 'https://maximumfun.org/transcripts/oh-no-ross-and-carrie/transcript-oh-no-ross-and-carrie-ep-377-ross-and-carrie-transmit-bashar-part-1-very-telling-edition/'),
 ('Jun 2018', '2027 “Contact Fulcrum”: an ~80-year cycle from Roswell (1947) to a major turning point', 'Pending.', 'https://tv.bashar.org/programs/2027-the-contact-fulcrum'),
 ('Feb 2023', '“2023 is the beginning of the window of open contact through 2033”; a 90–95% probability of contact 2026–2027 cited by a fan blog', 'Pending; Bashar adds that if nothing happens, humans didn’t “walk through the window”.', 'https://maximumfun.org/transcripts/oh-no-ross-and-carrie/transcript-oh-no-ross-and-carrie-ep-377-ross-and-carrie-transmit-bashar-part-1-very-telling-edition/'),
 ('Jan 2025', 'Open contact “within the next five years”; a 2020–2050 “reset”; hybrid children living among humans long-term', 'Pending.', 'https://nextlevelsoul.com/darryl-anka-2025/'),
 ('Dec 2025', '2025–2027 “three-year global breakdown phase” before breakthrough', 'Pending.', 'https://podcasts.apple.com/lv/podcast/248-darryl-anka-bashar-preparing-for-open-contact-the/id1611118279?i=1000739206449'),
 ('Mar 2026', '2026 = “the true Year of Disclosure”; 2027 = face-to-face contact / official public presentation', 'Pending as of September 2026.', 'https://www.bialikbreakdown.com/episodes/aliens-are-making-contact-3000-years-ahead-warning-were-making-big-mistakes-darryl-anka-bashar'),
]
ledger_html = '<ol class="ledger-list">' + ''.join(f'<li><span class="when">{esc(w)}</span><p class="claim">{esc(c)}</p><p class="status">{esc(st)} <a href="{esc(u)}" target="_blank" rel="noopener">{esc(short_url(u))}</a></p></li>' for w, c, st, u in ledger) + '</ol>'
TIMELINE = f'''<section class="sec" id="timeline"><div class="wrap">
<div class="sec-head"><p class="eyebrow">Timeline</p><h2>1951 → 2027, and what was claimed when</h2><div class="ruler"></div></div>
<div class="twocol">
<div><h3>Chronology</h3><p class="small">{len(timeline)} dated events from the research file; each links to its source.</p>{tl_html}</div>
<div><h3>Predictions ledger</h3><p class="small">Bashar's own framing: “there's no such thing as a prediction of <i>the</i> future. There are an infinite number of probable future realities.” Skeptics note this makes most claims unfalsifiable. What was said, and what can be checked:</p>{ledger_html}
<div class="callout"><h4>How the dates cluster in the corpus</h4><p class="small" style="margin:0">Across the {N} digests, 2027 is named in {H["docs_mentioning_2027"]} recordings and 2026 in {H["docs_mentioning_2026"]}; see the <a href="#analysis">dates chart</a>.</p></div></div>
</div>
</div></section>'''

# ------------------------------------------------------------------ TEACHINGS
def dl(ids): return ''.join(f'<a class="pill acc" data-go="#/diagram/{i}">◇ {esc(next((d["name"] for d in diagrams if d["id"]==i), i))[:40]}</a>' for i in ids)
gl_by = {slug(g['term']): g for g in glossary}
def tl_(terms): return ''.join(f'<a class="pill" data-go="#/term/{slug(t)}">{esc(t)}</a>' for t in terms if slug(t) in gl_by)
frames = [
 ('laws', 'The Five Laws of Creation', 'the axioms', '''<ol><li><b>You exist.</b></li><li><b>Everything is here and now.</b></li><li><b>The One is the All and the All are the One.</b></li><li><b>What you put out is what you get back.</b></li><li><b>Everything changes, except the first four laws.</b></li></ol><p>Bashar presents these as the physics behind everything else. An older four-law version (1998; still used in BasharTV's introduction) omits “here and now”; the fifth law was introduced as such in a 2013 session.</p>''', ['five-laws-of-creation'], ['Five Laws of Creation', 'Four Laws of Creation', 'All That Is / The One'], ['https://www.bashar.org/fivelaws', 'https://tv.bashar.org/pages/introduction']),
 ('formula', 'The Follow-Your-Excitement Formula', 'the practice', '''<ol><li>Act on your excitement — whatever is most exciting to you, in the moment, every moment you can.</li><li>Do it to the best of your ability; take it as far as you can go.</li><li>With absolutely no insistence, assumption or expectation of what the outcome should be.</li><li>Remain in a positive state regardless of what happens.</li><li>Constantly investigate your belief systems; release and replace the fear-based ones.</li></ol><p>Excitement is defined as “the physical translation of the vibrational resonance that is your true, core natural being.” Steps 1–3 are “the formula”; Bashar says acting on it automatically brings a “complete kit” — a driving engine, the organizing principle of synchronicity, the path of least resistance, connection, support, a reflective mirror and “all the tools you need.” In the corpus it is the second-largest theme and the most common answer to audience questions; skeptics call it “mostly good advice … but too overstated.”</p>''', ['the-formula', 'excitement-formula-kit', '1-3-5-7-11-download'], ['The Formula (Follow Your Excitement Formula)', 'Highest excitement', 'Synchronicity'], ['https://www.bashar.org/formula']),
 ('steps', 'The Seven Sequential Steps of Manifestation', 'the ladder', '''<ol><li>Vision — visualize what you want.</li><li>Desire — be intensely excited about it.</li><li>Belief — believe it is possible.</li><li>Acceptance — accept your belief and your ability as true.</li><li>Intent — want and intend are different; intend it.</li><li>Action — act and behave as if it has already manifested.</li><li>Allowance — detach from the outcome.</li></ol><p>Taught in an August 1995 session and published as an official guide page.</p>''', ['seven-steps-of-manifestation'], ['Seven Sequential Steps of Manifestation', 'Allowance'], ['https://www.bashar.org/sevensteps']),
 ('principles', "Bashar's 13 Basic Principles", 'the creed', '''<p>Thirteen statements published on bashar.org, opening with “You are a non-physical consciousness that is experiencing physical reality” and closing with “You are loved so unconditionally by Creation that you can even choose to believe that you are not loved.” Between them: you chose to be here and ecstasy is your birthright; the highest purpose is to be yourself fully; free will always; you attract experience through your strongest beliefs, emotions and actions; there is only one moment; you create the past and future from now; everything you experience is another aspect of yourself.</p>''', ['basic-principles-13'], ['Basic Principles', 'Ecstasy as birthright', 'Unconditional love'], ['https://www.bashar.org/principles']),
 ('mind', 'Physical mind, higher mind, and the levels of consciousness', 'the model of you', '''<p>The recurring division of labour: the physical mind perceives and acts on what is in front of it but “was never designed to know how”; the higher mind conceives, sees the whole path and chooses timing. Imagination is “the pipeline through which your Higher Self talks to you,” and excitement is the signal that the two are aligned. In the 2011 “Nine Levels of Consciousness” session the stack runs from Oversoul → soul → higher mind → the template level → collective and individual unconscious → beliefs → emotions → thoughts, with the conscious mind at the bottom; the 2017 “Triad Mind” adds the heart as the resonant middle between higher mind and head.</p>''', ['physical-mind-higher-mind', 'triad-mind', 'nine-levels-of-consciousness', 'construction-of-physical-reality'], ['Physical mind', 'Higher mind / Higher self', "Imagination ('I-magi-nation')", 'Oversoul', 'Nine Levels of Consciousness'], ['https://iasos.com/metaphys/bashar/']),
 ('beliefs', 'Beliefs → emotions → thoughts → actions', 'belief work', '''<p>“All emotions stem from beliefs. You can't feel something without believing something to be true first.” A definition produces an emotion, the emotion colours thought, thought drives behaviour, behaviour produces experience that appears to confirm the belief. Change the definition and the chain re-forms. The method: use the emotional charge (fear) as the tracer, ask what you would have to believe to feel this way, examine what releasing it would mean, replace it. Sessions dedicated to it include <i>Changing / Transforming Core Beliefs</i> (2006), <i>Brick Walls &amp; Beliefs</i> (2009), <i>The Black Box</i> (2014, 27 tricks of negative beliefs and 24 neutralizers), <i>The Story Tree</i> (2016) and <i>The Spectrum of Fear</i> (2017). It is the largest theme in the corpus.</p>''', ['belief-emotion-thought-action', 'changing-core-beliefs', 'black-box', 'spectrum-of-fear', 'story-tree', 'brick-walls-and-beliefs', 'transforming-core-beliefs'], ['Beliefs → emotions → actions', 'Fear-based beliefs', 'Definitions', 'Worthiness / deservability'], ['https://www.goodreads.com/quotes/tag/bashar', 'https://iasos.com/metaphys/bashar/']),
 ('permission', 'Permission slips', 'the tools', '''<p>Crystals, rituals, meditations, games, symbols, teachers — anything that lets you give yourself permission to access a state you already have. “The tool has no power of its own”; hold it lightly. Bashar builds a new permission slip into many sessions: the 7-Part Master Permission Slip (2014), the Hour of Power (2018), the Spiral, the Holotope image used at nearly every event, the Sacred Circuitry glyph cards (2010), Cybo (2016), the Parallel Reality Wheel (2020). In the digests, “permission slip” is flagged in 45 of {N} recordings.</p>''', ['permission-slips-concept', 'near-life-experience-master-permission-slip', 'hour-of-power', 'spiral-exercise', 'holotope', 'sacred-circuitry', 'cybo-lucky-13', 'parallel-reality-wheel'], ['Permission slip', 'Holotope', 'Sacred Circuitry', 'Cybo'], ['https://thalira.com/blogs/quantum-codex/bashar-channeling-darryl-anka']),
 ('parallel', 'Parallel realities, the shift, and time as one moment', 'the physics', '''<p>Every possible version of reality already exists, complete and static, like frames of film; consciousness moves through billions of these frames a second and the sequence it selects is experienced as motion, time and change. You never change the world you are on — you shift to a version that reflects the change in you, and your state of being is “the navigational device.” From 2019 (“Navigating the Splitting Prism”, “Earth Zero”) the same model is applied to the planet: many parallel Earths overlapping, diverging into positive and negative versions, with 2020 as “the eye of the needle.” Time itself is “an artificial construct created by collective human agreement”; there is only one moment, and reincarnation is simultaneous rather than sequential.</p>''', ['frames-of-film-parallel-shifting', 'parallel-realities-diagram-1997', 'parallel-reality-wheel', 'eye-of-the-needle', 'density-dimension-ladder', 'you-are-all-time-travelers', 'reincarnation-deeper-explanation', '33rd-parallel', 'as-above-so-below', 'prime-radiant'], ['Parallel realities', 'Splitting Prism', 'Earth Zero / zero template', 'Time / one moment', 'The Shift / New Earth', 'Density'], ['https://iasos.com/metaphys/bashar/', 'https://ethealing.nl/en/our-media/library-of-human-et/bashar-event-overview/transformation-new-earth/navigating-the-splitting-prism']),
 ('state', 'Circumstances don’t matter — only state of being matters', 'the stance', '''<p>Events are “neutral props” with no built-in meaning; you assign it. Select what you prefer without judging what you don't prefer. The universe works by resonance and reflection rather than by attracting objects: what you put out is the frequency of experience you can perceive, and other people and events mirror it back. Following excitement produces positive synchronicity; acting from fear produces “negative synchronicity” — obstacles that signal a pivot. Definitions Bashar insists on: doubt is “one hundred percent trust in a belief you don't prefer”; “try” presumes failure; hope implies doubt; “the greatest gift creation has given to all of you is that life is fundamentally meaningless.”</p>''', ['resonance-and-reflection', 'circle-of-self-empowerment', 'soul-blueprint-workshop'], ['State of being', 'Neutral props', 'Judgment vs preference', 'Positive / negative synchronicity', 'Referential Preferential You'], ['https://www.positivelife.ie/2010/10/bashar-circumstances-dont-matter-only-state-of-being-matters/', 'https://www.goodreads.com/quotes/tag/bashar']),
 ('contact', 'Open contact: protocols, windows and the 2027 fulcrum', 'the mission', '''<p>Bashar's stated job is to prepare Earth for open contact. The <i>Protocols of First Contact</i> (2016) list 43 steps from “discovery of the civilization” through sightings, a “connection individual,” a Contact Council, precursor contacts and open contact to Interstellar Alliance membership. The official <i>Guide to Open Contact</i> sequences sessions as the Window → the Door → the Gate; the <i>Interstellar Alliance Social Experiment</i> (2024) adds eight steps for participants; the <i>Interstellar Enneagram</i> (2014) maps nine civilizations — Orion, Anunnaki and the Greys in the past row, Essassani, Earth and the Yahyel in the present, Sirius, Arcturus and the Pleiades in the future. Dates: 2012 (end of the “hands-off quarantine”), fall 2016, the Window of Discovery 2018–2020, a contact window 2023–2033, 2026 “the year of disclosure,” the 2027 Contact Fulcrum (~80 years after Roswell), and a 2020–2050 “reset.”</p>''', ['protocols-of-first-contact', 'guide-to-open-contact-window-door-gate', 'interstellar-alliance-social-experiment', 'interstellar-enneagram', 'hybrid-races-ladder', 'ufo-witness-declaration', 'window-of-discovery', 'increasing-the-probability-of-contact', 'preparing-for-contact-101', 'tell-them-bashar-sent-you', 'vortex-array', 'interdimensional-portals', 'vortex-vibrations', 'contact-crystal-and-crystal-techniques'], ['Contact Fulcrum (2027)', 'Open contact', 'Protocols of First Contact', 'Interstellar Alliance', 'Yahyel (Ya\'yel)', 'Hybrid children', 'Window of Discovery (2018–2020)', 'Roswell cycle'], ['https://www.bashar.org/guide', 'https://www.bashar.org/socialexperiment', 'https://tv.bashar.org/programs/2027-the-contact-fulcrum']),
 ('essassani', 'Essassani technology, games and the channeling circuit', 'the world', '''<p>Three AI spheres — Epsilon, Eclipse, Epiphany — orbit Essassani as a “trinary consciousness”; Cybo is “the Sassani word for 13, the vibration of transformation” and a game played in Las Vegas in 2016; the 1992 <i>Keys of Ascension</i> chart pairs nine levels with Platonic solids, colours and senses; the 2015 <i>Mechanics of Channeling</i> session presents channeling as a circuit that downloads energy “from higher levels into our physical reality.”</p>''', ['essassani-ai-spheres-triad', 'eclipse', 'cybo-lucky-13', 'keys-of-ascension', 'mechanics-of-channeling', 'tis-the-season'], ['Epsilon / Eclipse / Epiphany', 'Essassani', 'Sassani', 'Cybo'], ['https://ethealing.nl/en/our-media/library-of-human-et/bashar-event-overview/civilizations-open-contact/1-epsilon']),
]
fr_html = ''
for fid, name, kicker, body, dids, terms_, srcs in frames:
    fr_html += f'<details class="frame" id="teach-{fid}"><summary><span class="k">{esc(kicker)}</span>{esc(name)}</summary><div class="body"><div class="prose" style="padding-top:12px">{body.replace("{N}", str(N))}</div><div class="links">{dl(dids)}{tl_(terms_)}</div>{src_links(srcs, 4)}</div></details>'
TEACH = f'''<section class="sec" id="teachings"><div class="wrap">
<div class="sec-head"><p class="eyebrow">Teachings</p><h2>The frameworks, in Bashar's own order of importance</h2><div class="ruler"></div></div>
<p class="lede" style="margin-bottom:22px">Eleven frameworks cover almost everything said in {N} recordings. Each card links to the diagrams that illustrate it and to the glossary. Wording marked as verbatim comes from bashar.org guide pages; everything else is paraphrased.</p>
{fr_html}
</div></section>'''

# ------------------------------------------------------------------ DIAGRAMS
KINDS = {'Official handout — redrawn from its text': ('k1', 'handout'), 'Reconstructed from the session description': ('k2', 'session'), "Model synthesized from Bashar's teaching": ('k3', 'model'), 'Concept illustration — handout layout unverified': ('k4', 'concept')}
dg_meta = []
figs = []
kind_count = collections.Counter()
KORDER = {'Official handout — redrawn from its text': 0, 'Reconstructed from the session description': 1, "Model synthesized from Bashar's teaching": 2, 'Concept illustration — handout layout unverified': 3}
CORDER = {'high': 0, 'medium': 1, 'low': 2}
diagrams = sorted(diagrams, key=lambda d: (KORDER[svgs[d['id']]['kind']], CORDER.get(d['confidence'], 3), d['name']))
for d in diagrams:
    s = svgs[d['id']]; kc, kk = KINDS[s['kind']]; kind_count[kk] += 1
    figs.append(f'<figure class="dgf" id="dg-{d["id"]}" data-id="{d["id"]}" data-k="{kk}">{s["svg"]}<figcaption><b>{esc(d["name"])}</b><span><span class="badge {kc}">{esc(kk)}</span> <span class="badge">{esc(d["confidence"])} confidence</span></span></figcaption></figure>')
    dg_meta.append({'id': d['id'], 'name': d['name'], 'kind': s['kind'], 'kind_class': kc, 'official_handout_url': d.get('official_handout_url'), 'session': d.get('session_title_and_date'), 'concept_summary': d.get('concept_summary'), 'visual_structure': d.get('visual_structure'), 'key_labels': d.get('key_labels') or [], 'steps_or_layers': d.get('steps_or_layers') or [], 'sources': d.get('sources') or [], 'confidence': d.get('confidence'), 'notes': d.get('notes')})
DIAG = f'''<section class="sec" id="diagrams"><div class="wrap">
<div class="sec-head"><p class="eyebrow">Diagram collection</p><h2>{len(diagrams)} handouts and models, redrawn</h2><div class="ruler"></div></div>
<p class="lede">bashar.org publishes 35 session handouts as image-only PDFs. None of that artwork is reproduced here. Instead each concept is redrawn from its text, from Bashar's own spoken walkthroughs, and from session descriptions — with a badge saying how much of the original's layout is actually known. Tap any figure for the full explanation, labels and sources.</p>
<div class="filters" id="dfilters"><button class="chip on" data-k="">All {len(diagrams)}</button><button class="chip" data-k="handout">Official handouts, redrawn from text ({kind_count["handout"]})</button><button class="chip" data-k="session">Reconstructed from session descriptions ({kind_count["session"]})</button><button class="chip" data-k="model">Models from the teaching ({kind_count["model"]})</button><button class="chip" data-k="concept">Concept illustrations, layout unverified ({kind_count["concept"]})</button></div>
<div class="dgrid" id="dgrid">{''.join(figs)}</div>
<p class="small" style="margin-top:14px">Attribution: the concepts belong to Bashar Communications / Darryl Anka; the drawings are original study aids. Official PDFs: <a href="https://www.bashar.org/handouts" target="_blank" rel="noopener">bashar.org/handouts</a>.</p>
</div></section>'''

# ------------------------------------------------------------------ ANALYSIS
M = an['method']
ANAL = f'''<section class="sec" id="analysis"><div class="wrap">
<div class="sec-head"><p class="eyebrow">Topic analysis</p><h2>What he talks about, measured</h2><div class="ruler"></div></div>
<p class="lede">{N} recordings — {H["n_full_sessions"]} full sessions, {H["n_interviews"]} interviews with Darryl Anka, {H["n_official_clips"]} official highlight clips and {H["n_clips"]} third-party clips, about {H["approx_words_analyzed"]/1e6:.2f} million transcript words — were digested into a fixed 20-topic mix, key terms, quotes and questions, then clustered.</p>
{C1}{C2}{C3}{C4}{C5}{C6}
<div class="grid c2" style="margin-top:0">{C8}{C9}</div>
{C7}
<div class="callout"><h4>Method &amp; caveats</h4><ul>
<li><b>Corpus.</b> {esc(M["corpus"])}</li>
<li><b>Document text.</b> {esc(M["document_text"])}</li>
<li><b>Vectorizer.</b> {esc(M["vectorizer"])}</li>
<li><b>Clustering.</b> {esc(M["clustering"])}</li>
<li><b>Map.</b> {esc(M["map"])}</li>
<li><b>Topic share.</b> {esc(M["topic_share"])}</li>
{''.join(f'<li>{esc(c)}</li>' for c in M["caveats"])}
<li><b>Year views.</b> Only {an["share_by_era"].get("2024–2026",{}).get("n",0)} recordings carry a reliable date (2024–2026); re-upload titles often invent dates, so no trend-over-decades claim is made.</li>
</ul></div>
</div></section>'''

# ------------------------------------------------------------------ LIBRARY
TYPE_CLASS = {'Full session (re-upload)': 't-full', 'Interview with Darryl Anka': 't-int', 'Official highlight clip': 't-off', 'Clip / excerpt': 't-clip'}
vcards = []
years = sorted({str(v['year']) for v in videos if v['year']}, reverse=True)
tagset = collections.Counter()
for v in sorted(videos, key=lambda v: (-(v['approx_word_count'] or 0))):
    top = sorted(v['topic_percentages'].items(), key=lambda x: -x[1])[:3]
    for t, _ in top: tagset[t] += 1
    text = ' '.join([v['title'], v['channel'] or '', v['show'] or '', v['opening_summary'] or '', ' '.join(k['term'] for k in v['key_terms'])]).lower()
    vcards.append(f'<div class="vcard" data-id="{v["video_id"]}" data-type="{esc(v["content_type"])}" data-year="{v["year"] or ""}" data-tags="{" ".join(t for t,_ in top)}" data-text="{esc(text[:1200])}"><span class="meta"><span class="type-dot {TYPE_CLASS[v["content_type"]]}"></span>{esc(v["content_type"])}{" · " + (str(v["year"]) if v["year_reliable"] else "~" + str(v["year"])) if v["year"] else ""}</span><b>{esc(clean_title2(v["title"]))}</b><span class="meta">{esc(v["show"] or v["channel"] or "")} · ~{(v["approx_word_count"] or 0):,} words</span><div class="tags">{"".join(f"<span>{esc(TAGL[t])}</span>" for t,_ in top[:2])}</div></div>')
vtype_opts = ''.join(f'<option value="{esc(t)}">{esc(t)}</option>' for t in order_types)
vyear_opts = ''.join(f'<option value="{y}">{y}</option>' for y in years)
vtag_opts = ''.join(f'<option value="{t}">{esc(TAGL[t])}</option>' for t, _ in tagset.most_common())
# catalog
def is_boiler(desc): return (not desc) or ('no official synopsis was located' in desc) or desc.startswith('Early-era Bashar channeling session')
cat_rows = []
dec_count = collections.Counter()
for c in sorted(catalog, key=lambda c: (c.get('date') or '9999')):
    d = c.get('date') or ''
    dec = f'{dec_of(d)}s' if dec_of(d) else 'undated'
    dec_count[dec] += 1
    desc = '' if is_boiler(c.get('description')) else (c.get('description') or '')
    if desc.startswith('Topics tagged on BasharTV:'): desc = desc.replace('Topics tagged on BasharTV:', 'Tags:')
    desc = re.sub(r'\s*Recording date .*$', '', desc)
    text = (c['title'] + ' ' + desc + ' ' + (c.get('event_or_location') or '')).lower()
    url = c.get('source_url') or ''
    tlink = f'<a href="{esc(url)}" target="_blank" rel="noopener">{esc(c["title"])}</a>' if url else esc(c['title'])
    cat_rows.append(f'<tr data-dec="{dec}" data-text="{esc(text[:600])}"><td class="d">{esc(d or "—")}</td><td class="t">{tlink}</td><td class="desc">{esc(desc[:220])}{"…" if len(desc)>220 else ""}</td></tr>')
dec_opts = ''.join(f'<option value="{d}">{d} ({n})</option>' for d, n in sorted(dec_count.items()))
# podcasts
prow = []
for p in sorted(podcasts, key=lambda p: str(p.get('date') or ''), reverse=True):
    link = p.get('youtube_url') or p.get('apple_url') or p.get('spotify_url') or ''
    text = ' '.join([p.get('show') or '', p.get('host') or '', p.get('episode_title') or '', p.get('description') or '']).lower()
    vid = re.search(r'v=([A-Za-z0-9_-]{11})', p.get('youtube_url') or '')
    dig = f' <a class="pill acc" data-go="#/video/{vid.group(1)}">digest</a>' if vid and vid.group(1) in vid_by else ''
    listen = f'<a href="{esc(link)}" target="_blank" rel="noopener">Listen ↗</a>' if link else ''
    prow.append(f'<div class="row" data-text="{esc(text[:600])}"><div class="d">{esc(p.get("date") or "")}<br>{esc(p.get("type") or "")}{"<br>" + esc(p["duration"]) if p.get("duration") else ""}</div><div><b>{esc(p.get("episode_title"))}</b><p>{esc(p.get("show"))}{" · " + esc(p["host"]) if p.get("host") else ""}</p><p>{esc(p.get("description") or "")}</p><span>{listen}{dig}</span></div></div>')
dlv_vids = ''.join(f'<li><a href="{esc(v["url"])}" target="_blank" rel="noopener">{esc(v["title"])}</a></li>' for v in dlv.get('videos', [])[:8])
LIB = f'''<section class="sec" id="library"><div class="wrap">
<div class="sec-head"><p class="eyebrow">Library</p><h2>Recordings, sessions, podcasts, channels</h2><div class="ruler"></div></div>
<div class="tabs" role="tablist"><button class="tab" role="tab" aria-selected="true" data-panel="p-videos">Digested recordings ({N})</button><button class="tab" role="tab" aria-selected="false" data-panel="p-cat">Session catalog ({len(catalog)})</button><button class="tab" role="tab" aria-selected="false" data-panel="p-pod">Podcasts &amp; interviews ({len(podcasts)})</button><button class="tab" role="tab" aria-selected="false" data-panel="p-chan">Channels &amp; official sources</button></div>
<div class="panel" id="p-videos">
<p class="small">Each card opens a digest: summary, paraphrased Q&amp;A, topic mix, key terms, short quotes, dates mentioned, and a link to the recording. Digests are AI-generated from public auto-transcripts and are not transcripts.</p>
<div class="fbar"><input id="vq" type="search" placeholder="Filter recordings (title, channel, terms…)" aria-label="Filter recordings"><select id="vtype" aria-label="Kind"><option value="">All kinds</option>{vtype_opts}</select><select id="vyear" aria-label="Year"><option value="">Any year</option>{vyear_opts}</select><select id="vtag" aria-label="Topic"><option value="">Any leading topic</option>{vtag_opts}</select><span class="small mono-num" id="vcount"></span></div>
<div class="vgrid" id="vgrid">{''.join(vcards)}</div>
</div>
<div class="panel" id="p-cat" hidden>
<p class="small">Session and event titles gathered from archive.org's fan-archived recordings (1984–2009 titles and dates only), BasharTV program pages (with official topic tags), bashar.org's calendar, Gaia and TVDB. Titles link to the source page.</p>
<div class="fbar"><input id="cq" type="search" placeholder="Search {len(catalog)} sessions…" aria-label="Search sessions"><select id="cdec" aria-label="Decade"><option value="">All decades</option>{dec_opts}</select><span class="small mono-num" id="ccount"></span></div>
<div class="tscroll"><table class="cat" id="cat"><thead><tr><th>Date</th><th>Session</th><th>Description / tags</th></tr></thead><tbody>{''.join(cat_rows)}</tbody></table></div>
<button class="more" id="cmore">Show more</button>
</div>
<div class="panel" id="p-pod" hidden>
<div class="fbar"><input id="pq" type="search" placeholder="Filter podcasts…" aria-label="Filter podcasts"></div>
<div class="pod" id="pod">{''.join(prow)}</div>
</div>
<div class="panel" id="p-chan" hidden>
<div class="chan">
<div class="card"><span class="mono">Official</span><h3>Bashar Channeled by Darryl Anka</h3><p>The official YouTube channel (@BasharChanneledbyDarrylAnka, linked from bashar.org): short “Highlights” clips only; ~229K subscribers (April 2026). Full sessions are streamed on <a href="https://tv.bashar.org" target="_blank" rel="noopener">BasharTV</a> and sold at <a href="https://store.bashar.org" target="_blank" rel="noopener">store.bashar.org</a>. Handouts: <a href="https://www.bashar.org/handouts" target="_blank" rel="noopener">bashar.org/handouts</a>. Also: Instagram @basharchanneling, TikTok/Facebook @basharchannelingofficial, Vimeo basharcommunications.</p><p><a href="https://www.youtube.com/@BasharChanneledbyDarrylAnka" target="_blank" rel="noopener">Open channel ↗</a></p></div>
<div class="card"><span class="mono">Unofficial · clip channel</span><h3>Divine Light Vibes</h3><p>{esc(dlv["description"])}</p><p>Not affiliated with Bashar Communications: a “manifest abundance” description with no mention of Anka or bashar.org, a dmca.jp contact address, channel keywords including “bashar clips,” and uploads titled “Bashar Twin Flame — …” that are 12–15 minute excerpts cut from longer public sessions (one transcript check: ~2,100 words of a genuine live session). Its favourites playlist “Bashar Channeling Playlist 2026” holds 326 videos. Subscriber and upload counts were not retrievable.</p><p><a href="{esc(dlv["channel_url"])}" target="_blank" rel="noopener">Open channel ↗</a></p><details class="tbl"><summary>Sample uploads found</summary><ul class="small">{dlv_vids}</ul></details></div>
<div class="card"><span class="mono">Unofficial · full-session re-uploads</span><h3>“[Full] Bashar :: …” channels</h3><p>Divine Insights, Eternal Inspiration, “Bashar Channeled by Darryl Anka 2025” (a look-alike) and others re-upload complete sessions with invented dates: one c. 2016 session appears under three “Breaking News” dates in 2025–2026; the Aug 2025 “Signs of the Times” livestream circulates as “A Step Along The Way” and “The Precursors” (2026). Bashar Communications actively files takedowns, so many links die. The library flags every title date judged unreliable.</p></div>
<div class="card"><span class="mono">Official · free guides</span><h3>Guide pages on bashar.org</h3><p><a href="https://www.bashar.org/formula" target="_blank" rel="noopener">The Formula</a> · <a href="https://www.bashar.org/fivelaws" target="_blank" rel="noopener">Five Laws</a> · <a href="https://www.bashar.org/sevensteps" target="_blank" rel="noopener">Seven Steps</a> · <a href="https://www.bashar.org/principles" target="_blank" rel="noopener">Basic Principles</a> · <a href="https://www.bashar.org/guide" target="_blank" rel="noopener">Guide to Open Contact</a> · <a href="https://www.bashar.org/socialexperiment" target="_blank" rel="noopener">Social Experiment</a> · <a href="https://www.bashar.org/event-calendar" target="_blank" rel="noopener">Event calendar</a></p></div>
</div>
</div>
</div></section>'''

# ------------------------------------------------------------------ GLOSSARY
gl_sorted = sorted(glossary, key=lambda g: g['term'].lower())
letters = sorted({g['term'][0].upper() for g in gl_sorted})
az = ''.join(f'<a href="#gl-{l}">{l}</a>' for l in letters)
gl_html = ''; cur = ''
gl_meta = []
for g in gl_sorted:
    s = slug(g['term']); l = g['term'][0].upper()
    anchor = f' id="gl-{l}"' if l != cur else ''; cur = l
    rel = ', '.join(g.get('related') or [])
    relspan = f'<span class="rel">See also: {esc(rel)}</span>' if rel else ''
    gl_html += f'<dl{anchor}><dt id="term-{s}"><a data-go="#/term/{s}" style="text-decoration:none;color:inherit">{esc(g["term"])}</a></dt><dd>{esc(g["definition"])}{relspan}</dd></dl>'
    gl_meta.append({'term': g['term'], 'slug': s, 'definition': g['definition'], 'related': g.get('related') or [], 'sources': g.get('sources') or []})
GLOSS = f'''<section class="sec" id="glossary"><div class="wrap">
<div class="sec-head"><p class="eyebrow">Glossary</p><h2>{len(glossary)} terms of art</h2><div class="ruler"></div></div>
<div class="az">{az}</div>
<div class="gl">{gl_html}</div>
</div></section>'''

# ------------------------------------------------------------------ SKEPTICS
SKEP = f'''<section class="sec" id="skeptics"><div class="wrap">
<div class="sec-head"><p class="eyebrow">Skeptics &amp; scholars</p><h2>The case against, and the academic reading</h2><div class="ruler"></div></div>
<div class="twocol">
<div class="prose">
<h3>Academic: an old esotericism in an alien costume</h3>
<p>Francesco Baroni (University of Lausanne), in “Darryl Anka and ‘Bashar’: Modern Channeling between Alien Narrative and Ancient Esotericism” (CESNUR, 2012), argues the discourse is “deeply rooted in the history of Western esotericism”: a Hermetic paradigm (“the One is the All”), the holographic microcosm, imagination as creative power (Bashar's “I-magi-nation” echoing Jacob Böhme), and close terminological parallels to Jane Roberts's Seth — “All That Is,” “Oversoul,” an entity that is the medium's future self. He notes failed predictions (a world government by 2011–13; a US–Soviet–Chinese alliance) and credits videotaping (from 1985) and YouTube (c. 2006) with Bashar's reach.</p>
{src_links(['https://www.cesnur.org/2012/el-baroni.htm','https://www.academia.edu/2605275/Darryl_Anka_and_Bashar_Modern_Channeling_between_Alien_Narrative_and_Ancient_Esotericism'])}
<h3>Investigative: Oh No, Ross and Carrie!</h3>
<p>The investigative-comedy podcast attended three Conscious Life Expo sessions (2022, 2023 ×2; $45–55 a ticket, ~800 people). Their observations: Anka visibly enters trance with jaw-clacking and head jerks; the Formula and “red-light / green-light synchronicity” are recycled as the answer to nearly every question; wording such as “the beginning of the window” leaves escape hatches; politically sensitive questions are declined; blame is routed back to the questioner's beliefs; the 2023–2033 contact window is conditional on human behaviour and therefore unfalsifiable; Bashar's “universal principles” map neatly onto Anka's own biography; and a 2010 documentary clip has Bashar concede the material “could just be coming from my imagination.” Their verdict on the Formula: “mostly good advice … but not good advice in the end, because it's too overstated.”</p>
{src_links(['https://maximumfun.org/transcripts/oh-no-ross-and-carrie/transcript-oh-no-ross-and-carrie-ep-377-ross-and-carrie-transmit-bashar-part-1-very-telling-edition/','https://maximumfun.org/transcripts/oh-no-ross-and-carrie/transcript-oh-no-ross-and-carrie-ross-and-carrie-transmit-bashar-part-2-follow-your-excitement-edition/','https://maximumfun.org/episodes/oh-no-ross-and-carrie/ross-and-carrie-consult-bashar-multi-dimensional-channeler-edition/'])}
</div>
<div class="prose">
<h3>Other critiques</h3>
<ul>
<li><b>Unfalsifiability.</b> “No such thing as a prediction of the future” plus parallel-reality framing (“different followers inhabit different versions”) insulates every claim; Thalira (2026) lists no verifiable evidence for Essassani, premium pricing and prediction failures.</li>
<li><b>Dependency and self-blame.</b> A 2024 Medium essay (“The Illusion of Cosmic Wisdom”) argues an unassailable ET authority and ambiguous slogans create interpretive dependency, with responsibility shifted to the seeker when results fail.</li>
<li><b>Press.</b> Mayim Bialik, after her March 2026 interview, wrote that she wanted scientists such as Neil deGrasse Tyson to weigh in; IBTimes UK notes “no scientific evidence confirming Bashar's existence.” Boing Boing (2015) reported Anka's copyright takedowns against GIF artists.</li>
<li><b>Track record.</b> See the <a href="#timeline">predictions ledger</a>: the checkable dated claims (2011–13 world government, 2012, fall 2016, 2018–2020) did not produce the announced events; 2026–2027 is pending.</li>
</ul>
{src_links(['https://thalira.com/blogs/quantum-codex/bashar-channeling-darryl-anka','https://medium.com/@dualisticunity/the-illusion-of-cosmic-wisdom-how-bashar-exploits-spiritual-seekers-133c52d511bb','https://bialikbreakdown.substack.com/p/interview-with-the-alien','https://www.ibtimes.co.uk/darryl-anka-bashar-extraterrestrial-contact-podcast-1804734','https://boingboing.net/2015/06/13/man-who-channels-alien-from-th.html'])}
<h3>What Bashar Communications says about belief</h3>
<p>The official “Message” says the material never presents any belief system “as being more valid than any other”; Anka: “it's not really about whether you believe Bashar is real … I can't prove any of this.” A 2009 session, <i>Debunking the Debunkers</i>, argues that “gullibility, skepticism and cynicism all represent essentially the same rejection of truth.” The often-quoted line “don't believe anything Bashar says just because he says it” was not found verbatim on any official page.</p>
{src_links(['https://www.bashar.org/message','https://awakenedmagazine.com/channeling-bashar-the-key-to-life-is-acting-on-your-passion-an-interview-with-darryl-anka/','https://ethealing.nl/en/our-media/library-of-human-et/bashar-event-overview/existence-consciousness/debunking-the-debunkers'])}
</div>
</div>
</div></section>'''

# ------------------------------------------------------------------ SOURCES & METHOD
SRC = f'''<section class="sec" id="sources"><div class="wrap">
<div class="sec-head"><p class="eyebrow">Sources &amp; method</p><h2>How this was built</h2><div class="ruler"></div></div>
<div class="twocol">
<div class="prose">
<h3>Pipeline</h3>
<ol class="plain">
<li><b>Discovery.</b> Web search and page fetches across bashar.org, tv.bashar.org, store.bashar.org, archive.org's fan-archived recordings, Apple Podcasts, Gaia, TVDB, the ethealing.nl session index, fan wikis, academic and press sources. Six parallel research strands (official clips, full sessions, podcasts, session catalog, diagrams, teachings) plus a planning advisor.</li>
<li><b>Digests.</b> For {N} public YouTube recordings the auto-transcript was read through a transcript service and condensed into a fixed schema: summary, paraphrased Q&amp;A, a 20-topic percentage mix, 25–40 key terms with frequency buckets, 5–8 quotes of ≤30 words, dates, tools and named entities. No full transcript is stored or published.</li>
<li><b>Analysis.</b> Python / scikit-learn: TF-IDF over the digest text (Bashar's multi-word terms fused), k-means archetypes on the topic mix, t-SNE map over LSA, weighted topic shares, term document-frequency, year extraction, keyword classification of {H["n_questions"]} questions, tag co-occurrence lift.</li>
<li><b>Diagrams.</b> The 35 official PDFs are image-only; seven had a text layer (Keys of Ascension, Spectrum of Fear, Parallel Reality Wheel, Protocols, Black Box, UFO Declaration, Window of Discovery). Everything else was reconstructed from Bashar's spoken walkthroughs and session descriptions, then drawn from scratch as SVG with a confidence badge.</li>
<li><b>Verification.</b> Every biographical date carries a source link; contradictions (start year 1983 vs 1984 vs 1987; five vs four laws; Yahyel vs Shalanaya) are flagged rather than resolved; unverifiable labels are marked as such in the research notes.</li>
</ol>
<h3>Limitations</h3>
<ul>
<li>The digest corpus is what YouTube offered in 2024–2026: re-uploads, highlight clips and interviews. It is not a random sample of 42 years, and it over-represents the contact theme relative to the 1980s–2000s catalog.</li>
<li>Topic percentages and quotes are model outputs from auto-captions; quotes are unverified against audio and are limited to 30 words.</li>
<li>Re-upload titles frequently carry invented dates; a year is shown only when the session itself, a podcast feed, or an upload date supports it.</li>
<li>Subscriber counts, RationalWiki's entry and several paywalled articles could not be retrieved and are cited without summary.</li>
</ul>
</div>
<div class="prose">
<h3>Primary sources</h3>
<ul>
<li>bashar.org — <a href="https://www.bashar.org/about" target="_blank" rel="noopener">about</a>, <a href="https://www.bashar.org/darryl-anka" target="_blank" rel="noopener">Darryl Anka</a>, <a href="https://www.bashar.org/handouts" target="_blank" rel="noopener">handouts</a>, <a href="https://www.bashar.org/formula" target="_blank" rel="noopener">formula</a>, <a href="https://www.bashar.org/fivelaws" target="_blank" rel="noopener">five laws</a>, <a href="https://www.bashar.org/sevensteps" target="_blank" rel="noopener">seven steps</a>, <a href="https://www.bashar.org/principles" target="_blank" rel="noopener">principles</a>, <a href="https://www.bashar.org/message" target="_blank" rel="noopener">message</a>, <a href="https://www.bashar.org/event-calendar" target="_blank" rel="noopener">event calendar</a></li>
<li><a href="https://tv.bashar.org" target="_blank" rel="noopener">BasharTV</a> program pages (official topic tags) · <a href="https://archive.org/advancedsearch.php?q=identifier%3Abashar-*" target="_blank" rel="noopener">archive.org fan archive</a> (1984–2009 titles and dates) · <a href="https://ethealing.nl/en/our-media/library-of-human-et/bashar-event-overview" target="_blank" rel="noopener">ethealing.nl session index</a></li>
<li>Interviews with Anka: <a href="https://batgap.com/darryl-anka-bashar-transcript/" target="_blank" rel="noopener">BATGAP (2014)</a>, <a href="https://awakenedmagazine.com/channeling-bashar-the-key-to-life-is-acting-on-your-passion-an-interview-with-darryl-anka/" target="_blank" rel="noopener">Awakened Magazine (2025)</a>, <a href="https://singjupost.com/aliens-are-making-contact-3000-years-ahead-w-darryl-anka-transcript/" target="_blank" rel="noopener">Bialik Breakdown transcript (2026)</a></li>
<li>Academic: <a href="https://www.cesnur.org/2012/el-baroni.htm" target="_blank" rel="noopener">Baroni, CESNUR 2012</a> · Skeptical: <a href="https://maximumfun.org/podcasts/oh-no-ross-and-carrie/" target="_blank" rel="noopener">Oh No, Ross and Carrie!</a> · Press: <a href="https://valley.labusinessjournal.com/media/cinema-film/close-encounters-valley/" target="_blank" rel="noopener">LA Business Journal (2013)</a>, <a href="https://boingboing.net/2015/06/13/man-who-channels-alien-from-th.html" target="_blank" rel="noopener">Boing Boing (2015)</a>, <a href="https://www.ibtimes.co.uk/darryl-anka-bashar-extraterrestrial-contact-podcast-1804734" target="_blank" rel="noopener">IBTimes UK (2026)</a></li>
<li>Transcripts were read via youtubetotranscript.com; each digest links to the YouTube recording it summarises.</li>
</ul>
<h3>Rights</h3>
<p>Bashar® material is © Darryl Anka / Bashar Communications, Inc. This is an independent, non-commercial reference: it quotes briefly for commentary and analysis, links to official sources for the full material, and does not reproduce handout artwork, session video or transcripts. Digests and drawings on this page were generated by Claude for the site's owner on 11 September 2026.</p>
</div>
</div>
</div></section>'''

# ------------------------------------------------------------------ search index
index = []
for v in videos: index.append({'k': 'video', 't': clean_title2(v['title']), 's': v['content_type'], 'x': (v['opening_summary'] or '')[:220] + ' ' + ' '.join(k['term'] for k in v['key_terms'][:30]), 'h': f'#/video/{v["video_id"]}'})
for d in dg_meta: index.append({'k': 'diagram', 't': d['name'], 's': d['kind'].split(' — ')[0], 'x': (d['concept_summary'] or '')[:200], 'h': f'#/diagram/{d["id"]}'})
for g in gl_meta: index.append({'k': 'glossary', 't': g['term'], 's': 'term', 'x': g['definition'][:200], 'h': f'#/term/{g["slug"]}'})
for fid, name, kicker, body, *_ in frames: index.append({'k': 'teaching', 't': name, 's': kicker, 'x': re.sub('<[^>]+>', '', body)[:200], 'h': f'#teach-{fid}'})
for p in podcasts: index.append({'k': 'podcast', 't': p.get('episode_title') or '', 's': f'{p.get("show") or ""} · {p.get("date") or ""}', 'x': (p.get('description') or '')[:160], 'h': p.get('youtube_url') or p.get('apple_url') or '#library'})
for c in catalog:
    desc = '' if is_boiler(c.get('description')) else (c.get('description') or '')
    index.append({'k': 'session', 't': c['title'], 's': c.get('date') or '', 'x': desc[:160], 'h': c.get('source_url') or '#library'})
for t in timeline: index.append({'k': 'timeline', 't': t['event'][:90], 's': t['year_or_date'], 'x': '', 'h': '#timeline'})

# slim videos for JS
for v in videos: v['title'] = clean_title2(v['title'])
vslim = [{k: v[k] for k in ('video_id','title','url','channel','official','content_type','format','year','year_reliable','year_basis','approx_word_count','opening_summary','qa_topics','topic_percentages','key_terms','quotes','predictions_and_dates','tools_or_exercises','named_entities','researcher_note','show','cluster')} for v in videos]
cl_slim = [{'id': c['id'], 'name': c['name'], 'members': c['members'], 'top_tags': c['top_tags'], 'top_terms': c['top_terms'], 'mean_words': c['mean_words']} for c in clusters]

NAV = [('#home', 'Home'), ('#who', 'Who'), ('#timeline', 'Timeline'), ('#teachings', 'Teachings'), ('#diagrams', 'Diagrams'), ('#analysis', 'Analysis'), ('#library', 'Library'), ('#glossary', 'Glossary'), ('#skeptics', 'Skeptics'), ('#sources', 'Sources')]
nav_html = ''.join(f'<a class="chip" href="{h}">{t}</a>' for h, t in NAV)
SIG = '<svg class="sig" viewBox="0 0 24 24" aria-hidden="true"><polygon points="12,3 21,20 3,20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/><circle cx="12" cy="14" r="2.4" fill="currentColor"/></svg>'
DEFS = '<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs><marker id="dg-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" class="dg-marker"/></marker><marker id="dg-arrow-2" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" class="dg-marker-2"/></marker></defs></svg>'

page = f'''<title>The Bashar Index</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,400;12..96,500;12..96,600;12..96,700;12..96,800&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400&family=IBM+Plex+Mono:wght@400;500;600&display=swap">
<style>{CSS}</style>
{DEFS}
<header class="mast"><div class="wrap"><div class="row"><a class="brand" href="#home">{SIG}The Bashar Index</a><form class="search" role="search" onsubmit="return false"><input id="q" type="search" placeholder="Search terms, sessions, diagrams…" aria-label="Search the index" autocomplete="off"></form><button class="theme-btn" id="themeBtn" aria-label="Toggle light/dark theme" title="Toggle theme"><svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="6" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M8 2a6 6 0 0 1 0 12z" fill="currentColor"/></svg></button></div><nav class="chips" aria-label="Sections">{nav_html}</nav></div></header>
<main>
{HOME}{WHO}{TIMELINE}{TEACH}{DIAG}{ANAL}{LIB}{GLOSS}{SKEP}{SRC}
</main>
<footer><div class="wrap"><p>The Bashar Index · an independent research reference compiled 11 September 2026 · not affiliated with, endorsed by, or speaking for Bashar Communications, Inc. or Darryl Anka. Bashar® is their mark. Claims about extraterrestrials, parallel realities and future events are reported as claims.</p><p><a href="#home">Back to top ↑</a></p></div></footer>
<div class="backdrop" id="backdrop"></div>
<aside class="sheet" id="sheet" role="dialog" aria-modal="true" aria-labelledby="sheetTitle"><div class="sh"><h3 id="sheetTitle">Detail</h3><button id="sheetLink" type="button">Copy link</button><button id="sheetClose" type="button" aria-label="Close">Close ✕</button></div><div class="sb" id="sheetBody"></div></aside>
<div class="tip" id="tip" role="tooltip"></div>
{json_block('d-videos', vslim)}
{json_block('d-diagrams', dg_meta)}
{json_block('d-glossary', gl_meta)}
{json_block('d-index', index)}
{json_block('d-tags', TAGL)}
{json_block('d-clusters', cl_slim)}
<script>{JS}</script>
'''
open(f'{S}/index.html', 'w').write(page)
print('written', len(page)/1024, 'KB', '| index entries', len(index), '| catalog rows', len(cat_rows), '| digests', N)
