"""Two options for a cast column grid inside the printed pyramid roof shell (one roof face, seen square on, 1:50).
Standalone apart from pyramid_drawings.py (sheet helpers + roof geometry). Run: python details/make_set.py
  A  ruled-surface grid: columns follow the straight lines from the base edge to the crown edge, drop out in two stages as they converge,
     horizontal ribs at the stage heights.
  B  diamond grid: two families of equal diagonals parallel to the hips, only a bottom ring (the 300 solid base) and a top ring (crown)."""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pyramid_drawings as g
from pyramid_drawings import Sheet, rect, layers

# ================= PARAMETERS =================
BUT_SPACING = 1500.0       # buttress spacing along the wall, about (7 equal bays on the 10400 centreline)
RIB_W, RIB_D = g.RIB_W, g.RIB_D   # rib / column width in the face; depth = the rib zone between the inner and the middle bead
MIN_PITCH = 500.0          # A: smallest column spacing allowed; below this every other column stops
TOP_RING = 128.0           # top ring depth in elevation (= 160 square to the slope)
BAR_KG_M = {16: 1.578, 12: 0.888}
RISE = g.RISE              # 6000
# the grid lies on the centre of the rib zone (= the shell surface of the Karamba model: the centroid of the inner and middle beads)
HALFB = g.HALF + g.RIB_C * g.SH          # half width of the grid at the eave
TOPB = g.OPEN / 2 + g.RIB_C * g.SH       # half width at the crown
KX = (HALFB - TOPB) / RISE            # half-width loss per unit height
VST = math.hypot(HALFB - TOPB, RISE) / RISE   # true length / elevation height (about 1.25)
w = lambda h: HALFB - KX * h
COL_PITCH = 2 * HALFB / 10            # A: column spacing at the base edge (10 bays)
DIAG_P = 2 * HALFB / 8                # B: spacing of one diagonal family along the base edge (8 diamonds wide)
H1 = (1 - MIN_PITCH / COL_PITCH) * HALFB / KX            # A: height where the spacing hits MIN_PITCH: every other column stops
H2 = (1 - MIN_PITCH / (2 * COL_PITCH)) * HALFB / KX      # A: same again: only the hips go on
RING_H = [H1 / 2, H1, H2]             # A: horizontal ribs; H1 and H2 are where columns stop
SOLID = g.SOLID_H

def tl(p, q): return math.hypot(q[0] - p[0], VST * (q[1] - p[1]))      # true length of an elevation segment

# ---------------- grid definitions: list of (kind, [(x, h), ...]) ----------------
def grid_A():
    segs = []
    n = int(round(2 * HALFB / COL_PITCH))
    xs = [-HALFB + i * COL_PITCH for i in range(n + 1)]
    # heights where the spacing (COL_PITCH * w/HALFB * 2^stage) reaches MIN_PITCH
    h1, h2 = H1, H2
    for i, x0 in enumerate(xs):
        top = h1 if i % 2 else (h2 if 0 < i < n else RISE - TOP_RING / 2)
        segs.append(("col", [(x0 * w(SOLID) / HALFB, SOLID), (x0 * w(top) / HALFB, top)]))
    for h in RING_H:
        segs.append(("ring", [(-w(h), h), (w(h), h)]))
    return segs, (h1, h2)

def grid_B():
    segs = []
    top = RISE - TOP_RING / 2
    for k in range(0, 9):                     # left-leaning family (parallel to the left hip), k = 0 is the hip
        for sgn in (1, -1):
            f = lambda h, k=k, sgn=sgn: sgn * (-HALFB + KX * h + k * DIAG_P)
            hmax = (2 * HALFB - k * DIAG_P) / (2 * KX)
            h1 = min(top, hmax)
            if h1 - SOLID > 200:
                segs.append(("diag", [(f(SOLID), SOLID), (f(h1), h1)]))
    return segs, None

def ring_segs(top=True):
    segs = [("solid", [(-w(0), 0), (w(0), 0)])]
    if top: segs.append(("ring", [(-w(RISE - TOP_RING / 2), RISE - TOP_RING / 2), (w(RISE - TOP_RING / 2), RISE - TOP_RING / 2)]))
    return segs

