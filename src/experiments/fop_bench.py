# fop_bench.py: the "frequency of a place" bench: granite surface plate, thin copper sphere at A, marked spot B,
# a laser vibrometer and striker/EMAT/microphone station at each end, location sensors, hammer and accelerometers,
# DAQ and laptop on a side bench.  venv/bin/python fop_bench.py [view] [WxH] [spp]
import sys, os, json, math, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector, Matrix
import rs_scene as S
import bench as B

OUT = '/home/claude/sphere/renders'; TEX = '/home/claude/sphere/tex'
PL = dict(a=2.4, b=1.2, t=0.25, z=0.0)                     # plate top at z = 0
A = Vector((-0.8, 0.0, 0.0)); Bp = Vector((0.8, 0.0, 0.0)); Cp = Vector((0.9, 0.45, 0.0))
RB = 0.04445

def granite_mat():
    m = S.mat_basic('granite', (0.22, 0.21, 0.22), 0.0, 0.38)
    nt = m.node_tree; b = S._p(m)
    tex = nt.nodes.new('ShaderNodeTexNoise'); tex.inputs['Scale'].default_value = 900.0; tex.inputs['Detail'].default_value = 8; tex.inputs['Roughness'].default_value = 0.7
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = 0.35; ramp.color_ramp.elements[0].color = (0.035, 0.035, 0.04, 1)
    ramp.color_ramp.elements[1].position = 0.70; ramp.color_ramp.elements[1].color = (0.20, 0.19, 0.20, 1)
    nt.links.new(tex.outputs['Fac'], ramp.inputs['Fac']); nt.links.new(ramp.outputs['Color'], b.inputs['Base Color'])
    tex2 = nt.nodes.new('ShaderNodeTexNoise'); tex2.inputs['Scale'].default_value = 400.0
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = 0.30; mr.inputs['To Max'].default_value = 0.48
    nt.links.new(tex2.outputs['Fac'], mr.inputs['Value']); nt.links.new(mr.outputs['Result'], b.inputs['Roughness'])
    return m

def post(name, loc, h, r, mat):
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=r, depth=h, location=(loc[0], loc[1], loc[2] + h / 2))
    ob = bpy.context.active_object; ob.name = name; ob.data.materials.append(mat); return ob

def tripod(name, loc, h, M):
    for k in range(3):
        a = math.radians(90 + k * 120)
        foot = Vector((loc[0] + 0.14 * math.cos(a), loc[1] + 0.14 * math.sin(a), loc[2]))
        top = Vector((loc[0], loc[1], loc[2] + h - 0.05))
        B.wire(name + '_leg', [foot, top], M['dark'], r=0.006)
    post(name + '_col', (loc[0], loc[1], loc[2] + h - 0.08), 0.12, 0.012, M['alu'])

