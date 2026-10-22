# sphere_modes.py: free vibration of a hollow (or solid) isotropic elastic sphere, three independent ways.
#   Method A: exact 3-D elastodynamics (Lamb 1882 extended to two traction-free surfaces): spherical Bessel
#             determinants, spheroidal (4x4, l>=1; 2x2, l=0) and torsional (2x2).
#   Method B: Rayleigh-Ritz on the 3-D strain energy, one angular order l at a time, radial Legendre basis,
#             angular integrals by Gauss-Legendre. Shares only Hooke's law and the strain definitions with A.
#   Method C: thin-shell membrane theory (Baker 1961) and Lamb's thin-shell torsional law, as the h -> 0 limit.
# All frequencies in Hz. Units SI.
import math
import numpy as np
from numpy.polynomial import legendre as L
from scipy.special import spherical_jn as sjn, spherical_yn as syn, eval_legendre
from scipy.optimize import brentq
from scipy.linalg import eigh

# ------------------------------------------------------------------------------------------ material
def copper(T_K=295.0):
    """OFE copper, polycrystal (Hill average of Ledbetter & Naimon 1974 single-crystal constants at 295 K).
       Temperature dependence of the moduli from Overton & Gaffney 1955 (dC44/dT = -29.1 MPa/K,
       dC11/dT = -37.8 MPa/K, dC12/dT = -16.3 MPa/K) and thermal expansion 16.5e-6/K."""
    dT = T_K - 295.0
    C11 = 169.1e9 - 37.8e6 * dT; C12 = 122.2e9 - 16.3e6 * dT; C44 = 75.42e9 - 29.1e6 * dT
    alpha = 16.5e-6
    rho = 8930.0 / (1 + 3 * alpha * dT)
    K = (C11 + 2 * C12) / 3
    GV = (C11 - C12 + 3 * C44) / 5
    GR = 5 * (C11 - C12) * C44 / (4 * C44 + 3 * (C11 - C12))
    G = 0.5 * (GV + GR)
    E = 9 * K * G / (3 * K + G); nu = (3 * K - 2 * G) / (2 * (3 * K + G))
    lam = K - 2 * G / 3
    return dict(C11=C11, C12=C12, C44=C44, K=K, G=G, E=E, nu=nu, lam=lam, mu=G, rho=rho,
                cL=math.sqrt((lam + 2 * G) / rho), cT=math.sqrt(G / rho), cP=math.sqrt(E / (rho * (1 - nu ** 2))),
                alpha=alpha, T=T_K)

def material(E, nu, rho):
    G = E / (2 * (1 + nu)); lam = E * nu / ((1 + nu) * (1 - 2 * nu)); K = lam + 2 * G / 3
    return dict(E=E, nu=nu, rho=rho, G=G, mu=G, lam=lam, K=K, cL=math.sqrt((lam + 2 * G) / rho), cT=math.sqrt(G / rho),
                cP=math.sqrt(E / (rho * (1 - nu ** 2))))

# ------------------------------------------------------------------------------------------ Method A
def _R(kind, l, x, d=0):
    f = sjn if kind == 'j' else syn
    if d == 0: return f(l, x)
    if d == 1: return f(l, x, derivative=True)
    # second derivative from the spherical Bessel equation
    return -(2 / x) * f(l, x, derivative=True) - (1 - l * (l + 1) / x ** 2) * f(l, x)

