"""Eave / roof-to-wall section, 1:10, for the 3DCP corbelled pyramid roof.
Model units mm, x = outward (0 = room-side face of wall and roof base), z = up (0 = top of ring beam).

Run:  python details/eave_section.py details/eave-section-1to10
      -> writes .svg, .pdf and .png  (needs: pip install shapely cairosvg)"""
import math
from shapely.geometry import Polygon, LineString, MultiLineString, box, Point
from shapely.ops import unary_union

# ---- from scripts/cork_house_roof.py (defaults) ----
H, S, T0, T1, W = 300.0, 150.0, 300.0, 100.0, 20.0
HOLE, BAR = 30.0, 12.0
K = S / H
# ---- assumption: 5 m room -> 12 courses (min_open 1000) ----
ROOM = 5000.0
n_c = 0
while ROOM - 2 * K * (n_c + 1) * H >= 1000.0:
    n_c += 1
ZTOP = n_c * H

def thick(z): return T0 + (T1 - T0) * z / ZTOP
def inner(z): return -K * z
def outer(z): return -K * z + thick(z)

# ---- assumptions ----
WALL_T = 300.0        # printed wall 20/260/20
RB_H = 300.0          # ring beam = top wall course, cavity concreted
ICB = 160.0           # expanded cork board, 2 x 80
BLK_H = 120.0         # insulating mounting block
BLK_FALL = 8.0
GUT_R = 75.0

ZBOT, ZBRK = -760.0, 1060.0
u = (-K, 1.0); ul = math.hypot(*u); u = (u[0] / ul, u[1] / ul)       # up the inner face
P0 = (inner(ZBRK), ZBRK)
def below_break(x, z): return (x - P0[0]) * u[0] + (z - P0[1]) * u[1] < 0
BIG = 5000
pp = (u[1], -u[0])
half = Polygon([(P0[0] + pp[0] * BIG, P0[1] + pp[1] * BIG),
                (P0[0] - pp[0] * BIG, P0[1] - pp[1] * BIG),
                (P0[0] - pp[0] * BIG - u[0] * BIG, P0[1] - pp[1] * BIG - u[1] * BIG),
                (P0[0] + pp[0] * BIG - u[0] * BIG, P0[1] + pp[1] * BIG - u[1] * BIG)])
CLIP = half.intersection(box(-2000, ZBOT, 2000, 3000))

# ---------------- svg helpers ----------------
out = []
def ptxt(x, z): return "{:.2f},{:.2f}".format(x, -z)

def poly_path(g):
    if g.is_empty: return ""
    geoms = getattr(g, "geoms", [g])
    d = ""
    for p in geoms:
        if p.geom_type != "Polygon": continue
        for ring in [p.exterior] + list(p.interiors):
            c = list(ring.coords)
            d += "M" + " L".join(ptxt(*q) for q in c) + "Z "
    return d

def fill(g, fillc, stroke="none", sw=0, extra=""):
    d = poly_path(g.intersection(CLIP))
    if d:
        out.append('<path d="{}" fill="{}" stroke="{}" stroke-width="{}" {}/>'.format(d, fillc, stroke, sw, extra))

def lines(g, sw, color="#000", dash=None, cap="butt", clip=True):
    if clip: g = g.intersection(CLIP)
    if g.is_empty: return
    geoms = getattr(g, "geoms", [g])
    d = ""
    for l in geoms:
        if l.geom_type == "LineString":
            d += "M" + " L".join(ptxt(*q) for q in l.coords) + " "
        elif l.geom_type == "Polygon":
            d += "M" + " L".join(ptxt(*q) for q in l.exterior.coords) + "Z "
    if d:
        out.append('<path d="{}" fill="none" stroke="{}" stroke-width="{}" stroke-linecap="{}" stroke-linejoin="round"{}/>'.format(
            d, color, sw, cap, ' stroke-dasharray="{}"'.format(dash) if dash else ""))

def outline(g, sw=5):
    lines(g.boundary if hasattr(g, "boundary") else g, sw)

