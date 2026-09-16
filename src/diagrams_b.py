"""Original SVG concept illustrations — part B (handouts whose layout could not be verified)."""
import math
from svglib import *
from diagrams_a import D, reg, K_CONCEPT, K_SESSION

# 35. 33rd Parallel — parallel incarnations ---------------------------------------------------------------
b = [text(200, 16, 'THE 33RD PARALLEL — parallel incarnations (concept)', 'dg-text', size=11.5, weight=700)]
b.append(rect(160, 30, 80, 30, 'dg-line dg-fill-2', 8)); b.append(text(200, 49, 'one consciousness', 'dg-text', size=9))
for i in range(5):
    y = 90 + i * 30
    b.append(path(f'M200,60 C200,{y-10} 40,{y-10} 40,{y}', 'dg-line-2')); b.append(line(40, y, 380, y, 'dg-line' if i == 2 else 'dg-line-2'))
    b.append(text(392, y + 3, ['a', 'b', 'you', 'd', 'e'][i], 'dg-muted', 'start', 8.5))
    for k in range(3): b.append(circle(100 + k * 110 + i * 9, y, 3, 'dg-accent-fill'))
b.append(path('M209,150 L209,120', 'dg-accent', 'marker-end="url(#dg-arrow)"')); b.append(path('M328,150 L328,180', 'dg-accent', 'marker-end="url(#dg-arrow)"'))
b.append(text(200, 245, 'simultaneous lives run in parallel and can exchange information; "Willa\'s PIN chart" maps such parallel incarnations', 'dg-text', size=8.5, maxchars=80))
b.append(note(400, 286, 'The handout\'s own chart is unreadable; this only illustrates the idea Willa/Bashar describe.'))
reg('33rd-parallel', K_CONCEPT, 400, 286, b, 'Parallel incarnations concept')

# 36. As above, so below --------------------------------------------------------------------------------
b = [text(200, 16, 'AS ABOVE, SO BELOW (concept)', 'dg-text', size=12, weight=700)]
up = ['The One', 'first reflection', 'trinity / balance point', 'oversoul', 'soul: higher mind + physical mind']
dn = ['template level', 'beliefs', 'emotions', 'thoughts / actions', 'physical experience']
for i, t in enumerate(up):
    y = 30 + i * 22; w = 120 + i * 40; b.append(rect(200 - w / 2, y, w, 18, 'dg-line-2 dg-fill-2', 3)); b.append(text(200, y + 12.5, t, 'dg-text', size=9))
b.append(line(20, 150, 380, 150, 'dg-accent')); b.append(text(200, 165, 'the same pattern repeats at every scale', 'dg-muted', size=8))
for i, t in enumerate(dn):
    y = 172 + i * 22; w = 280 - i * 40; b.append(rect(200 - w / 2, y, w, 18, 'dg-line-2 dg-fill', 3)); b.append(text(200, y + 12.5, t, 'dg-text', size=9))
b.append(note(400, 300, 'Inferred from the 2017 session description; the handout image was not readable.'))
reg('as-above-so-below', K_CONCEPT, 400, 300, b, 'As above so below mirror')

# 37. Brick walls and beliefs ---------------------------------------------------------------------------------
b = [text(200, 16, 'BRICK WALLS & BELIEFS (concept)', 'dg-text', size=12, weight=700)]
labels = ['"that\'s just how it is"', 'not enough', 'unsafe', 'not worthy', 'letting go will hurt', 'it protects me', 'change is impossible', 'nobody would', 'too late', 'I can\'t', 'unlovable', 'must be perfect']
k = 0
for r in range(3):
    off = 0 if r % 2 == 0 else 45
    for c in range(4):
        x = 20 + off + c * 90; y = 36 + r * 40
        if x + 86 > 385: continue
        hot = (r == 1 and c == 1)
        b.append(rect(x, y, 86, 34, 'dg-line ' + ('dg-fill-2' if hot else 'dg-fill'), 2)); b.append(text(x + 43, y + 21, labels[k % len(labels)], 'dg-text', size=8.5, maxchars=16)); k += 1
