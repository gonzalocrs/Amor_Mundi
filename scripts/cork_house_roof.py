"""Corbelled pyramid roof - hollow, lapped, 3D-printed pieces
(after Cork House, Eton 2019 - rooflight left out)

The roof is a sloped shell cut into horizontal courses. Thickness (measured
horizontally, like the print) tapers from t_bottom at the eaves to t_top at the opening.

Every piece is HOLLOW and open top and bottom: a room-side wall, an outside wall,
end walls and cross ribs, all `wall` thick (horizontal, i.e. print width).

By default (lap = 0) courses simply stack on flat bed joints and the rebar ties them.
With lap > 0, courses also hook into each other by offsetting the walls:
  - room-side wall: runs the full course height
  - outside wall: shifted down by the lap depth - it hangs below the course line
    as a nose and stops short at the top, so the bed joints of the two walls
    sit at different heights
  - ribs + end walls hang down into the lap band too, 1.5 mm clear of the
    room-side wall of the course below - this stops the piece sliding inward
In plan: small mitred corner piece at each end of every side + long pieces of
random length in between, all butt-jointed, staggered against the course below.

Section of one piece (w = outward, z = up):

          |  |                <- room-side wall continues to the course line
          |  |    |  |        <- outside wall stops lap-depth lower
          |  |....|  |           (cavity between, open top and bottom)
          |__|....|  |
             |rib |  |        <- rib + outside wall hang down into the band below
                  |__|

Paste into a GhPython component (Rhino 7) or a Python 3 Script component (Rhino 8).
Units: millimetres.

INPUTS  (only `rooms` is required - add the others as sliders when you want them)
    rooms        list  Rectangle3d  room-side face of the roof at its base, one per room
    piece_min    item  float        shortest long piece                    (default 1200)
    piece_max    item  float        longest long piece                     (default 2000)
    hip_L        item  float        corner piece length at the room-side face (default 300)
    course_H     item  float        course height                          (default 300)
    step         item  float        inward step per course (sets pitch)    (default 150)
    t_bottom     item  float        thickness at the bottom course         (default 300)
    t_top        item  float        thickness at the top course            (default 100)
    lap          item  float        lap depth as a share of thickness, 0 = flat bed joints (default 0)
    wall         item  float        wall / rib thickness (print width)     (default 20)
    rib_spacing  item  float        target spacing of cross ribs           (default 500)
    hollow       item  bool         False = solid pieces, fast preview     (default True)
    print_paths  item  bool         True = build print paths + bead preview (default False)
    layer_H      item  float        print layer height                     (default 15)
    speed        item  float        print speed in mm/s, for the check     (default 100)
    min_layer_t  item  float        shortest safe layer time in s          (default 30)
    piece        item  str          piece id to pick out, e.g. R0-C3-W-02  (default none)
    rebar        item  bool         leave holes for rebar + model the bars  (default True)
    bar_spacing  item  float        bar spacing along each row of bars     (default 500)
    bar_d        item  float        bar diameter                           (default 12)
    hole_d       item  float        printed hole diameter                  (default 30)
    min_open     item  float        stop when the top opening < this       (default 1000)
    max_courses  item  int          hard cap on courses                    (default 60)
    min_stagger  item  float        min offset from joints below           (default 250)
    seed         item  int          change for a different layout          (default 1)

OUTPUTS
    blocks       pieces as Breps, tree {room; course}
    ids          piece id per piece, same tree (H1/H2 = corner pieces)
    tags         label point per piece, same tree
    cutlist      print schedule: id, length at mid-thickness, thickness
    info         summary + warnings
    toolpaths    print path per layer, tree {room; course; piece} - one branch = one piece,
                 layers in print order, each starting where the last one ended
                 (feed a branch to SaladSlicer: Join Open Contours -> Curve Slicer -> Program Generator)
    beads        printed bead preview, ONE mesh per piece, tree {room; course} - same order
                 as blocks / ids, so item i of a branch is the same piece in all three
    check        printability rating of every piece that isn't OK (RED / AMBER + reasons)
    piece_paths  layer paths of the picked `piece` - wire straight into Join Open Contours
    piece_beads  bead preview of the picked `piece`, one mesh
    piece_check  rating of the picked `piece`
    rebar        the bars as Breps, tree {room}
    rebar_list   bar schedule: id, length

REBAR (rebar = True)
Bars follow the slope of each face (straight, inside the shell), in two rows: one a bead
in from the room-side wall, one a bead in from the outside wall, staggered by half a
spacing. The zig-zag touches alternate walls exactly at the bars, in every course, and
loops around each bar in an arc - the wall on one side and the arc on the other enclose
the hole with one bead of concrete all round. Piece joints are moved to fall between bars.
A bar runs up as long as every course has its hole: it stops where the piece gets too
thin (3 beads + hole) or where it runs into a corner. Needs print_paths for the holes;
the bars are modelled either way. With rebar on, bar_spacing replaces rib_spacing.

PRINTABILITY CHECK (per piece, needs print_paths)
  RED   - a layer prints faster than min_layer_t (concrete below hasn't stiffened)
        - lap stub: the room-side-wall-only band is shorter than 3 beads
  AMBER - a layer within 1.5 x min_layer_t
        - a corner sharper than 60 deg, or a segment shorter than one bead
  The lean of the walls (step / course_H) is the same for every piece - see info.

PRINT PATHS (print_paths = True)
Bead width = `wall`. Every layer is one continuous path, nothing printed twice:
room-side wall -> far end wall -> outside wall back -> start end wall -> zig-zag
through the cavity, touching both walls bead-to-bead. In the hanging lap band
the path is outside wall + end walls + zig-zag; in the top band, room-side wall only.
`rib_spacing` = zig-zag pitch. Where the cavity is too narrow for a zig-zag the
layer is a plain closed loop. Layer height is adjusted per piece so whole layers fit.
"""
import math
import random
import Rhino
import Rhino.Geometry as rg
from Grasshopper import DataTree
from Grasshopper.Kernel.Data import GH_Path


