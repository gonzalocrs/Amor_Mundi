"""Roof pieces with rib channels: 3D-printed lost formwork for the cast rib grid of the Karamba model

Takes the rib lines straight out of scripts/karamba_model.py (`rib_lines`, `rib_ids`) and cuts the printed roof shell
into pieces that leave an open channel wherever a rib runs. Stack the pieces, drop the bars into the channels and
pour: the channels become the cast ribs, the horizontal rib rings and the crown ring of the Karamba model.

What changed from scripts/cork_house_roof.py, and why:
  - Course joints are SQUARE TO THE SLOPE, not horizontal. Every piece prints upright (its walls vertical, zero lean)
    and is rotated into place. With horizontal courses on a 53 deg roof the printed walls lean 37 deg from vertical
    (cork_house_roof.py rates anything over 30 deg RED), and the force running down the face meets each horizontal bed
    joint 37 deg off square: shear / compression = tan 37 = 0.75 on the joint, against ~0.4 friction for mortar joints
    (EN 1996-1-1 3.6.2). On a joint square to the slope the membrane force is pure compression.
    Precedent: Striatus (Block Research Group ETH Zurich, Zaha Hadid CODE, incremental3D; Venice 2021): printed concrete
    blocks whose print layers are orthogonal to the force flow.
  - The column ribs run up the slope, so in the print they are near-vertical tubes; the horizontal ribs and the crown
    ring are open troughs along the top of a course (the course joint is put at the top of every ring).
  - At the hips each corner is two half pieces mitred on the hip; the hip rib channel straddles the mitre, so the cast
    hip rib covers that joint. Elsewhere joints are kept clear of the channels and staggered course to course.
  - Cores cast inside printed walls follow 3DCP wall practice (vertical rebar cores grouted in the printed cavity, as
    in ICC-ES AC509 walls); here the cores are the rib channels.

Build-up square to the slope, room side out (same as the Karamba model and the drawing set):
    inner bead | rib zone (rib_d, webs + channels) | middle bead | lattice zone (lattice, zig-zag web) | outer beads
Every printed layer is one `bead` wide, so the print width is `bead` (30 mm) everywhere.

Print path of one layer (one continuous path, no bead printed twice; layers alternate direction):
  long piece:   inner bead -> far end wall -> outer bead -> near end wall -> zig-zag webs across the rib zone, up and
                over every channel (the channel walls + the middle bead over the channel) -> middle bead back, stepping
                out into the lattice zone around each channel -> zig-zag lattice web
  hip piece:    zig-zag lattice web -> middle bead -> rib zone webs and channels -> up the hip channel wall, middle bead
                to the mitre -> mitre end wall (lattice zone only, the rib zone stays open into the hip channel) ->
                outer bead -> near end wall -> inner bead, ending at the mitre
  ring layers (inside a horizontal ring or the crown ring): the rib zone is an open trough, so the inner bead is a
                second contour (one stop per layer); counted in `info`.

Paste into a Python 3 Script component (Rhino 8) or GhPython (Rhino 7). Units: millimetres. The geometry core is pure
Python: `python scripts/rib_pieces.py` builds the default roof from karamba_model.py and checks every print layer.

INPUTS (all optional except rib_lines; same names and defaults as karamba_model.py where they overlap)
    rib_lines    list Line    karamba_model `rib_lines` (List Access)
    rib_ids      list str     karamba_model `rib_ids`   (List Access)
    centre       Point3d      module centre in plan (z ignored)                       0,0,0
    module       str          module name, first part of every piece id               M1
    clear        float        clear inside dimension along x                           10000
    clear_y      float        clear inside dimension along y (rectangle)               = clear
    wall, wall_h, base_h, rise, slope, opening, bead, outer_beads, lattice, rib_w, rib_d, crown_b: as karamba_model
    course_H     float        course height along the slope                            450
    piece_min    float        shortest long piece                                       900
    piece_max    float        longest long piece                                        1500
    hip_L        float        corner leg length on the room face (top of the course)   500
    web_sp       float        zig-zag pitch of the rib zone webs                        600
    wave         float        zig-zag pitch of the lattice web                          300
    layer_H      float        print layer height                                        10
    speed        float        print speed mm/s, for the layer-time check               100
    min_layer_t  float        shortest safe layer time, s                               30
    min_stagger  float        joint offset from the course below                       250
    density      float        printed concrete, t/m3                                    2.3
    seed         int          change for another joint layout                           1
    print_paths  bool         build print paths + bead preview (slow)                   False
    solids       bool         cut the channels out of `blocks` (booleans)              True
    piece        str          id of one piece to pick out                               none

OUTPUTS
    blocks       pieces as Breps in place, tree {face; course}  -> Revit (DirectShape)
    ids          piece id per block, same tree
    tags         label point per block
    cutlist      id, length, mass, layers, print time
    ribs         the cast concrete (ribs, rings, hips, crown ring) as Breps  -> Revit
    rib_names    one name per `ribs` item
    rib_axes     rib centrelines in place (for the bars)
    toolpaths    print path per layer, PRINT ORIENTATION (piece on the bed at the origin), tree {face; course; piece}
    beads        printed bead preview in place, one mesh per piece, tree {face; course}
    to_print     Transform per piece (in place -> on the print bed), tree {face; course}
    check        every piece rated AMBER / RED, with the reason
    piece_paths  the picked piece's layer paths on the print bed  -> Join Open Contours -> Curve Slicer (SaladSlicer)
    piece_beads  the picked piece's beads on the print bed
    piece_check  the picked piece's rating
    info         summary and warnings
"""
import math
import random

DEFAULTS = dict(
    clear=10000.0, clear_y=None, wall=400.0, wall_h=2500.0, base_h=300.0, rise=6000.0, slope=None, opening=1000.0,
    bead=30.0, outer_beads=1, lattice=120.0, rib_w=160.0, rib_d=160.0, crown_b=200.0,
    course_H=450.0, piece_min=900.0, piece_max=1500.0, hip_L=500.0, web_sp=600.0, wave=300.0,
    layer_H=10.0, speed=100.0, min_layer_t=30.0, min_stagger=250.0, density=2.3, seed=1, module="M1",
)
FACE = "ENWS"                     # face k = 0..3: +x, +y, -x, -y


# ===================================== small vector helpers =====================================
def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def _sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def _norm(a):
    L = math.sqrt(_dot(a, a))
    return tuple(x / L for x in a)


# 2D lines in a print layer, (a, c, d): a u + c w = d, a^2 + c^2 = 1, the piece's inside is a u + c w <= d
def _line(a, c, d):
    L = math.hypot(a, c)
    return (a / L, c / L, d / L)


def _ux(ln, w, inset=0.0):
    """u where the line (moved `inset` further inside the piece) crosses the rail at w"""
    a, c, d = ln
    return (d - inset - c * w) / a


def _left(u):                     # boundary on the -u side of a region (the region is at u >= this)
    return (-1.0, 0.0, -u)


def _right(u):                    # boundary on the +u side of a region
    return (1.0, 0.0, u)