def _spheroidal_rows(l, w, r, m, kinds=('j', 'y')):
    """Rows [sigma_rr, sigma_rtheta] (coefficients of Y and dY/dtheta) at radius r for the columns
       (P_j, P_y, N_j, N_y) [l>=1] or (P_j, P_y) [l=0]."""
    kL, kT = w / m['cL'], w / m['cT']; lam, mu = m['lam'], m['mu']; Ll = l * (l + 1)
    cols = []
    for kind in kinds:                                   # P-type: u = grad(R(kL r) Y)
        x = kL * r
        U = kL * _R(kind, l, x, 1); Up = kL ** 2 * _R(kind, l, x, 2)
        V = _R(kind, l, x) / r; Vp = kL * _R(kind, l, x, 1) / r - _R(kind, l, x) / r ** 2
        cols.append((U, Up, V, Vp))
    if l >= 1:
        for kind in kinds:                               # N-type: u = curl curl (r R(kT r) Y)
            x = kT * r
            R0, R1, R2 = _R(kind, l, x), _R(kind, l, x, 1), _R(kind, l, x, 2)
            U = Ll * R0 / r; Up = Ll * (kT * R1 / r - R0 / r ** 2)
            V = R0 / r + kT * R1; Vp = kT * R1 / r - R0 / r ** 2 + kT ** 2 * R2
            cols.append((U, Up, V, Vp))
    srr = [(lam + 2 * mu) * Up + lam * (2 * U - Ll * V) / r for (U, Up, V, Vp) in cols]
    srt = [mu * (Vp - V / r + U / r) for (U, Up, V, Vp) in cols]
    return srr, srt

def spheroidal_det(l, w, Ri, Ro, m):
    solid = Ri <= 0
    kinds = ('j',) if solid else ('j', 'y')
    rows = []
    for r in ((Ro,) if solid else (Ri, Ro)):
        srr, srt = _spheroidal_rows(l, w, r, m, kinds)
        rows.append(srr)
        if l >= 1: rows.append(srt)
    A = np.array(rows, dtype=float)                      # (nrows, ncols[, nw])
    if A.ndim == 3: A = np.moveaxis(A, 2, 0)              # (nw, nrows, ncols)
    A = A / np.linalg.norm(A, axis=-2, keepdims=True)     # column scaling: O(1) entries, same roots
    return np.linalg.det(A), A

def torsional_det(l, w, Ri, Ro, m):
    kT = w / m['cT']
    solid = Ri <= 0
    kinds = ('j',) if solid else ('j', 'y')
    rows = []
    for r in ((Ro,) if solid else (Ri, Ro)):
        x = kT * r
        rows.append([x * _R(k, l, x, 1) - _R(k, l, x) for k in kinds])   # sigma_rphi ∝ r d/dr (W/r)
    A = np.array(rows, dtype=float)
    if A.ndim == 3: A = np.moveaxis(A, 2, 0)
    A = A / np.linalg.norm(A, axis=-2, keepdims=True)
    return np.linalg.det(A), A

def find_roots(fun, fmin, fmax, df, nmax=50):
    """Sign changes of fun(2*pi*f) on a grid (fun accepts an array of omega), refined with brentq."""
    fs = np.arange(fmin, fmax, df)
    vals = np.asarray(fun(2 * math.pi * fs))
    out = []
    for i in range(len(fs) - 1):
        if vals[i] == 0: out.append(fs[i]); continue
        if np.sign(vals[i]) != np.sign(vals[i + 1]):
            try:
                r = brentq(lambda f: fun(2 * math.pi * f), fs[i], fs[i + 1], xtol=1e-9 * fs[i])
                out.append(r)
            except ValueError:
                pass
        if len(out) >= nmax: break
    return out

def exact_modes(Ri, Ro, m, fmax, lmax=12, df=None):
    """Method A: all spheroidal (nSl) and torsional (nTl) modes below fmax. Returns list of dicts."""
    fmin = 0.02 * fmax
    df = df or fmax / 20000
    modes = []
    for l in range(0, lmax + 1):
        fun = lambda w, l=l: spheroidal_det(l, w, Ri, Ro, m)[0]
        for n, f in enumerate(find_roots(fun, fmin, fmax, df), 1):
            # verify: smallest singular value of the scaled matrix must be tiny
            sv = np.linalg.svd(spheroidal_det(l, 2 * math.pi * f, Ri, Ro, m)[1], compute_uv=False)
            modes.append(dict(family='S', l=l, n=n, f=f, deg=2 * l + 1, smin=float(sv[-1] / sv[0])))
    for l in range(1, lmax + 1):
        fun = lambda w, l=l: torsional_det(l, w, Ri, Ro, m)[0]
        for n, f in enumerate(find_roots(fun, fmin, fmax, df), 1):
            sv = np.linalg.svd(torsional_det(l, 2 * math.pi * f, Ri, Ro, m)[1], compute_uv=False)
            modes.append(dict(family='T', l=l, n=n, f=f, deg=2 * l + 1, smin=float(sv[-1] / sv[0])))
    modes.sort(key=lambda d: d['f'])
    return modes

