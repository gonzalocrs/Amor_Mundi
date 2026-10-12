"""Plan, total section and eave detail for the 10 x 10 m buttressed pyramid roof (3D concrete printed).
Standalone: no dependency on scripts/cork_house_roof.py. Model units mm. Every number you may want to change is in PARAMETERS.

Run:  python details/pyramid_drawings.py [out_dir]
      -> pyramid-plan.svg, pyramid-section.svg, pyramid-detail.svg (+ .pdf/.png if `pip install cairosvg` works)"""
import math, os, sys

# ================= PARAMETERS =================
CLEAR = 10000.0            # clear inside dimension, square plan
WALL = 400.0               # wall thickness = ring beam width = roof base width
BEAM_H = 500.0             # ring beam depth
WALL_H = 2500.0            # ground to top of ring beam (= eave, roof base)
BUT_TOTAL, BUT_W = 700.0, 400.0   # buttress: 700 long measured from the inner wall face (flush with wall and beam), 400 wide (= the wall thickness, constant along its length)
BUT_L = BUT_TOTAL - WALL          # so it projects only this far beyond the outer wall face
OPEN = 1000.0              # square opening at the crown (inner face)
RISE = 8000.0              # roof height
T_LEAF0, T_LEAF1 = 160.0, 80.0   # inner structural leaf, horizontal width at base / crown
T_LAT, T_SKIN = 160.0, 80.0      # lattice zone and outer skin (constant)
CLAD = 30.0                # outer cladding on the roof (assumed)
WALL_LAYERS = (160.0, 160.0, 80.0)   # wall inner leaf (two 80 layers) / air zone / outer layer: same pattern as the roof
FOOT_W, FOOT_T, FOOT_Z = 1800.0, 250.0, -1000.0   # footing width, thickness, underside level (assumed)
HALF = CLEAR / 2
RUN = HALF - OPEN / 2
K = RUN / RISE             # inward lean of the roof (horizontal per vertical)
SLOPE = math.degrees(math.atan2(RISE, RUN))
assert abs(sum(WALL_LAYERS) - WALL) < 1e-6

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
    def P(self, x, z): return (self.ox + x * self.s, self.oz - z * self.s)
    def pts(self, ps): return " ".join("{:.2f},{:.2f}".format(*self.P(*p)) for p in ps)
    def poly(self, ps, fill="none", sw=0.25, stroke="#000", extra="", join="round"):
        if fill == PINK:
            fill = "#fff"                  # lattice cells are open air pockets (ventilation)
        self.o.append('<polygon points="{}" fill="{}" stroke="{}" stroke-width="{}" stroke-linejoin="{}" {}/>'.format(self.pts(ps), fill, stroke, sw, join, extra))
    def line(self, ps, sw=0.25, color="#000", dash=None, extra=""):
        self.o.append('<polyline points="{}" fill="none" stroke="{}" stroke-width="{}" stroke-linejoin="round"{} {}/>'.format(
            self.pts(ps), color, sw, ' stroke-dasharray="{}"'.format(dash) if dash else "", extra))
    def paths(self, polys, sw=0.25, color="#000"):
        d = " ".join("M" + " L".join("{:.1f},{:.1f}".format(*self.P(*q)) for q in pl) for pl in polys)
        self.o.append('<path d="{}" fill="none" stroke="{}" stroke-width="{}" stroke-linejoin="round"/>'.format(d, color, sw))
    def dot(self, x, z, r_mm, color=BLUE):
        px, py = self.P(x, z)
        self.o.append('<circle cx="{:.2f}" cy="{:.2f}" r="{:.2f}" fill="{}"/>'.format(px, py, max(r_mm * self.s, 0.35), color))
    def text(self, x, z, s, size=2.6, anchor="middle", weight="normal", rot=0, color="#000", italic=False):
        px, py = self.P(x, z)
        tr = ' transform="rotate({} {:.2f} {:.2f})"'.format(rot, px, py) if rot else ""
        self.o.append('<text x="{:.2f}" y="{:.2f}" font-size="{}" text-anchor="{}" font-weight="{}" fill="{}"{}{}>{}</text>'.format(
            px, py, size, anchor, weight, color, ' font-style="italic"' if italic else "", tr, s))
    def circle_label(self, x, z, label, r=2.6, fill="#fff", tc="#000"):
        px, py = self.P(x, z)
        self.o.append('<circle cx="{:.2f}" cy="{:.2f}" r="{}" fill="{}" stroke="#000" stroke-width="0.3"/>'.format(px, py, r, fill))
        self.o.append('<text x="{:.2f}" y="{:.2f}" font-size="{}" text-anchor="middle" fill="{}">{}</text>'.format(px, py + r * 0.36, r * 1.15, tc, label))
    def callout(self, n, x, z, tx, tz):
        self.line([(x, z), (tx, tz)], 0.2)
        self.dot(tx, tz, 0, "#000")
        self.circle_label(x, z, n, 2.4)
    def dim_h(self, xs, z, text_off=1.0, ext=None, labels=None, size=2.5):
        """horizontal dimension chain at height z; ext = z the extension lines start from."""
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
    def dim_v(self, zs, x, ext=None, labels=None, size=2.5):
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
    def level(self, x, z, label, side=1):
        s = self.s
        self.line([(x, z), (x + side * 6 / s, z)], 0.2)
        self.poly([(x, z), (x + 1.2 / s, z + 1.6 / s), (x - 1.2 / s, z + 1.6 / s)], "#000", 0.1)
        self.text(x + side * 7 / s, z - 0.5 / s, label, 2.5, "start" if side > 0 else "end")
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
    sh.paths(polys, sw)
    clip_end(sh)

