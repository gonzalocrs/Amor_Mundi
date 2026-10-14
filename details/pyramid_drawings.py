"""Plan, total section and eave detail for the 10 x 10 m buttressed pyramid roof (3D concrete printed).
Standalone: no dependency on scripts/cork_house_roof.py. Model units mm. Every number you may want to change is in PARAMETERS.

Run:  python details/pyramid_drawings.py [out_dir]
      -> pyramid-plan.svg, pyramid-section.svg, pyramid-detail.svg (+ .pdf/.png if `pip install cairosvg` works)"""
import math, os, sys

# ================= PARAMETERS =================
CLEAR = 10000.0            # clear inside dimension, square plan
WALL = 400.0               # wall thickness = roof base width
SOLID_H = 300.0            # the first 300 (vertical) of the roof is completely solid concrete, no air zone; there is no separate ring beam
WALL_H = 2500.0            # ground to top of wall (= eave, roof base)
BUT_TOTAL, BUT_W = 1000.0, 400.0  # buttress: 1000 long measured from the inner wall face (flush with the wall), 400 wide (= the wall thickness, constant along its length)
BUT_L = BUT_TOTAL - WALL          # so it projects only this far beyond the outer wall face
OPEN = 1000.0              # square opening at the crown (inner face)
RISE = 6000.0              # roof height
T_LEAF0, T_LEAF1 = 160.0, 80.0   # inner structural leaf, horizontal width at base / crown
T_LAT, T_SKIN = 160.0, 80.0      # lattice zone and outer skin (constant)
CLAD = 30.0                # outer cladding on the roof (assumed)
INS = 100.0                # insulation outside the printed roof shell (assumed)
INS_LW = 0.07              # line weight of every insulation outline and symbol: always much thinner than the structural lines (0.3 to 0.7)
BUT_SPACING = 1500.0       # buttresses about every 1.5 m along each wall
WALL_LAYERS = (160.0, 160.0, 80.0)   # wall inner leaf (two 80 layers) / air zone / outer layer: same pattern as the roof
FOOT_W, FOOT_T, FOOT_Z = 1800.0, 250.0, -1000.0   # footing width, thickness, underside level (assumed)
HALF = CLEAR / 2
RUN = HALF - OPEN / 2
K = RUN / RISE             # inward lean of the roof (horizontal per vertical)
SLOPE = math.degrees(math.atan2(RISE, RUN))
assert abs(sum(WALL_LAYERS) - WALL) < 1e-6

def but_pos():
    """buttress axes along a wall (centre line, corners included): equal bays of about BUT_SPACING"""
    c = HALF + WALL / 2
    nb = int(round(2 * c / BUT_SPACING))
    return [-c + 2 * c * k / nb for k in range(nb + 1)]

def leaf(h): return T_LEAF0 + (T_LEAF1 - T_LEAF0) * h / RISE
# layer thicknesses are square to the slope; horizontally each is wider by 1 / sin(slope)
SIN = math.sin(math.radians(SLOPE))
SH = 1.0 / SIN
def rx(h):
    x = -K * h
    return (x, x + leaf(h) * SH, x + (leaf(h) + T_LAT) * SH, x + (leaf(h) + T_LAT + T_SKIN) * SH)

BLUE, PINK = "#000", "#f4d6d6"   # BLUE = rebar colour (black: the drawings are greyscale); PINK = marker for the open air pockets

