# fop_diagrams.py: inline-SVG diagrams for the "frequency of a place" experiment page.
# Styling goes through CSS classes defined in the page (site .dg-* classes + .viz-* chart classes), so the
# diagrams follow the site theme in light and dark mode. Numbers come from calc/fp_results.json.
import json, math, html

def esc(s): return html.escape(str(s), quote=True)

class S:
    """Tiny SVG string builder."""
    def __init__(self, w, h, title, cls='dg', extra=''):
        self.w, self.h, self.title, self.cls, self.extra = w, h, title, cls, extra; self.b = []
    def add(self, s): self.b.append(s); return self
    def text(self, x, y, s, cls='dg-text', anchor='start', size=13, weight=None, italic=False, extra=''):
        st = f'font-size:{size}px' + (f';font-weight:{weight}' if weight else '') + (';font-style:italic' if italic else '')
        self.b.append(f'<text x="{x:.1f}" y="{y:.1f}" class="{cls}" text-anchor="{anchor}" style="{st}" {extra}>{esc(s)}</text>'); return self
    def rect(self, x, y, w, h, cls='dg-line', rx=4, extra=''):
        self.b.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" class="{cls}" {extra}/>'); return self
    def line(self, x1, y1, x2, y2, cls='dg-line', extra=''):
        self.b.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" class="{cls}" {extra}/>'); return self
    def arrow(self, x1, y1, x2, y2, cls='dg-line', marker='dg-arrow'):
        self.b.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" class="{cls}" marker-end="url(#{marker})"/>'); return self
    def circle(self, cx, cy, r, cls='dg-line', extra=''):
        self.b.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" class="{cls}" {extra}/>'); return self
    def path(self, d, cls='dg-line', extra=''):
        self.b.append(f'<path d="{d}" class="{cls}" {extra}/>'); return self
    def poly(self, pts, cls='dg-line', extra='', close=True):
        d = 'M' + ' L'.join(f'{x:.1f},{y:.1f}' for x, y in pts) + (' Z' if close else '')
        self.b.append(f'<path d="{d}" class="{cls}" {extra}/>'); return self
    def g(self, inner, extra=''):
        self.b.append(f'<g {extra}>{inner}</g>'); return self
    def __str__(self):
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" role="img" aria-label="{esc(self.title)}" class="{self.cls}" {self.extra}>'
                + ''.join(self.b) + '</svg>')

SUPD = str.maketrans('0123456789-', '⁰¹²³⁴⁵⁶⁷⁸⁹⁻')
def sci(v, nd=0):
    if v == 0: return '0'
    e = int(math.floor(math.log10(abs(v)))); mant = v / 10 ** e
    if round(mant, nd) >= 10: mant /= 10; e += 1
    ms = f'{mant:.{nd}f}'
    return (f'{ms}×10' if not (nd == 0 and ms == '1') else '10') + str(e).translate(SUPD)

def fmt_hz(f):
    return f'{f / 1e3:.2f} kHz' if f >= 1e3 else f'{f:.0f} Hz'

