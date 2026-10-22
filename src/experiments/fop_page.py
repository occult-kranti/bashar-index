# fop_page.py: builds experiments/frequency-of-place/index.html (site page) and fop_artifact.html (preview fragment).
#   python3 fop_page.py
import json, os, sys, re, html, math
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
DATA = f'{REPO}/data/experiments/frequency-of-place'
sys.path.insert(0, f'{REPO}/src'); sys.path.insert(0, HERE)
from css import CSS as SITE_CSS
import fop_diagrams as D

R = json.load(open(f'{REPO}/experiments/frequency-of-place/fp_results.json'))
SER = np.load(f'{DATA}/fp_series.npz')
GRAPH = json.load(open(f'{DATA}/graph.json'))
LIT = json.loads(re.search(r"```json\s*(\[.*?\])\s*```", open(f'{DATA}/literature.md').read(), re.S).group(1))
LIT_BY = {x['id']: x for x in LIT}
def esc(s): return html.escape(str(s if s is not None else ''), quote=True)
def hz(f): return f'{f / 1e3:.2f} kHz' if f >= 1e3 else f'{f:.0f} Hz'
from fop_diagrams import sci
def neg(x, fmt='.0f'): return format(x, fmt).replace('-', '−')
def mode(lab): return next(d for d in R['modes'] if d['label'] == lab)
sp, ct, le, air, st2, tab, sens, em = R['sphere'], R['contact'], R['location_effects'], R['air'], R['stage2'], R['table'], R['sensitivity'], R['em_cavity']
nmodes, nlines = R['n_modes_below_60k'], R['n_lines_below_60k']

# ------------------------------------------------------------------------------------------ CSS additions
EXTRA_CSS = r"""
/* page tokens for charts (validated for both themes) */
:root{--viz-s1:#0E8F7A;--viz-s2:#C47A1A;--viz-s3:#2F6DD0;--viz-s4:#B24A78;--viz-grid:rgba(20,24,34,.08);--viz-axis:rgba(20,24,34,.35);--viz-floor:#B24A78}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--viz-s1:#1BA58C;--viz-s2:#C98500;--viz-s3:#4F87E0;--viz-s4:#C46090;--viz-grid:rgba(232,236,242,.09);--viz-axis:rgba(232,236,242,.4);--viz-floor:#C46090}}
:root[data-theme="dark"]{--viz-s1:#1BA58C;--viz-s2:#C98500;--viz-s3:#4F87E0;--viz-s4:#C46090;--viz-grid:rgba(232,236,242,.09);--viz-axis:rgba(232,236,242,.4);--viz-floor:#C46090}
.viz-grid{stroke:var(--viz-grid);stroke-width:1} .viz-axis{stroke:var(--viz-axis);stroke-width:1.2;fill:none}
.viz-s1{color:var(--viz-s1)} .viz-s2{color:var(--viz-s2)} .viz-s3{color:var(--viz-s3)} .viz-s4{color:var(--viz-s4)}
.viz-stick{stroke:currentColor;stroke-width:2.2;stroke-linecap:round} .viz-dot{fill:currentColor;stroke:var(--surface);stroke-width:1.5}
.viz-line{fill:none;stroke:currentColor;stroke-width:2;stroke-linejoin:round} .viz-dashed{stroke-dasharray:6 4}
.viz-bar{fill:currentColor;opacity:.92} .viz-band{fill:currentColor;opacity:.85;rx:4} .viz-seq{fill:var(--viz-s1)} .viz-floor{stroke:var(--viz-floor);stroke-width:2;stroke-dasharray:5 4}
.viz-hit{fill:transparent} .viz-mark:hover .viz-stick,.viz-mark:hover .viz-bar,.viz-mark:hover .viz-band{opacity:.6} .viz-hover{fill:transparent}
.dg-copper-fill{fill:#b87333;stroke:#8f5a28;stroke-width:1}
.fig-scroll{overflow-x:auto;-webkit-overflow-scrolling:touch} .fig-scroll svg{min-width:560px}
figure.dgf{margin:18px 0} figure.dgf figcaption{font-size:.86rem;color:var(--muted);margin-top:8px}
.hero-fop{display:grid;grid-template-columns:1.2fr .8fr;gap:28px;align-items:start} @media(max-width:860px){.hero-fop{grid-template-columns:1fr}}
.kicker{font:600 .78rem var(--font-display);letter-spacing:.08em;text-transform:uppercase;color:var(--accent-ink)}
.lede{font-size:1.18rem;line-height:1.5;color:var(--ink-2);max-width:62ch}
.quote{border-left:3px solid var(--accent);padding:6px 14px;margin:14px 0;font-family:var(--font-body);font-style:italic;font-size:1.05rem}
.quote cite{display:block;font-style:normal;font-size:.84rem;color:var(--muted);margin-top:4px;font-family:var(--font-display)}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px} @media(max-width:760px){.grid2{grid-template-columns:1fr}}
.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:14px} @media(max-width:860px){.grid3{grid-template-columns:1fr 1fr}} @media(max-width:560px){.grid3{grid-template-columns:1fr}}
.stat{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:14px 16px;min-width:0}
.stat .v{font:700 1.6rem var(--font-display);letter-spacing:-.02em;font-variant-numeric:tabular-nums} .stat .l{font-size:.86rem;color:var(--muted)}
table.spec{width:100%;border-collapse:collapse;font-size:.92rem;font-variant-numeric:tabular-nums} table.spec th,table.spec td{padding:7px 8px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
table.spec th{font:600 .8rem var(--font-display);color:var(--muted);letter-spacing:.03em} table.spec td.num,table.spec th.num{text-align:right}
.tablewrap{overflow-x:auto} .ok{color:var(--accent-ink);font-weight:600}
.render{width:100%;height:auto;border-radius:12px;border:1px solid var(--line);display:block}
.net{position:relative;background:var(--surface);border:1px solid var(--line);border-radius:12px;overflow:hidden}
.net svg{width:100%;height:640px;display:block;touch-action:none;cursor:grab} .net svg:active{cursor:grabbing}
.net .ctl{display:flex;gap:8px;flex-wrap:wrap;padding:10px 12px;border-bottom:1px solid var(--line);align-items:center;font:500 .8rem var(--font-display)}
.net .ctl label{display:inline-flex;gap:5px;align-items:center;padding:3px 8px;border:1px solid var(--line-2);border-radius:999px;cursor:pointer}
.net .ctl input[type=search]{font:inherit;padding:4px 8px;border:1px solid var(--line-2);border-radius:8px;background:var(--bg);color:var(--ink);min-width:160px}
.net .info{padding:10px 12px;border-top:1px solid var(--line);font-size:.9rem;min-height:3.2em} .net .info a{word-break:break-all}
.nn{stroke:var(--surface);stroke-width:1.2} .nn.k-literature{fill:var(--viz-s1)} .nn.k-OpenAI{fill:var(--viz-s2)} .nn.k-Anthropic{fill:var(--viz-s3)} .nn.k-other{fill:var(--viz-s4)}
.nn.k-topic{fill:var(--surface);stroke:var(--ink);stroke-width:1.4} .nn.k-model,.nn.k-org{fill:var(--line-2)} .nn.k-experiment{fill:var(--accent)}
.ne{stroke:var(--line-2);stroke-opacity:.55;stroke-width:1} .ne.adj{stroke:var(--amber);stroke-opacity:.9;stroke-width:1.6;stroke-dasharray:4 3} .ne.feed{stroke:var(--accent);stroke-opacity:.7;stroke-width:1.4}
.nl{font:600 11px var(--font-display);} .nl-t{font-size:10.5px;font-weight:500;fill:var(--ink);pointer-events:none;paint-order:stroke;stroke:var(--surface);stroke-width:3px;stroke-linejoin:round}
.legend{display:flex;gap:14px;flex-wrap:wrap;font:500 .8rem var(--font-display);color:var(--ink-2);margin:8px 0} .legend i{display:inline-block;width:11px;height:11px;border-radius:50%;margin-right:5px;vertical-align:-1px}
details.srcs summary{cursor:pointer;font:600 .95rem var(--font-display)} details.srcs ol{font-size:.9rem} details.srcs li{margin-bottom:4px}
.pills{display:flex;gap:6px;flex-wrap:wrap;margin:10px 0}
.steps{counter-reset:s} .steps li{margin-bottom:10px}
.sec .wrap{max-width:1040px}
.mast .crumbs{font:500 .82rem var(--font-display);color:var(--muted)} .mast .crumbs a{color:var(--accent-ink);text-decoration:none}
@media (prefers-reduced-motion:reduce){.net svg *{transition:none}}
"""

