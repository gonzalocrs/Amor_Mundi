"""Two options for a cast column grid inside the printed pyramid roof shell (one roof face, seen square on, 1:50).
Standalone apart from pyramid_drawings.py (sheet helpers + roof geometry). Run: python details/roof_grid.py [out_dir]
  A  ruled-surface grid: columns follow the straight lines from the base edge to the crown edge, drop out in two stages as they converge,
     horizontal ribs at the stage heights.
  B  diamond grid: two families of equal diagonals parallel to the hips, only a bottom ring (the 300 solid base) and a top ring (crown)."""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pyramid_drawings as g
from pyramid_drawings import Sheet, rect

# ================= PARAMETERS =================
RIB_W = 160.0              # rib / column width in the face (assumed)
RIB_D = 240.0              # rib depth: the 160 air zone + layer 2, between the 80 outer skin and the 80 inner layer 1 (assumed)
COL_PITCH = 1000.0         # A: column spacing at the base edge
MIN_PITCH = 500.0          # A: smallest column spacing allowed; below this every other column stops
RING_H = [1667.0, 3333.0, 5000.0]   # A: horizontal ribs (centre heights above the eave); 3333 and 5000 are where columns stop
DIAG_P = 1250.0            # B: spacing of one diagonal family along the base edge (the diamond is 1250 wide)
TOP_RING = 128.0           # top ring depth in elevation (= 160 square to the slope)
BAR_KG_M = {16: 1.578, 12: 0.888}
HALFB = g.HALF             # 5000
RISE = g.RISE              # 6000
KX = (HALFB - g.OPEN / 2) / RISE      # half-width loss per unit height (0.75)
VST = math.hypot(HALFB - g.OPEN / 2, RISE) / RISE   # true length / elevation height (1.25)
w = lambda h: HALFB - KX * h
SOLID = g.SOLID_H

def tl(p, q): return math.hypot(q[0] - p[0], VST * (q[1] - p[1]))      # true length of an elevation segment

# ---------------- grid definitions: list of (kind, [(x, h), ...]) ----------------
def grid_A():
    segs = []
    n = int(round(2 * HALFB / COL_PITCH))
    xs = [-HALFB + i * COL_PITCH for i in range(n + 1)]
    # heights where the spacing (COL_PITCH * w/HALFB * 2^stage) reaches MIN_PITCH
    h1 = (HALFB - MIN_PITCH / COL_PITCH * HALFB) / KX
    h2 = (HALFB - MIN_PITCH / (2 * COL_PITCH) * HALFB) / KX
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
    sh.poly([(-w(0), 0), (w(0), 0), (w(RISE), RISE), (-w(RISE), RISE)], "#f6f6f6", 0.0)      # roof face, back of the shell
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

def section_inset(sh, X0, Z0):
    """horizontal cut through one rib, square to the slope, 1:10 (model = local * F). outside at the bottom, inside (room) at the top."""
    F = 5.0
    M = lambda u, v: (X0 + F * u, Z0 + F * v)
    W_ = 700.0
    u0, u1 = 270.0, 270.0 + RIB_W
    # concrete outline first, then fills
    sh.poly([M(0, 0), M(W_, 0), M(W_, 400), M(0, 400)], "#000", 0.5)
    sh.poly([M(0, 0), M(W_, 0), M(W_, 400), M(0, 400)], "#fff", 0.0)
    sh.poly([M(0, 0), M(W_, 0), M(W_, 80), M(0, 80)], "url(#conc)", 0.0)            # outer skin 80
    sh.poly([M(0, 320), M(W_, 320), M(W_, 400), M(0, 400)], "url(#conc)", 0.0)      # inner layer 1, 80
    sh.poly([M(0, 240), M(u0, 240), M(u0, 320), M(0, 320)], "url(#conc)", 0.0)      # layer 2, 80, interrupted by the rib
    sh.poly([M(u1, 240), M(W_, 240), M(W_, 320), M(u1, 320)], "url(#conc)", 0.0)
    sh.poly([M(0, 80), M(u0, 80), M(u0, 240), M(0, 240)], "url(#dots)", 0.0)        # open air zone = insulation
    sh.poly([M(u1, 80), M(W_, 80), M(W_, 240), M(u1, 240)], "url(#dots)", 0.0)
    rib = [M(u0, 80), M(u1, 80), M(u1, 320), M(u0, 320)]
    sh.poly(rib, "#fff", 0.0); sh.poly(rib, "url(#cast)", 0.0); sh.poly(rib, "none", 0.45)
    for v in (80, 240, 320):
        sh.line([M(0, v), M(W_, v)], 0.25)
    sh.poly([M(0, 0), M(W_, 0), M(W_, 400), M(0, 400)], "none", 0.5)
    sh.layer = "REBAR"
    sh.poly([M(u0 + 30, 110), M(u1 - 30, 110), M(u1 - 30, 290), M(u0 + 30, 290)], "none", 8 / sh.scale, g.BLUE, tw=8)    # stirrup Ø8
    for u, v in ((u0 + 52, 140), (u1 - 52, 140), (u0 + 52, 260), (u1 - 52, 260)):
        sh.dot(*M(u, v), 8)                                                                                              # 4 Ø16
    sh.layer = None
    sh.text(*M(-20, 40), "outside", 2.4, "end"); sh.text(*M(-20, 360), "inside", 2.4, "end")
    sh.dim_h([X0 + F * v for v in (0, u0, u1, W_)], Z0 - 150, ext=Z0, labels=["{:g}".format(u0), "{:g}".format(RIB_W), "{:g}".format(W_ - u1)])
    sh.dim_v([Z0 + F * v for v in (0, 80, 240, 320, 400)], X0 + F * W_ + 150, ext=X0 + F * W_, labels=["80", "160", "80", "80"])
    sh.text(X0, Z0 + F * 400 + 160, "Section through one rib, square to the slope, 1:10", 3.2, "start", weight="bold")
    sh.callout(3, X0 + F * W_ + 650, Z0 + F * 160, *M(u1 - 60, 200))
    sh.callout(4, X0 + F * W_ + 650, Z0 + F * 360, *M(550, 360))
    sh.callout(5, X0 + F * W_ + 650, Z0 + F * 40, *M(550, 40))
    sh.callout(6, X0 + F * W_ + 650, Z0 + F * 260, *M(550, 160))