b.append(path('M198,150 L198,170', 'dg-accent', 'marker-end="url(#dg-arrow)"'))
b.append(text(200, 186, 'the brick with the emotional charge is the clue', 'dg-text', size=9.5, weight=600))
b.append(text(200, 212, 'each brick is a definition holding the wall up; find the one behind the repeating block, examine what releasing it would mean, replace it', 'dg-text', size=9, maxchars=76))
b.append(note(400, 252, 'Bashar\'s metaphor from the 2009 workshop; the handout\'s own drawing is unverified.'))
reg('brick-walls-and-beliefs', K_CONCEPT, 400, 252, b, 'Brick wall of beliefs')

# 38. Changing core beliefs ---------------------------------------------------------------------------------------
b = [text(200, 16, 'CHANGING CORE BELIEFS (concept)', 'dg-text', size=12, weight=700)]
b.append(rect(120, 200, 160, 40, 'dg-line dg-fill-2', 8)); b.append(text(200, 218, 'core belief', 'dg-text', size=10, weight=700)); b.append(text(200, 232, '"I am not enough / not worthy / not safe"', 'dg-text', size=8))
for i, s in enumerate(['I must work harder', 'people leave', 'money is scarce', 'I\'ll be judged', 'it never works out']):
    x = 40 + i * 80
    b.append(path(f'M200,200 Q{x},170 {x},120', 'dg-line-2')); b.append(box(x - 36, 84, 72, 36, s, 'dg-line dg-fill', size=8.5))
b.append(text(200, 60, 'surface beliefs (many)', 'dg-muted', size=9)); b.append(text(200, 48, 'trace the emotional trigger downward to the root definition', 'dg-text', size=9))
b.append(text(60, 262, 'ask: "what would I have to believe is true to feel this way?"', 'dg-muted', 'start', 8.5, italic=True))
reg('changing-core-beliefs', K_CONCEPT, 400, 280, b, 'Core belief root')

# 39. Eclipse ---------------------------------------------------------------------------------------------------------
b = [text(200, 16, 'ECLIPSE (concept)', 'dg-text', size=12, weight=700)]
b.append(circle(170, 130, 60, 'dg-line dg-fill')); b.append(circle(230, 130, 60, 'dg-line dg-fill-2'))
b.append(text(140, 134, 'polarity', 'dg-text', size=9)); b.append(text(260, 134, 'polarity', 'dg-text', size=9)); b.append(text(200, 134, 'blend', 'dg-text', size=9, weight=700))
b.append(text(200, 214, 'the Aug 21, 2017 total eclipse as a symbol of blending and balancing the polarities within ourselves', 'dg-text', size=9, maxchars=70))
b.append(text(200, 242, 'also the name of one of Essassani\'s three AI spheres (see Epsilon · Epiphany · Eclipse)', 'dg-muted', size=8.5, maxchars=80))
reg('eclipse', K_CONCEPT, 400, 262, b, 'Eclipse polarities')

# 40. Increasing the probability of contact ---------------------------------------------------------------------------------
b = [text(200, 16, 'INCREASING THE PROBABILITY OF CONTACT (concept)', 'dg-text', size=11, weight=700)]
b.append(line(40, 220, 380, 220, 'dg-line')); b.append(line(40, 220, 40, 40, 'dg-line'))
b.append(path('M40,215 C150,215 220,150 380,50', 'dg-accent')); b.append(text(50, 34, 'probability of contact', 'dg-muted', 'start', 8.5))
for i, s in enumerate(['imagine a craft / being appearing', 'small, gentle real surprises', 'startle reflex no longer fires', 'calm, welcoming state']):
    x = 70 + i * 90; b.append(circle(x, 220, 4, 'dg-accent-fill')); b.append(text(x, 240, s, 'dg-text', size=8, maxchars=16, lh=9))
b.append(text(200, 100, 'train the nervous system not to be startled', 'dg-text', size=10, weight=600))
reg('increasing-the-probability-of-contact', K_CONCEPT, 400, 268, b, 'Contact probability concept')

# 41. Interdimensional portals ----------------------------------------------------------------------------------------------------------
b = [text(200, 16, 'THE INTERDIMENSIONAL PORTALS AND WHERE TO FIND THEM (concept)', 'dg-text', size=10, weight=700)]
b.append(path('M60,40 L300,40 L340,120 L330,230 L110,235 L70,180 Z', 'dg-line-2 dg-fill', 'opacity="0.7"')); b.append(text(90, 60, 'western US (schematic)', 'dg-muted', 'start', 8))
sites = [(215, 150, 'Sedona AZ ✓'), (300, 135, 'Santa Fe area ✓'), (120, 90, '?'), (150, 200, '?'), (250, 210, '?')]
for x, y, l in sites:
    b.append(circle(x, y, 7, 'dg-accent-fill' if '✓' in l else 'dg-line-2')); b.append(text(x, y - 12, l, 'dg-text', size=8.5))
