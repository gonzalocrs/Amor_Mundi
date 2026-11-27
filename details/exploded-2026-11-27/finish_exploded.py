"""Completes the exploded JSONs: label anchors for every group (the hidden ones from the same parallel projection,
fitted on the visible markers), and writes elements-<roof> data with rebar as checked and the key check numbers.
Also draws a check PNG of each linework. Run with Rhino's CPython."""
import json, os, math, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
KA = os.path.join(HERE, "..", "karamba", "2026-11-27")
CEN = {"15x10": (85.0, 0.0), "10x10": (85.0, -20.0)}
EL = json.load(open(os.path.join(HERE, "elements-model.json")))
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"


def lsq(A, b):
    n = len(A[0]); N = [[sum(r[i] * r[j] for r in A) for j in range(n)] + [sum(r[i] * v for r, v in zip(A, b))] for i in range(n)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(N[r][c])); N[c], N[p] = N[p], N[c]
        for r in range(n):
            if r != c and N[c][c]:
                f = N[r][c] / N[c][c]; N[r] = [x - f * y for x, y in zip(N[r], N[c])]
    return [N[i][n] / N[i][i] if N[i][i] else 0.0 for i in range(n)]


def anchor3d(roof, g):
    e = EL[roof][g]; cx, cy = CEN[roof]
    return (cx + e["size_m"][0] / 2, cy - e["size_m"][1] / 2, (e["z_m"][0] + e["z_m"][1]) / 2 + e["lift_m"])


for roof in ("15x10", "10x10"):
    f = os.path.join(HERE, "exploded-%s.json" % roof); D = json.load(open(f))
    vis = D["anchors"]
    A = [[*anchor3d(roof, g), 1.0] for g in vis]; B = [vis[g] for g in vis]
    M = [lsq(A, [b[k] for b in B]) for k in (0, 1)]
    ap = lambda r: [round(sum(a * c for a, c in zip(r, M[k])), 4) for k in (0, 1)]
    res = max(abs(ap(r)[k] - b[k]) for r, b in zip(A, B) for k in (0, 1))
    D["anchors"] = {g: ap([*anchor3d(roof, g), 1.0]) for g, _ in D["groups"]}
    D["anchor_note"] = "label anchor = the group's south-east outer corner at mid height (fit residual %.4f m)" % res
    json.dump(D, open(f, "w"), separators=(",", ":"))
    # check drawing
    xs = [p[0] for it in D["items"] for p in it["pts"]]; ys = [p[1] for it in D["items"] for p in it["pts"]]
    x0, x1, y0, y1 = min(xs) - 1, max(xs) + 6, min(ys) - 1, max(ys) + 1
    s = 1400 / (x1 - x0); Wp, Hp = 1400, int((y1 - y0) * s)
    col = {"rectangular strip footing": "#8a6d3b", "columns": "#444", "base ring step": "#000", "rib net": "#b03a2e", "printed courses": "#777", "crown ring": "#000"}
    out = []
    for it in D["items"]:
        pts = " ".join("%.1f,%.1f" % ((p[0] - x0) * s, (y1 - p[1]) * s) for p in it["pts"])
        out.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="0.6"/>' % (pts, col.get(it["layer"], "#000")))
    for g, (ax, ay) in D["anchors"].items():
        X, Y = (ax - x0) * s, (y1 - ay) * s
        out.append('<circle cx="%.1f" cy="%.1f" r="4" fill="#1f6feb"/><text x="%.1f" y="%.1f" font-family="Arial" font-size="22" fill="#1f6feb">%s</text>' % (X, Y, X + 8, Y + 7, g))
    html = '<html><body style="margin:0;background:#fff"><svg width="%d" height="%d" style="background:#fff">%s</svg></body></html>' % (Wp, Hp, "".join(out))
    h = os.path.join(HERE, "check-exploded-%s.html" % roof); open(h, "w").write(html)
    subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--screenshot=" + h[:-5] + ".png", "--window-size=%d,%d" % (Wp, Hp), "file:///" + h.replace("\\", "/")],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
    print(roof, "anchors", D["anchors"], "residual", res)

