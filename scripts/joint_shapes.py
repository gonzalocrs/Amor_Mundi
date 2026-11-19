"""Whole joint printed as one piece: rib + ring + node in one upright print, tested with rectangular, oval and circular
channels

Gonzalo, after option B (separate post) was dropped because a small printed part would not survive the pour: "maybe i
can print the whole joint as one piece?", then "test with rectangular, oval and circular ribs/rings".

The RING COURSE PIECE prints like the column piece in scripts/piece_test.py: upright, s (up the slope) vertical, so
print (x, y, z) = (u, n, s). The rib channel is then a vertical tube (any plan shape prints, no overhang). The ring
channel runs along u, a HORIZONTAL tunnel in the print, so its top is an overhang. Rule used: each layer may step
at most 7 mm over the one below (35 deg from vertical at 10 mm layers; the limit Akbarzadeh / PSL print to, Diamanti
2024). Where the shape is steeper than that (the flat top of the rectangle, the crown of the circle and the oval) the
tunnel closes at 35 deg instead: a pointed, "gothic" crown, as in corbelled vaults (Mycenaean tholoi, Cork House
2019) and the teardrop holes used for horizontal ducts in printed parts. The pointed crown also points up the slope
on the roof, so it is the high point where air collects when the ring is cast: put the vent there.

The ring sits at the bottom of the piece: 3 floor layers on the bed, the tunnel, its crown, then plain shell. The
column channel runs through all of it, so the node is one monolithic print with no small parts, and one pour from
the top of the column fills the column, the node and the ring.

Same depth for all three shapes (160 clear in n, so the downstand stays 160 below the room face); the oval is 220 long
in the other direction (u for the rib, s for the ring). Bars 4 x D12 per channel, 40 clear cover. Ring bars run along
u and column bars along s, so at the node they cross in planes of constant n: they must sit at different n (at least
one bar diameter apart, touching is allowed as in any mesh). The script places both cages to make that work.

Pure Python + shapely; `python scripts/joint_shapes.py` prints the comparison and writes details/piece-test/
joint-shapes.png and joint-shapes.json (data for the 3D view).
"""
import json
import math
import os

from shapely.affinity import scale
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import linemerge, unary_union

P = dict(L=1200.0, H=450.0, uc=600.0, bead=30.0, lh=10.0, speed=100.0, density=2.3, bar=12.0, cover=40.0,
         depth=160.0, width=160.0, oval=220.0, floor=30.0, step=7.0, dg=16.0,
         ring_d=250.0, ring_h=250.0, fillet=100.0, fill=True)              # middle rings, Karamba 2026-10-19
SHAPES = ("rect", "oval", "circle")
NAMES = dict(rect="Rectangular", oval="Oval", circle="Circular")

# shell build-up (same as piece_test.Section)
B = P["bead"]
nA, nB, c0, c1, T = B / 2, 1.5 * B, 2 * B, 2 * B + 120, 4 * B + 120
nO1, nO2 = T - B / 2, T - 1.5 * B
TOP, BOT = B, B - P["depth"]                    # channel clear, n from -130 to 30
NC = (TOP + BOT) / 2                            # channel centre n = -50


def _profile(shape, cx, cy, along):
    """channel clear shape centred at (cx, cy); `along` is its size in the first axis, depth in the second"""
    d = P["depth"]
    if shape == "rect":
        return box(cx - along / 2, cy - d / 2, cx + along / 2, cy + d / 2)
    if shape == "circle":
        return Point(cx, cy).buffer(d / 2, 128)
    return scale(Point(cx, cy).buffer(1.0, 128), P["oval"] / 2, d / 2)


def col_void(shape):
    """rib channel in plan (u, n)"""
    w = P["width"] if shape != "oval" else P["oval"]
    return _profile(shape, P["uc"], NC, w)


RN = TOP - P["ring_d"] / 2                      # ring channel centre n: its shell-side face stays at bead B