b.append(text(200, 258, 'five vortices/portals tied to chakras for locking in a preferred state during 2019; only two sites are confirmed by text sources', 'dg-text', size=8.5, maxchars=80))
reg('interdimensional-portals', K_CONCEPT, 400, 280, b, 'Portal sites concept')

# 42. Mechanics of channeling (circuit) ---------------------------------------------------------------------------------------------------
b = [text(200, 16, 'THE MECHANICS OF CHANNELING — as a circuit (concept)', 'dg-text', size=11, weight=700)]
comps = [(60, 'non-physical consciousness (source)'), (150, 'template level'), (240, 'brain: receiver & translator'), (330, 'speech / output')]
for x, l in comps:
    b.append(box(x - 40, 60, 80, 50, l, 'dg-line dg-fill', size=8.5))
for i in range(3): b.append(line(comps[i][0] + 40, 85, comps[i + 1][0] - 40, 85, 'dg-line'))
# resistor as belief filter
b.append(path('M180,85 l4,-6 l6,12 l6,-12 l6,12 l6,-12 l4,6', 'dg-accent')); b.append(text(205, 128, 'belief filter (resistance)', 'dg-muted', size=8))
b.append(box(200, 160, 80, 40, 'heart: resonance', 'dg-line dg-fill-2', size=9)); b.append(line(240, 110, 240, 160, 'dg-line-2')); b.append(line(240, 200, 240, 224, 'dg-line-2'))
b.append(text(240, 236, 'gamma brain-state · relaxed definitions = clean signal', 'dg-muted', size=8.5))
b.append(note(400, 262, 'Only the "circuit diagram" metaphor is confirmed for the 2015 handout; component labels are inferred from Bashar\'s general account.'))
reg('mechanics-of-channeling', K_CONCEPT, 400, 262, b, 'Channeling circuit')

# 43. Parallel realities diagram 1997 ---------------------------------------------------------------------------------------------------------
b = [text(200, 16, 'PARALLEL REALITIES (1997) — the frame model (concept)', 'dg-text', size=11.5, weight=700)]
for r in range(4):
    for c in range(7):
        x = 30 + c * 50; y = 40 + r * 44
        b.append(rect(x, y, 40, 32, 'dg-line-2', 2)); b.append(circle(x + 10 + c * 2, y + 16, 3 + r, 'dg-line-2'))
pathpts = [(50, 56), (100, 100), (150, 100), (200, 144), (250, 188), (300, 188), (350, 232)]
b.append(path('M' + ' L'.join(f'{x},{y}' for x, y in pathpts), 'dg-accent', 'marker-end="url(#dg-arrow)"'))
b.append(text(200, 236, 'every version already exists, static; the sequence consciousness selects is experienced as motion, time and change', 'dg-text', size=8.5, maxchars=80))
b.append(note(400, 280, 'The store notes Bashar supplied a diagram "to simplify the idea"; its contents were not recoverable.'))
reg('parallel-realities-diagram-1997', K_CONCEPT, 400, 280, b, 'Frame grid')

# 44. Preparing for contact 101 ----------------------------------------------------------------------------------------------------------------
b = [text(200, 16, 'PREPARING FOR CONTACT 101 — session map (concept)', 'dg-text', size=11.5, weight=700)]
b.append(f'<ellipse cx="200" cy="120" rx="150" ry="52" class="dg-line dg-fill"/>'); b.append(f'<ellipse cx="200" cy="120" rx="90" ry="30" class="dg-line-2"/>'); b.append(f'<ellipse cx="200" cy="120" rx="30" ry="10" class="dg-line-2"/>')
for x, y, l in [(90, 120, 'zone ?'), (310, 120, 'zone ?'), (200, 96, 'zone ?'), (200, 120, '"a gift"')]:
    b.append(text(x, y + 3, l, 'dg-muted' if '?' in l else 'dg-text', size=8.5))