# element data with rebar (as checked) and the key numbers from the Karamba run and the hand checks
S = json.load(open(os.path.join(KA, "corners_summary.json")))
RR = json.load(open(os.path.join(KA, "rect_result.json")))
DV = json.load(open(os.path.join(KA, "design-values-2026-11-27.json")))   # final sizes (2026-11-27)
data = {}
for roof in ("15x10", "10x10"):
    e = EL[roof]; c0 = S[roof + "|0"]; v = DV[roof]
    rib = {"15x10": [("bottom", 22, 28, "2D12"), ("middle", 16, 22, "2D10"), ("top", 12, 18, "2D8")],
           "10x10": [("bottom", 18, 24, "2D12"), ("middle", 14, 20, "2D10"), ("top", 12, 18, "2D8")]}[roof]
    data[roof] = {
        "rectangular strip footing": dict(e["rectangular strip footing"], section="%d x 500 mm strip, base -0.80, top -0.30" % (1200 if roof == "15x10" else 850),
                                          outside_m=RR[roof]["outer_m"], corner_blocks_m=RR[roof]["block_m"], rebar="D13 @ 200 both ways, to be confirmed",
                                          check="bearing %d kPa short-term (400 assumed), tipping FS %.2f, sliding FS %.2f" % (v["footing"]["bearing_kPa_short"], v["footing"]["tipping_FS_min"], v["footing"]["sliding_FS_min"])),
        "columns": dict(e["columns"], section="420 (radial) x 360 mm" if roof == "15x10" else "362 (radial) x 300 mm",
                        rebar="8D16, hoops D10 @ 100" if roof == "15x10" else "4D16, hoops D10 @ 100",
                        check="N %d to %d kN, utilisation %d %% (Fc 36)" % (round(-v["columns"]["N_kN_short"][1]), round(-v["columns"]["N_kN_short"][0]), v["columns"]["util_short"]["util_pct"])),
        "base ring step": dict(e["base ring step"], section=("cast ring 528 x 400 mm" if roof == "15x10" else "cast ring 552 x 400 mm") + " (typical width) in a 3 cm printed U formwork",
                               rebar="8D16, D10 stirrups @ 150", check="tension %s kN (typhoon), bending %s kNm, bars %d of 603 mm2 per face" % (
                                   ("%.0f" % v["base_ring"]["N_kN_short"][1], "%.1f" % v["base_ring"]["M_kNm_max"], round(c0["ring_bars"][0])))),
        "rib net": dict(e["rib net"], section=[{"band": b, "cast_core_mm": dc * 10, "printed_tube_mm": dt * 10, "rebar": r + ", to be confirmed"} for b, dc, dt, r in rib],
                        check="worst bottom band %d %% long-term (Fc 36: 12 MPa long, 24 MPa short)" % v["rib_worst_long_term"]["util_pct"],
                        note="volume = printed tubes (the cast cores sit inside them)"),
        "printed courses": dict(e["printed courses"], section="closed printed pieces, 3 cm walls, 3 cm lid, 6 x 4 cm groove for the course bar; each with its growth band",
                                check="carried by the ribs and rings; bonded bed joints (mortar pull-off test needed)"),
        "crown ring": dict(e["crown ring"], section="cast ring 250 x 250 mm in the printed top-course U formwork",
                           rebar="4D12, D8 @ 150", check="compression up to %.0f kN, %d %% (Fc 36)" % (-v["crown_ring"]["N_kN_short"][0], v["crown_ring"]["util_short"]["util_pct"])),
    }
    data[roof]["global"] = dict(weight_kN=v["weight_LONG_kN"], max_displacement_mm=c0["disp_mm"], buckling_factor=round(c0["buckling"], 1))
json.dump(data, open(os.path.join(HERE, "elements-data.json"), "w"), indent=1)
print("elements-data.json written")
