"""Plan slices through the pyramid roof, one sheet per roof-grid option. The cut planes are horizontal, looking down: the shell is cut as a square ring
(printed inner layers, air zone with the cast ribs cut, outer layer, insulation, cladding). One large slice near the eave (1:50) and two small ones higher up (1:100)
show how the grid thins out towards the crown.
Run: python details/make_set.py"""
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
        sh._rec("ring", TS(sq(outer)), TS(sq(inner)), fill, hatch)
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

CUT_H = 3500.0       # cut plane above the eave: +6.00 from the ground floor, just below the middle horizontal rib of grid A (+6.13)

def clip_seg(p, q, hmax):
    """part of the elevation segment p-q (x, h) that lies at or below h = hmax, or None"""
    if p[1] > q[1]: p, q = q, p
    if p[1] >= hmax: return None
    if q[1] <= hmax: return p, q
    t = (hmax - p[1]) / (q[1] - p[1])
    return p, (p[0] + t * (q[0] - p[0]), hmax)

def sheet(opt, h_cut=CUT_H):
    """roof plan cut at +6.00, looking down: the shell is cut as a ring (ribs cut in it), and below the cut the roof is seen with its ribs
    running from the base ring at the eave up to the cut (drawn as if the outer layer, insulation and cladding were transparent).
    The roof above the cut is removed and shown dashed (hips and the 1000 crown opening)."""
    lv = (g.WALL_H + h_cut) / 1000
    title = "Roof plan, cut at +{:.2f} · grid {}".format(lv, opt)
    sub = "horizontal cut through the roof, looking down on the ribs"
    hr = ", ".join("+{:.2f}".format((g.WALL_H + y) / 1000) for y in rg.RING_H)
    legend = [(1, False, "Cut at +{:.2f} ({:.0f} above the eave, just below the horizontal rib at +6.13): printed layers, air zone, cast ribs cut (crossed hatch), outer layer, insulation 100 and outer layer 30.".format(lv, h_cut)),
              (2, True, ("Ribs of grid A seen below the cut: all 11 columns per face run from the base ring at the eave up to the cut (every other one stops at +6.13, just above it)." if opt == "A" else
                         "Ribs of grid B seen below the cut: the two families of diagonals from the base ring at the eave up to the cut and the hips.")),
              (3, False, "Base ring: the 300 solid base at the eave (+2.50 to +2.80)."),
              (4, True, ("Horizontal rib of grid A at +4.31 (the next ones, at +6.13 and +7.77, are above the cut)." if opt == "A" else "No horizontal ribs in grid B between the base ring and the top ring.")),
              (5, False, "Hips: ribs from the corners of the eave up to the cut; dashed above it, up to the crown opening."),
              (6, False, "Roof edge at the eave (outside of the 30 outer layer). Very faint squares = printed layer joints (real layers 10, drawn every 200 in height)."),
              (7, False, "Above the cut (removed, dashed): hips and the crown opening at +8.50, {:.0f} clear inside ({:.0f} at the middle of the shell, {:.0f} outside the outer layer).".format(g.OPEN, 2 * rg.TOPB, 2 * (g.HALF + g.rx(g.RISE)[3] + (g.INS + g.CLAD) * SH))),
              (8, False, "Buttresses below the roof: their ends show beyond the roof edge; the wall under the roof is dashed.")]
    notes = ["Matches the roof-grid elevations: same rib geometry, same levels ({} for the horizontal ribs of grid A).".format(hr),
             "The ribs lie inside the shell, between the printed inner layers and the outer layer; here they are drawn as if the outer layer, insulation and cladding were transparent."]
    sh = Sheet(50, 150, 148.5, title, sub, legend, notes)
    sh.plain_legend = False
    s = sh.s
    cx, cz = (155.0 - 150.0) / s, 0.0
    T = lambda p: (cx + p[0], cz + p[1])
    TS = lambda ps: [T(p) for p in ps]
    HALF, WALL, BUT_L, BUT_W = g.HALF, g.WALL, g.BUT_L, g.BUT_W
    b = HALF + WALL
    out = lambda hh: g.HALF + g.rx(hh)[3] + (g.INS + g.CLAD) * SH       # outside of the cladding at height hh
    edge = out(0.0)
    for q in (sq(HALF), sq(b)):
        sh.line(TS(q + [q[0]]), 0.15, "#777", dash="3 1.5")
    for v in g.but_pos():
        for (xa, ya), (xb, yb) in (((v - BUT_W / 2, -b - BUT_L), (v + BUT_W / 2, -b)), ((v - BUT_W / 2, b), (v + BUT_W / 2, b + BUT_L)),
                                   ((-b - BUT_L, v - BUT_W / 2), (-b, v + BUT_W / 2)), ((b, v - BUT_W / 2), (b + BUT_L, v + BUT_W / 2))):
            q = [(xa, ya), (xb, ya), (xb, yb), (xa, yb)]
            sh.poly(TS(q), "#fff", 0.0); sh.poly(TS(q), "url(#conc)", 0.0); sh.poly(TS(q), "none", 0.35)
    sh.poly(TS(sq(edge)), "#fff", 0.45)
    hh = 200.0
    while hh < h_cut:
        sh.poly(TS(sq(out(hh))), "none", 0.025, "#d8d8d8")
        hh += 200.0
    face = {"S": lambda x, wv: (x, -wv), "N": lambda x, wv: (-x, wv), "E": lambda x, wv: (wv, x), "W": lambda x, wv: (-wv, -x)}
    segs, _ = rg.segments(opt)
    def band(h0, h1):
        d = "M" + " L".join("{:.2f},{:.2f}".format(*sh.P(*q)) for q in TS(sq(rg.w(h0)))) + "Z M" + " L".join("{:.2f},{:.2f}".format(*sh.P(*q)) for q in TS(sq(rg.w(h1)))) + "Z"
        sh.o.append('<path d="{0}" fill="#fff" fill-rule="evenodd"/><path d="{0}" fill="url(#cast)" fill-rule="evenodd"/>'.format(d))
        sh._rec("ring", TS(sq(rg.w(h0))), TS(sq(rg.w(h1))), "#fff", "url(#cast)")
        sh.poly(TS(sq(rg.w(h0))), "none", 0.3); sh.poly(TS(sq(rg.w(h1))), "none", 0.3)
    band(0.0, g.SOLID_H)
    for kind, pts in segs:
        if kind == "ring" and pts[0][1] + rg.TOP_RING / 2 < h_cut:
            y = pts[0][1]
            band(y - rg.TOP_RING / 2, y + rg.TOP_RING / 2)
    for kind, pts in segs:
        if kind not in ("col", "diag"): continue
        c = clip_seg(pts[0], pts[1], h_cut)
        if c is None: continue
        q = rg.quad(c[0], c[1], rg.RIB_W, kind)
        for f in face.values():
            pp = TS([f(x, rg.w(min(max(hv, 0.0), h_cut))) for x, hv in q])
            sh.poly(pp, "#fff", 0.0); sh.poly(pp, "url(#cast)", 0.0); sh.poly(pp, "none", 0.3)
    for sx in (-1, 1):
        for sy in (-1, 1):
            sh.line(TS([(sx * edge, sy * edge), (sx * out(h_cut), sy * out(h_cut))]), 0.35)
    m = draw_slice(sh, opt, h_cut, 1.0, cx, cz, True, label=False)
    r_in_c, r_out_c = g.OPEN / 2, out(g.RISE)
    for sx in (-1, 1):
        for sy in (-1, 1):
            sh.line(TS([(sx * m["hin"], sy * m["hin"]), (sx * r_in_c, sy * r_in_c)]), 0.2, "#555", dash="3 1.5")
    sh.line(TS(sq(r_in_c) + [sq(r_in_c)[0]]), 0.25, "#555", dash="3 1.5")
    sh.line(TS(sq(r_out_c) + [sq(r_out_c)[0]]), 0.15, "#555", dash="3 1.5")
    sh.text(*T((0, 120)), "crown opening above", 2.4, italic=True, color="#555"); sh.text(*T((0, -330)), "{:.0f} x {:.0f} clear, +8.50".format(g.OPEN, g.OPEN), 2.4, italic=True, color="#555")
    sh.dim_h([T((-edge, 0))[0], T((edge, 0))[0]], T((0, -6450))[1], ext=T((0, -edge - 60))[1], labels=["{:.0f} roof at the eave".format(2 * edge)])
    sh.dim_h([T((-m["hin"], 0))[0], T((m["hin"], 0))[0]], T((0, m["r_clad"] + 350))[1], ext=T((0, m["hin"] + 40))[1], labels=["{:.0f} clear at the cut".format(2 * m["hin"])])
    sh.dim_h([T((-r_in_c, 0))[0], T((r_in_c, 0))[0]], T((0, -1300))[1], ext=T((0, -r_in_c - 40))[1], labels=["{:.0f}".format(g.OPEN)])
    xcall = T((7000, 0))[0]
    def co(n, zc, tgt): sh.callout(n, xcall, T((0, zc))[1], *T(tgt))
    ot = m["o"]
    co(1, 3300, (m["hin"] + ot["l1"] / 2, 0.6 * m["hin"]))
    rib_pt = [p for k, p in segs if k in ("col", "diag")][2]
    c = clip_seg(rib_pt[0], rib_pt[1], h_cut)
    mid = ((c[0][0] + c[1][0]) / 2, (c[0][1] + c[1][1]) / 2)
    co(2, 1900, face["E"](mid[0], rg.w(mid[1])))
    co(3, -700, (rg.w(g.SOLID_H / 2), -2500.0))
    if opt == "A": co(4, 500, (rg.w(rg.RING_H[0]), 900.0))
    co(5, 4600, (0.5 * (edge + out(h_cut)), 0.5 * (edge + out(h_cut))))
    co(6, -2000, (edge - 40, -3200.0))
    co(7, -3300, (r_in_c, -0.3 * r_in_c))
    co(8, -4600, (b + BUT_L - 100, g.but_pos()[1]))
    return sh

if __name__ == "__main__":
    import make_set
    make_set.main()          # the whole drawing set: details/set/*.pdf, the merged set PDF and details/set/cad/*.dxf