b.append(text(200, 190, 'meditation 1: aboard a craft to retrieve a gift of self-knowledge', 'dg-text', size=9)); b.append(text(200, 206, 'meditation 2: into the parallel "template" reality of Earth', 'dg-text', size=9)); b.append(text(200, 222, 'exercise: where are the craft? · symbol-deciphering game', 'dg-text', size=9))
b.append(note(400, 250, 'The 2005 graphics "show the different locations on a space ship"; the zones themselves are unknown.'))
reg('preparing-for-contact-101', K_CONCEPT, 400, 250, b, 'Craft zones concept')

# 45. Reincarnation deeper explanation ----------------------------------------------------------------------------------------------------------------
b = [text(200, 16, 'REINCARNATION — simultaneous, not sequential (concept)', 'dg-text', size=11.5, weight=700)]
b.append(text(90, 40, 'the usual picture', 'dg-muted', size=9))
for i in range(5):
    x = 30 + i * 32; b.append(rect(x, 52, 24, 18, 'dg-line-2', 3));
    if i < 4: b.append(arrow(x + 25, 61, x + 31, 61, 'dg-line-2', 'dg-arrow-2'))
b.append(text(90, 86, 'lives end to end', 'dg-muted', size=8.5))
b.append(text(280, 40, "Bashar's picture", 'dg-muted', size=9))
b.append(circle(280, 150, 24, 'dg-line dg-fill-2')); b.append(text(280, 154, 'oversoul', 'dg-text', size=8.5))
for i in range(7):
    a = math.radians(-150 + i * 43); x, y = 280 + 78 * math.cos(a), 150 + 78 * math.sin(a)
    b.append(line(280 + 24 * math.cos(a), 150 + 24 * math.sin(a), x, y, 'dg-line')); b.append(rect(x - 11, y - 8, 22, 16, 'dg-line dg-fill', 3))
b.append(path('M225,110 Q250,60 320,95', 'dg-accent', 'marker-end="url(#dg-arrow)"')); b.append(text(90, 150, 'information flows between lives ("past life" = a parallel life you tune into)', 'dg-muted', 'middle', 8, maxchars=26))
b.append(text(200, 252, 'all lives exist at once in the one moment, like fingers of one hand', 'dg-text', size=9))
reg('reincarnation-deeper-explanation', K_CONCEPT, 400, 268, b, 'Simultaneous incarnations')

# 46. Resonance & reflection ---------------------------------------------------------------------------------------------------------------------------------
b = [text(200, 16, 'RESONANCE & REFLECTION (concept)', 'dg-text', size=12, weight=700)]
b.append(circle(60, 140, 22, 'dg-line dg-fill-2')); b.append(text(60, 144, 'you', 'dg-text', size=10, weight=600)); b.append(text(60, 176, 'state of being', 'dg-muted', size=8.5))
b.append(line(320, 60, 320, 220, 'dg-line')); b.append(text(340, 140, 'the mirror', 'dg-muted', 'start', 9, extra='transform="rotate(90 340 140)"'))
w = 'M90,120 ' + ' '.join(f'q10,-14 20,0 t20,0' for _ in range(5)); b.append(path(w, 'dg-accent', 'marker-end="url(#dg-arrow)"')); b.append(text(200, 100, 'frequency you generate', 'dg-muted', size=8.5))
w2 = 'M310,160 ' + ' '.join(f'q-10,14 -20,0 t-20,0' for _ in range(5)); b.append(path(w2, 'dg-accent', 'marker-end="url(#dg-arrow)"')); b.append(text(200, 190, 'reflected back as experience', 'dg-muted', size=8.5))
b.append(text(200, 246, '"what you put out is what you get back" — non-matching frequencies simply aren\'t reflected', 'dg-text', size=9, maxchars=70))
reg('resonance-and-reflection', K_CONCEPT, 400, 268, b, 'Resonance reflection')

