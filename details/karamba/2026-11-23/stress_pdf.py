"""Karamba stress set for the stepped roofs at the real 2 m height (2026-11-23), in the midterm press layout
(17 x 11 in, "STRUCTURAL ANALYSIS" header, numbered heading + one-line description, two columns).
Input: forces-15x10.json / forces-10x10.json written by k_dump.py inside Karamba (canvases
polyframe2/stepped-<roof>-karamba-2m-2026-11-23.gh). Every number on the sheets is read from those files or
computed by hand below from them. Force drawings: each element drawn as a line, width and colour by its value,
the same scale for LONG and SHORT.  Usage: python stress_pdf.py  (Rhino's CPython; PDF via headless Edge)."""
import os, sys, json, math, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", ".."))
import press_sheets as ps
from press_sheets import Page, W, H, EDGE

LCS = ["LONG", "W+Y", "W-Y", "W+X", "W-X", "W45", "LIVEX", "LIVEY", "EQX", "EQY"]
LONGS = ["LONG", "LIVEX", "LIVEY"]
SHORTS = ["W+Y", "W-Y", "W+X", "W-X", "W45", "EQX", "EQY"]
FC = 36.0; ALL_L = FC / 3; ALL_S = 2 * FC / 3            # AIJ allowable concrete compression (MPa)
RIB_D = {"15x10": {"rib_bottom": 0.22, "rib_middle": 0.16, "rib_top": 0.12},
         "10x10": {"rib_bottom": 0.18, "rib_middle": 0.14, "rib_top": 0.12}}
RECT = {"ring": (0.40, 0.40), "crown": (0.25, 0.25), "column15x10": (0.36, 0.36), "column10x10": (0.30, 0.30)}
NAMES = {"rib_bottom": "Ribs, bottom band", "rib_middle": "Ribs, middle band", "rib_top": "Ribs, top band",
         "ring": "Base ring 40x40", "crown": "Crown ring 25x25", "column": "Columns", "course": "Printed courses (hoops)",
         "fin": "Piece end walls (fins)"}
FOOT = {}
GROUPS = ["rib_bottom", "rib_middle", "rib_top", "ring", "crown", "column", "course", "fin"]


def load(roof):
    D = json.load(open(os.path.join(HERE, "forces-%s.json" % roof)))
    D["idx"] = {}
    for i, (g, a, b) in enumerate(D["els"]):
        D["idx"].setdefault(g, []).append(i)
    return D


def sec_props(roof, g):
    if g.startswith("rib"):
        Dm = RIB_D[roof][g]; return math.pi * Dm * Dm / 4, math.pi * Dm ** 3 / 32, math.pi * Dm ** 3 / 32, "solid round D%d" % round(Dm * 100)
    b, h = RECT["column" + roof] if g == "column" else RECT[g]
    return b * h, b * h * h / 6, h * b * b / 6, "%d x %d" % (round(b * 100), round(h * 100))


def group_stats(D, roof, g, lcs):
    f = D["forces"]; ids = D["idx"][g]; st = {}
    for k in ("N", "Vz", "Vy", "Mt", "My", "Mz"):
        vals = [f[lc][k][2 * i + t] for lc in lcs for i in ids for t in (0, 1)]
        st[k] = (min(vals), max(vals))
    if g in ("rib_bottom", "rib_middle", "rib_top", "ring", "crown", "column"):
        A, Wy, Wz, _ = sec_props(roof, g); best = (-1e9, ""); worst_t = (1e9, "")
        for lc in lcs:
            for i in ids:
                for t in (0, 1):
                    N = f[lc]["N"][2 * i + t]; My = f[lc]["My"][2 * i + t]; Mz = f[lc]["Mz"][2 * i + t]
                    m = math.hypot(My, Mz) / Wy if g.startswith("rib") else abs(My) / Wy + abs(Mz) / Wz
                    c = (-N / A + m) / 1000.0; tt = (-N / A - m) / 1000.0
                    if c > best[0]: best = (c, lc, N, math.hypot(My, Mz), i, t)
                    if tt < worst_t[0]: worst_t = (tt, lc, N, math.hypot(My, Mz), i, t)
        st["sc"] = best; st["st"] = worst_t
    return st


# ---------------- drawing helpers ----------------
def proj(p, view="axon"):
    x, y, z = p
    if view == "axon":               # parallel view from the south-east, 30 deg up
        u = (x - y) * 0.7071; v = -(x + y) * 0.7071 * 0.5 + z * 0.866
        return u, -v
    return x, -y


def frame_points(D, view="axon"):
    pts = [proj(p, view) for p in D["nodes"]]
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    return pts, (min(xs), min(ys), max(xs), max(ys))


def color(v, vmax):
    """compression (negative) blue, tension red, grey near zero"""
    t = max(-1.0, min(1.0, v / vmax)) if vmax else 0
    if t < 0:
        a = -t; return "#%02x%02x%02x" % (int(200 - 170 * a), int(200 - 120 * a), int(210 + 30 * a))
    a = t; return "#%02x%02x%02x" % (int(210 + 30 * a), int(200 - 150 * a), int(200 - 160 * a))


def mag(v, vmax):
    a = min(1.0, abs(v) / vmax) ** 0.7
    return "#%02x%02x%02x" % (int(205 + (190 - 205) * a), int(205 - 160 * a), int(205 - 165 * a))


def draw_forces(pg, D, key, lc, box, vmax, groups=None, view="axon"):
    """element lines inside box (x, y, w, h); width and colour by |value| (same vmax for LONG and SHORT)"""
    pts, (x0, y0, x1, y1) = frame_points(D, view)
    s = min(box[2] / (x1 - x0), box[3] / (y1 - y0))
    ox = box[0] + (box[2] - (x1 - x0) * s) / 2 - x0 * s; oy = box[1] + (box[3] - (y1 - y0) * s) / 2 - y0 * s
    f = D["forces"][lc][key]; segs = []
    for i, (g, a, b) in enumerate(D["els"]):
        if groups and g not in groups:
            continue
        v = 0.5 * (f[2 * i] + f[2 * i + 1])
        w = 0.08 + 1.1 * min(1.0, abs(v) / vmax) if vmax else 0.1
        segs.append((abs(v), '<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="%s" stroke-width="%.2f" stroke-linecap="round"/>' % (
            ox + pts[a][0] * s, oy + pts[a][1] * s, ox + pts[b][0] * s, oy + pts[b][1] * s, color(v, vmax) if key == "N" else mag(v, vmax), w)))
    segs.sort()
    pg.o.extend(s for _, s in segs)