def hatch(g, ang, sp, sw=1.3, offset=0.0):
    g = g.intersection(CLIP)
    if g.is_empty: return
    a = math.radians(ang)
    d = (math.cos(a), math.sin(a)); n = (-d[1], d[0])
    minx, miny, maxx, maxy = g.bounds
    cx, cy = (minx + maxx) / 2, (miny + maxy) / 2
    R = math.hypot(maxx - minx, maxy - miny)
    ls = []
    k = -R + offset
    while k < R:
        ox, oy = cx + n[0] * k, cy + n[1] * k
        ls.append([(ox - d[0] * R, oy - d[1] * R), (ox + d[0] * R, oy + d[1] * R)])
        k += sp
    lines(MultiLineString(ls).intersection(g), sw)

def zigzag_band(o, t, n, L, th, period, sw=1.4):
    """rigid-insulation zig-zag in a band: origin o, along t, across n, length L, thickness th."""
    pts = []
    s, up = 0.0, False
    while s <= L + period:
        a = th if up else 0.0
        pts.append((o[0] + t[0] * s + n[0] * a, o[1] + t[1] * s + n[1] * a))
        s += period / 2; up = not up
    return LineString(pts)

def text(x, z, s, size=26, anchor="start", weight="normal", rot=0, italic=False):
    tr = ' transform="rotate({:.2f} {:.2f} {:.2f})"'.format(rot, x, -z) if rot else ""
    out.append('<text x="{:.2f}" y="{:.2f}" font-size="{}" text-anchor="{}" font-weight="{}"{}{}>{}</text>'.format(
        x, -z, size, anchor, weight, ' font-style="italic"' if italic else "", tr, s))

def cm(v):
    """mm -> German cm notation with superscript mm."""
    c, m = divmod(int(round(v)), 10)
    return "{}<tspan dy='-9' font-size='17'>{}</tspan>".format(c, m) if m else str(c)

def dim_chain(pts, level, horizontal=True, ext_from=None, sw=1.3):
    """dimension chain; pts = coordinates along axis; ext_from = list of start points for extension lines."""
    tick = 14
    if horizontal:
        lines(LineString([(pts[0] - 30, level), (pts[-1] + 30, level)]), sw, clip=False)
        for i, p in enumerate(pts):
            z0 = ext_from[i] if ext_from else level + 60
            lines(LineString([(p, z0 - 10 if z0 > level else z0 + 10), (p, level - 20)]), 1.0, clip=False)
            lines(LineString([(p - tick, level - tick), (p + tick, level + tick)]), 2.6, clip=False)
        for a, b in zip(pts, pts[1:]):
            text((a + b) / 2, level + 14, cm(b - a), 30, "middle")
    else:
        lines(LineString([(level, pts[0] - 30), (level, pts[-1] + 30)]), sw, clip=False)
        for i, p in enumerate(pts):
            x0 = ext_from[i] if ext_from is not None else level + 60
            lines(LineString([(x0 - 10 if x0 < level else x0 + 10, p), (level + 20, p)]), 1.0, clip=False)
            lines(LineString([(level - tick, p - tick), (level + tick, p + tick)]), 2.6, clip=False)
        for a, b in zip(pts, pts[1:]):
            text(level - 14, (a + b) / 2, cm(b - a), 30, "middle", rot=-90)

def callout(n, cx, cz, tx, tz, assumed):
    lines(LineString([(cx, cz), (tx, tz)]), 1.3, clip=False)
    out.append('<circle cx="{:.1f}" cy="{:.1f}" r="7" fill="#000"/>'.format(tx, -tz))
    out.append('<circle cx="{:.1f}" cy="{:.1f}" r="34" fill="{}" stroke="#000" stroke-width="3"/>'.format(
        cx, -cz, "#fff" if assumed else "#000"))
    out.append('<text x="{:.1f}" y="{:.1f}" font-size="34" text-anchor="middle" fill="{}">{}</text>'.format(
        cx, -cz + 12, "#000" if assumed else "#fff", n))

