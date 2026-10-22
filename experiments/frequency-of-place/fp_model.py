# fp_model.py: numbers for the "frequency of a place" experiment (thin hollow copper sphere on a flat table).
#   python3 fp_model.py  -> fp_results.json, fp_series.npz
# Every number used on the page comes from here. Methods are cross-checked against each other (see 'checks').
import json, math, os, sys
import numpy as np
from numpy.polynomial import legendre as L
from scipy.linalg import eigh
from scipy.special import eval_legendre
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sphere_modes import copper, material, exact_modes, ritz_modes, membrane_modes, spheroidal_det, torsional_det, find_roots

HERE = os.path.dirname(os.path.abspath(__file__))
R = {}
g0 = 9.80665; kB = 1.380649e-23; c0 = 299792458.0; mu0 = 4e-7 * math.pi; G_N = 6.674e-11
# ------------------------------------------------------------------------------------------ the sphere
OD = 88.9e-3; h = 1.0e-3                       # Bashar: 3-4 in, "very thin", hollow, as round as possible
Ro = OD / 2; Ri = Ro - h; Rm = Ro - h / 2
m = copper()
mass = 4 / 3 * math.pi * (Ro ** 3 - Ri ** 3) * m['rho']
R['sphere'] = dict(OD_mm=OD * 1e3, wall_mm=h * 1e3, Ro_mm=Ro * 1e3, Ri_mm=Ri * 1e3, mass_g=mass * 1e3,
                   E_GPa=m['E'] / 1e9, G_GPa=m['G'] / 1e9, nu=m['nu'], rho=m['rho'], cL=m['cL'], cT=m['cT'], cP=m['cP'])
FMAX = 60e3
modes = exact_modes(Ri, Ro, m, FMAX, lmax=28, df=2.0)
for d in modes:
    d['label'] = f"{'S' if d['family'] == 'S' else 'T'}{d['l']}" + ('' if d['n'] == 1 else f"({d['n']})")
mem = membrane_modes(Rm, m, 28)
def mem_f(fam, l, branch=None):
    for d in mem:
        if d['family'] == fam and d['l'] == l and (branch is None or d['branch'] == branch): return d['f']
    return None
for d in modes:
    if d['family'] == 'S':
        d['membrane'] = mem_f('S', d['l'], 'lower' if (d['n'] == 1 and d['l'] >= 2) else 'upper')
        d['branch'] = 'lower' if (d['n'] == 1 and d['l'] >= 2) else 'upper'
    else:
        d['membrane'] = mem_f('T', d['l']) if d['n'] == 1 else None
R['modes'] = modes
R['n_modes_below_60k'] = len(modes); R['n_lines_below_60k'] = int(sum(d['deg'] for d in modes))
# ------------------------------------------------------------------------------------------ checks: A vs B, A vs literature
chk = {}
ml = material(1.0, 0.33, 1.0)
lit = {('T', 2): 2.5011, ('S', 2): 2.6497, ('S', 1): 3.5895, ('S', 0): 5.4322, ('T', 1): 5.7635}
k = ml['cT'] / (2 * math.pi); solid = {}
for (fam, l), ref in lit.items():
    fun = (lambda w, l=l: torsional_det(l, w, 0, 1.0, ml)[0]) if fam == 'T' else (lambda w, l=l: spheroidal_det(l, w, 0, 1.0, ml)[0])
    r = find_roots(fun, 0.1 * k, 7 * k, 0.001 * k, 1)[0]
    solid[f'{fam}{l}'] = dict(computed=2 * math.pi * r / ml['cT'], literature=ref)
chk['solid_vs_lobo1995'] = solid
chk['solid_max_rel_dev'] = max(abs(v['computed'] / v['literature'] - 1) for v in solid.values())
ab = []
for d in modes:
    if d['f'] > 45e3 or d['l'] > 8: continue
    fb, _, _ = ritz_modes(Ri, Ro, m, d['l'], d['family'], N=10)
    fb = [x for x in fb if x > 1.0]
    if len(fb) >= d['n']:
        ab.append(dict(label=d['label'], fA=d['f'], fB=fb[d['n'] - 1], rel=fb[d['n'] - 1] / d['f'] - 1))