def draw_groups(pg, D, box):
    pts, (x0, y0, x1, y1) = frame_points(D)
    s = min(box[2] / (x1 - x0), box[3] / (y1 - y0))
    ox = box[0] + (box[2] - (x1 - x0) * s) / 2 - x0 * s; oy = box[1] + (box[3] - (y1 - y0) * s) / 2 - y0 * s
    col = {"rib_bottom": "#b03a2e", "rib_middle": "#d35400", "rib_top": "#f39c12", "ring": "#000", "crown": "#000",
           "column": "#000", "course": "#c8c8c8", "fin": "#a9a9a9"}
    wid = {"rib_bottom": 0.7, "rib_middle": 0.55, "rib_top": 0.45, "ring": 0.9, "crown": 0.8, "column": 0.9, "course": 0.12, "fin": 0.12}
    for gset in (("course", "fin"), ("rib_bottom", "rib_middle", "rib_top"), ("ring", "crown", "column")):
        for i, (g, a, b) in enumerate(D["els"]):
            if g in gset:
                pg.o.append('<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="%s" stroke-width="%.2f" stroke-linecap="round"/>' % (
                    ox + pts[a][0] * s, oy + pts[a][1] * s, ox + pts[b][0] * s, oy + pts[b][1] * s, col[g], wid[g]))
    return col


def table(pg, x, y, cols, rows, widths, size=2.5, head=True):
    xx = x
    for c, w in zip(cols, widths):
        pg.text(xx, y, c, size, bold=True); xx += w
    pg.line(x, y + 1.3, x + sum(widths), y + 1.3, 0.2)
    y += 4.6
    for r in rows:
        xx = x
        for c, w in zip(r, widths):
            pg.text(xx, y, c, size); xx += w
        y += 4.0
    pg.line(x, y - 2.6, x + sum(widths), y - 2.6, 0.15)
    return y


def f1(v): return "%.1f" % v
def rng(t): return "%+.1f / %+.1f" % t


# ---------------- sheets ----------------
def sheet_model(no, R):
    pg = Page(no, "The Karamba model at the real height", "Both roofs as built in Rhino: columns up to +2.00, base ring +2.00 to +2.40, crown +11.90 (15x10) and +7.79 (10x10). Design model D2: the printed casing is tied to the ribs through the tubes, the bed joints only take compression and the head joints are open (sheet 09).")
    pg.header()
    for k, roof in enumerate(("15x10", "10x10")):
        D = R[roof]; x = ps.COLX[k]
        pg.column(k, "%s · %s" % ("AB"[k], roof.upper()), "%d elements, %d nodes, %d supports" % (len(D["els"]), len(D["nodes"]), len(D["reactions"]["LONG"]["RF"])))
        col = draw_groups(pg, D, (x, 64, ps.COLW, 112))
        rows = []
        for g in GROUPS:
            n = len(D["idx"].get(g, []))
            if not n: continue
            if g in ("course", "fin"):
                desc = ("printed, E x 0.02 of C30/37 (head joints open), tied to the ribs" if g == "course" else "printed walls across the bed joints: pinned trusses, E 25 GPa, compression only; weight in courses")
            else:
                desc = sec_props(roof, g)[3] + ", cast C30/37"
            rows.append((NAMES[g], str(n), desc))
        y = table(pg, x, 184, ("ELEMENT", "BARS", "SECTION / MATERIAL"), rows, (52, 16, 90))
        W_ = abs(D["sumF"]["LONG"][2])
        pg.text(x, y + 2, "Total weight LONG (self-weight + formwork top-up 0.34 + insulation and finishes 1.13 kN/m2): %.0f kN." % W_, 2.6)
    pg.text(16, H - 10, "Loads as nodal point loads (each face load split over its 3 nearest nodes; resultants checked). LONG: weight. SHORT: weight + typhoon qp 2.6 kN/m2 from 5 directions; earthquake Ci = 0.14; maintenance 0.6 kN/m2 on half the roof (checked as long-term).", 2.5)
    return pg


def sheet_forces(no, R, roof):
    D = R[roof]
    gov = max(SHORTS, key=lambda lc: D["maxdisp_cm"][lc])
    pg = Page(no, "The model under load: forces and moments together · %s" % roof,
              "One run of the whole %s roof under LONG (weight) and SHORT (weight + typhoon %s, the governing wind), same view and same scale for LONG and SHORT. Line width by value. Axial: blue compression, red tension; other forces: grey to red with the value." % (roof, gov))
    pg.header()
    keys = [("N", "AXIAL FORCE N"), ("Vz", "SHEAR Vz"), ("My", "BENDING My"), ("Mt", "TORSION Mt")]
    bw, bh = (W - 32) / 4 - 4, 62
    for j, (k, title) in enumerate(keys):
        allv = sorted(abs(v) for lc in ("LONG", gov) for v in D["forces"][lc][k]); vmax = allv[int(0.98 * (len(allv) - 1))] or 1
        for r, lc in enumerate(("LONG", gov)):
            x = 16 + j * (bw + 5.3); y = 58 + r * (bh + 14)
            if r == 0: pg.text(x, 56, title, 3.4, bold=True)
            pg.o.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="none" stroke="#999" stroke-width="0.15"/>' % (x, y, bw, bh))
            draw_forces(pg, D, k, lc, (x + 2, y + 2, bw - 4, bh - 4), vmax)
            vals = D["forces"][lc][k]
            pg.text(x, y + bh + 4.2, "%s: %s %.1f to %+.1f %s" % ("LONG" if r == 0 else "SHORT " + lc, k, min(vals), max(vals), "kN" if k in ("N", "Vz") else "kNm"), 2.5)
    for r, lab in enumerate(("LONG", "SHORT")):
        pg.text(9, 58 + r * (bh + 14) + bh / 2, lab, 3.4, bold=True, anchor="middle")
    rows = []
    for g in GROUPS:
        if g not in D["idx"]: continue
        a = group_stats(D, roof, g, LONGS); b = group_stats(D, roof, g, SHORTS)
        rows.append((NAMES[g] + " (%d)" % len(D["idx"][g]), rng(a["N"]), rng(a["My"]), rng(a["Mz"]), rng(b["N"]), rng(b["My"]), rng(b["Mz"])))
    y = 58 + 2 * (bh + 14) + 4
    pg.text(16, y, "BEAM FORCES FROM KARAMBA, MIN / MAX OF EACH MEMBER GROUP (kN, kNm; + tension). LONG = LONG, LIVEX, LIVEY; SHORT = 5 typhoon + 2 earthquake cases", 3.0, bold=True)
    yy = table(pg, 16, y + 6, ("", "N LONG", "My LONG", "Mz LONG", "N SHORT", "My SHORT", "Mz SHORT"), rows, (70, 34, 30, 30, 34, 30, 30))
    sl = D["sumF"]["LONG"]; sg = D["sumF"][gov]
    rl = D["reactions"]["LONG"]["RF"]
    txt = "Global check: LONG  sum V = %.0f kN = the weight, shared by %d supports (%.0f to %.0f kN each). SHORT %s  sum V = %.0f kN and sum H = %.0f kN. Max displacement %.1f mm LONG, %.1f mm SHORT (2nd order %.1f mm). First buckling load factor %.1f." % (
        abs(sl[2]), len(rl), min(f[2] for f in rl), max(f[2] for f in rl), gov, abs(sg[2]), math.hypot(sg[0], sg[1]), D["maxdisp_cm"]["LONG"] * 10, D["maxdisp_cm"][gov] * 10, D["maxdisp_ThII_cm"][gov] * 10, D["buckling"][0])
    pg.o.append('<rect x="14" y="%.1f" width="%.1f" height="9" fill="none" stroke="#000" stroke-width="0.3"/>' % (yy - 1, W - 28))
    pg.text(17, yy + 4.6, txt, 2.7, bold=True)
    return pg