# ------------------------------------------------------------------------------------------ D1: bench overview
def bench_overview(R):
    W, H = 760, 660; s = S(W, H, 'Plan and side view of the flat-table bench with the copper sphere at A and B')
    # ---- plan view
    px, py, pw, ph = 60, 84, 640, 320          # the plate 2.4 x 1.2 m -> 640 x 320 px (scale 266.7 px/m)
    sc = pw / 2.4
    s.text(px, 32, 'Plan view · granite surface plate 2.4 × 1.2 m (8 × 4 ft), grade AA, levelled', 'dg-text', size=15, weight=650)
    s.rect(px, py, pw, ph, 'dg-line dg-fill-2', rx=3)
    # grid metre marks
    for i in range(1, 24):
        x = px + i * 0.1 * sc
        s.line(x, py + ph, x, py + ph + (8 if i % 10 == 0 else 4), 'dg-line-2')
    for i in (0, 1, 2):
        s.text(px + i * sc, py + ph + 24, f'{i} m', 'dg-muted', 'middle', 12)
    s.text(px + 2.4 * sc, py + ph + 24, '2.4 m', 'dg-muted', 'middle', 12)
    # A and B positions (0.4 m from the ends on the centreline), C off-axis control
    Ax, Ay = px + 0.4 * sc, py + ph / 2; Bx, By = px + 2.0 * sc, py + ph / 2; Cx, Cy = px + 2.1 * sc, py + 0.15 * sc
    for (x, y, lab) in ((Ax, Ay, 'A'), (Bx, By, 'B')):
        s.circle(x, y, 0.0445 * sc, 'dg-copper-fill')
        s.circle(x, y, 0.0445 * sc + 6, 'dg-line-2')
        s.text(x, y - 0.0445 * sc - 12, lab, 'dg-text', 'middle', 16, 700)
    s.circle(Cx, Cy, 6, 'dg-line-2'); s.text(Cx - 10, Cy + 5, 'C  (off-axis control)', 'dg-muted', 'end', 12)
    s.arrow(Ax + 0.06 * sc, Ay + 0.44 * sc, Bx - 0.06 * sc, By + 0.44 * sc, 'dg-line-2', 'dg-arrow-2')
    s.text((Ax + Bx) / 2, Ay + 0.44 * sc + 18, 'move 1.6 m along the centreline, no rotation (seam mark kept facing +y)', 'dg-muted', 'middle', 12)
    # instruments at each station (symmetric)
    def station(x, y, side):
        d = 1 if side == 'right' else -1
        # laser Doppler vibrometer head outside the plate edge, looking along +y at the sphere's equator
        s.rect(x - 22, py - 30, 44, 24, 'dg-line dg-fill', rx=3); s.text(x, py - 13, 'LDV', 'dg-text', 'middle', 11, 650)
        s.line(x, py - 6, x, y - 0.0445 * sc - 8, 'dg-accent', 'stroke-dasharray="2 3"')
        # striker (solenoid) and EMAT coil below the ball, 45 deg either side
        for (dx, lab) in ((d * 0.2 * sc, 'striker'), (-d * 0.2 * sc, 'EMAT')):
            s.rect(x + dx - 20, y + 0.2 * sc, 40, 18, 'dg-line dg-fill', rx=3); s.text(x + dx, y + 0.2 * sc + 13, lab, 'dg-text', 'middle', 10)
            s.line(x + dx, y + 0.2 * sc, x + dx * 0.22, y + 0.055 * sc, 'dg-line-2')
        # microphone, upper outer side
        s.circle(x - d * 0.24 * sc, y - 0.18 * sc, 5, 'dg-line'); s.text(x - d * 0.24 * sc, y - 0.18 * sc - 9, 'mic', 'dg-text', 'middle', 10)
        # place sensors cluster, upper inner side
        bx0 = x + d * 0.12 * sc - (0 if d > 0 else 74)
        s.rect(bx0, y - 0.33 * sc, 74, 40, 'dg-line-2', rx=3)
        s.text(bx0 + 37, y - 0.33 * sc + 12, 'T · P · RH', 'dg-muted', 'middle', 9)
        s.text(bx0 + 37, y - 0.33 * sc + 23, 'B-field · seismic', 'dg-muted', 'middle', 9)
        s.text(bx0 + 37, y - 0.33 * sc + 34, 'acoustic · RF', 'dg-muted', 'middle', 9)
        # table accelerometer + hammer point
        s.rect(x + d * 0.1 * sc - 5, y + 0.07 * sc - 5, 10, 10, 'dg-ink-fill', rx=2)
        s.text(x + d * 0.1 * sc + d * 9, y + 0.07 * sc + 4, 'accel', 'dg-muted', 'start' if d > 0 else 'end', 10)
    station(Ax, Ay, 'right'); station(Bx, By, 'left')
    # levelling feet + electronic level
    for (x, y) in ((px + 0.15 * sc, py + 0.15 * sc), (px + 2.25 * sc, py + 0.15 * sc), (px + 1.2 * sc, py + 1.05 * sc)):
        s.circle(x, y, 7, 'dg-line-2'); s.circle(x, y, 2, 'dg-ink-fill')
    s.text(px + pw, py + ph + 24, 'levelling feet ◎ · electronic level reads 1 µrad', 'dg-muted', 'end', 11)
    # ---- side view
    sy = 540
    s.text(px, sy - 18, 'Side view', 'dg-text', size=15, weight=650)
    s.rect(px, sy, pw, 0.25 * sc, 'dg-line dg-fill-2', rx=2)
    s.text(px + pw - 6, sy + 0.25 * sc / 2 + 5, '250 mm granite · ≈ 1.9 t', 'dg-muted', 'end', 11)
    for x in (px + 0.3 * sc, px + 2.1 * sc, px + 1.2 * sc):
        s.rect(x - 10, sy + 0.25 * sc, 20, 36, 'dg-line', rx=2)
    s.line(px - 20, sy + 0.25 * sc + 36, px + pw + 20, sy + 0.25 * sc + 36, 'dg-line')
    s.text(px + pw, sy + 0.25 * sc + 54, 'stand on isolators · floor', 'dg-muted', 'end', 11)
    for (x, lab) in ((Ax, 'A'), (Bx, 'B')):
        # sphere resting on the plate (stage 1a) and on a three-point sapphire cradle (stage 1b, dashed)
        s.circle(x, sy - 0.0445 * sc, 0.0445 * sc, 'dg-copper-fill')
        s.text(x, sy - 0.0445 * sc * 2 - 10, lab, 'dg-text', 'middle', 14, 700)
    s.circle(Ax + 0.55 * sc, sy - 0.0445 * sc - 8, 0.0445 * sc, 'dg-line-2')
    s.poly([(Ax + 0.55 * sc - 14, sy), (Ax + 0.55 * sc - 10, sy - 8), (Ax + 0.55 * sc + 10, sy - 8), (Ax + 0.55 * sc + 14, sy)], 'dg-line-2')
    s.text(Ax + 0.55 * sc, sy + 0.25 * sc + 54, 'stage 1b: 3-point cradle', 'dg-muted', 'middle', 10)
    s.text(Ax, sy + 0.25 * sc + 54, 'stage 1a / 2: bare plate', 'dg-muted', 'middle', 10)
    # bell jar option over A
    s.path(f'M{Ax - 0.12 * sc:.1f},{sy:.1f} L{Ax - 0.12 * sc:.1f},{sy - 0.26 * sc:.1f} Q{Ax - 0.12 * sc:.1f},{sy - 0.36 * sc:.1f} {Ax - 0.02 * sc:.1f},{sy - 0.36 * sc:.1f} L{Ax + 0.02 * sc:.1f},{sy - 0.36 * sc:.1f} Q{Ax + 0.12 * sc:.1f},{sy - 0.36 * sc:.1f} {Ax + 0.12 * sc:.1f},{sy - 0.26 * sc:.1f} L{Ax + 0.12 * sc:.1f},{sy:.1f}', 'dg-line-2')
    s.text(Ax + 0.15 * sc, sy - 0.33 * sc, 'optional bell jar (vacuum), LDV through the glass', 'dg-muted', 'start', 10)
    s.text(Bx + 0.17 * sc, sy - 0.0445 * sc - 16, 'LDV beam', 'dg-muted', 'middle', 10)
    s.line(Bx + 0.3 * sc, sy - 0.0445 * sc, Bx + 0.0445 * sc, sy - 0.0445 * sc, 'dg-accent', 'stroke-dasharray="2 3"')
    s.rect(Bx + 0.3 * sc, sy - 0.0445 * sc - 10, 40, 20, 'dg-line dg-fill', rx=3); s.text(Bx + 0.3 * sc + 20, sy - 0.0445 * sc + 4, 'LDV', 'dg-text', 'middle', 10, 650)
    return str(s)