def ring_target(shape):
    """ring channel in section (n, s). Oval: the middle rings from Karamba (2026-10-19, 250 x 250), so ring_d deep
    in n and ring_h tall in s, its shell-side face at n = 30; the other shapes keep the first study's sizes"""
    if shape == "oval":
        return scale(Point(RN, P["floor"] + P["ring_h"] / 2).buffer(1.0, 128), P["ring_d"] / 2, P["ring_h"] / 2)
    h = P["width"]
    return Polygon([(y + NC, x + P["floor"] + h / 2) for x, y in _profile(shape, 0, 0, h).exterior.coords])


def _wave(u0, u1, n0, n1, pitch=400.0, step=10.0):
    span = abs(u1 - u0)
    k = max(1, int(round(span / (pitch / 2.0))))
    if k % 2 == 0:
        k += 1 if span / (pitch / 2.0) > k else -1
    m = max(2, int(math.ceil(span / step)))
    return [(u0 + (u1 - u0) * i / m, n0 + (n1 - n0) * (0.5 - 0.5 * math.cos(math.pi * k * i / m))) for i in range(m + 1)]


def _fillet_line(line, r):
    """round the sharp room-side corners where a line along n = nA turns down round the channel: close the region
    above it by r (fills the narrow wedges below it) and read the line back off its edge"""
    L, h = P["L"], B / 2
    q = Polygon([(-500, nA)] + line + [(L + 500, nA), (L + 500, 2000), (-500, 2000)])
    q = q.buffer(r, 64).buffer(-r, 64)
    ring = list(q.exterior.coords)[:-1]
    k = max(range(len(ring)), key=lambda i: ring[i][1])          # start the walk on the top edge
    ring = ring[k:] + ring[:k]
    out = [p for p in ring if p[1] < 1000 and h <= p[0] <= L - h]
    return out if out[0][0] < out[-1][0] else out[::-1]


def shell_layer(shape, nb=nB, no2=nO2, w0=c0, w1=c1, fillet=None, cv=None):
    """the column piece's single path (Gonzalo's sketch) with the U drawn round the rib shape; returns path, polygon.
    nb, no2, w0, w1 move bead B, bead O2 and the web's two edges (the tendon ducts open grooves this way);
    fillet rounds the U into bead A with that centreline radius (mm), so the rib grows out of the wall; cv replaces the
    rib channel (a polygon in u, n; the tapered column of scripts/joint_tapered.py)"""
    L, h = P["L"], B / 2
    cv = col_void(shape) if cv is None else cv
    ring = cv.buffer(h, 64).exterior                        # bead centreline round the channel
    cut = ring.intersection(box(-1, -1e4, L + 1, nA))       # the part below bead A
    cut = linemerge(cut) if cut.geom_type == "MultiLineString" else cut   # the ring may start inside the U
    seg = max(getattr(cut, "geoms", [cut]), key=lambda g: g.length)
    U = list(seg.coords)
    if U[0][0] > U[-1][0]:
        U.reverse()
    run = [(U[0][0], nA)] + U + [(U[-1][0], nA)]
    fillet = P["fillet"] if fillet is None else fillet
    if fillet:
        run = _fillet_line(run, fillet)
    path = ([(h, nb), (h, nA)] + run + [(L - h, nA), (L - h, nO1), (h, nO1), (h, nb),
            (L - B, nb)] + _wave(L - B - h, B + h, w0, w1) + [(B, no2), (L - B, no2)])
    poly = LineString(path).buffer(h, cap_style=2, join_style=2).union(box(0, 0, L, B)).difference(cv)
    return path, poly