def quad(p, q, wd, kind):
    """strip of true width wd around the elevation segment p-q (elevation x, h)"""
    dx, dh = q[0] - p[0], VST * (q[1] - p[1])
    L = math.hypot(dx, dh)
    nx, nh = -dh / L * wd / 2, dx / L * wd / 2          # normal in true-length space
    f = lambda pt, s: (pt[0] + s * nx, pt[1] + s * nh / VST)
    return [f(p, 1), f(q, 1), f(q, -1), f(p, -1)]

def draw_face(sh, segs):
    solid = [(-w(0), 0), (w(0), 0), (w(SOLID), SOLID), (-w(SOLID), SOLID)]
    strips = []
    for kind, pts in segs:
        if kind == "ring":
            y = pts[0][1]; strips.append(rect(pts[0][0], y - TOP_RING / 2, pts[1][0], y + TOP_RING / 2))
        elif kind == "solid":
            strips.append(solid)
        else:
            strips.append(quad(pts[0], pts[1], RIB_W, kind))
    for p in strips:
        sh.poly(p, "#000", 0.35)
    for p in strips:
        sh.poly(p, "#fff", 0.0); sh.poly(p, "url(#cast)", 0.0)
    # centre lines of the bars (one Ø16 pair per rib, drawn as a single dash-dot centreline)
    xo = lambda h: g.HALF + g.rx(h)[-1]
    layers(sh, [(-xo(0), 0), (xo(0), 0), (xo(RISE), RISE), (-xo(RISE), RISE)], 0, 0.03, step=100, color="#c4c4c4")      # printed layer joints on the whole shell (every 100 drawn; real layers are 10)
    sh.layer = "REBAR"
    for kind, pts in segs:
        if kind in ("col", "diag"):
            sh.line(pts, 0.15, "#000", dash="2 0.8")
        elif kind == "ring":
            sh.line(pts, 0.15, "#000", dash="2 0.8")
    sh.layer = None

def stats(segs):
    Lr = sum(tl(s[0], s[1]) for k, s in segs if k in ("col", "diag") )
    Lh = sum(tl(s[0], s[1]) for k, s in segs if k == "ring")
    return Lr, Lh