# ------------------------------------------------------------------------------------------ D2: sphere spectrum (stick chart)
def spectrum_chart(R):
    modes = [d for d in R['modes'] if d['f'] <= 60e3]
    W, H = 760, 360; s = S(W, H, 'Predicted resonances of the hollow copper sphere below 60 kHz', cls='dg viz')
    x0, x1, y0, y1 = 56, 740, 30, 290
    X = lambda f: x0 + (x1 - x0) * f / 60e3
    for k in range(0, 61, 10):
        s.line(X(k * 1e3), y0, X(k * 1e3), y1, 'viz-grid'); s.text(X(k * 1e3), y1 + 20, f'{k}', 'dg-muted', 'middle', 12)
    s.text((x0 + x1) / 2, y1 + 40, 'frequency (kHz)', 'dg-muted', 'middle', 12)
    # y: degeneracy 1..47 -> bar height (number of lines in the multiplet)
    ymax = 48
    Y = lambda n: y1 - (y1 - y0) * n / ymax
    for k in (1, 10, 20, 30, 40):
        s.line(x0 - 4, Y(k), x0, Y(k), 'viz-axis'); s.text(x0 - 8, Y(k) + 4, f'{k}', 'dg-muted', 'end', 11)
    s.text(14, (y0 + y1) / 2, 'lines in multiplet', 'dg-muted', 'middle', 11, extra=f'transform="rotate(-90 14 {(y0 + y1) / 2:.0f})"')
    s.line(x0, y1, x1, y1, 'viz-axis')
    cls = {('S', 'lower'): 'viz-s1', ('S', 'upper'): 'viz-s3', ('T', None): 'viz-s2'}
    for d in modes:
        c = cls[('T', None)] if d['family'] == 'T' else cls[('S', d['branch'])]
        x = X(d['f']); top = Y(d['deg'])
        tip = f"{d['label']} · {fmt_hz(d['f'])} · {d['deg']} degenerate lines · {'torsional' if d['family'] == 'T' else d['branch'] + '-branch spheroidal'}"
        s.add(f'<g class="viz-mark" data-tip="{esc(tip)}"><rect x="{x - 6:.1f}" y="{top - 6:.1f}" width="12" height="{y1 - top + 6:.1f}" class="viz-hit"/>'
              f'<line x1="{x:.1f}" y1="{y1:.1f}" x2="{x:.1f}" y2="{top:.1f}" class="{c} viz-stick"/><circle cx="{x:.1f}" cy="{top:.1f}" r="4" class="{c} viz-dot"/></g>')
    # selective direct labels
    for lab, dx, dy in (('S2', -10, -10), ('T2', 10, -10), ('S0', 14, -10), ('T3', 14, -10), ('S1', 0, -10), ('S2(2)', -16, -10), ('T4', 0, -10), ('T5', -14, -10), ('S14', -12, -10), ('S20', 14, -10)):
        d = next((m for m in modes if m['label'] == lab), None)
        if not d: continue
        s.text(X(d['f']) + dx, Y(d['deg']) + dy, lab, 'dg-text', 'middle', 11, 600)
    # legend (3 series)
    lx = x0 + 10; ly = y0 + 8
    for i, (c, name) in enumerate((('viz-s1', 'spheroidal, lower branch (bending/membrane)'), ('viz-s3', 'spheroidal, upper branch (breathing-like)'), ('viz-s2', 'torsional'))):
        s.add(f'<line x1="{lx:.0f}" y1="{ly + i * 18:.0f}" x2="{lx + 18:.0f}" y2="{ly + i * 18:.0f}" class="{c} viz-stick"/>')
        s.text(lx + 26, ly + i * 18 + 4, name, 'dg-text', 'start', 11)
    s.text(lx + 26, ly + 3 * 18 + 4, f"{len(modes)} modes · {sum(d['deg'] for d in modes)} lines below 60 kHz (in vacuum)", 'dg-muted', 'start', 11)
    return str(s)