def ring_void(shape):
    """printable tunnel: n interval (lo, hi) per layer, or None. Faces may step <= 7 mm per layer over the void"""
    tgt, lh, st = ring_target(shape), P["lh"], P["step"]
    n = int(round(P["H"] / lh))
    out, prev = [], None
    for i in range(n):
        s = (i + 0.5) * lh
        cut = tgt.intersection(LineString([(-1e3, s), (1e3, s)]))
        t = cut.bounds if not cut.is_empty else None
        if prev is None:
            cur = (t[0], t[2]) if t else None
        else:
            lo, hi = prev[0] + st, prev[1] - st             # the most the faces can close this layer
            if t:
                lo, hi = min(lo, t[0]), max(hi, t[2])
            cur = (lo, hi) if hi - lo > 1.0 else None
        out.append(cur)
        prev = cur
        if prev is None and i > 0 and out[i - 1] is not None:
            prev = None
    # the crown: once closed it stays closed
    seen = False
    for i, v in enumerate(out):
        if v:
            seen = True
        elif seen:
            out[i:] = [None] * (n - i)
            break
    return out


def ring_outer(voids):
    """room face of the downstand (n) per layer: 1 bead outside the tunnel, never undercut by more than 7 mm a layer,
    vertical down to the bed under the tunnel"""
    n = len(voids)
    last = max(i for i, v in enumerate(voids) if v)
    m = [None] * n
    for i in range(last, -1, -1):
        raw = voids[i][0] - B if voids[i] else None
        below = m[i + 1] if i < last else None
        if raw is None:
            m[i] = below
        elif below is None:
            m[i] = raw
        else:
            m[i] = min(raw, below + P["step"])
    return m


def layers(shape, closed=False, cage=None):
    """print layers in (u, n). closed: a version that can be poured on its own (test pour, bottom course): the column
    hole is capped by the floor layers and the tunnel by a bead at each end, with holes for the bars"""
    L, hole = P["L"], P["bar"] / 2 + 4
    lh = P["lh"]
    path, shell = shell_layer(shape, fillet=0)   # the joint keeps the plain U: a fillet adds contours round the ring
    cv = col_void(shape)
    voids = ring_void(shape)
    outer = ring_outer(voids)
    if P["fill"]:                               # above the crown the band runs on flat to the piece's top, so the
        top = max(i for i, m in enumerate(outer) if m is not None)      # flared column piece above lands on it
        outer[top + 1:] = [outer[top]] * (len(outer) - top - 1)          # (Gonzalo, 2026-10-19)
    out = []
    for i, (v, m) in enumerate(zip(voids, outer)):
        g = shell
        if m is not None:
            g = g.union(box(0, m, L, nB + B / 2))
        s = (i + 0.5) * lh
        if v and not closed:
            g = g.difference(box(-1, v[0], L + 1, v[1]))
        elif v:
            g = g.difference(box(B, v[0], L - B, v[1]))
            for n, bs in cage["ring"]:                  # bar holes in the end caps, teardrop: 20 wide, 6, closed
                w = 2 * hole if s <= bs + 1 else (6.0 if s <= bs + 1 + lh else 0)
                if w and s >= bs - hole:
                    for u0 in (-1, L - B):
                        g = g.difference(box(u0, n - w / 2, u0 + B + 1, n + w / 2))
        if closed and s < P["floor"]:
            g = g.difference(unary_union([Point(u, n).buffer(hole, 32) for u, n in cage["col"]]))
        else:
            g = g.difference(cv)
        g = g.buffer(0)
        out.append(dict(i=i, s=(i + 0.5) * P["lh"], void=v, outer=m, geom=g))
    return out, path


def _overhang(a, b):
    """how far layer b reaches past layer a below it (mm)"""
    d = b.difference(a)
    if d.is_empty or d.area < 1.0:
        return 0.0
    worst = 0.0
    for g in getattr(d, "geoms", [d]):
        for q in g.exterior.coords:
            worst = max(worst, a.distance(Point(q)))
    return worst


def _inside(poly, q, c):
    return poly.contains(Point(q)) and poly.exterior.distance(Point(q)) >= c - 1e-6


