"""Original SVG redrawings — part A (handouts whose content is known + core models)."""
import math
from svglib import *

D = {}   # slug -> (svg, kind)
K_HANDOUT = 'Official handout — redrawn from its text'
K_SESSION = 'Reconstructed from the session description'
K_MODEL = 'Model synthesized from Bashar\'s teaching'
K_CONCEPT = 'Concept illustration — handout layout unverified'

def reg(slug, kind, w, h, body, title):
    D[slug] = {'svg': svg(body, w, h, title), 'kind': kind, 'w': w, 'h': h}

# 1. 7-Part Master Permission Slip -------------------------------------------------
rows = [('Mon','Air','one deep breath','I am a child of creation · unique · worthy'),
        ('Tue','Water','one sip of water','I am happy · grateful · refreshed'),
        ('Wed','Food','one small bite','I am abundant · nurtured · fulfilled'),
        ('Thu','Love','a hug (mirror)','I am supported · guided · loved'),
        ('Fri','Freedom','a spin, arms out','I am awake · powerful · free'),
        ('Sat','Passion','favourite word ×3, sound, image','(your favourite word, sound, image)'),
        ('Sun','Dream','eyes closed, ×3','I am rested · connected · my life is a dream come true')]
b = [text(200, 18, 'THE 7-PART MASTER PERMISSION SLIP', 'dg-text', size=12, weight=700)]
y0 = 34; rh = 34
b.append(text(38, y0 - 6, 'Day · element', 'dg-muted', size=9)); b.append(text(128, y0 - 6, 'action before each line', 'dg-muted', size=9)); b.append(text(285, y0 - 6, 'three statements', 'dg-muted', size=9))
for i, (d, e, a, s) in enumerate(rows):
    y = y0 + i * rh
    b.append(rect(8, y, 384, rh - 4, 'dg-line-2 ' + ('dg-fill' if i % 2 == 0 else ''), 4))
    b.append(text(38, y + 20, f'{d} · {e}', 'dg-text', size=11, weight=600))
    b.append(text(128, y + 20, a, 'dg-text', size=9.5, maxchars=22))
    b.append(text(285, y + 20, s, 'dg-text', size=9.5, maxchars=42))
b.append(note(400, 300, '7 weeks (49 days), morning and evening. Table order from the session transcript; the handout\'s own layout is not visible.'))
reg('near-life-experience-master-permission-slip', K_SESSION, 400, 300, b, '7-Part Master Permission Slip table')

# 2. Nine Levels of Consciousness -------------------------------------------------
levels = [('1 Oversoul','np'),('2 Individual soul / spirit','np'),('3 Higher mind','np'),('4 Template-level reality','tp'),
          ('5 Collective unconscious — collective automatic mind','ph'),('6 Individual unconscious — individual automatic mind','ph'),
          ('7 Unconscious — beliefs / definitions','ph'),('8 Subconscious — emotions','ph'),('9 Conscious — thoughts (ego / personality)','ph')]
b = [text(210, 16, 'THE 9 LEVELS OF CONSCIOUSNESS', 'dg-text', size=12, weight=700)]
y0 = 26; rh = 23
for i, (lab, grp) in enumerate(levels):
    y = y0 + i * rh
    cls = 'dg-line ' + {'np':'dg-fill-2','tp':'dg-fill','ph':''}[grp]
    b.append(rect(70, y, 300, rh - 3, cls, 4))
    b.append(text(220, y + 14, lab, 'dg-text', size=9.5, maxchars=60))
# brackets
def bracket(y1, y2, label):
    return (path(f'M62,{y1} L56,{y1} L56,{y2} L62,{y2}', 'dg-line-2') + text(28, (y1 + y2) / 2 + 4, label, 'dg-muted', size=9, maxchars=11))
b.append(bracket(y0, y0 + 3 * rh - 3, 'non-physical'))
b.append(bracket(y0 + 3 * rh, y0 + 4 * rh - 3, 'quasi-physical'))
b.append(bracket(y0 + 4 * rh, y0 + 9 * rh - 3, 'physical'))
# shadow reflection (faded)
ys = y0 + 9 * rh + 4
b.append(rect(70, ys, 300, 14, 'dg-line-2', 4, 'opacity="0.45"')); b.append(rect(70, ys + 17, 300, 14, 'dg-line-2', 4, 'opacity="0.3"'))
b.append(text(220, ys + 10, '"shadow reflection" projected downward — described as an illusion', 'dg-muted', size=8.5))
b.append(arrow(385, y0 + 9 * rh - 6, 385, y0 + 4, 'dg-line-2', 'dg-arrow-2')); b.append(text(391, y0 + 100, 'higher frequency ↑', 'dg-muted', size=8, extra='transform="rotate(-90 391 %d)"' % (y0 + 100)))
b.append(note(400, 306, 'Order per the 2011 session walkthrough; graphic style of the original unverified.'))
reg('nine-levels-of-consciousness', K_SESSION, 400, 306, b, 'Nine levels of consciousness stack')

# 3. The Black Box ------------------------------------------------------------------
b = [text(200, 18, 'THE BLACK BOX', 'dg-text', size=12, weight=700)]
b.append(rect(150, 40, 100, 70, 'dg-ink-fill', 8)); b.append(text(200, 70, 'negative belief', 'dg-inv', size=10)); b.append(text(200, 84, '(a "black box")', 'dg-inv', size=9))
b.append(text(200, 128, 'suspension of disbelief: treat the belief as a quasi-intelligent structure with defences', 'dg-muted', size=9, maxchars=60))
b.append(rect(8, 150, 186, 128, 'dg-line dg-fill', 6)); b.append(text(101, 166, '27 tools & tricks it uses', 'dg-text', size=10.5, weight=600))
for i, s in enumerate(['claims to be the only view', 'threatens pain if released', 'poses as your protector', 'denies it even exists', '… (23 more)']):
    b.append(text(101, 184 + i * 19, s, 'dg-text', size=9.5))
b.append(rect(206, 150, 186, 128, 'dg-line dg-fill-2', 6)); b.append(text(299, 166, '24 negativity neutralizers', 'dg-text', size=10.5, weight=600))
for i, s in enumerate(['negative emotion ⇒ a belief', 'beliefs are assumptions', 'circumstances carry no meaning', 'fear peaking = belief dissolving', '… (20 more)']):
    b.append(text(299, 184 + i * 19, s, 'dg-text', size=9.5))
b.append(arrow(150, 75, 101, 148, 'dg-line-2', 'dg-arrow-2')); b.append(arrow(250, 75, 299, 148, 'dg-line-2', 'dg-arrow-2'))
reg('black-box', K_HANDOUT, 400, 290, b, 'The Black Box: two lists')

# 4. The Formula ---------------------------------------------------------------------
steps = ['Act on your highest excitement, in the moment, every moment you can',
         'To the best of your ability — take it as far as you can',
         'With zero insistence, assumption or expectation of the outcome',
         'Stay in a positive state regardless of what happens',
         'Constantly investigate your beliefs; release and replace the fear-based ones']
b = [text(200, 18, 'THE FORMULA  ·  follow your highest excitement', 'dg-text', size=12, weight=700)]
for i, s in enumerate(steps):
    y = 32 + i * 48
    b.append(circle(28, y + 20, 13, 'dg-ink-fill')); b.append(text(28, y + 24.5, str(i + 1), 'dg-inv', size=12, weight=700))
    b.append(rect(50, y, 342, 40, 'dg-line ' + ('dg-fill' if i < 3 else 'dg-fill-2'), 6)); b.append(text(221, y + 24, s, 'dg-text', size=10.5, maxchars=58))
    if i < 4: b.append(arrow(28, y + 34, 28, y + 46, 'dg-line-2', 'dg-arrow-2'))