def _d(name, default):
    """Optional input: works whether or not the input exists on the component."""
    v = globals().get(name)
    return default if v is None else v


P_MIN = float(_d('piece_min', 1200.0))
P_MAX = float(_d('piece_max', 2000.0))
HIP = float(_d('hip_L', 300.0))
H = float(_d('course_H', 300.0))
S = float(_d('step', 150.0))
T0 = float(_d('t_bottom', 300.0))
T1 = float(_d('t_top', 100.0))
LAP = float(_d('lap', 0.0))
W = float(_d('wall', 20.0))
RIB = float(_d('rib_spacing', 500.0))
HOLLOW = bool(_d('hollow', True))
PATHS = bool(_d('print_paths', False))
LH = float(_d('layer_H', 15.0))
SPEED = float(_d('speed', 100.0))
MIN_T = float(_d('min_layer_t', 30.0))
PICK = str(_d('piece', '')).strip()
REBAR = bool(_d('rebar', True))
BAR_SP = float(_d('bar_spacing', 500.0))
BAR_D = float(_d('bar_d', 12.0))
HOLE_D = float(_d('hole_d', 30.0))
MIN_OPEN = float(_d('min_open', 1000.0))
MAX_C = int(_d('max_courses', 60))
STAGGER = float(_d('min_stagger', 250.0))
SEED = int(_d('seed', 1))
CLR = 1.5      # print clearance between the hanging ribs and the wall below
EPS = 1.0      # cavity cutters overshoot the open top / bottom
NUDGE = 0.05   # keeps cutter faces off the room-side wall's face (no coplanar booleans)
MIN_CAV = 3.0  # narrower than this and the piece is printed solid
SQ2 = math.sqrt(2.0)

K = S / H                                  # inward run per unit of height

R_H = HOLE_D / 2.0                         # rebar hole radius
RA = R_H + W / 2.0                         # radius of the bead arc around a hole (centreline)
T_NEED = 3 * W + HOLE_D                    # thinnest piece that fits wall + hole + arc + wall

doc = Rhino.RhinoDoc.ActiveDoc
TOL = doc.ModelAbsoluteTolerance if doc else 0.01
rnd = random.Random(SEED)


def xy(u, v, d):
    """Run coordinates (u along the side, v across it) to plane x, y."""
    return (u, v) if d == 'x' else (v, u)


def const(u):
    return lambda w: u


def mitre_a(ua, off):
    """Hip at the start of a side: u moves out with w (45 deg), `off` = inset along u."""
    return lambda w: ua - w + off


def mitre_b(ub, off):
    return lambda w: ub + w - off