def cages(shape):
    """4 bars in each channel; ring and column bars must sit at n at least one bar apart (they cross at the node).
    Grid search over the half spacings, keeping cover and the EC2 8.2 clear spacing max(phi, dg + 5, 20)."""
    phi, cov = P["bar"], P["cover"] + P["bar"] / 2
    clear = max(phi, P["dg"] + 5, 20.0)
    cv, rt = col_void(shape), ring_target(shape)
    cu, cs = P["uc"], rt.centroid.y
    rn = rt.centroid.x
    best = None
    rng = [x * 0.5 for x in range(int((clear + phi) / 2 * 2), 200)]
    for an in rng:                                      # column cage half spacing in n
        # widest u spacing that fits for that an
        au = max([x for x in rng if all(_inside(cv, (cu + sx * x, NC + sn * an), cov)
                                        for sx in (-1, 1) for sn in (-1, 1))] or [0])
        if au == 0:
            continue
        for bn in rng:                                  # ring cage half spacing in n
            if min(abs(NC + a - (rn + b)) for a in (-an, an) for b in (-bn, bn)) < phi:
                continue
            bs = max([x for x in rng if all(_inside(rt, (rn + sn * bn, cs + ss * x), cov)
                                            for sn in (-1, 1) for ss in (-1, 1))] or [0])
            if bs == 0:
                continue
            score = (min(au, an, bn, bs), au + an + bn + bs)   # smallest lever arm as large as possible, then the rest
            if best is None or score > best[0]:
                best = (score, au, an, bn, bs)
    if best is None:
        return None
    _, au, an, bn, bs = best
    col = [(cu + sx * au, NC + sn * an) for sx in (-1, 1) for sn in (-1, 1)]       # (u, n), run along s
    ring = [(rn + sn * bn, cs + ss * bs) for sn in (-1, 1) for ss in (-1, 1)]      # (n, s), run along u
    gap = min(abs(a[1] - b[0]) for a in col for b in ring)
    return dict(col=col, ring=ring, col_arm=(2 * au, 2 * an), ring_arm=(2 * bn, 2 * bs),
                clear_col=2 * min(au, an) - phi, clear_ring=2 * min(bn, bs) - phi, cross=gap, need=clear)


def study(shape):
    cg = cages(shape)
    ls, path = layers(shape)
    lh, L = P["lh"], P["L"]
    vol = sum(x["geom"].area for x in ls) * lh
    t = [x["geom"].area / B / P["speed"] for x in ls]
    isl = [len(getattr(x["geom"], "geoms", [x["geom"]])) for x in ls]
    over = [0.0] + [_overhang(a["geom"], b["geom"]) for a, b in zip(ls, ls[1:])]
    tun = [x for x in ls if x["void"]]
    crown = max(x["s"] for x in tun) + lh / 2
    outer_top = max(x["s"] for x in ls if x["outer"] is not None) + lh / 2
    rt, cv = ring_target(shape), col_void(shape)
    # ring pour area: the printed tunnel section; column pour: its channel
    sec = unary_union([box(x["void"][0], x["s"] - lh / 2, x["void"][1], x["s"] + lh / 2) for x in tun])
    corners = {"rect": 4, "oval": 0, "circle": 0}[shape]
    return dict(shape=shape, layers=ls, path=path, mass=vol * P["density"] / 1e6, t_min=min(t), t_sum=sum(t),
                stops=sum(k - 1 for k in isl), islands=isl, overhang=over, max_over=max(over), crown=crown,
                tunnel=(min(x["s"] for x in tun) - lh / 2, crown), outer_top=outer_top,
                ring_area=sec.area, ring_target=rt.area, col_area=cv.area, cages=cg, corners=corners,
                pour=(sec.area * L + cv.area * (P["H"] - 0)) / 1e9 * 1000)