def exact_eigvec(fam, l, f, Ri, Ro, m):
    """Null vector of the boundary matrix -> radial functions U(r), V(r) (spheroidal) or W(r) (torsional)."""
    w = 2 * math.pi * f
    if fam == 'S':
        A = spheroidal_det(l, w, Ri, Ro, m)[1]
    else:
        A = torsional_det(l, w, Ri, Ro, m)[1]
    _, _, vt = np.linalg.svd(A); c = vt[-1]
    # undo the column scaling (the roots are unaffected but the null vector must be scaled back)
    if fam == 'S':
        rows = []
        for r in ((Ro,) if Ri <= 0 else (Ri, Ro)):
            srr, srt = _spheroidal_rows(l, w, r, m, ('j',) if Ri <= 0 else ('j', 'y')); rows.append(srr)
            if l >= 1: rows.append(srt)
        A0 = np.array(rows, dtype=float)
    else:
        kT = w / m['cT']; rows = []
        for r in ((Ro,) if Ri <= 0 else (Ri, Ro)):
            x = kT * r; rows.append([x * _R(k, l, x, 1) - _R(k, l, x) for k in (('j',) if Ri <= 0 else ('j', 'y'))])
        A0 = np.array(rows, dtype=float)
    c = c / np.linalg.norm(A0, axis=0)
    kinds = ('j',) if Ri <= 0 else ('j', 'y')
    def UV(r):
        if fam == 'T':
            kT = w / m['cT']; x = kT * r
            return sum(ci * _R(k, l, x) for ci, k in zip(c, kinds))
        kL, kT = w / m['cL'], w / m['cT']; Ll = l * (l + 1); U = V = 0.0; i = 0
        for k in kinds:
            x = kL * r; U += c[i] * kL * _R(k, l, x, 1); V += c[i] * _R(k, l, x) / r; i += 1
        if l >= 1:
            for k in kinds:
                x = kT * r; R0, R1 = _R(k, l, x), _R(k, l, x, 1)
                U += c[i] * Ll * R0 / r; V += c[i] * (R0 / r + kT * R1); i += 1
        return U, V
    return UV