chk['A_vs_B'] = ab; chk['A_vs_B_max_rel'] = max(abs(x['rel']) for x in ab)
# thin limit: h = 0.1 mm shell vs membrane theory
mt = exact_modes(Ro - 1e-4, Ro, m, 30e3, lmax=4, df=2.0); memt = membrane_modes(Ro - 0.5e-4, m, 4)
thin = []
for d in mt:
    if d['n'] != 1: continue
    br = 'lower' if (d['family'] == 'S' and d['l'] >= 2) else 'upper'
    ref = next((x['f'] for x in memt if x['family'] == d['family'] and x['l'] == d['l'] and (d['family'] == 'T' or x['branch'] == br)), None)
    if ref: thin.append(dict(label=f"{d['family']}{d['l']}", exact=d['f'], membrane=ref, rel=ref / d['f'] - 1))
chk['thin_limit_vs_membrane'] = thin; chk['thin_limit_max_rel'] = max(abs(x['rel']) for x in thin)
R['checks'] = chk
# ------------------------------------------------------------------------------------------ sensitivities (Method A, finite differences)
def f_of(fam, l, n, Ri_, Ro_, mat):
    fun = (lambda w: torsional_det(l, w, Ri_, Ro_, mat)[0]) if fam == 'T' else (lambda w: spheroidal_det(l, w, Ri_, Ro_, mat)[0])
    return find_roots(fun, 2e3, FMAX, 2.0, n)[n - 1]
key_modes = [d for d in modes if d['label'] in ('S2', 'S3', 'S4', 'T2', 'S0', 'S1', 'S2(2)', 'T3')]
sens = {}
for d in key_modes:
    fam, l, n = d['family'], d['l'], d['n']
    f0 = d['f']
    dh = 1e-5
    f_h = f_of(fam, l, n, Ri - dh, Ro, m)                       # thicker wall, same OD
    f_R = f_of(fam, l, n, Ri * 1.001, Ro * 1.001, m)            # 0.1 % larger, same wall ratio
    f_T = f_of(fam, l, n, Ri * (1 + m['alpha']), Ro * (1 + m['alpha']), copper(296.0))
    sens[d['label']] = dict(f=f0, dlnf_dlnh=(f_h / f0 - 1) / (dh / h), dlnf_dlnR=(f_R / f0 - 1) / 0.001,
                            ppm_per_K=(f_T / f0 - 1) * 1e6)
R['sensitivity'] = sens
# ------------------------------------------------------------------------------------------ contact with the table (m = 0 family, all l coupled)
# Hertz contact of the copper surface on granite under the sphere's own weight; shell local stiffness (Reissner) for reference
E_g, nu_g = 50e9, 0.25
Estar = 1 / ((1 - m['nu'] ** 2) / m['E'] + (1 - nu_g ** 2) / E_g)
W = mass * g0
delta = (9 * W ** 2 / (16 * Ro * Estar ** 2)) ** (1 / 3)
a_H = (3 * W * Ro / (4 * Estar)) ** (1 / 3)
k_H = 1.5 * W / delta
k_s = 4 * m['E'] * h ** 2 / (Ro * math.sqrt(3 * (1 - m['nu'] ** 2)))        # Reissner point-load stiffness of the shell
Gstar = 1 / ((2 - m['nu']) / m['G'] + (2 - nu_g) / (E_g / (2 * (1 + nu_g))))
k_t = 8 * Gstar * a_H                                                        # Mindlin tangential contact stiffness (no slip)
R['contact'] = dict(E_star_GPa=Estar / 1e9, weight_N=W, hertz_delta_um=delta * 1e6, hertz_radius_um=a_H * 1e6,
                    k_hertz_N_per_m=k_H, k_reissner_N_per_m=k_s, k_tangential_N_per_m=k_t,
                    bounce_mode_Hz=math.sqrt(1 / (1 / k_H + 1 / k_s) / mass) / (2 * math.pi))