# ------------------------------------------------------------------------------------------ copy
NAV = [('#claim', 'The claim'), ('#design', 'The bench'), ('#sphere', 'The sphere'), ('#place', 'The place'), ('#moves', 'What moves'),
       ('#protocol', 'Protocol'), ('#checks', 'Checks'), ('#papers', 'Papers'), ('#sources', 'Sources')]
SIG = '<svg class="sig" viewBox="0 0 24 24" aria-hidden="true"><polygon points="12,3 21,20 3,20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/><circle cx="12" cy="14" r="2.4" fill="currentColor"/></svg>'
DEFS = '<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs><marker id="dg-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" class="dg-marker"/></marker><marker id="dg-arrow-2" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" class="dg-marker-2"/></marker></defs></svg>'

def fig(svg, cap, scroll=True):
    return f'<figure class="dgf"><div class="{"fig-scroll" if scroll else ""}">{svg}</div><figcaption>{cap}</figcaption></figure>'

def quote(text, who, url, when=''):
    return f'<blockquote class="quote">“{esc(text)}”<cite>{esc(who)}{(" · " + esc(when)) if when else ""} · <a href="{esc(url)}" rel="noopener">source</a></cite></blockquote>'

YT = 'https://www.youtube.com/watch?v='
S_CLAIM = f'''
<section class="sec" id="claim"><div class="wrap">
<div class="kicker">What was said</div>
<h2>Bashar's copper-sphere experiment, in his words</h2>
<div class="prose">
<p>The idea behind this page appears in the index as a single sentence from a 2026 clip of Darryl Anka: location is a property of the object, not a place the object sits in. The experiment to go with it was found only on the web, in two session excerpts of a question-and-answer about gravity (the follow-up matches a question listed for the official 7 December 2014 session, <em>2015–2016: The Years of Expansion and Contraction</em>). Everything quoted here is a claim made in a channeling session or interview, reported as a claim.</p>
{quote("Location is a vibrational variable in the object itself.", "Darryl Anka, recounting Bashar", YT + "98KsASkO8Cs", "clip, 2026")}
{quote("Get a very, very, very flat table that's at least 6 to 10 ft long, very flat.", "Bashar, session excerpt", YT + "TWApwwr6mUk")}
{quote("Take a very thin copper ball, about 3 in, 4 in in diameter, hollow, very thin, as perfectly round as you can make it.", "Bashar, session excerpt", YT + "TWApwwr6mUk")}
{quote("Strike it and get it to vibrate or vibrate it through some other means. Measure those vibrations as precisely as you can.", "Bashar, session excerpt", YT + "TWApwwr6mUk")}
{quote("Then move the ball to the other end of the table and repeat that measurement. Find the difference in those two measurements.", "Bashar, session excerpt", YT + "TWApwwr6mUk")}
{quote("Bombard it, overwhelm it in a sense with the vibrational frequency that is specific to the other end of the table when the object was there.", "Bashar, session excerpt", YT + "TWApwwr6mUk")}
{quote("It will at least roll across the table to its new position and stop.", "Bashar, session excerpt", YT + "TWApwwr6mUk")}
{quote("As soon as your instruments are sensitive enough to tell the difference in the vibration of an object in two different locations…", "Bashar, session excerpt", YT + "TWApwwr6mUk")}
<p>The follow-up (Mammoth Awakening upload, Nov 2024) restates it as extracting <em>“the actual tone, the signature frequency of that pure, very thin-shelled copper sphere”</em>, moving it, extracting the tone at B, then <em>“bombard the sphere in location A with the vibrational tone of location B”</em>, after which it <em>“will stop and go no further because it has found its resting point within that vibrational equation”</em> (<a href="{YT}kQfWp5fD_MY" rel="noopener">source</a>). Anka's retellings span 2014 to 2026: BATGAP #236 (<em>“They may be very subtly different, but they're different”</em>, <a href="https://batgap.com/darryl-anka-bashar-transcript/" rel="noopener">transcript</a>), Next Level Soul Ep. 544, and Mayim Bialik's Breakdown (<em>“everything you consider to be a location has a specific signature frequency to it”</em>, <a href="https://singjupost.com/aliens-are-making-contact-3000-years-ahead-w-darryl-anka-transcript/" rel="noopener">transcript</a>). A session titled <em>Gravity</em> (fan transcript, c. 1997–2000) carries the general form: <em>“each object has its own vibration, its own signature frequency by which you can recognize it”</em> (<a href="https://www.bashararchive.com/transcript/gravity-part-1-of-4" rel="noopener">fan transcript</a>).</p>
<p><strong>What the protocol asks for, as stated:</strong> (1) a very flat table at least 6–10 ft long; (2) a thin, hollow, round copper sphere 3–4 in across; (3) the sphere's complete vibration, measured as precisely as possible at end A; (4) the same at end B; (5) the difference; (6) the sphere back at A, driven with B's tone, acoustically or electromagnetically; (7) watch whether it rolls to B and stops. Bashar gives no magnitude for the difference. This page designs steps 1–7 with today's instruments, computes what the instruments will read before any new effect, and states what each possible outcome would mean. It does not pronounce a result; the measurement would.</p>
<p class="muted" style="font-size:.9rem">Corpus check: of the 75 digested recordings only one (98KsASkO8Cs) states the claim; none contains the protocol. Catalogue sessions worth pulling for the full context: <em>How Bashar's Spaceship Flies</em> (1987), <em>Space Time Travel</em> (1991), <em>Resonance of the Land</em> (1997), <em>Gravity</em> (1997), <em>The Years of Expansion and Contraction</em> (7 Dec 2014).</p>
</div></div></section>'''