# ===================================== the roof =====================================
class Roof:
    """One pyramid module: a rectangle with four faces of the same slope and a hollow top. Each face k has a local
    frame: u along the side (+u towards face k+1), v up the slope, w square to the face out of the room (w = 0 is the
    room-side face). Course joints are planes v = const, the print layers too."""

    def __init__(self, p, centre=(0.0, 0.0)):
        self.p = p
        self.C = (float(centre[0]), float(centre[1]))
        hx = p["clear"] / 2.0
        hy = (p["clear_y"] or p["clear"]) / 2.0
        self.hx, self.hy = hx, hy
        run = min(hx, hy) - p["opening"] / 2.0
        if run <= 0:
            raise ValueError("opening must be smaller than the clear plan")
        rise = run * math.tan(math.radians(p["slope"])) if p["slope"] else float(p["rise"])
        self.rise = rise
        L = math.hypot(run, rise)
        self.sa, self.ca = rise / L, run / L
        self.slope = math.degrees(math.atan2(rise, run))
        b, n_out = p["bead"], int(p["outer_beads"])
        self.T = b * (2 + n_out) + p["rib_d"] + p["lattice"]
        self.c_rib = b + p["rib_d"] / 2.0
        # rails (bead centrelines) and touch lines (one bead off a rail)
        self.wI = b / 2.0
        self.tI = 1.5 * b
        self.wM = 1.5 * b + p["rib_d"]
        self.tM = self.wM - b
        self.tM2 = self.wM + b
        self.wO = [self.T - b / 2.0 - j * b for j in range(n_out)]      # outermost first
        self.tO = self.wO[-1] - b
        self.z_e = p["wall_h"]                                           # room-side face meets the wall at the eave
        self.v_s = p["base_h"] / self.sa                                 # top of the cast solid base (room face)
        self.v_top = rise / self.sa                                      # crown, room face
        self.faces = []
        for k in range(4):
            th = math.radians(90 * k)
            n, t = (math.cos(th), math.sin(th)), (-math.sin(th), math.cos(th))
            B = hx if k % 2 == 0 else hy
            A = hy if k % 2 == 0 else hx
            O = (self.C[0] + n[0] * B, self.C[1] + n[1] * B, self.z_e)
            self.faces.append(dict(k=k, n=n, t=t, A=A, B=B, O=O, U=(t[0], t[1], 0.0),
                                   V=(-n[0] * self.ca, -n[1] * self.ca, self.sa),
                                   N=(n[0] * self.sa, n[1] * self.sa, self.ca)))
        self.mitres = {}
        for k in range(4):
            for side in (1, -1):
                self.mitres[k, side] = self._mitre(k, side)

    def local(self, k, X):
        f = self.faces[k]
        r = _sub(X, f["O"])
        return (_dot(r, f["U"]), _dot(r, f["V"]), _dot(r, f["N"]))

    def world(self, k, u, v, w):
        f = self.faces[k]
        return tuple(f["O"][i] + u * f["U"][i] + v * f["V"][i] + w * f["N"][i] for i in range(3))

    def _mitre(self, k, side):
        """the hip plane between face k and its neighbour on side +1 (k+1, +u end) or -1 (k-1, -u end), in face k's
        frame: a u + b v + c w <= d is face k's side"""
        f, g = self.faces[k], self.faces[(k + side) % 4]
        nb = (f["n"][0] - g["n"][0], f["n"][1] - g["n"][1], 0.0)
        P0 = (self.C[0] + f["n"][0] * f["B"] + g["n"][0] * g["B"], self.C[1] + f["n"][1] * f["B"] + g["n"][1] * g["B"], 0.0)
        return (-_dot(nb, f["U"]), -_dot(nb, f["V"]), -_dot(nb, f["N"]), -_dot(nb, _sub(P0, f["O"])))

    def mitre_line(self, k, side, v):
        a, b, c, d = self.mitres[k, side]
        return _line(a, c, d - b * v)

    def mitre_u(self, k, side, v, w):
        return _ux(self.mitre_line(k, side, v), w)

    def v_of_z(self, z, w):
        """v of the point at height z on the layer plane w"""
        return (z - self.z_e - w * self.ca) / self.sa


# ===================================== ribs from the Karamba model =====================================
def map_ribs(roof, lines, ids):
    """Karamba rib lines (on the Karamba shell) -> the physical rib-zone mid-plane of each face.
    A point keeps its height z and its share xi of the face width between the hips (xi = -1 left hip, +1 right hip),
    so grid A columns (straight lines at constant xi) and the hips land exactly; grid B diagonals stay within a
    millimetre or two of parallel to the hips. Horizontal rings keep their height."""
    p = roof.p
    out = dict(segs={k: [] for k in range(4)}, ring_v=[], n_in=0, n_used=0, skipped=0)
    ids = list(ids or [])
    margin = p["wall"] + 50.0
    for i, ln in enumerate(lines or []):
        P1, P2 = ln
        rid = str(ids[i]).strip().lower() if i < len(ids) and ids[i] is not None else ""
        out["n_in"] += 1
        if not all(abs(P[0] - roof.C[0]) <= roof.hx + margin and abs(P[1] - roof.C[1]) <= roof.hy + margin for P in (P1, P2)):
            out["skipped"] += 1                      # another module's rib
            continue
        if rid == "hring" or (rid not in ("col", "diag", "hip") and abs(P1[2] - P2[2]) < 1.0):
            z = (P1[2] + P2[2]) / 2.0
            v = roof.v_of_z(z, roof.c_rib)
            if not any(abs(v - q) < 1.0 for q in out["ring_v"]):
                out["ring_v"].append(v)
            out["n_used"] += 1
            continue
        f1, f2 = _faces_of(roof, P1), _faces_of(roof, P2)
        used = False
        for k in sorted(set(f1) & set(f2)):
            a, xa = _to_face(roof, k, P1)
            b, xb = _to_face(roof, k, P2)
            if abs(a[1] - b[1]) < 1e-6:
                continue
            if a[1] > b[1]:
                a, b, xa, xb = b, a, xb, xa
            hip = 0
            if abs(xa) > 0.999 and abs(xb) > 0.999 and xa * xb > 0:
                hip = 1 if xa > 0 else -1
            out["segs"][k].append(dict(u1=a[0], v1=a[1], u2=b[0], v2=b[1], hip=hip, id=rid or "col"))
            used = True
        out["n_used"] += used
    out["ring_v"].sort()
    return out


def _faces_of(roof, X):
    m = [_dot((X[0] - roof.C[0], X[1] - roof.C[1]), f["n"]) - f["B"] for f in roof.faces]
    mx = max(m)
    return [k for k in range(4) if m[k] >= mx - 1.0]


def _to_face(roof, k, X):
    f = roof.faces[k]
    r = (X[0] - roof.C[0], X[1] - roof.C[1])
    dist, s = _dot(r, f["n"]), _dot(r, f["t"])
    xi = s / (dist + f["A"] - f["B"])
    z = X[2]
    dp = f["B"] - (z - roof.z_e) * roof.ca / roof.sa + roof.c_rib / roof.sa
    sp = xi * (dp + f["A"] - f["B"])
    P = (roof.C[0] + f["n"][0] * dp + f["t"][0] * sp, roof.C[1] + f["n"][1] * dp + f["t"][1] * sp, z)
    u, v, _ = roof.local(k, P)
    return (u, v), xi