b.append(note(400, 290, 'Five steps verbatim in spirit from bashar.org/formula (steps 1–3 are "the formula", 4–5 the supporting practice).'))
reg('the-formula', K_HANDOUT, 400, 290, b, 'The Formula five steps')

# 5. Hour of Power -------------------------------------------------------------------
aff = ['I am who I am for a reason','No insistence, no resistance','I am indestructible at my core','Past & future are illusions — now is all',
       'Perfect timing; I miss nothing','My life is my own','Unconditionally supported by creation','I am an expression of nature',
       'I always have what I need','I give & receive joy, love, compassion','My life is a synchronous orchestration','I am free to choose']
b = [text(200, 16, 'THE HOUR OF POWER — 12 affirmations × ~5 minutes', 'dg-text', size=11.5, weight=700)]
cx, cy, r0, r1 = 200, 165, 52, 100
for i in range(12):
    a0, a1 = i * 30, (i + 1) * 30
    b.append(path(wedge_path(cx, cy, r0, r1, a0 + 1, a1 - 1), 'dg-line-2 ' + ('dg-fill' if i % 2 == 0 else 'dg-fill-2')))
    am = math.radians(a0 + 15); tx, ty = cx + (r1 + 22) * math.sin(am), cy - (r1 + 22) * math.cos(am)
    b.append(text(cx + (r0 + r1) / 2 * math.sin(am), cy - (r0 + r1) / 2 * math.cos(am) + 4, str(i + 1), 'dg-text', size=10, weight=700))
    anchor = 'start' if 15 < a0 + 15 < 165 else ('end' if 195 < a0 + 15 < 345 else 'middle')
    b.append(text(tx, ty + 3, aff[i], 'dg-text', anchor, 8, maxchars=18, lh=9))
b.append(text(cx, cy - 4, '60', 'dg-text', size=16, weight=700)); b.append(text(cx, cy + 10, 'minutes', 'dg-muted', size=8))
reg('hour-of-power', K_SESSION, 400, 300, b, 'Hour of Power clock of 12 affirmations')

# 6. Interstellar Enneagram ---------------------------------------------------------
b = [text(200, 16, 'THE INTERSTELLAR ENNEAGRAM', 'dg-text', size=12, weight=700)]
gx, gy, cell, gap = 118, 62, 50, 18
names = [['Sirius','Arcturus','Pleiades'],['Essassani','Earth','Yahyel'],['Orion','Anunnaki','Grey Federation']]
rowlab = ['future','present','past']
def tile_symbol(r, c, x, y, s):
    o = []
    if (r, c) == (2, 0):   # Orion three-bar banner: black bottom, red middle, white top
        o += [rect(x + 12, y + 10, s - 24, 10, 'dg-white', 1), rect(x + 12, y + 21, s - 24, 10, 'dg-red', 1), rect(x + 12, y + 32, s - 24, 10, 'dg-black', 1)]
    elif (r, c) == (2, 1):  # Anunnaki winged disc (simplified)
        o += [rect(x + 4, y + 4, s - 8, s - 8, 'dg-black', 3), circle(x + s / 2, y + s / 2, 8, 'dg-gold'), circle(x + s / 2, y + s / 2, 2.5, 'dg-red'),
              path(f'M{x+s/2-9},{y+s/2-3} L{x+7},{y+s/2-10} M{x+s/2-9},{y+s/2} L{x+7},{y+s/2-3} M{x+s/2-9},{y+s/2+3} L{x+7},{y+s/2+4}', 'dg-blue-stroke'), path(f'M{x+s/2+9},{y+s/2-3} L{x+s-7},{y+s/2-10} M{x+s/2+9},{y+s/2} L{x+s-7},{y+s/2-3} M{x+s/2+9},{y+s/2+3} L{x+s-7},{y+s/2+4}', 'dg-blue-stroke')]
    elif (r, c) == (2, 2):  # Grey Federation stripes
        o += [rect(x + 8, y + 10, s - 16, 10, 'dg-black', 1), rect(x + 8, y + 21, s - 16, 10, 'dg-grey', 1), rect(x + 8, y + 32, s - 16, 10, 'dg-white', 1)]
    elif (r, c) == (1, 1):  # Earth nested squares
        o += [rect(x + 5, y + 5, s - 10, s - 10, 'dg-black', 2), polygon(regular_polygon(x + s / 2, y + s / 2, 18, 4, -90), 'dg-blue'),
              rect(x + s / 2 - 11, y + s / 2 - 11, 22, 22, 'dg-green', 1), polygon(regular_polygon(x + s / 2, y + s / 2, 9, 4, -90), 'dg-white')]
    elif (r, c) == (1, 2):  # Yahyel pentagon
        o += [rect(x + 5, y + 5, s - 10, s - 10, 'dg-black', 2), polygon(regular_polygon(x + s / 2, y + s / 2, 17, 5, -90), 'dg-white'), circle(x + s / 2, y + s / 2 + 2, 4, 'dg-green')]
    elif (r, c) == (1, 0):  # Essassani — triangle (unverified)
        o += [polygon(regular_polygon(x + s / 2, y + s / 2 + 3, 18, 3, -90), 'dg-line dg-fill-2'), text(x + s - 8, y + 12, '?', 'dg-muted', size=9)]
    else:
        o += [text(x + s / 2, y + s / 2 + 6, '?', 'dg-muted', size=18)]
    return ''.join(o)
for r in range(3):
    for c in range(3):
        x = gx + c * (cell + gap); y = gy + r * (cell + gap)
        b.append(rect(x, y, cell, cell, 'dg-line', 4)); b.append(tile_symbol(r, c, x, y, cell))
        b.append(text(x + cell / 2, y + cell + 10, names[r][c], 'dg-text', size=8))
    b.append(text(gx - 12, gy + r * (cell + gap) + cell / 2 + 3, rowlab[r], 'dg-muted', 'end', 9))
# outer boxes
b.append(box(gx, 34, 3 * cell + 2 * gap, 20, 'Hypersapien', 'dg-line-2', size=9.5))
b.append(box(gx, gy + 3 * (cell + gap) - 2, 3 * cell + 2 * gap, 20, 'Protosapien', 'dg-line-2', size=9.5))
b.append(rect(52, gy, 22, 3 * cell + 2 * gap, 'dg-line-2', 4)); b.append(text(63, gy + 93, 'Reptilian', 'dg-text', size=9, extra=f'transform="rotate(-90 63 {gy+93})"'))
b.append(rect(gx + 3 * cell + 2 * gap + 8, gy, 22, 3 * cell + 2 * gap, 'dg-line-2', 4)); xx = gx + 3 * cell + 2 * gap + 19; b.append(text(xx, gy + 93, 'New hybrids', 'dg-text', size=9, extra=f'transform="rotate(90 {xx} {gy+93})"'))
b.append(note(400, 312, 'Grid, row order and the past/present-row symbols follow Bashar\'s spoken walkthrough (2014). "?" = symbol not described in any text source.'))
reg('interstellar-enneagram', K_SESSION, 400, 312, b, 'Interstellar Enneagram 3×3 matrix')

# 7. Keys of Ascension ---------------------------------------------------------------
lev = [('9  All-That-Is','sphere','silvery, clear light'),('8  Galactic','disc / torus / halo','white light'),('7  Crown','(shape unknown)','violet, white-hot centre'),
       ('6  Third eye','tesseract','indigo'),('5  Throat','octahedron','blue'),('4  Heart','two tetrahedra base-to-base','emerald green'),
       ('3  Solar plexus','tetrahedron','golden yellow'),('2  Stomach','four-sided pyramid','golden orange'),('1  Root','cube','deep red')]