def common_legend(opt):
    L = [(3, True, "Rib (column): printed channel {:g} wide x {:g} deep in the 160 air zone + layer 2, filled with cast concrete, 4 Ø16 + Ø8 stirrups every 200 (assumed).".format(RIB_W, RIB_D)),
         (4, False, "Inner layer 1, 80: continuous, covers the grid on the room side."),
         (5, False, "Outer skin 80: continuous, covers the grid on the outside (cladding on it)."),
         (6, True, "Between the ribs the air zone stays open for thermal insulation (dotted).")]
    return L

def sheet(opt):
    segs, extra = grid_A() if opt == "A" else grid_B()
    if opt == "A":
        segs = segs + [("solid", [(-w(0), 0), (w(0), 0)]), ("ring", [(-w(RISE - TOP_RING / 2), RISE - TOP_RING / 2), (w(RISE - TOP_RING / 2), RISE - TOP_RING / 2)])]
    else:
        segs = segs + ring_segs(True)
    Lr, Lh = stats(segs)
    Lr4, Lh4 = 4 * Lr / 1000, 4 * Lh / 1000                                   # m, four faces (hips counted on both faces: shared, so a little high)
    nbars = 4
    steel = (Lr4 + Lh4) * nbars * BAR_KG_M[16]
    conc = (Lr4 + Lh4) * RIB_W * RIB_D * 1e-6
    if opt == "A":
        h1, h2 = extra
        title, sub = "Roof grid A: ruled-surface columns", "one roof face seen square on"
        legend = [(1, False, "Columns run in straight lines from the base edge (every {:g}) towards the crown edge, so they converge like the ruled surface of the sketch.".format(COL_PITCH)),
                  (2, False, "When the spacing drops to {:g} (about +{:.2f}) every other column stops; at about +{:.2f} only the four hip columns go on to the crown ring.".format(MIN_PITCH, (g.WALL_H + h1) / 1000, (g.WALL_H + h2) / 1000))]
        notes = ["Columns stop on a horizontal rib (at h = 3333 and 5000 above the eave); bars are lapped / hooked into it.",
                 "Horizontal ribs at 1667, 3333, 5000, plus the 300 solid base (bottom ring) and the top ring at the crown."]
    else:
        title, sub = "Roof grid B: diamond lattice", "one roof face seen square on"
        legend = [(1, False, "Diagonals parallel to the two hips (same inclination as the roof edges, {:.1f}° in the face), every {:g} along the base: equal diamonds {:g} wide.".format(math.degrees(math.atan2(RISE * VST, HALFB - g.OPEN / 2)), DIAG_P, DIAG_P)),
                  (2, False, "Bottom ring = the 300 solid base; top ring at the crown. The hips are two of the diagonals. No other horizontal ribs.")]
        notes = ["Every diagonal ends on a ring or on a hip, so no bar has a free end in the shell.",
                 "Diagonals do not stop as the roof narrows: the diamonds just get clipped by the hips."]
    legend = legend + common_legend(opt)
    notes += ["Rough quantities, four faces (hips counted twice, so slightly high): ribs {:.0f} m, {} bars, steel {:.0f} kg, cast concrete {:.1f} m3.".format(Lr4 + Lh4, "4 Ø16 each", steel, conc),
              "Rib size, bar count and the 160 x 240 channel are assumptions for the engineer to check. Elevation shows the face square on; true lengths are 1.25 x the drawn heights."]
    sh = Sheet(50, 157, 165, title, sub, legend, notes)
    sh.plain_legend = True
    draw_face(sh, segs)
    # dimensions and annotation
    xr = w(0) + 600
    sh.dim_v([0, SOLID], -w(0) - 600, ext=-w(0), labels=["300"])
    sh.dim_v([0, RISE], xr, ext=w(0), labels=["6000"])
    sh.dim_h([-w(0), w(0)], -450, ext=0, labels=["10000"])
    sh.dim_h([-w(RISE), w(RISE)], RISE + 450, ext=RISE, labels=["1000"])
    if opt == "A":
        for h in RING_H: sh.line([(-w(h) - 500, h), (-w(h) - 150, h)], 0.15, dash="2 1"); sh.text(-w(h) - 560, h - 60, "+{:.2f}".format((g.WALL_H + h) / 1000), 2.2, "end")
    if opt == "A":
        sh.callout(1, 6300, 2300, 3000 * w(2300) / HALFB, 2300)
        sh.callout(2, 6300, 4400, 4000 * w(extra[0]) / HALFB, extra[0])
    else:
        sh.callout(1, 6300, 2300, -1000, 2000)
        sh.callout(2, 6300, 5600, 0, RISE - TOP_RING / 2)
    sh.text(-HALFB - 500, RISE - 200, "Option " + opt, 4.2, "start", weight="bold")
    section_inset(sh, -5300, -4000)
    return sh

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
    for o in "AB":
        g.export(sheet(o), os.path.join(out, "roof-grid-" + o))