def report(R):
    rows = [("", *[NAMES[r["shape"]] for r in R])]
    f = lambda k, fmt: rows.append((k, *[fmt(r) for r in R]))
    f("Print: worst step over the layer below", lambda r: "{:.1f} mm ({})".format(
        r["max_over"], "ok" if r["max_over"] <= P["step"] + 0.2 else "TOO MUCH"))
    f("Ring tunnel, bed to crown", lambda r: "{:.0f}-{:.0f} mm".format(*r["tunnel"]))
    f("Ring pour area (printable / ideal)", lambda r: "{:.0f} / {:.0f} cm2".format(r["ring_area"] / 100,
                                                                                  r["ring_target"] / 100))
    f("Rib pour area", lambda r: "{:.0f} cm2".format(r["col_area"] / 100))
    f("Grout per piece (rib + ring)", lambda r: "{:.0f} l".format(r["pour"]))
    f("Printed piece", lambda r: "{:.0f} kg".format(r["mass"]))
    f("Layers with a separate bead (stops)", lambda r: "{}".format(r["stops"]))
    f("Shortest layer", lambda r: "{:.0f} s".format(r["t_min"]))
    f("Print time", lambda r: "{:.0f} min".format(r["t_sum"] / 60))
    f("Sharp corners in the rib bead", lambda r: str(r["corners"]))
    f("Column bars, spacing u x n", lambda r: "{:.0f} x {:.0f}".format(*r["cages"]["col_arm"]))
    f("Ring bars, spacing n x s", lambda r: "{:.0f} x {:.0f}".format(*r["cages"]["ring_arm"]))
    f("Clear between bars (need {:.0f})".format(R[0]["cages"]["need"]), lambda r: "{:.0f} / {:.0f}".format(
        r["cages"]["clear_col"], r["cages"]["clear_ring"]))
    f("Ring and column bars at the node, n apart", lambda r: "{:.0f} mm".format(r["cages"]["cross"]))
    w = [max(len(str(x[k])) for x in rows) for k in range(len(rows[0]))]
    return "\n".join("  ".join(str(c).ljust(w[k]) for k, c in enumerate(row)) for row in rows)


def _round(g):
    out = []
    for q in getattr(g, "geoms", [g]):
        q = q.simplify(0.4)
        out.append([[[round(x, 1), round(y, 1)] for x, y in q.exterior.coords[:-1]]] +
                   [[[round(x, 1), round(y, 1)] for x, y in h.coords[:-1]] for h in q.interiors])
    return out


def export(R):
    d = {}
    for r in R:
        kinds, seq, seqcut = [], [], []
        cut = box(300, -1e3, P["L"] + 1, 1e3)          # the 3D view's cut through the ring, as solid faces
        for x in r["layers"]:
            for g, sq in ((x["geom"], seq), (x["geom"].intersection(cut), seqcut)):
                k = json.dumps(_round(g))
                if k not in kinds:
                    kinds.append(k)
                sq.append(kinds.index(k))
        c = r["cages"]
        d[r["shape"]] = dict(
            kinds=[json.loads(k) for k in kinds], seq=seq, seqcut=seqcut,
            over=[round(o, 1) for o in r["overhang"]], isl=r["islands"],
            t=[round(x["geom"].area / B / P["speed"]) for x in r["layers"]],
            tunnel=r["tunnel"], mass=round(r["mass"]), time=round(r["t_sum"] / 60), stops=r["stops"],
            pour=round(r["pour"]), ring_area=round(r["ring_area"] / 100), col_area=round(r["col_area"] / 100),
            colbars=[[round(u, 1), round(n, 1)] for u, n in c["col"]],
            ringbars=[[round(n, 1), round(s, 1)] for n, s in c["ring"]],
            cross=round(c["cross"]), max_over=round(r["max_over"], 1))
    return d


