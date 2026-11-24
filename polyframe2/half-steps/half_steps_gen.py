# Half-steps course generator (stepped roof v3e, course division B -> half-height courses)
#
# Input: half-steps-course-samples.json, sampled from the v3e printed pieces with radial rays
#   (inner room face at bottom / mid / top of every course, outer vertical face at mid).
# Rule (each 0.5 m course becomes two 0.25 m courses):
#   - inner room face: unchanged (linear within each old course, read from the samples);
#   - lower half: outer face = old outer face O_k;
#   - upper half: outer face = midpoint of O_k and O_k+1 (half the old horizontal step);
#     so every new course bears on the same minimum width as the old one and the
#     re-entrant corners stay on the old envelope; material is only removed.
#   - base ring step, top course (U formwork for the crown ring), crown ring: unchanged.
# Pieces: same section rules as v3e: closed solid, 3 cm walls, 3 cm lid, open bottom,
#   groove 6 x 4 cm on the top centreline with a 3 cm surround, 3 cm end walls,
#   ends perpendicular to the course, ~1.2 m long, head joints staggered half a piece.
import math, json
import Rhino.Geometry as G

def _lerp(a, b, t):
    return a + (b - a) * t

class Course(object):
    pass

def load(path):
    return json.load(open(path))

def new_courses(S, roof, split=2):
    R = S[roof]
    cs = R["courses"]
    NS = len(cs[0]["rout"])
    printed = cs[:-1]
    out = []
    for k, c in enumerate(printed):
        z0, z1 = c["z0"], c["z1"]
        za, zb = c["zs"][0], c["zs"][2]
        ra, rb = c["rin"][0], c["rin"][2]
        Ok = c["rout"]
        # ADD-material rule (2026-11-21): the top half of each old course keeps the old outer
        # face, the lower half(s) step OUT toward the course below, so every new outer corner
        # lies on the old corner line and no material is removed (ribs stay covered).
        Op = R["base"]["rout"] if k == 0 else cs[k - 1]["rout"]
        def I(z, ra=ra, rb=rb, za=za, zb=zb):
            t = (z - za) / (zb - za)
            return [_lerp(ra[i], rb[i], t) for i in range(NS)]
        for s in range(split):
            cc = Course()
            cc.k = k
            cc.half = s
            cc.z0 = _lerp(z0, z1, float(s) / split)
            cc.z1 = _lerp(z0, z1, float(s + 1) / split)
            f = float(split - 1 - s) / split
            cc.O = [_lerp(Ok[i], Op[i], f) for i in range(NS)]
            cc.I = I
            out.append(cc)
    return out

def _poly(cx, cy, r):
    n = len(r)
    pts = [G.Point3d(cx + r[i] * math.cos(2 * math.pi * i / n), cy + r[i] * math.sin(2 * math.pi * i / n), 0) for i in range(n)]
    pts.append(pts[0])
    return G.PolylineCurve(pts)

def _hit(line, crv):
    ev = G.Intersect.Intersection.CurveCurve(line, crv, 1e-6, 1e-6)
    best = None
    for e in ev:
        t = e.ParameterA
        if best is None or abs(t - 1.5) < abs(best - 1.5):
            best = t
    return best