S_DESIGN = f'''
<section class="sec" id="design"><div class="wrap">
<div class="kicker">The bench</div>
<h2>The experiment, as designed</h2>
<div class="prose">
<p>Bashar's “very flat table” is a granite surface plate, the flattest large surface a machine shop owns: 2.4 × 1.2 × 0.25 m, grade AA (flat to about 13 µm over its length), about 1.9 t, on a three-point stand, levelled to within 20 µrad with an electronic level that reads 1 µrad. The sphere is an electroformed or two-piece spun copper shell, 88.9 mm (3½ in) outside diameter, 1.0 mm wall, {sp["mass_g"]:.0f} g, roundness held to 25 µm, with a 1 mm vent hole so that the air inside follows the air outside (the hole's own Helmholtz resonance is near {R["interior_air"]["vent_hole_helmholtz_Hz"]:.0f} Hz, far from everything else). Spot A and spot B are 1.6 m apart on the centreline; a third spot C, off-axis, is the control for the symmetric pair.</p>
<p>Three ways of exciting the sphere, all repeatable: a solenoid striker with a hard plastic tip that will not dent the copper (as Bashar says, “strike it”), an electromagnetic acoustic transducer coil that drives eddy currents in the copper without touching it, and a chirp from a small horn. Two ways of listening without touching: a laser Doppler vibrometer with beams at the equator and at 45° latitude (an equatorial beam alone misses the axisymmetric member of every odd-order multiplet), and a measurement microphone. The table itself gets an impact hammer and accelerometers. Each spot carries its own sensors for what makes a place a place: temperature, pressure, humidity, magnetic field, floor vibration, acoustic and radio background, and slope.</p>
</div>
{fig(D.bench_overview(R), 'Plan and side view, to scale. Both stations carry the same instruments so that the sphere is measured by the same chain at A and at B. Stage 1b uses a three-point sapphire cradle to make the support identical at both spots; an optional bell jar removes the air.')}
<div class="grid3">
<div class="stat"><div class="v">2.4 m</div><div class="l">granite plate, AA grade, 13 µm flat, 1 µrad level</div></div>
<div class="stat"><div class="v">{sp["OD_mm"]:.1f} mm</div><div class="l">copper shell, {sp["wall_mm"]:.1f} mm wall, {sp["mass_g"]:.0f} g</div></div>
<div class="stat"><div class="v">1.6 m</div><div class="l">from spot A to spot B, moved without rotation</div></div>
</div>
<h3 style="margin-top:22px">Parts and instruments</h3>
<div class="tablewrap"><table class="spec">
<tr><th>Item</th><th>Specification</th><th>Why</th></tr>
<tr><td>Granite surface plate</td><td>2.4 × 1.2 × 0.25 m, grade AA (ASME B89.3.7), 3-point stand on isolators</td><td>“very, very flat”; its own modes start near {tab["modes"][0]["f"]:.0f} Hz, far below the sphere's</td></tr>
<tr><td>Electronic level</td><td>Talyvel/Wyler class, 1 µrad resolution</td><td>a 1.5 mrad slope would roll the ball by itself (next sections)</td></tr>
<tr><td>Copper sphere</td><td>OFE copper, OD 88.9 mm, wall 1.0 ± 0.05 mm, roundness ≤ 25 µm, 1 mm vent hole, seam marked</td><td>“hollow, very thin, as perfectly round as you can make it”; the seam and any ovality split each multiplet</td></tr>
<tr><td>Support (stage 1b)</td><td>three sapphire balls on a PTFE ring, same part carried A → B</td><td>makes the contact the same at both spots</td></tr>
<tr><td>Striker</td><td>solenoid, 3 mm PEEK tip, timed pulse</td><td>Bashar's “strike it”, made repeatable without denting the shell</td></tr>
<tr><td>EMAT coil</td><td>meander coil + NdFeB magnet on a retracting arm, 5–60 kHz drive</td><td>“vibrate it through some other means”, without touching; the magnet is pulled back before the ring-down, since it damps the shell by eddy currents</td></tr>
<tr><td>Laser Doppler vibrometer</td><td>single-point, 0–100 kHz, through-glass capable; beams at the equator and at 45° latitude</td><td>non-contact pickup at ppm precision; two latitudes see every member of every multiplet</td></tr>
<tr><td>Microphone + horn</td><td>½-in measurement mic; compression driver for stage 2</td><td>air-borne spectrum; the acoustic “bombardment”</td></tr>
<tr><td>Coil driver (stage 2)</td><td>air-core coil, ≤ 1 mT at the ball, audio amplifier</td><td>the electromagnetic “bombardment”</td></tr>
<tr><td>Hammer + accelerometers</td><td>impact hammer, three 0.5 g accelerometers at A, B, C</td><td>the plate's response at each spot</td></tr>
<tr><td>Place sensors</td><td>PT100 (plate and air), barometer, RH, fluxgate magnetometer, seismic accelerometer, SDR</td><td>everything that differs between two places</td></tr>
<tr><td>Ball thermometer</td><td>the ball itself: the ratio of a torsional to the breathing line changes by {abs(R["precision"]["thermometry_ppm_per_K"]):.0f} ppm/K</td><td>a probe on a 1 mm shell would load it and an IR reading of polished copper fails; the two-line ratio resolves 10 mK</td></tr>
<tr><td>Motion read-out (stage 2)</td><td>laser displacement sensor, 1 µm; camera at 60 fps</td><td>detects creep long before rolling</td></tr>
<tr><td>DAQ</td><td>24-bit, 204.8 kS/s, 8 synchronous channels</td><td>sphere modes reach 60 kHz; one clock for all channels</td></tr>
</table></div>
</div></section>'''

m_s2, m_s3, m_t2, m_s0 = mode('S2'), mode('S3'), mode('T2'), mode('S0')
S_SPHERE = f'''
<section class="sec" id="sphere"><div class="wrap">
<div class="kicker">The sphere</div>
<h2>What the complete frequency of a copper sphere is</h2>
<div class="prose">
<p>A struck copper shell rings at its elastic resonances. For a thin complete sphere they come in families: a lower branch of spheroidal modes that starts with the five-fold “football” mode at {hz(m_s2["f"])}, torsional modes from {hz(m_t2["f"])}, and an upper branch that opens with the breathing mode at {hz(m_s0["f"])}. Below 60 kHz the model gives {nmodes} modes, which, because a perfect sphere's modes are degenerate (2l + 1 lines each), amount to {nlines} lines. A real sphere's seam and ovality split those lines, from a few parts in a thousand to a few percent depending on how even the wall is (Duffey and colleagues measured about 3 % for a ±5 % wall), so the measured spectrum is a comb of clusters. The complete spectrum in Bashar's sense is this comb: every line's frequency, width and amplitude.</p>
<p>The frequencies were computed two independent ways that agree to one part in 10⁹ (see <a href="#checks">checks</a>): the exact three-dimensional elasticity solution for a hollow sphere with both surfaces free (Lamb's 1882 problem extended to two surfaces) and a Rayleigh–Ritz solution of the same strain energy. Baker's membrane theory, a third route, agrees to one part in 10⁴ in the thin-wall limit and shows where bending takes over for this wall. Copper's elastic constants are the Ledbetter–Naimon 1974 values averaged for a polycrystal: E = {sp["E_GPa"]:.0f} GPa, G = {sp["G_GPa"]:.1f} GPa, ν = {sp["nu"]:.3f}, ρ = {sp["rho"]:.0f} kg/m³.</p>
</div>
{fig(D.spectrum_chart(R), f'Model spectrum of the {sp["OD_mm"]:.1f} mm × {sp["wall_mm"]:.0f} mm copper shell. Height is the number of degenerate lines in each multiplet; hover a stick for its mode. Bending stiffness lifts the lower branch above the membrane limit from l ≈ 4 upward.')}
{fig(D.mode_shapes(R), 'Cross-sections of the lowest modes, exaggerated. The football mode flexes the sphere into a spheroid; the breathing mode expands it uniformly; torsional modes twist the two hemispheres against each other.')}
{fig(D.spectrum_map(R), 'Everything that could be called a frequency of this sphere, on one log axis. The elastic ring is what the protocol measures; the nuclear-spin line is the only one tied to the place, through the magnetic field at that place.')}
<div class="tablewrap"><table class="spec">
<tr><th>Mode</th><th class="num">f (Hz)</th><th class="num">lines</th><th>family</th><th class="num">membrane theory (Hz)</th><th class="num">ppm/K</th></tr>
{"".join(f'<tr><td>{esc(d["label"])}</td><td class="num">{d["f"]:.1f}</td><td class="num">{d["deg"]}</td><td>{"torsional" if d["family"] == "T" else d["branch"] + " spheroidal"}</td><td class="num">{(f"{d["membrane"]:.0f}" if d.get("membrane") else "–")}</td><td class="num">{(neg(sens[d["label"]]["ppm_per_K"]) if d["label"] in sens else "")}</td></tr>' for d in R["modes"][:16])}
</table></div>
<p class="muted" style="font-size:.9rem">First 16 of {nmodes} modes below 60 kHz, in vacuum. The membrane column is Baker's closed form; the exact solution departs from it as bending takes over at higher l. The temperature coefficient is from the Overton–Gaffney 1955 slopes of copper's elastic constants. In air, the gas inside the shell shifts some of these lines by up to 0.16 % (next sections).</p>
</div></section>'''