def solid(kind, x, y, s=16):
    h = s / 2
    if kind == 'sphere': return circle(x, y, h, 'dg-line') + path(f'M{x-h},{y} A{h},{h/3} 0 0 0 {x+h},{y}', 'dg-line-2')
    if kind.startswith('disc'): return f'<ellipse cx="{x}" cy="{y}" rx="{h}" ry="{h/3}" class="dg-line"/>' + f'<ellipse cx="{x}" cy="{y}" rx="{h/3}" ry="{h/9}" class="dg-line-2"/>'
    if kind == 'tesseract': return rect(x - h, y - h, s, s, 'dg-line', 0) + rect(x - h / 2, y - h / 2, s / 2, s / 2, 'dg-line', 0) + ''.join(line(x + dx * h, y + dy * h, x + dx * h / 2, y + dy * h / 2, 'dg-line-2') for dx in (-1, 1) for dy in (-1, 1))
    if kind == 'octahedron': return polygon([(x, y - h), (x + h, y), (x, y + h), (x - h, y)], 'dg-line') + line(x - h, y, x + h, y, 'dg-line-2')
    if kind.startswith('two tetra'): return polygon([(x, y - h), (x + h, y + 1), (x - h, y + 1)], 'dg-line') + polygon([(x, y + h + 2), (x + h, y + 1), (x - h, y + 1)], 'dg-line')
    if kind == 'tetrahedron': return polygon([(x, y - h), (x + h, y + h), (x - h, y + h)], 'dg-line') + line(x, y - h, x + 2, y + h - 4, 'dg-line-2')
    if kind.startswith('four'): return polygon([(x, y - h), (x + h, y + h - 2), (x, y + h + 2), (x - h, y + h - 2)], 'dg-line') + line(x, y - h, x, y + h + 2, 'dg-line-2')
    if kind == 'cube': return rect(x - h, y - h + 4, s - 4, s - 4, 'dg-line', 0) + polygon([(x - h, y - h + 4), (x - h + 4, y - h), (x + h, y - h), (x + h - 4, y - h + 4)], 'dg-line') + polygon([(x + h - 4, y - h + 4), (x + h, y - h), (x + h, y + h - 4), (x + h - 4, y + h)], 'dg-line')
    return text(x, y + 4, '?', 'dg-muted', size=12)
b = [text(200, 15, 'THE KEYS OF ASCENSION — meditation chart', 'dg-text', size=11.5, weight=700)]
b.append(text(200, 29, 'formlessness → point → line → plane → the nine levels → collapse back', 'dg-muted', size=8.5))
for i, (n, sh, col) in enumerate(lev):
    y = 40 + i * 25
    b.append(rect(10, y, 380, 22, 'dg-line-2 ' + ('dg-fill-2' if i < 2 else ''), 3))
    b.append(solid(sh, 30, y + 11)); b.append(text(60, y + 15, n, 'dg-text', 'start', 10, weight=600)); b.append(text(178, y + 15, sh, 'dg-text', 'start', 9.5))
    b.append(text(385, y + 15, col, 'dg-muted', 'end', 9))
b.append(note(400, 290, 'Text from the 1992 handout; the solid-to-level pairing is the best-supported reading (one alternative shifts every solid one level up).'))
reg('keys-of-ascension', K_HANDOUT, 400, 290, b, 'Keys of Ascension chart')

# 8. Parallel Reality Wheel -------------------------------------------------------------
caps = ['Albrecht Eisenstein proposes relativity','JFK served two terms, lived to 1985','Indian Federation keeps control of the Americas','The Roman Empire continued to the present',
        'The USA elects first female president in 2012','Botticelli paints the Sistine Chapel','The USA is the United States of Atlantis','Peace is brokered in the Middle East in 1967']
b = [text(200, 16, 'THE PARALLEL REALITY WHEEL', 'dg-text', size=12, weight=700)]
cx, cy, r = 200, 158, 74
b.append(circle(cx, cy, r, 'dg-line dg-fill')); b.append(circle(cx, cy, 6, 'dg-ink-fill'))
b.append(text(cx, cy + 9, '?', 'dg-text', size=28, weight=700))
for i in range(8):
    a = math.radians(i * 45 - 90 + 22.5); px, py = cx + r * math.cos(a), cy + r * math.sin(a)
    b.append(line(cx, cy, px, py, 'dg-line-2'))
    b.append(circle(px, py, 9, 'dg-ink-fill')); b.append(text(px, py + 3.5, str(i + 1), 'dg-inv', size=9, weight=700))
    cs, sn = math.cos(a), math.sin(a)
    anchor = 'start' if cs > 0.3 else ('end' if cs < -0.3 else 'middle')
    tx = px + (14 if anchor == 'start' else -14 if anchor == 'end' else 0); ty = py + (20 if sn > 0.3 else -14 if sn < -0.3 else 0)
    b.append(text(tx, ty + 3, caps[i], 'dg-text', anchor, 7.5, maxchars=18, lh=8.5))
b.append(note(400, 300, 'Eight captions verbatim from the 2020 handout; their angular placement on the original is approximate.'))
reg('parallel-reality-wheel', K_HANDOUT, 400, 300, b, 'Parallel Reality Wheel')

# 9. Protocols of First Contact ----------------------------------------------------------
phases = [('Observation', 1, 7), ('Connection individual', 8, 13), ('Sightings & symbols', 14, 21), ('Contact program', 22, 29), ('Physical contact', 30, 33), ('Open contact', 34, 37), ('Alliance membership', 38, 43)]
b = [text(200, 16, 'PROTOCOLS OF FIRST CONTACT — 43 steps', 'dg-text', size=12, weight=700)]
x = 10
for i, (name, s, e) in enumerate(phases):
    n = e - s + 1; w = 6 + n * 6.6
    b.append(rect(x, 32, w, 200, 'dg-line-2 ' + ('dg-fill' if i % 2 == 0 else 'dg-fill-2'), 5))
    b.append(text(x + w / 2, 58, name, 'dg-text', size=7.5, maxchars=11, weight=600, lh=8.5))
    for j in range(n):
        yy = 92 + j * 15
        b.append(circle(x + w / 2, yy, 5.5, 'dg-line')); b.append(text(x + w / 2, yy + 2.5, str(s + j), 'dg-text', size=6.5))
    if i < len(phases) - 1: b.append(arrow(x + w + 1, 130, x + w + 8, 130, 'dg-line-2', 'dg-arrow-2'))
    x += w + 8
b.append(text(200, 250, '1 discovery · 6 sightings · 9 connection with the "connection individual" · 15 contact symbols · 25 Contact Council · 28 precursor contacts · 34 open contact · 41 Interstellar Alliance membership', 'dg-muted', size=8.5, maxchars=95))
b.append(note(400, 300, 'Step numbers verbatim from the 2016 handout; the phase groupings are an aid added here.'))
reg('protocols-of-first-contact', K_HANDOUT, 400, 300, b, 'Protocols of First Contact flow')

# 10. Sacred Circuitry ----------------------------------------------------------------------
b = [text(200, 16, 'SACRED CIRCUITRY — 15 glyph cards', 'dg-text', size=12, weight=700)]
for i in range(15):
    r_, c_ = divmod(i, 5); x = 30 + c_ * 70; y = 34 + r_ * 62
    b.append(rect(x, y, 60, 52, 'dg-line dg-fill', 5)); b.append(text(x + 30, y + 30, f'{i+1}', 'dg-muted', size=16))