def band_inner(a, b, z0, z1):
    """roof band between inner(z)+a and inner(z)+b."""
    return Polygon([(inner(z0) + a, z0), (inner(z1) + a, z1), (inner(z1) + b, z1), (inner(z0) + b, z0)])

def band_outer(a, b, z0, z1):
    """roof band between outer(z)-a and outer(z)-b (a > b)."""
    return Polygon([(outer(z0) - a, z0), (outer(z1) - a, z1), (outer(z1) - b, z1), (outer(z0) - b, z0)])

# ================= geometry (draft 3: roof = wall build-up) =================
ZR = ZBRK + 400
# Liam: wall 24 RC / insulation / 8 concrete; roof the same structure; roof 8 m tall; ring beam
IN_T, XPS_W, OUT_T = 240.0, 150.0, 80.0
XI0, XI1, XO1 = IN_T, IN_T + XPS_W, IN_T + XPS_W + OUT_T
RISE, TIN0, TIN1 = 8000.0, 240.0, 80.0        # proposed taper of the roof's inner leaf
XPS_R = 150.0                                   # roof lattice, horizontal width
RB = 300.0                                      # ring beam height
def tin(z): return TIN0 + (TIN1 - TIN0) * z / RISE
def lin(z): return inner(z) + tin(z)            # outer face of roof inner leaf
def ins(z): return lin(z) + XPS_R               # outer face of roof insulation
def ofc(z): return ins(z) + OUT_T               # outer face of roof
def band(f0, f1, z0, z1): return Polygon([(f0(z0), z0), (f0(z1), z1), (f1(z1), z1), (f1(z0), z0)])

tdir = (-(K + (TIN0 - TIN1) / RISE), 1.0); tl = math.hypot(*tdir); tdir = (tdir[0] / tl, tdir[1] / tl)
ndir = (tdir[1], -tdir[0])

def stipple(g, sp=22):
    g = g.intersection(CLIP)
    if g.is_empty: return
    minx, miny, maxx, maxy = g.bounds
    import random as _r
    rr = _r.Random(3)
    d = ""
    y = miny
    while y < maxy:
        x = minx + rr.uniform(0, sp)
        while x < maxx:
            px, py = x + rr.uniform(-6, 6), y + rr.uniform(-6, 6)
            if g.contains(Point(px, py)):
                d += "M{:.1f},{:.1f}h0.1 ".format(px, -py)
            x += sp
        y += sp * 0.8
    out.append('<path d="{}" stroke="#000" stroke-width="5" stroke-linecap="round"/>'.format(d))

def rc(g, sw=5):
    fill(g, "#fff"); hatch(g, 45, 32); outline(g, sw)

def bar_line(pts, w=8, col="#000", dash=None):
    lines(LineString(pts), w, col, dash=dash)

def dot(x, z, r=5):
    if CLIP.contains(Point(x, z)):
        out.append('<circle cx="{:.1f}" cy="{:.1f}" r="{}" fill="#000"/>'.format(x, -z, r))

# ---- wall ----
wall_in = box(0, ZBOT, IN_T, -RB)
ring = box(0, -RB, IN_T, 0)
wall_x = box(XI0, ZBOT, XI1, 0)
wall_out = box(XI1, ZBOT, XO1, 0)
rc(wall_in); rc(wall_out)
fill(ring, "#fff"); hatch(ring, 45, 32); hatch(ring, -45, 32, 0.9); outline(ring, 5)
fill(wall_x, "#fff")
stipple(wall_x)
outline(wall_x, 4)
for bx in (40, IN_T - 40):
    bar_line([(bx, ZBOT), (bx, -RB + 40)])
    for bz in range(int(-RB - 100), int(ZBOT), -200):
        dot(bx + (9 if bx < 100 else -9), bz)
xm = (XI1 + XO1) / 2
for bz in range(-150, int(ZBOT), -150):
    dot(xm, bz, 3)
for zj in (-RB, -2 * RB):
    lines(LineString([(XI1, zj), (XO1, zj)]), 4, "#fff")