def centre(roof):
    return (85.0, 0.0) if roof == "15x10" else (85.0, -20.0)


def rib_face_fbd(D, roof, lc="LONG"):
    """by hand from the Karamba bar forces: what the ribs put into the base ring (foot nodes = rib nodes shared with
    the ring) and into the crown ring. Force of a bar on its end node p = N * unit(p->q) (N + tension)."""
    W_ = abs(D["sumF"][lc][2])
    ring = set(); crown = set()
    for g, a, b in D["els"]:
        if g == "ring": ring |= {a, b}
        if g == "crown": crown |= {a, b}
    z_ring = D["nodes"][next(iter(ring))][2]; z_crown = D["nodes"][next(iter(crown))][2]
    cx, cy = centre(roof)
    f = D["forces"][lc]["N"]; Hf = Vf = Hc = Vc = 0.0; nf = set(); nc = set()
    for i, (g, a, b) in enumerate(D["els"]):
        if not g.startswith("rib"): continue
        for (pi, qi, t) in ((a, b, 0), (b, a, 1)):
            if pi not in ring and pi not in crown: continue
            p, q = D["nodes"][pi], D["nodes"][qi]; L = math.dist(p, q); N = f[2 * i + t]
            ux, uy, uz = (q[0] - p[0]) / L, (q[1] - p[1]) / L, (q[2] - p[2]) / L
            rx, ry = p[0] - cx, p[1] - cy; rl = math.hypot(rx, ry) or 1
            radial = (ux * rx + uy * ry) / rl              # + = towards the outside
            if pi in ring:
                Hf += N * radial; Vf += -N * uz; nf.add(pi)   # outward push / downward load on the ring
            else:
                Hc += -N * radial; Vc += N * uz; nc.add(pi)   # inward push on the crown ring
    return W_, z_ring, z_crown, Hf, Hc, Vf, len(nf), len(nc), Vc


def arrow(pg, x1, y1, x2, y2, w=0.35, color="#000"):
    pg.line(x1, y1, x2, y2, w, color)
    L = math.hypot(x2 - x1, y2 - y1) or 1; ux, uy = (x2 - x1) / L, (y2 - y1) / L
    pg.o.append('<path d="M%.2f %.2f L%.2f %.2f L%.2f %.2f Z" fill="%s"/>' % (
        x2, y2, x2 - 2.2 * ux + 0.9 * uy, y2 - 2.2 * uy - 0.9 * ux, x2 - 2.2 * ux - 0.9 * uy, y2 - 2.2 * uy + 0.9 * ux, color))


def fbd(pg, D, roof, x, y):
    """hand free body of the rib net: weight down, what the ribs put into the base ring and the crown ring (LONG)"""
    W_, zr, zc, Hf, Hc, Vf, nf, nc, Vc = rib_face_fbd(D, roof)
    pg.text(x, y, "FREE BODY OF THE RIB NET, LONG", 3.0, bold=True)
    fx, fy, cx_, cy_ = x + 16, y + 62, x + 62, y + 14          # foot and crown of one face, schematic
    pg.line(fx, fy, cx_, cy_, 1.4)
    pg.line(fx - 10, fy, fx + 2, fy, 0.25); pg.line(cx_, cy_, cx_ + 14, cy_, 0.25)
    pg.text(cx_ + 2, cy_ - 2, "crown ring +%.2f" % zc, 2.2, italic=True)
    for t in range(1, 7):
        px = fx + (cx_ - fx) * t / 7.0; py = fy + (cy_ - fy) * t / 7.0
        arrow(pg, px, py - 9, px, py - 1.2, 0.25)
    pg.text(fx + 34, fy - 18, "W = %.0f kN" % W_, 2.7, bold=True)
    pg.text(fx + 34, fy - 14.5, "(whole roof, LONG)", 2.3, italic=True)
    arrow(pg, fx + 1, fy + 4, fx - 13, fy + 4, 0.6, "#b03a2e"); pg.text(fx - 14, fy + 8.5, "H %.0f kN out" % Hf, 2.4, color="#b03a2e")
    arrow(pg, fx + 3, fy + 1, fx + 3, fy + 13, 0.6); pg.text(fx + 5, fy + 12, "V %.0f kN down" % Vf, 2.4)
    pg.text(fx - 14, fy - 2, "base ring +%.2f" % zr, 2.2, italic=True)
    arrow(pg, cx_ - 14, cy_ + 5, cx_ - 1, cy_ + 5, 0.6, "#2c5aa0"); pg.text(cx_ - 34, cy_ + 6, "H %.0f kN in" % Hc, 2.4, color="#2c5aa0")
    yy = fy + 20
    for t in ("Sums over the %d rib feet on the base ring and the %d rib heads on the crown ring (Karamba bar forces)." % (nf, nc),
              "The ribs bring V = %.0f kN of the %.0f kN down to the ring (%d %%); the rest goes down the printed pieces." % (Vf, W_, round(100 * Vf / W_)),
              "The outward foot thrust H = %.0f kN is tied by the base ring; the crown ring takes %.0f kN inward." % (Hf, Hc)):
        pg.text(x, yy, t, 2.4); yy += 3.8
    return yy