def coupled_m0(k_spring, Lmax=44, N=8):
    """Axisymmetric (m=0) spheroidal family with a radial point spring k at the south pole, all l coupled."""
    blocks = []; sizes = []; vpole = []
    for l in range(0, Lmax + 1):
        f, prof, (K, M, vecs) = ritz_modes(Ri, Ro, m, l, 'S', N=N)
        blocks.append((K, M)); sizes.append(K.shape[0])
        nb = N + 1
        v = np.zeros(K.shape[0])
        # U(Ro) * P_l(cos pi) ; the m=0 member's radial displacement at the pole theta = pi: P_l(-1) = (-1)^l
        for kk in range(nb): v[kk] = L.legval(1.0, [0] * kk + [1]) * ((-1) ** l)
        vpole.append(v)
    n = sum(sizes); Kt = np.zeros((n, n)); Mt = np.zeros((n, n)); V = np.zeros(n); o = 0
    for (K, M), s, v in zip(blocks, sizes, vpole):
        Kt[o:o + s, o:o + s] = K; Mt[o:o + s, o:o + s] = M; V[o:o + s] = v; o += s
    # energies in ritz_modes carry a factor 1/(4 pi) relative to the full 3-D integrals (no phi integral, 1/2 in front):
    # K_3D = 4 pi K, M_3D = 4 pi M... both scaled the same, so add the spring as (1/2 k v v^T) / (2 pi) * ... -> k v v^T / (4 pi) * 1/2 * 2
    # Spring energy 1/2 k u^2 vs strain energy 1/2 u^T K_3D u: with K = K_3D/(4 pi), add k v v^T/(4 pi).
    Kt = Kt + k_spring * np.outer(V, V) / (4 * math.pi)
    vals, vecs = eigh(Kt, Mt)
    vals = np.where(vals < 0, 0, vals)
    return np.sqrt(vals) / (2 * math.pi), vecs, V, Mt

f_free, _, _, _ = coupled_m0(0.0)
f_free = [x for x in f_free if x > 100]
# convergence of the point-spring coupling in the number of coupled l's
_conv = {}
for _L in (24, 34, 44):
    _fc, _, _, _ = coupled_m0(k_H, Lmax=_L); _fc = [x for x in _fc if x > 100]
    _conv[_L] = dict(bounce=_fc[0], S2_m0=_fc[int(np.argmin(np.abs(np.array(_fc) - 9943.4)))])
res_contact = {}
for name, kk in (('hertz', k_H), ('hertz_x0.8', 0.8 * k_H), ('hertz_x1.2', 1.2 * k_H), ('series_hertz_reissner', 1 / (1 / k_H + 1 / k_s))):
    fc, _, _, _ = coupled_m0(kk)
    res_contact[name] = [x for x in fc if x > 100][:14]
R['contact']['m0_free_Hz'] = f_free[:14]
R['contact']['m0_with_spring_Hz'] = res_contact
R['contact']['bounce_mode_coupled_Hz'] = res_contact['hertz'][0]          # rigid-body bounce on the contact, shell compliance included
R['contact']['convergence_in_Lmax'] = _conv
R['contact']['hertz_diameter_um'] = 2 * a_H * 1e6
R['contact']['series_note'] = 'series_hertz_reissner double-counts the shell compliance (already in the Ritz model); kept for reference only'
# |m| = 1 members: tangential (Mindlin) stiffness, first order, relative to the m = 0 radial shift
_s2 = None
# identify shifts of the lowest free m=0 lines (S2 lower at ~9.9 kHz etc.) by nearest matching
def shifts(fc):
    out = []
    for f in f_free[:8]:
        j = int(np.argmin(np.abs(np.array(fc) - f)))
        out.append(dict(free=f, contact=fc[j], rel=fc[j] / f - 1))
    return out