def channels_at(roof, segs, k, v):
    """rib channels crossing the layer v of face k: regular [(lo, hi)] (u, constant across the rib zone) and the
    hip channels {side: u of the channel's inner edge}"""
    hw0 = roof.p["rib_w"] / 2.0
    reg, hip = [], {}
    for s in segs[k]:
        if not (s["v1"] - 1e-6 <= v <= s["v2"] + 1e-6):
            continue
        f = (v - s["v1"]) / (s["v2"] - s["v1"])
        uc = s["u1"] + f * (s["u2"] - s["u1"])
        du, dv = s["u2"] - s["u1"], s["v2"] - s["v1"]
        ev = abs(dv) / math.hypot(du, dv)
        hw = hw0 / max(ev, 0.2)
        if s["hip"]:
            side = s["hip"]
            e = uc - side * hw                        # the hip rib is rib_w wide square to the hip, half in each face
            hip[side] = min(hip.get(side, e), e) if side > 0 else max(hip.get(side, e), e)
        else:
            reg.append((uc - hw, uc + hw))
    return reg, hip


def _merge(iv, gap):
    out = []
    for lo, hi in sorted(iv):
        if out and lo - out[-1][1] < gap:
            out[-1] = (out[-1][0], max(out[-1][1], hi))
        else:
            out.append((lo, hi))
    return out


# ===================================== courses and joints =====================================
def courses(roof, ring_v):
    p = roof.p
    bands = [(v - p["rib_w"] / 2.0, v + p["rib_w"] / 2.0, "ring") for v in ring_v]
    bands.append((roof.v_top - p["crown_b"], roof.v_top + 1.0, "crown"))
    warn = []
    breaks = [roof.v_s]
    for lo, hi, kind in bands[:-1]:
        if lo < roof.v_s + 100.0 or hi > roof.v_top - p["crown_b"] - 100.0:
            warn.append("ring at v {:.0f} too close to the base or the crown: no course joint forced".format((lo + hi) / 2))
            continue
        breaks.append(hi)
    breaks = sorted(set(breaks)) + [roof.v_top]
    cs = []
    for a, b in zip(breaks, breaks[1:]):
        n = max(1, int(round((b - a) / p["course_H"])))
        for i in range(n):
            cs.append((a + (b - a) * i / n, a + (b - a) * (i + 1) / n))
    for (lo, hi, kind) in bands:
        for c0, c1 in cs:
            if c0 + 1.0 < lo < c1 - 1.0 and hi > c1 + 1.0:
                warn.append("{} band {:.0f}-{:.0f} crosses the course joint at {:.0f}".format(kind, lo, hi, c1))
    return cs, bands, warn


def _forbidden(roof, segs, k, v0, v1, clr):
    """u intervals where a vertical joint can't go in this course (a channel within clr), and the hip limits"""
    iv, lim = [], {1: 1e9, -1: -1e9}
    vs = [v0 + (v1 - v0) * i / 4.0 for i in range(5)]
    for v in vs:
        reg, hip = channels_at(roof, segs, k, v)
        iv += [(lo - clr, hi + clr) for lo, hi in reg]
        for side, e in hip.items():
            lim[side] = min(lim[side], e - clr) if side > 0 else max(lim[side], e + clr)
    return _merge(iv, 0.0), lim


def lay_joints(roof, segs, k, v0, v1, below, rnd, warn, tag):
    p, b = roof.p, roof.p["bead"]
    clr = 7 * b                                       # joint to channel: room for the walls, the zig-zag and the bumps
    bad, lim = _forbidden(roof, segs, k, v0, v1, clr)
    uR = roof.mitre_u(k, 1, v1, 0.0)                    # room-face hip at the top of the course
    uL = roof.mitre_u(k, -1, v1, 0.0)
    leg_min = 4 * b + p["rib_w"]                      # shortest leg that still holds the hip channel and its walls
    hiR = min(lim[1], uR - leg_min)
    loL = max(lim[-1], uL + leg_min)
    ok = lambda j: not any(lo < j < hi for lo, hi in bad)
    stag = p["min_stagger"]

    def pick(lo, hi, target, spread=0.0):
        best = None
        j = lo
        while j <= hi + 1e-6:
            if ok(j):
                dmin = min([abs(j - q) for q in below] or [1e9])
                key = (dmin >= stag, -abs(j - target) + (rnd.uniform(-spread, spread) if spread else 0.0))
                if best is None or key > best[0]:
                    best = (key, j)
            j += 10.0
        return None if best is None else best[1]

    if hiR - loL < 2 * leg_min:
        warn.append("{}: side too short for two hip pieces".format(tag))
        jm = pick(loL, hiR, (loL + hiR) / 2.0) if hiR > loL else (uL + uR) / 2.0
        return [jm if jm is not None else (uL + uR) / 2.0]
    jL = pick(loL, max(loL, uL + p["hip_L"] + p["piece_max"]), uL + p["hip_L"])
    jL = jL if jL is not None else pick(loL, hiR, uL + p["hip_L"])
    jR = pick(min(hiR, uR - p["hip_L"] - p["piece_max"]), hiR, uR - p["hip_L"])
    jR = jR if jR is not None else pick(loL, hiR, uR - p["hip_L"])
    if jL is None or jR is None or jR - jL < p["piece_min"]:   # the two hip pieces meet: one joint
        jm = pick(loL, hiR, (loL + hiR) / 2.0, spread=200.0)
        if jm is None:
            warn.append("{}: no joint clear of the channels".format(tag))
            jm = (loL + hiR) / 2.0
        return [jm]
    joints, pos = [jL], jL
    while jR - pos > p["piece_max"]:
        lo, hi = pos + p["piece_min"], min(pos + p["piece_max"], jR - p["piece_min"])
        j = pick(lo, hi, rnd.uniform(lo, hi), spread=100.0) if hi >= lo else None
        if j is None:
            j = pick(pos + 0.6 * p["piece_min"], min(pos + 1.3 * p["piece_max"], jR - 0.5 * p["piece_min"]), (lo + hi) / 2.0)
            if j is None:
                warn.append("{}: a piece longer than piece_max (channels in the way)".format(tag))
                break
        joints.append(j)
        pos = j
    joints.append(jR)
    return joints