b.append(text(200, 236, 'Days 1–3: cards 1→15 in order, ~1 min each · from day 4: any order, ≤15 min, once a day', 'dg-text', size=9.5, maxchars=80))
b.append(note(400, 276, 'The glyph artwork is copyrighted and not reproduced; only the card count and viewing protocol are shown.'))
reg('sacred-circuitry', K_SESSION, 400, 276, b, 'Sacred Circuitry card grid')

# 11. Spectrum of Fear --------------------------------------------------------------------------
sf = [('A','Basic self-awareness','the first reflection'),('SI','Survival instinct',''),('L','Awareness of (self-imposed) limitations','A + SI'),('EX','Experience','learned, accepted parameters'),
      ('C','Caution','alertness'),('W','Wariness','sensing "bad vibes"'),('F','Fear','protective / resistance, pain'),('PAR','Paranoia','irrational; negative beliefs only'),
      ('PAN','Panic','phobias'),('T','Terror','life-threatening'),('','DEATH','existential crisis, dissociation')]
b = [text(200, 15, 'THE SPECTRUM OF FEAR — each level contains all the levels below it', 'dg-text', size=11, weight=700)]
n = len(sf)
for i, (code, name, desc) in enumerate(sf):
    y = 262 - i * 22; w = 60 + i * 30
    b.append(rect(10, y - 18, w, 20, 'dg-line-2 dg-fill', 3, f'opacity="{0.35 + 0.06 * i:.2f}"'))
    b.append(text(14, y - 4, (f'{code}  {name}' if code else name), 'dg-text', 'start', 9.5, weight=600))
    if desc: b.append(text(392, y - 4, desc, 'dg-muted', 'end', 8.5))
b.append(arrow(396, 262, 396, 40, 'dg-line-2', 'dg-arrow-2'))
reg('spectrum-of-fear', K_HANDOUT, 400, 275, b, 'Spectrum of Fear staircase')

# 12. Story Tree ---------------------------------------------------------------------------------
b = [text(200, 16, 'THE STORY TREE', 'dg-text', size=12, weight=700)]
b.append(rect(160, 220, 80, 40, 'dg-line dg-fill', 8)); b.append(text(200, 244, 'the experience', 'dg-text', size=10))
for k, (lab, xs, cls, tags) in enumerate([('negative story (as lived)', 70, 'dg-line', ['A', 'B', 'C']), ('preferred story (present tense)', 330, 'dg-line dg-fill-2', ["A′", "B′", "C′"])]):
    b.append(path(f'M200,220 Q{xs},200 {xs},180', 'dg-line-2'))
    for i, t in enumerate(tags):
        y = 165 - i * 50
        b.append(box(xs - 32, y - 16, 64, 32, t, cls, size=12, weight=700))
        if i < 2: b.append(arrow(xs, y - 16, xs, y - 34, 'dg-line', 'dg-arrow'))
    b.append(text(xs, 205, lab, 'dg-muted', size=8.5, maxchars=20))
b.append(box(160, 120, 80, 34, 'neutralise each moment', 'dg-line-2', size=9))
b.append(arrow(102, 90, 158, 132, 'dg-line-2', 'dg-arrow-2')); b.append(arrow(242, 132, 298, 90, 'dg-line-2', 'dg-arrow-2'))
b.append(text(200, 60, 'each preferred moment logically generates the next', 'dg-muted', size=8.5, maxchars=30))
b.append(note(400, 290, 'A/B/C slots and the process are from the 2016 session; whether the original is drawn as a literal tree is unverified.'))
reg('story-tree', K_SESSION, 400, 290, b, 'Story Tree')

# 13. Triad Mind ----------------------------------------------------------------------------------
b = [text(200, 16, 'THE TRIAD MIND', 'dg-text', size=12, weight=700)]
pts = [(200, 60), (80, 230), (320, 230)]
b.append(polygon(pts, 'dg-line-2'))
b.append(box(140, 40, 120, 40, 'Higher mind', 'dg-line dg-fill-2', size=11, weight=600))
b.append(box(20, 210, 120, 40, 'Heart mind', 'dg-line dg-fill', size=11, weight=600))
b.append(box(260, 210, 120, 40, 'Head / physical mind', 'dg-line dg-fill', size=10.5, weight=600))
b.append(arrow(170, 82, 100, 206, 'dg-line', 'dg-arrow')); b.append(text(110, 140, 'frequency / vibration', 'dg-muted', 'end', 8.5))
b.append(arrow(120, 206, 190, 82, 'dg-line-2', 'dg-arrow-2')); b.append(text(175, 160, 'pure resonance', 'dg-muted', 'start', 8.5))
b.append(arrow(142, 232, 258, 232, 'dg-line', 'dg-arrow')); b.append(text(200, 262, 'filtered through beliefs', 'dg-muted', size=8.5))
b.append(note(400, 290, 'The three minds and the flow are Bashar\'s words (2017); the triangular layout is inferred from "triad".'))
reg('triad-mind', K_SESSION, 400, 290, b, 'Triad Mind')

# 14. UFO Witness Declaration -------------------------------------------------------------------------
b = [text(200, 16, 'UFO WITNESS DECLARATION (2012)', 'dg-text', size=12, weight=700)]
b.append(rect(40, 28, 320, 240, 'dg-line', 6))
for i, (t, s) in enumerate([('FACT', 'Hudson Valley, 1982–85: thousands of witnesses'), ('FACT', 'Belgium, 1989–90: tracked by radar & fighter jets'), ('FACT', 'Arizona, 1997: the "Phoenix lights"')]):
    y = 46 + i * 34
    b.append(rect(52, y, 296, 26, 'dg-line-2 dg-fill', 4)); b.append(text(70, y + 16, t, 'dg-text', 'start', 10, weight=700)); b.append(text(108, y + 16, s, 'dg-text', 'start', 9.5))
b.append(text(200, 168, '"more than 50% of Americans believe…" · "over 36 million Americans have seen a UFO"', 'dg-text', size=9.5, maxchars=60))
b.append(text(200, 205, 'in political terms: a bloc larger than most voting blocs', 'dg-muted', size=9.5, maxchars=50))
b.append(rect(120, 228, 160, 28, 'dg-ink-fill', 6)); b.append(text(200, 246, 'call to action: declare openly', 'dg-inv', size=9.5))
reg('ufo-witness-declaration', K_HANDOUT, 400, 280, b, 'UFO Witness Declaration structure')

# 15. Window of Discovery form ----------------------------------------------------------------------------
b = [text(200, 16, 'WINDOW OF DISCOVERY: 2018–2020', 'dg-text', size=12, weight=700), text(200, 30, 'Bashar event, December 1st, 2017 · please print clearly', 'dg-muted', size=9)]
for i, (h, q) in enumerate([('NEGATIVE', 'What do you REALLY believe is a highly probable negative event in the next 3 years?'), ('POSITIVE', '…highly probable positive event in the next 3 years?')]):
    x = 20 + i * 190
    b.append(rect(x, 42, 170, 150, 'dg-line ' + ('dg-fill' if i == 0 else 'dg-fill-2'), 6)); b.append(text(x + 85, 60, h, 'dg-text', size=11, weight=700))
    b.append(text(x + 85, 92, q, 'dg-text', size=8.5, maxchars=34))
    for k in range(2): b.append(line(x + 14, 140 + k * 24, x + 156, 140 + k * 24, 'dg-line-2'))