# ring beam: 4 Ø16 + stirrup Ø8
for bx in (52, IN_T - 52):
    for bz in (-RB + 52, -52):
        dot(bx, bz, 8)
lines(Polygon([(36, -RB + 36), (IN_T - 36, -RB + 36), (IN_T - 36, -36), (36, -36)]).exterior, 4)
# ---- roof ----
r_in = band(inner, lin, 0, ZR)
r_x = band(lin, ins, 0, ZR)
r_out = band(ins, ofc, 4, ZR)
rc(r_in); rc(r_out)
fill(r_x, "#fff")
th = XPS_R * ndir[0]
stipple(r_x)
outline(r_x, 4)
for zj in (H, 2 * H, 3 * H, 4 * H):
    lines(LineString([(inner(zj), zj), (lin(zj), zj)]), 4, "#fff")
    lines(LineString([(ins(zj), zj), (ofc(zj), zj)]), 4, "#fff")
# inner leaf meshes (two layers near the base) + starters from the ring beam
zz = [0, ZR]
bar_line([(inner(z) + 42, z) for z in zz])
bar_line([(lin(z) - 42, z) for z in zz])
for z in range(100, int(ZR), 200):
    dot(inner(z) + 51, z); dot(lin(z) - 51, z)
bar_line([(64, -RB + 60), (64, 0)] + [(inner(z) + 64, z) for z in (0, 650)], 8, "#666")
bar_line([(IN_T - 64, -RB + 60), (IN_T - 64, 0)] + [(lin(z) - 64, z) for z in (0, 650)], 8, "#666")
# outer skin: wire in bed joints
for zj in range(150, int(ZR), 150):
    dot((ins(zj) + ofc(zj)) / 2, zj, 3)
# printed drip nose on the bottom roof course
nose = Polygon([(ins(4), 4), (XO1 + 25, 4), (XO1 + 25, 34), (ofc(60), 60)])
fill(nose, "#fff"); hatch(nose, 45, 32); outline(nose, 5)
lines(LineString([(XO1 + 8, 4), (XO1 + 8, 12)]), 4)
# water-repellent coating on the outside faces
lines(LineString([(ofc(z) + 6, z) for z in (60, ZR)]), 2.5, dash="5 7")
lines(LineString([(XO1 + 6, -20), (XO1 + 6, ZBOT)]), 2.5, dash="5 7")
# outlines / joint lines
lines(LineString([(0, 0), (XI0, 0)]), 2)
lines(LineString([(0, -RB), (XI0, -RB)]), 2)

# ---- break lines ----
b0 = (P0[0] - pp[0] * 100, P0[1] - pp[1] * 100)
b1 = (P0[0] + pp[0] * 720, P0[1] + pp[1] * 720)
lines(LineString([b0, b1]), 5, dash="60 14 8 14", clip=False)
lines(LineString([(-120, ZBOT), (XO1 + 120, ZBOT)]), 5, dash="60 14 8 14", clip=False)

# ---- dims ----
dim_chain([0, XI0, XI1, XO1], ZBOT - 90, True, ext_from=[ZBOT] * 4)
dim_chain([-RB, 0, H, 2 * H, 3 * H], -720, False, ext_from=[0, 0, inner(H), inner(2 * H), inner(3 * H)])
zt = 900
xs = [inner(zt), lin(zt), ins(zt), ofc(zt)]
lv = zt + 75
lines(LineString([(xs[0] - 25, lv), (xs[-1] + 25, lv)]), 1.3, clip=False)
for xx in xs:
    lines(LineString([(xx, zt + 8), (xx, lv + 18)]), 1.0, clip=False)
    lines(LineString([(xx - 12, lv - 12), (xx + 12, lv + 12)]), 2.6, clip=False)
for a, b in zip(xs, xs[1:]):
    text((a + b) / 2, lv + 12, cm(b - a), 26, "middle")
# eave nose
lines(LineString([(XO1, -60), (XO1 + 25, -60)]), 1.3, clip=False)
for xx in (XO1, XO1 + 25):
    lines(LineString([(xx, -45), (xx, -75)]), 1.0, clip=False)
    lines(LineString([(xx - 9, -69), (xx + 9, -51)]), 2.6, clip=False)