def lay_run(a, b, below):
    """Joints splitting [a, b] into pieces between P_MIN and P_MAX, clear of the joints below."""
    length = b - a
    if length <= P_MAX:
        return []
    n_lo = int(math.ceil(length / P_MAX))
    n_hi = max(n_lo, int(length // P_MIN))
    n = min(max(int(round(length / ((P_MIN + P_MAX) / 2.0))), n_lo), n_hi)
    joints = []
    pos = a
    for i in range(n - 1):
        m = n - i
        rest = b - pos
        lo = max(P_MIN, rest - (m - 1) * P_MAX)
        hi = min(P_MAX, rest - (m - 1) * P_MIN)
        if lo > hi:  # can't keep every piece in range: share the run evenly
            lo = hi = rest / m
        best, best_d = pos + lo, -1.0
        for _ in range(30):
            j = pos + rnd.uniform(lo, hi)
            dmin = min([abs(j - q) for q in below] or [1e9])
            if dmin >= STAGGER:
                best = j
                break
            if dmin > best_d:
                best, best_d = j, dmin
        joints.append(best)
        pos = best
    return joints


def ruled(pl, d, face, out, section, fa, fb):
    """Sweep a (w, z) section along the side between u = fa(w) and u = fb(w).
    Built from planar faces - no booleans. Returns None if it can't close."""
    def pt(u, w, z):
        x, y = xy(u, face + out * w, d)
        return pl.PointAt(x, y, z)

    if any(fb(w) - fa(w) < 1.0 for w, z in section):
        return None
    A = [pt(fa(w), w, z) for w, z in section]
    B = [pt(fb(w), w, z) for w, z in section]
    loops = [A + [A[0]], B + [B[0]]]
    n = len(section)
    for i in range(n):
        j = (i + 1) % n
        loops.append([A[i], A[j], B[j], B[i], A[i]])
    faces = []
    for loop in loops:
        f = rg.Brep.CreatePlanarBreps(rg.PolylineCurve(loop), TOL)
        if f:
            faces.extend(f)
    joined = rg.Brep.JoinBreps(faces, TOL)
    if not joined or len(joined) != 1 or not joined[0].IsSolid:
        return None
    brep = joined[0]
    if brep.SolidOrientation == rg.BrepSolidOrientation.Inward:
        brep.Flip()
    return brep


def cells_between(a, b):
    """Split the inside of a butt-jointed piece [a, b] into cells between ribs."""
    inside = b - a - 2 * W
    n = max(1, int(round(inside / RIB)))
    cell = (inside - (n - 1) * W) / n
    out = []
    u = a + W
    for _ in range(n):
        out.append((const(u), const(u + cell)))
        u += cell + W
    return out


def zigzag(u_s, u_e, w_a, w_b, ea, eb):
    """Zig-zag from u_s to u_e, alternating between the lines w_a and w_b (first vertex on w_a).
    Vertices stay a bead clear of the end walls (ea / eb = end wall centrelines).
    Returns None if it doesn't fit: under one full tooth, or a leg shorter than a bead,
    or a leg that would run backwards against the end walls."""
    if abs(u_e - u_s) < RIB:
        return None
    m = max(2, int(round(abs(u_e - u_s) / (RIB / 2.0))))
    step = (u_e - u_s) / m
    sign = 1.0 if step > 0 else -1.0
    pts = []
    for j in range(m + 1):
        w = w_a if j % 2 == 0 else w_b
        u = u_s + j * step
        if j > 0:
            u = min(max(u, ea(w) + W), eb(w) - W)
            pu, pw = pts[-1]
            if (u - pu) * sign < 0 or math.hypot(u - pu, w - pw) < W:
                return None
        pts.append((u, w))
    return pts


def sharpest_corner(pts, closed):
    """Smallest angle (deg) the path folds into at any vertex - 180 = straight, small = sharp."""
    n = len(pts)
    best = 180.0
    for i in range(n if closed else n - 1):
        if not closed and i == 0:
            continue
        a, b, c = pts[i - 1], pts[i], pts[(i + 1) % n]
        v1x, v1y, v2x, v2y = a.X - b.X, a.Y - b.Y, c.X - b.X, c.Y - b.Y
        l1, l2 = math.hypot(v1x, v1y), math.hypot(v2x, v2y)
        if l1 < 1e-6 or l2 < 1e-6:
            continue
        cosang = max(-1.0, min(1.0, (v1x * v2x + v1y * v2y) / (l1 * l2)))
        best = min(best, math.degrees(math.acos(cosang)))
    return best


def bead_mesh(pts, closed, z_mid, width, height, seg=3):
    """Printed bead along a horizontal polyline: flat top/bottom, round sides, mitred corners."""
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
        has_prev, has_next = closed or i > 0, closed or i < n - 1
        if has_prev and has_next:
            t1, t2 = unit(pts[i - 1], pts[i]), unit(pts[i], pts[(i + 1) % n])
            sx, sy = t1[1] + t2[1], -t1[0] - t2[0]
            L = math.hypot(sx, sy)
            if L < 1e-6:
                sx, sy, L = t1[1], -t1[0], 1.0
            sx, sy = sx / L, sy / L
            scale = 1.0 / max(0.35, sx * t1[1] - sy * t1[0])
        else:
            t = unit(pts[i - 1], pts[i]) if has_prev else unit(pts[i], pts[i + 1])
            sx, sy, scale = t[1], -t[0], 1.0
        for s, v in prof:
            m.Vertices.Add(pts[i].X + sx * s * scale, pts[i].Y + sy * s * scale, z_mid + v)
    for i in range(n if closed else n - 1):
        j = (i + 1) % n
        for k in range(P):
            k2 = (k + 1) % P
            m.Faces.AddFace(i * P + k, j * P + k, j * P + k2, i * P + k2)
    if not closed:
        for ring, flip in ((0, True), (n - 1, False)):
            ci = m.Vertices.Count
            m.Vertices.Add(pts[ring].X, pts[ring].Y, z_mid)
            for k in range(P):
                a, b = ring * P + k, ring * P + (k + 1) % P
                m.Faces.AddFace(b, a, ci) if flip else m.Faces.AddFace(a, b, ci)
    m.Normals.ComputeNormals()
    return m


blocks = DataTree[object]()
ids = DataTree[object]()
tags = DataTree[object]()
toolpaths = DataTree[object]()
beads = DataTree[object]()
check = []
piece_paths = []
piece_beads = None
piece_check = "no piece picked" if not PICK else "{} not found (needs print_paths on)".format(PICK)
n_rating = {"OK": 0, "AMBER": 0, "RED": 0}
rebar = DataTree[object]()
rebar_list = []
bar_lengths = []
layer_heights = []
n_zig = 0
n_loop = 0
cutlist = []
info = []
field_lengths = []
volume = 0.0
n_hips = 0
n_solid = 0
failed = []
hollow_failed = []

for r_i, rect in enumerate(rooms or []):
    pl = rect.Plane
    ix0, ix1 = rect.X.Min, rect.X.Max
    iy0, iy1 = rect.Y.Min, rect.Y.Max
    short = min(ix1 - ix0, iy1 - iy0)

    # courses that fit before the top opening gets too small
    n_c = 0
    while n_c < MAX_C and short - 2 * K * (n_c + 1) * H >= MIN_OPEN:
        n_c += 1
    if n_c == 0:
        info.append("room {}: smaller than min_open, nothing built".format(r_i))
        continue
    z_top = n_c * H

    def thick(z):
        return T0 + (T1 - T0) * z / z_top

    def inner(z):
        return -K * z

    def outer(z):
        return -K * z + thick(z)

    def envelope(c):
        """(w, z) outline of course c before hollowing. w is outward from the base rectangle."""
        z0, z1 = c * H, (c + 1) * H
        pts = [(inner(z0), z0)]
        if c == n_c - 1 or LAP <= 0:          # flat top
            pts += [(inner(z1), z1), (outer(z1), z1)]
        else:                                 # outside wall stops lap-depth below the course line
            zr = z1 - LAP * thick(z1)
            pts += [(inner(z1), z1), (inner(z1) + W, z1), (inner(zr) + W, zr), (outer(zr), zr)]
        if c > 0 and LAP > 0:                 # outside wall + ribs hang down into the band below
            zn = z0 - LAP * thick(z0)
            pts += [(outer(zn), zn), (inner(zn) + W + CLR, zn), (inner(z0) + W + CLR, z0)]
        else:
            pts.append((outer(z0), z0))
        return pts

    def cavity(c):
        """(w, z) outline of the open cavity of course c, overshooting top and bottom."""
        z0, z1 = c * H, (c + 1) * H
        zb = (z0 - LAP * thick(z0) if c > 0 else z0) - EPS
        zt = z1 + EPS
        return [(inner(zb) + W + NUDGE, zb), (inner(zt) + W + NUDGE, zt),
                (outer(zt) - W, zt), (outer(zb) - W, zb)]

    def bar_w(z, row):
        """Bar axis at height z: one bead in from the room-side ('i') or outside ('o') wall.
        Both faces are planes, so this is a straight line up the slope."""
        return inner(z) + W + R_H if row == 'i' else outer(z) - W - R_H

    def node_fits(u, row, zm, ea, eb):
        """Does the arc around a hole at u fit between this piece's end walls?"""
        wa = bar_w(zm, row)
        return all(ea(w) + RA + W <= u <= eb(w) - RA - W for w in (wa - RA, wa, wa + RA))

    def node_chain(nodes, zm, band, forward):
        """Zig-zag through the bar nodes: straight legs, and an arc around each hole on the
        cavity side - the wall closes the hole on the other side. In the hanging lap band the
        room-side arcs are shortened to clear the room-side wall of the piece below."""
        pts = []
        for u_n, row in (nodes if forward else list(reversed(nodes))):
            wa = bar_w(zm, row)
            if row == 'i':
                a0, a1 = (150.0, 30.0) if band == 'nose' else (180.0, 0.0)
            else:
                a0, a1 = 180.0, 360.0
            arc = [(u_n + RA * math.cos(math.radians(a0 + (a1 - a0) * j / 8.0)),
                    wa + RA * math.sin(math.radians(a0 + (a1 - a0) * j / 8.0))) for j in range(9)]
            pts += arc if forward else arc[::-1]
        return pts

    def layer_path(zm, band, ea, eb, nodes=None):
        """One print layer of a piece as (u, w) points + closed flag + whether it has a zig-zag.
        ea / eb: centreline of the start / far end wall as a function of w.
        nodes: rebar positions [(u, row)] in this piece - the zig-zag then runs through them."""
        wi = inner(zm) + W / 2.0              # room-side wall centreline
        wo = outer(zm) - W / 2.0              # outside wall centreline
        if band == 'top':                     # lap band above the outside wall: room-side wall only
            return [(ea(wi), wi), (eb(wi), wi)], False, False
        if nodes and thick(zm) < T_NEED:
            nodes = None
        # zig-zag touch lines: one bead in from each wall (in the nose band, clear of the wall below)
        zi = inner(zm) + 1.5 * W + CLR if band == 'nose' else wi + W
        zo = wo - W
        fits = zo - zi >= 0.5 * W
        if band == 'main':
            loop = [(ea(wi), wi), (eb(wi), wi), (eb(wo), wo), (ea(wo), wo)]
            if nodes:
                return loop + [(ea(zi), zi)] + node_chain(nodes, zm, band, True), False, True
            zig = zigzag(ea(zi), min(eb(zi), eb(zo)) - W, zi, zo, ea, eb) if fits else None
            if zig is None:
                return loop + [loop[0]], True, False
            return loop + zig, False, True
        # nose band: outside wall + both end walls + zig-zag back
        if zi >= wo - 0.5 * W:
            return [(ea(wo), wo), (eb(wo), wo)], False, False
        u = [(ea(zi), zi), (ea(wo), wo), (eb(wo), wo)]
        if nodes:
            return u + [(eb(zi), zi)] + node_chain(nodes, zm, band, False), False, True
        zig = zigzag(eb(zi), max(ea(zi), ea(zo)) + W, zi, zo, ea, eb) if fits else None
        if zig is None:
            return u + [(eb(zi), zi)], False, False
        return u + zig, False, True

    below = {'S': [], 'N': [], 'W': [], 'E': []}
    # (name, run axis, base face position, outward sign, base corners along the run)
    sides = [('S', 'x', iy0, -1, ix0, ix1),
             ('N', 'x', iy1, 1, ix0, ix1),
             ('W', 'y', ix0, -1, iy0, iy1),
             ('E', 'y', ix1, 1, iy0, iy1)]

    # rebar positions along each side - the same in every course, so the holes line up.
    # Centred on the side, alternating room-side ('i') and outside ('o') rows, half a spacing apart.
    nodes = {}
    for name, d, face, out, ua, ub in sides:
        half_sp = BAR_SP / 2.0
        k_max = int((ub - ua) / 2.0 / half_sp)
        nodes[name] = [((ua + ub) / 2.0 + k * half_sp, 'i' if k % 2 == 0 else 'o')
                       for k in range(-k_max, k_max + 1)]
    bar_top = {}                              # (side, node index) -> last course it has a hole in
    bar_alive = set((name, i) for name in nodes for i in range(len(nodes[name])))

    for c in range(n_c):
        z0, z1 = c * H, (c + 1) * H
        env = envelope(c)
        cav = cavity(c)
        zm = (z0 + z1) / 2.0
        wm = (inner(zm) + outer(zm)) / 2.0    # mid-thickness, where lengths are measured
        t_here = thick(zm)
        can_hollow = HOLLOW and thick(z1) - 2 * W >= MIN_CAV
        holes_here = REBAR and thick(z1) >= T_NEED
        present = set()
        path = GH_Path(r_i, c)
        k_piece = 0

        for name, d, face, out, ua, ub in sides:
            hip_a, hip_b = ua - wm, ub + wm   # hip line at mid-thickness (for the cut list)
            w_in = inner(zm)                  # corner pieces are measured on the room-side face
            ja, jb = ua - w_in + HIP, ub + w_in - HIP
            if jb - ja < 50:                   # side too short: corner pieces meet in the middle
                ja = jb = (hip_a + hip_b) / 2.0
            js = lay_run(ja, jb, below[name]) if jb > ja else []
            if REBAR and jb > ja and len(nodes[name]) > 1:
                # move every joint to the middle between two bars, so no joint cuts a hole
                us = [u for u, row in nodes[name]]
                mids = [(a + b) / 2.0 for a, b in zip(us, us[1:])]
                up = [m for m in mids if m >= ja]
                dn = [m for m in mids if m <= jb]
                ja2 = up[0] if up else ja      # corner pieces only get longer, never shorter
                jb2 = dn[-1] if dn else jb
                if jb2 - ja2 < 0.5 * P_MIN:    # too little left between the corners: they meet at a bar gap
                    centre = min(mids, key=lambda m: abs(m - (ja + jb) / 2.0))
                    ja = jb = centre
                    js = []
                elif jb2 > ja2:
                    ja, jb = ja2, jb2
                    snapped = sorted(set(min(mids, key=lambda m: abs(m - j)) for j in js))
                    js, last = [], ja         # drop joints that would leave a piece under half piece_min
                    for j in snapped:
                        if j - last >= 0.5 * P_MIN and jb - j >= 0.5 * P_MIN:
                            js.append(j)
                            last = j
            below[name] = [ja] + js + [jb]

            # (label, piece start/end, cavity cells, end wall centrelines for printing,
            #  mid-thickness start/end, is corner)
            half = W / 2.0
            parts = [("H1", mitre_a(ua, 0.0), const(ja),
                      [(mitre_a(ua, W * SQ2), const(ja - W))],
                      mitre_a(ua, half * SQ2), const(ja - half), hip_a, ja, True)]
            cuts = [ja] + js + [jb] if jb > ja else []
            for k in range(len(cuts) - 1):
                parts.append(("{:02d}".format(k + 1), const(cuts[k]), const(cuts[k + 1]),
                              cells_between(cuts[k], cuts[k + 1]),
                              const(cuts[k] + half), const(cuts[k + 1] - half),
                              cuts[k], cuts[k + 1], False))
            parts.append(("H2", const(jb), mitre_b(ub, 0.0),
                          [(const(jb + W), mitre_b(ub, W * SQ2))],
                          const(jb + half), mitre_b(ub, half * SQ2), jb, hip_b, True))

            for label, fa, fb, cells, ea, eb, l0, l1, is_hip in parts:
                pid = "R{}-C{}-{}-{}".format(r_i, c, name, label)
                brep = ruled(pl, d, face, out, env, fa, fb)
                if brep is None:
                    failed.append(pid)
                    continue
                piece_nodes = []              # rebar holes in this piece
                if holes_here:
                    for i_n, (u_n, row) in enumerate(nodes[name]):
                        if node_fits(u_n, row, zm, ea, eb):
                            piece_nodes.append((u_n, row))
                            present.add((name, i_n))
                if can_hollow:
                    cutters = [ruled(pl, d, face, out, cav, ca, cb) for ca, cb in cells]
                    cutters = [x for x in cutters if x is not None]
                    res = rg.Brep.CreateBooleanDifference([brep], cutters, TOL) if cutters else None
                    if res and len(res) == 1:
                        brep = res[0]
                    else:
                        hollow_failed.append(pid)
                else:
                    n_solid += 1
                blocks.Add(brep, path)
                ids.Add(pid, path)
                x, y = xy((l0 + l1) / 2.0, face + out * wm, d)
                tags.Add(pl.PointAt(x, y, z1), path)
                cutlist.append("{}  {:.0f} mm long, {:.0f} mm thick".format(pid, l1 - l0, t_here))
                volume += brep.GetVolume()
                if is_hip:
                    n_hips += 1
                else:
                    field_lengths.append(l1 - l0)

                if PATHS:
                    ppath = GH_Path(r_i, c, k_piece)
                    z_bot = z0 - LAP * thick(z0) if c > 0 else z0
                    zr = z1 - LAP * thick(z1) if c < n_c - 1 else z1 + 1.0
                    n_l = max(1, int(round((z1 - z_bot) / LH)))
                    lh = (z1 - z_bot) / n_l
                    layer_heights.append(lh)
                    prev = None
                    picked = pid == PICK
                    worst_t, min_seg, sharpest, stub = 1e9, 1e9, 180.0, None
                    piece_mesh = rg.Mesh()    # all layers of this piece as one mesh
                    for li in range(n_l):
                        zm = z_bot + (li + 0.5) * lh
                        band = 'nose' if (c > 0 and zm < z0) else ('top' if zm > zr else 'main')
                        uw, closed, has_zig = layer_path(zm, band, ea, eb, piece_nodes)
                        if has_zig:
                            n_zig += 1
                        else:
                            n_loop += 1
                        zt = z_bot + (li + 1) * lh    # nozzle height = top of the layer
                        pts = []
                        for u, w in uw:
                            x, y = xy(u, face + out * w, d)
                            p = pl.PointAt(x, y, zt)
                            if not pts or p.DistanceTo(pts[-1]) > 0.5:
                                pts.append(p)
                        if closed:
                            if pts[0].DistanceTo(pts[-1]) < 0.5:
                                pts = pts[:-1]
                            if prev is not None:      # start the loop at the corner nearest the last layer's end
                                s = min(range(len(pts)), key=lambda i: pts[i].DistanceTo(prev))
                                pts = pts[s:] + pts[:s]
                            pts.append(pts[0])
                        elif prev is not None and pts[-1].DistanceTo(prev) < pts[0].DistanceTo(prev):
                            pts.reverse()             # start where the last layer ended
                        if len(pts) < 2:
                            continue
                        prev = pts[-1]
                        crv = rg.PolylineCurve(pts)
                        toolpaths.Add(crv, ppath)
                        flat = [rg.Point3d(p.X, p.Y, p.Z) for p in (pts[:-1] if closed else pts)]
                        bm = bead_mesh(flat, closed, zt - lh / 2.0, W, lh)
                        if bm:
                            piece_mesh.Append(bm)
                        if picked:
                            piece_paths.append(crv)

                        # printability numbers for this layer
                        segs = [pts[i].DistanceTo(pts[i + 1]) for i in range(len(pts) - 1)]
                        worst_t = min(worst_t, sum(segs) / SPEED)
                        min_seg = min(min_seg, min(segs))
                        sharpest = min(sharpest, sharpest_corner(flat, closed))
                        if band == 'top':
                            stub = sum(segs) if stub is None else min(stub, sum(segs))

                    piece_mesh.Normals.ComputeNormals()
                    piece_mesh.Compact()
                    beads.Add(piece_mesh, path)   # one mesh per piece, same order as blocks / ids
                    if picked:
                        piece_beads = piece_mesh

                    red, amber = [], []
                    if worst_t < MIN_T:
                        red.append("layer only {:.0f} s".format(worst_t))
                    elif worst_t < 1.5 * MIN_T:
                        amber.append("layer {:.0f} s (close to {:.0f})".format(worst_t, MIN_T))
                    if stub is not None and stub < 3 * W:
                        red.append("lap stub {:.0f} mm long".format(stub))
                    if sharpest < 60.0:
                        amber.append("{:.0f} deg corner".format(sharpest))
                    if min_seg < W:
                        amber.append("{:.0f} mm segment".format(min_seg))
                    rating = "RED" if red else ("AMBER" if amber else "OK")
                    n_rating[rating] += 1
                    line = "{}  {}  {}".format(pid, rating, " | ".join(red + amber)).rstrip()
                    if rating != "OK":
                        check.append(line)
                    if picked:
                        piece_check = line
                k_piece += 1

        # a bar carries on only while every course has its hole
        for key in list(bar_alive):
            if key in present:
                bar_top[key] = c
            else:
                bar_alive.discard(key)

    # the bars: straight, up the slope, from the eave to the top of their last course
    if REBAR:
        side_of = dict((s[0], s) for s in sides)
        for (name, i_n), c_last in sorted(bar_top.items()):
            _, d, face, out, ua, ub = side_of[name]
            u_n, row = nodes[name][i_n]
            ends = []
            for z in (0.0, (c_last + 1) * H):
                x, y = xy(u_n, face + out * bar_w(z, row), d)
                ends.append(pl.PointAt(x, y, z))
            axis = rg.Line(ends[0], ends[1])
            cyl = rg.Cylinder(rg.Circle(rg.Plane(ends[0], axis.Direction), BAR_D / 2.0), axis.Length)
            rebar.Add(cyl.ToBrep(True, True), GH_Path(r_i))
            bar_id = "R{}-{}-{}{:02d}".format(r_i, name, row, i_n + 1)
            rebar_list.append("{}  {:.0f} mm  (courses 0-{})".format(bar_id, axis.Length, c_last))
            bar_lengths.append(axis.Length)

    info.append("room {}: {} courses, rise {:.0f}, top opening {:.0f} x {:.0f}".format(
        r_i, n_c, z_top, ix1 - ix0 - 2 * K * z_top, iy1 - iy0 - 2 * K * z_top))

info.append("{} pieces: {} long pieces + {} corner pieces".format(
    len(field_lengths) + n_hips, len(field_lengths), n_hips))
if field_lengths:
    info.append("long pieces {:.0f} - {:.0f} mm".format(min(field_lengths), max(field_lengths)))
info.append("thickness {:.0f} -> {:.0f} mm, pitch {:.0f} deg".format(
    T0, T1, math.degrees(math.atan2(H, S))))
if HOLLOW:
    info.append("walls {:.0f} mm, cavity {:.0f} -> {:.0f} mm wide".format(
        W, T0 - 2 * W, T1 - 2 * W))
info.append("material: {:.3f} m3".format(volume / 1e9))

if PATHS and layer_heights:
    info.append("print: bead {:.0f} mm, layers {:.1f} - {:.1f} mm (adjusted per piece from {:.0f})".format(
        W, min(layer_heights), max(layer_heights), LH))
    info.append("print: {} layers with zig-zag, {} without (too narrow, too short or lap band)".format(n_zig, n_loop))
    info.append("check: {} OK, {} AMBER, {} RED  (at {:.0f} mm/s, min layer {:.0f} s) - see `check`".format(
        n_rating["OK"], n_rating["AMBER"], n_rating["RED"], SPEED, MIN_T))
    lean = math.degrees(math.atan2(S, H))
    info.append("print: walls lean {:.0f} deg from vertical, {:.1f} mm shift per layer{}".format(
        lean, K * LH, "  - RED: too steep for wet concrete" if lean > 30 else
        ("  - AMBER: test it" if lean > 20 else "")))
    if HOLLOW:
        info.append("note: `hollow` shows straight ribs - the print paths use a zig-zag; "
                    "turn hollow off and look at `beads` for the printed result")

if REBAR:
    if bar_lengths:
        info.append("rebar: {} bars, {:.1f} m total, longest {:.0f} mm, {:.0f} mm bars in {:.0f} mm holes".format(
            len(bar_lengths), sum(bar_lengths) / 1000.0, max(bar_lengths), BAR_D, HOLE_D))
    else:
        info.append("rebar: no bars fit - pieces need at least {:.0f} mm thickness (3 beads + hole)".format(T_NEED))
    if T_NEED > T1:
        info.append("rebar: bars stop where the roof gets thinner than {:.0f} mm".format(T_NEED))
    if BAR_SP / 4.0 < RA + W:
        info.append("WARNING: bar_spacing too tight - joints can't fit between bars (need >= {:.0f})".format(
            4 * (RA + W)))
    if not PATHS:
        info.append("rebar: bars modelled, but the holes are only in the print paths - turn print_paths on")

if LAP < 0 or LAP >= 1:
    info.append("WARNING: lap should be between 0 (no lap) and 1 (share of thickness)")
if HOLLOW and n_solid:
    info.append("note: {} pieces too thin to hollow with {:.0f} mm walls - left solid".format(n_solid, W))
if P_MAX < 1.5 * P_MIN:
    info.append("note: narrow length range - some runs can't stay in range and get shared evenly")
if hollow_failed:
    info.append("WARNING: hollowing failed on {} pieces (left solid): {}".format(
        len(hollow_failed), ", ".join(hollow_failed[:10])))
if failed:
    info.append("WARNING: {} pieces failed to build: {}".format(len(failed), ", ".join(failed[:10])))