tm = tab['modes']
S_PLACE = f'''
<section class="sec" id="place"><div class="wrap">
<div class="kicker">The place</div>
<h2>The frequency of a point on the table</h2>
<div class="prose">
<p>A point on a table has a spectrum of its own: tap it and it answers with the table's modes, weighted by how much each mode moves at that point. That driving-point response is measured with an impact hammer and an accelerometer; it is the standard way to give a location on a structure a frequency signature. For the granite plate the model's first six free modes lie between {tm[0]["f"]:.0f} and {tm[5]["f"]:.0f} Hz. Spots A and B are mirror images about the plate's centre, so an ideal plate gives them identical responses; spot C, off-axis, differs. That is a design choice: if A and B are meant to differ as places, the plate should not be able to tell them apart.</p>
<p>The sphere also changes the table's frequencies, by an amount that depends on where it sits: its {sp["mass_g"]:.0f} g shifts the fifth mode ({tm[4]["f"]:.0f} Hz) by {tm[4]["shift_ppm_A"]:.0f} ppm at A and {tm[4]["shift_ppm_C"]:.0f} ppm at C, and the second mode ({tm[1]["f"]:.0f} Hz) by {tm[1]["shift_ppm_A"]:.0f} ppm at A and {tm[1]["shift_ppm_C"]:.0f} ppm at C. That is a location-dependent frequency of the coupled system, and it is the ordinary kind: it comes from the mode shape of the plate. (The point-mass estimate holds for plate modes well below the ball's bounce on its contact, about {R["contact"]["bounce_mode_coupled_Hz"]:.0f} Hz.)</p>
</div>
{fig(D.table_modes(R, SER), 'Kirchhoff free-plate modes of the 2.4 × 1.2 × 0.25 m granite plate (one hue, darker = more motion). The plate is thick for its length, so real values run a few percent lower than this thin-plate model.')}
{fig(D.frf_chart(SER), 'Modelled driving-point accelerance at A, B and C with 1 % damping, relative scale. A and B coincide by symmetry; C has its own set of peaks.')}
<div class="prose"><p>Beyond the table, each place is described by what the place sensors log: surface and air temperature, pressure and humidity, the magnetic field vector, floor vibration, the acoustic and radio background, and slope. Those are the quantities the protocol must record at A and at B before any difference in the sphere can be attributed to the place rather than to the surroundings.</p></div>
</div></section>'''

S_MOVES = f'''
<section class="sec" id="moves"><div class="wrap">
<div class="kicker">What moves</div>
<h2>What changes when the ball changes place, in the baseline model</h2>
<div class="prose">
<p>Before any new physics, several known effects can make the sphere read differently at A and at B. The design has to measure or remove each of them so that only an unexplained difference would remain. The chart ranks them in parts per million of a mode frequency against the smallest difference the design can claim.</p>
</div>
{fig(D.budget_chart(R), 'Known effects, as modelled. The contact bars apply to the sphere resting directly on the plate (stage 1a); the cradle of stage 1b makes the contact repeatable and the bell jar removes the air, inside and out. The floor of about 2 ppm is set by how well the sphere’s temperature can be corrected, not by the electronics.')}
<div class="grid2">
<div class="card"><h4>Contact with the plate (large)</h4><p>Resting on granite, the shell touches at a Hertz contact {ct["hertz_diameter_um"]:.0f} µm across with a stiffness of {ct["k_hertz_N_per_m"] / 1e6:.1f} MN/m, comparable to the shell's own point stiffness ({ct["k_reissner_N_per_m"] / 1e6:.1f} MN/m). The model couples all axisymmetric modes through that spring (44 angular orders; the shifted lines are converged to 0.01 %, the bounce frequency to about 1 %): the m = 0 member of the football multiplet rises by {100 * ct["shift_hertz"][0]["rel"]:.2f} % ({ct["shift_hertz"][0]["contact"] - ct["shift_hertz"][0]["free"]:.0f} Hz), the two |m| = 1 members by about {100 * ct["m1_members"]["S2"]["m1_rel_first_order"]:.2f} % through friction, the rest hardly at all. A ±20 % change in contact stiffness between two spots moves the shifted line by {le["contact_variation_ppm"]:.0f} ppm. The contact also adds a rigid bounce mode near {ct["bounce_mode_coupled_Hz"]:.0f} Hz. This is why stage 1b carries the same cradle from A to B.</p></div>
<div class="card"><h4>Temperature (large)</h4><p>Copper's moduli fall with temperature: every mode shifts by about {neg(sens["S2"]["ppm_per_K"])} ppm per kelvin ({neg(sens["S0"]["ppm_per_K"])} for the breathing mode). A 0.5 K difference between the ends of a 2.4 m plate is 100 ppm. The sphere's temperature must be logged and the lines corrected with a coefficient measured on this sphere; correcting to 10 mK leaves 2 ppm, the design floor.</p></div>
<div class="card"><h4>Air outside and inside (large for some lines)</h4><p>Outside, air loads the shell and radiates its sound: in air the football mode's quality factor is limited to about {air["Q_rad_S2"]:.0f}, so a strike rings down in {air["tau_amp_ms"]:.0f} ms; the reactive part shifts frequencies by at most {air["reactive_shift_bound"] * 1e6:.0f} ppm, of which a 1 K change moves about {air["ppm_per_K_bound"]:.1f} ppm. Inside, the trapped air has cavity resonances of its own ({", ".join(f"{d['f'] / 1e3:.1f}" for d in R["interior_air"]["cavity_modes"][:8])} kHz …), and a shell line that sits near one of them is pulled: in the model the football line moves by {R["interior_air"]["shifts"]["S2"]["shift_ppm"]:+.0f} ppm and the l = 4 line by {R["interior_air"]["shifts"]["S4"]["shift_ppm"]:+.0f} ppm, the latter changing by {R["interior_air"]["shifts"]["S4"]["ppm_per_K"]:.0f} ppm per kelvin of air temperature, as much as the copper itself. The vent hole and the bell jar remove both effects; without a vent, a sealed shell in vacuum would carry {R["interior_air"]["sealed_in_vacuum_prestress_MPa"]:.1f} MPa of membrane stress.</p></div>
<div class="card"><h4>Motion (only while moving)</h4><p>While the sphere travels at 5 cm/s, a microphone hears every line Doppler-shifted by {le["doppler_ppm_at_0p05_m_per_s"]:.0f} ppm; the vibrometer, which measures surface velocity, does not. At rest the shift is zero.</p></div>
<div class="card"><h4>Fields (the one place-tag in the baseline model)</h4><p>Copper's nuclei precess at {le["nmr_63Cu_Hz_in_50uT"]:.0f} Hz (⁶³Cu) and {le["nmr_65Cu_Hz_in_50uT"]:.0f} Hz (⁶⁵Cu) in Earth's 50 µT field, {le["nmr_shift_Hz_per_uT"]:.1f} Hz per µT; the field across a lab varies by about 1 µT, so this frequency does differ between A and B. It is a property of the field at the place, measurable with a magnetometer. The static field does nothing to the elastic lines (eddy damping rate {sci(le["eddy_damping_rate_per_s"])} s⁻¹).</p></div>
<div class="card"><h4>Gravity (negligible)</h4><p>A one-tonne mass near one end changes g by {sci(le["gravity_delta_g_rel_1t_mass"])} of itself; through the shell's static stress that is {sci(le["gravity_freq_rel"])} of a mode frequency. The gravitational redshift of a clock moved 1 mm in height is {sci(le["redshift_rel_1mm"])}. Both are far below anything the bench can see.</p></div>
</div>
<div class="prose" style="margin-top:18px"><p>The frequency estimate itself is not the limit: fitting one {air["tau_amp_ms"]:.0f} ms ring-down at 40 dB signal-to-noise bounds the error at {R["precision"]["sigma_f_Hz_snr40dB"] * 1e3:.1f} mHz on a 10 kHz line (Cramér–Rao for a steady tone; two to three times that for a decaying one), or about {3 * R["precision"]["ppm_snr40"]:.1f} ppm at worst. The design floor of about 2 ppm is set by temperature and support repeatability, and it applies to lines measured in the bell jar or far from an interior air resonance.</p></div>
</div></section>'''