R['contact']['shift_hertz'] = shifts(res_contact['hertz'])
R['contact']['shift_hertz_x0.8'] = shifts(res_contact['hertz_x0.8'])
R['contact']['shift_hertz_x1.2'] = shifts(res_contact['hertz_x1.2'])
# |m| = 1 members via tangential spring, first order (u_theta at the pole): ratio to the m=0 shift = (k_t/k_H) (V/U)^2 l(l+1)/4
_m1 = {}
for fam, l in (('S', 2), ('S', 3), ('S', 4)):
    fB, prof, _ = ritz_modes(Ri, Ro, m, l, 'S', N=10)
    idx = [i for i, x in enumerate(fB) if x > 100][0]
    U, V = prof(idx, np.array([Ro])); ratio = (k_t / k_H) * (float(V[0]) / float(U[0])) ** 2 * l * (l + 1) / 2   # pole amplitude V l(l+1)/2, modal-mass ratio l(l+1)/2
    m0 = R['contact']['shift_hertz'][l - 2]['rel']
    _m1[f'S{l}'] = dict(m0_rel=m0, m1_rel_first_order=m0 * ratio, m1_over_m0=ratio)
R['contact']['m1_members'] = _m1
# ------------------------------------------------------------------------------------------ air loading, Q, ring-down, precision
rho_air, c_air = 1.19, 345.0
f2 = next(d['f'] for d in modes if d['label'] == 'S2')
k_ac = 2 * math.pi * f2 / c_air
ms = m['rho'] * h                                                   # areal mass of the shell
Q_rad = 2 * math.pi * f2 * ms / (rho_air * c_air)                    # radiation-limited Q (plane-wave radiation, kR >> 1)
air_shift_bound = rho_air / (ms * k_ac)                             # |df/f| upper bound from reactive air loading
R['air'] = dict(kR_at_S2=k_ac * Ro, Q_rad_S2=Q_rad, tau_amp_ms=2 * Q_rad / (2 * math.pi * f2) * 1e3,
                reactive_shift_bound=air_shift_bound, ppm_per_K_bound=air_shift_bound * 1e6 / 295,
                ppm_per_kPa_bound=air_shift_bound * 1e6 / 101.3)
# --- air trapped inside the closed shell: rigid-wall cavity modes (zeros of j_l') and their loading of the shell modes
from scipy.special import spherical_jn as _sjn
from scipy.optimize import brentq as _brentq
def cavity_modes(a, c, lmax=8, nmax=3):
    out = []
    for l in range(0, lmax + 1):
        xs = np.linspace(0.3, 40, 8000); v = _sjn(l, xs, derivative=True); roots = []
        for i in range(len(xs) - 1):
            if np.sign(v[i]) != np.sign(v[i + 1]):
                r = _brentq(lambda x: _sjn(l, x, derivative=True), xs[i], xs[i + 1]); 
                if r > 1e-3: roots.append(r)
            if len(roots) >= nmax: break
        for n, x in enumerate(roots, 1):
            out.append(dict(l=l, n=n, x=x, f=x * c / (2 * math.pi * a)))
    return sorted(out, key=lambda d: d['f'])
def interior_shift(fam, l, f, T_air=295.0, P_air=101325.0):
    """First-order shift of a shell mode from the air inside: added mass per area m_add = rho_air j_l(ka)/(k j_l'(ka)),
       weighted by the radial fraction of the mode's kinetic energy. Returns (df/f, m_add/m_s)."""
    if fam != 'S': return 0.0, 0.0
    c = 331.3 * math.sqrt(T_air / 273.15); rho = P_air / (287.05 * T_air)
    k = 2 * math.pi * f / c; x = k * Ri
    m_add = rho * _sjn(l, x) / (k * _sjn(l, x, derivative=True))
    fB, prof, _ = ritz_modes(Ri, Ro, m, l, 'S', N=10)
    idx = [i for i, v in enumerate(fB) if v > 100]
    # match the requested mode by frequency
    j = idx[int(np.argmin([abs(fB[i] - f) for i in idx]))]
    U, V = prof(j, np.array([Ro])); U, V = float(U[0]), float(V[0])
    frac = U ** 2 / (U ** 2 + l * (l + 1) * V ** 2) if l else 1.0
    ratio = m_add / ms
    return -0.5 * ratio * frac, ratio