def build_course(cc, cx, cy, j, P):
    """Return list of piece breps for one new course, plus info."""
    z0, z1 = cc.z0, cc.z1
    lid, wall, gw, gd, gs = P["lid"], P["wall"], P["groove_w"] / 2.0, P["groove_d"], P["groove_w"] / 2.0 + P["wall"]
    zb = z0 - 0.01             # void runs out through the open bottom
    zt = z1 - lid              # underside of the lid
    zg = zt - gd               # underside of the groove surround
    curves = {
        "Ib": _poly(cx, cy, cc.I(zb)),
        "I0": _poly(cx, cy, cc.I(z0)),
        "It": _poly(cx, cy, cc.I(zt)),
        "Ig": _poly(cx, cy, cc.I(zg)),
        "I1": _poly(cx, cy, cc.I(z1)),
        "O": _poly(cx, cy, cc.O),
    }
    NS = len(cc.O)
    zm = 0.5 * (z0 + z1)
    rI = cc.I(zm)
    mid = [0.5 * (rI[i] + cc.O[i]) for i in range(NS)]
    step = 4
    mpts = [G.Point3d(cx + mid[i] * math.cos(2 * math.pi * i / NS), cy + mid[i] * math.sin(2 * math.pi * i / NS), 0) for i in range(0, NS, step)]
    mpts.append(mpts[0])
    M = G.Curve.CreateInterpolatedCurve(mpts, 3, G.CurveKnotStyle.ChordPeriodic)
    L = M.GetLength()
    n = max(3, int(round(L / P["piece_len"])))
    seg = L / n
    off = (j % 2) * 0.5 * seg

    def station(a):
        a = a % L
        ok, t = M.LengthParameter(a)
        p = M.PointAt(t)
        tg = M.TangentAt(t)
        nv = G.Vector3d(-tg.Y, tg.X, 0)       # left normal; M runs CCW so this points inward
        nv.Unitize()
        ln = G.LineCurve(p - nv * 1.5, p + nv * 1.5)
        s = {}
        for key, crv in curves.items():
            h = _hit(ln, crv)
            if h is None:
                return None
            s[key] = (h - ln.Domain.Min) - 1.5   # signed distance along nv from p (positive = inward)
        return p, nv, s

    def prof(st, kind):
        p, nv, s = st
        # signed distances: inward positive. Outer face s["O"] is the most negative.
        sO = s["O"]
        if kind == "env":
            pts = [(s["I0"], z0), (sO, z0), (sO, z1), (s["I1"], z1)]
        else:
            # inner wall horizontal thickness from the local face slope
            dz = z1 - z0
            dr = abs(s["I1"] - s["I0"])
            sinb = dz / math.sqrt(dz * dz + dr * dr)
            hin = wall / sinb
            sc = 0.5 * (s["I1"] + sO)               # groove centreline on the top face
            if kind == "void":
                pts = [(s["Ib"] - hin, zb), (sO + wall, zb), (sO + wall, zt), (sc - gs, zt), (sc - gs, zg),
                       (sc + gs, zg), (sc + gs, zt), (s["It"] - hin, zt)]
            else:  # groove
                pts = [(sc - gw, z1 - gd), (sc + gw, z1 - gd), (sc + gw, z1 + 0.01), (sc - gw, z1 + 0.01)]
        out = [G.Point3d(p.X + nv.X * a, p.Y + nv.Y * a, z) for a, z in pts]
        out.append(out[0])
        return G.PolylineCurve(out)

    def solid(a0, a1, kind):
        k = max(2, int(math.ceil((a1 - a0) / P["facet"])) + 1)
        secs = []
        for i in range(k):
            st = station(a0 + (a1 - a0) * i / (k - 1.0))
            if st is None:
                return None
            secs.append(prof(st, kind))
        lo = G.Brep.CreateFromLoft(secs, G.Point3d.Unset, G.Point3d.Unset, G.LoftType.Straight, False)
        if not lo:
            return None
        b = lo[0].CapPlanarHoles(0.001)
        if b is None:
            return None
        if b.SolidOrientation == G.BrepSolidOrientation.Inward:
            b.Flip()
        return b

    pieces = []
    fails = 0
    for i in range(n):
        a0 = off + i * seg
        a1 = a0 + seg
        env = solid(a0, a1, "env")
        vd = solid(a0 + P["end_wall"], a1 - P["end_wall"], "void")
        gr = solid(a0 - 0.02, a1 + 0.02, "groove")
        if env is None or vd is None or gr is None:
            fails += 1
            continue
        res = G.Brep.CreateBooleanDifference([env], [vd, gr], 0.0005)
        if res and len(res) == 1 and res[0].IsSolid:
            pieces.append(res[0])
        else:
            fails += 1
            pieces.append(env)   # keep the envelope so nothing goes missing; reported as a failure
    info = {"z0": z0, "z1": z1, "n": n, "seg": seg, "L": L, "fails": fails}
    return pieces, info

DEFAULTS = {"lid": 0.03, "wall": 0.03, "groove_w": 0.06, "groove_d": 0.04, "end_wall": 0.03, "piece_len": 1.2, "facet": 0.2}


# ---------------------------------------------------------------------------
# Rings in the half-step rhythm (base ring step and crown ring course)
# Each ring's outer face is split into two half-height bands; the upper band
# steps in by half a step, like the courses. The cast core keeps its height and
# follows the stepped face inside the 3 cm printed formwork (L-shaped core).
def _station_fn(M, curves):
    L = M.GetLength()
    def station(a):
        a = a % L
        ok, t = M.LengthParameter(a)
        p = M.PointAt(t)
        tg = M.TangentAt(t)
        nv = G.Vector3d(-tg.Y, tg.X, 0)
        nv.Unitize()
        ln = G.LineCurve(p - nv * 1.5, p + nv * 1.5)
        s = {}
        for key, crv in curves.items():
            h = _hit(ln, crv)
            if h is None:
                return None
            s[key] = (h - ln.Domain.Min) - 1.5
        return p, nv, s
    return station, L

def _mid_curve(cx, cy, ra, rb):
    NS = len(ra)
    mpts = [G.Point3d(cx + 0.5 * (ra[i] + rb[i]) * math.cos(2 * math.pi * i / NS),
                      cy + 0.5 * (ra[i] + rb[i]) * math.sin(2 * math.pi * i / NS), 0) for i in range(0, NS, 4)]
    mpts.append(mpts[0])
    return G.Curve.CreateInterpolatedCurve(mpts, 3, G.CurveKnotStyle.ChordPeriodic)

def _loft(secs, closed):
    lo = G.Brep.CreateFromLoft(secs, G.Point3d.Unset, G.Point3d.Unset, G.LoftType.Straight, closed)
    if not lo:
        return None
    b = lo[0]
    if not closed:
        b = b.CapPlanarHoles(0.001)
        if b is None:
            return None
    if b.SolidOrientation == G.BrepSolidOrientation.Inward:
        b.Flip()
    return b