# 47. Circle of self empowerment ---------------------------------------------------------------------------------------------------------------------------------
b = [text(200, 16, 'CIRCLE OF SELF EMPOWERMENT (concept)', 'dg-text', size=12, weight=700)]
cx, cy = 200, 150
for i, l in enumerate(['shift brain state', 'raise frequency', 'align with the natural self', 'act from empowerment']):
    a0 = i * 90; a1 = a0 + 90
    b.append(path(wedge_path(cx, cy, 40, 92, a0 + 2, a1 - 2), 'dg-line-2 ' + ('dg-fill' if i % 2 else 'dg-fill-2')))
    am = math.radians(a0 + 45); b.append(text(cx + 66 * math.sin(am), cy - 66 * math.cos(am) + 3, l, 'dg-text', size=8, maxchars=12, lh=9))
b.append(text(cx, cy + 4, 'you', 'dg-text', size=11, weight=700))
b.append(note(400, 270, 'Only the name confirms a circle; segment contents of the 2017 "birthday gift" handout are unverified.'))
reg('circle-of-self-empowerment', K_CONCEPT, 400, 270, b, 'Self empowerment circle')

# 48. Soul blueprint --------------------------------------------------------------------------------------------------------------------------------------------------
b = [text(200, 16, 'THE SOUL BLUEPRINT (concept)', 'dg-text', size=12, weight=700)]
b.append(rect(40, 36, 320, 96, 'dg-line dg-fill-2', 8)); b.append(text(200, 54, 'template level — the blueprint chosen before incarnation', 'dg-text', size=9.5, weight=600))
for i, l in enumerate(['themes', 'attributes & talents', 'challenges', 'agreements']):
    b.append(box(52 + i * 78, 66, 70, 52, l, 'dg-line-2 dg-fill', size=9))
b.append(arrow(200, 134, 200, 166, 'dg-line', 'dg-arrow')); b.append(text(214, 152, 'played out by', 'dg-muted', 'start', 8.5))
b.append(rect(90, 168, 220, 44, 'dg-line dg-fill', 8)); b.append(text(200, 186, 'the personality', 'dg-text', size=10, weight=600)); b.append(text(200, 204, 'read it through what excites and what triggers you', 'dg-text', size=8.5))
b.append(note(400, 240, '"Visual charts" were used in the 2005 workshop but are undescribed; this shows the concept only.'))
reg('soul-blueprint-workshop', K_CONCEPT, 400, 240, b, 'Soul blueprint concept')

# 49. Tell them Bashar sent you -----------------------------------------------------------------------------------------------------------------------------------
b = [text(200, 16, 'TELL THEM BASHAR SENT YOU (concept)', 'dg-text', size=12, weight=700)]
for i, l in enumerate(['sleep / altered state', 'lucid awareness in the dream', 'encounter (Yahyel & others)', 'the pass-phrase: "Bashar sent me"', 'recall & integrate on waking']):
    x = 12 + i * 78
    b.append(box(x, 60, 70, 60, l, 'dg-line ' + ('dg-fill-2' if i == 3 else 'dg-fill'), size=8.5))
    if i < 4: b.append(arrow(x + 71, 90, x + 77, 90, 'dg-line', 'dg-arrow'))
b.append(text(200, 150, 'a permission slip signalling readiness and friendly intent — step 2 of the Guide to Open Contact (2021)', 'dg-text', size=9, maxchars=70))
reg('tell-them-bashar-sent-you', K_CONCEPT, 400, 180, b, 'Dream contact pass phrase')

# 50. 'Tis the season ---------------------------------------------------------------------------------------------------------------------------------------------------------------
b = [text(200, 16, "'TIS THE SEASON", 'dg-text', size=12, weight=700)]
b.append(circle(200, 110, 34, 'dg-line dg-fill-2')); [b.append(line(200 + 44 * math.cos(math.radians(a)), 110 + 44 * math.sin(math.radians(a)), 200 + 58 * math.cos(math.radians(a)), 110 + 58 * math.sin(math.radians(a)), 'dg-line-2')) for a in range(0, 360, 30)]
b.append(text(200, 186, 'a holiday-season handout listed on bashar.org; no description of its contents could be found', 'dg-muted', size=9, maxchars=60))
b.append(text(200, 220, 'Bashar\'s December sessions usually reinterpret solstice light and gift-giving as permission slips for generosity and self-worth', 'dg-text', size=8.5, maxchars=80))
reg('tis-the-season', K_CONCEPT, 400, 250, b, 'Season placeholder')