cav = cavity_modes(Ri, 345.0)
R['interior_air'] = dict(cavity_modes=[d for d in cav if d['f'] < 60e3][:24],
                         vent_hole_helmholtz_Hz=(345.0 / (2 * math.pi)) * math.sqrt((math.pi * 0.5e-3 ** 2) / (4 / 3 * math.pi * Ri ** 3 * (h + 1.7 * 0.5e-3))),
                         sealed_in_vacuum_prestress_MPa=101325 * Rm / (2 * h) / 1e6)
loads = {}
for d in modes:
    if d['f'] > 30e3 or d['family'] != 'S': continue
    s0, r0 = interior_shift('S', d['l'], d['f'])
    s1, _ = interior_shift('S', d['l'], d['f'], 296.0)
    loads[d['label']] = dict(shift_ppm=s0 * 1e6, m_add_over_m_s=r0, ppm_per_K=(s1 - s0) * 1e6, first_order_ok=abs(r0) < 0.1)
R['interior_air']['shifts'] = loads
_big = {k: v for k, v in loads.items() if abs(v['shift_ppm']) > 100}
R['interior_air']['note'] = 'first-order; lines with |m_add| > 0.1 m_s sit near a cavity resonance and need a coupled solve; a 1 mm vent hole lets the bell jar evacuate the interior'
# Cramer-Rao bound on the frequency of a decaying sinusoid: use the record length ~ tau_amp with SNR at start
def crb_sigma_f(T, fs, snr_db):
    N = T * fs; snr = 10 ** (snr_db / 10)
    return math.sqrt(6 / ((2 * math.pi) ** 2 * snr * N * T ** 2))
tau = 2 * Q_rad / (2 * math.pi * f2)
R['precision'] = {f'sigma_f_Hz_snr{s}dB': crb_sigma_f(tau, 204800, s) for s in (40, 60)}
R['precision']['ppm_snr40'] = R['precision']['sigma_f_Hz_snr40dB'] / f2 * 1e6
R['precision']['record_s'] = tau; R['precision']['fs'] = 204800
R['precision']['note'] = 'constant-amplitude CRB; a decaying record is 2-3x looser'
# two-family thermometry: T2 and S0 have different ppm/K, so their ratio reads the ball's temperature
R['precision']['thermometry_ppm_per_K'] = sens['T2']['ppm_per_K'] - sens['S0']['ppm_per_K']
# ------------------------------------------------------------------------------------------ location effects (A vs B, 2.4 m apart)
Lx = 2.4
g_grad_vert = 3.086e-6                                             # m/s^2 per m (free-air)
redshift_per_m = g0 / c0 ** 2
# a 1000 kg object 2 m from A and 4.4 m from B: horizontal delta g
dg = G_N * 1000 / 2.0 ** 2 - G_N * 1000 / 4.4 ** 2
prestress_rel = m['rho'] * g0 * Ro / m['E']
gyro63, gyro65 = 11.289e6, 12.093e6                                 # Hz/T
B_earth = 50e-6; dB_room = 1e-6
skin = lambda f: math.sqrt(2 * 1.68e-8 / (2 * math.pi * f * mu0))
R['location_effects'] = {
    'temperature_ppm_per_K': -200.0,
    'temperature_note': 'measured ppm/K from the model: see sensitivity; a 0.5 K end-to-end gradient = 100 ppm',
    'contact_variation_ppm': abs(R['contact']['shift_hertz_x1.2'][0]['rel'] - R['contact']['shift_hertz_x0.8'][0]['rel']) * 1e6,
    'air_density_ppm_per_K_bound': R['air']['ppm_per_K_bound'], 'air_density_ppm_per_kPa_bound': R['air']['ppm_per_kPa_bound'],
    'doppler_ppm_at_0p05_m_per_s': 0.05 / c_air * 1e6,
    'gravity_delta_g_rel_1t_mass': dg / g0, 'gravity_prestress_rel': prestress_rel, 'gravity_freq_rel': prestress_rel * dg / g0,
    'redshift_rel_per_m_height': redshift_per_m, 'redshift_rel_1mm': redshift_per_m * 1e-3,
    'nmr_63Cu_Hz_in_50uT': gyro63 * B_earth, 'nmr_65Cu_Hz_in_50uT': gyro65 * B_earth, 'nmr_shift_Hz_per_uT': gyro63 * 1e-6,
    'nmr_room_variation_Hz': gyro63 * dB_room, 'skin_depth_mm_at_564Hz': skin(gyro63 * B_earth) * 1e3,
    'eddy_damping_rate_per_s': 5.96e7 * B_earth ** 2 / m['rho'],
    'measurement_floor_ppm_after_T_correction_10mK': 2.0,
}
# EM cavity modes of the hollow interior
R['em_cavity'] = dict(TM101_GHz=2.7437 * c0 / (2 * math.pi * Ri) / 1e9, TE101_GHz=4.4934 * c0 / (2 * math.pi * Ri) / 1e9,
                      skin_depth_um_3GHz=skin(3.0e9) * 1e6, Q_order=Ri / skin(3.0e9))