# ------------------------------------------------------------------------------------------ D3: mode shapes
def mode_shapes(R):
    ms = R['mode_shapes_surface']
    W, H = 760, 250; s = S(W, H, 'Shapes of the lowest modes of the hollow sphere (cross-sections, exaggerated)')
    items = [('S2', 'l = 2  "football"', 2), ('S3', 'l = 3', 3), ('S4', 'l = 4', 4), ('S5', 'l = 5', 5), ('S0', 'l = 0  breathing', 0), ('T2', 'l = 2 torsional', 2)]
    r0 = 46
    for i, (lab, name, l) in enumerate(items):
        cx, cy = 70 + i * 124, 110
        s.circle(cx, cy, r0, 'dg-line-2')
        if lab.startswith('S'):
            amp = 0.16 if l else 0.10
            pts = []
            for k in range(181):
                th = math.pi * k / 90
                # radial pattern P_l(cos theta) ; the deformed outline
                from numpy.polynomial import legendre as LG
                P = LG.legval(math.cos(th), [0] * l + [1])
                r = r0 * (1 + amp * P)
                pts.append((cx + r * math.sin(th), cy - r * math.cos(th)))
            s.poly(pts, 'dg-accent')
        else:
            # torsional: arrows of opposite sense on the two hemispheres
            for (ang, dirn) in ((-50, 1), (50, -1), (130, 1), (230, -1)):
                a = math.radians(ang); x, y = cx + (r0 - 10) * math.sin(a), cy - (r0 - 10) * math.cos(a)
                dx, dy = dirn * 12 * math.cos(a), dirn * 12 * math.sin(a)
                s.arrow(x - dx, y - dy, x + dx, y + dy, 'dg-accent', 'dg-arrow')
        s.text(cx, cy + r0 + 26, lab, 'dg-text', 'middle', 14, 700)
        s.text(cx, cy + r0 + 44, name, 'dg-muted', 'middle', 11)
        f = ms[lab]['f'] if lab in ms else next(d['f'] for d in R['modes'] if d['label'] == lab)
        s.text(cx, cy + r0 + 60, fmt_hz(f), 'dg-text', 'middle', 12)
        deg = 2 * l + 1
        s.text(cx, cy + r0 + 76, f'{deg} lines' if deg > 1 else '1 line', 'dg-muted', 'middle', 11)
    return str(s)