def station(M, P, side, labels):
    d = 1 if side > 0 else -1
    z0 = PL['z']
    # laser vibrometer head on a tripod, 0.45 m from the ball, looking at its equator
    hp = P + Vector((0, -0.92, 0))                           # outside the plate (plate edge at y = -0.6), on the floor
    tripod('ldv_tripod', (hp.x, hp.y, z0 - PL['t'] - 0.76), 0.76 + PL['t'] + RB - 0.04, M)
    body = B.box('ldv_head', (hp.x, hp.y, z0 + RB), (0.09, 0.19, 0.08), M['dark'], 0.004)
    lens = S.spin_mesh('ldv_lens', [(0.0005, 0.0), (0.016, 0.0), (0.016, 0.02), (0.012, 0.02), (0.012, 0.024), (0.0005, 0.024)], 32, M['nickel'])
    lens.matrix_world = Matrix.Translation((hp.x, hp.y + 0.095, z0 + RB)) @ S.look_matrix(Vector((0, 1, 0)))
    glass = S.mat_basic('glass', (0.6, 0.7, 0.75), 0.0, 0.05, **{'Transmission Weight': 0.9})
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.011, depth=0.002, location=(hp.x, hp.y + 0.119, z0 + RB), rotation=(math.pi / 2, 0, 0))
    bpy.context.active_object.data.materials.append(glass)
    # beam (thin emissive line) from the lens to the ball
    beam = S.mat_emit('beam', (1.0, 0.15, 0.1), 18.0)
    B.wire('ldv_beam', [Vector((hp.x, hp.y + 0.12, z0 + RB)), Vector((P.x, P.y - RB - 0.002, z0 + RB))], beam, r=0.0006)
    labels['ldv' + ('A' if d < 0 else 'B')] = (hp.x, hp.y - 0.05, z0 + RB + 0.05)
    # striker (solenoid on a small stand) at 45 deg behind-right, EMAT coil opposite
    sp = P + Vector((d * 0.17, 0.17, 0))
    post('striker_post', (sp.x, sp.y, z0), 0.03, 0.012, M['alu'])
    sol = B.box('striker', (sp.x, sp.y, z0 + RB), (0.03, 0.03, 0.06), M['dark'], 0.003)
    pin = B.wire('striker_pin', [Vector((sp.x, sp.y, z0 + RB)), P + (sp - P).normalized() * (RB + 0.012) + Vector((0, 0, RB))], M['nickel'], r=0.003)
    labels['striker' + ('A' if d < 0 else 'B')] = (sp.x, sp.y, z0 + RB + 0.04)
    ep = P + Vector((-d * 0.17, 0.17, 0))
    post('emat_post', (ep.x, ep.y, z0), 0.03, 0.012, M['alu'])
    bpy.ops.mesh.primitive_torus_add(major_radius=0.022, minor_radius=0.006, location=(ep.x, ep.y, z0 + RB), rotation=(0, math.pi / 2, math.radians(45 if d < 0 else -45)))
    coil = bpy.context.active_object; coil.data.materials.append(M['cu_rod'])
    B.box('emat_mag', (ep.x, ep.y, z0 + RB), (0.03, 0.012, 0.03), M['dark'], 0.002)
    labels['emat' + ('A' if d < 0 else 'B')] = (ep.x, ep.y, z0 + RB + 0.035)
    # measurement microphone on a thin stand
    mp = P + Vector((-d * 0.22, -0.16, 0))
    post('mic_stand', (mp.x, mp.y, z0), 0.10, 0.004, M['alu'])
    post('mic', (mp.x, mp.y, z0 + 0.10), 0.05, 0.007, M['nickel'])
    labels['mic' + ('A' if d < 0 else 'B')] = (mp.x, mp.y, z0 + 0.16)
    # location sensor cluster: small box with a PT100 lead, fluxgate, seismic accelerometer
    cp = P + Vector((d * 0.30, -0.05, 0))
    B.box('sensors', (cp.x, cp.y, z0 + 0.02), (0.08, 0.06, 0.04), M['dark'], 0.003)
    B.box('fluxgate', (cp.x + d * 0.07, cp.y, z0 + 0.012), (0.02, 0.02, 0.024), M['alu'], 0.002)
    B.box('seis', (cp.x, cp.y - 0.06, z0 + 0.012), (0.03, 0.03, 0.024), M['nickel'], 0.002)
    labels['sensors' + ('A' if d < 0 else 'B')] = (cp.x, cp.y, z0 + 0.05)
    # table accelerometer (small cube) near the ball
    ap = P + Vector((d * 0.10, 0.08, 0))
    B.box('accel', (ap.x, ap.y, z0 + 0.006), (0.012, 0.012, 0.012), M['nickel'], 0.001)
    B.wire('accel_cable', [Vector((ap.x, ap.y + 0.006, z0 + 0.006)), Vector((ap.x + d * 0.05, ap.y + 0.25, z0 + 0.003)), Vector((ap.x + d * 0.1, PL['b'] / 2 + 0.05, z0 - 0.1))], M['rubber'], r=0.0012)

