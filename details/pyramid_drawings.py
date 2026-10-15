"""Plan, total section and eave detail for the 10 x 10 m buttressed pyramid roof (3D concrete printed).
Standalone: no dependency on scripts/cork_house_roof.py. Model units mm. Every number you may want to change is in PARAMETERS.

Run:  python details/make_set.py   (builds the whole set; this file only defines the drawings)"""
import math, os, sys

# ================= PARAMETERS =================
CLEAR = 10000.0            # clear inside dimension, square plan
WALL = 400.0               # wall thickness = roof base width
SOLID_H = 300.0            # the first 300 (vertical) of the roof is completely solid concrete, no cavity or lattice; there is no separate ring beam
WALL_H = 2500.0            # ground to top of wall (= eave, roof base)
BUT_TOTAL, BUT_W = 1000.0, 400.0  # buttress: 1000 long measured from the inner wall face (flush with the wall), 400 wide (= the wall thickness, constant along its length)
BUT_L = BUT_TOTAL - WALL          # so it projects only this far beyond the outer wall face
OPEN = 1000.0              # square opening at the crown (inner face)
RISE = 6000.0              # roof height
# printed build-up, same defaults as scripts/karamba_model.py: every printed layer is one bead wide
BEAD = 30.0                # print width of every printed layer (roof and walls)
OUTER_BEADS = 2            # number of outer beads (roof and walls)
LATTICE = 120.0            # roof lattice zone: a wavy printed bead with insulation between its loops
FILL = 0.25                # solid share of the lattice zones (wavy bead); used by the Karamba model for the weight
RIB_W, RIB_D = 160.0, 160.0   # cast rib width; rib depth = depth of the rib zone (a cavity crossed by the ribs)
# roof, square to the slope, room side out (constant from eave to crown): inner bead | rib zone | middle bead | lattice zone | outer beads
ROOF_LAYERS = (BEAD, RIB_D, BEAD, LATTICE, OUTER_BEADS * BEAD)
T_ROOF = sum(ROOF_LAYERS)  # 400
RIB_C = BEAD + RIB_D / 2   # rib axis = centre of the rib zone, from the room-side face (= the shell surface of the Karamba model)
WAVE_ROOF, WAVE_WALL = 300.0, 480.0   # period of the wavy lattice bead in the roof / the walls (assumed)
# no insulation or cladding outside the printed shell: the insulation is in the lattice zones, the outer beads are exposed concrete
BUT_SPACING = 1500.0       # buttresses about every 1.5 m along each wall
# wall, room side out: inner bead | lattice zone (wavy bead + insulation) | outer beads
WALL_LAYERS = (BEAD, WALL - (1 + OUTER_BEADS) * BEAD, OUTER_BEADS * BEAD)
FOOT_W, FOOT_T, FOOT_Z = 1800.0, 250.0, -1000.0   # footing width, thickness, underside level (assumed)
HALF = CLEAR / 2
RUN = HALF - OPEN / 2
K = RUN / RISE             # inward lean of the roof (horizontal per vertical)
SLOPE = math.degrees(math.atan2(RISE, RUN))
assert WALL_LAYERS[1] > 0, "the wall is thinner than its beads"

def but_pos():
    """buttress axes along a wall (centre line, corners included): equal bays of about BUT_SPACING"""
    c = HALF + WALL / 2
    nb = int(round(2 * c / BUT_SPACING))
    return [-c + 2 * c * k / nb for k in range(nb + 1)]

# layer thicknesses are square to the slope; horizontally each is wider by 1 / sin(slope)
SIN = math.sin(math.radians(SLOPE))
SH = 1.0 / SIN
def rx(h):
    """horizontal x of the roof layer faces at height h above the eave (x = 0: inner wall face), room side out:
    0 room-side face | inner bead | 1 | rib zone | 2 | middle bead | 3 | lattice zone | 4 | outer beads | 5 outer face (= rx(h)[-1])"""
    x = -K * h
    out = [x]
    for t in ROOF_LAYERS:
        x += t * SH; out.append(x)
    return tuple(out)

def wavy(A, B, period):
    """centreline of the wavy lattice bead between two edge offsets A < B (bead centrelines), as a function of the
    position along the band: touches B at s = 0 and every period, A half a period later"""
    m, a = (A + B) / 2, (B - A) / 2
    return lambda s: m + a * math.cos(2 * math.pi * s / period)

def wavy_ring(r_in, r_out, period, w=BEAD, n=12):
    """closed wavy bead around a square (plan), in the band between the squares of half width r_in < r_out; it touches
    the outer side at the corners and every period, the inner side half a period later. Returns the centreline points."""
    R = r_out - w / 2
    p = 2 * R / max(1, round(2 * R / period))
    f = wavy(r_in + w / 2, R, p)
    k = int(round(2 * R / p)) * n
    side = [(-R + 2 * R * i / k, f(2 * R * i / k)) for i in range(k)]
    pts = [(s, -r) for s, r in side] + [(r, s) for s, r in side] + [(-s, r) for s, r in side] + [(-r, -s) for s, r in side]
    return pts + [pts[0]]

BLUE, PINK = "#000", "#f4d6d6"   # BLUE = rebar colour (black: the drawings are greyscale); PINK = marker for the open air pockets