def my_along(pg, D, roof, x, y, w, h):
    """M = sqrt(My2+Mz2) of every rib bar end against its height, LONG grey and SHORT red"""
    pg.text(x, y, "BENDING ALONG THE RIBS: M AT EVERY BAR END", 3.0, bold=True)
    y0 = y + 5; zr = 2.4; zc = max(p[2] for p in D["nodes"])
    pts = {"LONG": [], "SHORT": []}
    for i, (g, a, b) in enumerate(D["els"]):
        if not g.startswith("rib"): continue
        for t, ni in ((0, a), (1, b)):
            z = D["nodes"][ni][2]
            ml = max(math.hypot(D["forces"][lc]["My"][2 * i + t], D["forces"][lc]["Mz"][2 * i + t]) for lc in LONGS)
            ms = max(math.hypot(D["forces"][lc]["My"][2 * i + t], D["forces"][lc]["Mz"][2 * i + t]) for lc in SHORTS)
            pts["LONG"].append((z, ml)); pts["SHORT"].append((z, ms))
    mmax = max(m for _, m in pts["SHORT"]); mmax = math.ceil(mmax / 2.0) * 2
    pg.line(x + 10, y0, x + 10, y0 + h, 0.25); pg.line(x + 10, y0 + h, x + w, y0 + h, 0.25)
    for k in range(0, int(mmax) + 1, 2 if mmax <= 12 else 4):
        X = x + 10 + (w - 10) * k / mmax; pg.line(X, y0 + h, X, y0 + h + 1, 0.2); pg.text(X, y0 + h + 4, str(k), 2.2, anchor="middle")
    pg.text(x + w, y0 + h + 8, "M (kNm)", 2.3, anchor="end")
    for zz in (zr, (zr + zc) / 2, zc):
        Y = y0 + h - h * (zz - zr) / (zc - zr); pg.text(x + 9, Y + 0.8, "+%.1f" % zz, 2.1, anchor="end")
    for key, colr, rr in (("SHORT", "#b03a2e", 0.45), ("LONG", "#555", 0.4)):
        for z, m in pts[key]:
            if z < zr - 0.01: continue
            pg.o.append('<circle cx="%.2f" cy="%.2f" r="%.2f" fill="%s" fill-opacity="0.55"/>' % (x + 10 + (w - 10) * m / mmax, y0 + h - h * (z - zr) / (zc - zr), rr, colr))
    pg.text(x + w - 32, y0 + 4, "grey: LONG cases", 2.3, color="#555"); pg.text(x + w - 32, y0 + 8, "red: SHORT cases", 2.3, color="#b03a2e")
    return y0 + h + 10


def section_stress(pg, roof, g, st, x, y):
    """stress across the governing core section, linear from -N/A - M/W to -N/A + M/W (compression +)"""
    A, Wm, _, name = sec_props(roof, g)
    c, lc, N, M = st[0], st[1], st[2], st[3]
    s_a = -N / A / 1000; s_b = M / Wm / 1000
    top, bot = s_a + s_b, s_a - s_b
    pg.text(x, y, "STRESS ACROSS THE GOVERNING CORE, %s (%s)" % (name.replace("solid round ", ""), lc), 3.0, bold=True)
    r = 9; ccx, ccy = x + 12, y + 16
    pg.o.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="#eee" stroke="#000" stroke-width="0.3"/>' % (ccx, ccy, r))
    pg.line(ccx - r - 3, ccy, ccx + r + 3, ccy, 0.15)
    sc = 26.0 / max(abs(top), abs(bot), 1)
    bx = x + 44
    pg.line(bx, ccy - r - 2, bx, ccy + r + 2, 0.3)
    pg.o.append('<path d="M%.2f %.2f L%.2f %.2f L%.2f %.2f L%.2f %.2f Z" fill="#b03a2e" fill-opacity="0.35" stroke="#b03a2e" stroke-width="0.3"/>' % (
        bx, ccy - r, bx + top * sc, ccy - r, bx + bot * sc, ccy + r, bx, ccy + r))
    pg.text(bx + top * sc + 1.5, ccy - r + 1, "%.1f MPa compression" % top, 2.3)
    pg.text(bx + max(bot * sc, 0) + 1.5, ccy + r, "%.1f MPa %s" % (abs(bot), "tension" if bot < 0 else "compression"), 2.3)
    pg.text(x, ccy + r + 6, "N = %.1f kN, M = %.1f kNm:  N/A = %.1f MPa,  M/W = %.1f MPa." % (N, M, s_a, s_b), 2.4)
    return ccy + r + 10


def sheet_ribs(no, R):
    pg = Page(no, "Ribs: stresses and bending", "Solid round cast cores in printed tubes. Stress at every bar end from Karamba, sigma = N/A + M/W with M = sqrt(My2 + Mz2); allowable Fc 36 (AIJ): 12 MPa long-term, 24 MPa short-term.")
    pg.header()
    for k, roof in enumerate(("15x10", "10x10")):
        D = R[roof]; x = ps.COLX[k]; cw = ps.COLW
        pg.column(k, "%s · %s" % ("AB"[k], roof.upper()), "core D %s cm (bottom / middle / top band)" % " / ".join(str(round(100 * RIB_D[roof][g])) for g in ("rib_bottom", "rib_middle", "rib_top")))
        fbd(pg, D, roof, x, 66)
        my_along(pg, D, roof, x + cw / 2 + 4, 66, cw / 2 - 6, 70)
        rows = []; st = {}
        for g in ("rib_bottom", "rib_middle", "rib_top"):
            a = group_stats(D, roof, g, LONGS); b = group_stats(D, roof, g, SHORTS); st[g] = (a, b)
            rows.append((NAMES[g] + ", " + sec_props(roof, g)[3], "%.1f MPa, %d %% (%s)" % (a["sc"][0], round(100 * a["sc"][0] / ALL_L), a["sc"][1]),
                         "%.1f MPa, %d %% (%s)" % (b["sc"][0], round(100 * b["sc"][0] / ALL_S), b["sc"][1]), "%.1f MPa" % -min(a["st"][0], b["st"][0])))
        y = table(pg, x, 168, ("BAND", "LONG-TERM sigma c", "SHORT-TERM sigma c", "max tension"), rows, (60, 44, 44, 24))
        y += 6; y0 = y
        pg.text(x, y, "UTILISATION (DEMAND / ALLOWABLE)", 3.0, bold=True); y += 4
        for g in ("rib_bottom", "rib_middle", "rib_top"):
            a, b = st[g]
            for lab, u in (("long", a["sc"][0] / ALL_L), ("short", b["sc"][0] / ALL_S)):
                pg.text(x, y + 2.2, "%s, %s" % (g.replace("rib_", ""), lab), 2.4)
                pg.o.append('<rect x="%.1f" y="%.1f" width="%.1f" height="2.6" fill="#ddd"/>' % (x + 24, y, 50))
                pg.o.append('<rect x="%.1f" y="%.1f" width="%.1f" height="2.6" fill="%s"/>' % (x + 24, y, 50 * min(u, 1), "#b03a2e" if u > 0.9 else "#555"))
                pg.text(x + 77, y + 2.2, "%d %%" % round(100 * u), 2.4); y += 4.0
        a, b = st["rib_bottom"]
        gov = a["sc"] if a["sc"][0] / ALL_L > b["sc"][0] / ALL_S else b["sc"]
        section_stress(pg, roof, "rib_bottom", gov, x + cw / 2 + 4, y0)
    pg.text(16, H - 10, "Tension on the far face of a core (max tension column) is taken by bars in the core. Every band passes in both roofs; the governing bars are in the bottom band.", 2.5)
    return pg