# ------------------------------------------------------------------------------------------ Method B
def ritz_modes(Ri, Ro, m, l, fam='S', N=12, nq=40, na=64, nmodes=6):
    """Rayleigh-Ritz on the exact 3-D strain energy for angular order l (m=0 member of the multiplet).
       Radial basis: Legendre polynomials P_0..P_N in xi=(2r-Ri-Ro)/(Ro-Ri). Returns frequencies [Hz] and
       a function giving the radial profiles of the lowest modes."""
    lam, mu, rho = m['lam'], m['mu'], m['rho']
    xq, wq = L.leggauss(nq); r = 0.5 * (Ro - Ri) * xq + 0.5 * (Ro + Ri); wr = 0.5 * (Ro - Ri) * wq
    xa, wa = L.leggauss(na)                                   # x = cos(theta)
    P = eval_legendre(l, xa); dP = np.array([(eval_legendre(l, x + 1e-6) - eval_legendre(l, x - 1e-6)) / 2e-6 for x in xa])
    # exact derivative dP/dx via recurrence for accuracy
    if l >= 1:
        dP = l * (xa * eval_legendre(l, xa) - eval_legendre(l - 1, xa)) / (xa ** 2 - 1)
    else:
        dP = 0 * xa
    s = np.sqrt(1 - xa ** 2)
    Pth = -s * dP                                             # dP/dtheta
    # d2P/dtheta2 from Legendre's equation: P_thth + cot(theta) P_th + l(l+1) P = 0
    Pthth = -(xa / s) * Pth - l * (l + 1) * P
    cotPth = (xa / s) * Pth                                   # cot(theta) dP/dtheta = -x dP/dx (finite)
    # basis values and radial derivatives at quadrature points
    nb = N + 1
    Pm = np.array([L.legval(xq, [0] * k + [1]) for k in range(nb)])                 # (nb, nq)
    dPm = np.array([L.legval(xq, L.legder([0] * k + [1])) for k in range(nb)]) * (2 / (Ro - Ri))
    if fam == 'S':
        nv = nb if l >= 1 else 0                            # no tangential motion for l = 0
        ndof = nb + nv
        K = np.zeros((ndof, ndof)); M = np.zeros((ndof, ndof))
        for iq in range(nq):
            rq = r[iq]
            # strain vectors for each basis function: [e_rr, e_tt, e_pp, e_rt] as arrays over theta
            eps = []
            for k in range(nb):     # U basis
                U, Up = Pm[k, iq], dPm[k, iq]
                eps.append(np.array([Up * P, U * P / rq, U * P / rq, 0.5 * (U / rq) * Pth]))
            for k in range(nv):     # V basis
                V, Vp = Pm[k, iq], dPm[k, iq]
                eps.append(np.array([0 * P, V * Pthth / rq, V * cotPth / rq, 0.5 * (Vp - V / rq) * Pth]))
            E = np.array(eps)                                 # (ndof, 4, na)
            tr = E[:, 0] + E[:, 1] + E[:, 2]
            # energy density: 1/2 lam tr^2 + mu (err^2+ett^2+epp^2+2 ert^2); bilinear form
            Wk = lam * np.einsum('ia,ja,a->ij', tr, tr, wa) + 2 * mu * (np.einsum('ia,ja,a->ij', E[:, 0], E[:, 0], wa)
                 + np.einsum('ia,ja,a->ij', E[:, 1], E[:, 1], wa) + np.einsum('ia,ja,a->ij', E[:, 2], E[:, 2], wa)
                 + 2 * np.einsum('ia,ja,a->ij', E[:, 3], E[:, 3], wa))
            K += 0.5 * Wk * rq ** 2 * wr[iq]
            disp = np.zeros((ndof, 2, na))
            for k in range(nb):
                disp[k, 0] = Pm[k, iq] * P
            for k in range(nv):
                disp[nb + k, 1] = Pm[k, iq] * Pth
            Mk = np.einsum('ica,jca,a->ij', disp, disp, wa)
            M += 0.5 * rho * Mk * rq ** 2 * wr[iq]
    else:
        ndof = nb
        K = np.zeros((ndof, ndof)); M = np.zeros((ndof, ndof))
        for iq in range(nq):
            rq = r[iq]
            eps = []
            for k in range(nb):
                W, Wp = Pm[k, iq], dPm[k, iq]
                eps.append(np.array([0.5 * (Wp - W / rq) * Pth, 0.5 * (W / rq) * (Pthth - cotPth)]))   # e_rphi, e_thphi
            E = np.array(eps)
            # energy density mu*eps:eps = mu*(2 e_rphi^2 + 2 e_thphi^2); the 0.5 below mirrors the spheroidal branch
            Wk = 4 * mu * (np.einsum('ia,ja,a->ij', E[:, 0], E[:, 0], wa) + np.einsum('ia,ja,a->ij', E[:, 1], E[:, 1], wa))
            K += 0.5 * Wk * rq ** 2 * wr[iq]
            disp = np.array([Pm[k, iq] * Pth for k in range(nb)])
            M += 0.5 * rho * np.einsum('ia,ja,a->ij', disp, disp, wa) * rq ** 2 * wr[iq]
    # symmetric generalized eigenproblem; drop the rigid-body / near-null directions
    vals, vecs = eigh(K, M)
    vals = np.where(vals < 0, 0, vals)
    f = np.sqrt(vals) / (2 * math.pi)
    # modal quantities for the lowest modes (radial profiles on a grid)
    def profile(idx, rr):
        a = vecs[:, idx]
        xi = (2 * rr - Ri - Ro) / (Ro - Ri)
        if fam == 'S':
            U = sum(a[k] * L.legval(xi, [0] * k + [1]) for k in range(nb))
            V = sum(a[nb + k] * L.legval(xi, [0] * k + [1]) for k in range(nb)) if l >= 1 else 0 * U
            return U, V
        return sum(a[k] * L.legval(xi, [0] * k + [1]) for k in range(nb))
    return f, profile, (K, M, vecs)