text(XO1 + 43, -70, cm(25), 24)
# slope triangle
zs = 560
p1 = (inner(zs) - 170, zs); p2 = (p1[0] + 150 * 0.8, p1[1] - 300 * 0.8)
lines(LineString([p1, (p1[0], p2[1]), p2, p1]), 1.3, clip=False)
text(p1[0] - 12, (p1[1] + p2[1]) / 2, "30", 24, "end")
text((p1[0] + p2[0]) / 2, p2[1] - 32, "15", 24, "middle")
text(p2[0] + 18, p2[1] + 40, "63,4°", 24)

text(-560, -430, "inside (cooled)", 30, italic=True)
text(-560, -475, "θi = 26 °C", 26, italic=True)
text(560, -650, "outside", 30, italic=True)
text(560, -695, "θe ≈ 31 °C (Aug.)", 26, italic=True)

A = True; C = False
callout(1, -540, 150, inner(170) + 120, 170, A)
callout(2, -300, -230, 120, -230, A)
callout(3, -300, -80, 64, -100, A)
callout(4, 360, 640, (lin(560) + ins(560)) / 2, 560, A)
callout(5, 130, 1010, ofc(880) + 6, 880, A)
callout(6, 480, 400, (ins(330) + ofc(330)) / 2, 330, C)
callout(7, 640, 120, XO1 + 15, 20, A)
callout(8, -330, -600, 120, -600, C)
callout(9, 640, -260, (XI0 + XI1) / 2, -300, A)
callout(10, 640, -420, XO1 - 40, -450, C)
callout(11, 640, -110, (XI0 + XI1) / 2, -20, A)
callout(12, -560, 650, inner(650) - 2, 650, C)

# ---- inset: whole roof at 1:200 (drawn in model units, scaled separately) ----
ins_out = []
def ip(x, z): return "{:.1f},{:.1f}".format(x, -z)
def ipoly(f0, f1, z0, z1, fillc):
    pts = [(f0(z0), z0), (f0(z1), z1), (f1(z1), z1), (f1(z0), z0)]
    ins_out.append('<path d="M{}Z" fill="{}" stroke="#000" stroke-width="12"/>'.format(" L".join(ip(*q) for q in pts), fillc))
ipoly(inner, lin, 0, RISE, "#bbb")
ipoly(lin, ins, 0, RISE, "#fff")
ipoly(ins, ofc, 0, RISE, "#666")
ins_out.append('<path d="M{}Z" fill="#888" stroke="#000" stroke-width="12"/>'.format(" L".join(ip(*q) for q in [(0, -1200), (0, 0), (IN_T, 0), (IN_T, -1200)])))
ins_out.append('<path d="M{}Z" fill="#666" stroke="#000" stroke-width="12"/>'.format(" L".join(ip(*q) for q in [(XI1, -1200), (XI1, 0), (XO1, 0), (XO1, -1200)])))
ins_out.append('<path d="M{} L{}" stroke="#000" stroke-width="8" stroke-dasharray="120 50 20 50"/>'.format(ip(-4500, RISE), ip(-3600, RISE)))
for zl in (0, 4000, 8000):
    x0 = ofc(zl) + 200
    ins_out.append('<path d="M{} L{}" stroke="#000" stroke-width="6"/>'.format(ip(ofc(zl) + 60, zl), ip(x0 - 40, zl)))
    ins_out.append('<text x="{:.0f}" y="{:.0f}" font-size="270">{} cm  (z = {:.0f} m)</text>'.format(x0, -zl + 130, cm(tin(zl)).replace("dy='-9' font-size='17'", "dy='-90' font-size='170'"), zl / 1000))
ins_out.append('<text x="{:.0f}" y="{:.0f}" font-size="270">8,00 m</text>'.format(-5600, -RISE / 2))
ins_out.append('<path d="M{} L{}" stroke="#000" stroke-width="6"/>'.format(ip(-4300, 0), ip(-4300, RISE)))
for zl in (0, RISE):
    ins_out.append('<path d="M{} L{}" stroke="#000" stroke-width="10"/>'.format(ip(-4420, zl - 120), ip(-4180, zl + 120)))