S_PROTOCOL = f'''
<section class="sec" id="protocol"><div class="wrap">
<div class="kicker">Protocol</div>
<h2>Three stages, with controls</h2>
{fig(D.protocol_chain(R), 'Stage 0 characterises the two places; stage 1 is Bashar’s measurement, made repeatable; stage 2 is his drive test, with the controls that separate a claimed effect from ordinary forces.')}
<div class="grid2">
<div class="card"><h4>Stage 0 · the places</h4><ol class="steps">
<li>Level the plate to ≤ 20 µrad; record flatness map.</li>
<li>Hammer survey: driving-point response at A, B, C (10 hits each).</li>
<li>Log at A and B for 24 h: temperature (plate, air), pressure, humidity, magnetic field, floor vibration, acoustic and RF background.</li>
<li>Put the sphere's own temperature coefficient on record: sweep 18–26 °C in the bell jar at A and fit ppm/K per line.</li></ol></div>
<div class="card"><h4>Stage 1 · the sphere's spectrum at A, then at B</h4><ol class="steps">
<li>Mark the seam; the sphere keeps the same orientation throughout.</li>
<li>1a, bare plate (Bashar's set-up): strike, EMAT and chirp excitation, 10 repeats each, re-seating the sphere between repeats; record LDV, microphone, ball temperature.</li>
<li>1b, cradle, then 1c, cradle in the bell jar: same sequence. The EMAT magnet is retracted before every ring-down.</li>
<li>Move to B along the centreline on a padded carrier, no rotation; repeat 1a–1c; return to A and repeat (A, B, A, B).</li>
<li>Fit every line (frequency, width, amplitude); read the ball's temperature from the torsional-to-breathing line ratio; correct for temperature and air density; compare A and B line by line.</li></ol></div>
<div class="card"><h4>Stage 2 · “the tone of B”, played at A</h4><ol class="steps">
<li>Build the drive signal from the B spectrum: all fitted lines at their amplitudes; also the A − B difference spectrum.</li>
<li>Play it at A through the horn (≤ 140 dB at the ball, inside an enclosure, hearing protection worn) and through the coil (≤ 1 mT, 20 % duty), one at a time, for 10 min each; record displacement at 1 µm, video, and the ball's temperature, since the coil alone warms it by about {st2["eddy_dT_per_10min_K"]:.1f} K per 10 min at full duty.</li>
<li>Controls, same durations: the A tone; band-limited noise; silence; and the same B tone with the driver moved to the far side of the ball. Map the sound field around the ball first: in a standing wave a ball drifts toward a pressure node whichever side the horn is on.</li>
<li>Repeat with the sphere at B driven with the A tone.</li></ol></div>
<div class="card"><h4>What each outcome would mean</h4><ul>
<li><strong>Stage 1, lines agree within the floor:</strong> no location signature above about 2 ppm at these two spots with this sphere. Bashar's protocol sets no magnitude, so this bounds it rather than closes it.</li>
<li><strong>Lines differ, and the difference follows temperature, contact or air:</strong> a difference of the surroundings, already in the budget.</li>
<li><strong>Lines differ, the difference survives the cradle and the bell jar, reverses on A ↔ B, and repeats:</strong> a candidate location signature; replicate on another plate, in another building, with another sphere.</li>
<li><strong>Stage 2, motion toward B that the controls do not produce:</strong> the thresholds below say what ordinary forces can do; anything beyond them, in the predicted direction, repeatable, is the signal the claim predicts.</li></ul></div>
</div>
<h3 style="margin-top:22px">Forces that can move the ball anyway</h3>
<div class="grid3">
<div class="stat"><div class="v">{st2["F_roll_mN"]:.1f} mN</div><div class="l">force that starts the {sp["mass_g"]:.0f} g ball rolling (rolling-resistance coefficient {st2["C_rr"]:.4f})</div></div>
<div class="stat"><div class="v">{st2["slope_threshold_mrad"]:.1f} mrad</div><div class="l">slope that rolls it by itself; the level reads 1 µrad</div></div>
<div class="stat"><div class="v">{st2["spl_for_rolling_dB"]:.0f} dB</div><div class="l">sound level at which radiation pressure in a travelling wave reaches the rolling threshold (120 dB gives {st2["F_acoustic_120dB_uN"]:.0f} µN)</div></div>
<div class="stat"><div class="v">{st2["F_eddy_1mT_mN"]:.1f} mN</div><div class="l">eddy-current push from a 1 mT coil field, directed away from the coil</div></div>
<div class="stat"><div class="v">1 µm</div><div class="l">displacement resolution: creep is visible long before rolling</div></div>
<div class="stat"><div class="v">4 controls</div><div class="l">A tone · noise · silence · driver on the far side</div></div>
</div>
<div class="prose" style="margin-top:14px"><p>In a travelling wave, radiation pressure and eddy-current forces push the ball <em>away from</em> the driver; the claim predicts motion <em>toward B</em> whichever side the driver is on. Putting the driver on the far side of the ball is therefore the decisive control: ordinary forces and the claimed effect then point in opposite directions. Vibration-induced creep is measured with the drive off, and tilt is checked with the level before and after every run.</p></div>
</div></section>'''

chk = R['checks']
S_CHECKS = f'''
<section class="sec" id="checks"><div class="wrap">
<div class="kicker">Checks</div>
<h2>Calculation check</h2>
<div class="prose"><p>Every number on this page comes from two Python files, <a href="sphere_modes.py">sphere_modes.py</a> and <a href="fp_model.py">fp_model.py</a>, published next to this page with their output, <a href="fp_results.json">fp_results.json</a>. The sphere frequencies are computed by methods that share only Hooke's law, and the solid-sphere limit is compared with published tables.</p></div>
<div class="tablewrap"><table class="spec">
<tr><th>Check</th><th>Method A</th><th>Method B or reference</th><th class="num">Agreement</th></tr>
{"".join(f'<tr><td>Solid sphere, ν = 0.33: {k}</td><td>exact determinant: ωR/c_T = {v["computed"]:.4f}</td><td>Lobo 1995 table: {v["literature"]:.4f}</td><td class="num ok">{sci(abs(v["computed"] / v["literature"] - 1), 1)}</td></tr>' for k, v in chk["solid_vs_lobo1995"].items())}
<tr><td>Hollow shell, {len(chk["A_vs_B"])} modes below 45 kHz</td><td>exact 3-D determinant (spherical Bessel functions)</td><td>Rayleigh–Ritz on the 3-D strain energy</td><td class="num ok">{sci(chk["A_vs_B_max_rel"], 1)}</td></tr>
<tr><td>Thin limit, 0.1 mm wall</td><td>exact 3-D determinant</td><td>Baker 1961 membrane theory</td><td class="num ok">{sci(chk["thin_limit_max_rel"], 1)}</td></tr>
<tr><td>Granite plate, square free plate test</td><td>Rayleigh–Ritz plate: {", ".join(f"{x:.3f}" for x in tab["leissa_check"]["computed"])}</td><td>Leissa 1969: {", ".join(f"{x:.3f}" for x in tab["leissa_check"]["literature"])}</td><td class="num ok">{sci(max(abs(a / b - 1) for a, b in zip(tab["leissa_check"]["computed"], tab["leissa_check"]["literature"])), 1)}</td></tr>
<tr><td>Thin-shell data point</td><td>membrane theory for Duffey et al. 2007's stainless float (R/h ≈ 71.5)</td><td>their measured n = 2 line: 5088 Hz vs their theory 5078 Hz</td><td class="num ok">reported</td></tr>
</table></div>
<div class="prose"><p>Inputs: Ledbetter & Naimon 1974 copper constants (C₁₁ = 169.1, C₁₂ = 122.2, C₄₄ = 75.42 GPa, Hill average); Overton & Gaffney 1955 temperature slopes; Johnson's contact mechanics for the Hertz contact; Reissner's point-load stiffness of a spherical shell; Leissa's free-plate values; the Cramér–Rao bound for a sinusoid in noise. The contact coupling, the interior air loading (first order in the added mass) and the exterior air bound are first-principles estimates, not fits to data; they set the size of the effects, not their last digit.</p></div>
{fig(D.software_stack(), 'Software stack. The prediction side is the two files behind this page; acquisition and modal analysis use open Python packages (pyEMA, sdypy, nidaqmx-python) plus the vibrometer’s own software.', scroll=True)}
</div></section>'''