# ------------------------------------------------------------------------------------------ Method C
def membrane_modes(R, m, nmax=12):
    """Baker (1961) membrane theory of a complete thin spherical shell: for each n, two branches of
       Omega = omega R / c_p, c_p = sqrt(E/(rho(1-nu^2))):  Omega^4 - Omega^2 [n(n+1)+1+3nu] + (1-nu^2)[n(n+1)-2] = 0.
       Torsional (Lamb, thin shell): omega R / c_T = sqrt((n-1)(n+2))."""
    nu, cP, cT = m['nu'], m['cP'], m['cT']
    out = []
    for n in range(0, nmax + 1):
        lam_n = n * (n + 1); b = lam_n + 1 + 3 * nu; c = (1 - nu ** 2) * (lam_n - 2)
        disc = math.sqrt(max(b * b - 4 * c, 0))
        for br, O2 in (('lower', (b - disc) / 2), ('upper', (b + disc) / 2)):
            if O2 <= 1e-12: continue
            if n == 0 and br == 'lower': continue
            out.append(dict(family='S', branch=br, l=n, f=math.sqrt(O2) * cP / (2 * math.pi * R), Omega=math.sqrt(O2)))
        if n >= 2:
            out.append(dict(family='T', branch='membrane', l=n, f=math.sqrt((n - 1) * (n + 2)) * cT / (2 * math.pi * R)))
    out.sort(key=lambda d: d['f'])
    return out

# ------------------------------------------------------------------------------------------ demo / self-test
if __name__ == '__main__':
    m = copper()
    print('Cu: E=%.1f GPa G=%.2f GPa K=%.1f nu=%.4f cL=%.0f cT=%.0f cP=%.0f' % (m['E'] / 1e9, m['G'] / 1e9, m['K'] / 1e9, m['nu'], m['cL'], m['cT'], m['cP']))
    # Method A on a solid sphere vs the literature (Lobo 1995, nu=0.33): T2 2.5011, S2 2.6497, S1 3.5895, S0 5.4322, T1 5.7635
    ml = material(1.0, 0.33, 1.0); R = 1.0
    print('solid sphere (nu=0.33), omega R / cT:')
    for fam, l, ref in (('T', 2, 2.5011), ('S', 2, 2.6497), ('S', 1, 3.5895), ('S', 0, 5.4322), ('T', 1, 5.7635), ('S', 3, 3.95 if False else None)):
        fun = (lambda w: torsional_det(l, w, 0, R, ml)[0]) if fam == 'T' else (lambda w: spheroidal_det(l, w, 0, R, ml)[0])
        roots = find_roots(fun, 0.05 * ml['cT'] / (2 * math.pi), 2.0 * ml['cT'] / (2 * math.pi), 0.0005 * ml['cT'] / (2 * math.pi), 3)
        vals = [2 * math.pi * f * R / ml['cT'] for f in roots]
        print(f'  {fam}{l}: {vals[:3]}  literature {ref}')