# ================= svg helpers =================
class Sheet:
    def __init__(self, scale, ox, oz, title, sub, legend, notes, w=420, h=297):
        self.s, self.ox, self.oz, self.w, self.h = 1.0 / scale, ox, oz, w, h
        self.scale = scale
        self.o = []; self.title, self.sub, self.legend, self.notes = title, sub, legend, notes
        self.plain_legend = False
        self.rec = []; self.layer = None; self.mute = 0     # recorder for the CAD (DXF) export: model-space geometry, mm
    def _rec(self, *a):
        if not self.mute: self.rec.append(a)
    def P(self, x, z): return (self.ox + x * self.s, self.oz - z * self.s)
    def pts(self, ps): return " ".join("{:.2f},{:.2f}".format(*self.P(*p)) for p in ps)
    def poly(self, ps, fill="none", sw=0.25, stroke="#000", extra="", join="round", tw=None):
        if fill == PINK:
            fill = "#fff"                  # lattice cells are open air pockets (ventilation)
        self._rec("poly", list(ps), fill, sw, stroke, self.layer, tw)
        self.o.append('<polygon points="{}" fill="{}" stroke="{}" stroke-width="{}" stroke-linejoin="{}" {}/>'.format(self.pts(ps), fill, stroke, sw, join, extra))
    def line(self, ps, sw=0.25, color="#000", dash=None, extra="", tw=None):
        self._rec("line", list(ps), sw, color, dash, self.layer, tw)
        self.o.append('<polyline points="{}" fill="none" stroke="{}" stroke-width="{}" stroke-linejoin="round"{} {}/>'.format(
            self.pts(ps), color, sw, ' stroke-dasharray="{}"'.format(dash) if dash else "", extra))
    def paths(self, polys, sw=0.25, color="#000", layer=None):
        self._rec("paths", [list(p) for p in polys], sw, layer or self.layer)
        d = " ".join("M" + " L".join("{:.1f},{:.1f}".format(*self.P(*q)) for q in pl) for pl in polys)
        self.o.append('<path d="{}" fill="none" stroke="{}" stroke-width="{}" stroke-linejoin="round"/>'.format(d, color, sw))
    def dot(self, x, z, r_mm, color=BLUE):
        self._rec("circle", x, z, max(r_mm, 0.35 * self.scale), True, self.layer)
        px, py = self.P(x, z)
        self.o.append('<circle cx="{:.2f}" cy="{:.2f}" r="{:.2f}" fill="{}"/>'.format(px, py, max(r_mm * self.s, 0.35), color))
    def text(self, x, z, s, size=2.6, anchor="middle", weight="normal", rot=0, color="#000", italic=False):
        self._rec("text", x, z, s, size, anchor, rot, self.layer)
        px, py = self.P(x, z)
        tr = ' transform="rotate({} {:.2f} {:.2f})"'.format(rot, px, py) if rot else ""
        self.o.append('<text x="{:.2f}" y="{:.2f}" font-size="{}" text-anchor="{}" font-weight="{}" fill="{}"{}{}>{}</text>'.format(
            px, py, size, anchor, weight, color, ' font-style="italic"' if italic else "", tr, s))
    def circle_label(self, x, z, label, r=2.6, fill="#fff", tc="#000"):
        self._rec("circle", x, z, r * self.scale, False, "ANNOTATION")
        self._rec("text", x, z - r * 0.36 * self.scale, str(label), r * 1.15, "middle", 0, "ANNOTATION")
        self.mute += 1
        px, py = self.P(x, z)
        self.o.append('<circle cx="{:.2f}" cy="{:.2f}" r="{}" fill="{}" stroke="#000" stroke-width="0.3"/>'.format(px, py, r, fill))
        self.o.append('<text x="{:.2f}" y="{:.2f}" font-size="{}" text-anchor="middle" fill="{}">{}</text>'.format(px, py + r * 0.36, r * 1.15, tc, label))
        self.mute -= 1
    def callout(self, n, x, z, tx, tz):
        old, self.layer = self.layer, "ANNOTATION"
        self.line([(x, z), (tx, tz)], 0.2)
        self.dot(tx, tz, 0, "#000")
        self.circle_label(x, z, n, 2.4)
        self.layer = old
    def dim_h(self, xs, z, text_off=1.0, ext=None, labels=None, size=2.5):
        """horizontal dimension chain at height z; ext = z the extension lines start from."""
        _ol, self.layer = self.layer, "DIMS"
        s = self.s; tick = 1.2 / s
        self.line([(xs[0] - 1.5 / s, z), (xs[-1] + 1.5 / s, z)], 0.2)
        for x in xs:
            e = ext if ext is not None else z
            sgn = 1 if e > z else -1
            self.line([(x, e - sgn * 0.8 / s), (x, z - sgn * 1.2 / s)], 0.12)
            self.line([(x - tick / 2, z - tick / 2), (x + tick / 2, z + tick / 2)], 0.45)
        for i, (a, b) in enumerate(zip(xs, xs[1:])):
            t = labels[i] if labels else "{:g}".format(round(b - a))
            self.text((a + b) / 2, z + 0.9 / s, t, size)
        self.layer = _ol
    def dim_v(self, zs, x, ext=None, labels=None, size=2.5):
        _ol, self.layer = self.layer, "DIMS"
        s = self.s; tick = 1.2 / s
        self.line([(x, zs[0] - 1.5 / s), (x, zs[-1] + 1.5 / s)], 0.2)
        for z in zs:
            e = ext if ext is not None else x
            sgn = 1 if e > x else -1
            self.line([(e - sgn * 0.8 / s, z), (x - sgn * 1.2 / s, z)], 0.12)
            self.line([(x - tick / 2, z - tick / 2), (x + tick / 2, z + tick / 2)], 0.45)
        for i, (a, b) in enumerate(zip(zs, zs[1:])):
            t = labels[i] if labels else "{:g}".format(round(b - a))
            self.text(x - 0.9 / self.s, (a + b) / 2, t, size, rot=-90)
        self.layer = _ol
    def level(self, x, z, label, side=1):
        _ol, self.layer = self.layer, "DIMS"
        s = self.s
        self.line([(x, z), (x + side * 6 / s, z)], 0.2)
        self.poly([(x, z), (x + 1.2 / s, z + 1.6 / s), (x - 1.2 / s, z + 1.6 / s)], "#000", 0.1)
        self.text(x + side * 7 / s, z - 0.5 / s, label, 2.5, "start" if side > 0 else "end")
        self.layer = _ol
    def svg(self):
        W, H = self.w, self.h
        tb = W - 112                      # title block x
        parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="{}mm" height="{}mm" viewBox="0 0 {} {}" font-family="Helvetica, Arial, sans-serif">'.format(W, H, W, H),
                 '<defs>'
                 '<pattern id="conc" width="1.6" height="1.6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="1.6" stroke="#000" stroke-width="0.14"/></pattern>'
                 '<pattern id="earth" width="2.4" height="2.4" patternUnits="userSpaceOnUse" patternTransform="rotate(-45)"><line x1="0" y1="0" x2="0" y2="2.4" stroke="#777" stroke-width="0.12"/></pattern>'
                 '<pattern id="cast" width="1.6" height="1.6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="1.6" stroke="#000" stroke-width="0.14"/><line x1="0" y1="0" x2="1.6" y2="0" stroke="#000" stroke-width="0.14"/></pattern>'
                 '<pattern id="dots" width="1.5" height="1.5" patternUnits="userSpaceOnUse"><circle cx="0.4" cy="0.4" r="0.11" fill="#000"/><circle cx="1.15" cy="1.1" r="0.11" fill="#000"/></pattern>'
                 '</defs>',
                 '<rect width="{}" height="{}" fill="#fff"/>'.format(W, H),
                 '<rect x="8" y="8" width="{}" height="{}" fill="none" stroke="#000" stroke-width="0.35"/>'.format(W - 16, H - 16),
                 '<g clip-path="url(#cl)">'.replace(' clip-path="url(#cl)"', "")]
        parts += self.o
        parts.append('</g>')
        parts.append('<line x1="{0}" y1="8" x2="{0}" y2="{1}" stroke="#000" stroke-width="0.35"/>'.format(tb, H - 8))
        x0, y = tb + 4, 20
        parts.append('<text x="{}" y="{}" font-size="5.4" font-weight="bold">{}</text>'.format(x0, y, self.title)); y += 5.5
        parts.append('<text x="{}" y="{}" font-size="3.1">{}</text>'.format(x0, y, self.sub)); y += 9
        if self.plain_legend:
            for n, assumed, txt in self.legend:
                lines = wrap("({}{}) {}".format(n, "*" if assumed else "", txt), 66)
                for i, l in enumerate(lines):
                    parts.append('<text x="{}" y="{:.1f}" font-size="2.8">{}</text>'.format(x0 + (0 if i == 0 else 4), y + i * 3.5, l))
                y += 3.5 * len(lines) + 1.5
            y += 1
            parts.append('<text x="{}" y="{}" font-size="2.8">* = assumed, to confirm</text>'.format(x0, y)); y += 8
        else:
          for n, assumed, txt in self.legend:
            lines = wrap(txt, 52)
            parts.append('<circle cx="{}" cy="{}" r="2.3" fill="{}" stroke="#000" stroke-width="0.3"/>'.format(x0 + 2.3, y - 1, "#fff" if assumed else "#000"))
            parts.append('<text x="{}" y="{}" font-size="2.7" text-anchor="middle" fill="{}">{}</text>'.format(x0 + 2.3, y, "#000" if assumed else "#fff", n))
            for i, l in enumerate(lines):
                parts.append('<text x="{}" y="{:.1f}" font-size="2.8">{}</text>'.format(x0 + 7, y + i * 3.5, l))
            y += 3.5 * len(lines) + 2
          if self.legend:
            y += 2
            parts.append('<circle cx="{}" cy="{}" r="2" fill="#000"/><text x="{}" y="{}" font-size="2.7">from your sketches</text>'.format(x0 + 2.3, y - 1, x0 + 7, y)); y += 5
            parts.append('<circle cx="{}" cy="{}" r="2" fill="#fff" stroke="#000" stroke-width="0.3"/><text x="{}" y="{}" font-size="2.7">assumed by me, to confirm</text>'.format(x0 + 2.3, y - 1, x0 + 7, y)); y += 8
        if self.notes:
            parts.append('<text x="{}" y="{}" font-size="3.1" font-weight="bold">Notes</text>'.format(x0, y)); y += 4.5
        for n_ in self.notes:
            for i, l in enumerate(wrap(n_, 58)):
                parts.append('<text x="{}" y="{:.1f}" font-size="2.8">{}</text>'.format(x0 + (0 if i == 0 else 2), y, l)); y += 3.5
            y += 1
        # scale bar (5 x 1 m or 5 x 100 mm)
        unit = 1000 if self.scale >= 50 else 100
        label = "m" if unit == 1000 else "dm"
        sy = H - 20
        for i in range(5):
            parts.append('<rect x="{:.2f}" y="{}" width="{:.2f}" height="1.6" fill="{}" stroke="#000" stroke-width="0.2"/>'.format(x0 + i * unit * self.s, sy, unit * self.s, "#000" if i % 2 == 0 else "#fff"))
            parts.append('<text x="{:.2f}" y="{}" font-size="2.5" text-anchor="middle">{}</text>'.format(x0 + i * unit * self.s, sy - 1, i))
        parts.append('<text x="{:.2f}" y="{}" font-size="2.5" text-anchor="middle">{}</text>'.format(x0 + 5 * unit * self.s, sy - 1, 5))
        parts.append('<text x="{:.2f}" y="{}" font-size="2.5">{}</text>'.format(x0 + 5 * unit * self.s + 3, sy + 1.4, label))
        parts.append('<text x="{}" y="{}" font-size="2.6">Scale 1:{} at A3 · dimensions in mm · draft 1, 2026-10-11</text>'.format(x0, H - 12, self.scale))
        parts.append('<text x="{}" y="{}" font-size="2.6">pyramid-roof · hand estimates, not engineered</text>'.format(x0, H - 9))
        parts.append('</svg>')
        return "\n".join(parts)

def wrap(s, n):
    words, out, cur = s.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > n: out.append(cur); cur = w
        else: cur = (cur + " " + w).strip()
    out.append(cur); return out

def zig(sh, A, B, n, sw=0.22, color="#000"):
    """zig-zag rib between two edge functions A(t), B(t), t in 0..1, n periods."""
    pts = []
    for i in range(n + 1):
        pts.append(A(i / n))
        if i < n: pts.append(B((i + 0.5) / n))
    sh.line(pts, sw, color)

def loops_g(sh, cid, origin, e_along, e_across, W, v0, v1, clip, sw=0.2):
    """insulation-style loop chain (the reference symbol) in a band of width W: straight strands cross near the edges and are
    joined by round arcs that touch the edges. Proportions measured from the reference. origin = a point on edge u = 0,
    e_across points from that edge to the other one, e_along runs along the band over v0..v1, clip = (x0, z0, x1, z1)."""
    P_, R_, UL, UR = 0.37, 0.19, 0.16, 0.843          # pitch, arc radius, crossing positions (fractions of the width)
    pitch = P_ * W
    def M(u, v):
        return (origin[0] + e_across[0] * u * W + e_along[0] * v, origin[1] + e_across[1] * u * W + e_along[1] * v)
    n = int((v1 - v0) / pitch) + 3
    vl = lambda k: v0 + (k - 0.5) * pitch
    vr = lambda k: vl(k) + pitch / 2
    clip_begin(sh, cid, *clip)
    polys = []
    for k in range(-1, n):
        polys.append([M(UL, vl(k)), M(UR, vr(k))])
        polys.append([M(UR, vr(k)), M(UL, vl(k + 1))])
        for side in (1, -1):
            c_u, e_u = (1 - R_, UR) if side == 1 else (R_, UL)
            vc = ((vr(k) + vr(k + 1)) if side == 1 else (vl(k) + vl(k + 1))) / 2
            th = math.atan2(pitch / 2, abs(e_u - c_u) * W)
            polys.append([M(c_u + side * R_ * math.cos(-th + 2 * th * i / 12), vc + R_ * W * math.sin(-th + 2 * th * i / 12)) for i in range(13)])
    sh.paths(polys, sw, layer="AIR-ZONE-SYMBOL")
    clip_end(sh)