# ===================================== print paths =====================================
class Layer:
    """one print layer of one piece: computes the path in (u, w)"""

    def __init__(self, roof, segs, k, v, endS, endF, band, mitS=False, mitF=False):
        self.r, self.k, self.v = roof, k, v
        self.b = roof.p["bead"]
        self.eS, self.eF = endS, endF                 # boundary lines of the piece (inside <=)
        self.band = band
        self.hipF = self.hipS = None
        reg, hip = channels_at(roof, segs, k, v) if not band else ([], {})
        cS, cF = _ux(endS, roof.c_rib, 0.0), _ux(endF, roof.c_rib, 0.0)
        reg = [(lo, hi) for lo, hi in reg if hi > cS and lo < cF]
        reg = _merge(reg, 2 * self.b)
        self.warn = []
        if mitF and 1 in hip:                                    # mitre at F with a hip rib
            e = hip[1]
            while reg and reg[-1][1] > e - 7 * self.b:            # a channel too close to the hip channel joins it
                e = min(e, reg.pop()[0])
            self.hipF = e
        if mitS and -1 in hip:
            e = hip[-1]
            while reg and reg[0][0] < e + 7 * self.b:
                e = max(e, reg.pop(0)[1])
            self.hipS = e
        uS = _ux(endS, self.r.tI, 3 * self.b)
        uF = _ux(endF, self.r.tI, 3 * self.b)
        keep = []
        for lo, hi in reg:
            if lo < uS or hi > uF:
                self.warn.append("channel {:.0f}-{:.0f} runs into the piece end".format(lo, hi))
            else:
                keep.append((lo, hi))
        self.reg = keep

    def path(self):
        if self.hipS is not None and self.hipF is not None:
            raise ValueError("a piece with a hip channel at both ends")
        if self.hipS is not None:                     # mirror u, build as a hip at F, mirror back
            m = self._mirror()
            return [[(-u, w) for u, w in c] for c in m.path()]
        if self.band:
            return self._band()
        if self.hipF is not None:
            return [self._hip()]
        return [self._long()]

    def _mirror(self):
        m = Layer.__new__(Layer)
        m.__dict__.update(self.__dict__)
        flip = lambda ln: (-ln[0], ln[1], ln[2])
        m.eS, m.eF = flip(self.eF), flip(self.eS)
        m.hipF, m.hipS = -self.hipS, None
        m.reg = sorted((-hi, -lo) for lo, hi in self.reg)
        return m

    # --- pieces of path
    def _zig(self, Lb, Rb, a, b_, pitch, w1, w2):
        """zig-zag between the touch lines w1 and w2 from point a to point b_ (each on w1 or w2), its vertices one
        bead clear of the boundary lines Lb (left) and Rb (right). Returns the points after a, ending with b_."""
        bd = self.b
        lim = lambda w: (_ux(Lb, w, bd), _ux(Rb, w, bd))
        other = lambda w: w2 if abs(w - w1) < 1e-6 else w1
        ua, wa = a
        ub, wb = b_
        same = abs(wa - wb) < 1e-6
        u0 = max(ua, lim(wa)[0])
        u1 = min(ub, lim(wb)[1])
        span = u1 - u0
        if span <= 0:                                  # no room for a web: straight to the end
            return [b_]
        pts = [(u0, wa)] if u0 > ua + 0.5 else []
        m = int(round(span / (pitch / 2.0)))
        if same and m % 2:
            m += 1
        if not same and m % 2 == 0:
            m += 1
        mid = []
        while m >= 2:
            mid, okay, prev = [], True, (u0, wa)
            for j in range(1, m):
                w = wa if j % 2 == 0 else other(wa)
                lw, rw = lim(w)
                u = min(max(u0 + span * j / m, lw), rw)
                if u < prev[0] - 1e-6 or math.hypot(u - prev[0], w - prev[1]) < bd:
                    okay = False
                    break
                mid.append((u, w))
                prev = (u, w)
            if okay and math.hypot(u1 - prev[0], wb - prev[1]) >= bd:
                break
            mid = []
            m -= 2
        pts += mid + [(u1, wb)]
        if ub > u1 + 0.5:
            pts.append(b_)
        return pts

    def _rib_pass(self, start, end_line, end_w):
        """S -> F across the rib zone: zig-zag webs between the channels; over each channel: up its left wall, the
        middle bead across, down its right wall. start = (u, w) on tI or tM; ends on end_w (tI or tM) one bead short
        of end_line"""
        r, bd = self.r, self.b
        pts = [start]
        Lb = _shift(self.eS, bd / 2.0)
        cur = start
        for lo, hi in self.reg:
            WL, WR = lo - bd / 2.0, hi + bd / 2.0
            foot = (WL, r.tI)
            pts += self._zig(Lb, _right(WL), cur, foot, self.r.p["web_sp"], r.tI, r.tM)
            pts += [(WL, r.wM), (WR, r.wM), (WR, r.tI)]
            cur = (WR, r.tI)
            Lb = _left(WR)
        if end_w is None:                              # hip piece: end at the hip channel's wall foot
            WL = self.hipF - bd / 2.0
            pts += self._zig(Lb, _right(WL), cur, (WL, r.tI), self.r.p["web_sp"], r.tI, r.tM)
            return pts
        u_end = _ux(end_line, end_w, bd)
        pts += self._zig(Lb, end_line, cur, (u_end, end_w), self.r.p["web_sp"], r.tI, r.tM)
        return pts

    def _bumps(self):
        bd = self.b
        bs = [(lo - 1.5 * bd, hi + 1.5 * bd) for lo, hi in self.reg]    # bump leg centrelines
        return _merge(bs, bd)

    def _m_rail_back(self, u_from, u_to):
        """middle bead from u_from (F side) back to u_to (S side), stepping out over each channel"""
        r, bd = self.r, self.b
        pts = [(u_from, r.wM)]
        for lo, hi in reversed(self._bumps()):
            if hi > u_from or lo < u_to:
                continue
            pts += [(hi, r.wM), (hi, r.tM2), (lo, r.tM2), (lo, r.wM)]
        pts.append((u_to, r.wM))
        return pts

    def _lattice(self, start_u, end_u, Rb, end_w):
        """zig-zag web S -> F between the middle bead (or its bumps) and the outer bead, from (start_u, tM2)"""
        r, bd = self.r, self.b
        bumps = self._bumps()
        top = r.tM2 + bd                              # touch line over a bump
        z = [(start_u, r.tM2)] + self._zig(_left(start_u - bd), Rb, (start_u, r.tM2), (end_u, end_w),
                                           self.r.p["wave"], r.tM2, r.tO)
        pts = []
        for u, w in z:
            if abs(w - r.tM2) < 1e-6:
                for lo, hi in bumps:
                    if lo - 2.5 * bd < u < hi + 2.5 * bd:
                        u, w = min(max(u, lo + bd), hi - bd), top
                        break
            if pts and u < pts[-1][0] - 1e-6:
                continue
            pts.append((u, w))
        return pts

    def _long(self):
        r, bd = self.r, self.b
        eS, eF = self.eS, self.eF
        c = lambda ln, w: _ux(ln, w, bd / 2.0)          # end wall centreline at w
        wO = r.wO[0]
        P = [(c(eS, r.wI), r.wI), (c(eF, r.wI), r.wI), (c(eF, wO), wO), (c(eS, wO), wO), (c(eS, r.tI), r.tI)]
        rib = self._rib_pass((c(eS, r.tI), r.tI), _shift(eF, bd / 2.0), r.tM)
        P += rib[1:]
        u_end = rib[-1][0]
        P += self._m_rail_back(u_end, _ux(eS, r.wM, 1.5 * bd))
        u0 = _ux(eS, r.tM2, 1.5 * bd)
        P += self._lattice(u0, _ux(eF, r.tO, 1.5 * bd), _shift(eF, bd / 2.0), r.tO)
        return _clean(P)

    def _hip(self):
        """hip channel at F (mitre), closed end wall at S"""
        r, bd = self.r, self.b
        eS, eF = self.eS, self.eF
        c = lambda ln, w: _ux(ln, w, bd / 2.0)
        wO = r.wO[0]
        WLh = self.hipF - bd / 2.0
        # 1 lattice web S -> F, ending above the hip channel wall
        lat = self._lattice(_ux(eS, r.tM2, 1.5 * bd), WLh - bd, _right(WLh), r.tM2)
        if abs(lat[-1][1] - r.tM2) > 1e-6:
            lat.append((WLh - bd, r.tM2))
        P = lat
        # 2 middle bead F -> S, stepping out over the channels
        P += self._m_rail_back(WLh - bd, _ux(eS, r.wM, 1.5 * bd))
        # 3 rib zone S -> F, ending at the hip channel wall foot
        start = (_ux(eS, r.tM, 1.5 * bd), r.tM)
        P += self._rib_pass(start, None, None)
        # up the hip channel wall, middle bead to the mitre, mitre wall (lattice zone), outer bead, near end wall,
        # inner bead to the mitre
        P += [(WLh, r.wM), (c(eF, r.wM), r.wM), (c(eF, wO), wO), (c(eS, wO), wO), (c(eS, r.wI), r.wI),
              (c(eF, r.wI), r.wI)]
        return _clean(P)

    def _band(self):
        """inside a ring band: the rib zone is an open trough; end walls only across the lattice zone"""
        r, bd = self.r, self.b
        eS, eF = self.eS, self.eF
        c = lambda ln, w: _ux(ln, w, bd / 2.0)
        wO = r.wO[0]
        A = [(c(eS, r.wM), r.wM), (c(eF, r.wM), r.wM), (c(eF, wO), wO), (c(eS, wO), wO), (c(eS, r.tM2), r.tM2)]
        A += self._lattice(_ux(eS, r.tM2, 1.5 * bd), _ux(eF, r.tO, 1.5 * bd), _shift(eF, bd / 2.0), r.tO)
        B = [(c(eF, r.wI), r.wI), (c(eS, r.wI), r.wI)]
        return [_clean(A), _clean(B)]


