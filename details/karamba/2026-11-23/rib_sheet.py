"""Sheet 08 of the Karamba stress set: one rib of the 15x10 roof from the base ring to the crown, in the layout of the
midterm page 06 (free body, moment along the rib, capacity vs demand, stress across the section, Karamba picture).
Input rib-path/rib-path-15x10.json (rib_path.py, from the Karamba forces of the saved 2 m canvas). The rib is branched,
so the free body is drawn on the developed rib (unrolled into its own vertical plane) and every branch that leaves it
is shown as the force it puts into the path at that Y-joint. Writes 08-one-rib.pdf/.png and appends page 08 to
karamba-stress-2026-11-23.pdf (saved as karamba-stress-2026-11-23-with-rib.pdf)."""
import os, sys, json, math, base64, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", ".."))
import stress_pdf as s
from press_sheets import W, H, EDGE
P = json.load(open(os.path.join(HERE, "rib-path", "rib-path-15x10.json")))
NET = r"C:\Users\gonza\AppData\Local\Temp\claude\5c622a39c96e3387\d0f96d15-672a-4d67-b7d7-f160f3f4487b\scratchpad\ribpath\rib-path-15x10-net.png"
RED, BLUE, GREY = "#b03a2e", "#2c5aa0", "#555"
FS_L, FS_S, COVER = 215.0, 345.0, 40.0      # SD345 allowable steel stress (MPa) long / short; cover to bar centre (mm)


def developed():
    nodes = P["nodes"]; u = [0.0]; tang = []
    for k in range(1, len(nodes)):
        a, b = nodes[k - 1]["xyz"], nodes[k]["xyz"]; d = math.hypot(b[0] - a[0], b[1] - a[1]); u.append(u[-1] + d)
    for k in range(len(nodes)):
        a = nodes[max(k - 1, 0)]["xyz"]; b = nodes[min(k + 1, len(nodes) - 1)]["xyz"]
        dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy) or 1; tang.append((dx / L, dy / L))
    return u, [n["xyz"][2] for n in nodes], tang


def bar_M(b, lc):
    """(s_from, s_to, N_from, N_to, M_from, M_to) with M = sqrt(My2+Mz2), in path order"""
    e0, e1 = b["cases"][lc]["ends"]
    if e0["node"] != b["from_node"]: e0, e1 = e1, e0
    return e0, e1