b.append(text(200, 214, 'DO NOT write what you want — write what you honestly believe is most likely. DO NOT discuss. DO NOT erase your gut answer.', 'dg-text', size=8.5, maxchars=80))
b.append(rect(150, 236, 100, 24, 'dg-ink-fill', 12)); b.append(text(200, 252, 'YOU HAVE 3 MINUTES', 'dg-inv', size=9.5, weight=700))
reg('window-of-discovery', K_HANDOUT, 400, 275, b, 'Window of Discovery form')

# 16. Belief → Emotion → Thought → Action -----------------------------------------------------------------------
b = [text(200, 16, 'BELIEF → EMOTION → THOUGHT → ACTION → EXPERIENCE', 'dg-text', size=11.5, weight=700)]
labs = ['Belief / definition', 'Emotion', 'Thought', 'Action / behaviour', 'Experience']
for i, l in enumerate(labs):
    x = 8 + i * 78
    b.append(box(x, 44, 70, 44, l, 'dg-line ' + ('dg-fill-2' if i == 0 else 'dg-fill'), size=9.5, weight=600 if i == 0 else None))
    if i < 4: b.append(arrow(x + 71, 66, x + 77, 66, 'dg-line', 'dg-arrow'))
b.append(path('M357,90 Q357,120 200,120 Q43,120 43,90', 'dg-line-2', 'marker-end="url(#dg-arrow-2)"')); b.append(text(200, 133, 'experience appears to confirm the belief (feedback)', 'dg-muted', size=8.5))
b.append(rect(20, 158, 170, 100, 'dg-line-2', 6)); b.append(text(105, 176, 'Circumstances', 'dg-text', size=11, weight=600)); b.append(line(60, 176, 150, 176, 'dg-accent'))
b.append(text(105, 200, 'neutral props — no built-in meaning', 'dg-muted', size=9, maxchars=22))
b.append(text(105, 238, '"circumstances don\'t matter"', 'dg-text', size=9, italic=True))
b.append(rect(210, 158, 170, 100, 'dg-line dg-fill-2', 6)); b.append(text(295, 176, 'State of being', 'dg-text', size=11, weight=600))
b.append(text(295, 200, 'the cause: what you put out is what you get back', 'dg-text', size=9, maxchars=24))
b.append(text(295, 238, '"only state of being matters"', 'dg-text', size=9, italic=True))
reg('belief-emotion-thought-action', K_MODEL, 400, 270, b, 'Belief-emotion-thought-action chain')

# 17. Physical mind / Higher mind --------------------------------------------------------------------------------
b = [text(200, 16, 'HIGHER MIND & PHYSICAL MIND — the division of labour', 'dg-text', size=11.5, weight=700)]
b.append(rect(60, 32, 280, 70, 'dg-line dg-fill-2', 8)); b.append(text(200, 52, 'HIGHER MIND', 'dg-text', size=12, weight=700)); b.append(text(200, 74, 'conceives · sees the whole path · chooses timing · "the pilot"', 'dg-text', size=9.5, maxchars=50))
b.append(rect(60, 122, 280, 26, 'dg-line-2 dg-fill', 6)); b.append(text(200, 139, 'template level  ·  the heart / resonance', 'dg-text', size=9.5))
b.append(rect(60, 168, 280, 70, 'dg-line dg-fill', 8)); b.append(text(200, 188, 'PHYSICAL MIND', 'dg-text', size=12, weight=700)); b.append(text(200, 210, 'perceives · acts on what is in front of it · "the passenger / navigator"', 'dg-text', size=9.5, maxchars=52))
b.append(arrow(30, 104, 30, 166, 'dg-line', 'dg-arrow')); b.append(text(24, 138, 'excitement & synchronicity', 'dg-muted', 'middle', 8, extra='transform="rotate(-90 24 138)"'))
b.append(arrow(372, 166, 372, 104, 'dg-line', 'dg-arrow')); b.append(text(380, 138, 'trust & action', 'dg-muted', 'middle', 8, extra='transform="rotate(90 380 138)"'))
b.append(note(400, 262, 'The physical mind "was never designed to know how" — that is the higher mind\'s job (recurring teaching).'))
reg('physical-mind-higher-mind', K_MODEL, 400, 262, b, 'Higher mind and physical mind')

# 18. Frames of film / parallel shifting -----------------------------------------------------------------------------
b = [text(200, 16, 'PARALLEL REALITIES — shifting through static "frames"', 'dg-text', size=11.5, weight=700)]
for i in range(7):
    x = 12 + i * 54
    b.append(rect(x, 40, 48, 40, 'dg-line', 2))
    for k in range(4): b.append(rect(x + 3 + k * 11.5, 34, 6, 4, 'dg-line-2', 1)); b.append(rect(x + 3 + k * 11.5, 82, 6, 4, 'dg-line-2', 1))
    b.append(circle(x + 14 + i * 3, 60, 5 + i * 0.6, 'dg-line-2'))
b.append(circle(36, 60, 4, 'dg-accent-fill')); b.append(path('M40,58 Q63,40 90,58 Q117,40 144,58 Q171,40 198,58', 'dg-accent', 'marker-end="url(#dg-arrow)"'))
b.append(text(200, 104, 'each frame is a complete, static reality; consciousness "hops" between them ~billions of times per second, producing the feeling of motion and time', 'dg-text', size=9, maxchars=80))
# fan of strips
for i, (dy, lab) in enumerate([(-34, 'reality A'), (0, 'reality B (chosen by your state of being)'), (34, 'reality C')]):
    y = 190 + dy
    b.append(path(f'M60,190 Q120,190 180,{y} L380,{y}', 'dg-line' if i == 1 else 'dg-line-2'))
    for k in range(6): b.append(rect(190 + k * 32, y - 8, 26, 16, 'dg-line-2' if i != 1 else 'dg-line dg-fill', 2))
    b.append(text(382, y - 11, lab, 'dg-muted', 'end', 7.5))
b.append(circle(60, 190, 5, 'dg-accent-fill')); b.append(text(40, 194, 'now', 'dg-text', 'end', 9))
b.append(note(400, 268, '"You don\'t change the world you are on — you shift to a version that reflects the change in you."'))
reg('frames-of-film-parallel-shifting', K_MODEL, 400, 268, b, 'Frames of film model of parallel realities')

# 19. Five Laws ---------------------------------------------------------------------------------------------------------
b = [text(200, 16, 'THE FIVE LAWS OF CREATION', 'dg-text', size=12, weight=700)]
b.append(rect(30, 30, 340, 236, 'dg-line dg-fill-2', 12)); b.append(text(200, 48, 'Law 5 · Everything changes — except the first four laws', 'dg-text', size=10.5, weight=600))
for i, l in enumerate(['Law 1 · You exist', 'Law 2 · Everything is here and now', 'Law 3 · The One is the All and the All are the One', 'Law 4 · What you put out is what you get back']):
    y = 64 + i * 48
    b.append(rect(60, y, 280, 40, 'dg-line dg-fill', 8)); b.append(text(200, y + 24, l, 'dg-text', size=10.5, maxchars=44))
b.append(note(400, 296, 'Wording per bashar.org/fivelaws. An earlier four-law version (1998) omits "here and now".'))
reg('five-laws-of-creation', K_HANDOUT, 400, 296, b, 'Five Laws of Creation')