def section_inset(sh, X0, Z0, F=5.0, callouts=True, W_=700.0):
    """plan cut through one rib at one print layer, square to the slope, 1:10 (model = local * F). outside at the bottom, inside (room) at the top.
    Printed beads (30, black rim, hatched body) form the layers and the channel walls; the channel is filled with poured concrete."""
    k = F / 5.0                                                                          # layout offsets scale with the drawing scale (F = 5 at 1:10, 2 at 1:5 on the 1:10 sheet)
    M = lambda u, v: (X0 + F * u, Z0 + F * v)
    B, T = g.BEAD, g.T_ROOF
    u0 = (W_ - RIB_W) / 2
    u1 = u0 + RIB_W
    v_l0 = g.OUTER_BEADS * B                    # local v from the outside face: outer beads | lattice | middle bead | rib zone | inner bead
    v_l1 = v_l0 + g.LATTICE
    v_r0, v_r1 = v_l1 + B, v_l1 + B + RIB_D
    sh.poly([M(0, 0), M(W_, 0), M(W_, T), M(0, T)], "#fff", 0.0)
    sh.poly([M(0, v_l0), M(W_, v_l0), M(W_, v_l1), M(0, v_l1)], "url(#dots)", 0.0)    # lattice zone: insulation between the loops of the wavy bead
    g.clip_begin(sh, "wv{:g}".format(F), *M(0, v_l0), *M(W_, v_l1))                    # wavy bead, touching the outer beads and the middle bead in turn
    f = g.wavy(v_l0 + B / 2, v_l1 - B / 2, g.WAVE_ROOF)
    us = [-B + (W_ + 2 * B) * i / 80 for i in range(81)]
    g.printed(sh, [M(u, f(u - W_ / 2)) for u in us], B, F, rim=0.4)
    g.clip_end(sh)
    beads = [rect(0, i * B, W_, (i + 1) * B) for i in range(g.OUTER_BEADS)]            # outer beads
    beads += [rect(0, v_l1, W_, v_r0),                                                  # middle bead
              rect(0, v_r1, W_, T),                                                     # inner bead
              rect(u0 - B, v_r0, u0, v_r1), rect(u1, v_r0, u1 + B, v_r1)]               # channel walls of the rib, across the rib zone
    for q in beads:
        q = [M(*pt) for pt in q]
        sh.poly(q, "#fff", 0.4); sh.poly(q, "url(#conc)", 0.0)
    rib = [M(u0, v_r0), M(u1, v_r0), M(u1, v_r1), M(u0, v_r1)]                          # poured core; the rest of the rib zone is an empty cavity
    sh.poly(rib, "#fff", 0.0); sh.poly(rib, "url(#cast)", 0.0); sh.poly(rib, "none", 0.5)
    sh.poly([M(0, 0), M(W_, 0), M(W_, T), M(0, T)], "none", 0.5)
    sh.layer = "REBAR"
    sh.poly([M(u0 + 30, v_r0 + 30), M(u1 - 30, v_r0 + 30), M(u1 - 30, v_r1 - 30), M(u0 + 30, v_r1 - 30)], "none", 8 / sh.scale, g.BLUE, tw=8)    # stirrup Ø8
    for u, v in ((u0 + 45, v_r0 + 45), (u1 - 45, v_r0 + 45), (u0 + 45, v_r1 - 45), (u1 - 45, v_r1 - 45)):
        sh.dot(*M(u, v), 8)                                                                                              # 4 Ø16
    sh.layer = None
    sh.text(*M(-20, 0.5 * v_l0), "outside", 2.4, "end"); sh.text(*M(-20, T - 0.5 * B), "inside", 2.4, "end")
    old_lf, sh.dimlfac = sh.dimlfac, 1.0 / F                                            # dimensions in the inset measure true sizes
    us_d = (0, u0 - B, u0, u1, u1 + B, W_)
    sh.dim_h([X0 + F * u for u in us_d], Z0 - 300 * k, ext=Z0 - 30 * k, labels=["{:g}".format(b_ - a_) for a_, b_ in zip(us_d, us_d[1:])])
    vs_d = [0, v_l0, v_l1, v_r0, v_r1, T]
    lab_v = ["{:g}".format(b_ - a_) for a_, b_ in zip(vs_d, vs_d[1:])]
    if g.OUTER_BEADS > 1: lab_v[0] = "{} x {:g}".format(g.OUTER_BEADS, B)            # the outer beads as one dimension
    sh.dim_v([Z0 + F * v for v in vs_d], X0 + F * W_ + 150 * k, ext=X0 + F * W_, labels=lab_v)
    sh.dimlfac = old_lf
    sh.text(X0, Z0 + F * T + 160 * k, "Plan cut through a rib at one layer, 1:{:g}".format(sh.scale / F), 3.2, "start", weight="bold")
    if callouts:
        cx = X0 + F * W_ + 650
        sh.callout(4, cx, Z0 + F * (T - B / 2), *M(550, T - B / 2))
        sh.callout(3, cx, Z0 + F * (v_r0 + v_r1) / 2, *M(u1 - 70, (v_r0 + v_r1) / 2))
        sh.callout(10, cx + 800, Z0 + F * (v_r0 + v_r1) / 2, *M(u1 + B / 2, (v_r0 + v_r1) / 2 - 40))
        sh.callout(12, cx, Z0 + F * (v_l1 + v_r0) / 2 - 220, *M(550, (v_l1 + v_r0) / 2))
        sh.callout(6, cx, Z0 + F * (v_l0 + v_l1) / 2 - 150, *M(600, (v_l0 + v_l1) / 2))
        sh.callout(5, cx, Z0 + F * B / 2 - 60, *M(550, B / 2))