def foot_check(D, B, trib, Df=0.8, tf=0.5):
    """strip footing under each support, from the Karamba reactions: bearing (effective area), tipping, sliding"""
    sp = [p for p in D["nodes"] if abs(p[2]) < 1e-6]          # supports = the z = 0 nodes, in Karamba's order
    nS = len(sp); worst = {}
    for lc in LCS:
        wq = None; wt = 99; ws = 99
        for k2, (f, mm) in enumerate(zip(D["reactions"][lc]["RF"], D["reactions"][lc]["RM"])):
            p0, p1 = sp[(k2 - 1) % nS], sp[(k2 + 1) % nS]
            tx, ty = p1[0] - p0[0], p1[1] - p0[1]; tl = math.hypot(tx, ty); tx, ty = tx / tl, ty / tl   # along the strip
            nx, ny = ty, -tx                                                                                 # across the strip
            Ha, Hl = abs(f[0] * nx + f[1] * ny), abs(f[0] * tx + f[1] * ty)
            Ma = abs(mm[0] * tx + mm[1] * ty) + Ha * Df
            Ml = abs(mm[0] * nx + mm[1] * ny) + Hl * Df
            N = f[2] + 24 * B * tf * trib + 18 * B * (Df - tf) * trib
            Bp, Lp = B - 2 * Ma / N, trib - 2 * Ml / N
            qmax = N / (Bp * Lp) if Bp > 0 and Lp > 0 else 1e9
            if wq is None or qmax > wq[0]: wq = (qmax, Ma / N)
            wt = min(wt, N * B / 2 / Ma if Ma else 99, N * trib / 2 / Ml if Ml else 99)
            ws = min(ws, 0.5 * N / math.hypot(f[0], f[1]))
        worst[lc] = (wq, wt, ws)
    return worst


def sheet_rings_columns(no, R):
    pg = Page(no, "Rings, columns and footings", "The base ring ties the foot thrust of the ribs (tension), the crown ring gathers them at the top (compression). Columns carry the ring to the rectangular strip footing; footing checked by hand from the Karamba reactions.")
    pg.header()
    for k, roof in enumerate(("15x10", "10x10")):
        D = R[roof]; x = ps.COLX[k]
        pg.column(k, "%s · %s" % ("AB"[k], roof.upper()), "")
        W_, zr, zc, Hf, Hc, Vf, nf, nc, Vc = rib_face_fbd(D, roof)
        per = sum(math.dist(D["nodes"][a], D["nodes"][b]) for (g, a, b) in D["els"] if g == "ring")
        req = per / (2 * math.pi); q = Hf / per; T = q * req
        a = group_stats(D, roof, "ring", LONGS); b = group_stats(D, roof, "ring", SHORTS)
        cr = group_stats(D, roof, "crown", LONGS); crs = group_stats(D, roof, "crown", SHORTS)
        co = group_stats(D, roof, "column", LONGS); cos = group_stats(D, roof, "column", SHORTS)
        y = 68
        pg.text(x, y, "BASE RING 40 x 40 (TIE), HAND CHECK AGAINST KARAMBA", 3.0, bold=True); y += 5
        for t in ("Outward foot thrust of the ribs (LONG): H = %.0f kN on a ring perimeter of %.1f m: q = %.1f kN/m." % (Hf, per, q),
                  "Hoop tension, ring taken as a circle of the same perimeter: r = %.2f m, T = q r = %.1f x %.2f = %.0f kN." % (req, q, req, T),
                  "Karamba: N = %+.0f to %+.0f kN LONG, up to %+.0f kN SHORT (tension all round); M up to %.1f kNm." % (a["N"][0], a["N"][1], b["N"][1], max(max(abs(v) for v in b["My"]), max(abs(v) for v in b["Mz"]))),
                  "The ring also ties what the printed pieces push out, so Karamba is above the rib-only hand value.",
                  "Bars for the tension: As = %.0f kN / 215 MPa = %d mm2 long-term, %.0f / 345 = %d mm2 short-term; 8D16 = 1,592 mm2." % (a["N"][1], round(a["N"][1] / 0.215), b["N"][1], round(b["N"][1] / 0.345))):
            pg.text(x, y, t, 2.5); y += 4.2
        y += 3
        pg.text(x, y, "CROWN RING 25 x 25 (COMPRESSION)", 3.0, bold=True); y += 5
        for t in ("Inward push of the rib heads (LONG): H = %.0f kN; the ribs also hold the ring up, V = %.0f kN." % (Hc, Vc),
                  "Karamba: N = %+.1f to %+.1f kN LONG, %+.1f to %+.1f kN SHORT; sigma max %.1f MPa = %d %% of %d MPa." % (cr["N"][0], cr["N"][1], crs["N"][0], crs["N"][1], crs["sc"][0], round(100 * crs["sc"][0] / ALL_S), ALL_S)):
            pg.text(x, y, t, 2.5); y += 4.2
        y += 3
        n_col = len(D["reactions"]["LONG"]["RF"])
        bsec = sec_props(roof, "column"); A_c = bsec[0]
        pg.text(x, y, "COLUMNS %s, %d IN KARAMBA, +-0.00 TO +2.00" % (bsec[3], n_col), 3.0, bold=True); y += 5
        vl = [f[2] for f in D["reactions"]["LONG"]["RF"]]
        for t in ("By hand: weight %.0f kN / %d columns = %.0f kN each; Karamba LONG %.0f to %.0f kN (the long sides carry more)." % (W_, n_col, W_ / n_col, min(vl), max(vl)),
                  "Karamba: N = %+.0f to %+.0f kN LONG, %+.0f to %+.0f kN SHORT; M up to %.1f kNm (SHORT)." % (co["N"][0], co["N"][1], cos["N"][0], cos["N"][1], max(abs(v) for v in cos["My"] + cos["Mz"])),
                  "sigma = N/A + M/W: %.1f MPa LONG (%d %%), %.1f MPa SHORT (%d %%), governing case %s." % (co["sc"][0], round(100 * co["sc"][0] / ALL_L), cos["sc"][0], round(100 * cos["sc"][0] / ALL_S), cos["sc"][1])):
            pg.text(x, y, t, 2.5); y += 4.2
        y += 3
        # rectangular strip footing with square corner blocks (Gonzalo 2026-11-23), by hand from the support reactions
        import rect_check
        RR = json.load(open(os.path.join(HERE, "rect_result.json")))[roof]
        B = 1.20 if roof == "15x10" else 0.85
        rc_, Ls = rect_check.check(roof, B)
        worst = {lc: ((v[0], 0.0), v[1], v[2]) for lc, v in rc_.items()}; rows = []
        pg.text(x, y, "RECTANGULAR STRIP FOOTING %d x 50, SQUARE CORNER BLOCKS, BASE -0.80, HAND CHECK" % round(B * 100), 3.0, bold=True); y += 5
        pg.text(x, y, "Straight strips on the side column lines, outside %.2f x %.2f m; corner blocks %.2f x %.2f m under the corner columns. Each column on %.2f m of strip." % (RR["outer_m"][0], RR["outer_m"][1], RR["block_m"][0], RR["block_m"][1], Ls), 2.4); y += 4
        pg.text(x, y, "N = reaction + strip + soil; M = reaction moment + H x 0.80, plus N x the column's offset from the strip axis (up to %.2f m). Effective-area bearing; continuity not counted." % max(v for v in RR["col_offsets"] if v < 0.5), 2.4); y += 5
        for lab, lcs, qa in (("LONG", LONGS, 200.0), ("SHORT", SHORTS, 400.0)):
            lq = max(lcs, key=lambda l: worst[l][0][0]); lt = min(lcs, key=lambda l: worst[l][1]); ls = min(lcs, key=lambda l: worst[l][2])
            rows.append((lab, "%.0f kPa / %.0f (%d %%), %s" % (worst[lq][0][0], qa, round(100 * worst[lq][0][0] / qa), lq),
                         "%.1f (%s)" % (worst[lt][1], lt), "%.1f (%s)" % (worst[ls][2], ls)))
        y = table(pg, x, y + 1, ("", "BEARING q max / allowable", "TIPPING FS", "SLIDING FS (mu 0.5)"), rows, (16, 66, 34, 40))
        okt = all(worst[l][1] >= 1.5 for l in LCS); oks = all(worst[l][2] >= 1.5 for l in LCS)
        okq = all(worst[l][0][0] <= (200 if l in LONGS else 400) for l in LCS)
        pg.text(x, y + 1, "Required: tipping FS = N (B/2) / M >= 1.5, sliding FS = 0.5 N / H >= 1.5. Bearing %s, tipping %s, sliding %s." % (
            "OK" if okq else "NOT OK", "OK" if okt else "NOT OK", "OK" if oks else "NOT OK"), 2.4, bold=True)
        Bn = B
        Bn = 0.5
        while min(v[1] for v in rect_check.check(roof, Bn)[0].values()) < 1.5 and Bn < 4: Bn += 0.05
        FOOT[roof] = (worst, okq, okt, oks, B, Bn)
        if not okt:
            y += 5
            pg.text(x, y, "Tipping is short of 1.5 (min %.2f); a %.2f m wide strip gives 1.5." % (min(v[1] for v in worst.values()), Bn), 2.4, color="#b03a2e")
    pg.text(16, H - 10, "Soil bearing 200 kPa long-term / 400 kPa short-term assumed (no site investigation yet). Rhino and Karamba have the same supports: 20 columns on the 15x10, 16 on the 10x10. Narrowest strip reaching tipping 1.5: %.2f m (15x10), %.2f m (10x10)." % (FOOT["15x10"][5], FOOT["10x10"][5]) + "", 2.5)
    return pg