# 20. Seven steps -----------------------------------------------------------------------------------------------------------
st = [('Vision', 'visualise what you want'), ('Desire', 'be intensely excited'), ('Belief', 'believe it is possible'), ('Acceptance', 'accept it as true'), ('Intent', 'intend, not merely want'), ('Action', 'act as if it has manifested'), ('Allowance', 'detach from the outcome')]
b = [text(200, 16, 'THE SEVEN SEQUENTIAL STEPS OF MANIFESTATION', 'dg-text', size=11.5, weight=700)]
for i, (n, d) in enumerate(st):
    x = 10 + i * 26; y = 240 - i * 30; w = 390 - x
    b.append(rect(x, y, w, 28, 'dg-line ' + ('dg-fill' if i % 2 == 0 else 'dg-fill-2'), 4))
    b.append(text(x + 10, y + 18, f'{i+1}  {n}', 'dg-text', 'start', 10.5, weight=600)); b.append(text(x + w - 8, y + 18, d, 'dg-muted', 'end', 8.5))
b.append(note(400, 298, 'Read bottom to top. Wording per bashar.org/sevensteps (taught in a 1995 session).'))
reg('seven-steps-of-manifestation', K_HANDOUT, 400, 298, b, 'Seven steps staircase')

# 21. Basic Principles ring --------------------------------------------------------------------------------------------------
bp = ['non-physical consciousness in physical reality', 'you chose to be here; ecstasy is your birthright', 'highest purpose: be yourself fully', 'free will, always', 'anything relevant to your theme is possible',
      'beliefs + emotions + actions attract experience', 'excitement = your core vibration; follow it', 'naturally abundant, always supported', 'only one moment in creation', 'you create past & future from now',
      'you are eternal', 'everything you experience is another aspect of you', 'loved so unconditionally you can believe you are not']
b = [text(200, 15, "BASHAR'S 13 BASIC PRINCIPLES", 'dg-text', size=12, weight=700)]
cx, cy, r0, r1 = 96, 160, 34, 70
for i in range(13):
    a0 = i * 360 / 13; a1 = (i + 1) * 360 / 13
    b.append(path(wedge_path(cx, cy, r0, r1, a0 + 0.8, a1 - 0.8), 'dg-line-2 ' + ('dg-fill' if i % 2 == 0 else 'dg-fill-2')))
    am = math.radians(a0 + 180 / 13); mx, my = cx + (r0 + r1) / 2 * math.sin(am), cy - (r0 + r1) / 2 * math.cos(am)
    b.append(text(mx, my + 3.5, str(i + 1), 'dg-text', size=9.5, weight=700))
b.append(text(cx, cy + 4, 'you', 'dg-text', size=12, weight=700))
for i, s in enumerate(bp):
    y = 40 + i * 19
    b.append(text(184, y, f'{i+1}.', 'dg-muted', 'start', 9, weight=700)); b.append(text(200, y, s, 'dg-text', 'start', 8.2))
reg('basic-principles-13', K_HANDOUT, 400, 300, b, 'Thirteen basic principles')

# 22. Excitement formula kit ------------------------------------------------------------------------------------------------------
b = [text(200, 16, 'THE FORMULA + "THE COMPLETE KIT"', 'dg-text', size=12, weight=700)]
for i, l in enumerate(['act on highest excitement', 'to the best of your ability', 'zero insistence on outcome', 'stay positive']):
    b.append(box(8 + i * 97, 32, 90, 44, l, 'dg-line dg-fill-2', size=9.5))