def build(M):
    gran = granite_mat()
    # plate
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, PL['z'] - PL['t'] / 2))
    plate = bpy.context.active_object; plate.name = 'plate'; plate.scale = (PL['a'], PL['b'], PL['t'])
    plate.data.materials.append(gran); bv = plate.modifiers.new('bev', 'BEVEL'); bv.width = 0.004; bv.segments = 3
    # steel stand: three legs on a frame
    steel = S.mat_basic('steel_paint', (0.18, 0.19, 0.21), 0.3, 0.5)
    for (x, y) in ((-0.95, -0.35), (-0.95, 0.35), (0.95, 0.0)):
        B.box('leg', (x, y, PL['z'] - PL['t'] - 0.37), (0.08, 0.08, 0.74), steel, 0.003)
        B.box('foot', (x, y, PL['z'] - PL['t'] - 0.75), (0.16, 0.16, 0.02), M['dark'], 0.002)
    B.box('frame_x', (0, 0, PL['z'] - PL['t'] - 0.05), (2.1, 0.08, 0.08), steel, 0.003)
    B.box('frame_y', (-0.95, 0, PL['z'] - PL['t'] - 0.05), (0.08, 0.78, 0.08), steel, 0.003)
    # floor
    floor = S.mat_basic('lab_floor', (0.16, 0.16, 0.155), 0.0, 0.7)
    bpy.ops.mesh.primitive_plane_add(size=14, location=(0, 0, PL['z'] - PL['t'] - 0.76))
    bpy.context.active_object.data.materials.append(floor)
    # the sphere at A: thin copper shell (rendered as a copper sphere)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=48, radius=RB, location=(A.x, A.y, PL['z'] + RB))
    ball = bpy.context.active_object; ball.name = 'ball'; ball.data.materials.append(M['cu']); ball.data.shade_smooth()
    # seam line (two spun hemispheres soldered at the equator) as a thin torus
    bpy.ops.mesh.primitive_torus_add(major_radius=RB, minor_radius=0.0004, major_segments=128, minor_segments=8, location=(A.x, A.y, PL['z'] + RB))
    bpy.context.active_object.data.materials.append(M['nickel'])
    # spot B: a thin ring of white tape on the plate + 'B' marker; spot C small ring
    tape = S.mat_basic('tape', (0.92, 0.92, 0.88), 0.0, 0.7)
    for (P, r) in ((Bp, RB + 0.01), (Cp, 0.025)):
        bpy.ops.mesh.primitive_torus_add(major_radius=r, minor_radius=0.0025, major_segments=96, minor_segments=6, location=(P.x, P.y, PL['z'] + 0.0012))
        bpy.context.active_object.data.materials.append(tape)
    # the two stations
    labels = {}
    station(M, A, -1, labels); station(M, Bp, +1, labels)
    # modal hammer lying on the plate near C, accelerometer at C
    hp = Cp + Vector((-0.25, 0.1, 0))
    B.wire('hammer_handle', [Vector((hp.x, hp.y, PL['z'] + 0.012)), Vector((hp.x + 0.26, hp.y - 0.05, PL['z'] + 0.012))], M['dark'], r=0.011)
    B.box('hammer_head', (hp.x + 0.29, hp.y - 0.055, PL['z'] + 0.015), (0.05, 0.022, 0.03), M['nickel'], 0.003)
    B.box('accelC', (Cp.x, Cp.y, PL['z'] + 0.006), (0.012, 0.012, 0.012), M['nickel'], 0.001)
    # electronic level on the plate
    B.box('level', (0.0, -0.42, PL['z'] + 0.03), (0.16, 0.05, 0.06), M['alu'], 0.003)
    lvl = S.mat_image('level_scr', f'{TEX}/level_scr.png', emit=1.2, rough=0.2)
    B.plane('level_screen', (0.0, -0.4455, PL['z'] + 0.038), 0.10, 0.03, (0, -1, 0), lvl)
    # side bench with DAQ chassis and laptop (behind, +y side)
    B.box('side_bench', (0.0, 1.05, PL['z'] - 0.10), (1.6, 0.6, 0.04), M['bench'], 0.003)
    for (x, y) in ((-0.7, 0.8), (0.7, 0.8), (-0.7, 1.3), (0.7, 1.3)):
        post('bench_leg', (x, y, PL['z'] - PL['t'] - 0.76), 0.64, 0.02, steel)
    daq = B.instrument('daq', (-0.45, 0.85, PL['z'] - 0.08 + 0.09), (0.44, 0.30, 0.18), f'{TEX}/daq.png', M)
    lap = S.mat_basic('laptop', (0.30, 0.31, 0.33), 0.6, 0.35)
    B.box('lap_base', (0.35, 0.95, PL['z'] - 0.08 + 0.009), (0.34, 0.24, 0.018), lap, 0.004)
    lm = S.mat_image('lap_scr', f'{TEX}/fop_laptop.png', emit=1.4, rough=0.1)
    ang = math.radians(105); hc = Vector((0.35, 0.95 + 0.12, PL['z'] - 0.08 + 0.019)); up = Vector((0, -math.cos(ang), math.sin(ang))); lid_c = hc + up * 0.11
    B.box('lap_lid', lid_c + Vector((0, 0.004 * math.sin(ang), 0.004 * math.cos(ang))), (0.34, 0.006, 0.22), lap, 0.003).rotation_euler = (-(ang - math.pi / 2), 0, 0)
    B.plane('lap_screen', lid_c - Vector((0, 0.0008 * math.sin(ang), -0.0008 * math.cos(ang))) + Vector((0, -0.003, 0)), 0.31, 0.195, (0, -math.sin(ang), -math.cos(ang)), lm, up=tuple(up))
    labels.update(dict(ball=(A.x, A.y, PL['z'] + RB), spotB=(Bp.x, Bp.y, PL['z']), spotC=(Cp.x, Cp.y, PL['z']), hammer=(hp.x + 0.15, hp.y, PL['z'] + 0.02),
                       level=(0.0, -0.42, PL['z'] + 0.06), daq=(-0.45, 0.85, PL['z'] + 0.05), laptop=(0.35, 0.95, PL['z'] + 0.08), plate=(0.0, -0.6, PL['z'])))
    # lights: big soft key from above-left, fill from right, rim behind
    def area(name, loc, target, size, color, energy, size_y=None):
        ld = bpy.data.lights.new(name, 'AREA'); ld.shape = 'RECTANGLE'; ld.size = size; ld.size_y = size_y or size; ld.color = color; ld.energy = energy
        ob = bpy.data.objects.new(name, ld); S.link(ob); ob.location = loc
        ob.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    area('key', (-2.0, -2.2, 2.6), (0, 0, 0), 2.2, (1.0, 0.86, 0.72), 420, 1.4)
    area('fill', (2.6, -1.6, 1.4), (0.5, 0, 0), 2.0, (0.86, 0.90, 1.0), 140, 1.0)
    area('rim', (0.5, 2.6, 2.0), (0, 0, 0), 0.5, (0.7, 0.75, 1.0), 260, 2.4)
    area('top', (0, 0, 3.2), (0, 0, 0), 2.6, (1.0, 0.95, 0.9), 150)
    w = bpy.data.worlds.new('world'); bpy.context.scene.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs[0].default_value = (0.012, 0.013, 0.016, 1)
    return labels

