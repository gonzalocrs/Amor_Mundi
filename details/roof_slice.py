"""Plan slices through the pyramid roof, one sheet per roof-grid option. The cut planes are horizontal, looking down: the shell is cut as a square ring
(printed inner layers, air zone with the cast ribs cut, outer layer, insulation, cladding). One large slice near the eave (1:50) and two small ones higher up (1:100)
show how the grid thins out towards the crown.
Run: python details/roof_slice.py [out_dir]  ->  roof-slice-A.svg/.pdf, roof-slice-B.svg/.pdf"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pyramid_drawings as g
import roof_grid as rg
from pyramid_drawings import Sheet

MAIN_H = 5999.0                  # large slice, above the eave: +8.50 from the ground floor, at the crown, through the top ring
SMALL = [(1500.0, 250.0, 78.0), (4500.0, 250.0, 205.0)]    # (height above the eave, paper x, paper y of the centre) of the two small slices (+4.00, +7.00)
SH = g.SH
ALPHA = math.radians(g.SLOPE)

def sq(h): return [(-h, -h), (h, -h), (h, h), (-h, h)]

def offsets(h):
    """horizontal distances from the inner face of the shell at height h to: layer 1, layer 2, air zone, outer layer, insulation, cladding"""
    r = g.rx(h)
    x0 = r[0]
    return {"l1": 80 * SH, "l2": r[1] - x0, "air": r[2] - x0, "skin": r[3] - x0, "ins": r[3] - x0 + g.INS * SH, "clad": r[3] - x0 + (g.INS + g.CLAD) * SH}

def cut_ribs(opt, h):
    """ribs cut by the plane at height h: list of dict(x centre at mid-depth along the face, width along the wall, shear per unit depth); hips and horizontal ring flags"""
    segs, _ = rg.segments(opt)
    out, hips, rings = [], False, False
    for kind, pts in segs:
        if kind == "ring":
            if abs(h - pts[0][1]) <= rg.TOP_RING / 2: rings = True
            continue
        if kind == "solid": continue
        (x0, h0), (x1, h1) = pts
        if not (min(h0, h1) - 1e-6 <= h <= max(h0, h1) + 1e-6): continue
        x = x0 + (x1 - x0) * (h - h0) / (h1 - h0)
        dx, dh = x1 - x0, h1 - h0
        ang = math.atan2(rg.VST * abs(dh), abs(dx))                   # rib angle in the face plane against the horizontal
        wcut = rg.RIB_W / math.sin(ang)
        skew = -(dx / (rg.VST * dh)) * math.cos(ALPHA)                # the face is inclined: the cut shears along the wall with depth
        if abs(abs(x) - rg.w(h)) < 5:                                   # hip ribs: corner blocks
            hips = True
            continue
        out.append(dict(x=x, w=wcut, skew=skew))
    return out, hips, rings

def draw_slice(sh, opt, h, f, cx, cz, full):
    T = lambda p: (cx + f * p[0], cz + f * p[1])
    TS = lambda ps: [T(p) for p in ps]
    def ring(outer, inner, fill, hatch=None):
        d = "M" + " L".join("{:.2f},{:.2f}".format(*sh.P(*q)) for q in TS(sq(outer))) + "Z M" + " L".join("{:.2f},{:.2f}".format(*sh.P(*q)) for q in TS(sq(inner))) + "Z"
        sh.o.append('<path d="{}" fill="{}" fill-rule="evenodd"/>'.format(d, fill))
        if hatch: sh.o.append('<path d="{}" fill="{}" fill-rule="evenodd"/>'.format(d, hatch))
    def square(r_, lw): sh.poly(TS(sq(r_)), "none", lw)
    def to_plan(face, u, t, hin):
        a = hin + t
        return {"S": (u, -a), "E": (a, u), "N": (-u, a), "W": (-a, -u)}[face]
    o = offsets(h)
    r = g.rx(h)
    hin = g.HALF + r[0]
    r_l1, r_l2, r_air, r_skin = hin + o["l1"], hin + o["l2"], hin + (r[2] - r[0]), hin + o["skin"]
    r_ins, r_clad = hin + o["ins"], hin + o["clad"]
    ring(r_clad, r_ins, "#555")
    ring(r_ins, r_skin, "#fff", "url(#dots)")
    ring(r_skin, r_air, "#fff", "url(#conc)")                      # outer layer
    ring(r_air, r_l2, "#fff", "url(#dots)")                        # air zone (insulation)
    ring(r_l2, r_l1, "#fff", "url(#conc)")                         # layer 2
    ring(r_l1, hin, "#fff", "url(#conc)")                          # layer 1
    for r_, lw in ((r_clad, 0.3), (r_ins, g.INS_LW), (r_skin, 0.4), (r_air, 0.3), (r_l2, 0.25), (r_l1, 0.25), (hin, 0.6)):
        square(r_, lw)
    ribs, hips, ring_cut = cut_ribs(opt, h)
    core_t0, core_t1 = o["l1"], r[2] - r[0]                         # rib core = layer 2 + air zone
    tm = (core_t0 + core_t1) / 2
    for face in "SENW":
        for rb in ribs:
            uc = lambda t: rb["x"] + rb["skew"] * (t - tm)
            loc = [(uc(core_t0) - rb["w"] / 2, core_t0), (uc(core_t1) - rb["w"] / 2, core_t1), (uc(core_t1) + rb["w"] / 2, core_t1), (uc(core_t0) + rb["w"] / 2, core_t0)]
            pp = TS([to_plan(face, u, t, hin) for u, t in loc])
            sh.poly(pp, "#fff", 0.0); sh.poly(pp, "url(#cast)", 0.0); sh.poly(pp, "none", 0.45 if full else 0.3)
            if full:
                for dd in (60, 180):                                # the 4 bars Ø16 (2 x 2 in plan)
                    for du in (-28, 28):
                        px, py = T(to_plan(face, uc(core_t0 + dd * SH) + du, core_t0 + dd * SH, hin))
                        sh.dot(px, py, 8 * f)
    if ring_cut:
        ring(r_air, r_l2, "#fff", "url(#cast)")
    if hips:
        for sx in (-1, 1):
            for sy in (-1, 1):
                a0, a1 = hin + core_t0, hin + core_t1
                pp = TS([(sx * a0, sy * a0), (sx * a1, sy * a0), (sx * a1, sy * a1), (sx * a0, sy * a1)])
                sh.poly(pp, "#fff", 0.0); sh.poly(pp, "url(#cast)", 0.0); sh.poly(pp, "none", 0.45 if full else 0.3)
    lab = "+{:.2f}".format((g.WALL_H + h) / 1000)
    sh.text(*T((0, r_clad + 300 / f * 1.0)), "cut at {} (1:{:g})".format(lab, 50 / f), 3.0 if full else 2.6, weight="bold")
    return dict(hin=hin, o=o, ribs=ribs, hips=hips, r=r, core=(core_t0, core_t1), tm=tm, r_clad=r_clad, r_skin=r_skin, r_air=r_air, r_l2=r_l2, r_l1=r_l1, r_ins=r_ins, T=T)

def sheet(opt):
    # main slice centre, in model coordinates
    cx0, cz0 = (110.0 - 150.0) / sh_s_guess(), -(150.0 - 148.5) / sh_s_guess()
    h = MAIN_H
    title = "Roof plan slices · grid {}".format(opt)
    sub = "horizontal cuts through the roof, looking down"
    o = offsets(h)
    legend = [(1, False, "Inner layer 1, 80 printed, room side, then layer 2 (printed, thinner towards the crown)."),
              (2, False, "Air zone, open between the ribs, for insulation (dotted)."),
              (3, True, "Cast concrete cut by the plane (crossed hatch): the ribs, {}, each 160 wide across the rib and 240 deep (the cut is longer than 160 and sheared where the rib is inclined in the face; 4 Ø16 and stirrups as in the rib section), and, at the crown, the whole top ring.".format("columns of grid A" if opt == "A" else "the two diagonal families of grid B")),
              (4, True, "Corner blocks: the four hip ribs, cut across the corners (cast)."),
              (5, False, "Outer layer 80, printed."),
              (6, False, "Insulation 100 (very thin line), then the outer layer 30 (dark).")]
    notes = ["Heights are levels from the ground floor. Large slice at +{:.2f} (at the crown, {} above the eave), drawn at 1:20 so the top ring is readable, through the top ring; small slices at +4.00 and +7.00, 1:100 (the scale bar is for 1:50).".format((g.WALL_H + h) / 1000, int(h)),
             ("Option A: all columns at +4.00; at +7.00 every other column has stopped (they stop once the spacing is 500); at the crown only the four hip ribs and the top ring are left. The middle horizontal ribs are at +4.31, +6.13 and +7.77." if opt == "A" else
              "Option B: the same two diagonal families at every height, clipped by the hips; at the crown only the hips and the top ring are cut (the diagonals end on the ring)."),
             "Layer 2 thins towards the crown (the leaf is 160 at the base, 80 at the crown). Ribs use the same geometry as the roof-grid sheets; bars and stirrups are assumed."]
    sh = Sheet(50, 150, 148.5, title, sub, legend, notes)
    sh.plain_legend = False
    s = sh.s
    F_MAIN = 2.5                                                       # the large slice is drawn at 1:20 so the crown ring is readable
    cx0, cz0 = (105.0 - 150.0) / s, (148.5 - 150.0) / s
    m = draw_slice(sh, opt, h, F_MAIN, cx0, cz0, True)
    T = m["T"]; hin = m["hin"]; r = m["r"]
    zb = -m["r_clad"] - 250
    sh.dim_h([T((-m["r_clad"], 0))[0], T((-hin, 0))[0], T((hin, 0))[0], T((m["r_clad"], 0))[0]], T((0, zb))[1], ext=T((0, -m["r_clad"] - 40))[1],
             labels=["{:.0f}".format(m["o"]["clad"]), "{:.0f} clear at the cut".format(2 * hin), "{:.0f}".format(m["o"]["clad"])])
    sh.dim_h([T((-m["r_clad"], 0))[0], T((m["r_clad"], 0))[0]], T((0, zb - 330))[1], ext=T((0, zb))[1], labels=["{:.0f} overall at the cut".format(2 * m["r_clad"])])
    xcall = T((m["r_clad"] + 700, 0))[0]
    def co(n, frac, tgt):
        sh.callout(n, xcall, T((0, frac * m["r_clad"]))[1], tgt[0], tgt[1])
    ot = m["o"]
    co(1, 0.95, T((hin + ot["l1"] / 2, 0.55 * hin)))
    co(2, 0.6, T((hin + (m["r_l2"] - hin + m["r_air"] - hin) / 2, -0.2 * hin)))
    co(3 if not m["ribs"] else 3, 0.25, T((hin + m["tm"], (m["ribs"][0]["x"] if m["ribs"] else 0.0)))) if False else None
    co(4, 0.0, T((hin + (m["core"][0] + m["core"][1]) / 2, -(hin + (m["core"][0] + m["core"][1]) / 2)))) if m["hips"] else None
    co(3, 0.3, T((hin + m["tm"], 0.0)))                         # the cast top ring (or a rib, lower down)
    co(5, -0.4, T((hin + (ot["skin"] + (m["r_air"] - hin)) / 2, -0.5 * hin)))
    co(6, -0.75, T((hin + (ot["ins"] + ot["skin"]) / 2, -0.8 * hin)))
    for hh, px, py in SMALL:
        draw_slice(sh, opt, hh, 0.5, (px - 150.0) / s, (148.5 - py) / s, False)
    return sh

def sh_s_guess(): return 1.0 / 50

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
    for opt in "AB":
        g.export(sheet(opt), os.path.join(out, "roof-slice-" + opt))
