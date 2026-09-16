"""Tiny SVG helper library for the Bashar diagram redrawings.
All styling goes through CSS classes so the page theme controls colours:
 .dg-line (stroke ink 2px)  .dg-line-2 (thin dashed)  .dg-fill (accent tint)  .dg-fill-2 (accent-2 tint)
 .dg-text (ink)  .dg-muted (muted text)  .dg-accent (accent stroke)  .dg-accent-2  .dg-ink-fill (solid ink)
 .dg-c1..c8 categorical fills
Arrow markers are defined once in the page (#dg-arrow, #dg-arrow-2).
"""
import math, html

def esc(s):
    return html.escape(str(s), quote=True)

def wrap(s, maxchars):
    words = str(s).split()
    lines, cur = [], ''
    for w in words:
        if len(cur) + len(w) + (1 if cur else 0) <= maxchars:
            cur = (cur + ' ' + w).strip()
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines or ['']

def text(x, y, s, cls='dg-text', anchor='middle', size=12, maxchars=None, lh=None, weight=None, italic=False, extra=''):
    lines = wrap(s, maxchars) if maxchars else [str(s)]
    lh = lh or size * 1.2
    style = f"font-size:{size}px" + (f";font-weight:{weight}" if weight else '') + (";font-style:italic" if italic else '')
    out = [f'<text x="{x:.1f}" y="{y:.1f}" class="{cls}" text-anchor="{anchor}" style="{style}" {extra}>']
    # vertically centre multi-line blocks around y
    off = -(len(lines) - 1) * lh / 2
    for i, ln in enumerate(lines):
        out.append(f'<tspan x="{x:.1f}" dy="{(off if i == 0 else lh):.1f}">{esc(ln)}</tspan>')
    out.append('</text>')
    return ''.join(out)

def rect(x, y, w, h, cls='dg-line', rx=6, extra=''):
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" class="{cls}" {extra}/>'

def box(x, y, w, h, label, cls='dg-line dg-fill', tcls='dg-text', size=11, rx=6, maxchars=None, weight=None):
    mc = maxchars or max(6, int(w / (size * 0.56)))
    return rect(x, y, w, h, cls, rx) + text(x + w / 2, y + h / 2 + size * 0.35, label, tcls, 'middle', size, mc, weight=weight)

def line(x1, y1, x2, y2, cls='dg-line', extra=''):
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" class="{cls}" {extra}/>'

def arrow(x1, y1, x2, y2, cls='dg-line', marker='dg-arrow'):
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" class="{cls}" marker-end="url(#{marker})"/>'

def path(d, cls='dg-line', extra=''):
    return f'<path d="{d}" class="{cls}" {extra}/>'

def circle(cx, cy, r, cls='dg-line', extra=''):
    return f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" class="{cls}" {extra}/>'

def polygon(points, cls='dg-line', extra=''):
    pts = ' '.join(f'{x:.1f},{y:.1f}' for x, y in points)
    return f'<polygon points="{pts}" class="{cls}" {extra}/>'

def regular_polygon(cx, cy, r, n, rot=-90):
    return [(cx + r * math.cos(math.radians(rot + 360 * i / n)), cy + r * math.sin(math.radians(rot + 360 * i / n))) for i in range(n)]

def arc_path(cx, cy, r, a0, a1):
    """arc from angle a0 to a1 (degrees, clockwise from 12 o'clock)"""
    def pt(a):
        return cx + r * math.sin(math.radians(a)), cy - r * math.cos(math.radians(a))
    x0, y0 = pt(a0); x1, y1 = pt(a1)
    large = 1 if (a1 - a0) % 360 > 180 else 0
    return f'M{x0:.1f},{y0:.1f} A{r:.1f},{r:.1f} 0 {large} 1 {x1:.1f},{y1:.1f}'

def wedge_path(cx, cy, r0, r1, a0, a1):
    def pt(a, r):
        return cx + r * math.sin(math.radians(a)), cy - r * math.cos(math.radians(a))
    xa, ya = pt(a0, r1); xb, yb = pt(a1, r1); xc, yc = pt(a1, r0); xd, yd = pt(a0, r0)
    large = 1 if (a1 - a0) % 360 > 180 else 0
    return (f'M{xa:.1f},{ya:.1f} A{r1:.1f},{r1:.1f} 0 {large} 1 {xb:.1f},{yb:.1f} '
            f'L{xc:.1f},{yc:.1f} A{r0:.1f},{r0:.1f} 0 {large} 0 {xd:.1f},{yd:.1f} Z')

def svg(body, w=400, h=280, title=''):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img" aria-label="{esc(title)}" class="dg">'
            f'{"".join(body)}</svg>')

def note(w, h, s, size=9.5):
    """small italic caption at bottom"""
    return text(w / 2, h - 8, s, 'dg-muted', 'middle', size, maxchars=int(w / (size * 0.52)), italic=True)