VIEWS = {'wide': dict(az=-118, el=24, dist=4.3, target=(0.0, 0.05, 0.05), lens=35),
         'stationA': dict(az=-125, el=22, dist=1.35, target=(-0.75, 0.0, 0.05), lens=45)}

if __name__ == '__main__':
    view = sys.argv[1] if len(sys.argv) > 1 else 'wide'
    res = tuple(int(x) for x in (sys.argv[2] if len(sys.argv) > 2 else '960x540').split('x'))
    spp = int(sys.argv[3]) if len(sys.argv) > 3 else 16
    t0 = time.time(); S.reset(); M = S.materials()
    labels = build(M)
    v = VIEWS[view]
    S.orbit_cam(v['az'], v['el'], v['dist'], target=Vector(v['target']), lens=v['lens'])
    bpy.context.view_layer.update()
    bpy.context.scene.render.resolution_x, bpy.context.scene.render.resolution_y = res
    path = f'{OUT}/fop_{view}_{res[0]}.png'
    keys = list(labels.keys()); pts = S.project([labels[k] for k in keys])
    json.dump({k: p[:2] for k, p in zip(keys, pts)}, open(path.replace('.png', '_anchors.json'), 'w'), indent=1)
    if os.environ.get('ANCHORS_ONLY'): print('anchors only'); raise SystemExit
    S.render(path, res, spp)
    print(f'[fop {view}] {res} {spp}spp in {time.time() - t0:.1f}s -> {path}')