def section_long(sh, X0, Z0, F=2.5, H=800.0):
    """section along the centre of a rib at the eave, 1:20, in the true roof geometry: the inner, middle and outer beads are printed (joints every 10,
    drawn every 20), the lattice zone holds the insulation, the core is poured: the first lift is the solid base, then the rib in lifts."""
    SH, rx, SOL = g.SH, g.rx, SOLID
    M = lambda x, h: (X0 + F * x, Z0 + F * h)
    def band(f0, f1, h0, h1):        # f0, f1 return the x offsets of the two edges at height h
        return [M(f0(h0), h0), M(f0(h1), h1), M(f1(h1), h1), M(f1(h0), h0)]
    e = [lambda h, i=i: rx(h)[i] for i in range(6)]         # layer faces, room side out: inner bead | rib zone | middle bead | lattice | outer beads
    inner_b = band(e[0], e[1], SOL, H)               # printed above the base
    mid_b = band(e[2], e[3], SOL, H)
    lat_z = band(e[3], e[4], SOL, H)
    outer_b = band(e[4], e[5], SOL, H)
    base_cast = band(e[0], e[5], 0, SOL)             # the bottom 300 is full concrete over the whole 400, one pour with the rib
    rib_cast = band(e[1], e[2], SOL, H)              # above the base the rib fills the rib zone
    z0 = Z0
    printed_ = (inner_b, mid_b, outer_b)
    for p in printed_ + (base_cast, rib_cast):
        sh.poly(p, "#000", 0.5)
    for p in printed_:
        sh.poly(p, "#fff", 0.0); sh.poly(p, "url(#conc)", 0.0); layers(sh, p, z0, 0.06, step=20 * F)
    sh.poly(lat_z, "#fff", 0.0); sh.poly(lat_z, "url(#dots)", 0.0)
    for p in (base_cast, rib_cast):
        sh.poly(p, "#fff", 0.0); sh.poly(p, "url(#cast)", 0.0)
    for p in printed_ + (lat_z, base_cast, rib_cast):
        sh.poly(p, "none", 0.4)
    for i in range(1, g.OUTER_BEADS):                                                 # joints between the outer beads
        sh.line([M(e[4](SOL) + i * g.BEAD * SH, SOL), M(e[4](H) + i * g.BEAD * SH, H)], 0.15)
    sh.line([M(e[1](SOL), SOL), M(e[2](SOL), SOL)], 0.5, "#fff")                       # no joint between the base and the rib core
    # pour lifts across the core
    for h in (600.0,):                                                                # first lift = the base and the first 300 of the rib together
        if h < H:
            sh.line([M(e[1](h), h), M(e[2](h), h)], 0.3, "#000", dash="2 1")
    # rebar: 2 of the 4 Ø16 are in the cut plane (45 from the faces of the core), stirrups Ø8 every 200
    sh.layer = "REBAR"
    for dd in (45, RIB_D - 45):
        sh.line([M(e[1](0) + dd * SH, 0), M(e[1](H) + dd * SH, H)], 16 * F / sh.scale, g.BLUE, tw=16)
    for h in range(100, int(H), 200):
        sh.line([M(e[1](h) + 30 * SH, h), M(e[2](h) - 30 * SH, h)], 8 * F / sh.scale, g.BLUE, tw=8)
    sh.layer = None
    sh.line([M(e[0](0) - 120, 0), M(e[5](0) + 260, 0)], 0.3)
    sh.text(X0 - 20 * F * 6, Z0 + F * H + 160, "Section along a rib at the eave, 1:20", 3.2, "start", weight="bold")
    xr_ = e[5](H * 0.5) + 520
    mid = lambda i, h: M((e[i](h) + e[i + 1](h)) / 2, h)
    sh.callout(11, X0 + F * xr_, Z0 + F * 700, *mid(1, 300))
    sh.callout(3, X0 + F * xr_, Z0 + F * 560, *mid(1, 560))
    sh.callout(6, X0 + F * xr_, Z0 + F * 400, *mid(3, 450))
    sh.callout(5, X0 + F * xr_, Z0 + F * 250, *mid(4, 380))
    sh.callout(4, X0 + F * (e[0](600) - 380), Z0 + F * 600, *mid(0, 600))
    sh.callout(12, X0 + F * (e[0](600) - 380), Z0 + F * 380, *mid(2, 500))