def loops(sh, cid, xa, xb, z0, z1, sw=0.2):
    """vertical band between x = xa and x = xb, z0..z1"""
    sg = 1 if xb > xa else -1
    loops_g(sh, cid, (xa, 0.0), (0.0, 1.0), (sg, 0.0), abs(xb - xa), z0, z1, (min(xa, xb), z0, max(xa, xb), z1), sw)

R = lambda x, z: (x, z)
def rect(x0, z0, x1, z1): return [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]
def conc(sh, ps): sh.poly(ps, "#fff", 0.0); sh.poly(ps, "url(#conc)", 0.0)

# =====================================================================
# 1. PLAN
# =====================================================================
def plan():
    sh = Sheet(50, 150, 148.5, "Floor plan",
               "10 x 10 m clear · 8 buttresses · printed walls",
               [(1, True, "Printed wall 400 (= ring beam width = roof base width). Buttresses solid black: 400 wide (same as the wall), 700 deep from the inner face (flush with the wall inside), so they project 300 outside."),
                (2, True, "Openings, one per bay between the buttresses: doors 1000 (south-west and north-east bays), windows 1800 in the other six. Positions and sizes are placeholders."),
                (3, False, "Pyramid roof above (dashed): 1000 square crown, hips to the corners, roof base 400 thick square to the slope, so its outer edge lands about 59 outside the wall face."),
                (4, True, "Buttresses at the 4 corners and the 4 mid-spans, axes 5200 apart (centre to centre of wall).")],
               ["Section A-A cuts through the east and west mid-span buttresses.",
                "Detail D1 is the eave at the east mid-span buttress."], )
    a, b = HALF, HALF + WALL            # inner / outer face
    c = HALF + WALL / 2                 # wall centreline
    xs = [-c, 0, c]
    # strokes first, fills second so overlapping joints disappear
    fins = []
    fin = lambda x0, y0, x1, y1: [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    for v in xs:                         # east / west fins and north / south fins
        # each buttress runs 700 from the inner wall face, through the wall, to 300 beyond the outer face
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
    sh.line(ring, BW * sh.s + 0.1, "#000", extra='stroke-linecap="butt"')
    sh.line(ring, BW * sh.s, "#fff", extra='stroke-linecap="butt"')
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
    bays = [("S", -c / 2, True), ("S", c / 2, False), ("N", -c / 2, False), ("N", c / 2, True),
            ("E", -c / 2, False), ("E", c / 2, False), ("W", -c / 2, False), ("W", c / 2, False)]
    DOOR_W, WIN_W = 1000.0, 1800.0
    for side, al, door in bays:
        opening(side, al, DOOR_W if door else WIN_W, door)
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
    # grid
    gx = 7500
    for lab, v in zip("ABC", xs):
        sh.line([(v, -b - BUT_L - 600), (v, b + BUT_L + 700)], 0.12, dash="6 1 1 1")
        sh.circle_label(v, b + BUT_L + 700 + 400, lab, 2.6); sh.circle_label(v, -b - BUT_L - 600 - 400, lab, 2.6)
    for lab, v in zip("123", xs):
        sh.line([(-b - BUT_L - 600, v), (b + BUT_L + 700, v)], 0.12, dash="6 1 1 1")
        if v != 0:
            sh.circle_label(-b - BUT_L - 1000, v, lab, 2.6); sh.circle_label(b + BUT_L + 1100, v, lab, 2.6)
    # dimensions
    sh.dim_h([-b, -a, a, b], -b - BUT_L - 350, ext=-b - 100, labels=["{:g}".format(WALL), "10000 clear", "{:g}".format(WALL)])
    sh.dim_h([-b - BUT_L, b + BUT_L], -b - BUT_L - 700 + 0, ext=-b - BUT_L, labels=["{:g} overall".format(2 * (b + BUT_L))])
    sh.dim_v([-c, 0, c], -b - BUT_L - 350, ext=-b - 100, labels=["{:g}".format(c), "{:g}".format(c)])
    sh.dim_h([-c, 0, c], b + BUT_L + 350, ext=b + 100, labels=["{:g}".format(c), "{:g}".format(c)])
    sh.text(b + BUT_L / 2, BUT_W / 2 + 120, "{:g}".format(BUT_L), 2.4); sh.text(b + BUT_L / 2, -BUT_W / 2 - 330, "{:g}".format(BUT_W), 2.4)
    sh.dim_h([a, a + BUT_TOTAL], BUT_W / 2 + 520, ext=BUT_W / 2 + 60, labels=["{:g} from the inner face".format(BUT_TOTAL)])
    # section line A-A and detail marker
    L = b + BUT_L + 700
    sh.line([(-L, 0), (-b - BUT_L - 350, 0)], 0.5, dash="6 1.5 1 1.5"); sh.line([(b + BUT_L + 350, 0), (L, 0)], 0.5, dash="6 1.5 1 1.5")
    for sgn in (-1, 1):
        px_, py_ = sh.P(sgn * L, 0)
        sh.o.append('<polygon points="{:.2f},{:.2f} {:.2f},{:.2f} {:.2f},{:.2f}" fill="#000"/>'.format(px_, py_ - 0.2, px_ - sgn * -0 + 0, py_ - 4.5, px_ + sgn * 3, py_ - 2.2).replace("", ""))
        sh.circle_label(sgn * (L + 500), 0, "A", 2.6, "#000", "#fff")
    # detail D1 marker around the east eave
    sh.line([(b - 450, -450), (b + 450, -450), (b + 450, 450), (b - 450, 450), (b - 450, -450)], 0.25, dash="1.5 0.8")
    sh.circle_label(b + 450, 450 + 400, "D1", 3.0)
    sh.callout(1, b + BUT_L + 1100, c + 700, b, c + 100)
    sh.callout(2, -c / 2 - 1500, -b - BUT_L - 100, -c / 2 - 500, -b)
    sh.callout(3, 2500, 2500, top_o, top_o)
    sh.callout(4, -b - BUT_L - 1400, c, -b - BUT_L, c)
    return sh

# =====================================================================
# 2. TOTAL SECTION  A-A  (looking north, cut through y = 0)
# =====================================================================
def section():
    sh = Sheet(50, 157, 252, "Total section A-A",
               "through the east and west mid-span buttresses, looking north",
               [(1, True, "Footing {:g} x {:g}, underside at {:g} (frost depth and bearing are guesses).".format(FOOT_W, FOOT_T, FOOT_Z)),
                (2, True, "Printed wall 400, same pattern as the roof: two 80 inner layers, a 160 air zone, an 80 outer layer."),
                (3, False, "Ring beam 400 wide x 500 deep, embedded in the buttress notch; top at +2.50, flush with the buttress top."),
                (4, False, "Buttress 400 wide, 700 from the inner face (300 beyond the wall), L-shaped around the ring beam: it rises to +2.50, flush with the roof base."),
                (5, False, "Roof shell: 400 thick square to the slope at the base (two 80 inner layers, a 160 air zone, an 80 outer layer), 320 at the crown; about 459 / 367 horizontally."),
                (6, False, "Crown opening 1000 clear; roof rises 8000 over {:g}, slope {:.1f}°.".format(RUN, SLOPE))],
               ["Layer pattern from your drawing; at the crown the second inner layer ends, so the leaf is 80 there (assumed).",
                "The cut runs through the mid-span buttresses; the north wall with its door and window is seen beyond.", "Faint grid on the back roof face and the north wall = printed pieces in running bond, about 1500 wide, 800 high on the roof and 440 on the wall (assumed sizes)."])
    s = sh.s
    ground = [(-6800, 0), (6800, 0)]
    sh.poly(rect(-6800, FOOT_Z - 100, 6800, 0), "url(#earth)", 0.0)
    sh.line(ground, 0.5)
    # back (north) roof face seen from inside: printed pieces in running bond, very faint
    PIECE_H, PIECE_W = 800.0, 1500.0
    half_w = lambda h: HALF - K * h
    nrow = int(round(RISE / PIECE_H))
    for r in range(nrow):
        h0, h1_ = r * RISE / nrow, (r + 1) * RISE / nrow
        w0, w1 = half_w(h0), half_w(h1_)
        sh.poly([(-w0, WALL_H + h0), (w0, WALL_H + h0), (w1, WALL_H + h1_), (-w1, WALL_H + h1_)], "#f3f3f3" if r % 2 else "#fafafa", 0.0)
        n = max(1, int(round(2 * ((w0 + w1) / 2) / PIECE_W)))
        for i in range(1, n):
            x = -1.0 + 2.0 * i / n if r % 2 == 0 else -1.0 + 2.0 * (i - 0.5) / n
            if abs(x) < 1:
                sh.line([(x * w0, WALL_H + h0), (x * w1, WALL_H + h1_)], 0.13, "#a8a8a8")
        sh.line([(-w1, WALL_H + h1_), (w1, WALL_H + h1_)], 0.13, "#a8a8a8")
    for sgn in (-1, 1):
        def X(x): return sgn * x
        # footing + stem + wall + buttress
        foot = [(X(HALF + WALL / 2 + BUT_L / 2 - FOOT_W / 2 + 0), FOOT_Z), (X(HALF + WALL / 2 + BUT_L / 2 + FOOT_W / 2), FOOT_Z),
                (X(HALF + WALL / 2 + BUT_L / 2 + FOOT_W / 2), FOOT_Z + FOOT_T), (X(HALF + WALL / 2 + BUT_L / 2 - FOOT_W / 2), FOOT_Z + FOOT_T)]
        stem = [(X(HALF), FOOT_Z + FOOT_T), (X(HALF + WALL + BUT_L), FOOT_Z + FOOT_T), (X(HALF + WALL + BUT_L), 0), (X(HALF), 0)]
        wall = [(X(HALF), 0), (X(HALF + WALL), 0), (X(HALF + WALL), WALL_H - BEAM_H), (X(HALF), WALL_H - BEAM_H)]
        but = [(X(HALF + WALL), 0), (X(HALF + WALL + BUT_L), 0), (X(HALF + WALL + BUT_L), WALL_H), (X(HALF + WALL), WALL_H)]
        beam = [(X(HALF), WALL_H - BEAM_H), (X(HALF + WALL), WALL_H - BEAM_H), (X(HALF + WALL), WALL_H), (X(HALF), WALL_H)]
        for p in (foot, stem, wall, but, beam):
            sh.poly(p, "#000", 0.3 if p in (foot, stem) else 0.7)     # below ground: finer line
        for p in (foot, stem, wall, but, beam):
            sh.poly(p, "#fff", 0.0); sh.poly(p, "url(#cast)" if p is beam else "url(#conc)", 0.0)    # beam is cut in the section plane: crossed hatch
        li, ll, _ = WALL_LAYERS
        zt = WALL_H - BEAM_H
        sh.poly([(X(HALF + li), 0), (X(HALF + li + ll), 0), (X(HALF + li + ll), zt), (X(HALF + li), zt)], PINK, 0.0)
        loops(sh, "lp{}".format(sgn), X(HALF + li), X(HALF + li + ll), 0, zt, 0.15)      # wall: loop symbol from the reference
        sh.line([(X(HALF + li), 0), (X(HALF + li), zt)], 0.25); sh.line([(X(HALF + li + ll), 0), (X(HALF + li + ll), zt)], 0.25)
        sh.poly(beam, "none", 0.3)
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
    # north wall beyond the cut, seen from inside: printed pieces, ring beam band, door (NE bay) and window (NW bay)
    zt = WALL_H - BEAM_H
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
    sh.poly(rect(-HALF, zt, HALF, WALL_H), "#e8e8e8", 0.0)
    sh.line([(-HALF, zt), (HALF, zt)], 0.25, "#888")
    sh.text(-HALF + 150, zt + 110, "ring beam", 2.2, "start", italic=True, color="#666")
    cx = (HALF + WALL / 2) / 2
    for x0, x1, z0, z1, lab in ((cx - 500, cx + 500, 0, 2000, "door"), (-cx - 900, -cx + 900, 900, 2000, "window")):
        sh.poly(rect(x0, z0, x1, z1), "#fff", 0.3, "#444")
        sh.poly(rect(x0 - 40, z0, x1 + 40, z1 + 40), "none", 0.15, "#444")
        if lab == "window":
            sh.line([((x0 + x1) / 2, z0), ((x0 + x1) / 2, z1)], 0.2, "#444")
            sh.poly(rect(x0 - 40, z0 - 60, x1 + 40, z0), "none", 0.2, "#444")
        sh.text((x0 + x1) / 2, (z0 + z1) / 2, lab + " (N wall)", 2.2, italic=True, color="#555")
    sh.line(ground, 0.5)       # ground line drawn last so it runs unbroken through the walls and buttresses
    # floor, openings
    sh.line([(-HALF, 0), (HALF, 0)], 0.6)
    sh.line([(-HALF + 20, -150), (HALF - 20, -150)], 0.2, dash="3 1")
    sh.text(0, -420, "floor slab on gravel (not detailed)", 2.4, italic=True)
    # dims
    xr = HALF + WALL + BUT_L
    sh.dim_v([0, WALL_H, WALL_H + RISE], xr + 900 + 600 * 0, ext=xr + 150, labels=["2500", "8000"])
    sh.dim_v([0, WALL_H + RISE], xr + 1500, ext=xr + 150, labels=["10500 total"])
    sh.dim_v([FOOT_Z, 0], xr + 900, ext=xr + 150, labels=["1000"])
    sh.dim_h([-HALF - WALL, -HALF, HALF, HALF + WALL], FOOT_Z - 650, ext=FOOT_Z, labels=["{:g}".format(WALL), "10000 clear", "{:g}".format(WALL)])
    sh.dim_h([-HALF - WALL - BUT_L, HALF + WALL + BUT_L], FOOT_Z - 1150, ext=FOOT_Z - 700, labels=["{:g} overall incl. buttresses".format(CLEAR + 2 * (WALL + BUT_L))])
    sh.dim_h([-OPEN / 2, OPEN / 2], WALL_H + RISE + 600, ext=WALL_H + RISE, labels=["1000"])
    sh.line([(HALF, WALL_H), (OPEN / 2, WALL_H + RISE)], 0.0)
    sh.level(-xr - 600, 0, "±0.00", -1); sh.level(-xr - 600, WALL_H, "+2.50 eave", -1); sh.level(-xr - 600, WALL_H + RISE, "+10.50 crown", -1)
    sh.level(-xr - 600, FOOT_Z, "-1.00", -1)
    sh.text(0, 3200, "ROOM", 3.2, weight="bold"); sh.text(0, 2700, "10 x 10 m clear", 2.6)
    sh.text(HALF - RUN * 0.5 - 1000, WALL_H + RISE * 0.5, "{:.1f}°".format(SLOPE), 2.8, rot=0, italic=True)
    sh.callout(1, xr + 2400, FOOT_Z + 200, xr - 200, FOOT_Z + 200)
    sh.callout(2, HALF + WALL / 2 + 2600, 1800, HALF + WALL / 2, 1200)
    sh.callout(3, HALF + WALL / 2 + 3300, 3200, HALF + WALL / 2, WALL_H - BEAM_H / 2)
    sh.callout(4, xr + 2400, 900, HALF + WALL + BUT_L - 150, 700)
    sh.callout(5, 3600, 7500, HALF - K * 5200 + 200, WALL_H + 5200)
    sh.callout(6, 1800, WALL_H + RISE + 1100, 300, WALL_H + RISE)
    # detail marker D1
    sh.line([(HALF + 450 - 900, WALL_H - 450), (HALF + 450 + 900, WALL_H - 450), (HALF + 450 + 900, WALL_H + 1500), (HALF + 450 - 900, WALL_H + 1500), (HALF + 450 - 900, WALL_H - 450)], 0.25, dash="1.5 0.8")
    sh.circle_label(HALF + 450 + 900 + 400, WALL_H + 1500, "D1", 3.0)
    return sh

# =====================================================================
# 3. DETAIL D1  eave, 1:10
# =====================================================================
def clip_begin(sh, cid, x0, z0, x1, z1):
    (ax, ay), (bx, by) = sh.P(x0, z0), sh.P(x1, z1)
    sh.o.append('<clipPath id="{}"><rect x="{:.2f}" y="{:.2f}" width="{:.2f}" height="{:.2f}"/></clipPath><g clip-path="url(#{})">'.format(
        cid, min(ax, bx), min(ay, by), abs(bx - ax), abs(by - ay), cid))

def clip_end(sh): sh.o.append('</g>')

def printed(sh, pts, w_mm, f, fill="url(#conc)"):
    """a printed bead drawn as a wide stroke: black rim, white body, hatch. w_mm = bead width in mm, f = model-to-paper factor."""
    w = w_mm * sh.s * f
    ext = 'stroke-linecap="butt"'
    sh.line(pts, w + 0.5, "#000", extra=ext); sh.line(pts, w, "#fff", extra=ext); sh.line(pts, w - 0.04, fill, extra=ext)

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
    sh.o.append('<circle cx="{:.2f}" cy="{:.2f}" r="{:.2f}" fill="#fff" stroke="#000" stroke-width="0.3"/>'.format(px, py, 27.5 * sh.s * F))
    sh.o.append('<circle cx="{:.2f}" cy="{:.2f}" r="{:.2f}" fill="{}"/>'.format(px, py, 6 * sh.s * F, BLUE))
    # frame ends (break)
    for v in (0, P):
        sh.line([M(-40, v), M(440, v)], 0.25, "#000", dash="3 1 0.6 1")
    # dimensions (horizontal, paper-true: 1:5)
    z_d = Z0 - 140
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
    sh.text(X0, Z0 + F * P + 240, "Plan of one roof piece, 1:5", 3.4, "start", weight="bold")
    sh.text(X0, Z0 + F * P + 150, "layer pattern, bars every ≈ 600 along the path", 2.4, "start")

def detail():
    ZB, ZT = 1500.0, 3400.0
    sh = Sheet(10, 100, 420, "Detail D1: eave, roof to wall",
               "at the mid-span buttress, section A-A, 1:10 · piece plan 1:5",
               [(1, False, "Roof outer layer 80, printed with the rest of the piece; cladding on the outside face (dashed line)."),
                (2, False, "Zig-zag bead 80 in a 160 zone; it touches the outer layer and layer 2 every ≈ 600; the cells between are open air pockets for ventilation."),
                (3, False, "Layer 2, 80: printed bead that curves to leave a pocket for the bar."),
                (4, False, "Inner layer 1, 80, room side. Layers 1 and 2 together are the structural leaf: 160 at the base, 80 at the crown (layer 2 ends)."),
                (5, True, "Rebar pocket Ø55 in the leaf, bar Ø12 every ≈ 600 along the path, grouted after placing."),
                (6, True, "Starter bars Ø12 from the ring beam into the pockets, lap 650; roof bars stop where the load allows (open)."),
                (7, True, "Ring bars Ø12 in the pocket zone every 300 (assumed)."),
                (8, True, "Ring beam 400 x 500, cast in place: 6 Ø16, stirrups Ø8 / 150; embedded in the buttress notch."),
                (9, False, "Buttress 400 wide, 700 from the inner face (300 beyond the wall), L-shaped around the ring beam; top flush with the roof base at +2.50."),
                (10, True, "Wall 400 printed, same pattern as the roof; Ø16 bars in the pockets run from the footing into the beam and on into the roof pockets (assumed).")],
               ["Layer pattern from your drawing: from the inside, 80 + 80 printed layers (the second curves round the bar), then a 160 zig-zag zone, then the 80 outer layer; 400 in total.",
                "Roof thicknesses are square to the slope; the wall is vertical. Black heavy lines and dots = rebar, white lattice cells = open air, single hatch = printed concrete, crossed hatch = ring beam cut in the section plane."])
    ZH = WALL_H
    # --- wall + buttress + beam
    wall = rect(0, ZB, WALL, WALL_H - BEAM_H)
    beam = rect(0, WALL_H - BEAM_H, WALL, WALL_H)
    but = [(WALL, ZB), (WALL + BUT_L, ZB), (WALL + BUT_L, WALL_H), (WALL, WALL_H)]
    for p in (wall, beam, but):
        sh.poly(p, "#000", 0.7)
    for p in (wall, beam, but):
        sh.poly(p, "#fff", 0.0); sh.poly(p, "url(#cast)" if p is beam else "url(#conc)", 0.0)    # beam is cut in the section plane: crossed hatch
    li, ll, ls_ = WALL_LAYERS
    sh.poly(rect(li, ZB, li + ll, WALL_H - BEAM_H), PINK, 0.0)
    sh.line([(li, ZB), (li, WALL_H - BEAM_H)], 0.3); sh.line([(li + ll, ZB), (li + ll, WALL_H - BEAM_H)], 0.3)
    sh.line([(80, ZB), (80, WALL_H - BEAM_H)], 0.2)   # joint between the two inner layers
    sh.poly(wall, "none", 0.45); sh.poly(beam, "none", 0.55); sh.poly(but, "none", 0.45)
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
        sh.poly(p, "#fff", 0.0); sh.poly(p, "url(#conc)", 0.0)
    sh.poly(latp, PINK, 0.0)
    for p in (layer1, layer2, latp, skinp):
        sh.poly(p, "none", 0.45)
    loops(sh, "lpd", li, li + ll, ZB, WALL_H - BEAM_H, 0.2)      # wall: loop symbol from the reference
    # cladding on the outside face: a row of short dashes just outside the outer layer
    off = 8.0
    sh.line([(rx(0)[3] + nrm[0] * off, ZH + nrm[1] * off), (rx(h1)[3] + nrm[0] * off, ZH + h1 + nrm[1] * off)], 0.7, "#000", dash="1.3 0.9")
    # the roof continues: dash-dot line at the top of the detail, square to the slope
    sh.line([(c[0] - nrm[0] * 380, c[1] - nrm[1] * 380), (c[0] + nrm[0] * 560, c[1] + nrm[1] * 560)], 0.5, "#000", dash="7 1.5 1.2 1.5")
    # ---- rebar
    xb = lambda h: rx(h)[0] + 80 * SH                                  # centre of the pocket = joint of layers 1 and 2
    for sgn in (-1, 1):
        sh.line([(xb(0) + sgn * 27.5 * SH, ZH), (xb(h1) + sgn * 27.5 * SH, ZH + h1)], 0.15, "#555", dash="2 0.8")     # pocket Ø55
    sh.line([(xb(0) - 14, WALL_H - 380), (xb(0) - 14, ZH), (xb(566) - 14, ZH + 566)], 0.7, BLUE)           # starter, lap 650 along the slope
    sh.line([(xb(0) + 14, ZH), (xb(h1) + 14, ZH + h1)], 0.7, BLUE)                                        # roof bar
    for h in range(300, int(h1), 300):
        sh.dot(xb(h), ZH + h, 6)
    # ring beam
    sh.poly(rect(30, WALL_H - BEAM_H + 30, WALL - 30, WALL_H - 30), "none", 0.35, BLUE)
    for (x, z) in [(60, WALL_H - BEAM_H + 60), (WALL - 60, WALL_H - BEAM_H + 60), (60, WALL_H - 60), (WALL - 60, WALL_H - 60), (60, WALL_H - BEAM_H / 2), (WALL - 60, WALL_H - BEAM_H / 2)]:
        sh.dot(x, z, 8)
    for sgn in (-1, 1):
        sh.line([(80 + sgn * 27.5, ZB), (80 + sgn * 27.5, WALL_H - BEAM_H)], 0.15, "#555", dash="2 0.8")
    sh.line([(80, ZB), (80, WALL_H - 60)], 0.7, BLUE)
    # ---- dimensions
    sh.dim_v([WALL_H - BEAM_H, WALL_H], -260, ext=-30, labels=["{:g}".format(BEAM_H)])
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
    sh.callout(3, -620, ZH + 360, xb(360) + 50, ZH + 360)
    sh.callout(4, -620, ZH + 560, rx(560)[0] + 40, ZH + 560)
    sh.callout(5, -620, ZH + 760, xb(760), ZH + 760)
    sh.callout(6, -470, WALL_H - 140, xb(0) - 14, WALL_H - 140)
    sh.callout(7, -620, ZH + 160, xb(300), ZH + 300)
    sh.callout(8, 760, WALL_H - 120, WALL - 60, WALL_H - 150)
    sh.callout(9, 800, WALL_H - 800, WALL + 150, WALL_H - 840)
    sh.callout(10, 1100, ZB + 600, li + ll / 2, ZB + 600)
    piece_plan(sh, 1000, 2600)
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
    export(section(), os.path.join(out, "pyramid-section"))
    export(detail(), os.path.join(out, "pyramid-detail"))
    print("slope {:.1f} deg, run {:g}, rise {:g}".format(SLOPE, RUN, RISE))