def _shift(ln, inset):
    a, c, d = ln
    return (a, c, d - inset)


def _clean(P):
    out = []
    for q in P:
        if not out or math.hypot(q[0] - out[-1][0], q[1] - out[-1][1]) > 0.5:
            out.append(q)
    return out


# ===================================== the whole roof =====================================
def build(p, lines, ids, centre=(0.0, 0.0), paths=False):
    roof = Roof(p, centre)
    rb = map_ribs(roof, lines, ids)
    cs, bands, warn = courses(roof, rb["ring_v"])
    rnd = random.Random(int(p["seed"]))
    b = p["bead"]
    pieces = []
    for k in range(4):
        below = []
        for ci, (v0, v1) in enumerate(cs):
            tag = "{}-{}-C{:02d}".format(p["module"], FACE[k], ci + 1)
            js = lay_joints(roof, rb["segs"], k, v0, v1, below, rnd, warn, tag)
            below = js
            ends = [None] + js + [None]
            for i in range(len(ends) - 1):
                kind = "H1" if i == 0 else "H2" if i == len(ends) - 2 else "{:02d}".format(i)
                pieces.append(dict(id="{}-{}".format(tag, kind), k=k, c=ci, v0=v0, v1=v1, uS=ends[i], uF=ends[i + 1]))
    res = dict(roof=roof, ribs=rb, courses=cs, bands=bands, pieces=pieces, warn=warn)
    if paths:
        for pc in pieces:
            pc["layers"] = piece_layers(roof, rb["segs"], bands, pc)
    return res


def end_lines(roof, pc, v):
    eS = _left(pc["uS"]) if pc["uS"] is not None else roof.mitre_line(pc["k"], -1, v)
    eF = _right(pc["uF"]) if pc["uF"] is not None else roof.mitre_line(pc["k"], 1, v)
    return eS, eF


def piece_layers(roof, segs, bands, pc):
    p = roof.p
    n_l = max(1, int(round((pc["v1"] - pc["v0"]) / p["layer_H"])))
    lh = (pc["v1"] - pc["v0"]) / n_l
    out = []
    for li in range(n_l):
        vm = pc["v0"] + (li + 0.5) * lh
        band = any(lo <= vm <= hi for lo, hi, _ in bands)
        eS, eF = end_lines(roof, pc, vm)
        L = Layer(roof, segs, pc["k"], vm, eS, eF, band, pc["uS"] is None, pc["uF"] is None)
        cons = L.path()
        if li % 2:                                   # every other layer runs backwards: it starts where the last ended
            cons = [list(reversed(cn)) for cn in reversed(cons)]
        out.append(dict(v=pc["v0"] + (li + 1) * lh, lh=lh, contours=cons, band=band, warn=L.warn))
    return out


def piece_check(roof, pc):
    p = roof.p
    b = p["bead"]
    worst_t, sharp, short, n2 = 1e9, 180.0, 1e9, 0
    length = vol = 0.0
    for ly in pc["layers"]:
        Lsum = 0.0
        if len(ly["contours"]) > 1:
            n2 += 1
        for cn in ly["contours"]:
            segs = [math.hypot(q[0] - p_[0], q[1] - p_[1]) for p_, q in zip(cn, cn[1:])]
            Lsum += sum(segs)
            if segs:
                short = min(short, min(segs))
            sharp = min(sharp, _sharpest(cn))
        worst_t = min(worst_t, Lsum / p["speed"])
        length += Lsum
        vol += Lsum * b * ly["lh"]
    red, amber = [], []
    if worst_t < p["min_layer_t"]:
        red.append("layer only {:.0f} s".format(worst_t))
    elif worst_t < 1.5 * p["min_layer_t"]:
        amber.append("layer {:.0f} s".format(worst_t))
    if sharp < 30.0:
        amber.append("{:.0f} deg corner".format(sharp))
    if short < b / 2.0:
        amber.append("{:.0f} mm segment".format(short))
    pc.update(mass=vol * p["density"] / 1e6, vol=vol, print_s=length / p["speed"], n2=n2,
              rating="RED" if red else "AMBER" if amber else "OK", why=red + amber)
    return pc


def _sharpest(P):
    best = 180.0
    for a, b, c in zip(P, P[1:], P[2:]):
        v1 = (a[0] - b[0], a[1] - b[1])
        v2 = (c[0] - b[0], c[1] - b[1])
        l1, l2 = math.hypot(*v1), math.hypot(*v2)
        if l1 < 1e-6 or l2 < 1e-6:
            continue
        cosang = max(-1.0, min(1.0, (v1[0] * v2[0] + v1[1] * v2[1]) / (l1 * l2)))
        best = min(best, math.degrees(math.acos(cosang)))
    return best