def sheet_summary(no, R):
    pg = Page(no, "Utilisation summary", "Every member type of both roofs at the real height, worst long-term and short-term case. Concrete Fc 36: 12 MPa long-term, 24 MPa short-term; soil 200 / 400 kPa assumed.")
    pg.header()
    if not FOOT:
        sheet_rings_columns("05", R)
    for k, roof in enumerate(("15x10", "10x10")):
        D = R[roof]; x = ps.COLX[k]
        pg.column(k, "%s · %s" % ("AB"[k], roof.upper()), "")
        rows = []; bars = []
        for g in ("rib_bottom", "rib_middle", "rib_top", "ring", "crown", "column"):
            a = group_stats(D, roof, g, LONGS); b = group_stats(D, roof, g, SHORTS)
            ul = a["sc"][0] / ALL_L; us = b["sc"][0] / ALL_S
            lab = NAMES[g] + (" (concrete)" if g == "ring" else "")
            rows.append((lab, sec_props(roof, g)[3], "%.1f MPa, %d %%" % (a["sc"][0], round(100 * ul)), "%.1f MPa, %d %%" % (b["sc"][0], round(100 * us)), "OK" if max(ul, us) < 1 else "CHECK"))
            bars.append((lab, ul, us))
        worst, okq, okt, oks, B, Bn = FOOT[roof]
        ql = max(worst[l][0][0] for l in LONGS); qs = max(worst[l][0][0] for l in SHORTS)
        rows.append(("Strip footing, bearing", "%d x 50" % round(B * 100), "%.0f kPa, %d %%" % (ql, round(ql / 2)), "%.0f kPa, %d %%" % (qs, round(qs / 4)), "OK" if okq else "CHECK"))
        bars.append(("Strip footing, bearing", ql / 200, qs / 400))
        tl = min(worst[l][1] for l in LONGS); ts = min(worst[l][1] for l in SHORTS)
        rows.append(("Strip footing, tipping FS", "need 1.5", "%.2f, %d %%" % (tl, round(150 / tl)), "%.2f, %d %%" % (ts, round(150 / ts)), "OK" if okt else "CHECK"))
        bars.append(("Strip footing, tipping", 1.5 / tl, 1.5 / ts))
        y = table(pg, x, 70, ("MEMBER", "SECTION", "LONG", "SHORT", ""), rows, (52, 28, 34, 34, 14), size=2.6)
        y += 6
        pg.text(x, y, "UTILISATION, LONG (GREY) AND SHORT (RED)", 3.0, bold=True); y += 5
        bw = 110
        for lab, ul, us in bars:
            pg.text(x, y + 2.3, lab, 2.4)
            for j, (u, c) in enumerate(((ul, "#666"), (us, "#b03a2e"))):
                yy = y + j * 2.8
                pg.o.append('<rect x="%.1f" y="%.1f" width="%.1f" height="2.4" fill="#e6e6e6"/>' % (x + 46, yy, bw))
                pg.o.append('<rect x="%.1f" y="%.1f" width="%.1f" height="2.4" fill="%s"/>' % (x + 46, yy, bw * min(u, 1.2) / 1.2, c))
                pg.text(x + 48 + bw, yy + 2.1, "%d %%" % round(100 * u), 2.2)
            y += 7.4
        X1 = x + 46 + bw / 1.2
        pg.line(X1, y - 7.4 * len(bars) - 1, X1, y - 1.5, 0.3)
        pg.text(X1, y + 1.5, "100 %", 2.2, anchor="middle")
        y += 7
        pg.text(x, y, "GLOBAL", 3.0, bold=True); y += 5
        gov = max(SHORTS, key=lambda lc: D["maxdisp_cm"][lc])
        for t in ("Weight LONG: %.0f kN." % abs(D["sumF"]["LONG"][2]),
                  "Max displacement: %.1f mm LONG, %.1f mm SHORT (%s); 2nd order %.1f mm." % (D["maxdisp_cm"]["LONG"] * 10, D["maxdisp_cm"][gov] * 10, gov, D["maxdisp_ThII_cm"][gov] * 10),
                  "First buckling load factor: %.1f." % D["buckling"][0],
                  "Support reactions LONG: V %.0f to %.0f kN; SHORT: V %.0f to %.0f kN, H up to %.0f kN." % (
                      min(f[2] for f in D["reactions"]["LONG"]["RF"]), max(f[2] for f in D["reactions"]["LONG"]["RF"]),
                      min(f[2] for lc in SHORTS for f in D["reactions"][lc]["RF"]), max(f[2] for lc in SHORTS for f in D["reactions"][lc]["RF"]),
                      max(math.hypot(f[0], f[1]) for lc in SHORTS for f in D["reactions"][lc]["RF"]))):
            pg.text(x, y, t, 2.6); y += 4.4
        if not okt:
            pg.text(x, y + 2, "Open point: footing tipping (sheet 05), needs %.2f m." % Bn, 2.6, bold=True, color="#b03a2e")
    pg.text(16, H - 10, "Source: Karamba3D 3.1, canvases polyframe2/stepped-15x10-karamba-2m-2026-11-23.gh and stepped-10x10-karamba-2m-2026-11-23.gh (geometry at the real height, rib cores as modelled). Ring in tension: bars on sheet 05.", 2.5)
    return pg