def _poly_sec(st, pts):
    p, nv, s = st
    out = [G.Point3d(p.X + nv.X * a, p.Y + nv.Y * a, z) for a, z in pts]
    out.append(out[0])
    return G.PolylineCurve(out)

def build_ring(S, roof, which, P):
    R = S[roof]
    cx, cy = R["cx"], R["cy"]
    cs = R["courses"]
    NS = len(cs[0]["rout"])
    w = P["wall"]
    e = 0.01
    if which == "base":
        B = R["base"]
        z0, z1 = B["z0"], B["z1"]
        zs = 0.5 * (z0 + z1)
        O0 = cs[0]["rout"]
        mid = [0.5 * (B["rout"][i] + O0[i]) for i in range(NS)]
        curves = {"Ri": _poly(cx, cy, B["rin"]), "Ro": _poly(cx, cy, B["rout"]), "Rm": _poly(cx, cy, mid)}
        M = _mid_curve(cx, cy, B["rin"], B["rout"])
        def env(s):
            return [(s["Ri"], z0), (s["Ro"], z0), (s["Ro"], zs), (s["Rm"], zs), (s["Rm"], z1), (s["Ri"], z1)]
        def core(s, cut):
            d = e if cut else 0.0
            return [(s["Ri"] - w, z0 + w), (s["Ro"] + w, z0 + w), (s["Ro"] + w, zs - w), (s["Rm"] + w, zs - w),
                    (s["Rm"] + w, z1 + d), (s["Ri"] - w, z1 + d)]
    else:
        t = cs[-1]
        z0, z1 = t["z0"], t["z1"]
        zs = 0.5 * (z0 + z1)
        za, zb = t["zs"][0], t["zs"][2]
        ra, rb = t["rin"][0], t["rin"][2]
        def I(z):
            f = (z - za) / (zb - za)
            return [_lerp(ra[i], rb[i], f) for i in range(NS)]
        Ro = t["rout"]
        O17 = cs[-2]["rout"]
        # ADD rule: lower band steps OUT half a step (toward the last course), upper band keeps the old face
        Rlow = [0.5 * (O17[i] + Ro[i]) for i in range(NS)]
        curves = {"I0": _poly(cx, cy, I(z0)), "I0w": _poly(cx, cy, I(z0 + w)), "I1": _poly(cx, cy, I(z1)),
                  "I1e": _poly(cx, cy, I(z1 + e)), "Ro": _poly(cx, cy, Rlow), "Rm": _poly(cx, cy, Ro)}
        M = _mid_curve(cx, cy, I(zs), Ro)
        def hin(s):
            dz = z1 - z0
            dr = abs(s["I1"] - s["I0"])
            return w * math.sqrt(dz * dz + dr * dr) / dz
        def env(s):
            return [(s["I0"], z0), (s["Ro"], z0), (s["Ro"], zs), (s["Rm"], zs), (s["Rm"], z1), (s["I1"], z1)]
        def core(s, cut):
            d = e if cut else 0.0
            h = hin(s)
            top = s["I1e"] if cut else s["I1"]
            return [(s["I0w"] - h, z0 + w), (s["Ro"] + w, z0 + w), (s["Ro"] + w, zs - w), (s["Rm"] + w, zs - w),
                    (s["Rm"] + w, z1 + d), (top - h, z1 + d)]
    station, L = _station_fn(M, curves)

    def solid(a0, a1, fn, closed=False):
        k = max(2, int(math.ceil((a1 - a0) / P["facet"])) + 1)
        secs = []
        n = k - 1 if closed else k
        for i in range(n):
            st = station(a0 + (a1 - a0) * i / (k - 1.0))
            if st is None:
                return None
            secs.append(_poly_sec(st, fn(st[2])))
        return _loft(secs, closed)

    cast = solid(0.0, L, lambda s: core(s, False), closed=True)
    n = max(3, int(round(L / P["piece_len"])))
    seg = L / n
    pieces, fails = [], 0
    for i in range(n):
        a0, a1 = i * seg, (i + 1) * seg
        en = solid(a0, a1, env)
        cu = solid(a0 - 0.02, a1 + 0.02, lambda s: core(s, True))
        if en is None or cu is None:
            fails += 1
            continue
        res = G.Brep.CreateBooleanDifference([en], [cu], 0.0005)
        if res and len(res) >= 1:
            pieces += list(res)
        else:
            fails += 1
            pieces.append(en)
    # numbers at theta = 0 for the report
    st0 = station(0.0)
    info = {"z0": z0, "zs": zs, "z1": z1, "n": n, "fails": fails, "L": L,
            "cast_ok": cast is not None and cast.IsSolid}
    if cast is not None:
        amp = G.VolumeMassProperties.Compute(cast)
        info["cast_area_avg"] = abs(amp.Volume) / L if amp else None
    return pieces, cast, info