# ------------------------------------------------------------------------------------------ D4: complete spectrum map
def spectrum_map(R):
    W, H = 760, 350; s = S(W, H, 'Every frequency the sphere has, from hertz to terahertz, and what each depends on', cls='dg viz')
    x0, x1 = 50, 730; lo, hi = 2, 14            # log10 Hz
    X = lambda f: x0 + (x1 - x0) * (math.log10(f) - lo) / (hi - lo)
    yax = 290
    s.line(x0, yax, x1, yax, 'viz-axis')
    for e in range(lo, hi + 1):
        s.line(X(10 ** e), yax, X(10 ** e), yax + 6, 'viz-axis')
        lab = {2: '100 Hz', 3: '1 kHz', 4: '10 kHz', 5: '100 kHz', 6: '1 MHz', 7: '10 MHz', 8: '100 MHz', 9: '1 GHz', 10: '10 GHz', 11: '100 GHz', 12: '1 THz', 13: '10 THz', 14: '100 THz'}[e]
        if e % 2 == 0: s.text(X(10 ** e), yax + 22, lab, 'dg-muted', 'middle', 11)
    le = R['location_effects']; em = R['em_cavity']; th = R['thermal']
    f_lo = R['modes'][0]['f']; f_hi = max(d['f'] for d in R['modes'])
    bands = [
        (le['nmr_63Cu_Hz_in_50uT'], le['nmr_65Cu_Hz_in_50uT'], 'viz-s4', '⁶³Cu / ⁶⁵Cu nuclear spins', f"{le['nmr_63Cu_Hz_in_50uT']:.0f} and {le['nmr_65Cu_Hz_in_50uT']:.0f} Hz in Earth's 50 µT field", 'set by the field at the place (±11 Hz per µT)', 216, 'start'),
        (R['interior_air']['cavity_modes'][0]['f'], 60e3, 'viz-s4', 'air resonances inside the shell', f"{R['interior_air']['cavity_modes'][0]['f'] / 1e3:.1f} kHz upward, dense", 'air temperature and pressure; removed by the vent hole + bell jar', 156, 'start'),
        (R['contact']['bounce_mode_coupled_Hz'] * 0.9, R['contact']['bounce_mode_coupled_Hz'] * 1.1, 'viz-s2', 'bounce on the contact', f"≈ {R['contact']['bounce_mode_coupled_Hz']:.0f} Hz (model)", 'set by the surface under the ball', 96, 'start'),
        (f_lo, 60e3, 'viz-s1', 'elastic ring modes (the tone)', f"{fmt_hz(f_lo)} to 60 kHz: {R['n_modes_below_60k']} modes, {R['n_lines_below_60k']} lines", 'geometry, copper, temperature; shifted by the contact', 36, 'middle'),
        (em['TM101_GHz'] * 1e9, em['TE101_GHz'] * 1e9, 'viz-s3', 'microwave cavity modes inside', f"TM₁₀₁ {em['TM101_GHz']:.2f} GHz · TE₁₀₁ {em['TE101_GHz']:.2f} GHz", 'inner radius only (closed shell)', 96, 'middle'),
        (th['peak_THz'] * 1e12 / 3, th['peak_THz'] * 1e12 * 3, 'viz-s2', 'thermal radiation peak', f"{th['peak_THz']:.0f} THz (λ ≈ {th['wien_peak_um']:.1f} µm) at 295 K", "the ball's temperature", 36, 'end'),
    ]
    for (fa, fb, c, name, val, dep, yoff, anc) in bands:
        xa, xb = X(fa), X(fb); y = yax - yoff
        s.add(f'<g class="viz-mark" data-tip="{esc(name + ": " + val + ". " + dep)}"><rect x="{xa - 4:.1f}" y="{y - 9:.1f}" width="{max(xb - xa, 2) + 8:.1f}" height="18" class="{c} viz-band"/></g>')
        tx = xa - 4 if anc == 'start' else (xb + 4 if anc == 'end' else (xa + xb) / 2)
        s.text(tx, y - 16, name, 'dg-text', anc, 11, 600)
        s.text(tx, y + 24, dep, 'dg-muted', anc, 10)
    s.text(x0, 24, 'The complete spectrum of one copper sphere', 'dg-text', 'start', 15, 650)
    s.text(x0, 42, 'bands to scale on a log axis; hover or tap for the numbers', 'dg-muted', 'start', 11)
    return str(s)