# 51. Transforming core beliefs worksheet ------------------------------------------------------------------------------------------------------------------------------------
b = [text(200, 16, 'TRANSFORMING CORE BELIEFS — the writing tool (concept)', 'dg-text', size=11, weight=700)]
cols = ['the limiting belief', 'what would I have to believe for this to feel true?', 'what fear stops me releasing it?', 'how does holding it serve me?', 'the preferred definition']
for i, c in enumerate(cols):
    x = 8 + i * 78
    b.append(rect(x, 32, 72, 200, 'dg-line-2 ' + ('dg-fill' if i % 2 == 0 else ''), 4)); b.append(text(x + 36, 56, c, 'dg-text', size=8, maxchars=15, lh=9))
    for k in range(5): b.append(line(x + 8, 100 + k * 26, x + 64, 100 + k * 26, 'dg-line-2'))
b.append(note(400, 258, 'Bashar\'s diagnostic questions are documented; the 2006 handout\'s own layout is inferred.'))
reg('transforming-core-beliefs', K_CONCEPT, 400, 258, b, 'Belief worksheet')

# 52. Vortex array -------------------------------------------------------------------------------------------------------------------------------------------------------------------
b = [text(200, 16, 'THE SEDONA VORTEX ARRAY (partial reconstruction)', 'dg-text', size=11.5, weight=700)]
cx, cy = 200, 150
bodies = ['Sun', 'Mercury', 'Venus', 'Earth', 'Moon', 'Mars', 'Ceres', 'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto', 'Sol']
for i, n in enumerate(bodies):
    a = math.radians(-90 + i * 360 / 13); x, y = cx + 92 * math.cos(a), cy + 92 * math.sin(a)
    b.append(circle(x, y, 13, 'dg-line dg-fill')); b.append(text(x, y + 3, n, 'dg-text', size=6.5))
    b.append(line(cx + 30 * math.cos(a), cy + 30 * math.sin(a), x - 13 * math.cos(a), y - 13 * math.sin(a), 'dg-line-2'))
b.append(circle(cx, cy, 28, 'dg-line dg-fill-2')); b.append(text(cx, cy - 2, 'contact', 'dg-text', size=8)); b.append(text(cx, cy + 9, 'symbol', 'dg-text', size=8))
for i in range(5):
    a = math.radians(-90 + i * 72 + 36); x, y = cx + 58 * math.cos(a), cy + 58 * math.sin(a)
    b.append(polygon(regular_polygon(x, y, 8, 5, -90), 'dg-line-2'))
b.append(text(200, 262, 'three layers: 13 celestial-body symbols · hybrid-family energetic symbols · the Bashar contact symbol at centre (not reproduced)', 'dg-text', size=8.5, maxchars=80))
b.append(note(400, 304, 'Element inventory from a fan reconstruction of the 2015 handout; the geometric arrangement is not confirmed.'))
reg('vortex-array', K_CONCEPT, 400, 304, b, 'Vortex array elements')

# 53. Vortex vibrations ---------------------------------------------------------------------------------------------------------------------------------------------------------
b = [text(200, 16, 'VORTEX VIBRATIONS — Earth as a body with energy centres (concept)', 'dg-text', size=10.5, weight=700)]
b.append(circle(200, 150, 92, 'dg-line dg-fill')); b.append(f'<ellipse cx="200" cy="150" rx="92" ry="30" class="dg-line-2"/>'); b.append(f'<ellipse cx="200" cy="150" rx="40" ry="92" class="dg-line-2"/>')
nodes = [(200, 66), (150, 110), (262, 122), (128, 170), (236, 176), (196, 228), (280, 190)]
for i, (x, y) in enumerate(nodes):
    for (x2, y2) in nodes[i + 1:i + 3]: b.append(line(x, y, x2, y2, 'dg-line-2'))
for x, y in nodes: b.append(circle(x, y, 5, 'dg-accent-fill'))
b.append(text(200, 262, 'vortices correspond to and communicate with one another (and with human chakras); focused intention at one feeds the network', 'dg-text', size=8.5, maxchars=80))
reg('vortex-vibrations', K_CONCEPT, 400, 285, b, 'Vortex network concept')