def draw(R, fn):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon as MP, Circle

    fig, ax = plt.subplots(2, 3, figsize=(16, 12.5), gridspec_kw=dict(height_ratios=[1.35, 1]))
    conc, conc2, ink, red, blue = "#c9c3b8", "#b5aea2", "#2b2b2b", "#c0392b", "#2f6db3"
    for k, r in enumerate(R):
        a = ax[0, k]
        # ring section at u = 300 (away from the node): the layer bands in (n, s)
        for x in r["layers"]:
            s0 = x["s"] - P["lh"] / 2
            sec = x["geom"].intersection(box(299.5, -1e3, 300.5, 1e3))
            for g in getattr(sec, "geoms", [sec]):
                if g.is_empty:
                    continue
                n0, n1 = g.bounds[1], g.bounds[3]
                a.add_patch(plt.Rectangle((n0, s0), n1 - n0, P["lh"], fc=conc if x["i"] % 2 else conc2,
                                          ec="white", lw=0.3))
        rt = ring_target(r["shape"])
        a.add_patch(MP(list(rt.exterior.coords), closed=True, fill=False, ec=blue, lw=1.2, ls="--"))
        for n, s in r["cages"]["ring"]:
            a.add_patch(Circle((n, s), P["bar"] / 2, fc=ink))
        for u, n in r["cages"]["col"]:
            a.axvline(n, color=red, lw=0.8, ls=":")
        a.annotate("crown {:.0f}".format(r["tunnel"][1]), (NC, r["tunnel"][1]), (NC - 150, r["tunnel"][1] + 40),
                   arrowprops=dict(arrowstyle="-", lw=0.6), fontsize=8)
        a.set_xlim(-200, 260)
        a.set_ylim(0, P["H"])
        a.set_aspect("equal")
        a.set_title("{} ring, section along the slope\nworst step {:.1f} mm/layer (limit 7), tunnel {:.0f} cm2"
                    .format(NAMES[r["shape"]], r["max_over"], r["ring_area"] / 100), fontsize=10)
        a.set_xlabel("n (mm), room side left")
        a.set_ylabel("s, print height (mm)")
        a.axvline(0, color="#777", lw=0.6)
        b = ax[1, k]
        # plan of a tunnel layer and of a plain layer round the node
        lyr = r["layers"]
        mid = [x for x in lyr if x["void"]][len([x for x in lyr if x["void"]]) // 2]
        for g in getattr(mid["geom"], "geoms", [mid["geom"]]):
            b.add_patch(MP(list(g.exterior.coords), closed=True, fc=conc, ec=ink, lw=0.4))
            for h in g.interiors:
                b.add_patch(MP(list(h.coords), closed=True, fc="white", ec=ink, lw=0.4))
        cv = col_void(r["shape"])
        b.add_patch(MP(list(cv.exterior.coords), closed=True, fill=False, ec=blue, lw=1.0, ls="--"))
        for u, n in r["cages"]["col"]:
            b.add_patch(Circle((u, n), P["bar"] / 2, fc=red))
        for n, s in r["cages"]["ring"]:
            b.axhline(n, color=ink, lw=1.2)
        b.set_xlim(300, 900)
        b.set_ylim(-200, 260)
        b.set_aspect("equal")
        b.set_title("Layer {} (s = {:.0f}), plan round the node: {} contours\nprinted {:.0f} kg, {} stops, {:.0f} min"
                    .format(mid["i"], mid["s"], len(getattr(mid["geom"], "geoms", [mid["geom"]])), r["mass"],
                            r["stops"], r["t_sum"] / 60), fontsize=10)
        b.set_xlabel("u (mm)")
        b.set_ylabel("n (mm)")
    fig.suptitle("Whole joint printed as one piece: rib + ring + node, printed upright (s vertical)", fontsize=13)
    fig.text(0.5, 0.01, "Blue dashed: the ideal channel. Top: ring bars as dots, the column bars' planes as red lines. "
             "Bottom: column bars as red dots, ring bars as black lines. They cross at least 12 mm apart.",
             ha="center", fontsize=9)
    fig.tight_layout(rect=(0, 0.025, 1, 1))
    fig.savefig(fn, dpi=110)
    plt.close(fig)


def main():
    R = [study(s) for s in SHAPES]
    print(report(R))
    here = os.path.dirname(os.path.abspath(__file__))
    folder = os.path.normpath(os.path.join(here, "..", "details", "piece-test"))
    draw(R, os.path.join(folder, "joint-shapes.png"))
    with open(os.path.join(folder, "joint-shapes.json"), "w") as f:
        json.dump(export(R), f, separators=(",", ":"))
    with open(os.path.join(folder, "joint-shapes.txt"), "w") as f:
        f.write(report(R) + "\n")
    print("wrote", folder)
    return R


if __name__ == "__main__":
    main()