# ------------------------------------------------------------------------------------------ papers / network
n_lab = sum(1 for n in GRAPH['nodes'] if n['kind'] == 'paper'); n_lit = sum(1 for n in GRAPH['nodes'] if n['kind'] == 'literature')
S_PAPERS = f'''
<section class="sec" id="papers"><div class="wrap">
<div class="kicker">Papers</div>
<h2>Papers and topics: a network chart</h2>
<div class="prose">
<p>Two bodies of work meet here. The physics and engineering literature the design rests on: {n_lit} sources in 13 topics, from Lamb's 1882 sphere to this year's machine-learning inversions of resonant ultrasound spectra. And the 2025–2026 science and mathematics releases of the AI laboratories: {n_lab} items from OpenAI, Anthropic, Google DeepMind and third parties, each with its verification status as reported (Lean-formalised, independently checked, author-verified, self-reported, or disputed).</p>
<p>The honest finding of the search: none of the laboratory releases touches elastic eigenvalue problems, modal analysis, inverse spectral problems or measurement design. The nearest are third-party, AI-assisted preprints on the Schiffer and Pompeiu eigenvalue problems and on the spectrum of a Laplacian on 3-spheres, drawn in amber. One caveat: the full contents file of OpenAI's bulk release could not be read, so a spectral paper buried in it cannot be ruled out. What this body of work offers the design is method: rigorous computer-assisted certificates for computed eigenvalues (from the third-party Schiffer preprint), independent formal checking as practised in the laboratory releases, and a documented list of ways agentic physics work goes wrong, including fabricated intermediate results and over-claimed verification.</p>
</div>
<div class="legend"><span><i style="background:var(--accent)"></i>this experiment</span><span><i style="background:var(--viz-s1)"></i>physics &amp; engineering literature</span><span><i style="background:var(--viz-s2)"></i>OpenAI</span><span><i style="background:var(--viz-s3)"></i>Anthropic</span><span><i style="background:var(--viz-s4)"></i>DeepMind, third party</span><span><i style="background:var(--surface);border:1.5px solid var(--ink)"></i>topic</span><span><i style="background:var(--line-2)"></i>model / organisation</span></div>
<div class="net" id="net">
<div class="ctl"><input id="netq" type="search" placeholder="Find a paper or topic" aria-label="Find a node"><label><input type="checkbox" class="netk" value="literature" checked> literature</label><label><input type="checkbox" class="netk" value="paper" checked> lab releases</label><label><input type="checkbox" class="netk" value="topic" checked> topics</label><label><input type="checkbox" class="netk" value="model" checked> models &amp; orgs</label><label><input type="checkbox" id="netlab"> labels</label><button type="button" id="netreset">Reset view</button></div>
<svg id="netsvg" viewBox="0 0 960 640" aria-label="Network chart of papers, topics and this experiment"><g id="netg"><g id="nete"></g><g id="netn"></g><g id="netl"></g></g></svg>
<div class="info" id="netinfo">Drag to pan, scroll or pinch to zoom, tap a node for its details and link. Amber dashed edges are the “adjacent to this experiment” links; teal edges feed the design.</div>
</div>
<details class="srcs" style="margin-top:14px"><summary>Laboratory releases as a list ({n_lab})</summary><div class="tablewrap"><table class="spec"><tr><th>Item</th><th>Org</th><th>Date</th><th>Field</th><th>Verification as reported</th></tr>
{"".join(f'<tr><td><a href="{esc(n["url"])}" rel="noopener">{esc(n["label"])}</a></td><td>{esc(n["org"])}</td><td>{esc(n["date"])}</td><td>{esc(n["field"])}</td><td>{esc(n["verified"])}</td></tr>' for n in sorted([n for n in GRAPH["nodes"] if n["kind"] == "paper"], key=lambda n: n["date"]))}
</table></div></details>
<p class="muted" style="font-size:.88rem;margin-top:10px">Counts and statuses were collected on 22 October 2026 from the laboratories' own pages, arXiv and the sources logged in the research notes. OpenAI's bulk release was announced as 722 manuscripts with 162 (22 %) Lean-formalised and three later retracted; its repository README, read the same day, lists 719 manuscripts in 372 families and puts the Lean-formalised share of top-line results at about 42 %. Both figures are the laboratory's own. Disputes (the October 2025 Erdős over-claim, the Navier–Stokes priority question) are recorded as disputes.</p>
</div></section>'''

# sources
lit_used = sorted({n['id'][4:] for n in GRAPH['nodes'] if n['kind'] == 'literature'}, key=lambda k: (k[0], int(re.sub(r'\D', '', k) or 0)))
S_SOURCES = f'''
<section class="sec" id="sources"><div class="wrap">
<div class="kicker">Sources</div>
<h2>Sources and method notes</h2>
<div class="prose">
<p><strong>Recordings.</strong> Session excerpts: <a href="{YT}TWApwwr6mUk" rel="noopener">Bashar Reveals How ET Ships Actually Travel Across the Universe</a> (Bashar Spiritual Insights; the protocol) and <a href="{YT}kQfWp5fD_MY" rel="noopener">How Objects Teleport: Bashar's Gravity and Frequency Experiment</a> (Mammoth Awakening, Nov 2024; the follow-up, matching a question listed for the 7 Dec 2014 session on <a href="https://vimeo.com/204074583" rel="noopener">Bashar Communications' Vimeo</a>). Interviews: <a href="{YT}98KsASkO8Cs" rel="noopener">Heart Coherence Collaborative clip</a> (2026); <a href="https://batgap.com/darryl-anka-bashar-transcript/" rel="noopener">BATGAP #236</a> (June 2014); <a href="https://nextlevelsoul.com/darryl-anka-2025/" rel="noopener">Next Level Soul Ep. 544</a> (Jan 2025); <a href="https://singjupost.com/aliens-are-making-contact-3000-years-ahead-w-darryl-anka-transcript/" rel="noopener">Mayim Bialik's Breakdown</a> (Mar 2026); <a href="https://www.bashararchive.com/transcript/gravity-part-1-of-4" rel="noopener">Gravity</a> (fan transcript, c. 1997).</p>
<p><strong>Transcripts.</strong> Wording was taken from auto-caption transcripts served by youtubetotranscript.com and from the podcast and interview sites linked above; the YouTube pages themselves and seven other transcript services were blocked or returned no captions. Quotes are kept to 30 words and link to the recording. A fifth video found in search, <em>What is Bashar's COPPER BALL TECHNIQUE?</em> (UEH7N1aZIZk), could not be opened.</p>
<p><strong>Numbers.</strong> All model values are from <code>fp_model.py</code> run on 22 October 2026 with the inputs listed under <a href="#checks">checks</a>; they describe a baseline, not a measurement. The sphere and plate are parametrised; change the inputs and rerun.</p>
<p><strong>Not affiliated.</strong> This page is part of an independent research site. It is not affiliated with, endorsed by, or connected to Bashar Communications, Inc. or Darryl Anka. Claims in sessions and interviews are reported as claims.</p>
</div>
<details class="srcs"><summary>Physics and engineering sources used in the design ({len(lit_used)})</summary><ol>
{"".join(f'<li><a href="{esc(LIT_BY[k].get("url", ""))}" rel="noopener">{esc(LIT_BY[k]["title"])}</a> — {esc(LIT_BY[k].get("authors", ""))}, {esc(LIT_BY[k].get("venue", ""))} {esc(LIT_BY[k].get("year", ""))}</li>' for k in lit_used if k in LIT_BY)}
</ol></details>
</div></section>'''