def loops(sh, cid, xa, xb, z0, z1, sw=0.2):
    """vertical band between x = xa and x = xb, z0..z1"""
    sg = 1 if xb > xa else -1
    loops_g(sh, cid, (xa, 0.0), (0.0, 1.0), (sg, 0.0), abs(xb - xa), z0, z1, (min(xa, xb), z0, max(xa, xb), z1), sw)

R = lambda x, z: (x, z)
def rect(x0, z0, x1, z1): return [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]
LAYER_H = 10.0             # 3D-printed concrete layer height (wall and roof)
def layers(sh, ps, z0, sw=0.12, step=None, color="#000"):
    """Horizontal joints between printed layers every LAYER_H, from z0 up, clipped to the convex polygon ps."""
    zs = [p[1] for p in ps]
    segs = []
    LH = step or LAYER_H          # step: coarser indicative joints on small-scale sheets (every n-th layer)
    k = math.floor((min(zs) - z0) / LH) + 1
    while z0 + k * LH < max(zs) - 1e-6:
        z = z0 + k * LH; k += 1
        xs = []
        for a, b in zip(ps, ps[1:] + ps[:1]):
            if (a[1] - z) * (b[1] - z) < 0:
                xs.append(a[0] + (b[0] - a[0]) * (z - a[1]) / (b[1] - a[1]))
        if len(xs) >= 2:
            segs.append([(min(xs), z), (max(xs), z)])
    sh.paths(segs, sw, color=color, layer="PRINT-LAYERS")

def conc(sh, ps): sh.poly(ps, "#fff", 0.0); sh.poly(ps, "url(#conc)", 0.0)