def common_legend(opt):
    B = g.BEAD
    L = [(3, True, "Rib (column) {:g} wide x {:g} deep in the rib zone, between the inner and the middle bead: the printed channel stays as formwork, filled with cast concrete; 4 Ø16 + Ø8 stirrups every 200 (assumed), or fibre concrete (see notes).".format(RIB_W, RIB_D)),
         (4, False, "Inner bead {:g}: continuous, covers the grid on the room side.".format(B)),
         (5, False, "{} outer beads {:g}: continuous, the outside of the printed shell, exposed concrete (no insulation or cladding outside).".format(g.OUTER_BEADS, B)),
         (6, True, "Lattice zone {:g}: wavy printed bead {:g} touching the middle and the outer beads in turn, insulation between (dotted).".format(g.LATTICE, B)),
         (10, False, "Printed channel walls {:g} each side of the rib, from the inner to the middle bead: permanent formwork. Between the ribs the rib zone is an empty cavity.".format(B)),
         (11, True, "Poured core: the solid base (300, full concrete over the whole {:g}) and the rib in one pour, lifts of about 600 from the eave (assumed, dashed), no joint between base and rib. Printed layer joints every 10 (drawn every 20).".format(g.T_ROOF)),
         (12, False, "Middle bead {:g}: closes the rib zone outside; inner and middle bead are the structural skins, the ribs the webs (as in the Karamba model).".format(B))]
    return L

def building(sh):
    """wall, buttresses, ground and footing, seen from outside (south face), under the roof face"""
    zg = -g.WALL_H
    HALF, WALL, BUT_L, BUT_W = g.HALF, g.WALL, g.BUT_L, g.BUT_W
    c = HALF + WALL / 2
    sh.poly(rect(-7300, zg - 1100, 7300, zg), "url(#earth)", 0.0)
    sh.poly(rect(-(HALF + WALL), zg, HALF + WALL, 0), "#fff", 0.5)                  # printed wall, outer face
    pr = lambda q: layers(sh, q, zg, 0.03, step=100, color="#c4c4c4")                                     # printed layer joints (every 100 drawn; real layers are 10)
    nb = int(round(2 * c / BUT_SPACING))                                                 # bays between buttresses (about 1.5 m)
    xs = [-c + 2 * c * k / nb for k in range(nb + 1)]
    dash = dict(color="#8c8c8c", dash="3 1.6")
    for j in range(0, nb, 2):                                                            # every other bay shows the printed wall: faint layer joints, dashed piece divisions
        xa, xb = xs[j] + BUT_W / 2, xs[j + 1] - BUT_W / 2
        pr(rect(xa, zg, xb, 0))
        wr = 5
        for r in range(1, wr):
            z = zg + r * g.WALL_H / wr
            sh.line([(xa, z), (xb, z)], 0.1, **dash)
        for r in range(wr):
            if r % 2: sh.line([((xa + xb) / 2, zg + r * g.WALL_H / wr), ((xa + xb) / 2, zg + (r + 1) * g.WALL_H / wr)], 0.1, **dash)
    for j in (1, 3, 5):                                                                  # odd bays: full curtain wall, or the door in the middle bay
        xa, xb = xs[j] + BUT_W / 2, xs[j + 1] - BUT_W / 2
        if j == 3:
            cxm = (xa + xb) / 2
            sh.poly(rect(cxm - 500, zg, cxm + 500, zg + 2000), "#fff", 0.3, "#444")
            sh.poly(rect(cxm - 540, zg, cxm + 540, zg + 2040), "none", 0.15, "#444")
        else:
            sh.poly(rect(xa, zg, xb, 0), "#fff", 0.35, "#444")
            sh.poly(rect(xa + 40, zg + 40, xb - 40, -40), "none", 0.15, "#444")
            sh.line([((xa + xb) / 2, zg + 40), ((xa + xb) / 2, -40)], 0.2, "#444")
            for zz in (zg + g.WALL_H / 3, zg + 2 * g.WALL_H / 3): sh.line([(xa + 40, zz), (xb - 40, zz)], 0.15, "#444")
    for x in xs:                                                                         # buttresses: one continuous strip each, 400 wide, corners included
        q = rect(x - BUT_W / 2, zg, x + BUT_W / 2, 0)
        sh.poly(q, "#fff", 0.0); pr(q); sh.poly(q, "none", 0.5)
    ft, fb = zg + g.FOOT_Z + g.FOOT_T, zg + g.FOOT_Z
    fx = c + BUT_L / 2 + g.FOOT_W / 2
    sh.line([(-fx, fb), (fx, fb), (fx, ft), (-fx, ft), (-fx, fb)], 0.25, dash="3 1")      # strip footing, hidden
    sh.line([(-HALF - WALL - BUT_L, ft), (-HALF - WALL - BUT_L, zg)], 0.25, dash="3 1"); sh.line([(HALF + WALL + BUT_L, ft), (HALF + WALL + BUT_L, zg)], 0.25, dash="3 1")
    sh.line([(-7300, zg), (7300, zg)], 0.5)
    # shell silhouette (outer face) behind the grid
    xo = lambda h: g.HALF + g.rx(h)[-1]
    sh.poly([(-xo(0), 0), (xo(0), 0), (xo(RISE), RISE), (-xo(RISE), RISE)], "#fff", 0.35)
    # division between printed pieces, dashed: running bond, about 1500 wide, rows 750 high on the roof (assumed)
    dash = dict(color="#8c8c8c", dash="3 1.6")
    PW = 1500.0
    nrow = 8
    for r in range(nrow):
        h0, h1 = r * RISE / nrow, (r + 1) * RISE / nrow
        if r: sh.line([(-xo(h0), h0), (xo(h0), h0)], 0.1, **dash)
        wm = (xo(h0) + xo(h1)) / 2
        n = max(1, int(round(2 * wm / PW)))
        for i in range(1, n):
            x = -1.0 + 2.0 * (i if r % 2 == 0 else i - 0.5) / n
            if abs(x) < 1: sh.line([(x * xo(h0), h0), (x * xo(h1), h1)], 0.1, **dash)