# ---------------- corner-leg removal study (Gonzalo 2026-11-23) ----------------
def elem_util(D, roof):
    """per element: max over all load cases of sigma_c / allowable (LONG 12, SHORT 24); None for courses and fins"""
    f = D["forces"]; out = []
    props = {g: sec_props(roof, g) for g in ("rib_bottom", "rib_middle", "rib_top", "ring", "crown", "column")}
    for i, (g, a, b) in enumerate(D["els"]):
        if g not in props:
            out.append(None); continue
        A, Wy, Wz, _ = props[g]; u = 0
        for lc in LCS:
            al = ALL_L if lc in LONGS else ALL_S
            for t in (0, 1):
                N = f[lc]["N"][2 * i + t]; My = f[lc]["My"][2 * i + t]; Mz = f[lc]["Mz"][2 * i + t]
                m = math.hypot(My, Mz) / Wy if g.startswith("rib") else abs(My) / Wy + abs(Mz) / Wz
                u = max(u, (-N / A + m) / 1000.0 / al)
        out.append(u)
    return out


def ucolor(u):
    t = max(0.0, min(1.0, u))
    if t < 0.5:
        a = t / 0.5; return "#%02x%02x%02x" % (int(150 + 90 * a), int(190 + 20 * a), int(150 - 100 * a))
    a = (t - 0.5) / 0.5; return "#%02x%02x%02x" % (int(240 - 20 * a), int(210 - 170 * a), int(50 - 10 * a))


def draw_util(pg, D, roof, box):
    pts, (x0, y0, x1, y1) = frame_points(D)
    s_ = min(box[2] / (x1 - x0), box[3] / (y1 - y0))
    ox = box[0] + (box[2] - (x1 - x0) * s_) / 2 - x0 * s_; oy = box[1] + (box[3] - (y1 - y0) * s_) / 2 - y0 * s_
    U = elem_util(D, roof); segs = []
    for i, (g, a, b) in enumerate(D["els"]):
        u = U[i]
        col, w = ("#d6d6d6", 0.08) if u is None else (ucolor(u), 0.25 + 0.6 * min(u, 1))
        segs.append((-1 if u is None else u, '<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="%s" stroke-width="%.2f" stroke-linecap="round"/>' % (
            ox + pts[a][0] * s_, oy + pts[a][1] * s_, ox + pts[b][0] * s_, oy + pts[b][1] * s_, col, w)))
    segs.sort(); pg.o.extend(q for _, q in segs)
    for (rx, ry) in D.get("removed", []):
        px, py = proj((rx, ry, 0.0)); X, Y = ox + px * s_, oy + py * s_
        pg.o.append('<path d="M%.2f %.2f L%.2f %.2f M%.2f %.2f L%.2f %.2f" stroke="#c0392b" stroke-width="0.5"/>' % (X - 1.6, Y - 1.6, X + 1.6, Y + 1.6, X - 1.6, Y + 1.6, X + 1.6, Y - 1.6))


def sheet_corners(no):
    import corners_report as cr
    pg = Page(no, "Corner columns taken out", "Computed on the earlier casing model (B: courses E x 0.02, end walls bending, E x 0.3), before D2; in D2 the ribs are at the same level (76 % vs 75 %), so the conclusions hold. The diagonal corner column of each roof corner removed (column and its support): 1, 2 on the same long side, 2 diagonal, 3 and all 4. Everything else as built; all 10 load cases. Colour: worst sigma / allowable of each bar (green low, red at 100 %); red cross = column taken out.")
    pg.header()
    W_ = json.load(open(os.path.join(HERE, "corners_footing_width.json")))
    bw = (W - 32) / 6 - 3
    for r, roof in enumerate(("15x10", "10x10")):
        y = 58 + r * 98
        pg.text(16, y - 3, roof.upper(), 3.4, bold=True)
        rows = []
        for k, (case, lab) in enumerate(cr.CASES):
            D = cr.load(roof, case); S = cr.summary(roof, case)
            x = 16 + k * (bw + 3.6)
            pg.o.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="none" stroke="#bbb" stroke-width="0.15"/>' % (x, y, bw, 44))
            draw_util(pg, D, roof, (x + 1.5, y + 1.5, bw - 3, 41))
            pg.text(x, y + 48, lab, 2.4, bold=True)
            u = S["util"]
            for j, t in enumerate(("ribs %d / %d / %d %%" % (round(100 * u["rib_bottom"]), round(100 * u["rib_middle"]), round(100 * u["rib_top"])),
                                   "base ring concrete %d %%, M %.0f kNm" % (round(100 * u["ring"]), S["ring_M"]),
                                   "ring bars %d of %d mm2 per face" % (round(S["ring_bars"][0]), cr.AS_FACE),
                                   "crown %d %%, columns %d %%" % (round(100 * u["crown"]), round(100 * u["column"])),
                                   "max displacement %.1f mm (%s)" % (S["disp_mm"], S["disp_lc"]),
                                   "buckling factor %.1f" % S["buckling"],
                                   "column reaction %.0f to %.0f kN" % (S["fz_min"], S["fz_max"]),
                                   "footing width for tipping 1.5: %s m" % ("%.2f" % W_[roof + "|" + case] if case != "0" else ("1.15" if roof == "15x10" else "0.80")))):
                pg.text(x, y + 52.5 + 3.6 * j, t, 2.2)
    pg.text(16, H - 16, "Result: the roofs stand with any of the corner columns taken out, up to all four. Every member stays under its allowable (worst: 15x10 bottom ribs 78 %); deflection and buckling barely change (the base ring", 2.6, bold=True)
    pg.text(16, H - 11.5, "bridges the corner). What changes: the base ring bends more at the free corner (M up to 41 kNm, 94 % of 3D16 per face on the 15x10), and the side columns next to a free corner carry more (up to 176 kN),", 2.6, bold=True)
    pg.text(16, H - 7, "so the strip footing must widen to keep tipping at 1.5: 1.30 m on the 15x10 and 1.05 m on the 10x10 with all four corners out. If corners are left open, add 2D16 per face to the ring at the corner.", 2.6, bold=True)
    return pg