# =====================================================================
# 1. PLAN
# =====================================================================
def plan(grid=None):
    sh = Sheet(50, 150, 148.5, "Floor plan" + ("" if grid is None else " · roof grid " + grid),
               "10 x 10 m clear · buttress every 1.5 m · printed walls",
               [(1, True, "Printed wall 400 (= roof base width). Buttresses solid black: 400 wide (same as the wall), 1000 deep from the inner face (flush with the wall inside), so they project 600 outside; one about every 1.5 m (7 bays of 1486 on the wall centreline, 8 per side, corners included)."),
                (2, True, "Openings, 1000 wide, in every other bay (the 2nd, 4th and 6th): doors in the middle bay of the south and north walls, windows elsewhere. The other bays stay printed wall. Positions and sizes are placeholders."),
                (3, False, "Pyramid roof above (dashed): 1000 square crown, hips to the corners, roof base 400 thick square to the slope, so its outer edge lands about 59 outside the wall face."),
                (4, True, "Buttress axes 1486 apart along each wall (centre to centre), corners included.")],
               ["Section A-A cuts through the 4th buttress from the south on the east and west walls (y = {:.0f}).".format(but_pos()[3]),
                "Detail D1 is the eave at the east buttress on that cut."], )
    a, b = HALF, HALF + WALL            # inner / outer face
    c = HALF + WALL / 2                 # wall centreline
    xs = but_pos()
    y0 = xs[3]                           # section A-A cuts through the 4th buttress from the south (y = {:.0f})
    # strokes first, fills second so overlapping joints disappear
    fins = []
    fin = lambda x0, y0, x1, y1: [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    for v in xs:                         # east / west fins and north / south fins
        # each buttress runs 1000 from the inner wall face, through the wall, to 600 beyond the outer face
        fins.append(fin(a, v - BUT_W / 2, b + BUT_L, v + BUT_W / 2))
        fins.append(fin(-b - BUT_L, v - BUT_W / 2, -a, v + BUT_W / 2))
        fins.append(fin(v - BUT_W / 2, a, v + BUT_W / 2, b + BUT_L))
        fins.append(fin(v - BUT_W / 2, -b - BUT_L, v + BUT_W / 2, -a))
    ring = rect(-b, -b, b, b)
    inner = rect(-a, -a, a, a)
    # corner fins of the neighbouring wall at a corner are the same rectangles twice; fine (drawn on top of each other)
    sh.poly(ring, "none", 1.0)
    px = " ".join("{:.2f},{:.2f}".format(*sh.P(*p)) for p in ring)
    d = "M" + " L".join("{:.2f},{:.2f}".format(*sh.P(*p)) for p in ring) + "Z M" + " L".join("{:.2f},{:.2f}".format(*sh.P(*p)) for p in inner) + "Z"
    sh.o.append('<path d="{0}" fill="#fff" fill-rule="evenodd"/><path d="{0}" fill="url(#conc)" fill-rule="evenodd"/>'.format(d))
    sh.poly(inner, "none", 0.5)
    # wall layers (same pattern as the roof): 160 inner leaf (two 80 layers), 160 air zone, 80 outer layer
    li_, ll_, _ = WALL_LAYERS
    z0_, z1_ = a + li_, a + li_ + ll_
    sq = lambda h: [(-h, -h), (h, -h), (h, h), (-h, h)]
    dair = "M" + " L".join("{:.2f},{:.2f}".format(*sh.P(*q)) for q in sq(z1_)) + "Z M" + " L".join("{:.2f},{:.2f}".format(*sh.P(*q)) for q in sq(z0_)) + "Z"
    sh.o.append('<path d="{}" fill="#fff" fill-rule="evenodd"/>'.format(dair))
    sh._rec("hatch", [ring, sq(z1_), sq(z0_), inner], "conc", "HATCH-PRINTED")     # wall = leaf + outer layer, air zone left open
    for h_ in (a + 80, z0_, z1_):
        sh.poly(sq(h_), "none", 0.1 if h_ == a + 80 else 0.15)
    # printed zig-zag bead as one continuous ring, so it turns the corners: vertices touch the outer layer at every corner
    BW = 80.0
    m_i, m_o = z0_ + BW / 2, z1_ - BW / 2
    n_seg = 2 * int(round(m_o / 190.0))                    # even, so both ends of a side are on the outer line
    step = 2 * m_o / n_seg
    ring = []
    for k in range(n_seg):
        r = m_o if k % 2 == 0 else m_i
        al = -m_o + k * step
        ring.append((al, -r))                               # south side, west to east
    for k in range(n_seg):
        r = m_o if k % 2 == 0 else m_i
        ring.append((r, -m_o + k * step))                   # east side, south to north
    for k in range(n_seg):
        r = m_o if k % 2 == 0 else m_i
        ring.append((m_o - k * step, r))                    # north side, east to west
    for k in range(n_seg):
        r = m_o if k % 2 == 0 else m_i
        ring.append((-r, m_o - k * step))                   # west side, north to south
    ring.append(ring[0])
    sh.mute += 1
    sh.line(ring, BW * sh.s + 0.1, "#000", extra='stroke-linecap="butt"')
    sh.line(ring, BW * sh.s, "#fff", extra='stroke-linecap="butt"')
    sh.mute -= 1
    sh._rec("bead", ring, BW, False, "PRINTED-BEAD")
    for p in fins:                                          # buttresses: solid black fill only (no rim), so it ends exactly on the wall faces
        sh.poly(p, "#000", 0.0)
    # outline of the union (outer ring edge only where not covered by fins) handled by the black pass above
    # openings: every bay between the buttresses gets a door or a window
    def pt(side, al, ac):
        return {"S": (al, -(a + ac)), "N": (al, a + ac), "E": (a + ac, al), "W": (-(a + ac), al)}[side]
    def opening(side, al, w, door):
        sh.poly([pt(side, al - w / 2, -5), pt(side, al + w / 2, -5), pt(side, al + w / 2, WALL + 5), pt(side, al - w / 2, WALL + 5)], "#fff", 0.0)
        for e in (-w / 2, w / 2):
            sh.line([pt(side, al + e, 0), pt(side, al + e, WALL)], 0.5)
        if door:
            sh.line([pt(side, al - w / 2, 0), pt(side, al - w / 2, -w)], 0.35)
            arc = [pt(side, al - w / 2 + w * math.sin(math.radians(90 * k / 24)), -w * math.cos(math.radians(90 * k / 24))) for k in range(25)]
            sh.line(arc, 0.15, dash="1.2 0.8")
        else:
            for ac in (WALL * 0.35, WALL * 0.65):
                sh.line([pt(side, al - w / 2, ac), pt(side, al + w / 2, ac)], 0.2)
    DOOR_W, WIN_W = 1000.0, 1000.0
    for side in "SNEW":                                  # openings in every other bay (the odd ones); the even bays stay printed wall
        for j in (1, 3, 5):
            opening(side, (xs[j] + xs[j + 1]) / 2, DOOR_W, side in "SN" and j == 3)
    # roof above, dashed
    top_o = HALF - RUN + T_LEAF1 + T_LAT + T_SKIN   # outer face half-width at the crown = 500 + 240
    top_o = OPEN / 2 + (T_LEAF1 + T_LAT + T_SKIN) * SH
    base_o = HALF + (T_LEAF0 + T_LAT + T_SKIN) * SH
    for half in (base_o, top_o, OPEN / 2):
        sh.line([(-half, -half), (half, -half), (half, half), (-half, half), (-half, -half)], 0.2, dash="3 1.2 0.6 1.2")
    for sx in (-1, 1):
        for sy in (-1, 1):
            sh.line([(sx * base_o, sy * base_o), (sx * top_o, sy * top_o)], 0.2, dash="3 1.2 0.6 1.2")
    sh.text(0, 0, "pyramid roof above", 2.6, italic=True); sh.text(0, -450, "crown opening 1000 x 1000", 2.4, italic=True)
    # insulation (100) and outer layer (30) outside the roof shell: outline at the roof base, very thin
    ins_o = base_o + INS * SH
    sh.line([(-ins_o, -ins_o), (ins_o, -ins_o), (ins_o, ins_o), (-ins_o, ins_o), (-ins_o, -ins_o)], INS_LW, "#000")
    cl_o = base_o + (INS + CLAD) * SH
    sh.line([(-cl_o, -cl_o), (cl_o, -cl_o), (cl_o, cl_o), (-cl_o, cl_o), (-cl_o, -cl_o)], 0.25, "#555")
    sh.legend.append((5, True, "Roof build-up outside the shell (outline at the eave): insulation 100 (very thin line), then the outer layer 30."))
    sh.callout(5, base_o + 1400, base_o + 1500, ins_o, ins_o - 200)
    if grid:                                                  # cast ribs of the roof grid, seen from above, on the four faces (dashed)
        import roof_grid as rg
        segs, _ = rg.segments(grid)
        face = {"S": lambda x, wv: (x, -wv), "N": lambda x, wv: (-x, wv), "E": lambda x, wv: (wv, x), "W": lambda x, wv: (-wv, -x)}
        def sq(wv): return [(-wv, -wv), (wv, -wv), (wv, wv), (-wv, wv), (-wv, -wv)]
        for kind, pts in segs:
            if kind in ("ring", "solid"):
                hs = [pts[0][1]] if kind == "ring" else [0.0, SOLID_H]
                for hh in hs: sh.line(sq(rg.w(hh)), 0.2, "#555", dash="2 1")
            else:
                for f in face.values():
                    sh.line([f(x, rg.w(h)) for x, h in pts], 0.2, "#555", dash="2 1")
        sh.legend.append((6, True, "Cast ribs of roof grid {} seen from above (dashed), with the bottom ring (the 300 solid base) and the horizontal / top rings.".format(grid)))
    # grid
    gx = 7500
    for lab, v in zip("ABCDEFGH", xs):
        sh.line([(v, -b - BUT_L - 600), (v, b + BUT_L + 700)], 0.12, dash="6 1 1 1")
        sh.circle_label(v, b + BUT_L + 700 + 400, lab, 2.6); sh.circle_label(v, -b - BUT_L - 600 - 400, lab, 2.6)
    for lab, v in zip("12345678", xs):
        sh.line([(-b - BUT_L - 600, v), (b + BUT_L + 700, v)], 0.12, dash="6 1 1 1")
        if v != y0:                                      # the section line A-A runs along this axis; its markers sit there
            sh.circle_label(-b - BUT_L - 1000, v, lab, 2.6); sh.circle_label(b + BUT_L + 1100, v, lab, 2.6)
    # dimensions
    sh.dim_h([-b, -a, a, b], -b - BUT_L - 350, ext=-b - 100, labels=["{:g}".format(WALL), "10000 clear", "{:g}".format(WALL)])
    sh.dim_h([-b - BUT_L, b + BUT_L], -b - BUT_L - 700 + 0, ext=-b - BUT_L, labels=["{:g} overall".format(2 * (b + BUT_L))])
    bay_l = ["{:.0f}".format(xs[1] - xs[0])] * (len(xs) - 1)
    sh.dim_v(xs, -b - BUT_L - 350, ext=-b - 100, labels=bay_l)
    sh.dim_h(xs, b + BUT_L + 350, ext=b + 100, labels=bay_l)
    sh.text(b + BUT_L / 2, y0 + BUT_W / 2 + 120, "{:g}".format(BUT_L), 2.4); sh.text(b + BUT_L / 2, y0 - BUT_W / 2 - 330, "{:g}".format(BUT_W), 2.4)
    sh.dim_h([a, a + BUT_TOTAL], y0 + BUT_W / 2 + 520, ext=y0 + BUT_W / 2 + 60, labels=["{:g} from the inner face".format(BUT_TOTAL)])
    # section line A-A and detail marker
    L = b + BUT_L + 700
    sh.line([(-L, y0), (-b - BUT_L - 350, y0)], 0.5, dash="6 1.5 1 1.5"); sh.line([(b + BUT_L + 350, y0), (L, y0)], 0.5, dash="6 1.5 1 1.5")
    for sgn in (-1, 1):
        px_, py_ = sh.P(sgn * L, y0)
        tri = [(px_, py_ - 0.2), (px_, py_ - 4.5), (px_ + sgn * 3, py_ - 2.2)]
        sh.o.append('<polygon points="{:.2f},{:.2f} {:.2f},{:.2f} {:.2f},{:.2f}" fill="#000"/>'.format(*[c for p in tri for c in p]))
        sh._rec("solid", [((q[0] - sh.ox) / sh.s, (sh.oz - q[1]) / sh.s) for q in tri], "ANNOTATION")
        sh.circle_label(sgn * (L + 500), y0, "A", 2.6, "#000", "#fff")
    # detail D1 marker around the east eave
    sh.line([(b - 450, y0 - 450), (b + 450, y0 - 450), (b + 450, y0 + 450), (b - 450, y0 + 450), (b - 450, y0 - 450)], 0.25, dash="1.5 0.8")
    sh.circle_label(b + 450, y0 - 450 - 400, "D1", 3.0)
    sh.callout(1, b + BUT_L + 1100, c + 700, b, c + 100)
    sh.callout(2, -c / 2 - 1500, -b - BUT_L - 100, -c / 2 - 500, -b)
    sh.callout(3, 2500, 2500, top_o, top_o)
    sh.callout(4, -b - BUT_L - 1400, c, -b - BUT_L, c)
    return sh

# =====================================================================
# 2. TOTAL SECTION  A-A  (looking north, cut through y = 0)
# =====================================================================
def back_face(sh, grid):
    """north roof face seen from inside: white, very faint printed layer joints, dashed piece divisions in running bond, and (grid = 'A' or 'B')
    the cast ribs behind the inner layer as dashed outlines. Uses the mid-surface geometry of roof_grid.py."""
    dz = WALL_H
    import roof_grid as rg
    wd = rg.w
    face = [(-wd(0), dz), (wd(0), dz), (wd(RISE), dz + RISE), (-wd(RISE), dz + RISE)]
    sh.poly(face, "#fff", 0.3)
    layers(sh, face, dz, 0.03, step=100, color="#c4c4c4")
    dash = dict(color="#8c8c8c", dash="3 1.6")
    nrow = 8
    for r in range(nrow):
        h0, h1_ = r * RISE / nrow, (r + 1) * RISE / nrow
        if r: sh.line([(-wd(h0), dz + h0), (wd(h0), dz + h0)], 0.1, **dash)
        n = max(1, int(round(2 * (wd(h0) + wd(h1_)) / 2 / 1500.0)))
        for i in range(1, n):
            x = -1.0 + 2.0 * (i if r % 2 == 0 else i - 0.5) / n
            if abs(x) < 1: sh.line([(x * wd(h0), dz + h0), (x * wd(h1_), dz + h1_)], 0.1, **dash)
    if grid:
        segs, _ = rg.segments(grid)
        for kind, pts in segs:
            if kind == "solid":                                           # bottom ring = the 300 solid base, across the whole face
                q = [(-wd(0), dz), (wd(0), dz), (wd(SOLID_H), dz + SOLID_H), (-wd(SOLID_H), dz + SOLID_H)]
                sh.line(q + [q[0]], 0.2, "#555", dash="2 1")
                continue
            if kind == "ring":
                y = pts[0][1]; q = rect(pts[0][0], y - rg.TOP_RING / 2, pts[1][0], y + rg.TOP_RING / 2)
            else:
                q = rg.quad(pts[0], pts[1], rg.RIB_W, kind)
            q = [(x, h + dz) for x, h in q]
            sh.line(q + [q[0]], 0.2, "#555", dash="2 1")

def back_wall(sh):
    """north wall seen from inside: printed pieces in running bond (shaded rows), openings at the bays: window, door (middle), window"""
    xs = but_pos()
    PIECE_W = 1500.0
    zt = WALL_H
    nrow_w = 5
    nw = int(round(CLEAR / PIECE_W))
    for r in range(nrow_w):
        z0, z1 = r * zt / nrow_w, (r + 1) * zt / nrow_w
        sh.poly(rect(-HALF, z0, HALF, z1), "#f3f3f3" if r % 2 else "#fafafa", 0.0)
        for i_ in range(1, nw):
            x = -HALF + CLEAR * ((i_ if r % 2 == 0 else i_ - 0.5) / nw)
            if -HALF < x < HALF:
                sh.line([(x, z0), (x, z1)], 0.13, "#a8a8a8")
        sh.line([(-HALF, z1), (HALF, z1)], 0.13, "#a8a8a8")
    for j in (1, 3, 5):
        cxm = (xs[j] + xs[j + 1]) / 2
        z0_, z1_ = (0, 2000) if j == 3 else (900, 2000)
        x0_, x1_ = cxm - 500, cxm + 500
        sh.poly(rect(x0_, z0_, x1_, z1_), "#fff", 0.3, "#444")
        sh.poly(rect(x0_ - 40, z0_, x1_ + 40, z1_ + 40), "none", 0.15, "#444")
        if j != 3:
            sh.line([((x0_ + x1_) / 2, z0_), ((x0_ + x1_) / 2, z1_)], 0.2, "#444")
            sh.poly(rect(x0_ - 40, z0_ - 60, x1_ + 40, z0_), "none", 0.2, "#444")

def section(grid=None):
    y0 = but_pos()[3]
    gname = {"A": "roof grid A, ruled-surface columns", "B": "roof grid B, diamond lattice", None: "no roof grid shown"}[grid]
    sh = Sheet(50, 157, 252, "Total section A-A" + ("" if grid is None else " · grid " + grid),
               "through the east and west buttresses, looking north",
               [(1, True, "Footing {:g} x {:g}, underside at {:g} (frost depth and bearing are guesses).".format(FOOT_W, FOOT_T, FOOT_Z)),
                (2, True, "Printed wall 400, same pattern as the roof: two 80 inner layers, a 160 air zone, an 80 outer layer."),
                (3, False, "Solid base of the roof: the first 300 (vertical) above the eave is completely solid concrete, 400 wide, no air zone; there is no ring beam."),
                (4, False, "Buttress 400 wide, 1000 from the inner face (600 beyond the wall), one about every 1.5 m (8 per side); it rises to +2.50, flush with the roof base."),
                (5, False, "Roof shell: 400 thick square to the slope at the base (two 80 inner layers, a 160 air zone, an 80 outer layer), 320 at the crown; about {:.0f} / {:.0f} horizontally.".format(400 * SH, 320 * SH)),
                (6, False, "Crown opening 1000 clear; roof rises {:g} over {:g}, slope {:.1f}° ({:.1f}° from the vertical).".format(RISE, RUN, SLOPE, 90 - SLOPE)),
                (7, True, "Everything is 3D printed in 10 mm layers; crossed hatch = solid cast concrete (roof base, ribs). Printed layer joints and the cast fill of the buttress and footing are shown in the roof-grid sheets and in detail D1."),
                (8, True, "Outside the printed shell: insulation {:g} (dotted), then the outer layer (cladding {:g}, dark).".format(INS, CLAD)),
                (9, True, "Cast ribs of the roof grid, seen on the back face as dashed outlines ({}). The cut lies in the air zone between ribs; rib sections are on the roof-grid sheets.".format(gname))],
               ["Layer pattern from your drawing; at the crown the second inner layer ends, so the leaf is 80 there (assumed).",
                "The cut runs through the 4th buttress from the south (y = {:.0f}); the north wall with its door and windows is seen beyond.".format(y0),
                "Faint grid on the back roof face and the north wall = printed pieces in running bond, about 1500 wide (assumed sizes). Dashed outlines on the back roof face = cast ribs."])
    s = sh.s
    ground = [(-6800, 0), (6800, 0)]
    sh.poly(rect(-6800, FOOT_Z - 100, 6800, 0), "url(#earth)", 0.0)
    sh.line(ground, 0.5)
    back_face(sh, grid)
    for sgn in (-1, 1):
        def X(x): return sgn * x
        # footing + stem + wall + buttress
        foot = [(X(HALF + WALL / 2 + BUT_L / 2 - FOOT_W / 2 + 0), FOOT_Z), (X(HALF + WALL / 2 + BUT_L / 2 + FOOT_W / 2), FOOT_Z),
                (X(HALF + WALL / 2 + BUT_L / 2 + FOOT_W / 2), FOOT_Z + FOOT_T), (X(HALF + WALL / 2 + BUT_L / 2 - FOOT_W / 2), FOOT_Z + FOOT_T)]
        stem = [(X(HALF), FOOT_Z + FOOT_T), (X(HALF + WALL + BUT_L), FOOT_Z + FOOT_T), (X(HALF + WALL + BUT_L), 0), (X(HALF), 0)]
        wall = [(X(HALF), 0), (X(HALF + WALL), 0), (X(HALF + WALL), WALL_H), (X(HALF), WALL_H)]
        but = [(X(HALF + WALL), 0), (X(HALF + WALL + BUT_L), 0), (X(HALF + WALL + BUT_L), WALL_H), (X(HALF + WALL), WALL_H)]
        for p in (foot, stem, wall, but):
            sh.poly(p, "#000", 0.3 if p in (foot, stem) else 0.7)     # below ground: finer line
        for p in (foot, stem, wall, but):
            sh.poly(p, "#fff", 0.0); sh.poly(p, "url(#conc)", 0.0)
        li, ll, _ = WALL_LAYERS
        zt = WALL_H
        sh.poly([(X(HALF + li), 0), (X(HALF + li + ll), 0), (X(HALF + li + ll), zt), (X(HALF + li), zt)], PINK, 0.0)
        loops(sh, "lp{}".format(sgn), X(HALF + li), X(HALF + li + ll), 0, zt, INS_LW)      # wall: loop symbol from the reference
        sh.line([(X(HALF + li), 0), (X(HALF + li), zt)], 0.25); sh.line([(X(HALF + li + ll), 0), (X(HALF + li + ll), zt)], 0.25)
        sh.line([(X(HALF), 0), (X(HALF), WALL_H)], 0.6)
        # roof bands
        def band(i, j, h0=0.0, h1=RISE):
            lo0, lo1 = rx(h0)[i], rx(h1)[i]; hi0, hi1 = rx(h0)[j], rx(h1)[j]
            return [(X(HALF + lo0), WALL_H + h0), (X(HALF + lo1), WALL_H + h1), (X(HALF + hi1), WALL_H + h1), (X(HALF + hi0), WALL_H + h0)]
        leafp, latp, skinp = band(0, 1), band(1, 2), band(2, 3)
        # note: rx = (inner, inner+leaf, +lattice, +skin) -> bands 0-1 leaf, 1-2 lattice, 2-3 skin
        sh.poly(leafp, "#000", 0.7)
        sh.poly(latp, "#000", 0.0)
        sh.poly(skinp, "#000", 0.0)
        for p in (leafp,):
            sh.poly(p, "#fff", 0.0); sh.poly(p, "url(#conc)", 0.0)
        sh.poly(latp, PINK, 0.25)
        sh.poly(skinp, "#fff", 0.0); sh.poly(skinp, "url(#conc)", 0.0); sh.poly(skinp, "none", 0.45)
        sh.poly(leafp, "none", 0.45)
        for t0, t1, kind in ((0.0, INS, "ins"), (INS, INS + CLAD, "clad")):                          # insulation and outer layer outside the printed shell
            q = [(X(HALF + rx(0)[3] + t0 * SH), WALL_H), (X(HALF + rx(RISE)[3] + t0 * SH), WALL_H + RISE), (X(HALF + rx(RISE)[3] + t1 * SH), WALL_H + RISE), (X(HALF + rx(0)[3] + t1 * SH), WALL_H)]
            if kind == "ins":
                sh.poly(q, "#fff", 0.0); sh.poly(q, "url(#dots)", 0.0); sh.poly(q, "none", INS_LW)
            else:
                sh.poly(q, "#555", 0.2)
        # solid base: the first SOLID_H of the roof is one block of concrete over the full 400 (crossed hatch = cast solid)
        solid = [(X(HALF + rx(0)[0]), WALL_H), (X(HALF + rx(SOLID_H)[0]), WALL_H + SOLID_H), (X(HALF + rx(SOLID_H)[3]), WALL_H + SOLID_H), (X(HALF + rx(0)[3]), WALL_H)]
        sh.poly(solid, "#fff", 0.0); sh.poly(solid, "url(#cast)", 0.0); sh.poly(solid, "none", 0.6)
        sh.line([(X(HALF + rx(0)[0]), WALL_H), (X(HALF + rx(0)[3]), WALL_H)], 0.25)
        sh.line([(X(HALF + rx(0)[0]), WALL_H), (X(HALF + rx(0)[3]), WALL_H)], 0.25)
    back_wall(sh)
    sh.line(ground, 0.5)       # ground line drawn last so it runs unbroken through the walls and buttresses
    # floor, openings
    sh.line([(-HALF, 0), (HALF, 0)], 0.6)
    sh.line([(-HALF + 20, -150), (HALF - 20, -150)], 0.2, dash="3 1")
    sh.text(0, -420, "floor slab on gravel (not detailed)", 2.4, italic=True)
    # dims
    xr = HALF + WALL + BUT_L
    sh.dim_v([0, WALL_H, WALL_H + RISE], xr + 300, ext=xr + 150, labels=["{:g}".format(WALL_H), "{:g}".format(RISE)])
    sh.dim_v([0, WALL_H + RISE], xr + 700, ext=xr + 150, labels=["{:g} total".format(WALL_H + RISE)])
    sh.dim_v([FOOT_Z, 0], xr + 300, ext=xr + 150, labels=["1000"])
    sh.dim_h([-HALF - WALL, -HALF, HALF, HALF + WALL], FOOT_Z - 650, ext=FOOT_Z, labels=["{:g}".format(WALL), "10000 clear", "{:g}".format(WALL)])
    sh.dim_h([-HALF - WALL - BUT_L, HALF + WALL + BUT_L], FOOT_Z - 1150, ext=FOOT_Z - 700, labels=["{:g} overall incl. buttresses".format(CLEAR + 2 * (WALL + BUT_L))])
    sh.dim_h([-OPEN / 2, OPEN / 2], WALL_H + RISE + 600, ext=WALL_H + RISE, labels=["1000"])
    sh.line([(HALF, WALL_H), (OPEN / 2, WALL_H + RISE)], 0.0)
    sh.level(-xr - 600, 0, "±0.00", -1); sh.level(-xr - 600, WALL_H, "+2.50 eave", -1); sh.level(-xr - 600, WALL_H + RISE, "+{:.2f} crown".format((WALL_H + RISE) / 1000), -1)
    sh.level(-xr - 600, FOOT_Z, "-1.00", -1)
    sh.text(HALF - RUN * 0.5 - 1000, WALL_H + RISE * 0.5, "{:.1f}°".format(SLOPE), 2.8, rot=0, italic=True)
    sh.callout(1, xr + 1200, FOOT_Z + 200, xr - 200, FOOT_Z + 200)
    sh.callout(2, xr + 1200, 1800, HALF + WALL / 2, 1200)
    sh.callout(3, xr + 1200, 3200, HALF + WALL / 2 - 80, WALL_H + SOLID_H / 2)
    sh.callout(4, xr + 1200, 900, HALF + WALL + BUT_L - 150, 700)
    sh.callout(5, 3600, 7500, HALF - K * 5200 + 200, WALL_H + 5200)
    sh.callout(6, 1800, WALL_H + RISE + 1100, 300, WALL_H + RISE)
    sh.callout(7, xr + 1200, 150, HALF + WALL + BUT_L - 40, 150)
    hx = 2600
    sh.callout(8, 4300, WALL_H + 4900, HALF + rx(hx)[3] + (INS / 2) * SH + 0.0, WALL_H + hx)
    gx_, gz_ = ((0.0, 3000.0) if grid == "A" else (-1008.0, 2000.0)) if grid else (0.0, 3000.0)
    if grid:
        sh.callout(9, -3600, WALL_H + 4600, gx_, WALL_H + gz_)
    # detail marker D1
    sh.line([(HALF + 450 - 900, WALL_H - 450), (HALF + 450 + 900, WALL_H - 450), (HALF + 450 + 900, WALL_H + 1500), (HALF + 450 - 900, WALL_H + 1500), (HALF + 450 - 900, WALL_H - 450)], 0.25, dash="1.5 0.8")
    sh.circle_label(HALF + 450 + 300, WALL_H + 1500 + 450, "D1", 3.0)
    return sh

# =====================================================================
# 3. DETAIL D1  eave, 1:10
# =====================================================================
def clip_begin(sh, cid, x0, z0, x1, z1):
    sh._rec("clip", (x0, z0, x1, z1))
    (ax, ay), (bx, by) = sh.P(x0, z0), sh.P(x1, z1)
    sh.o.append('<clipPath id="{}"><rect x="{:.2f}" y="{:.2f}" width="{:.2f}" height="{:.2f}"/></clipPath><g clip-path="url(#{})">'.format(
        cid, min(ax, bx), min(ay, by), abs(bx - ax), abs(by - ay), cid))

def clip_end(sh):
    sh._rec("clipend")
    sh.o.append('</g>')

def printed(sh, pts, w_mm, f, fill="url(#conc)"):
    """a printed bead drawn as a wide stroke: black rim, white body, hatch. w_mm = bead width in mm, f = model-to-paper factor."""
    w = w_mm * sh.s * f
    ext = 'stroke-linecap="butt"'
    sh.mute += 1
    sh.line(pts, w + 0.5, "#000", extra=ext); sh.line(pts, w, "#fff", extra=ext); sh.line(pts, w - 0.04, fill, extra=ext)
    sh.mute -= 1
    sh._rec("bead", list(pts), w_mm * f, fill == "url(#conc)", "PRINTED-BEAD")

def piece_plan(sh, X0, Z0):
    """Plan of one roof piece, 1:5 (model mm = local mm * F in sh coordinates). inside on the right."""
    F = 2.0
    M = lambda u, v: (X0 + F * u, Z0 + F * v)
    P, v0, HL, SAG, U_SKIN, U_L2, U_L1 = 600.0, 300.0, 105.0, 68.0, 80.0, 280.0, 320.0
    R_ = (HL ** 2 + SAG ** 2) / (2 * SAG)
    def prof(dv): return max(0.0, math.sqrt(R_ ** 2 - dv ** 2) - (R_ - SAG)) if abs(dv) < HL else 0.0
    vs = [i * 10.0 for i in range(61)]
    clip_begin(sh, "pp", X0, Z0, X0 + F * 400, Z0 + F * P)
    sh.poly([M(0, 0), M(400, 0), M(400, P), M(0, P)], "#fff", 0.0)
    sh.poly([M(80, 0), M(240, 0), M(240, P), M(80, P)], "#fff", 0.0)          # open air pockets between the bead and the layers
    # outer skin
    sh.poly([M(0, 0), M(80, 0), M(80, P), M(0, P)], "#000", 0.0)
    sh.poly([M(0, -50), M(80, -50), M(80, P + 50), M(0, P + 50)], "#fff", 0.5, "#000")
    sh.poly([M(0, -50), M(80, -50), M(80, P + 50), M(0, P + 50)], "url(#conc)", 0.0)
    # pocket lens (rebar void) between layer 2 and layer 1
    lens = [M(U_L2 + 40 - prof(v - v0), v) for v in vs] + [M(U_L1, v) for v in reversed(vs)]
    sh.poly(lens, "#e4e4e4", 0.0)
    # layer 2 (80, serpentine) and zig-zag bead (80)
    printed(sh, [M(U_L2 - prof(v - v0), v) for v in vs], 80, F)
    bead = [M(120, -60)] + [M(120, 0)]
    pts = [(120.0, 0.0), (v0 - HL - 0.0, 200.0)]
    bead = [M(120, -150), M(200, v0 - P - HL)] + [M(120, 0), M(200, v0 - HL)] + [M(200 - prof(v - v0), v) for v in vs if abs(v - v0) <= HL] + [M(200, v0 + HL), M(120, P), M(200, v0 + P - HL)]
    printed(sh, bead, 80, F)
    # inner layer 1
    sh.poly([M(U_L1, -50), M(400, -50), M(400, P + 50), M(U_L1, P + 50)], "#fff", 0.5, "#000")
    sh.poly([M(U_L1, -50), M(400, -50), M(400, P + 50), M(U_L1, P + 50)], "url(#conc)", 0.0)
    clip_end(sh)
    # rebar: Ø55 hole with Ø12 bar
    cu, cv = U_L1 - SAG / 2 - 3, v0
    px, py = sh.P(*M(cu, cv))
    sh._rec("circle", X0 + F * cu, Z0 + F * cv, 27.5 * F, False, "REBAR-POCKET")
    sh._rec("circle", X0 + F * cu, Z0 + F * cv, 6 * F, True, "REBAR")
    sh.o.append('<circle cx="{:.2f}" cy="{:.2f}" r="{:.2f}" fill="#fff" stroke="#000" stroke-width="0.3"/>'.format(px, py, 27.5 * sh.s * F))
    sh.o.append('<circle cx="{:.2f}" cy="{:.2f}" r="{:.2f}" fill="{}"/>'.format(px, py, 6 * sh.s * F, BLUE))
    # frame ends (break)
    for v in (0, P):
        sh.line([M(-40, v), M(440, v)], 0.25, "#000", dash="3 1 0.6 1")
    # dimensions (horizontal, paper-true: 1:5)
    z_d = Z0 - 100
    xs = [X0 + F * u for u in (0, 80, 240, 320, 400)]
    sh.dim_h(xs, z_d, ext=Z0 - 30, labels=["80", "160", "80", "80"])
    # numbered callouts on the right, same numbers as the legend
    CX = X0 + F * 400 + 170
    def num(n, u, v, cz):
        x, z = M(u, v)
        sh.callout(n, CX, cz, x, z)
    num(1, 40, 120, Z0 + F * 120)
    num(2, 170, 480, Z0 + F * 480 + 150)
    num(3, 235, 190, Z0 + F * 250)
    num(4, 360, 80, Z0 + F * 60)
    num(5, 318, 300, Z0 + F * 345)
    sh.text(X0 + F * 400, Z0 + F * P + 60, "inside", 2.6, "end", weight="bold"); sh.text(X0, Z0 + F * P + 60, "outside", 2.6, "start", weight="bold")
    sh.text(X0, Z0 + F * P + 200, "Plan of one roof piece, 1:5", 3.4, "start", weight="bold")
    sh.text(X0, Z0 + F * P + 130, "layer pattern, bars every @ 600 along the path", 2.4, "start")

def piece_plan_b(sh, X0, Z0):
    """Variant B of the roof piece plan, 1:5: layer 2 straight, the bar pocket sits in a bulge of the inner layer 1."""
    F = 2.0
    M = lambda u, v: (X0 + F * u, Z0 + F * v)
    P, v0 = 600.0, 300.0
    def arc(HL, SAG):
        R_ = (HL ** 2 + SAG ** 2) / (2 * SAG)
        return lambda dv: max(0.0, math.sqrt(R_ ** 2 - dv ** 2) - (R_ - SAG)) if abs(dv) < HL else 0.0
    bulge, lens = arc(130.0, 70.0), arc(80.0, 65.0)
    vs = [i * 10.0 for i in range(61)]
    clip_begin(sh, "pq", X0, Z0, X0 + F * 480, Z0 + F * P)
    sh.poly([M(0, 0), M(480, 0), M(480, P), M(0, P)], "#fff", 0.0)
    # outer skin
    sh.poly([M(0, -50), M(80, -50), M(80, P + 50), M(0, P + 50)], "#fff", 0.5, "#000")
    sh.poly([M(0, -50), M(80, -50), M(80, P + 50), M(0, P + 50)], "url(#conc)", 0.0)
    # layer 2: straight
    sh.poly([M(240, -50), M(320, -50), M(320, P + 50), M(240, P + 50)], "#fff", 0.5, "#000")
    sh.poly([M(240, -50), M(320, -50), M(320, P + 50), M(240, P + 50)], "url(#conc)", 0.0)
    # zig-zag bead: touches the outer layer at v = 0, 300, 600 and layer 2 at v = 150, 450
    printed(sh, [M(200, -150), M(120, 0), M(200, 150), M(120, 300), M(200, 450), M(120, 600), M(200, 750)], 80, F)
    # inner layer 1 with the bulge on the room side and the pocket notch on the layer-2 side
    l1 = [M(320, -50), M(400, -50)] + [M(400 + bulge(v - v0), v) for v in vs] + [M(400, P + 50), M(320, P + 50)] + [M(320 + lens(v - v0), v) for v in reversed(vs)]
    sh.poly(l1, "#fff", 0.5, "#000")
    sh.poly(l1, "url(#conc)", 0.0)
    clip_end(sh)
    # rebar: Ø55 hole with Ø12 bar
    cu, cv = 357.5, v0
    px, py = sh.P(*M(cu, cv))
    sh._rec("circle", X0 + F * cu, Z0 + F * cv, 27.5 * F, False, "REBAR-POCKET")
    sh._rec("circle", X0 + F * cu, Z0 + F * cv, 6 * F, True, "REBAR")
    sh.o.append('<circle cx="{:.2f}" cy="{:.2f}" r="{:.2f}" fill="#fff" stroke="#000" stroke-width="0.3"/>'.format(px, py, 27.5 * sh.s * F))
    sh.o.append('<circle cx="{:.2f}" cy="{:.2f}" r="{:.2f}" fill="{}"/>'.format(px, py, 6 * sh.s * F, BLUE))
    for v in (0, P):
        sh.line([(M(-40, v)), M(500, v)], 0.25, "#000", dash="3 1 0.6 1")

def detail():
    ZB, ZT = 1500.0, 3400.0
    sh = Sheet(10, 100, 420, "Detail D1: eave, roof to wall",
               "",
               [(1, False, "Roof outer layer 80, printed with the rest of the piece; outside it the insulation 100 (dotted) and the outer layer 30 (dark)."),
                (2, False, "Zig-zag lattice 80 in a 160 zone; it touches the outer layer and layer 2 every @ 600; the cells between are open air pockets for ventilation."),
                (3, False, "Layer 2, 80: printed bead; beside each rib it turns into the printed channel walls (see the plan cut)."),
                (4, False, "Inner layer 1, 80, room side. Layers 1 and 2 together are the structural leaf: 160 at the base, 80 at the crown (layer 2 ends)."),
                (5, True, "Rib (cast column): channel 160 wide x 240 deep through layer 2 and the 160 zone, filled with poured concrete; section cut along the rib. It continues into the solid base without a joint."),
                (6, True, "Rib bars R, 4 Ø16 (2 in the cut), anchored in the solid base where they cross the hooks of the wall bars A (assumed; steel fibre in the concrete could replace them)."),
                (7, True, "Stirrups Ø8 every 200 (assumed)."),
                (8, False, "Solid base of the roof: over the first 300 (vertical) above the eave the 160 zone between the printed layers is filled with cast concrete instead of the open lattice; wall bars A hook into it. Replaces the ring beam."),
                (9, False, "Buttress 400 wide, 1000 from the inner face (600 beyond the wall): printed formwork (80 end cap shown) filled with cast concrete; top flush with the roof base at +2.50."),
                (10, True, "Wall 400 printed, same pattern as the roof; wall bars A Ø16 run from the footing up into the solid base and end in a 160 hook (assumed). The roof grid is A or B (see the roof-grid sheets); the detail is cut along a rib.")],
               [])
    sh.plain_legend = True
    ZH = WALL_H
    # --- wall + buttress
    wall = rect(0, ZB, WALL, WALL_H)
    but = [(WALL, ZB), (WALL + BUT_L, ZB), (WALL + BUT_L, WALL_H), (WALL, WALL_H)]
    cap = [(WALL + BUT_L - 80, ZB), (WALL + BUT_L, ZB), (WALL + BUT_L, WALL_H), (WALL + BUT_L - 80, WALL_H)]      # printed end cap of the buttress
    for p in (wall, but):
        sh.poly(p, "#000", 0.7)
    for p in (wall, but):
        sh.poly(p, "#fff", 0.0)
        if p is not wall:
            sh.poly(p, "url(#cast)", 0.0)                                      # buttress: cast core inside printed formwork
    sh.poly(cap, "#fff", 0.0); sh.poly(cap, "url(#conc)", 0.0); layers(sh, cap, ZB); sh.poly(cap, "none", 0.45)
    layers(sh, wall, ZB)                                                      # wall: printed layers, 10 each
    li, ll, ls_ = WALL_LAYERS
    sh.poly(rect(li, ZB, li + ll, WALL_H), PINK, 0.0)
    sh.line([(li, ZB), (li, WALL_H)], 0.3); sh.line([(li + ll, ZB), (li + ll, WALL_H)], 0.3)
    sh.line([(80, ZB), (80, WALL_H)], 0.2)   # joint between the two inner layers
    sh.poly(wall, "none", 0.45); sh.poly(but, "none", 0.45)
    # --- roof bands over z in [ZH, ZT]
    h1 = ZT - ZH
    # the roof is cut square to the slope at the top of the detail (dash-dot line)
    d = (rx(h1)[3] - rx(0)[3], h1); L = math.hypot(*d)
    t_ = (d[0] / L, d[1] / L); nrm = (d[1] / L, -d[0] / L)
    c = (rx(h1)[1], ZT)
    def tip(i, a=0.0):
        x0, x1 = rx(0)[i] + a, rx(h1)[i] + a
        l = ((c[0] - x0) * t_[0] + (c[1] - ZH) * t_[1]) / ((x1 - x0) * t_[0] + h1 * t_[1])
        return (x0 + l * (x1 - x0), ZH + l * h1)
    layer1 = [(rx(0)[0], ZH), tip(0), tip(0, 80 * SH), (rx(0)[0] + 80 * SH, ZH)]
    layer2 = [(rx(0)[0] + 80 * SH, ZH), tip(0, 80 * SH), tip(1), (rx(0)[1], ZH)]
    latp = [(rx(0)[1], ZH), tip(1), tip(2), (rx(0)[2], ZH)]
    skinp = [(rx(0)[2], ZH), tip(2), tip(3), (rx(0)[3], ZH)]
    for p in (layer1, layer2, skinp):
        sh.poly(p, "#fff", 0.0); layers(sh, p, ZH)                            # roof: printed layers, 10 each
    sh.poly(latp, PINK, 0.0)
    for p in (layer1, layer2, latp, skinp):
        sh.poly(p, "none", 0.45)
    # solid base: the first SOLID_H of the roof is one block of concrete over the full thickness, covering the layers drawn above
    solid = [(rx(0)[1], ZH), (rx(SOLID_H)[1], ZH + SOLID_H), (rx(SOLID_H)[2], ZH + SOLID_H), (rx(0)[2], ZH)]
    sh.poly(solid, "#fff", 0.0); sh.poly(solid, "url(#cast)", 0.0)      # air zone filled with cast concrete; layers 1, 2 and the outer layer stay printed
    # rib: above the solid base the channel replaces layer 2 and the 160 zone, filled with poured concrete (no joint with the base)
    off1 = 80 * SH
    core = [(rx(SOLID_H)[0] + off1, ZH + SOLID_H), tip(0, off1), tip(2), (rx(SOLID_H)[2], ZH + SOLID_H)]
    sh.poly(core, "#fff", 0.0); sh.poly(core, "url(#cast)", 0.0)
    sh.line([(rx(SOLID_H)[0] + off1, ZH + SOLID_H), tip(0, off1), tip(2), (rx(SOLID_H)[2], ZH + SOLID_H)], 0.55)
    sh.line([(rx(0)[1], ZH), (rx(SOLID_H)[1], ZH + SOLID_H)], 0.55); sh.line([(rx(0)[2], ZH), (rx(SOLID_H)[2], ZH + SOLID_H)], 0.55)
    loops(sh, "lpd", li, li + ll, ZB, WALL_H, INS_LW)      # wall: loop symbol from the reference
    # insulation (dotted) and outer layer (dark) outside the printed shell, up to the cut line
    for a0, a1, kind in ((0.0, INS * SH, "ins"), (INS * SH, (INS + CLAD) * SH, "clad")):
        q = [(rx(0)[3] + a0, ZH), tip(3, a0), tip(3, a1), (rx(0)[3] + a1, ZH)]
        if kind == "ins":
            sh.poly(q, "#fff", 0.0); sh.poly(q, "url(#dots)", 0.0); sh.poly(q, "none", INS_LW)
        else:
            sh.poly(q, "#555", 0.3)
    # the roof continues: dash-dot line at the top of the detail, square to the slope
    sh.line([(c[0] - nrm[0] * 380, c[1] - nrm[1] * 380), (c[0] + nrm[0] * 560, c[1] + nrm[1] * 560)], 0.5, "#000", dash="7 1.5 1.2 1.5")
    # ---- rebar: every bar is drawn at its true diameter (1:10, so Ø16 = 1.6 mm on the sheet); black = steel
    e1 = lambda h: rx(h)[0] + 80 * SH                                   # inner edge of the rib core (joint of layers 1 and 2)
    bar = lambda pts, d: sh.line(pts, d / sh.scale, BLUE, tw=d)
    sh.layer = "REBAR-POCKET"
    for sgn in (-1, 1):
        sh.line([(80 + sgn * 27.5, ZB), (80 + sgn * 27.5, WALL_H)], 0.15, "#555", dash="2 0.8")       # wall pocket Ø55
    sh.layer = "REBAR"
    # A  wall bar Ø16: footing up into the solid base, 90 deg hook (10d) in the base core
    A_X, HOOK_Z = 95.0, WALL_H + SOLID_H - 110
    bar([(A_X, ZB), (A_X, HOOK_Z), (A_X + 160, HOOK_Z)], 16)
    # R  rib bars Ø16: two of the four are in the cut, 60 and 180 from the inner edge of the 240 deep core; anchored in the solid base
    for dd in (60, 180):
        bar([(e1(40) + dd * SH, ZH + 40), (e1(h1) + dd * SH, ZH + h1)], 16)
    # stirrups Ø8 every 200 above the base
    for h in range(500, int(h1), 200):
        bar([(e1(h) + 30 * SH, ZH + h), (rx(h)[2] - 30 * SH, ZH + h)], 8)
    sh.layer = None
    # ---- dimensions
    sh.dim_v([WALL_H, WALL_H + SOLID_H], -300, ext=-30, labels=["{:g}".format(SOLID_H)])
    sh.dim_h([0, li, li + ll, WALL], ZB - 130, ext=ZB, labels=["{:g}".format(li), "{:g}".format(ll), "{:g}".format(WALL - li - ll)])
    sh.dim_h([WALL, WALL + BUT_L], ZB - 130, ext=ZB, labels=["{:g}".format(BUT_L)])
    sh.dim_h([0, BUT_TOTAL], ZB - 330, ext=ZB - 130, labels=["{:g} from the inner face".format(BUT_TOTAL)])
    # dimension chain along the dash-dot cut, square to the slope: true thickness of each zone
    pts = [tip(0), tip(1), tip(2), tip(3)]
    off = 420.0
    ang = -math.degrees(math.atan2(t_[1], t_[0]))
    ang = ang if abs(ang) <= 90 else ang + 180
    dl = [(p_[0] + t_[0] * off, p_[1] + t_[1] * off) for p_ in pts]
    sh.line([dl[0], dl[-1]], 0.2)
    tk = 1.2 / sh.s / 2
    for p_, q_ in zip(pts, dl):
        sh.line([(p_[0] + t_[0] * 60, p_[1] + t_[1] * 60), (q_[0] + t_[0] * 40, q_[1] + t_[1] * 40)], 0.12)
        sh.line([(q_[0] - (t_[0] + nrm[0]) * tk, q_[1] - (t_[1] + nrm[1]) * tk), (q_[0] + (t_[0] + nrm[0]) * tk, q_[1] + (t_[1] + nrm[1]) * tk)], 0.45)
    for k in range(3):
        mx, mz = (dl[k][0] + dl[k + 1][0]) / 2 + t_[0] * 60, (dl[k][1] + dl[k + 1][1]) / 2 + t_[1] * 60
        sh.text(mx, mz, "{:g}".format(round(math.hypot(pts[k + 1][0] - pts[k][0], pts[k + 1][1] - pts[k][1]))), 2.5, rot=ang)
    sh.text(-860, WALL_H + 30, "+2.50 eave", 2.6, "start", weight="bold")
    sh.line([(-860, WALL_H), (-100, WALL_H)], 0.2, dash="4 1")
    # ---- callouts
    sh.callout(1, 880, ZH + 760, rx(500)[3] - 10, ZH + 500)
    sh.callout(2, 880, ZH + 380, (rx(250)[1] + rx(250)[2]) / 2, ZH + 250)
    sh.callout(3, -620, ZH + 360, (e1(150) + rx(150)[1]) / 2, ZH + 150)
    sh.callout(4, -620, ZH + 560, rx(560)[0] + 40, ZH + 560)
    sh.callout(5, -620, ZH + 760, e1(760) + 150 * SH, ZH + 760)
    sh.callout(6, -470, WALL_H - 140, e1(150) + 60 * SH, ZH + 150)
    sh.callout(7, -620, ZH + 160, e1(500) + 120 * SH, ZH + 500)
    sh.callout(8, 760, ZH + 150, 220, ZH + 150)
    sh.callout(9, -620, ZB + 100, WALL + 250, ZB + 250)
    sh.callout(10, -620, ZB + 400, li + ll / 2, ZB + 600)
    import roof_grid as rg
    rg.section_inset(sh, 1100, 2700, F=2.0, callouts=False, W_=400.0)           # plan cut through a rib at one layer, 1:5
    return sh

def export(sh, path):
    svg = sh.svg()
    open(path + ".svg", "w").write(svg)
    try:
        import cairosvg
        cairosvg.svg2pdf(bytestring=svg.encode(), write_to=path + ".pdf")
        cairosvg.svg2png(bytestring=svg.encode(), write_to=path + ".png", output_width=4200)
    except Exception as e:
        print("  (pdf/png skipped:", type(e).__name__, ")")
    print("wrote", path + ".svg")

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
    export(plan(), os.path.join(out, "pyramid-plan"))
    export(plan("A"), os.path.join(out, "pyramid-plan-gridA"))
    export(plan("B"), os.path.join(out, "pyramid-plan-gridB"))
    export(section(), os.path.join(out, "pyramid-section"))
    export(section("A"), os.path.join(out, "pyramid-section-gridA"))
    export(section("B"), os.path.join(out, "pyramid-section-gridB"))
    export(detail(), os.path.join(out, "pyramid-detail"))
    print("slope {:.1f} deg, run {:g}, rise {:g}".format(SLOPE, RUN, RISE))