R['thermal'] = dict(wien_peak_um=2.898e-3 / 295 * 1e6, peak_THz=c0 / (2.898e-3 / 295) / 1e12)
# ------------------------------------------------------------------------------------------ the table: granite plate, free-free Kirchhoff, Rayleigh-Ritz
def plate_modes(a, b, hp, E, nu, rho, N=9, nmodes=12):
    D = E * hp ** 3 / (12 * (1 - nu ** 2)); rh = rho * hp
    xq, wq = L.leggauss(24)
    # basis: Legendre products P_i(xi) P_j(eta), xi,eta in [-1,1]; x = a xi/2, y = b eta/2
    P = np.array([L.legval(xq, [0] * i + [1]) for i in range(N + 1)])
    dP = np.array([L.legval(xq, L.legder([0] * i + [1])) for i in range(N + 1)]) * (2 / a)
    d2P = np.array([L.legval(xq, L.legder([0] * i + [1], 2)) for i in range(N + 1)]) * (2 / a) ** 2
    Q = P; dQ = dP * (a / b); d2Q = d2P * (a / b) ** 2
    idx = [(i, j) for i in range(N + 1) for j in range(N + 1)]; n = len(idx)
    K = np.zeros((n, n)); M = np.zeros((n, n))
    wxy = np.outer(wq, wq) * (a / 2) * (b / 2)
    Wxx = [np.outer(d2P[i], Q[j]) for (i, j) in idx]; Wyy = [np.outer(P[i], d2Q[j]) for (i, j) in idx]
    Wxy = [np.outer(dP[i], dQ[j]) for (i, j) in idx]; Wv = [np.outer(P[i], Q[j]) for (i, j) in idx]
    for p in range(n):
        for q in range(p, n):
            kk = D * np.sum(wxy * (Wxx[p] * Wxx[q] + Wyy[p] * Wyy[q] + nu * (Wxx[p] * Wyy[q] + Wyy[p] * Wxx[q]) + 2 * (1 - nu) * Wxy[p] * Wxy[q]))
            mm = rh * np.sum(wxy * Wv[p] * Wv[q])
            K[p, q] = K[q, p] = kk; M[p, q] = M[q, p] = mm
    vals, vecs = eigh(K, M)
    f = np.sqrt(np.clip(vals, 0, None)) / (2 * math.pi)
    def shape(k, x, y):
        xi, eta = 2 * x / a, 2 * y / b; v = vecs[:, k]; w = 0
        for c, (i, j) in zip(v, idx):
            w = w + c * L.legval(xi, [0] * i + [1]) * L.legval(eta, [0] * j + [1])
        return w
    # modal mass normalisation: vecs are M-orthonormal (eigh) -> phi^T M phi = 1 => modal mass 1 kg with phi in these units
    return f, shape, vecs, M