def fbd(pg, x, y, w, h):
    pg.text(x, y, "FREE BODY OF THE RIB, DEVELOPED, LONG (kN)", 3.0, bold=True)
    u, z, tang = developed()
    sc = min(w / (u[-1] + 3.0), h / (z[-1] - z[0] + 1.0))
    X = lambda uu: x + 14 + uu * sc; Y = lambda zz: y + 6 + h - (zz - z[0] + 0.3) * sc
    nodes = P["nodes"]; bars = P["bars"]
    for k, b in enumerate(bars):
        wdt = {"bottom": 1.6, "middle": 1.2, "top": 0.85}[b["band"]]
        pg.line(X(u[k]), Y(z[k]), X(u[k + 1]), Y(z[k + 1]), wdt)
    fsc = 0.45                                                     # mm per kN
    course = 0.0
    for k, n in enumerate(nodes):
        tx, ty = tang[k]
        for key, f in n["delivered"]["LONG"].items():
            F = f["F_kN"]; fh = F[0] * tx + F[1] * ty; fv = F[2]       # in the developed plane: along the rib in plan, and up
            if key == "course":
                course += fv
                pg.o.append('<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="#888" stroke-width="0.2"/>' % (X(u[k]), Y(z[k]) - 5, X(u[k]), Y(z[k]) - 1))
                s.arrow(pg, X(u[k]), Y(z[k]) - 5, X(u[k]), Y(z[k]) - 0.8, 0.2, "#888")
            elif key == "branch_rib" and 0 < k < len(nodes) - 1:
                L = math.hypot(fh, fv)
                if L < 0.5: continue
                x2, y2 = X(u[k]), Y(z[k]); x1, y1 = x2 - fh * fsc * 2, y2 + fv * fsc * 2
                s.arrow(pg, x1, y1, x2, y2, 0.45, BLUE)
                lx = X(u[k]) - 16                                    # labels in a column left of the rib, with a leader
                pg.line(lx + 0.8, y2, x2 - 1.4, y2, 0.12, "#9ab")
                pg.text(lx, y2 + 0.8, "%.1f" % L, 2.2, anchor="end", color=BLUE)
        if n["y_joint"]:
            pg.o.append('<circle cx="%.2f" cy="%.2f" r="1.1" fill="white" stroke="#000" stroke-width="0.35"/>' % (X(u[k]), Y(z[k])))
    # foot: base ring + column + the branch that starts at the foot
    f0 = P["nodes"][0]["delivered"]["LONG"]; tx, ty = tang[0]
    tot = [sum(v["F_kN"][i] for kk, v in f0.items() if kk in ("ring", "column")) for i in range(3)]
    br = f0.get("branch_rib", {"F_kN": [0, 0, 0]})["F_kN"]
    fh, fv = tot[0] * tx + tot[1] * ty, tot[2]
    x0, y0 = X(u[0]), Y(z[0])
    s.arrow(pg, x0, y0 + 16, x0, y0 + 0.8, 0.6); pg.text(x0 + 2, y0 + 14, "V %.1f up (ring + column)" % fv, 2.3)
    s.arrow(pg, x0 - 14 * (1 if fh > 0 else -1), y0, x0, y0, 0.6, RED)
    pg.text(x0 - 15, y0 + 4, "H %.1f %s" % (abs(fh), "in" if fh > 0 else "out"), 2.3, color=RED)
    pg.text(x0 + 2, y0 + 17.5, "branch rib at the foot: %.1f along, %.1f vertical" % (br[0] * tx + br[1] * ty, br[2]), 2.1, italic=True)
    fc = P["nodes"][-1]["delivered"]["LONG"]["crown"]["F_kN"]; tx, ty = tang[-1]
    xc, yc = X(u[-1]), Y(z[-1])
    pg.text(xc + 3, yc - 3, "crown ring: %.1f along, %.1f vertical" % (fc[0] * tx + fc[1] * ty, fc[2]), 2.3, color=BLUE)
    pg.text(xc + 3, yc + 0.5, "+%.2f" % z[-1], 2.1, italic=True)
    pg.text(x0 - 15, y0 + 7.6, "+%.2f base ring" % z[0], 2.1, italic=True)
    pg.text(X(u[len(u) // 2]) + 10, Y(z[len(z) // 2]) + 6, "courses: %.1f kN down in total (grey)" % course, 2.3, color="#666")
    pg.text(X(u[len(u) // 2]) + 10, Y(z[len(z) // 2]) + 9.5, "branches leaving the path at Y-joints (blue, kN)", 2.3, color=BLUE)
    pg.text(X(u[len(u) // 2]) + 10, Y(z[len(z) // 2]) + 13, "own weight of the cores %.1f kN" % P["rib_self_weight_total_kN"], 2.3, color="#666")
    pg.text(x, y + h + 30, "Developed: horizontal = distance along the rib in plan, vertical = height. Forces projected into that plane; the", 2.2, italic=True)
    pg.text(x, y + h + 33.2, "out-of-plane parts (towards the room) are in the json. Arrows on the path: what the other members put into it.", 2.2, italic=True)


def along(pg, x, y, w, h):
    pg.text(x, y, "M ALONG THE RIB, |M| = sqrt(My2 + Mz2)", 3.0, bold=True)
    y0 = y + 6; L = P["path_length_m"]
    mmax = max(max(e0_e1) for b in P["bars"] for lc in ("LONG", "W-Y") for e0_e1 in [[math.hypot(e["My"], e["Mz"]) for e in b["cases"][lc]["ends"]]])
    mmax = math.ceil(mmax / 2) * 2
    Xm = lambda m: x + 6 + (w - 8) * m / mmax; Ys = lambda ss: y0 + h - h * ss / L
    pg.line(Xm(0), y0, Xm(0), y0 + h, 0.3)
    poly = {"LONG": [], "W-Y": []}
    for lc in poly:
        for b in P["bars"]:
            e0, e1 = bar_M(b, lc); s0 = P["nodes"][b["index"]]["s_m"]; s1 = P["nodes"][b["index"] + 1]["s_m"]
            poly[lc] += [(math.hypot(e0["My"], e0["Mz"]), s0), (math.hypot(e1["My"], e1["Mz"]), s1)]
    pts = " ".join("%.2f,%.2f" % (Xm(m), Ys(ss)) for m, ss in poly["LONG"])
    pg.o.append('<polygon points="%.2f,%.2f %s %.2f,%.2f" fill="#ccc" stroke="#555" stroke-width="0.25"/>' % (Xm(0), Ys(0), pts, Xm(0), Ys(L)))
    pg.o.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="0.45"/>' % (" ".join("%.2f,%.2f" % (Xm(m), Ys(ss)) for m, ss in poly["W-Y"]), RED))
    for k in range(0, int(mmax) + 1, 2 if mmax <= 14 else 4):
        pg.line(Xm(k), y0 + h, Xm(k), y0 + h + 1, 0.2); pg.text(Xm(k), y0 + h + 4, str(k), 2.1, anchor="middle")
    pg.text(x + w, y0 + h + 7.5, "kNm", 2.2, anchor="end")
    for n in P["nodes"]:
        if n["y_joint"]:
            pg.line(Xm(0) - 1.5, Ys(n["s_m"]), Xm(mmax), Ys(n["s_m"]), 0.12, "#bbb")
    for band in ("bottom", "middle", "top"):
        ss = [P["nodes"][b["index"]]["s_m"] for b in P["bars"] if b["band"] == band]
        pg.text(Xm(0) - 1, Ys((min(ss) + max(ss) + 0.5) / 2), band, 2.1, anchor="end", color="#666")
    m0l = math.hypot(*[bar_M(P["bars"][0], "LONG")[0][k] for k in ("My", "Mz")]); m0s = math.hypot(*[bar_M(P["bars"][0], "W-Y")[0][k] for k in ("My", "Mz")])
    pg.text(Xm(m0s) + 1.5, Ys(0) - 9, "foot: %.1f LONG," % m0l, 2.3, anchor="end", bold=True)
    pg.text(Xm(m0s) + 1.5, Ys(0) - 5.5, "%.1f W-Y" % m0s, 2.3, anchor="end", bold=True, color=RED)
    pg.text(x + w - 26, y0 + 3, "grey: LONG", 2.2, color=GREY); pg.text(x + w - 26, y0 + 6.5, "red: typhoon W-Y", 2.2, color=RED)
    pg.text(x + w - 26, y0 + 10, "thin lines: Y-joints", 2.2, color="#999")
    pg.text(x, y0 + h + 12, "Values from Karamba at every bar end of the path.", 2.2, italic=True)


def capacity(pg, x, y, w, h):
    pg.text(x, y, "CAPACITY vs DEMAND, |M|", 3.0, bold=True)
    y0 = y + 6; L = P["path_length_m"]
    rows = []
    for b in P["bars"]:
        dm = b["core_D_mm"] / 1000.0; A = math.pi * dm * dm / 4; Wm = math.pi * dm ** 3 / 32
        for t, key in ((0, "from_node"), (1, "to_node")):
            ss = P["nodes"][b["index"] + t]["s_m"]
            el = bar_M(b, "LONG")[t]; es = bar_M(b, "W-Y")[t]
            capl = max(0.0, (12.0 - (-el["N"] / A / 1000.0)) * Wm * 1000)        # kNm, concrete fibre at 12 MPa with the actual N
            caps = max(0.0, (24.0 - (-es["N"] / A / 1000.0)) * Wm * 1000)
            rows.append((ss, capl, caps, math.hypot(el["My"], el["Mz"]), math.hypot(es["My"], es["Mz"])))
    mmax = math.ceil(max(r[2] for r in rows) / 5) * 5
    Xm = lambda m: x + 6 + (w - 8) * m / mmax; Ys = lambda ss: y0 + h - h * ss / L
    pg.line(Xm(0), y0, Xm(0), y0 + h, 0.3)
    pg.o.append('<polyline points="%s" fill="none" stroke="#000" stroke-width="0.45"/>' % " ".join("%.2f,%.2f" % (Xm(r[2]), Ys(r[0])) for r in rows))
    pg.o.append('<polyline points="%s" fill="none" stroke="#000" stroke-width="0.45" stroke-dasharray="2,1.2"/>' % " ".join("%.2f,%.2f" % (Xm(r[1]), Ys(r[0])) for r in rows))
    pg.o.append('<polygon points="%.2f,%.2f %s %.2f,%.2f" fill="#ccc" stroke="#555" stroke-width="0.25"/>' % (Xm(0), Ys(0), " ".join("%.2f,%.2f" % (Xm(r[3]), Ys(r[0])) for r in rows), Xm(0), Ys(L)))
    pg.o.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="0.4"/>' % (" ".join("%.2f,%.2f" % (Xm(r[4]), Ys(r[0])) for r in rows), RED))
    for k in range(0, int(mmax) + 1, 5):
        pg.line(Xm(k), y0 + h, Xm(k), y0 + h + 1, 0.2); pg.text(Xm(k), y0 + h + 4, str(k), 2.1, anchor="middle")
    pg.text(x + w, y0 + h + 7.5, "kNm", 2.2, anchor="end")
    r0 = rows[0]
    pg.o.append('<circle cx="%.2f" cy="%.2f" r="0.9" fill="#000"/><circle cx="%.2f" cy="%.2f" r="0.9" fill="%s"/>' % (Xm(r0[3]), Ys(0), Xm(r0[4]), Ys(0), RED))
    pg.text(Xm(r0[4]) + 4, Ys(0) - 9, "LONG %.1f = %d %%" % (r0[3], round(100 * P["bars"][0]["cases"]["LONG"]["utilisation"])), 2.3, bold=True)
    pg.text(Xm(r0[4]) + 4, Ys(0) - 5.5, "W-Y %.1f = %d %%" % (r0[4], round(100 * P["bars"][0]["cases"]["W-Y"]["utilisation"])), 2.3, bold=True, color=RED)
    lx = x + w - 34
    pg.line(lx, y0 + 2, lx + 6, y0 + 2, 0.45); pg.text(lx + 7, y0 + 3, "capacity SHORT (24 MPa)", 2.1)
    pg.o.append('<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="#000" stroke-width="0.45" stroke-dasharray="2,1.2"/>' % (lx, y0 + 6, lx + 6, y0 + 6)); pg.text(lx + 7, y0 + 7, "capacity LONG (12 MPa)", 2.1)
    pg.o.append('<rect x="%.2f" y="%.2f" width="6" height="2" fill="#ccc"/>' % (lx, y0 + 9)); pg.text(lx + 7, y0 + 11, "demand LONG", 2.1)
    pg.line(lx, y0 + 14, lx + 6, y0 + 14, 0.4, RED); pg.text(lx + 7, y0 + 15, "demand W-Y", 2.1)
    pg.text(x, y0 + h + 12, "Capacity = (allowable - N/A) x W of the core, with the bar's own N;", 2.2, italic=True)
    pg.text(x, y0 + h + 15.2, "the step at each band change is the core going D220 -> D160 -> D120.", 2.2, italic=True)


def section(pg, x, y):
    b = P["bars"][0]; dm = b["core_D_mm"]; A = math.pi * dm * dm / 4.0; Wm = math.pi * dm ** 3 / 32.0
    pg.text(x, y, "STRESS ACROSS THE RIB FOOT, CORE D%d, MPa (+ COMPRESSION, - TENSION)" % dm, 3.0, bold=True)
    yy = y + 8
    for lc, al, fs in (("LONG", 12.0, FS_L), ("W-Y", 24.0, FS_S)):
        e = bar_M(b, lc)[0]; M = math.hypot(e["My"], e["Mz"]); na = -e["N"] * 1000 / A; mw = M * 1e6 / Wm
        r = 8; cx, cy = x + 10, yy + 9
        pg.o.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="url(#conc)" stroke="#000" stroke-width="0.35"/>' % (cx, cy, r))
        pg.o.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="none" stroke="#000" stroke-width="0.2" stroke-dasharray="1,0.8"/>' % (cx, cy, r + 2.2))
        for k in range(6):
            a = 2 * math.pi * k / 6; pg.o.append('<circle cx="%.2f" cy="%.2f" r="0.75" fill="#000"/>' % (cx + (r - 2.2) * math.cos(a), cy + (r - 2.2) * math.sin(a)))
        pg.text(cx, cy + r + 6, "%s" % lc, 2.4, anchor="middle", bold=True)
        sc = 0.9; base = cy + 2; x1 = x + 32
        pg.line(x1, base, x1 + 20, base, 0.2)
        pg.o.append('<rect x="%.2f" y="%.2f" width="20" height="%.2f" fill="url(#conc)" stroke="#000" stroke-width="0.25"/>' % (x1, base - na * sc, na * sc))
        pg.text(x1, base - na * sc - 1.2, "%.2f" % na, 2.0); pg.text(x1 + 10, base + 4, "N/A = %.1f kN / %.0f mm2" % (-e["N"], A), 2.0, anchor="middle")
        pg.text(x1 + 25, base - 1, "+", 3.0)
        x2 = x1 + 32
        pg.o.append('<polygon points="%.2f,%.2f %.2f,%.2f %.2f,%.2f %.2f,%.2f" fill="url(#conc)" stroke="#000" stroke-width="0.25"/>' % (x2, base, x2, base + mw * sc * 0.5, x2 + 24, base - mw * sc * 0.5, x2 + 24, base))
        pg.line(x2, base, x2 + 24, base, 0.2)
        pg.text(x2 + 24, base - mw * sc * 0.5 - 1, "%.2f" % mw, 2.0, anchor="end"); pg.text(x2, base + mw * sc * 0.5 + 3, "-%.2f" % mw, 2.0)
        pg.text(x2 + 12, base + mw * sc * 0.5 + 6.5, "M/W = %.1f kNm / %.2f x 10^6 mm3" % (M, Wm / 1e6), 2.0, anchor="middle")
        pg.text(x2 + 29, base - 1, "=", 3.0)
        x3 = x2 + 36; top = na + mw; bot = na - mw
        pg.o.append('<polygon points="%.2f,%.2f %.2f,%.2f %.2f,%.2f %.2f,%.2f" fill="url(#conc)" stroke="#000" stroke-width="0.25"/>' % (x3, base, x3, base - bot * sc * 0.5, x3 + 24, base - top * sc * 0.5, x3 + 24, base))
        pg.line(x3, base, x3 + 24, base, 0.2)
        pg.text(x3 + 24, base - top * sc * 0.5 - 1, "%.2f" % top, 2.0, anchor="end", bold=True); pg.text(x3, base - bot * sc * 0.5 + 3, "%.2f" % bot, 2.0, bold=True)
        pg.text(x3 + 12, base - bot * sc * 0.5 + 7, "together: %d %% of %d MPa" % (round(100 * top / al), al), 2.0, anchor="middle")
        d = dm - COVER; As = M * 1e6 / (0.875 * d * fs)
        pg.text(x3 + 34, base - 6, "Tension face %.1f MPa: as plain concrete it would crack (about 2.6 MPa)." % abs(bot), 2.3)
        pg.text(x3 + 34, base - 2.5, "Bars: As = M / (0.875 d fs) = %.1f x10^6 / (0.875 x %d x %d) = %.0f mm2 per face." % (M, d, fs, As), 2.3)
        pg.text(x3 + 34, base + 1, "%s" % ("2-D13 (254 mm2) on each face: 6-D13 around the core, wind can come from any side." if As <= 254 else "2-D16 (398 mm2) on each face: 6-D16 around the core."), 2.3)
        yy += 25


def image(pg, x, y, w, path, cap):
    b64 = base64.b64encode(open(path, "rb").read()).decode()
    hh = w * 2000 / 3200
    pg.o.append('<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" fill="none" stroke="#000" stroke-width="0.25"/>' % (x, y, w, hh))
    pg.o.append('<image x="%.2f" y="%.2f" width="%.2f" height="%.2f" href="data:image/png;base64,%s"/>' % (x, y, w, hh, b64))
    yy = y + hh + 4
    for line in cap:
        pg.text(x, yy, line, 2.3, italic=True); yy += 3.4


def page():
    pg = s.Page("08", "One rib, base ring to crown (15x10)", "The bottom-band rib bar with the highest stress, followed up to the crown ring; at each Y-joint the straighter branch is kept and the other one becomes a force on the path. Karamba forces of the 2 m design model D2 (casing tied to the ribs, bed joints compression-only, sheet 09), checked by hand: sigma = N/A + M/W.")
    pg.header()
    fbd(pg, 16, 62, 125, 104)
    along(pg, 160, 62, 70, 130)
    capacity(pg, 246, 62, 72, 130)
    image(pg, 330, 66, 92, NET, ["The analysed rib (red) in the 15x10 rib net, from the", "SW. Foot on the north long side at (85.0, 4.8, +2.40),", "crown at +11.90; 26 bars, 10.77 m, 6 Y-joints."])
    tab = [("bottom", "D220", "8"), ("middle", "D160", "8"), ("top", "D120", "10")]
    yy = 140
    pg.text(330, yy, "THE PATH", 3.0, bold=True); yy += 5
    for band, d, n in tab:
        bb = [b for b in P["bars"] if b["band"] == band]
        ul = max(b["cases"]["LONG"]["utilisation"] for b in bb); us = max(b["cases"]["W-Y"]["utilisation"] for b in bb)
        pg.text(330, yy, "%s band, core %s, %s bars: max %d %% LONG, %d %% W-Y" % (band, d, n, round(100 * ul), round(100 * us)), 2.4); yy += 4
    pg.text(330, yy + 2, "Local axes: z = out of the roof plane (room side), y in the", 2.3, italic=True)
    pg.text(330, yy + 5.4, "roof surface. My is out-of-plane bending, Mz in-plane.", 2.3, italic=True)
    pg.line(16, 207, W - 16, 207, 0.2)
    section(pg, 16, 212)
    return pg


def build():
    pg = page()
    base = os.path.join(HERE, "08-one-rib")
    html = ('<!doctype html><html><head><meta charset="utf-8"><style>@page{size:17in 11in;margin:0}html,body{margin:0}'
            'svg{display:block;width:17in;height:11in}</style></head><body>%s</body></html>' % pg.svg())
    open(base + ".html", "w", encoding="utf-8").write(html)
    url = "file:///" + (base + ".html").replace("\\", "/")
    subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--print-to-pdf=" + base + ".pdf", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=180)
    subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--window-size=1632,1056", "--force-device-scale-factor=2", "--screenshot=" + base + ".png", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=180)
    import pypdf
    w = pypdf.PdfWriter()
    for p in pypdf.PdfReader(os.path.join(HERE, "karamba-stress-2026-11-23.pdf")).pages: w.add_page(p)
    w.add_page(pypdf.PdfReader(base + ".pdf").pages[0])
    w.write(os.path.join(HERE, "karamba-stress-2026-11-23-with-rib.pdf"))
    print("ok", base)


if __name__ == "__main__":
    build()