inset_svg = "\n".join(ins_out)
# ---- plan of one wall piece, 1:20 (x = along the wall, y = depth, inside at the top) ----
pl = []
PL_L = 1650.0
LEG = 412.0                                     # run of one zig-zag leg (150 deep at ~20 deg)
def pp_(x, y): return "{:.1f},{:.1f}".format(x, y)
def phatch(x0, y0, x1, y1):
    for k in range(-40, 60):
        ls = LineString([(k * 60, y0), (k * 60 + (y1 - y0), y1)]).intersection(box(x0, y0, x1, y1))
        if not ls.is_empty and ls.geom_type == "LineString":
            c = list(ls.coords)
            pl.append('<path d="M{} L{}" stroke="#000" stroke-width="3"/>'.format(pp_(*c[0]), pp_(*c[-1])))
    pl.append('<rect x="{}" y="{}" width="{}" height="{}" fill="none" stroke="#000" stroke-width="10"/>'.format(x0, y0, x1 - x0, y1 - y0))
phatch(0, 0, PL_L, IN_T)
for i_, x in enumerate(range(150, int(PL_L), 250)):
    y = 60 if i_ % 2 == 0 else IN_T - 60
    pl.append('<circle cx="{}" cy="{}" r="15" fill="#c8c8c8" stroke="#000" stroke-width="5"/>'.format(x, y))
    pl.append('<circle cx="{}" cy="{}" r="6" fill="#000"/>'.format(x, y))
y0, y1 = IN_T, IN_T + XPS_W
pts, x, up = [], -LEG / 2, False
while x < PL_L + LEG:
    pts.append((x, y1 - 10 if up else y0 + 10)); x += LEG; up = not up
rib = LineString(pts).intersection(box(0, y0, PL_L, y1))
dots = ""
rr2 = __import__("random").Random(5)
yy = y0 + 10
while yy < y1 - 6:
    xx = rr2.uniform(0, 22)
    while xx < PL_L:
        dots += "M{:.1f},{:.1f}h0.1 ".format(xx + rr2.uniform(-5, 5), yy + rr2.uniform(-4, 4)); xx += 24
    yy += 20
pl.append('<path d="{}" stroke="#000" stroke-width="6" stroke-linecap="round"/>'.format(dots))
pl.append('<path d="M{}" fill="none" stroke="#fff" stroke-width="44"/>'.format(" L".join(pp_(*q) for q in rib.coords)))
pl.append('<path d="M{}" fill="none" stroke="#000" stroke-width="20"/>'.format(" L".join(pp_(*q) for q in rib.coords)))
phatch(0, y1, PL_L, y1 + OUT_T)
for xb in (0, PL_L):
    pl.append('<path d="M{} L{}" stroke="#000" stroke-width="8" stroke-dasharray="60 14 8 14"/>'.format(pp_(xb, -60), pp_(xb, y1 + OUT_T + 60)))
def pdim(a_, b_, at, vertical, label):
    if vertical:
        pl.append('<path d="M{} L{}" stroke="#000" stroke-width="4"/>'.format(pp_(at, a_), pp_(at, b_)))
        for v in (a_, b_):
            pl.append('<path d="M{} L{}" stroke="#000" stroke-width="7"/>'.format(pp_(at - 22, v - 22), pp_(at + 22, v + 22)))
        pl.append('<text x="{}" y="{}" font-size="70">{}</text>'.format(at + 40, (a_ + b_) / 2 + 25, label))
    else:
        pl.append('<path d="M{} L{}" stroke="#000" stroke-width="4"/>'.format(pp_(a_, at), pp_(b_, at)))
        for v in (a_, b_):
            pl.append('<path d="M{} L{}" stroke="#000" stroke-width="7"/>'.format(pp_(v - 22, at + 22), pp_(v + 22, at - 22)))
        pl.append('<text x="{}" y="{}" font-size="70" text-anchor="middle">{}</text>'.format((a_ + b_) / 2, at - 25, label))