# validation: square free plate, nu = 0.3 -> Leissa lambda = omega a^2 sqrt(rho h / D): 13.468, 19.596, 24.270, 34.801
fsq, _, _, _ = plate_modes(1.0, 1.0, 0.01, 1.0, 0.3, 1.0, N=9)
Dsq = 1.0 * 0.01 ** 3 / (12 * (1 - 0.09)); lam_sq = [2 * math.pi * f * 1.0 * math.sqrt(1.0 * 0.01 / Dsq) for f in fsq if f > 1e-3][:5]
R['table'] = dict(a_m=2.4, b_m=1.2, thickness_m=0.25, E_GPa=50, nu=0.25, rho=2700, mass_kg=2.4 * 1.2 * 0.25 * 2700,
                  leissa_check=dict(computed=lam_sq[:4], literature=[13.468, 19.596, 24.270, 34.801]))
ft, shape, vecs, Mt = plate_modes(2.4, 1.2, 0.25, 50e9, 0.25, 2700, N=9)
elastic = [(k, f) for k, f in enumerate(ft) if f > 1.0][:10]
A_pt = (-0.8, 0.0); B_pt = (0.8, 0.0); C_pt = (0.6, 0.4)
tab_modes = []
for k, f in elastic:
    phiA, phiB, phiC = shape(k, *A_pt), shape(k, *B_pt), shape(k, *C_pt)
    # mass loading by the sphere (point mass) at A: df/f = -1/2 m phi^2 / modal mass (modal mass = 1 with M-orthonormal vecs)
    tab_modes.append(dict(f=f, phiA2=phiA ** 2, phiB2=phiB ** 2, phiC2=phiC ** 2,
                          shift_ppm_A=-0.5 * mass * phiA ** 2 * 1e6, shift_ppm_B=-0.5 * mass * phiB ** 2 * 1e6, shift_ppm_C=-0.5 * mass * phiC ** 2 * 1e6))
R['table']['modes'] = tab_modes
R['table']['note'] = 'Kirchhoff thin-plate, free edges; h/a = 0.10 so shear deformation lowers the real values by a few %; A=(-0.8,0), B=(0.8,0), C=(0.6,0.4) m from the centre; point-mass shifts valid only well below the ~700 Hz bounce mode'
# driving-point FRF magnitudes at A, B, C (accelerance), 1 % modal damping
fr = np.linspace(20, 600, 1200); eta_d = 0.01
def frf(pt):
    H = np.zeros_like(fr, dtype=complex)
    for k, f in elastic:
        ph = shape(k, *pt); w0 = 2 * math.pi * f; w = 2 * math.pi * fr
        H += ph ** 2 * (-w ** 2) / (w0 ** 2 - w ** 2 + 1j * eta_d * w0 ** 2)
    return np.abs(H)
HA, HB, HC = frf(A_pt), frf(B_pt), frf(C_pt)
# ------------------------------------------------------------------------------------------ stage 2: forces that can move the ball
C_rr = 1.5e-3                                                  # rolling-resistance coefficient, hard metal on hard flat (order 1e-3)
F_roll = C_rr * W
slope_threshold = C_rr                                          # tan(theta) to start rolling
def rad_force(spl_db):
    p = 2e-5 * 10 ** (spl_db / 20); I = p ** 2 / (rho_air * c_air)
    return (I / c_air) * math.pi * Ro ** 2                      # large sphere (ka >> 1) in a travelling wave: ~I/c x cross-section