b.append(arrow(200, 80, 200, 104, 'dg-line', 'dg-arrow')); b.append(text(214, 96, 'excitement then contains', 'dg-muted', 'start', 8.5))
kit = ['the driving engine', 'organizing principle (synchronicity)', 'path of least resistance', 'path of connection', 'path of support', 'reflective mirror', 'all the tools you need']
for i, l in enumerate(kit):
    x = 8 + (i % 4) * 97; y = 110 + (i // 4) * 60
    b.append(box(x, y, 90, 50, l, 'dg-line dg-fill', size=9))
b.append(text(345, 180, '= 11 elements', 'dg-text', size=10, weight=600)); b.append(text(345, 196, '(the "1-3-5-7-11")', 'dg-muted', size=8.5))
b.append(note(400, 240, 'Kit property names vary slightly by session.'))
reg('excitement-formula-kit', K_MODEL, 400, 240, b, 'Formula and kit')

# 23. Hybrid races ladder ----------------------------------------------------------------------------------------------------------
b = [text(200, 16, 'THE HYBRID RACES — as described in the 2014–2018 sessions', 'dg-text', size=11, weight=700)]
b.append(rect(150, 28, 100, 38, 'dg-black', 4)); b.append(rect(158, 34, 84, 8, 'dg-black', 0)); b.append(rect(158, 43, 84, 8, 'dg-grey', 0)); b.append(rect(158, 52, 84, 8, 'dg-white', 0))
b.append(text(200, 78, 'Grey Federation (source of the programme)', 'dg-muted', size=8.5))
b.append(text(60, 78, 'Earth humans →', 'dg-muted', size=8.5)); b.append(path('M90,84 Q120,120 330,164', 'dg-line-2', 'marker-end="url(#dg-arrow-2)"'))
flags = [('1st', 'black dot'), ('2nd', 'violet dot'), ('3rd Essassani', 'triangle?'), ('4th', 'gold dot'), ('5th Yahyel', 'green dot'), ('6th Earth', 'hexagon, violet'), ('7th', 'hexagon, star')]
dots = {'black dot': 'dg-black', 'violet dot': 'dg-violet', 'gold dot': 'dg-gold', 'green dot': 'dg-green'}
for i, (n, sym) in enumerate(flags):
    x = 12 + i * 55; y = 96
    b.append(rect(x, y, 48, 48, 'dg-black', 3))
    if 'hexagon' in sym:
        b.append(polygon(regular_polygon(x + 24, y + 24, 17, 6, -90), 'dg-white'))
        b.append(circle(x + 24, y + 24, 4, 'dg-violet') if 'violet' in sym else polygon(regular_polygon(x + 24, y + 24, 8, 6, -90), 'dg-black'))
    elif 'triangle' in sym:
        b.append(polygon(regular_polygon(x + 24, y + 27, 17, 3, -90), 'dg-white')); b.append(text(x + 40, y + 12, '?', 'dg-white-text', size=9))
    else:
        b.append(polygon(regular_polygon(x + 24, y + 24, 17, 5, -90), 'dg-white')); b.append(circle(x + 24, y + 26, 4, dots[sym]))
    b.append(text(x + 24, y + 60, n, 'dg-text', size=7.5, maxchars=13, lh=9));
    if i < 6: b.append(arrow(x + 49, y + 24, x + 54, y + 24, 'dg-line-2', 'dg-arrow-2'))
b.append(text(200, 200, 'Each race is a step in a Grey–human hybridisation programme; Earth is described as becoming the 6th ("homo galacticus").', 'dg-text', size=9, maxchars=70))
b.append(note(400, 236, 'Flag descriptions from fan renderings of the sessions; names of the 1st, 2nd and 4th races were not found in text.'))
reg('hybrid-races-ladder', K_SESSION, 400, 236, b, 'Hybrid races ladder')

# 24. Density ladder -------------------------------------------------------------------------------------------------------------------
b = [text(200, 16, 'DENSITY vs DIMENSION', 'dg-text', size=12, weight=700)]
tiers = [('5th density', 'non-physical light; Essassani upper range', 'steam'), ('4th density', 'transitional, telepathic; Earth\'s shift; Yahyel / Essassani lower range', 'water'), ('3rd density', 'self-aware physical humanity — Earth now', 'ice')]
for i, (n, d, ic) in enumerate(tiers):
    y = 34 + i * 62
    b.append(rect(70, y, 250, 52, 'dg-line ' + ('dg-fill-2' if i == 0 else 'dg-fill'), 6)); b.append(text(195, y + 18, n, 'dg-text', size=11, weight=700)); b.append(text(195, y + 38, d, 'dg-text', size=8.5, maxchars=48))
    x, yy = 40, y + 26
    if ic == 'ice': b.append(rect(x - 12, yy - 12, 24, 24, 'dg-line', 2)); b.append(line(x - 12, yy, x + 12, yy, 'dg-line-2')); b.append(line(x, yy - 12, x, yy + 12, 'dg-line-2'))
    if ic == 'water': b.append(path(f'M{x-14},{yy} q7,-8 14,0 t14,0', 'dg-line')); b.append(path(f'M{x-14},{yy+8} q7,-8 14,0 t14,0', 'dg-line-2'))
    if ic == 'steam': [b.append(path(f'M{x-10+k*10},{yy+10} q4,-8 0,-16 q-4,-6 0,-10', 'dg-line-2')) for k in range(3)]
    b.append(text(x, y + 50, ic, 'dg-muted', size=8))
b.append(arrow(340, 120, 340, 44, 'dg-line', 'dg-arrow')); b.append(text(352, 84, 'the shift', 'dg-muted', 'start', 9))
b.append(text(200, 236, 'dimension = coordinates of space/time (where) · density = vibrational state (how fast/fine)', 'dg-text', size=9, maxchars=70))
b.append(note(400, 278, 'Only the 3rd/4th/5th tiers are attested in the sources used; the ice/water/steam icons are an analogy.'))
reg('density-dimension-ladder', K_MODEL, 400, 278, b, 'Density ladder')

# 25. Eye of the needle ---------------------------------------------------------------------------------------------------------------------
b = [text(200, 16, 'THE EYE OF THE NEEDLE — 2020 as a pivotal point', 'dg-text', size=11.5, weight=700)]
for i in range(9):
    y0 = 50 + i * 20
    b.append(path(f'M10,{y0} C120,{y0} 150,150 200,150', 'dg-line-2'))
for i, (y1, cls, lab) in enumerate([(70, 'dg-accent', 'positive Earth'), (110, 'dg-line-2', ''), (150, 'dg-line-2', ''), (190, 'dg-line-2', ''), (230, 'dg-line', 'negative Earth')]):
    b.append(path(f'M200,150 C250,150 280,{y1} 390,{y1}', cls))
    if lab: b.append(text(388, y1 - 6, lab, 'dg-muted', 'end', 8.5))
b.append(circle(200, 150, 9, 'dg-line dg-fill')); b.append(text(200, 176, '2020', 'dg-text', size=11, weight=700)); b.append(text(200, 190, 'the aperture', 'dg-muted', size=8.5))
b.append(text(60, 250, 'many overlapping timelines converge…', 'dg-muted', 'start', 8.5)); b.append(text(390, 250, '…then diverge into distinct worlds', 'dg-muted', 'end', 8.5))
b.append(note(400, 290, 'Bashar\'s metaphor (April 2020); the five permission-slip steps of that session were not recovered, so none are shown.'))
reg('eye-of-the-needle', K_SESSION, 400, 290, b, 'Eye of the Needle hourglass')

# 26. 1-3-5-7-11 -------------------------------------------------------------------------------------------------------------------------------
b = [text(200, 16, 'THE 1-3-5-7-11 DOWNLOAD', 'dg-text', size=12, weight=700)]
tiers = [('1', 'the One — existence'), ('3', 'the trinity: original · reflection · balance point'), ('5', 'the five laws of creation'), ('7', 'seven neutral needs: air, water, sleep/dream, food, shelter, connection, creative expression'), ('11', 'the formula: 4 steps + 7 tools')]
for i, (n, d) in enumerate(tiers):
    y = 30 + i * 46; w = 120 + i * 66; x = 200 - w / 2
    b.append(rect(x, y, w, 40, 'dg-line ' + ('dg-fill-2' if i % 2 == 0 else 'dg-fill'), 6))
    b.append(text(x + 22, y + 25, n, 'dg-text', size=16, weight=700)); b.append(text(x + 44 + (w - 60) / 2, y + 24, d, 'dg-text', size=9, maxchars=int((w - 60) / 5.2)))
reg('1-3-5-7-11-download', K_SESSION, 400, 268, b, '1-3-5-7-11 tiers')

# 27. Prime radiant -------------------------------------------------------------------------------------------------------------------------------
b = [text(200, 16, 'THE PRIME RADIANT — one particle drawing all of reality', 'dg-text', size=11.5, weight=700)]
pts = []
for t in range(0, 1000, 3):
    u = t / 1000 * 2 * math.pi
    pts.append((200 + 150 * math.sin(5 * u + 0.6), 148 + 80 * math.sin(6 * u)))
d = 'M' + ' L'.join(f'{x:.1f},{y:.1f}' for x, y in pts) + ' Z'
b.append(path(d, 'dg-line-2'))
b.append(circle(200, 150, 26, 'dg-accent-fill', 'opacity="0.35"')); b.append(text(200, 154, 'matter', 'dg-text', size=9))
b.append(text(200, 236, 'where the single infinitely fast line crosses itself densely = "space/time" (matter); the gaps between = "time/space" (energy)', 'dg-text', size=9, maxchars=76))
b.append(note(400, 262, 'Illustrative knot; no official figure exists.'))
reg('prime-radiant', K_MODEL, 400, 262, b, 'Prime radiant')

# 28. Construction of physical reality ---------------------------------------------------------------------------------------------------------------
b = [text(200, 15, 'FROM THE ONE TO THE PERSONALITY — construction of physical reality', 'dg-text', size=10.5, weight=700)]
tiers = ['The One / Infinite', 'First reflection (angelic)', 'Trinity: original · reflection · balance point', 'Vesica piscis', 'Oversoul', 'Individual soul = higher mind + physical mind', 'Template level', 'Pineal gland (interface)', 'Personality: beliefs · emotions · actions', 'Physical reality']
for i, t in enumerate(tiers):
    y = 26 + i * 25
    b.append(rect(80, y, 240, 21, 'dg-line-2 ' + ('dg-fill-2' if i < 5 else 'dg-fill'), 3)); b.append(text(200, y + 14, t, 'dg-text', size=9.5, maxchars=46))
    if i == 2: b.append(polygon([(50, y + 19), (62, y + 2), (74, y + 19)], 'dg-line'))
    if i == 3: b.append(circle(56, y + 10, 8, 'dg-line-2')); b.append(circle(66, y + 10, 8, 'dg-line-2'))
    if i < 9: b.append(arrow(340, y + 4, 340, y + 22, 'dg-line-2', 'dg-arrow-2'))
b.append(note(400, 290, 'Compiled from several sessions by a secondary source; not an official handout.'))
reg('construction-of-physical-reality', K_MODEL, 400, 290, b, 'Descent from the One')

# 29. Essassani AI spheres -----------------------------------------------------------------------------------------------------------------------------------
b = [text(200, 16, 'EPSILON · EPIPHANY · ECLIPSE — the three spheres of Essassani', 'dg-text', size=11, weight=700)]
cx, cy, R = 200, 160, 82
b.append(circle(cx, cy, 30, 'dg-line dg-fill-2')); b.append(text(cx, cy + 4, 'Essassani', 'dg-text', size=9.5, weight=600))
tri = regular_polygon(cx, cy, R, 3, -90); b.append(polygon(tri, 'dg-line-2'))
for (x, y), n in zip(tri, ['Epsilon (senior)', 'Eclipse', 'Epiphany']):
    b.append(circle(x, y, 18, 'dg-line dg-fill')); b.append(circle(x, y, 12, 'dg-line-2')); b.append(circle(x, y, 6, 'dg-line-2'))
    b.append(text(x, y + (34 if y > cy else -26), n, 'dg-text', size=9))
b.append(text(200, 262, 'three AI spheres (~75 mi / 120 km each, hundreds of thin layers) orbiting the planet at 120°; with the planet they form a tetrahedron — a "trinary consciousness"', 'dg-text', size=8.5, maxchars=80))
reg('essassani-ai-spheres-triad', K_SESSION, 400, 290, b, 'Essassani AI spheres')

# 30. Spiral exercise ---------------------------------------------------------------------------------------------------------------------------------------------
b = [text(200, 16, 'THE SPIRAL — a neurological permission slip', 'dg-text', size=12, weight=700)]
pts = []
for t in range(0, 1440, 6):
    a = math.radians(t); r = 4 + t / 1440 * 78
    pts.append((120 + r * math.cos(a), 150 + r * math.sin(a)))
b.append(path('M' + ' L'.join(f'{x:.1f},{y:.1f}' for x, y in pts), 'dg-line'))
b.append(arrow(120 + 84, 150 - 8, 120 + 40, 150 - 8, 'dg-accent', 'dg-arrow')); b.append(text(120, 250, 'inward → core of being · outward → manifestation', 'dg-muted', size=8.5))
# squared spiral
sq = [(300, 150)]; x, y = 300, 150; L = 8
for i in range(9):
    dx, dy = [(1, 0), (0, 1), (-1, 0), (0, -1)][i % 4]; L += 9 if i % 2 else 9; x += dx * L; y += dy * L; sq.append((x, y))
b.append(path('M' + ' L'.join(f'{x:.1f},{y:.1f}' for x, y in sq), 'dg-line-2'))
b.append(text(300, 250, 'squared spiral → implies a cube', 'dg-muted', size=8.5))
b.append(note(400, 275, 'Relax · gaze at or picture the spiral · trace inward to the core · reverse outward · let it become meditative.'))
reg('spiral-exercise', K_SESSION, 400, 275, b, 'Spiral exercise')

# 31. Holotope --------------------------------------------------------------------------------------------------------------------------------------------------------
b = [text(200, 16, 'THE HOLOTOPE — a radial meditation image (original lattice, not the artwork)', 'dg-text', size=10.5, weight=700)]
cx, cy = 200, 158
for k in range(24):
    a = math.radians(k * 15); b.append(line(cx, cy, cx + 105 * math.cos(a), cy + 105 * math.sin(a), 'dg-line-2', 'opacity="0.5"'))
for r in (18, 36, 56, 78, 102):
    b.append(polygon(regular_polygon(cx, cy, r, 12, -90 + r), 'dg-line-2'))
b.append(circle(cx, cy, 10, 'dg-accent-fill')); b.append(circle(cx, cy, 4, 'dg-white'))
b.append(note(400, 288, 'Relax and breathe · focus on the centre · hold the chosen state ~15 min · return softly when distracted.'))
reg('holotope', K_CONCEPT, 400, 288, b, 'Holotope lattice')

# 32. Social experiment steps ------------------------------------------------------------------------------------------------------------------------------------
se = ['Alignment', 'Daily routines', 'Practical action', 'Dual identity / homo galacticus', 'Volunteer Corps', 'Gatherings', 'Open Contact', 'Shifting realities']
b = [text(200, 16, 'THE INTERSTELLAR ALLIANCE SOCIAL EXPERIMENT — 8 steps (2024)', 'dg-text', size=10.5, weight=700)]
for i, s in enumerate(se):
    x = 10 + i * 37; y = 236 - i * 26; w = 390 - x
    b.append(rect(x, y, w, 24, 'dg-line ' + ('dg-fill' if i % 2 == 0 else 'dg-fill-2'), 4)); b.append(text(x + 8, y + 16, f'{i+1}  {s}', 'dg-text', 'start', 10, weight=600))
b.append(note(400, 292, 'Step titles per the official bashar.org guide page; released sequentially through 2024.'))
reg('interstellar-alliance-social-experiment', K_HANDOUT, 400, 292, b, 'Social experiment steps')

# 33. Guide to open contact ------------------------------------------------------------------------------------------------------------------------------------
b = [text(200, 16, 'GUIDE TO OPEN CONTACT — the Window, the Door & the Gate', 'dg-text', size=11, weight=700)]
for i, (n, d) in enumerate([('WINDOW', 'sightings, dreams, precursors'), ('DOOR', 'individual & small-group encounters'), ('GATE', 'open contact, galactic citizenship')]):
    x = 28 + i * 124
    b.append(rect(x, 40, 96, 90, 'dg-line ' + ('dg-fill' if i < 2 else 'dg-fill-2'), 8)); b.append(rect(x + 14, 54, 68, 62, 'dg-line-2', 4))
    b.append(text(x + 48, 82, n, 'dg-text', size=12, weight=700)); b.append(text(x + 48, 102, d, 'dg-text', size=8, maxchars=18))
    if i < 2: b.append(arrow(x + 98, 85, x + 122, 85, 'dg-line', 'dg-arrow'))
b.append(text(200, 152, 'preparatory sessions: Increasing the Probability of Contact → Tell Them Bashar Sent You → Breaking News → Mirror, Mirror → Matters of the Heart → The Window, the Door & the Gate → Becoming a Galactic Citizen 1–3 → In Two Worlds', 'dg-muted', size=8, maxchars=90))
b.append(line(30, 210, 370, 210, 'dg-line'));
for xx, lab in [(30, '1947 Roswell'), (200, '2025'), (370, '2033')]:
    b.append(line(xx, 204, xx, 216, 'dg-line')); b.append(text(xx, 232, lab, 'dg-muted', size=8.5))
b.append(rect(200, 200, 170, 20, 'dg-fill-2', 3, 'opacity="0.6"')); b.append(text(285, 196, 'contact window 2025–2033', 'dg-text', size=8.5))
b.append(circle(242, 210, 6, 'dg-accent-fill')); b.append(text(242, 246, '2027 fulcrum', 'dg-text', size=9, weight=600))
reg('guide-to-open-contact-window-door-gate', K_MODEL, 400, 260, b, 'Window door gate sequence')

# 34. Permission slips concept ---------------------------------------------------------------------------------------------------------------------------------
b = [text(200, 16, 'PERMISSION SLIPS — the tool has no power of its own', 'dg-text', size=11.5, weight=700)]
nodes = [(50, 90, 'You (already able)'), (200, 60, 'permission slip: object, ritual, teacher…'), (350, 90, 'belief: "now I\'m allowed"'), (300, 200, 'state shift'), (100, 200, 'experience')]
for x, y, l in nodes: b.append(box(x - 46, y - 22, 92, 44, l, 'dg-line dg-fill', size=8.5))
b.append(arrow(96, 82, 154, 68, 'dg-line', 'dg-arrow')); b.append(arrow(246, 68, 304, 82, 'dg-line', 'dg-arrow')); b.append(arrow(340, 112, 312, 178, 'dg-line', 'dg-arrow')); b.append(arrow(254, 200, 146, 200, 'dg-line', 'dg-arrow'))
b.append(path('M70,112 Q140,150 254,190', 'dg-line-2', 'marker-end="url(#dg-arrow-2)"')); b.append(text(150, 140, 'the shortcut: you never needed it', 'dg-muted', size=8.5, italic=True))
b.append(note(400, 250, '"Hold them lightly" — a permission slip works only because you decide it does.'))
reg('permission-slips-concept', K_MODEL, 400, 250, b, 'Permission slip loop')