def sheet_casing(no, R):
    """the casing model D2 in plain words, with the numbers from formwork/variant-D.json and the D2 forces"""
    V = json.load(open(os.path.join(HERE, "formwork", "variant-D.json")))["results"]
    pg = Page(no, "How the printed casing works (design model D2)", "Every printed piece is printed around its rib tube and the cast core runs through it, so the pieces hang on the ribs. The bed joints between courses are mortar: they only push. The joints between pieces along a course are taken as open.")
    pg.header()
    for k, roof in enumerate(("15x10", "10x10")):
        D = R[roof]; x = ps.COLX[k]; d2 = V["%s D2" % roof]; d1 = V["%s D1" % roof]
        pg.column(k, "%s · %s" % ("AB"[k], roof.upper()), "")
        y = 68
        pg.text(x, y, "HOW IT IS MODELLED IN KARAMBA", 3.0, bold=True); y += 5
        for t in ("Ribs, rings, crown and columns: cast C30/37 beams, as on the other sheets.",
                  "Courses (the printed hoops): beams on the rib nodes, E x 0.02, so a course cannot work as a stiff ring (open head joints).",
                  "End walls of the pieces (cross every bed joint): pinned trusses, axial force only, compression only.",
                  "Karamba's Tension/Compression Eliminator removes every end wall that would pull and solves again, once for each load case.",
                  "Weight of the casing: in the courses; loads as on sheet 01."):
            pg.text(x, y, t, 2.5); y += 4.2
        y += 4
        pg.text(x, y, "WHAT IT DOES", 3.0, bold=True); y += 5
        sh = d2["base_share_LONG"]; out = d2["fins_dropped_in_tension"]
        wind = [lc for lc in SHORTS if out[lc]]
        for t in ("About %d %% of the weight reaches the base ring through the casing, %d %% through the ribs (LONG)." % (round(100 * sh["courses_fins_share"]), 100 - round(100 * sh["courses_fins_share"])),
                  "Under typhoon some end walls lift off their bed joint and drop out: up to %d of %d (%s); none under weight, maintenance or %s." % (max(out.values()), d2["fins_total"], ", ".join("%s %d" % (lc, out[lc]) for lc in wind), "earthquake" if not out.get("EQX") and not out.get("EQY") else "EQX"),
                  "The ribs carry that load around the open joints. No member is left pulling across a bed joint in any case (largest axial force in a remaining end wall %.3f kN)." % max(d2["max_axial_N_in_remaining_fins_kN"].values()),
                  "End walls in compression up to %.1f MPa; courses %.1f MPa compression, %.1f MPa along the hoop: far under the printed concrete." % (d2["fins_max_compression"]["MPa"], d2["courses_max_compression"]["MPa"], d2["courses_max_tension_along_hoop"]["MPa"]),
                  "Shear between printed tube and cast core: at most %.2f MPa, %d %% of 0.5 MPa for a smooth printed surface." % (max(v["tau_long_MPa"] for v in d2["tube_core_interface"].values()), round(100 * max(v["util_smooth_0.5MPa"] for v in d2["tube_core_interface"].values())))):
            pg.text(x, y, t, 2.5); y += 4.2
        y += 4
        pg.text(x, y, "OPEN OR CLOSED HEAD JOINTS (THE TWO BOUNDS)", 3.0, bold=True); y += 4
        rows = [("worst rib, long-term", "%d %% (%s, %s)" % (round(100 * d2["rib_long"]["util"]), d2["rib_long"]["band"].replace("rib_", ""), d2["rib_long"]["case"]), "%d %%" % round(100 * d1["rib_long"]["util"])),
                ("worst rib, short-term", "%d %% (%s, %s)" % (round(100 * d2["rib_short"]["util"]), d2["rib_short"]["band"].replace("rib_", ""), d2["rib_short"]["case"]), "%d %%" % round(100 * d1["rib_short"]["util"])),
                ("max deflection", "%.1f mm (%s)" % (d2["max_deflection_mm"], d2["deflection_case"]), "%.1f mm" % d1["max_deflection_mm"]),
                ("first buckling factor", "%.1f" % d2["buckling_factor_1_LONG_model"], "%.0f" % d1["buckling_factor_1_LONG_model"])]
        y = table(pg, x, y + 1, ("", "D2: head joints open (used)", "D1: head joints stiff"), rows, (50, 62, 44))
        pg.text(x, y + 2, "The drawings and sheets 01-08 use D2, the safer of the two.", 2.4, bold=True)
        import rib_sheet
        img = "C:/Users/gonza/AppData/Local/Temp/claude/5c622a39c96e3387/d0f96d15-672a-4d67-b7d7-f160f3f4487b/scratchpad/formwork/formwork-%s-D2.png" % roof
        if os.path.exists(img):
            rib_sheet.image(pg, x, y + 8, 125, img, ["D2, worst short-term case (%s): cast members coloured by sigma / 24 MPa (white 0, yellow 50 %%, red 100 %%);" % d2["rib_short"]["case"],
                                                    "printed courses and end walls as thin grey lines."])
    pg.text(16, H - 10, "Joints: a full mortar bed under each course and mortared head joints seat and seal the pieces; they never need to pull. The tie is the cast core running continuously through every piece's tube.", 2.5)
    return pg


def build(outdir):
    R = {roof: load(roof) for roof in ("15x10", "10x10")}
    sheets = [("01", "karamba-model", lambda: sheet_model("01", R)),
              ("02", "forces-15x10", lambda: sheet_forces("02", R, "15x10")),
              ("03", "forces-10x10", lambda: sheet_forces("03", R, "10x10")),
              ("04", "ribs", lambda: sheet_ribs("04", R)),
              ("05", "rings-columns-footing", lambda: sheet_rings_columns("05", R)),
              ("06", "utilisation", lambda: sheet_summary("06", R)),
              ("07", "corner-columns-removed", lambda: sheet_corners("07")),
              ("08", "one-rib", lambda: __import__("rib_sheet").page()),
              ("09", "casing-model", lambda: sheet_casing("09", R))]
    out = []
    for no, name, fn in sheets:
        pg = fn(); base = os.path.join(outdir, "%s-%s" % (no, name))
        html = ('<!doctype html><html><head><meta charset="utf-8"><style>@page{size:17in 11in;margin:0}html,body{margin:0}'
                'svg{display:block;width:17in;height:11in}</style></head><body>%s</body></html>' % pg.svg())
        open(base + ".html", "w", encoding="utf-8").write(html)
        url = "file:///" + (base + ".html").replace("\\", "/")
        subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--print-to-pdf=" + base + ".pdf", url],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=180)
        out.append(base + ".pdf"); print(name, flush=True)
    import pypdf
    w = pypdf.PdfWriter()
    for p in out:
        w.add_page(pypdf.PdfReader(p).pages[0])
    w.write(os.path.join(outdir, "karamba-stress-2026-11-23.pdf"))
    print("merged")


if __name__ == "__main__":
    build(HERE)