pdim(0, IN_T, PL_L + 60, True, "24")
pdim(y0, y1, PL_L + 60, True, "15")
pdim(y1, y1 + OUT_T, PL_L + 60, True, "8")
xt = [q[0] for q in pts if q[1] > y0 + 50 and 0 < q[0] < PL_L]
if len(xt) >= 2:
    pdim(xt[0], xt[1], y1 + OUT_T + 140, False, "≈ 82")
pl.append('<text x="20" y="-40" font-size="70">inside</text>')
pl.append('<text x="20" y="{}" font-size="70">outside</text>'.format(y1 + OUT_T + 120))
plan_svg = "\n".join(pl)


svg_body = "\n".join(out)

# ================= page =================
PW, PH = 420, 297
S10 = 0.1
OX, OY = 108, 150
legend = [
    (1, A, "Roof inner leaf, printed reinforced concrete, 24 at the ring beam tapering to 8 (one bead) at the top of the 8 m roof; bars in printed holes stop at 9 (z ≈ 7.5 m)"),
    (2, A, "Ring beam 24 × 30 on the wall inner leaf, cast in place, 4 Ø16, stirrups Ø8 / 150; ties the roof's outward push"),
    (3, A, "Starter bars Ø12 from the ring beam into the roof leaf, lap 650"),
    (4, C, "Printed lattice 150 (your idea): one 20 mm zig-zag bead at ≈ 20°, touching each leaf every ≈ 80 cm (see plan); cells filled with cork granulate or water-repellent perlite (λ ≈ 0.05); U ≈ 0.47"),
    (5, A, "Breathable water-repellent mineral coating on all outside faces (moisture control on the outside in a cooled building)"),
    (6, C, "Roof outer skin 80, printed with the lattice and inner leaf as one piece; stainless wire in bed joints; light colour"),
    (7, A, "Printed drip nose 2⁵ on the bottom roof course, so rain drips clear of the wall; no gutter"),
    (8, C, "Wall inner leaf, reinforced concrete 240, mesh both faces"),
    (9, C, "Wall lattice 150, same as (4)"),
    (10, C, "Wall outer skin 80, same as (6)"),
    (11, A, "Fill runs on from the wall lattice into the roof lattice: no gap in the insulation at the eave; cap it at the top opening"),
    (12, C, "Room-side face: printed concrete, pitch 63.4° (course 300, step 150 from the roof script)"),
]
def wrap(s, n):
    words, lines_, cur = s.split(), [], ""
    for w_ in words:
        if len(cur) + len(w_) + 1 > n:
            lines_.append(cur); cur = w_
        else:
            cur = (cur + " " + w_).strip()
    lines_.append(cur)
    return lines_

leg = []
LX, LY = 262, 30
leg.append('<text x="{}" y="{}" font-size="5.2" font-weight="bold">Eave section, roof-to-wall junction</text>'.format(LX, LY - 8))
leg.append('<text x="{}" y="{}" font-size="3.2">Printed pieces: inner leaf / filled lattice / skin · Ishigaki · 1:10 at A3 · cm</text>'.format(LX, LY - 2))
y = LY + 8
for n, assumed, s in legend:
    leg.append('<circle cx="{}" cy="{}" r="2.6" fill="{}" stroke="#000" stroke-width="0.3"/>'.format(LX + 2.6, y - 1.1, "#fff" if assumed else "#000"))
    leg.append('<text x="{}" y="{}" font-size="2.9" text-anchor="middle" fill="{}">{}</text>'.format(LX + 2.6, y, "#000" if assumed else "#fff", n))
    for i, l in enumerate(wrap(s, 70)):
        leg.append('<text x="{}" y="{:.1f}" font-size="2.9">{}</text>'.format(LX + 8, y + i * 3.7, l))
    y += 3.7 * len(wrap(s, 70)) + 2.4
