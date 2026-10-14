"""Plan slices through the pyramid roof, one sheet per roof-grid option. The cut planes are horizontal, looking down: the shell is cut as a square ring
(printed inner layers, air zone with the cast ribs cut, outer layer, insulation, cladding). One large slice near the eave (1:50) and two small ones higher up (1:100)
show how the grid thins out towards the crown.
Run: python details/roof_slice.py [out_dir]  ->  roof-slice-A.svg/.pdf, roof-slice-B.svg/.pdf"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pyramid_drawings as g
import roof_grid as rg
from pyramid_drawings import Sheet

MAIN_H = 3500.0                  # large slice, above the eave: +6.00 from the ground floor, all ribs present, just below the middle horizontal rib of grid A (+6.13)
SMALL = [(1500.0, 250.0, 78.0), (5000.0, 250.0, 205.0)]    # (height above the eave, paper x, paper y of the centre) of the two small slices (+4.00, +7.50)
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

def draw_slice(sh, opt, h, f, cx, cz, full, label=True):
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
    if label: sh.text(*T((0, r_clad + 300 / f * 1.0)), "cut at {} (1:{:g})".format(lab, 50 / f), 3.0 if full else 2.6, weight="bold")
    return dict(hin=hin, o=o, ribs=ribs, hips=hips, r=r, core=(core_t0, core_t1), tm=tm, r_clad=r_clad, r_skin=r_skin, r_air=r_air, r_l2=r_l2, r_l1=r_l1, r_ins=r_ins, T=T)

def sheet(opt):
    """roof plan cut at the crown (+8.50), looking down: the top ring is cut, and below it the whole roof is seen with its ribs running
    from the base ring at the eave up to the top ring (drawn as if the outer layer, insulation and cladding were transparent)"""
    h_cut = g.RISE - 1.0
    title = "Roof plan, cut at +8.50 · grid {}".format(opt)
    sub = "horizontal cut through the top ring, looking down on the ribs"
    hr = ", ".join("+{:.2f}".format((g.WALL_H + y) / 1000) for y in rg.RING_H)
    legend = [(1, False, "Cut at +8.50 (crown, 6.00 above the roof base) through the top ring: printed layers, cast ring (crossed hatch), insulation and outer layer; crown opening 1000."),
              (2, True, ("Ribs of grid A, seen from above: columns from the base ring at the eave to where they stop (every other one at +{:.2f}, the rest at +{:.2f}); the four hip ribs go on to the top ring.".format((g.WALL_H + rg.H1) / 1000, (g.WALL_H + rg.H2) / 1000)) if opt == "A" else
                         "Ribs of grid B, seen from above: two families of diagonals from the base ring at the eave to the hips and the top ring."),
              (3, False, "Base ring: the 300 solid base at the eave (+2.50 to +2.80)."),
              (4, True, ("Horizontal ribs of grid A at {}.".format(hr)) if opt == "A" else "No horizontal ribs between the base ring and the top ring in grid B."),
              (5, False, "Hips: four ribs from the corners of the eave to the corners of the top ring."),
              (6, False, "Roof edge at the eave (outside of the 30 outer layer). Very faint squares = printed layer joints (real layers 10, drawn every 200 in height)."),
              (7, False, "Buttresses below the roof: their ends show beyond the roof edge; the wall under the roof is dashed.")]
    notes = ["The ribs lie inside the shell, between the printed inner layers and the outer layer; here they are drawn as if the outer layer, insulation and cladding were transparent, so their whole run from the eave to the crown can be seen.",
             "Ribs are drawn on the mid-surface of the shell, 160 wide, with the same geometry as the roof-grid sheets and sections."]
    sh = Sheet(50, 150, 148.5, title, sub, legend, notes)
    sh.plain_legend = False
    s = sh.s
    cx, cz = (155.0 - 150.0) / s, 0.0
    T = lambda p: (cx + p[0], cz + p[1])
    TS = lambda ps: [T(p) for p in ps]
    HALF, WALL, BUT_L, BUT_W = g.HALF, g.WALL, g.BUT_L, g.BUT_W
    b = HALF + WALL
    edge = HALF + g.rx(0)[3] + (g.INS + g.CLAD) * SH                     # outside of the cladding at the eave
    # buttresses (visible beyond the roof edge) and the wall under the roof (dashed)
    for q in (sq(HALF), sq(b)):
        sh.line(TS(q + [q[0]]), 0.15, "#777", dash="3 1.5")
    for v in g.but_pos():
        for (xa, ya), (xb, yb) in (((v - BUT_W / 2, -b - BUT_L), (v + BUT_W / 2, -b)), ((v - BUT_W / 2, b), (v + BUT_W / 2, b + BUT_L)),
                                   ((-b - BUT_L, v - BUT_W / 2), (-b, v + BUT_W / 2)), ((b, v - BUT_W / 2), (b + BUT_L, v + BUT_W / 2))):
            q = [(xa, ya), (xb, ya), (xb, yb), (xa, yb)]
            sh.poly(TS(q), "#fff", 0.0); sh.poly(TS(q), "url(#conc)", 0.0); sh.poly(TS(q), "none", 0.35)
    # roof seen from above: white, very faint layer joints (contours every 100 in height)
    sh.poly(TS(sq(edge)), "#fff", 0.45)
    hh = 200.0
    while hh < g.RISE:
        rr = rg.w(hh) + (edge - rg.w(0))
        sh.poly(TS(sq(rr)), "none", 0.025, "#d8d8d8")
        hh += 200.0
    face = {"S": lambda x, wv: (x, -wv), "N": lambda x, wv: (-x, wv), "E": lambda x, wv: (wv, x), "W": lambda x, wv: (-wv, -x)}
    segs, _ = rg.segments(opt)
    # base ring (solid 300) and horizontal / top rings as square bands
    def band(h0, h1):
        d = "M" + " L".join("{:.2f},{:.2f}".format(*sh.P(*q)) for q in TS(sq(rg.w(h0)))) + "Z M" + " L".join("{:.2f},{:.2f}".format(*sh.P(*q)) for q in TS(sq(rg.w(h1)))) + "Z"
        sh.o.append('<path d="{0}" fill="#fff" fill-rule="evenodd"/><path d="{0}" fill="url(#cast)" fill-rule="evenodd"/>'.format(d))
        sh.poly(TS(sq(rg.w(h0))), "none", 0.3); sh.poly(TS(sq(rg.w(h1))), "none", 0.3)
    band(0.0, g.SOLID_H)
    for kind, pts in segs:
        if kind == "ring":
            y = pts[0][1]
            band(y - rg.TOP_RING / 2, min(y + rg.TOP_RING / 2, g.RISE))
    # ribs: 160 wide strips on the mid-surface, projected to plan
    for kind, pts in segs:
        if kind not in ("col", "diag"): continue
        q = rg.quad(pts[0], pts[1], rg.RIB_W, kind)
        for f in face.values():
            pp = TS([f(x, rg.w(min(max(hv, 0.0), g.RISE))) for x, hv in q])
            sh.poly(pp, "#fff", 0.0); sh.poly(pp, "url(#cast)", 0.0); sh.poly(pp, "none", 0.3)
    # hips (visible edges of the roof)
    for sx in (-1, 1):
        for sy in (-1, 1):
            sh.line(TS([(sx * edge, sy * edge), (sx * rg.w(g.RISE), sy * rg.w(g.RISE))]), 0.35)
    # the cut at +8.50: the top ring, drawn over everything
    m = draw_slice(sh, opt, h_cut, 1.0, cx, cz, False, label=False)
    # dimensions and callouts
    sh.dim_h([T((-edge, 0))[0], T((edge, 0))[0]], T((0, -6450))[1], ext=T((0, -edge - 60))[1], labels=["{:.0f} roof at the eave".format(2 * edge)])
    xcall = T((7000, 0))[0]
    def co(n, zc, tgt): sh.callout(n, xcall, T((0, zc))[1], *T(tgt))
    co(1, 2600, (m["r_l2"] + 20, 0.0))
    rib_pt = [p for k, p in segs if k in ("col", "diag")][len([1 for k, p in segs if k in ("col", "diag")]) // 3]
    mid = ((rib_pt[0][0] + rib_pt[1][0]) / 2, (rib_pt[0][1] + rib_pt[1][1]) / 2)
    co(2, 1500, face["E"](mid[0], rg.w(mid[1])))
    co(3, -800, (rg.w(g.SOLID_H / 2), -2000.0))
    if opt == "A": co(4, 400, (rg.w(rg.RING_H[0]), 1200.0))
    co(5, 4300, (0.5 * (edge + rg.w(g.RISE)), 0.5 * (edge + rg.w(g.RISE))))
    co(6, -2000, (edge - 40, -3000.0))
    co(7, -4300, (b + BUT_L - 100, g.but_pos()[1]))
    return sh

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
    for opt in "AB":
        g.export(sheet(opt), os.path.join(out, "roof-slice-" + opt))