# ------------------------------------------------------------------------------------------ D5: table modes + FRF
def table_modes(R, series):
    import numpy as np
    xs, ys, shapes = series['xs'], series['ys'], series['shapes']
    tm = R['table']['modes']
    W, H = 760, 330; s = S(W, H, 'The first six free modes of the granite plate, with points A, B and C', cls='dg viz')
    s.text(20, 24, 'Mode shapes of the plate (Kirchhoff, free edges) · colour = |displacement|', 'dg-text', 'start', 14, 650)
    cw, ch = 220, 110; sc = cw / 2.4
    for k in range(6):
        ox, oy = 20 + (k % 3) * 246, 44 + (k // 3) * 140
        Z = np.abs(shapes[k]); Z = Z / Z.max()
        # coarse raster cells (sequential single hue via opacity)
        step = 4
        for j in range(0, len(ys) - 1, step):
            for i in range(0, len(xs) - 1, step):
                v = float(Z[j:j + step, i:i + step].mean())
                x = ox + (xs[i] + 1.2) * sc; y = oy + (0.6 - ys[j]) * sc
                s.add(f'<rect x="{x:.1f}" y="{y - (ys[min(j + step, len(ys) - 1)] - ys[j]) * sc:.1f}" width="{(xs[min(i + step, len(xs) - 1)] - xs[i]) * sc:.1f}" height="{(ys[min(j + step, len(ys) - 1)] - ys[j]) * sc:.1f}" class="viz-seq" style="opacity:{0.08 + 0.92 * v:.2f}"/>')
        s.rect(ox, oy, cw, ch, 'dg-line', rx=2)
        for (px, py, lab) in ((-1.0, 0.0, 'A'), (1.0, 0.0, 'B'), (0.9, 0.45, 'C')):
            x = ox + (px + 1.2) * sc; y = oy + (0.6 - py) * sc
            s.circle(x, y, 4, 'dg-ink-fill'); s.text(x + 7, y + 4, lab, 'dg-text', 'start', 11, 700)
        fa, fc = abs(tm[k]['shift_ppm_A']), abs(tm[k]['shift_ppm_C'])
        s.text(ox, oy + ch + 16, f"mode {k + 1} · {tm[k]['f']:.0f} Hz · ball at A: −{fa:.0f} ppm · at C: −{fc:.0f} ppm", 'dg-muted', 'start', 10)
    return str(s)

def frf_chart(series):
    fr, HA, HB, HC = series['fr'], series['HA'], series['HB'], series['HC']
    W, H = 760, 300; s = S(W, H, 'Driving-point response of the plate at A, B and C', cls='dg viz')
    x0, x1, y0, y1 = 60, 730, 30, 250
    X = lambda f: x0 + (x1 - x0) * (f - 20) / 580
    lo, hi = -3, 2
    Y = lambda v: y1 - (y1 - y0) * (math.log10(max(v, 1e-9)) - lo) / (hi - lo)
    for e in range(lo, hi + 1):
        s.line(x0, Y(10 ** e), x1, Y(10 ** e), 'viz-grid'); s.text(x0 - 8, Y(10 ** e) + 4, f'10{"⁻" if e < 0 else ""}{str(abs(e)).translate(str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹"))}', 'dg-muted', 'end', 11)
    for f in range(100, 601, 100):
        s.line(X(f), y1, X(f), y1 + 5, 'viz-axis'); s.text(X(f), y1 + 20, f'{f}', 'dg-muted', 'middle', 11)
    s.line(x0, y1, x1, y1, 'viz-axis')
    s.text((x0 + x1) / 2, y1 + 40, 'frequency (Hz)', 'dg-muted', 'middle', 12)
    s.text(16, (y0 + y1) / 2, 'accelerance, relative', 'dg-muted', 'middle', 11, extra=f'transform="rotate(-90 16 {(y0 + y1) / 2:.0f})"')
    import numpy as np
    norm = max(HA.max(), HB.max(), HC.max())
    for arr, c, name in ((HA / norm, 'viz-s1', 'A'), (HB / norm, 'viz-s2', 'B (mirror of A)'), (HC / norm, 'viz-s3', 'C')):
        d = 'M' + ' L'.join(f'{X(f):.1f},{min(Y(v), y1):.1f}' for f, v in zip(fr[::2], arr[::2]))
        s.path(d, f'{c} viz-line' + (' viz-dashed' if name.startswith('B') else ''))
    # legend
    for i, (c, name) in enumerate((('viz-s1', 'point A'), ('viz-s2', 'point B (identical by symmetry)'), ('viz-s3', 'point C, off-axis'))):
        s.add(f'<line x1="{x0 + 10}" y1="{y0 + 8 + i * 18}" x2="{x0 + 30}" y2="{y0 + 8 + i * 18}" class="{c} viz-line{" viz-dashed" if i == 1 else ""}"/>')
        s.text(x0 + 38, y0 + 12 + i * 18, name, 'dg-text', 'start', 11)
    s.add(f'<rect x="{x0}" y="{y0}" width="{x1 - x0}" height="{y1 - y0}" class="viz-hover" data-frf="1"/>')
    return str(s)

# ------------------------------------------------------------------------------------------ D6: location-effect budget
def budget_chart(R):
    le = R['location_effects']; ct = R['contact']; air = R['air']; sens = R['sensitivity']
    rows = [
        ('Contact with the table (m = 0 line of each multiplet, bare plate)', abs(ct['shift_hertz'][0]['rel']) * 1e6, f"shift vs free: +{100 * ct['shift_hertz'][0]['rel']:.2f} % at S2; a ±20 % change in contact stiffness between two spots moves it by {le['contact_variation_ppm']:.0f} ppm", 'support'),
        ('Air inside the shell, line near a resonance (S4, no vent)', abs(R['interior_air']['shifts']['S4']['shift_ppm']), f"first-order added mass; S2 {R['interior_air']['shifts']['S2']['shift_ppm']:+.0f} ppm, S4 {R['interior_air']['shifts']['S4']['shift_ppm']:+.0f} ppm; the vent hole and bell jar remove it", 'air'),
        ('Air inside the shell, 1 K change in air temperature (S4)', abs(R['interior_air']['shifts']['S4']['ppm_per_K']), 'the interior resonances move with the speed of sound in air', 'air'),
        ('Contact stiffness differing between spot A and spot B (±20 %)', le['contact_variation_ppm'], 'same spring model; surface finish, dust and load decide it', 'support'),
        ('Temperature, 0.5 K difference end to end', 100.0, f"{sens['S2']['ppm_per_K']:.0f} ppm/K from the copper moduli (model)".replace('-', '−'), 'temperature'),
        ('Doppler while the ball moves at 5 cm/s (microphone only)', le['doppler_ppm_at_0p05_m_per_s'], 'disappears when it stops; the laser vibrometer does not see it', 'motion'),
        ('Air outside, 1 K or 0.3 kPa change in air density', air['ppm_per_K_bound'] * 1.0, 'upper bound on the exterior reactive loading; vanishes in the bell jar', 'air'),
        ('Measurement floor after temperature correction (≈ 10 mK)', le['measurement_floor_ppm_after_T_correction_10mK'], 'the smallest A–B difference the design can claim', 'floor'),
        ('Frequency estimate alone (ring-down, 40 dB SNR)', R['precision']['ppm_snr40'], 'Cramér–Rao bound; electronics are not the limit', 'floor'),
        ('Gravity differing by a 1 t mass nearby', le['gravity_freq_rel'] * 1e6, 'static prestress of the shell × Δg/g', 'gravity'),
        ('Gravitational redshift, 1 mm height difference', le['redshift_rel_1mm'] * 1e6, 'general relativity; same height ⇒ zero', 'gravity'),
    ]
    W = 760; rh = 30; H = 70 + rh * len(rows) + 40
    s = S(W, H, 'How much each known effect can change a ring frequency between A and B, in parts per million', cls='dg viz')
    x0, x1 = 330, 680; lo, hi = -14, 4
    X = lambda v: x0 + (x1 - x0) * (math.log10(max(v, 10 ** lo)) - lo) / (hi - lo)
    y0 = 60
    for e in range(lo, hi + 1, 2):
        x = X(10 ** e); s.line(x, y0 - 6, x, y0 + rh * len(rows), 'viz-grid')
        lab = f'10{"⁻" if e < 0 else ""}{str(abs(e)).translate(str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹"))}' if e not in (0, 2, 4) else {0: '1', 2: '100', 4: '10⁴'}[e]
        s.text(x, y0 - 12, lab, 'dg-muted', 'middle', 11)
    s.text(x1, y0 - 30, 'parts per million of a mode frequency (log scale)', 'dg-muted', 'end', 11)
    floor = le['measurement_floor_ppm_after_T_correction_10mK']
    s.line(X(floor), y0 - 6, X(floor), y0 + rh * len(rows), 'viz-floor')
    s.text(X(floor) - 6, y0 + rh * len(rows) + 16, f'design floor ≈ {floor:.0f} ppm', 'dg-text', 'end', 11, 600)
    for i, (name, v, tip, kind) in enumerate(rows):
        y = y0 + i * rh + rh / 2
        s.text(x0 - 10, y + 4, name, 'dg-text', 'end', 11)
        xa, xb = X(10 ** lo), X(v)
        c = 'viz-s1' if kind != 'floor' else 'viz-s4'
        s.add(f'<g class="viz-mark" data-tip="{esc(name + ": " + (f"{v:.3g} ppm" if v >= 1e-3 else sci(v, 1) + " ppm") + ". " + tip)}">'
              f'<rect x="{xa:.1f}" y="{y - 7:.1f}" width="{max(xb - xa, 2):.1f}" height="14" rx="3" class="{c} viz-bar"/></g>')
        vs = (f'{v:.0f}' if v >= 10 else f'{v:.2g}') if v >= 1e-3 else sci(v)
        s.text(xb + 6, y + 4, vs, 'dg-muted', 'start', 10.5)
    return str(s)

# ------------------------------------------------------------------------------------------ D7: protocol / measurement chain
def protocol_chain(R):
    W, H = 760, 470; s = S(W, H, 'The measurement chain and the three stages of the protocol')
    def block(x, y, w, h, title, sub=None, cls='dg-line dg-fill'):
        s.rect(x, y, w, h, cls, rx=6); s.text(x + w / 2, y + (h / 2 + 4 if not sub else h / 2 - 3), title, 'dg-text', 'middle', 12, 650)
        if sub: s.text(x + w / 2, y + h / 2 + 13, sub, 'dg-muted', 'middle', 10)
    # stage 0
    s.text(20, 26, 'Stage 0 · characterise the two places', 'dg-text', 'start', 14, 700)
    for i, (t, u) in enumerate((('hammer + accelerometer', 'plate response at A, B, C'), ('seismic accelerometer', 'floor and plate vibration'), ('microphone', 'acoustic background'),
                                ('fluxgate + SDR', 'magnetic field · RF'), ('PT100 · barometer · RH', 'air and surface temperature'), ('electronic level', 'slope ≤ 20 µrad'))):
        block(20 + (i % 3) * 246, 38 + (i // 3) * 46, 230, 38, t, u)
    # stage 1
    s.text(20, 160, 'Stage 1 · the sphere\'s complete spectrum at A, then at B', 'dg-text', 'start', 14, 700)
    y = 172
    block(20, y, 120, 54, 'excite', 'striker · EMAT · chirp')
    block(160, y, 150, 54, 'copper sphere', 'bare plate / cradle / bell jar')
    block(330, y, 130, 54, 'laser vibrometer', 'non-contact, + microphone')
    block(480, y, 120, 54, '24-bit DAQ', '204.8 kS/s, synced')
    block(620, y, 120, 54, 'mode fit', 'f, Q per line (ppm)')
    for xa in (140, 310, 460, 600): s.arrow(xa, y + 27, xa + 20, y + 27)
    s.text(20, y + 74, 'repeat 10×, re-seat the ball each time, log T · P · RH · B at the ball; then move A → B without rotating it and repeat; then back to A', 'dg-muted', 'start', 11)
    # stage 2
    s.text(20, 290, 'Stage 2 · synthesise "the tone of B" and play it at A', 'dg-text', 'start', 14, 700)
    y = 302
    block(20, y, 170, 54, 'B spectrum → drive signal', 'all lines, measured amplitudes')
    block(210, y, 140, 54, 'acoustic driver', 'horn, ≤ 140 dB')
    block(210, y + 62, 140, 54, 'coil driver', '≤ 1 mT at the ball')
    block(370, y, 150, 116, 'sphere at A', 'on the bare plate')
    block(540, y, 200, 54, 'laser displacement + camera', '1 µm; records drift and rolling')
    block(540, y + 62, 200, 54, 'controls', 'A-tone · noise · silence · driver on the far side')
    s.arrow(190, y + 27, 210, y + 27); s.arrow(190, y + 27, 210, y + 89, 'dg-line'); s.arrow(350, y + 27, 370, y + 40); s.arrow(350, y + 89, 370, y + 76)
    s.arrow(520, y + 58, 540, y + 27); s.arrow(520, y + 58, 540, y + 89)
    s.text(20, y + 140, 'Read-out: direction and size of any motion vs the controls, with the radiation-pressure and tilt thresholds known in advance (next section).', 'dg-muted', 'start', 11)
    return str(s)

# ------------------------------------------------------------------------------------------ D8: software stack
def software_stack():
    W, H = 760, 230; s = S(W, H, 'Software stack for the experiment')
    cols = [('Prediction', ['sphere_modes.py', 'fp_model.py', 'NumPy · SciPy']),
            ('Acquisition', ['nidaqmx-python (DAQ)', 'VibSoft (vibrometer)', 'GNU Radio (RF survey)']),
            ('Analysis', ['pyEMA · sdypy (modal fit)', 'matrix pencil (ring-down)', 'RUScal · rus-probe']),
            ('Records', ['pandas · HDF5 logs', 'git-tracked run sheets', 'this page (build script)'])]
    for i, (title, items) in enumerate(cols):
        x = 20 + i * 185
        s.rect(x, 30, 170, 170, 'dg-line dg-fill', rx=8)
        s.text(x + 85, 54, title, 'dg-text', 'middle', 14, 700)
        for j, it in enumerate(items):
            s.text(x + 12, 84 + j * 34, it, 'dg-text', 'start', 11)
    for i in range(3):
        s.arrow(190 + i * 185, 115, 205 + i * 185, 115)
    s.text(20, 220, 'Open source except the vibrometer software; every number on this page comes from the two prediction files.', 'dg-muted', 'start', 11)
    return str(s)