y += 2
leg.append('<circle cx="{}" cy="{}" r="2.2" fill="#000"/>'.format(LX + 2.6, y - 1))
leg.append('<text x="{}" y="{}" font-size="2.9">from scripts/cork_house_roof.py or given by you</text>'.format(LX + 8, y))
y += 5
leg.append('<circle cx="{}" cy="{}" r="2.2" fill="#fff" stroke="#000" stroke-width="0.3"/>'.format(LX + 2.6, y - 1))
leg.append('<text x="{}" y="{}" font-size="2.9">assumed by me: not defined yet</text>'.format(LX + 8, y))
y += 8
notes = [
    "Each piece = inner leaf + lattice + outer skin, printed in one go, open top/bottom.",
    "Ribs are the heat bridges: few, long, flat ribs (≈ 20°) keep U ≈ 0.47. Empty cells ≈ 2.0.",
    "Inner leaf 24 → 8 (load ≈ 0.3 MPa at the base). Widths horizontal, as printed.",
    "Hand estimates, not engineered or simulated: confirm structure + U-value.",
]
leg.append('<text x="{}" y="{}" font-size="3.2" font-weight="bold">Notes</text>'.format(LX, y)); y += 4.6
for l in notes:
    leg.append('<text x="{}" y="{:.1f}" font-size="2.9">{}</text>'.format(LX, y, l)); y += 3.8

# scale bar 0-50 cm at 1:10
sb_y = 284
sb = ['<g stroke="#000" stroke-width="0.25">']
for i in range(5):
    sb.append('<rect x="{}" y="{}" width="10" height="1.6" fill="{}"/>'.format(LX + i * 10, sb_y, "#000" if i % 2 == 0 else "#fff"))
sb.append('</g>')
for i in range(0, 6):
    sb.append('<text x="{}" y="{}" font-size="2.6" text-anchor="middle">{}</text>'.format(LX + i * 10, sb_y - 1.2, i * 10))
sb.append('<text x="{}" y="{}" font-size="2.6">cm</text>'.format(LX + 53, sb_y + 1.6))
sb.append('<text x="{}" y="{}" font-size="2.6">Studio V · GSAPP · LiamEwald/pyramid-roof · draft 4, 2026-10-11</text>'.format(LX + 70, sb_y + 1.6))

svg = """<svg xmlns="http://www.w3.org/2000/svg" width="{PW}mm" height="{PH}mm" viewBox="0 0 {PW} {PH}" font-family="DejaVu Sans, Helvetica, Arial, sans-serif">
<rect width="{PW}" height="{PH}" fill="#fff"/>
<rect x="8" y="8" width="{iw}" height="{ih}" fill="none" stroke="#000" stroke-width="0.35"/>
<g transform="translate({OX} {OY}) scale({s})">
{body}
</g>
{leg}
{sb}
<g transform="translate({LX} 231) scale(0.05)">{plan}</g>
<text x="{LX}" y="216" font-size="3.2" font-weight="bold">Plan of one wall piece, 1:20</text>
<text x="{LX}" y="220.5" font-size="2.6">inner leaf with rebar holes · zig-zag rib, cells filled · outer skin</text>
<g transform="translate(238 274) scale(0.01)">{inset}</g>
<text x="194" y="184" font-size="3.2" font-weight="bold">Whole roof, 1:100</text>
<text x="194" y="188.5" font-size="2.6">inner leaf (grey) tapers 24 → 8</text>
</svg>""".format(PW=PW, PH=PH, iw=PW - 16, ih=PH - 16, OX=OX, OY=OY, s=S10, body=svg_body, leg="\n".join(leg), sb="\n".join(sb), inset=inset_svg, plan=plan_svg, LX=LX)

import sys
dst = sys.argv[1]
open(dst + ".svg", "w").write(svg)
import cairosvg
cairosvg.svg2pdf(bytestring=svg.encode(), write_to=dst + ".pdf")
cairosvg.svg2png(bytestring=svg.encode(), write_to=dst + ".png", output_width=4200)
print("courses", n_c, "ztop", ZTOP, "t@900", thick(900))