B0 = 1e-3                                                       # coil field at the ball, 1 mT rms
F_eddy = (B0 ** 2 / (2 * mu0)) * math.pi * Ro ** 2             # order-of-magnitude eddy-current repulsion (f >> skin cutoff)
# eddy-current heating of the shell by the 1 mT drive: sheet-conductor estimate P ~ 1/2 * K^2 * R_s * area, K = B0/mu0 surface current
_Rs = math.sqrt(math.pi * 10e3 * mu0 * 1.68e-8)                    # surface resistance at 10 kHz (skin depth 0.65 mm < wall)
_P_eddy = 0.5 * (B0 / mu0) ** 2 * _Rs * 2 * math.pi * Ro ** 2       # roughly half the surface sees the field
_dTdt = _P_eddy / (mass * 385.0)
R['stage2'] = dict(eddy_heating_W=_P_eddy, eddy_dT_per_10min_K=_dTdt * 600, C_rr=C_rr, F_roll_mN=F_roll * 1e3, slope_threshold_mrad=slope_threshold * 1e3, level_resolution_urad=1.0,
                   plate_flatness_um=12.7, F_acoustic_120dB_uN=rad_force(120) * 1e6, F_acoustic_140dB_mN=rad_force(140) * 1e3,
                   spl_for_rolling_dB=20 * math.log10(math.sqrt(F_roll / (math.pi * Ro ** 2) * rho_air * c_air ** 2) / 2e-5),
                   F_eddy_1mT_mN=F_eddy * 1e3, displacement_resolution_um=1.0, seismic_walk_note='vibration-induced creep must be measured with the drive off')
# surface amplitudes of the key modes for the mode-shape figure
_ms = {}
for fam, l, n in (('S', 2, 1), ('S', 3, 1), ('S', 4, 1), ('S', 5, 1), ('S', 0, 1), ('S', 1, 1), ('S', 2, 2), ('T', 2, 1), ('T', 3, 1)):
    fB, prof, _ = ritz_modes(Ri, Ro, m, l, fam, N=10)
    idx = [i for i, x in enumerate(fB) if x > 100][n - 1]
    key = f'{fam}{l}' + ('' if n == 1 else f'({n})')
    if fam == 'S':
        U, V = prof(idx, np.array([Ro])); _ms[key] = dict(f=float(fB[idx]), V_over_U=(float(V[0]) / float(U[0])) if float(U[0]) else None)
    else:
        _ms[key] = dict(f=float(fB[idx]))
R['mode_shapes_surface'] = _ms
# ------------------------------------------------------------------------------------------ save
def conv(o):
    if isinstance(o, (np.floating,)): return float(o)
    if isinstance(o, (np.integer,)): return int(o)
    if isinstance(o, (np.bool_,)): return bool(o)
    if isinstance(o, np.ndarray): return o.tolist()
    raise TypeError(str(type(o)))
OUTD = os.environ.get('FP_OUT', HERE)
json.dump(R, open(f'{OUTD}/fp_results.json', 'w'), indent=1, default=conv)
# plate mode shapes on a grid for the figures
xs = np.linspace(-1.2, 1.2, 97); ys = np.linspace(-0.6, 0.6, 49)
X, Y = np.meshgrid(xs, ys)
shapes = np.array([[[shape(k, x, y) for x in xs] for y in ys] for k, f in elastic[:6]])
np.savez_compressed(f'{OUTD}/fp_series.npz', fr=fr, HA=HA, HB=HB, HC=HC, xs=xs, ys=ys, shapes=shapes)
print('modes below 60 kHz:', len(modes), 'lines:', R['n_lines_below_60k'])
for d in modes[:30]:
    print(f"{d['label']:7s} {d['f']:9.1f} Hz  x{d['deg']}  membrane {d.get('membrane') or 0:9.1f}")
print('checks:', json.dumps({k: v for k, v in chk.items() if 'max' in k}, indent=1))
print('sensitivity:', json.dumps(sens, indent=1))
print('contact:', json.dumps({k: v for k, v in R['contact'].items() if not k.startswith('m0')}, indent=1))
print('contact shifts:', json.dumps(R['contact']['shift_hertz'][:4], indent=1))
print('air:', R['air']); print('precision:', R['precision'])
print('table check:', R['table']['leissa_check']); print('table modes:', json.dumps(tab_modes[:6], indent=1))
print('stage2:', R['stage2']); print('location:', json.dumps(R['location_effects'], indent=1))