# ================= svg helpers =================
class Sheet:
    def __init__(self, scale, ox, oz, title, sub, legend, notes, w=420, h=297):
        self.s, self.ox, self.oz, self.w, self.h = 1.0 / scale, ox, oz, w, h
        self.scale = scale
        self.o = []; self.title, self.sub, self.legend, self.notes = title, sub, legend, notes
        self.plain_legend = False
        self.sheet_no = ""                                  # set by make_set.py
        self.scale_note = ""                                # e.g. "insets at 1:10" when a sheet mixes scales
        self.dimlfac = 1.0                                  # measurement factor for dimensions inside scaled insets (CAD DIMLFAC)
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
        """horizontal dimension chain at height z; ext = z the extension lines start from. Recorded for CAD as real DIMENSION entities."""
        self._rec("dimh", list(xs), z, z if ext is None else ext, labels, size, self.dimlfac)
        self.mute += 1
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
        self.mute -= 1
    def dim_v(self, zs, x, ext=None, labels=None, size=2.5):
        self._rec("dimv", list(zs), x, x if ext is None else ext, labels, size, self.dimlfac)
        self.mute += 1
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
        self.mute -= 1
    def dim_aligned(self, pts, t_, off, size=2.5):
        """dimension chain between points pts that lie on a straight line, measured along that line; the dimension line is offset by off
        along the unit vector t_ (perpendicular to the measured direction). Recorded for CAD as ALIGNED dimensions."""
        self._rec("dima", [tuple(p) for p in pts], tuple(t_), off, size, self.dimlfac)
        self.mute += 1
        _ol, self.layer = self.layer, "DIMS"
        s = self.s
        dl = [(p[0] + t_[0] * off, p[1] + t_[1] * off) for p in pts]
        d = (pts[-1][0] - pts[0][0], pts[-1][1] - pts[0][1]); L = math.hypot(*d); u = (d[0] / L, d[1] / L)
        ang = -math.degrees(math.atan2(u[1], u[0])); ang = ang if abs(ang) <= 90 else ang + 180
        self.line([dl[0], dl[-1]], 0.2)
        tk = 1.2 / s / 2
        for p, q in zip(pts, dl):
            self.line([(p[0] + t_[0] * 0.8 / s, p[1] + t_[1] * 0.8 / s), (q[0] + t_[0] * 1.2 / s, q[1] + t_[1] * 1.2 / s)], 0.12)
            self.line([(q[0] - (u[0] + t_[0]) * tk, q[1] - (u[1] + t_[1]) * tk), (q[0] + (u[0] + t_[0]) * tk, q[1] + (u[1] + t_[1]) * tk)], 0.45)
        sg = 1 if (u[0] * t_[1] - u[1] * t_[0]) < 0 else -1
        for k in range(len(pts) - 1):
            mx, mz = (dl[k][0] + dl[k + 1][0]) / 2 + t_[0] * 0.9 / s, (dl[k][1] + dl[k + 1][1]) / 2 + t_[1] * 0.9 / s
            self.text(mx, mz, "{:g}".format(round(math.hypot(pts[k + 1][0] - pts[k][0], pts[k + 1][1] - pts[k][1]) * self.dimlfac)), size, rot=ang)
        self.layer = _ol
        self.mute -= 1
    def level(self, x, z, label, side=1):
        _ol, self.layer = self.layer, "ANNOTATION"          # level marks are annotation, not dimensions
        s = self.s
        self.line([(x, z), (x + side * 6 / s, z)], 0.2)
        self.poly([(x, z), (x + 1.2 / s, z + 1.6 / s), (x - 1.2 / s, z + 1.6 / s)], "#000", 0.1)
        self.text(x + side * 7 / s, z - 0.5 / s, label, 2.5, "start" if side > 0 else "end")
        self.layer = _ol
    def panel(self):
        """everything outside the drawing area, in paper mm (y down): border, title block, legend, notes, scale bar, footer.
        Used by svg() and by the CAD export (paper space), so both are identical. Items: ("line", x1, y1, x2, y2, w), ("rect", x, y, w, h, fill, sw),
        ("circle", cx, cy, r, fill), ("text", x, y, size, text, bold, anchor)."""
        W, H = self.w, self.h
        tb = W - 112
        it = [("rect", 8, 8, W - 16, H - 16, None, 0.35), ("line", tb, 8, tb, H - 8, 0.35)]
        x0, y = tb + 4, 20
        it.append(("text", x0, y, 5.4, self.title, True, "start")); y += 5.5
        if self.sub:
            it.append(("text", x0, y, 3.1, self.sub, False, "start"))
        y += 9
        for n, _assumed, txt in self.legend:
            lines = wrap(txt, 52)
            it.append(("circle", x0 + 2.3, y - 1, 2.3, "#fff"))
            it.append(("text", x0 + 2.3, y, 2.7, str(n), False, "middle"))
            for i, l in enumerate(lines):
                it.append(("text", x0 + 7, y + i * 3.5, 2.8, l, False, "start"))
            y += 3.5 * len(lines) + 2
        if self.notes:
            y += 3
            it.append(("text", x0, y, 3.1, "Notes", True, "start")); y += 4.5
        for n_ in self.notes:
            for i, l in enumerate(wrap(n_, 58)):
                it.append(("text", x0 + (0 if i == 0 else 2), y, 2.8, l, False, "start")); y += 3.5
            y += 1
        # scale bar (5 x 1 m or 5 x 100 mm)
        unit = 1000 if self.scale >= 50 else 100
        label = "m" if unit == 1000 else "dm"
        sy = H - 30
        nb = 4
        for i in range(nb):
            it.append(("rect", x0 + i * unit * self.s, sy, unit * self.s, 1.6, "#000" if i % 2 == 0 else "#fff", 0.2))
            it.append(("text", x0 + i * unit * self.s, sy - 1, 2.5, str(i), False, "middle"))
        it.append(("text", x0 + nb * unit * self.s, sy - 1, 2.5, str(nb), False, "middle"))
        it.append(("text", x0 + nb * unit * self.s + 2, sy + 1.4, 2.5, label, False, "start"))
        # title block footer
        it.append(("line", tb, H - 24, W - 8, H - 24, 0.35))
        it.append(("text", x0, H - 18.5, 2.6, "Pyramid roof · 3D-printed concrete · GSAPP", True, "start"))
        it.append(("text", x0, H - 14.5, 2.6, "Scale 1:{} at A3{} · dimensions in mm".format(self.scale, (" · " + self.scale_note) if self.scale_note else ""), False, "start"))
        it.append(("text", x0, H - 10.5, 2.6, "2026-10-14 · hand estimates, not engineered", False, "start"))
        if self.sheet_no:
            it.append(("text", W - 11, H - 12, 6.0, self.sheet_no, True, "end"))
        return it

    def svg(self):
        W, H = self.w, self.h
        parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="{}mm" height="{}mm" viewBox="0 0 {} {}" font-family="Helvetica, Arial, sans-serif">'.format(W, H, W, H),
                 '<defs>'
                 '<pattern id="conc" width="1.6" height="1.6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="1.6" stroke="#000" stroke-width="0.14"/></pattern>'
                 '<pattern id="earth" width="2.4" height="2.4" patternUnits="userSpaceOnUse" patternTransform="rotate(-45)"><line x1="0" y1="0" x2="0" y2="2.4" stroke="#777" stroke-width="0.12"/></pattern>'
                 '<pattern id="cast" width="1.6" height="1.6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="1.6" stroke="#000" stroke-width="0.14"/><line x1="0" y1="0" x2="1.6" y2="0" stroke="#000" stroke-width="0.14"/></pattern>'
                 '<pattern id="dots" width="1.5" height="1.5" patternUnits="userSpaceOnUse"><circle cx="0.4" cy="0.4" r="0.11" fill="#000"/><circle cx="1.15" cy="1.1" r="0.11" fill="#000"/></pattern>'
                 '</defs>',
                 '<rect width="{}" height="{}" fill="#fff"/>'.format(W, H), '<g>']
        parts += self.o
        parts.append('</g>')
        tb = W - 112
        parts.append('<rect x="{}" y="0" width="{}" height="{}" fill="#fff"/>'.format(tb, W - tb, H))      # nothing of the drawing runs into the title block
        for i in self.panel():
            if i[0] == "line":
                parts.append('<line x1="{}" y1="{}" x2="{}" y2="{}" stroke="#000" stroke-width="{}"/>'.format(*i[1:]))
            elif i[0] == "rect":
                _, x, y, w, h, fill, sw = i
                parts.append('<rect x="{:.2f}" y="{:.2f}" width="{:.2f}" height="{:.2f}" fill="{}" stroke="#000" stroke-width="{}"/>'.format(x, y, w, h, fill or "none", sw))
            elif i[0] == "circle":
                parts.append('<circle cx="{:.2f}" cy="{:.2f}" r="{}" fill="{}" stroke="#000" stroke-width="0.3"/>'.format(*i[1:]))
            else:
                _, x, y, size, txt, bold, anchor = i
                parts.append('<text x="{:.2f}" y="{:.2f}" font-size="{}" text-anchor="{}"{}>{}</text>'.format(x, y, size, anchor, ' font-weight="bold"' if bold else "", txt))
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
    sh = Sheet(50, 154, 148.5, "Floor plan" + ("" if grid is None else " · roof grid " + grid),
               "10 x 10 m clear · buttress every 1.5 m · printed walls",
               [(1, True, "Printed wall {:g} (= roof base width), room side out: inner bead {:g}, lattice zone {:g} (wavy bead {:g} with insulation between its loops, dotted), {} outer beads {:g}. Buttresses solid black: 400 wide (same as the wall), 1000 deep from the inner face (flush with the wall inside), so they project 600 outside; one about every 1.5 m (7 bays of 1486 on the wall centreline, 8 per side, corners included).".format(WALL, BEAD, WALL_LAYERS[1], BEAD, OUTER_BEADS, BEAD)),
                (2, True, "Every other bay (the 2nd, 4th and 6th) is a full-height curtain wall, the whole bay between two buttresses; the middle bay of the south and north walls has a 1000 door instead. The other bays stay printed wall. Positions and sizes are placeholders."),
                (3, False, "Pyramid roof above (dashed): 1000 x 1000 clear crown opening, hips to the corners; the roof is {:g} thick square to the slope from eave to crown, so the shell ends {:.0f} outside the wall face; the outer beads are exposed concrete (no cladding).".format(T_ROOF, T_ROOF * SH - WALL)),
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
    # wall layers, room side out: inner bead, lattice zone (wavy bead + insulation), outer beads
    li_, ll_, _ = WALL_LAYERS
    z0_, z1_ = a + li_, a + li_ + ll_
    sq = lambda h: [(-h, -h), (h, -h), (h, h), (-h, h)]
    dair = "M" + " L".join("{:.2f},{:.2f}".format(*sh.P(*q)) for q in sq(z1_)) + "Z M" + " L".join("{:.2f},{:.2f}".format(*sh.P(*q)) for q in sq(z0_)) + "Z"
    sh.o.append('<path d="{0}" fill="#fff" fill-rule="evenodd"/><path d="{0}" fill="url(#dots)" fill-rule="evenodd"/>'.format(dair))
    sh._rec("hatch", [ring, sq(z1_), sq(z0_), inner], "conc", "HATCH-PRINTED")     # wall = inner bead + outer beads, lattice zone left open
    sh._rec("ring", sq(z1_), sq(z0_), "#fff", "url(#dots)")                         # insulation in the lattice zone
    for h_ in [z0_, z1_] + [z1_ + BEAD * i for i in range(1, OUTER_BEADS)]:
        sh.poly(sq(h_), "none", 0.15 if h_ in (z0_, z1_) else 0.08)
    # printed wavy bead as one continuous ring, so it turns the corners: it touches the outer beads at every corner
    ring = wavy_ring(z0_, z1_, WAVE_WALL)
    printed(sh, ring, BEAD, 1.0, fill="#fff", rim=0.12)
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
    DOOR_W = 1000.0
    def curtain(side, al, w):
        """full-height curtain wall filling the whole bay between two buttresses: glazing line in the middle of the wall, mullion ticks"""
        sh.poly([pt(side, al - w / 2, -5), pt(side, al + w / 2, -5), pt(side, al + w / 2, WALL + 5), pt(side, al - w / 2, WALL + 5)], "#fff", 0.0)
        for e in (-w / 2, w / 2):
            sh.line([pt(side, al + e, 0), pt(side, al + e, WALL)], 0.5)
        for dv in (-25, 25):                                                     # glazing: two thin lines
            sh.line([pt(side, al - w / 2, WALL / 2 + dv), pt(side, al + w / 2, WALL / 2 + dv)], 0.25)
        for e in (-w / 2 + 25, 0.0, w / 2 - 25):                                  # mullions 50 x 150
            sh.poly([pt(side, al + e - 25, WALL / 2 - 75), pt(side, al + e + 25, WALL / 2 - 75), pt(side, al + e + 25, WALL / 2 + 75), pt(side, al + e - 25, WALL / 2 + 75)], "#000", 0.2)
    for side in "SNEW":                                  # every other bay (the odd ones) is a full curtain wall, or the door (middle bay of the south and north walls); the even bays stay printed wall
        for j in (1, 3, 5):
            cxm = (xs[j] + xs[j + 1]) / 2
            if side in "SN" and j == 3: opening(side, cxm, DOOR_W, True)
            else: curtain(side, cxm, xs[j + 1] - xs[j] - BUT_W)
    # roof above, dashed
    top_o = OPEN / 2 + T_ROOF * SH                  # outer face half width at the crown
    base_o = HALF + T_ROOF * SH
    for half in (base_o, top_o, OPEN / 2):
        sh.line([(-half, -half), (half, -half), (half, half), (-half, half), (-half, -half)], 0.2, dash="3 1.2 0.6 1.2")
    for sx in (-1, 1):
        for sy in (-1, 1):
            sh.line([(sx * base_o, sy * base_o), (sx * top_o, sy * top_o)], 0.2, dash="3 1.2 0.6 1.2")
    sh.text(0, 0, "pyramid roof above", 2.6, italic=True); sh.text(0, -450, "crown opening 1000 x 1000", 2.4, italic=True)
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
        sh.legend.append((5, True, "Cast ribs of roof grid {} seen from above (dashed), with the bottom ring (the 300 solid base) and the horizontal / top rings.".format(grid)))
    # grid
    gx = 7500
    E = b + BUT_L + 800                                  # grid bubbles, just inside the sheet border
    for lab, v in zip("ABCDEFGH", xs):
        sh.line([(v, -E + 200), (v, E - 200)], 0.12, dash="6 1 1 1")
        sh.circle_label(v, E, lab, 2.6); sh.circle_label(v, -E, lab, 2.6)
    for lab, v in zip("12345678", xs):
        sh.line([(-E + 200, v), (E - 200, v)], 0.12, dash="6 1 1 1")
        if v != y0:                                      # the section line A-A runs along this axis; its markers sit there
            sh.circle_label(-E, v, lab, 2.6); sh.circle_label(E, v, lab, 2.6)
    # dimensions
    sh.dim_h([-b, -a, a, b], -b - BUT_L - 350, ext=-b - 100, labels=["{:g}".format(WALL), "10000 clear", "{:g}".format(WALL)])
    sh.dim_h([-b - BUT_L, b + BUT_L], -b - BUT_L - 700 + 0, ext=-b - BUT_L, labels=["{:g} overall".format(2 * (b + BUT_L))])
    bay_l = ["{:.0f}".format(xs[1] - xs[0])] * (len(xs) - 1)
    sh.dim_v(xs, -b - BUT_L - 350, ext=-b - 100, labels=bay_l)
    sh.dim_h(xs, b + BUT_L + 350, ext=b + 100, labels=bay_l)
    sh.dim_h([a, b, b + BUT_L], y0 + BUT_W / 2 + 350, ext=y0 + BUT_W / 2 + 40)                                   # wall 400 | buttress 600 beyond the wall
    sh.dim_h([a, a + BUT_TOTAL], y0 + BUT_W / 2 + 750, ext=y0 + BUT_W / 2 + 350, labels=["{:g} from the inner face".format(BUT_TOTAL)])
    sh.dim_v([y0 - BUT_W / 2, y0 + BUT_W / 2], b + BUT_L + 350, ext=b + BUT_L + 40)                                  # buttress width 400
    # section line A-A and detail marker
    L = E - 450
    sh.line([(-L, y0), (-b - BUT_L - 350, y0)], 0.5, dash="6 1.5 1 1.5"); sh.line([(b + BUT_L + 350, y0), (L, y0)], 0.5, dash="6 1.5 1 1.5")
    for sgn in (-1, 1):
        px_, py_ = sh.P(sgn * L, y0)
        tri = [(px_, py_ - 0.2), (px_, py_ - 4.5), (px_ + sgn * 3, py_ - 2.2)]
        sh.o.append('<polygon points="{:.2f},{:.2f} {:.2f},{:.2f} {:.2f},{:.2f}" fill="#000"/>'.format(*[c for p in tri for c in p]))
        sh._rec("solid", [((q[0] - sh.ox) / sh.s, (sh.oz - q[1]) / sh.s) for q in tri], "ANNOTATION")
        sh.circle_label(sgn * E, y0, "A", 2.6, "#000", "#fff")
    # detail D1 marker around the east eave
    sh.line([(b - 450, y0 - 450), (b + 450, y0 - 450), (b + 450, y0 + 450), (b - 450, y0 + 450), (b - 450, y0 - 450)], 0.25, dash="1.5 0.8")
    sh.circle_label(b + 450, y0 - 450 - 400, "D1", 3.0)
    sh.callout(1, b + BUT_L + 1100, c + 700, b, c + 100)
    sh.callout(2, -c / 2 - 1500, -b - BUT_L - 100, -c / 2 - 500, -b)
    sh.callout(3, 2500, 2500, top_o, top_o)
    sh.callout(4, -3600, (xs[5] + xs[6]) / 2, -b - BUT_L / 2, xs[6])
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
    """north wall seen from inside, laid out like the floor plan and drawn like the roof-grid sheets: buttress strips every ~1.5 m (outside the wall, shown through it),
    every other bay printed wall (white, very faint layer joints, dashed piece divisions in running bond), the bays in between full curtain wall, door in the middle bay"""
    xs = but_pos()
    zt = WALL_H
    dash = dict(color="#8c8c8c", dash="3 1.6")
    sh.poly(rect(-HALF, 0, HALF, zt), "#fff", 0.3)
    for j in range(0, len(xs) - 1, 2):                                        # printed wall in the even bays
        xa, xb = max(xs[j] + BUT_W / 2, -HALF), min(xs[j + 1] - BUT_W / 2, HALF)
        if xb <= xa: continue
        layers(sh, rect(xa, 0, xb, zt), 0, 0.03, step=100, color="#c4c4c4")
        for r in range(1, 5):
            sh.line([(xa, r * zt / 5), (xb, r * zt / 5)], 0.1, **dash)
        for r in range(5):
            if r % 2: sh.line([((xa + xb) / 2, r * zt / 5), ((xa + xb) / 2, (r + 1) * zt / 5)], 0.1, **dash)
    for x in xs:                                                              # buttresses (outside the wall), shown through it
        xa, xb = max(x - BUT_W / 2, -HALF), min(x + BUT_W / 2, HALF)
        if xb > xa:
            sh.poly(rect(xa, 0, xb, zt), "#fff", 0.35, "#555")
            layers(sh, rect(xa, 0, xb, zt), 0, 0.03, step=100, color="#c4c4c4")
    for j in (1, 3, 5):                                                       # curtain wall bays, door in the middle one
        xa, xb = xs[j] + BUT_W / 2, xs[j + 1] - BUT_W / 2
        if j == 3:
            cxm = (xa + xb) / 2
            sh.poly(rect(cxm - 500, 0, cxm + 500, 2000), "#fff", 0.3, "#444")
            sh.poly(rect(cxm - 540, 0, cxm + 540, 2040), "none", 0.15, "#444")
        else:
            sh.poly(rect(xa, 0, xb, zt), "#fff", 0.35, "#444")                  # full-height glazing
            sh.poly(rect(xa + 40, 40, xb - 40, zt - 40), "none", 0.15, "#444")   # frame
            sh.line([((xa + xb) / 2, 40), ((xa + xb) / 2, zt - 40)], 0.2, "#444")   # mullion
            for zz in (zt / 3, 2 * zt / 3): sh.line([(xa + 40, zz), (xb - 40, zz)], 0.15, "#444")   # transoms

def section(grid=None):
    y0 = but_pos()[3]
    gname = {"A": "roof grid A, ruled-surface columns", "B": "roof grid B, diamond lattice", None: "no roof grid shown"}[grid]
    sh = Sheet(50, 161, 240, "Total section A-A" + ("" if grid is None else " · grid " + grid),
               "through the east and west buttresses, looking north",
               [(1, True, "Footing {:g} x {:g}, underside at {:g} (frost depth and bearing are guesses).".format(FOOT_W, FOOT_T, FOOT_Z)),
                (2, True, "Wall {:g}. The cut passes through a buttress, so the wall is solid with the buttress here (no insulation). Between buttresses it is printed: an inner bead {:g}, a lattice zone {:g} (wavy bead + insulation), {} outer beads {:g}.".format(WALL, BEAD, WALL_LAYERS[1], OUTER_BEADS, BEAD)),
                (3, False, "Solid base of the roof: the first 300 (vertical) above the eave is completely solid concrete, 400 wide, no cavity or lattice zone; there is no ring beam."),
                (4, False, "Buttress 400 wide, 1000 from the inner face (600 beyond the wall), one about every 1.5 m (8 per side); it rises to +2.50, flush with the roof base."),
                (5, False, "Roof shell {:g} thick square to the slope, the same from eave to crown (about {:.0f} horizontally), every printed layer one {:g} bead: inner bead {:g}, rib zone {:g} (cavity crossed by the cast ribs), middle bead {:g}, lattice zone {:g} (wavy bead + insulation, dotted), {} outer beads {:g}, exposed concrete outside.".format(T_ROOF, T_ROOF * SH, BEAD, BEAD, RIB_D, BEAD, LATTICE, OUTER_BEADS, BEAD)),
                (6, False, "Crown opening 1000 clear; roof rises {:g} over {:g}, slope {:.1f}° ({:.1f}° from the vertical).".format(RISE, RUN, SLOPE, 90 - SLOPE)),
                (7, True, "Everything is 3D printed in 10 mm layers; crossed hatch = solid cast concrete (roof base, ribs). Printed layer joints and the cast fill of the buttress and footing are shown in the roof-grid sheets and in detail D1."),
                (8, True, "Cast ribs of the roof grid, seen on the back face as dashed outlines ({}). The cut lies between ribs, where the rib zone is an empty cavity; rib sections are on the roof-grid sheets.".format(gname))],
               ["Roof build-up as in the Karamba model (scripts/karamba_model.py): bead {:g}, {} outer beads, lattice {:g}, rib zone {:g}; inner and middle bead are the structural skins, the ribs the webs between them.".format(BEAD, OUTER_BEADS, LATTICE, RIB_D),
                "The cut runs through the 4th buttress from the south (y = {:.0f}), as on the floor plan. Beyond it the north wall is seen as on the plan: buttress every 1.5 m (strips outside the wall), every other bay printed wall, the bays in between full-height curtain wall (door in the middle one).".format(y0),
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
        zt = WALL_H
        # the cut passes through a buttress, so the wall is solid with it here: no lattice zone, no insulation
        sh.line([(X(HALF), 0), (X(HALF), WALL_H)], 0.6)
        # roof bands, room side out: inner bead | rib zone | middle bead | lattice zone | outer beads (rx edges 0..5)
        def band(i, j, h0=0.0, h1=RISE, a=0.0, b=0.0):
            lo0, lo1 = rx(h0)[i] + a, rx(h1)[i] + a; hi0, hi1 = rx(h0)[j] + b, rx(h1)[j] + b
            return [(X(HALF + lo0), WALL_H + h0), (X(HALF + lo1), WALL_H + h1), (X(HALF + hi1), WALL_H + h1), (X(HALF + hi0), WALL_H + h0)]
        shell = band(0, 5)
        inner_b, rib_z, mid_b, lat_z, outer_b = (band(i, i + 1) for i in range(5))
        sh.poly(shell, "#000", 0.7)
        for p in (inner_b, mid_b, outer_b):                                    # printed beads
            sh.poly(p, "#fff", 0.0); sh.poly(p, "url(#conc)", 0.0)
        sh.poly(rib_z, "#fff", 0.0)                                            # rib zone between ribs: empty cavity
        sh.poly(lat_z, "#fff", 0.0); sh.poly(lat_z, "url(#dots)", 0.0)       # lattice zone: wavy bead + insulation
        for p in (rib_z, lat_z):
            sh.poly(p, "none", 0.25)
        for i in range(1, OUTER_BEADS):                                        # joints between the outer beads
            e = [band(4, 4, a=i * BEAD * SH)[k] for k in (0, 1)]
            sh.line(e, 0.1)
        sh.poly(shell, "none", 0.6)
        # solid base: the first SOLID_H of the roof is one block of concrete over the full 400 (crossed hatch = cast solid)
        solid = [(X(HALF + rx(0)[0]), WALL_H), (X(HALF + rx(SOLID_H)[0]), WALL_H + SOLID_H), (X(HALF + rx(SOLID_H)[-1]), WALL_H + SOLID_H), (X(HALF + rx(0)[-1]), WALL_H)]
        sh.poly(solid, "#fff", 0.0); sh.poly(solid, "url(#cast)", 0.0); sh.poly(solid, "none", 0.6)
        sh.line([(X(HALF + rx(0)[0]), WALL_H), (X(HALF + rx(0)[-1]), WALL_H)], 0.25)
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
    gx_, gz_ = ((0.0, 3000.0) if grid == "A" else (-1008.0, 2000.0)) if grid else (0.0, 3000.0)
    if grid:
        sh.callout(8, -3600, WALL_H + 4600, gx_, WALL_H + gz_)
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

def printed(sh, pts, w_mm, f, fill="url(#conc)", rim=0.5):
    """a printed bead drawn as a wide stroke: black rim, white body, hatch. w_mm = bead width in mm, f = model-to-paper factor,
    rim = rim line weight on paper (thinner on small-scale sheets)."""
    w = w_mm * sh.s * f
    ext = 'stroke-linecap="butt"'
    sh.mute += 1
    sh.line(pts, w + rim, "#000", extra=ext); sh.line(pts, w, "#fff", extra=ext)
    if fill != "#fff":
        sh.line(pts, w - 0.04, fill, extra=ext)
    sh.mute -= 1
    sh._rec("bead", list(pts), w_mm * f, fill == "url(#conc)", "PRINTED-BEAD")

def detail():
    ZB, ZT = 1800.0, 3400.0
    li, ll, lo = WALL_LAYERS
    CAP = OUTER_BEADS * BEAD                                                     # printed end cap of the buttress: two beads, like the outer beads of the wall
    sh = Sheet(10, 100, 420, "Detail D1: eave, roof to wall",
               "",
               [(1, False, "{} outer beads {:g}, the outside of the printed piece: exposed concrete, no insulation or cladding outside (the insulation is in the lattice zone).".format(OUTER_BEADS, BEAD)),
                (2, False, "Lattice zone {:g}: a wavy printed bead {:g} that touches the middle bead and the outer beads in turn (period about {:g}, assumed), insulation between its loops (dotted).".format(LATTICE, BEAD, WAVE_ROOF)),
                (3, False, "Middle bead {:g}: closes the rib zone on the outside. Inner and middle bead are the two structural skins of the roof, the ribs the webs between them (as in the Karamba model).".format(BEAD)),
                (4, False, "Inner bead {:g}, room side: continuous, it covers the ribs. The roof is {:g} thick square to the slope from eave to crown.".format(BEAD, T_ROOF)),
                (5, True, "Rib (cast column) {:g} wide x {:g} deep: fills the rib zone between the inner and the middle bead, inside two printed channel walls of {:g} (see the plan cut), filled with poured concrete; section cut along the rib. It rises out of the solid base in the same pour, without a joint. Between the ribs the rib zone is an empty cavity.".format(RIB_W, RIB_D, BEAD)),
                (6, True, "Rib bars R, 4 Ø16 (2 in the cut), anchored in the solid base where they cross the hooks of the wall bars A (assumed; steel fibre in the concrete could replace them)."),
                (7, True, "Stirrups Ø8 every 200 (assumed)."),
                (8, False, "Solid base of the roof: the first 300 (vertical) above the eave is full cast concrete over the whole {:g}, no cavity or lattice, poured in one go with the rib above it; wall bars A hook into it. Replaces the ring beam.".format(T_ROOF)),
                (9, False, "Buttress 400 wide, 1000 from the inner face (600 beyond the wall): printed formwork ({:g} end cap of {} beads shown) filled with cast concrete; top flush with the roof base at +2.50.".format(CAP, OUTER_BEADS)),
                (10, True, "Wall {:g} at the buttress: printed inner bead {:g} and {} outer beads {:g}, the {:g} zone between them cast and one body with the buttress (no insulation here, the cut is through the buttress; between buttresses this zone is the wavy bead + insulation). Wall bars A Ø16 run in the cast zone from the footing up into the solid base and end in a 160 hook (assumed). The roof grid is A or B (see the roof-grid sheets); the detail is cut along a rib.".format(WALL, li, OUTER_BEADS, BEAD, ll))],
               [])
    sh.plain_legend = True
    ZH = WALL_H
    # --- wall + buttress
    wall = rect(0, ZB, WALL, WALL_H)
    but = [(WALL, ZB), (WALL + BUT_L, ZB), (WALL + BUT_L, WALL_H), (WALL, WALL_H)]
    cap = [(WALL + BUT_L - CAP, ZB), (WALL + BUT_L, ZB), (WALL + BUT_L, WALL_H), (WALL + BUT_L - CAP, WALL_H)]
    for p in (wall, but):
        sh.poly(p, "#000", 0.7)
    for p in (wall, but):
        sh.poly(p, "#fff", 0.0)
        if p is not wall:
            sh.poly(p, "url(#cast)", 0.0)                                      # buttress: cast core inside printed formwork
    sh.poly(cap, "#fff", 0.0); sh.poly(cap, "url(#conc)", 0.0); layers(sh, cap, ZB); sh.poly(cap, "none", 0.45)
    layers(sh, rect(0, ZB, li, WALL_H), ZB); layers(sh, rect(li + ll, ZB, WALL, WALL_H), ZB)       # wall: printed inner bead and outer beads, 10 mm layers
    sh.poly(rect(li, ZB, li + ll, WALL_H), "#fff", 0.0); sh.poly(rect(li, ZB, li + ll, WALL_H), "url(#cast)", 0.0)   # at the buttress the lattice zone is cast, one body with the buttress: no insulation here
    sh.line([(li, ZB), (li, WALL_H)], 0.3); sh.line([(li + ll, ZB), (li + ll, WALL_H)], 0.3)
    for i in range(1, OUTER_BEADS):                                            # joints between the outer beads (wall and buttress cap)
        sh.line([(li + ll + i * BEAD, ZB), (li + ll + i * BEAD, WALL_H)], 0.2)
        sh.line([(WALL + BUT_L - i * BEAD, ZB), (WALL + BUT_L - i * BEAD, WALL_H)], 0.2)
    sh.poly(wall, "none", 0.45); sh.poly(but, "none", 0.45)
    # --- roof bands over z in [ZH, ZT]; rx edges: 0 room side | inner bead | 1 | rib zone | 2 | middle bead | 3 | lattice | 4 | outer beads | 5
    h1 = ZT - ZH
    # the roof is cut square to the slope at the top of the detail (dash-dot line)
    d = (rx(h1)[-1] - rx(0)[-1], h1); L = math.hypot(*d)
    t_ = (d[0] / L, d[1] / L); nrm = (d[1] / L, -d[0] / L)
    c = (rx(h1)[1], ZT)
    def tip(i, a=0.0):
        x0, x1 = rx(0)[i] + a, rx(h1)[i] + a
        l = ((c[0] - x0) * t_[0] + (c[1] - ZH) * t_[1]) / ((x1 - x0) * t_[0] + h1 * t_[1])
        return (x0 + l * (x1 - x0), ZH + l * h1)
    def band(i, j):
        return [(rx(0)[i], ZH), tip(i), tip(j), (rx(0)[j], ZH)]
    inner_b, mid_b, lat_z, outer_b = band(0, 1), band(2, 3), band(3, 4), band(4, 5)
    for p in (inner_b, mid_b, outer_b):
        sh.poly(p, "#fff", 0.0); layers(sh, p, ZH)                            # roof: printed beads, 10 mm layers
    sh.poly(lat_z, "#fff", 0.0); sh.poly(lat_z, "url(#dots)", 0.0)           # lattice zone: insulation between the loops of the wavy bead
    for p in (inner_b, mid_b, lat_z, outer_b):
        sh.poly(p, "none", 0.45)
    for i in range(1, OUTER_BEADS):
        sh.line([(rx(0)[4] + i * BEAD * SH, ZH), tip(4, i * BEAD * SH)], 0.2)
    # solid base: the first SOLID_H of the roof is one block of concrete over the full thickness, covering the layers drawn above
    solid = [(rx(0)[0], ZH), (rx(SOLID_H)[0], ZH + SOLID_H), (rx(SOLID_H)[-1], ZH + SOLID_H), (rx(0)[-1], ZH)]
    sh.poly(solid, "#fff", 0.0); sh.poly(solid, "url(#cast)", 0.0)      # the bottom 300 is full concrete over the whole 400, in one pour with the rib above it
    # rib: above the solid base the rib fills the rib zone, poured concrete (no joint with the base)
    core = [(rx(SOLID_H)[1], ZH + SOLID_H), tip(1), tip(2), (rx(SOLID_H)[2], ZH + SOLID_H)]
    sh.poly(core, "#fff", 0.0); sh.poly(core, "url(#cast)", 0.0)
    sh.line(core, 0.55)
    sh.line([(rx(SOLID_H)[0], ZH + SOLID_H), (rx(SOLID_H)[1], ZH + SOLID_H)], 0.55)            # the inner bead and the outer layers start (printed) on top of the block; no line across the rib core
    sh.line([(rx(SOLID_H)[2], ZH + SOLID_H), (rx(SOLID_H)[-1], ZH + SOLID_H)], 0.55)
    sh.line([(rx(SOLID_H)[0], ZH + SOLID_H), (rx(0)[0], ZH), (rx(0)[-1], ZH), (rx(SOLID_H)[-1], ZH + SOLID_H)], 0.55)
    # the roof continues: dash-dot line at the top of the detail, square to the slope
    sh.line([(c[0] - nrm[0] * 380, c[1] - nrm[1] * 380), (c[0] + nrm[0] * 560, c[1] + nrm[1] * 560)], 0.5, "#000", dash="7 1.5 1.2 1.5")
    # ---- rebar: every bar is drawn at its true diameter (1:10, so Ø16 = 1.6 mm on the sheet); black = steel
    e1 = lambda h: rx(h)[1]                                             # inner edge of the rib core (outside of the inner bead)
    bar = lambda pts, d: sh.line(pts, d / sh.scale, BLUE, tw=d)
    sh.layer = "REBAR"
    # A  wall bar Ø16 in the cast zone of the wall: footing up into the solid base, 90 deg hook (10d) in the base core
    A_X, HOOK_Z = li + 50.0, WALL_H + SOLID_H - 110
    bar([(A_X, ZB), (A_X, HOOK_Z), (A_X + 160, HOOK_Z)], 16)
    # R  rib bars Ø16: two of the four are in the cut, 45 from the inner and the outer face of the rib core; anchored in the solid base
    for dd in (45, RIB_D - 45):
        bar([(e1(40) + dd * SH, ZH + 40), (e1(h1) + dd * SH, ZH + h1)], 16)
    # stirrups Ø8 every 200 above the base
    for h in range(500, int(h1), 200):
        bar([(e1(h) + 30 * SH, ZH + h), (rx(h)[2] - 30 * SH, ZH + h)], 8)
    sh.layer = None
    # ---- dimensions
    sh.dim_v([WALL_H, WALL_H + SOLID_H], -300, ext=-30, labels=["{:g}".format(SOLID_H)])
    ob = "{} x {:g}".format(OUTER_BEADS, BEAD) if OUTER_BEADS > 1 else "{:g}".format(BEAD)     # the outer beads as one dimension: 30 each is too tight to letter
    sh.dim_h([0, li, li + ll, WALL], ZB - 130, ext=ZB, labels=["{:g}".format(li), "{:g}".format(ll), ob])
    sh.dim_h([WALL, WALL + BUT_L], ZB - 130, ext=ZB, labels=["{:g}".format(BUT_L)])
    sh.dim_h([0, BUT_TOTAL], ZB - 330, ext=ZB - 130, labels=["{:g} from the inner face".format(BUT_TOTAL)])
    # dimension chain along the dash-dot cut, square to the slope: true thickness of every layer, inside to outside
    pts = [tip(i) for i in range(6)]      # inner bead | rib zone | middle bead | lattice | outer beads
    sh.dim_aligned(pts, t_, 420.0)
    sh.text(-860, WALL_H + 30, "+2.50 eave", 2.6, "start", weight="bold")
    sh.line([(-860, WALL_H), (-100, WALL_H)], 0.2, dash="4 1")
    # ---- callouts
    mid = lambda h, i, j: ((rx(h)[i] + rx(h)[j]) / 2, ZH + h)
    sh.callout(1, 880, ZH + 760, *mid(500, 4, 5))
    sh.callout(2, 880, ZH + 380, *mid(450, 3, 4))
    sh.callout(3, 880, ZH + 1120, *mid(900, 2, 3))
    sh.callout(4, -620, ZH + 560, *mid(560, 0, 1))
    sh.callout(5, -620, ZH + 760, e1(760) + RIB_D / 2 * SH, ZH + 760)
    sh.callout(6, -470, WALL_H - 140, e1(150) + 45 * SH, ZH + 150)
    sh.callout(7, -620, ZH + 160, e1(500) + RIB_D / 2 * SH, ZH + 500)
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
    import make_set
    make_set.main()          # the whole drawing set: details/set/*.pdf, the merged set PDF and details/set/cad/*.dxf