def rib_solids(roof, rb, bands):
    """the cast concrete, in face coordinates: list of (name, k, polygon in (u, v), w0, w1, trims) where trims are
    the mitre sides that cut the solid ((k, side) planes)"""
    p = roof.p
    w0, w1 = p["bead"], p["bead"] + p["rib_d"]
    big = roof.hx + roof.hy + 2 * roof.T
    out = []
    for k in range(4):
        for i, s in enumerate(_chains(rb["segs"][k])):
            (u1, v1), (u2, v2) = s["a"], s["b"]
            if v2 < roof.v_s:
                continue
            if v1 < roof.v_s:                         # the cast base starts there
                f = (roof.v_s - v1) / (v2 - v1)
                u1, v1 = u1 + f * (u2 - u1), roof.v_s
            if v2 > roof.v_top:
                f = (roof.v_top - v1) / (v2 - v1)
                u2, v2 = u1 + f * (u2 - u1), roof.v_top
            ev = abs(v2 - v1) / math.hypot(u2 - u1, v2 - v1)
            hw = p["rib_w"] / 2.0 / max(ev, 0.2)
            if s["hip"] > 0:      # half hip: from the side line out past the mitre
                poly = [(u1 - hw, v1), (u1 + big, v1), (u2 + big, v2), (u2 - hw, v2)]
                trims = [(k, 1)]
                name = "hip {}{}".format(FACE[k], FACE[(k + 1) % 4])
            elif s["hip"] < 0:
                poly = [(u1 - big, v1), (u1 + hw, v1), (u2 + hw, v2), (u2 - big, v2)]
                trims = [(k, -1)]
                name = "hip {}{}".format(FACE[(k - 1) % 4], FACE[k])
            else:
                poly = [(u1 - hw, v1), (u1 + hw, v1), (u2 + hw, v2), (u2 - hw, v2)]
                trims = []
                name = "{} {}".format(s["id"], FACE[k])
            out.append(dict(name=name, k=k, poly=poly, w0=w0, w1=w1, trims=trims, axis=((u1, v1), (u2, v2))))
        for lo, hi, kind in bands:
            hi = min(hi, roof.v_top)
            out.append(dict(name="{} {} +{:.0f}".format(kind, FACE[k], (lo + hi) / 2), k=k,
                            poly=[(-big, lo), (big, lo), (big, hi), (-big, hi)], w0=w0, w1=w1,
                            trims=[(k, 1), (k, -1)], axis=None))
    return out


def _chains(segs):
    """join consecutive collinear rib segments into straight ribs"""
    left = sorted(segs, key=lambda s: (s["hip"], s["id"], s["v1"]))
    out = []
    for s in left:
        a, b = (s["u1"], s["v1"]), (s["u2"], s["v2"])
        if out:
            q = out[-1]
            d1 = _norm((q["b"][0] - q["a"][0], q["b"][1] - q["a"][1]))
            d2 = _norm((b[0] - a[0], b[1] - a[1]))
            if q["hip"] == s["hip"] and q["id"] == s["id"] and math.hypot(a[0] - q["b"][0], a[1] - q["b"][1]) < 1.0 \
                    and _dot(d1, d2) > 0.99999:
                q["b"] = b
                continue
        out.append(dict(a=a, b=b, hip=s["hip"], id=s["id"]))
    return out


def summary(res):
    roof, p = res["roof"], res["roof"].p
    pcs = res["pieces"]
    rb = res["ribs"]
    n_ch = sum(len(v) for v in rb["segs"].values())
    lines = ["module {}: clear {:.0f} x {:.0f}, slope {:.1f} deg, rise {:.0f}, build-up {:.0f} square to the slope".format(
        p["module"], 2 * roof.hx, 2 * roof.hy, roof.slope, roof.rise, roof.T),
        "ribs from Karamba: {} lines in, {} used ({} rib segments, {} horizontal rings at v {}), {} outside this module".format(
            rb["n_in"], rb["n_used"], n_ch, len(rb["ring_v"]), ", ".join("{:.0f}".format(v) for v in rb["ring_v"]) or "-",
            rb["skipped"]),
        "{} courses square to the slope ({:.0f} - {:.0f} along the slope), {} pieces ({} hip pieces)".format(
            len(res["courses"]), min(b - a for a, b in res["courses"]), max(b - a for a, b in res["courses"]),
            len(pcs), sum(1 for x in pcs if x["uS"] is None or x["uF"] is None))]
    longs = [x for x in pcs if x["uS"] is not None and x["uF"] is not None]
    if longs:
        ls = [x["uF"] - x["uS"] for x in longs]
        lines.append("long pieces {:.0f} - {:.0f} mm".format(min(ls), max(ls)))
    if pcs and "mass" in pcs[0]:
        ms = [x["mass"] for x in pcs]
        tot = sum(x["vol"] for x in pcs) / 1e9
        lines.append("printed: {:.2f} m3 = {:.1f} t; heaviest piece {:.0f} kg, mean {:.0f} kg".format(
            tot, tot * p["density"], max(ms), sum(ms) / len(ms)))
        rat = {"OK": 0, "AMBER": 0, "RED": 0}
        for x in pcs:
            rat[x["rating"]] += 1
        lines.append("check: {OK} OK, {AMBER} AMBER, {RED} RED (at {sp:.0f} mm/s, min layer {mt:.0f} s)".format(
            sp=p["speed"], mt=p["min_layer_t"], **rat))
        n2 = sum(x["n2"] for x in pcs)
        if n2:
            lines.append("{} ring-band layers print the inner bead as a second contour (one stop per layer)".format(n2))
    if int(p["outer_beads"]) > 1:
        lines.append("WARNING: outer_beads > 1: only the outermost outer bead is in the path")
    if p["rib_d"] < 200 and res["bands"]:
        lines.append("note: the crown ring is cast in the rib zone of the top course: {:.0f} wide x {:.0f} deep "
                     "(karamba crown_b x crown_h should match)".format(p["crown_b"], p["rib_d"]))
    lines += ["WARNING: " + w for w in res["warn"][:12]]
    return "\n".join(lines)