def segments(opt):
    """all rib segments of option opt ('A' or 'B') incl. the bottom (solid base) and top rings; extra = stop heights for A"""
    segs, extra = grid_A() if opt == "A" else grid_B()
    if opt == "A":
        segs = segs + [("solid", [(-w(0), 0), (w(0), 0)]), ("ring", [(-w(RISE - TOP_RING / 2), RISE - TOP_RING / 2), (w(RISE - TOP_RING / 2), RISE - TOP_RING / 2)])]
    else:
        segs = segs + ring_segs(True)
    return segs, extra

def sheet(opt):
    segs, extra = segments(opt)
    Lr, Lh = stats(segs)
    Lr4, Lh4 = 4 * Lr / 1000, 4 * Lh / 1000                                   # m, four faces (hips counted on both faces: shared, so a little high)
    nbars = 4
    steel = (Lr4 + Lh4) * nbars * BAR_KG_M[16]
    conc = (Lr4 + Lh4) * RIB_W * RIB_D * 1e-6
    if opt == "A":
        h1, h2 = extra
        title, sub = "Roof grid A: ruled-surface columns", "one roof face seen square on"
        legend = [(1, False, "Columns run in straight lines from the base edge (every {:.0f}) towards the crown edge, so they converge like the ruled surface of the sketch.".format(COL_PITCH)),
                  (2, False, "When the spacing drops to {:g} (about +{:.2f}) every other column stops; at about +{:.2f} only the four hip columns go on to the crown ring.".format(MIN_PITCH, (g.WALL_H + h1) / 1000, (g.WALL_H + h2) / 1000))]
        notes = ["Columns stop on a horizontal rib (at {:.0f} and {:.0f} above the eave); bars are lapped / hooked into it.".format(H1, H2),
                 "Horizontal ribs at {:.0f}, {:.0f}, {:.0f}, plus the 300 solid base (bottom ring) and the top ring at the crown.".format(*RING_H)]
    else:
        title, sub = "Roof grid B: diamond lattice", "one roof face seen square on"
        legend = [(1, False, "Diagonals parallel to the two hips (same inclination as the roof edges, {:.1f}° in the face), every {:.0f} along the base: equal diamonds {:.0f} wide.".format(math.degrees(math.atan2(RISE * VST, HALFB - TOPB)), DIAG_P, DIAG_P)),
                  (2, False, "Bottom ring = the 300 solid base; top ring at the crown. The hips are two of the diagonals. No other horizontal ribs.")]
        notes = ["Every diagonal ends on a ring or on a hip, so no bar has a free end in the shell.",
                 "Diagonals do not stop as the roof narrows: the diamonds just get clipped by the hips."]
    legend = legend + common_legend(opt) + [(7, False, "Printed wall {:g}, to +2.50: inner bead {:g}, lattice zone {:g} (wavy bead + insulation), {} outer beads {:g}.".format(g.WALL, g.BEAD, g.WALL_LAYERS[1], g.OUTER_BEADS, g.BEAD)),
                                             (8, False, "Buttresses 400 wide, 1000 from the inner face (600 outside), about every 1.5 m ({} bays of {:.0f} on the wall centreline, {} per side, corners included); every other bay is printed wall, the bays between are full-height curtain wall (door in the middle one).".format(round(2 * (g.HALF + g.WALL / 2) / BUT_SPACING), 2 * (g.HALF + g.WALL / 2) / round(2 * (g.HALF + g.WALL / 2) / BUT_SPACING), round(2 * (g.HALF + g.WALL / 2) / BUT_SPACING) + 1)),
                                             (9, True, "Strip footing 1800 x 250, underside at -1.00 (hidden, dashed): printed edge formwork, cast core.")]
    notes += ["Dashed lines = printed pieces in running bond (about 1500 x 750); very faint lines = printed layer joints (10 mm layers, drawn every 100).",
              "Printed mortar beads are permanent formwork; ribs, base and buttress cores are poured concrete (after the Obayashi 3dpod paper, 2023). Steel-fibre concrete could replace the rib bars, to be confirmed by the engineer.",
              "Rough quantities, four faces: ribs {:.0f} m, steel {:.0f} kg (4 Ø16 per rib), poured concrete {:.1f} m3.".format(Lr4 + Lh4, steel, conc)]
    legend.sort(key=lambda e: e[0])
    sh = Sheet(50, 157, 140, title, sub, legend, notes)
    sh.plain_legend = True
    building(sh)
    draw_face(sh, segs)
    xr = 7000
    sh.dim_v([0, SOLID], -w(0) - 700, ext=-w(0), labels=["300"])
    sh.dim_v([-g.WALL_H, 0], xr, ext=6100, labels=["{:g}".format(g.WALL_H)])
    sh.dim_v([0, RISE], xr, ext=w(0) + 500, labels=["{:g}".format(RISE)])
    sh.dim_h([-g.OPEN / 2, g.OPEN / 2], RISE + 380, ext=RISE, labels=["{:g} clear".format(g.OPEN)])      # crown opening, inside face (same as section and plan)
    zg = -g.WALL_H
    sh.level(-6700, zg, "±0.00", -1); sh.level(-6700, 0, "+2.50", -1); sh.level(-6700, RISE, "+8.50", -1); sh.level(-6700, zg + g.FOOT_Z, "-1.00", -1)
    sh.callout(7, -6900, zg + 1900, -4200, zg + 1900)
    sh.callout(8, -6900, zg + 700, -(g.HALF + g.WALL / 2), zg + 700)
    sh.callout(9, -6900, zg + g.FOOT_Z + 400, -6100, zg + g.FOOT_Z + 250)
    if opt == "A":
        for h in RING_H: sh.line([(-w(h) - 500, h), (-w(h) - 150, h)], 0.15, dash="2 1"); sh.text(-w(h) - 560, h - 60, "+{:.2f}".format((g.WALL_H + h) / 1000), 2.2, "end")
    if opt == "A":
        sh.callout(1, 6300, 2300, 3000 * w(2300) / HALFB, 2300)
        sh.callout(2, 6300, 4400, 4000 * w(extra[0]) / HALFB, extra[0])
    else:
        sh.callout(1, 6300, 2300, -1000, 2000)
        sh.callout(2, 6300, 5600, 0, RISE - TOP_RING / 2)
    sh.text(-HALFB - 800, RISE - 200, "Option " + opt, 4.2, "start", weight="bold")
    section_inset(sh, -5300, -6100)
    section_long(sh, 3000, -6100)
    return sh

if __name__ == "__main__":
    import make_set
    make_set.main()          # the whole drawing set: details/set/*.pdf, the merged set PDF and details/set/cad/*.dxf
