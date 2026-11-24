"""Option A (Gonzalo 2026-11-23): 36x36 columns (15x10, 20) / 30x30 (10x10, 16) at the Karamba support stations,
centred under the base ring step, on pads 1.8 / 1.4 x 0.5 (base -0.80, top -0.30). Pads that touch or nearly touch
(gap < 0.15 m) are cast as one combined footing (bounding rectangle along the line between the two columns).
Writes pads_layout.json for the GH canvas (planes and half-sizes)."""
import json, math
HERE = r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\details\karamba\2026-11-23"
M = json.load(open(HERE + r"\model_columns.json"))
SPEC = {"15x10": dict(col=0.36, pad=1.8, missing=(91.4253, 4.2024, 55.3)),
        "10x10": dict(col=0.30, pad=1.4, missing=(89.2633, -15.7367, 45.0))}
def corners(cx, cy, ang, a, b):
    t = math.radians(ang); ux, uy = math.cos(t), math.sin(t); vx, vy = -uy, ux
    return [(cx + sx * a * ux + sy * b * vx, cy + sx * a * uy + sy * b * vy) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
def sat_gap(P, Q):
    """separating-axis gap between two convex polygons (negative = overlap)"""
    best = -1e9
    for poly in (P, Q):
        for i in range(len(poly)):
            x1, y1 = poly[i]; x2, y2 = poly[(i + 1) % len(poly)]
            nx, ny = y2 - y1, x1 - x2; L = math.hypot(nx, ny); nx, ny = nx / L, ny / L
            pa = [x * nx + y * ny for x, y in P]; qa = [x * nx + y * ny for x, y in Q]
            best = max(best, max(min(qa) - max(pa), min(pa) - max(qa)))
    return best
out = {}
for roof, s in SPEC.items():
    cols = []
    for (x, y, n, lens) in M[roof]:
        ang = max(lens)[1]                       # long (depth) edge = across the ring step
        cols.append((x, y, ang))
    cols.append(s["missing"])
    cen = (85.0, 0.0) if roof == "15x10" else (85.0, -20.0)
    cols.sort(key=lambda c: math.atan2(c[1] - cen[1], c[0] - cen[0]))
    h = s["pad"] / 2
    pads = [corners(x, y, a, h, h) for x, y, a in cols]
    n = len(cols); pairs = []
    for i in range(n):
        j = (i + 1) % n; g = sat_gap(pads[i], pads[j])
        if g < 0.15: pairs.append((i, j, round(g, 3)))
    used = set(); footings = []
    for i, j, g in pairs:
        (x1, y1, _), (x2, y2, _) = cols[i], cols[j]
        ang = math.degrees(math.atan2(y2 - y1, x2 - x1)); t = math.radians(ang)
        ux, uy, vx, vy = math.cos(t), math.sin(t), -math.sin(t), math.cos(t)
        pts = pads[i] + pads[j]
        us = [px * ux + py * uy for px, py in pts]; vs = [px * vx + py * vy for px, py in pts]
        cu, cv = (min(us) + max(us)) / 2, (min(vs) + max(vs)) / 2
        footings.append(dict(cx=cu * ux + cv * vx, cy=cu * uy + cv * vy, ang=ang, hx=(max(us) - min(us)) / 2, hy=(max(vs) - min(vs)) / 2, cols=[i, j], gap=g))
        used |= {i, j}
    for i, (x, y, a) in enumerate(cols):
        if i not in used: footings.append(dict(cx=x, cy=y, ang=a, hx=h, hy=h, cols=[i], gap=None))
    out[roof] = dict(cols=[dict(cx=x, cy=y, ang=a, h=s["col"] / 2) for x, y, a in cols], footings=footings, pairs=pairs)
    print(roof, len(cols), "columns,", len(footings), "footings; combined pairs:", pairs)
    for f in footings:
        if len(f["cols"]) > 1: print("   combined %.2f x %.2f at (%.2f, %.2f) %.1f deg" % (2 * f["hx"], 2 * f["hy"], f["cx"], f["cy"], f["ang"]))
json.dump(out, open(HERE + r"\pads_layout.json", "w"), indent=1)