# ------------------------------------------------------------------------------------------ network JS
NET_JS = r"""
(function(){
const G=JSON.parse(document.getElementById('d-graph').textContent);
const svg=document.getElementById('netsvg'), gE=document.getElementById('nete'), gN=document.getElementById('netn'), gL=document.getElementById('netl'), root=document.getElementById('netg'), info=document.getElementById('netinfo');
const N=G.nodes, E=G.edges; const byId={}; N.forEach((n,i)=>{byId[n.id]=n; n.i=i;});
const W=960,H=640; const kindOf=n=>n.kind==='paper'?(n.org==='OpenAI'?'OpenAI':n.org==='Anthropic'?'Anthropic':'other'):n.kind;
const deg={}; E.forEach(e=>{deg[e.source]=(deg[e.source]||0)+1; deg[e.target]=(deg[e.target]||0)+1;});
const rad=n=>n.kind==='experiment'?16:n.kind==='topic'?6+Math.min(8,(deg[n.id]||0)*0.6):n.kind==='paper'?6:n.kind==='literature'?4.5:4;
// two-column layout: physics topics left, AI-lab topics right, the experiment in the middle; papers fan out from their topic
const CX=W/2, CY=H/2;
const topics=N.filter(n=>n.kind==='topic'); const phys=topics.filter(n=>n.side==='physics'), lab=topics.filter(n=>n.side!=='physics');
const degOf=n=>deg[n.id]||0;
phys.sort((a,b)=>degOf(b)-degOf(a)); lab.sort((a,b)=>degOf(b)-degOf(a));
function column(list,x,y0,y1){list.forEach((n,i)=>{n.x=x; n.y=y0+(y1-y0)*(i+0.5)/list.length; n.col=x<CX?-1:1;});}
column(phys,CX-130,70,H-70); column(lab,CX+130,36,H-36);
const about={}; E.forEach(e=>{if(e.rel==='about'){(about[e.source]=about[e.source]||[]).push(byId[e.target]);}});
let seed=11; const rnd=()=>{seed=(seed*9301+49297)%233280; return seed/233280;};
const exp=N.find(n=>n.kind==='experiment'); exp.x=CX; exp.y=CY;
const perTopic={}; 
N.filter(n=>n.kind==='paper'||n.kind==='literature').forEach(n=>{
  const ts=(about[n.id]||[]).filter(t=>t.col!==undefined); const t=ts[0];
  const side=n.kind==='literature'?-1:1;
  const k=(perTopic[t?t.id:'none'+side]=(perTopic[t?t.id:'none'+side]||0)+1);
  const yt=t?t.y:CY; const xt=t?t.x:CX+side*150;
  n.x=xt+side*(198+(k%3)*36); n.y=yt+((k-1)-(k%3))*0.5*12*(k%2?1:-1)+(rnd()-0.5)*8; n.col=side;});
N.filter(n=>n.kind==='model'||n.kind==='org').forEach(n=>{
  const ps=E.filter(e=>(e.rel==='produced_by'||e.rel==='authored_by')&&e.target===n.id).map(e=>byId[e.source]).filter(p=>p&&p.y!==undefined);
  const ym=ps.length?ps.reduce((s,p)=>s+p.y,0)/ps.length:CY; n.x=CX+446+(rnd()-0.5)*16; n.y=ym+(rnd()-0.5)*20; n.col=1;});
N.forEach(n=>{n.ax=n.x;n.ay=n.y;});
const L=E.map(e=>({s:byId[e.source],t:byId[e.target],rel:e.rel})).filter(l=>l.s&&l.t);
// relax overlaps (vertical mostly), pull back to the assigned position
for(let k=0;k<160;k++){
  for(let i=0;i<N.length;i++){const a=N[i]; if(a.kind==='experiment')continue; for(let j=i+1;j<N.length;j++){const b=N[j]; if(b.kind==='experiment')continue; let dx=b.x-a.x, dy=b.y-a.y; const d=Math.sqrt(dx*dx+dy*dy)+0.01; const min=rad(a)+rad(b)+7; if(d<min){const f=(min-d)/d*0.5; dx*=f;dy*=f; a.x-=dx*0.3;a.y-=dy;b.x+=dx*0.3;b.y+=dy;}}}
  N.forEach(n=>{if(n.kind==='experiment')return; n.x+=(n.ax-n.x)*0.1; n.y+=(n.ay-n.y)*0.04; n.x=Math.max(12,Math.min(W-12,n.x)); n.y=Math.max(12,Math.min(H-12,n.y));});
}
// draw
const ns='http://www.w3.org/2000/svg';
const lines=L.map(l=>{const el=document.createElementNS(ns,'line'); el.setAttribute('class','ne'+(l.rel==='adjacent_to_experiment'?' adj':l.rel==='feeds_experiment'?' feed':'')); gE.appendChild(el); return el;});
const circles=N.map(n=>{const el=document.createElementNS(ns,'circle'); el.setAttribute('r',rad(n)); el.setAttribute('class','nn k-'+kindOf(n)); el.dataset.id=n.id; el.setAttribute('tabindex','0'); el.setAttribute('role','button'); el.setAttribute('aria-label',n.label); gN.appendChild(el); return el;});
const labels=N.map(n=>{const el=document.createElementNS(ns,'text'); el.setAttribute('class','nl'+(n.kind==='topic'?' nl-t':'')); el.textContent=n.kind==='experiment'?'this experiment':(n.kind==='topic'&&n.label.length>30?n.label.slice(0,29)+'…':n.label); if(n.kind==='topic'&&n.col<0) el.setAttribute('text-anchor','end'); el.style.display=(n.kind==='experiment'||n.kind==='topic')?'':'none'; gL.appendChild(el); return el;});
function place(){lines.forEach((el,i)=>{const l=L[i]; el.setAttribute('x1',l.s.x);el.setAttribute('y1',l.s.y);el.setAttribute('x2',l.t.x);el.setAttribute('y2',l.t.y);});
 circles.forEach((el,i)=>{el.setAttribute('cx',N[i].x);el.setAttribute('cy',N[i].y);}); labels.forEach((el,i)=>{const n=N[i]; const left=(n.kind==='topic'&&n.col<0); el.setAttribute('x',left?n.x-rad(n)-4:n.x+rad(n)+3);el.setAttribute('y',n.kind==='experiment'?n.y+rad(n)+14:n.y+4); if(n.kind==='experiment'){el.setAttribute('text-anchor','middle'); el.setAttribute('x',n.x);}});}
place();
// pan/zoom
let tx=0,ty=0,sc=1; const apply=()=>root.setAttribute('transform',`translate(${tx},${ty}) scale(${sc})`);
let drag=null; svg.addEventListener('pointerdown',e=>{drag={x:e.clientX,y:e.clientY,tx,ty}; svg.setPointerCapture(e.pointerId);});
svg.addEventListener('pointermove',e=>{if(!drag)return; const r=svg.getBoundingClientRect(); const k=W/r.width; tx=drag.tx+(e.clientX-drag.x)*k; ty=drag.ty+(e.clientY-drag.y)*k; apply();});
svg.addEventListener('pointerup',()=>drag=null); svg.addEventListener('pointercancel',()=>drag=null);
svg.addEventListener('wheel',e=>{e.preventDefault(); const r=svg.getBoundingClientRect(); const k=W/r.width; const mx=(e.clientX-r.left)*k, my=(e.clientY-r.top)*k; const f=e.deltaY<0?1.15:1/1.15; tx=mx-(mx-tx)*f; ty=my-(my-ty)*f; sc*=f; apply();},{passive:false});
let pinch=null; svg.addEventListener('touchstart',e=>{if(e.touches.length===2){pinch=Math.hypot(e.touches[0].clientX-e.touches[1].clientX,e.touches[0].clientY-e.touches[1].clientY);}},{passive:true});
svg.addEventListener('touchmove',e=>{if(e.touches.length===2&&pinch){const d=Math.hypot(e.touches[0].clientX-e.touches[1].clientX,e.touches[0].clientY-e.touches[1].clientY); const f=d/pinch; pinch=d; sc*=f; tx=W/2-(W/2-tx)*f; ty=H/2-(H/2-ty)*f; apply(); e.preventDefault();}},{passive:false});
document.getElementById('netreset').addEventListener('click',()=>{tx=0;ty=0;sc=1;apply();});
// filters, search, labels
const boxes=Array.from(document.querySelectorAll('.netk')); const q=document.getElementById('netq'); const labBox=document.getElementById('netlab');
function refresh(){const on=new Set(boxes.filter(b=>b.checked).map(b=>b.value)); const s=q.value.trim().toLowerCase();
 const vis=N.map(n=>{const k=n.kind==='org'?'model':n.kind; return (n.kind==='experiment'||on.has(k))&&(!s||n.label.toLowerCase().includes(s)||(n.summary||'').toLowerCase().includes(s));});
 circles.forEach((el,i)=>{el.style.display=vis[i]?'':'none'; el.style.opacity=(s&&vis[i])?'1':'';});
 labels.forEach((el,i)=>{const n=N[i]; el.style.display=(vis[i]&&(labBox.checked||n.kind==='experiment'||n.kind==='topic'||(s&&s.length>1)))?'':'none';});
 lines.forEach((el,i)=>{el.style.display=(vis[L[i].s.i]&&vis[L[i].t.i])?'':'none';});}
boxes.forEach(b=>b.addEventListener('change',refresh)); q.addEventListener('input',refresh); labBox.addEventListener('change',refresh);
function show(n){const esc=s=>String(s||'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
 info.innerHTML=`<strong>${esc(n.label)}</strong>${n.org?' · '+esc(n.org):''}${n.date?' · '+esc(n.date):''}${n.verified?' · <em>'+esc(n.verified)+'</em>':''}<br>${esc(n.summary||'')}${n.url&&n.url!=='#design'?' <a href="'+esc(n.url)+'" rel="noopener">open ↗</a>':''}`;}
gN.addEventListener('click',e=>{const el=e.target.closest('circle'); if(el) show(byId[el.dataset.id]);});
gN.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){const el=e.target.closest('circle'); if(el){e.preventDefault(); show(byId[el.dataset.id]);}}});
gN.addEventListener('pointerover',e=>{const el=e.target.closest('circle'); if(el) show(byId[el.dataset.id]);});
})();
"""
PAGE_JS = r"""
(function(){
const $=(s,r=document)=>r.querySelector(s), $$=(s,r=document)=>Array.from(r.querySelectorAll(s));
const root=document.documentElement;
try{const t=localStorage.getItem('bx-theme'); if(t==='dark'||t==='light') root.setAttribute('data-theme',t);}catch(e){}
$('#themeBtn')?.addEventListener('click',()=>{const cur=root.getAttribute('data-theme'); const sys=matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light'; const now=(cur||sys)==='dark'?'light':'dark'; root.setAttribute('data-theme',now); try{localStorage.setItem('bx-theme',now);}catch(e){}});
const chips=$$('.chips a.chip'); const secs=chips.map(c=>$(c.getAttribute('href'))).filter(Boolean);
if('IntersectionObserver' in window){const io=new IntersectionObserver(es=>{es.forEach(e=>{if(e.isIntersecting){chips.forEach(c=>c.removeAttribute('aria-current'));const c=chips.find(x=>x.getAttribute('href')==='#'+e.target.id);if(c)c.setAttribute('aria-current','true');}});},{rootMargin:'-40% 0px -55% 0px'}); secs.forEach(s=>io.observe(s));}
const tip=$('#tip');
document.addEventListener('mouseover',e=>{const t=e.target.closest('[data-tip]'); if(!t){tip.classList.remove('on');return;} tip.textContent=t.getAttribute('data-tip'); tip.classList.add('on');});
document.addEventListener('mousemove',e=>{if(!tip.classList.contains('on'))return; const w=tip.offsetWidth,h=tip.offsetHeight; let x=e.clientX+14,y=e.clientY+14; if(x+w>innerWidth-8)x=e.clientX-w-10; if(y+h>innerHeight-8)y=e.clientY-h-10; tip.style.left=x+'px'; tip.style.top=y+'px';});
document.addEventListener('mouseout',e=>{if(e.target.closest('[data-tip]'))tip.classList.remove('on');});
document.addEventListener('click',e=>{const t=e.target.closest('[data-tip]'); if(!t){return;} tip.textContent=t.getAttribute('data-tip'); tip.classList.add('on'); const r=t.getBoundingClientRect(); tip.style.left=Math.max(8,Math.min(innerWidth-tip.offsetWidth-8,r.left))+'px'; tip.style.top=(r.bottom+8)+'px'; setTimeout(()=>tip.classList.remove('on'),3500);});
})();
"""