# ===================================== Grasshopper glue =====================================
def _gh_main():
    import Rhino
    import Rhino.Geometry as rg
    from Grasshopper import DataTree
    from Grasshopper.Kernel.Data import GH_Path
    G = globals()
    p = dict(DEFAULTS)
    p.update({k: G[k] for k in DEFAULTS if G.get(k) is not None})
    doc = Rhino.RhinoDoc.ActiveDoc
    tol = doc.ModelAbsoluteTolerance if doc else 0.01
    cen = G.get("centre")
    centre = (cen.X, cen.Y) if cen is not None else (0.0, 0.0)
    lines = []
    for ln in G.get("rib_lines") or []:
        if hasattr(ln, "From"):
            a, b = ln.From, ln.To
        else:
            a, b = ln.PointAtStart, ln.PointAtEnd
        lines.append(((a.X, a.Y, a.Z), (b.X, b.Y, b.Z)))
    pick = str(G.get("piece") or "").strip()
    paths = bool(G.get("print_paths") or False)
    solids = G.get("solids")
    solids = True if solids is None else bool(solids)
    out = dict(blocks=DataTree[object](), ids=DataTree[object](), tags=DataTree[object](), cutlist=[], ribs=[],
               rib_names=[], rib_axes=[], toolpaths=DataTree[object](), beads=DataTree[object](),
               to_print=DataTree[object](), check=[], piece_paths=[], piece_beads=None,
               piece_check="no piece picked" if not pick else "{} not found".format(pick))
    try:
        res = build(p, lines, G.get("rib_ids"), centre, paths=paths)
    except ValueError as e:
        out["info"] = "ERROR: {}".format(e)
        G.update(out)
        return
    roof = res["roof"]
    P3 = lambda q: rg.Point3d(*q)

    def fplane(k, w):
        f = roof.faces[k]
        o = roof.world(k, 0.0, 0.0, w)
        return rg.Plane(P3(o), rg.Vector3d(*f["U"]), rg.Vector3d(*f["V"]))

    def prism(k, poly, w0, w1):
        f = roof.faces[k]
        crv = rg.PolylineCurve([P3(roof.world(k, u, v, w0)) for u, v in poly + [poly[0]]])
        srf = rg.Surface.CreateExtrusion(crv, rg.Vector3d(*f["N"]) * (w1 - w0))
        br = srf.ToBrep().CapPlanarHoles(tol)
        if br and br.SolidOrientation == rg.BrepSolidOrientation.Inward:
            br.Flip()
        return br

    def trim(br, k, side):
        a, b, c, d = roof.mitres[k, side]
        f = roof.faces[k]
        nrm = tuple(a * f["U"][i] + b * f["V"][i] + c * f["N"][i] for i in range(3))   # outward (discarded) side
        L = math.sqrt(_dot(nrm, nrm))
        # a point on the plane: along the normal from the frame origin
        o = tuple(f["O"][i] + nrm[i] / L * (d / L) for i in range(3))
        pl = rg.Plane(P3(o), rg.Vector3d(*nrm))
        parts = br.Trim(pl, tol)
        if not parts:
            return br
        cut = parts[0].CapPlanarHoles(tol)
        return cut or parts[0]

    v_eps = 2.0
    counter = {}
    for pc in res["pieces"]:
        k, v0, v1 = pc["k"], pc["v0"], pc["v1"]
        path = GH_Path(k, pc["c"])
        big = roof.T * 3 + 500.0
        uS = pc["uS"] if pc["uS"] is not None else roof.mitre_u(k, -1, v0, 0.0) - big
        uF = pc["uF"] if pc["uF"] is not None else roof.mitre_u(k, 1, v0, 0.0) + big
        br = prism(k, [(uS, v0), (uF, v0), (uF, v1), (uS, v1)], 0.0, roof.T)
        if pc["uS"] is None:
            br = trim(br, k, -1)
        if pc["uF"] is None:
            br = trim(br, k, 1)
        if solids and br:
            cut = []
            w0, w1 = p["bead"], p["bead"] + p["rib_d"]
            for s in res["ribs"]["segs"][k]:
                lo_v, hi_v = max(v0 - v_eps, s["v1"]), min(v1 + v_eps, s["v2"])
                if hi_v - lo_v < 1.0:
                    continue
                for (va, vb) in ((lo_v, hi_v),):
                    ra, ha = channels_one(roof, s, va)
                    rb_, hb = channels_one(roof, s, vb)
                    if s["hip"] > 0:
                        poly = [(ra - ha, va), (ra + big, va), (rb_ + big, vb), (rb_ - hb, vb)]
                    elif s["hip"] < 0:
                        poly = [(ra - big, va), (ra + ha, va), (rb_ + hb, vb), (rb_ - big, vb)]
                    else:
                        poly = [(ra - ha, va), (ra + ha, va), (rb_ + hb, vb), (rb_ - hb, vb)]
                    us = [q[0] for q in poly]
                    if max(us) < uS - 1 or min(us) > uF + 1:
                        continue
                    cc = prism(k, poly, w0, w1)
                    if cc:
                        cut.append(cc)
            for lo, hi, kind in res["bands"]:
                lo_v, hi_v = max(lo, v0 - v_eps), min(hi, v1)
                if hi_v - lo_v < 1.0:
                    continue
                if hi_v >= v1 - 1.0:
                    hi_v = v1 + v_eps
                cc = prism(k, [(uS - 50, lo_v), (uF + 50, lo_v), (uF + 50, hi_v), (uS - 50, hi_v)], w0, w1)
                if cc:
                    cut.append(cc)
            if cut:
                d = rg.Brep.CreateBooleanDifference([br], cut, tol)
                if d and len(d) == 1:
                    br = d[0]
                else:
                    res["warn"].append("{}: channel cut failed, block left solid".format(pc["id"]))
        out["blocks"].Add(br, path)
        out["ids"].Add(pc["id"], path)
        um = ((pc["uS"] if pc["uS"] is not None else roof.mitre_u(k, -1, v1, 0.0)) +
              (pc["uF"] if pc["uF"] is not None else roof.mitre_u(k, 1, v1, 0.0))) / 2.0
        out["tags"].Add(P3(roof.world(k, um, (v0 + v1) / 2.0, roof.T)), path)
        # print frame: origin at the piece's (uS, v0, 0), z = up the slope
        u_ref = pc["uS"] if pc["uS"] is not None else roof.mitre_u(k, -1, v0, roof.T)
        f = roof.faces[k]
        Uv, Vv = rg.Vector3d(*f["U"]), rg.Vector3d(*f["V"])
        Yv = rg.Vector3d.CrossProduct(Vv, Uv)
        situ = rg.Plane(P3(roof.world(k, u_ref, v0, 0.0)), Uv, Yv)
        xf = rg.Transform.PlaneToPlane(situ, rg.Plane.WorldXY)
        out["to_print"].Add(xf, path)
        picked = pc["id"] == pick
        if paths:
            piece_check(roof, pc)
            n_in = counter.get((k, pc["c"]), 0)
            counter[k, pc["c"]] = n_in + 1
            ppath = GH_Path(k, pc["c"], n_in)
            mesh = rg.Mesh()
            for ly in pc["layers"]:
                for cn in ly["contours"]:
                    pts = [P3(roof.world(k, u, ly["v"], w)) for u, w in cn]
                    crv = rg.PolylineCurve(pts)
                    crv.Transform(xf)
                    out["toolpaths"].Add(crv, ppath)
                    if picked:
                        out["piece_paths"].append(crv)
                    flat = [rg.Point3d(q.X, q.Y, q.Z) for q in crv.ToPolyline()]
                    bm = _bead_mesh(rg, flat, ly["v"] - v0 - ly["lh"] / 2.0, p["bead"], ly["lh"])
                    if bm:
                        mesh.Append(bm)
            mesh.Normals.ComputeNormals()
            mesh.Compact()
            if picked:
                out["piece_beads"] = mesh.DuplicateMesh()
            inv = xf.TryGetInverse()[1]
            mesh.Transform(inv)
            out["beads"].Add(mesh, path)
            line = "{}  {}  {}".format(pc["id"], pc["rating"], " | ".join(pc["why"])).rstrip()
            if pc["rating"] != "OK":
                out["check"].append(line)
            if picked:
                out["piece_check"] = line
            out["cutlist"].append("{}  {:.0f} kg, {} layers, {:.0f} min print".format(
                pc["id"], pc["mass"], len(pc["layers"]), pc["print_s"] / 60.0))
        else:
            out["cutlist"].append("{}  {:.0f} long at the room face".format(
                pc["id"], (pc["uF"] if pc["uF"] is not None else roof.mitre_u(k, 1, v1, 0.0)) -
                (pc["uS"] if pc["uS"] is not None else roof.mitre_u(k, -1, v1, 0.0))))
            if picked:
                out["piece_check"] = "{}: turn print_paths on for paths and the check".format(pick)
    for rs in rib_solids(roof, res["ribs"], res["bands"]):
        br = prism(rs["k"], rs["poly"], rs["w0"], rs["w1"])
        for k_, side in rs["trims"]:
            br = trim(br, k_, side)
        if br:
            out["ribs"].append(br)
            out["rib_names"].append(rs["name"])
        if rs["axis"]:
            (ua, va), (ub, vb) = rs["axis"]
            out["rib_axes"].append(rg.Line(P3(roof.world(rs["k"], ua, va, roof.c_rib)),
                                           P3(roof.world(rs["k"], ub, vb, roof.c_rib))))
    out["info"] = summary(res)
    G.update(out)