# 54. You are all time travelers ---------------------------------------------------------------------------------------------------------------------------------------------------
b = [text(200, 14, 'YOU ARE ALL TIME TRAVELERS (concept)', 'dg-text', size=12, weight=700)]
b.append(circle(200, 145, 40, 'dg-line dg-fill-2')); b.append(text(200, 142, 'the one', 'dg-text', size=10, weight=600)); b.append(text(200, 156, 'moment', 'dg-text', size=10, weight=600))
for i, (a, lab) in enumerate([(180, '"past" frames'), (0, '"future" frames'), (90, 'here'), (270, 'elsewhere')]):
    ar = math.radians(a); x, y = 200 + 120 * math.cos(ar), 145 + 80 * math.sin(ar)
    b.append(arrow(200 + 42 * math.cos(ar), 145 + 42 * math.sin(ar), x - 8 * math.cos(ar), y - 8 * math.sin(ar), 'dg-line-2', 'dg-arrow-2'))
    for k in range(3): b.append(rect(x - 10 + (k - 1) * 14 * (1 if a in (0, 180) else 0), y - 7 + (k - 1) * 12 * (1 if a in (90, 270) else 0), 12, 9, 'dg-line-2', 1))
    b.append(text(x, y + (30 if a == 90 else -22 if a == 270 else 24), lab, 'dg-muted', size=8.5))
b.append(text(200, 262, '"time is a side effect of consciousness shifting" — travelling = tuning to a different frame', 'dg-text', size=9, maxchars=70))
reg('you-are-all-time-travelers', K_CONCEPT, 400, 285, b, 'Time travel concept')

# 55. Cybo -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
b = [text(200, 16, 'CYBO: LUCKY 13 — the Essassani transformation game', 'dg-text', size=11.5, weight=700)]
b.append(polygon(regular_polygon(120, 130, 46, 10, -90), 'dg-line dg-fill')); b.append(polygon(regular_polygon(120, 130, 26, 5, -90), 'dg-line-2')); b.append(text(120, 135, '12', 'dg-text', size=14, weight=700))
b.append(text(120, 196, '12-sided die (per one session transcript)', 'dg-muted', size=8, maxchars=24))
for i in range(13):
    x = 220 + (i % 7) * 24; y = 100 + (i // 7) * 30
    b.append(rect(x, y, 18, 22, 'dg-line-2 dg-fill-2', 3)); b.append(text(x + 9, y + 15, str(i + 1), 'dg-text', size=8))
b.append(text(292, 178, '13 rounds — "Cybo" is the Sassani word for 13, the vibration of transformation', 'dg-text', size=8.5, maxchars=34))
b.append(note(400, 240, 'Rules were not documented anywhere fetchable; the die and round count come from a transcript digest of the 2016 session.'))
reg('cybo-lucky-13', K_CONCEPT, 400, 240, b, 'Cybo game')

# 56. Contact crystal & crystal techniques --------------------------------------------------------------------------------------------------------------------------------------------------
b = [text(200, 16, 'CRYSTAL TECHNIQUES — the pyramid antenna (the only geometric spec)', 'dg-text', size=10.5, weight=700)]
b.append(polygon([(120, 60), (200, 200), (40, 200)], 'dg-line dg-fill')); b.append(rect(30, 200, 180, 8, 'dg-copper', 0)); b.append(line(120, 40, 120, 200, 'dg-copper')); b.append(polygon([(112, 68), (120, 48), (128, 68)], 'dg-line-2 dg-fill-2'))
b.append(text(120, 232, 'clay pyramid, Giza proportions · copper base plate · copper rod through the apex crystal — "a lens for magnetism"', 'dg-text', size=8.5, maxchars=44))
b.append(circle(300, 110, 30, 'dg-line-2')); b.append(path('M300,80 L300,140', 'dg-line-2')); b.append(text(300, 152, 'stone bell: a crystal slice rung under water above the heart', 'dg-muted', size=8, maxchars=26))
for i, (n, cls) in enumerate([('quartz', 'dg-white'), ('rose', 'dg-rose'), ('amethyst', 'dg-violet'), ('hematite', 'dg-grey')]):
    b.append(circle(250 + i * 32, 200, 8, cls)); b.append(text(250 + i * 32, 218, n, 'dg-muted', size=7.5))
b.append(text(298, 238, 'personal grid, arranged by intuition', 'dg-muted', size=8))
reg('contact-crystal-and-crystal-techniques', K_CONCEPT, 400, 270, b, 'Crystal techniques')