def build(artifact=False, render_src='render-bench.jpg', render2_src='render-station.jpg'):
    hero = f'''
<section class="sec" id="home"><div class="wrap">
<div class="hero-fop">
<div>
<div class="kicker">Experiment design · The Bashar Index</div>
<h1>The frequency of a place</h1>
<p class="lede">Bashar's own test of “location is a vibrational variable in the object itself”: capture the complete ring of a thin copper sphere at one end of a very flat table, capture it again at the other end, find the difference, then play the second place's tone to the first. This page designs that bench with today's instruments, computes what they would read before any new effect, and says what each outcome would mean.</p>
<div class="pills"><span class="pill acc">design, not a verdict</span><span class="pill">model numbers, not measurements</span><span class="pill">{nmodes} modes · {nlines} lines below 60 kHz</span><span class="pill amber">claims reported as claims</span></div>
</div>
<div><img class="render" src="{render_src}" alt="Rendered view of the granite table with the copper sphere at spot A, the marked spot B, two laser vibrometers, striker and coil stations, and the data acquisition bench" width="1920" height="1080"><p class="muted" style="font-size:.84rem;margin-top:6px">Visualization of the bench. Screens show model values.</p></div>
</div>
</div></section>'''
    render2 = f'<figure class="dgf"><img class="render" src="{render2_src}" alt="Close view of station A: the copper sphere on the granite with the laser beam on its equator, the solenoid striker, the EMAT coil, the microphone and the place-sensor box" width="1920" height="1080"><figcaption>Station A, close: striker (left), copper shell with its seam, EMAT coil behind, microphone (right), place sensors in front, vibrometer beam on the equator.</figcaption></figure>'
    body = hero + S_CLAIM + S_DESIGN.replace('<h3 style="margin-top:22px">Parts and instruments</h3>', render2 + '<h3 style="margin-top:22px">Parts and instruments</h3>') + S_SPHERE + S_PLACE + S_MOVES + S_PROTOCOL + S_CHECKS + S_PAPERS + S_SOURCES
    nav = ''.join(f'<a class="chip" href="{h}">{t}</a>' for h, t in NAV)
    index_href = '../../index.html' if not artifact else 'https://occult-kranti.github.io/bashar-index/'
    head_mast = f'''<header class="mast"><div class="wrap"><div class="row"><a class="brand" href="{index_href}">{SIG}The Bashar Index</a><span class="crumbs"><a href="{index_href}">Index</a> › Experiments › The frequency of a place</span><button class="theme-btn" id="themeBtn" aria-label="Toggle light/dark theme" title="Toggle theme"><svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="6" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M8 2a6 6 0 0 1 0 12z" fill="currentColor"/></svg></button></div><nav class="chips" aria-label="Sections">{nav}</nav></div></header>'''
    footer = '''<footer><div class="wrap"><p>The Bashar Index · experiment design page compiled 22 October 2026 · not affiliated with, endorsed by, or speaking for Bashar Communications, Inc. or Darryl Anka. Bashar® is their mark. Claims about extraterrestrials, parallel realities and location as a vibrational variable are reported as claims; the numbers here are model values for a bench that has not been built.</p><p><a href="#home">Back to top ↑</a></p></div></footer>'''
    graph_json = json.dumps(GRAPH, ensure_ascii=False).replace('</', '<\\/')
    inner = f'''<title>The Frequency of a Place</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,400;12..96,500;12..96,600;12..96,700;12..96,800&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400&family=IBM+Plex+Mono:wght@400;500;600&display=swap">
<style>{SITE_CSS}{EXTRA_CSS}</style>
{DEFS}
{head_mast}
<main>{body}</main>
{footer}
<div class="tip" id="tip" role="tooltip"></div>
<script type="application/json" id="d-graph">{graph_json}</script>
<script>{PAGE_JS}</script>
<script>{NET_JS}</script>
'''
    if artifact:
        return '<meta name="claude:viewport-fit-sides" content="cover">\n' + inner
    return f'<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n<meta name="description" content="Design of Bashar\'s copper-sphere experiment: the complete vibration spectrum of a thin copper sphere at two places on a flat table, the spectrum of each place, and a drive test with controls.">\n' + inner.replace('</style>', '</style>\n</head>\n<body>', 1).replace('<title>', '<title>', 1) + '</body>\n</html>\n'

if __name__ == '__main__':
    out_dir = f'{REPO}/experiments/frequency-of-place'
    os.makedirs(out_dir, exist_ok=True)
    page = build(False)
    # move the stylesheet links into head: the title/link/style already precede the body split above
    open(f'{out_dir}/index.html', 'w').write(page)
    # open(f'{HERE}/fop_artifact.html', 'w').write(build(True, 'render-bench.jpg', 'render-station.jpg'))  # claude.ai preview copy
    print('written', len(page) / 1024, 'KB')