def channels_one(roof, s, v):
    """centre u and half width (in u) of one rib segment at v (extrapolated past its ends)"""
    f = (v - s["v1"]) / (s["v2"] - s["v1"])
    uc = s["u1"] + f * (s["u2"] - s["u1"])
    du, dv = s["u2"] - s["u1"], s["v2"] - s["v1"]
    ev = abs(dv) / math.hypot(du, dv)
    return uc, roof.p["rib_w"] / 2.0 / max(ev, 0.2)


def _bead_mesh(rg, pts, z_mid, width, height, seg=3):
    """printed bead along a horizontal polyline: flat top / bottom, round sides (as cork_house_roof.py)"""
    r = min(width, height) / 2.0
    cx = width / 2.0 - r
    prof = [(cx + r * math.cos(-math.pi / 2 + math.pi * i / seg), height / 2.0 * math.sin(-math.pi / 2 + math.pi * i / seg))
            for i in range(seg + 1)]
    prof += [(-cx + r * math.cos(math.pi / 2 + math.pi * i / seg), height / 2.0 * math.sin(math.pi / 2 + math.pi * i / seg))
             for i in range(seg + 1)]
    n, P = len(pts), len(prof)
    if n < 2:
        return None

    def unit(a, b):
        dx, dy = b.X - a.X, b.Y - a.Y
        L = math.hypot(dx, dy) or 1.0
        return dx / L, dy / L

    m = rg.Mesh()
    for i in range(n):
        if 0 < i < n - 1:
            t1, t2 = unit(pts[i - 1], pts[i]), unit(pts[i], pts[i + 1])
            sx, sy = t1[1] + t2[1], -t1[0] - t2[0]
            L = math.hypot(sx, sy)
            if L < 1e-6:
                sx, sy, L = t1[1], -t1[0], 1.0
            sx, sy = sx / L, sy / L
            scale = 1.0 / max(0.35, sx * t1[1] - sy * t1[0])
        else:
            t = unit(pts[i - 1], pts[i]) if i else unit(pts[i], pts[i + 1])
            sx, sy, scale = t[1], -t[0], 1.0
        for s, v in prof:
            m.Vertices.Add(pts[i].X + sx * s * scale, pts[i].Y + sy * s * scale, z_mid + v)
    for i in range(n - 1):
        for k in range(P):
            k2 = (k + 1) % P
            m.Faces.AddFace(i * P + k, (i + 1) * P + k, (i + 1) * P + k2, i * P + k2)
    m.Normals.ComputeNormals()
    return m


# ===================================== self-test (no Rhino) =====================================
def _selftest():
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import karamba_model as km
    for grid, kw in (("A", dict(n_cols=4)), ("A", {}), ("B", {})):
        m = km.build_model(grid=grid, **kw)
        lines = [(a, b) for a, b, _ in m["ribs"]]
        ids = [r for _, _, r in m["ribs"]]
        p = dict(DEFAULTS)
        res = build(p, lines, ids, paths=True)
        bad, rep = 0, []
        for pc in res["pieces"]:
            piece_check(res["roof"], pc)
            bad += _overlaps(res["roof"], pc, rep)
        print("grid {} {}".format(grid, kw))
        print(summary(res))
        heavy = sorted(res["pieces"], key=lambda x: -x["mass"])[:3]
        print("heaviest: " + ", ".join("{} {:.0f} kg".format(x["id"], x["mass"]) for x in heavy))
        print("layers with beads printed twice: {} of {}".format(bad, sum(len(x["layers"]) for x in res["pieces"])))
        for r in rep:
            print("   ", r[0], "layer", r[1], "gap {:.1f}".format(r[2][0]),
                  [tuple(int(round(c)) for c in q) for q in r[2][1]], [tuple(int(round(c)) for c in q) for q in r[2][2]])
        print()


def _overlaps(roof, pc, report=None):
    """count layers where two beads that are far apart along the path come closer than a bead width (printed twice)"""
    try:
        from shapely.geometry import LineString
    except ImportError:
        return 0
    b = roof.p["bead"]
    bad = 0
    for li, ly in enumerate(pc["layers"]):
        segs = []                                     # (geometry, path distance at start, contour)
        for ci, cn in enumerate(ly["contours"]):
            s = 0.0
            for p_, q in zip(cn, cn[1:]):
                L = math.hypot(q[0] - p_[0], q[1] - p_[1])
                segs.append((LineString([p_, q]), s, s + L, ci))
                s += L
        hit = None
        for i in range(len(segs)):
            for j in range(i + 1, len(segs)):
                gi, a0, a1, ci = segs[i]
                gj, b0, b1, cj = segs[j]
                if ci == cj and b0 - a1 < 1.6 * b:     # neighbours along the path: their corner is fine
                    continue
                d = gi.distance(gj)
                if d < b - 1.0:
                    hit = (d, list(gi.coords), list(gj.coords))
                    break
            if hit:
                break
        if hit:
            bad += 1
            if report is not None and len(report) < 8:
                report.append((pc["id"], li, hit))
    return bad


if __name__ == "__main__":
    try:
        import Rhino  # noqa
        _gh_main()
    except ImportError:
        _selftest()
else:
    try:
        import Rhino  # noqa
        _gh_main()
    except ImportError:
        pass
