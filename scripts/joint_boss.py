"""Print paths for the boss that locks a piece to the one above it (Gonzalo 2026-10-19: lock the node pieces, no
dowels, no loose parts; the thin ring lip looked fragile, so it is a solid boss)

In two cavity cells (test_print.LIP_U) the cell walls step in 7 mm a layer over the piece's top layers until the
cells are closed (8 layers), and a solid boss stands LIP_N layers proud on top, 4 mm clear of the walls of the same
cells in the piece above, which drops over it. Each closing layer and each boss layer is one spiral per cell, an
extra contour, so it costs pump stops (option 1 has stops anyway; on option 2 they are the only ones).

Two versions of the node:
  1: the column piece below the ring is the flared piece turned over (bed to bed under the beam: no boss there);
     only the beam gets a boss, into the column piece above.
  2: the column piece below the ring prints upright on a printable flare (test_print.flare_up_w) with its own boss
     into the beam; the beam's boss goes into the column piece above.

`python scripts/joint_boss.py` writes details/piece-test/{beam-boss, column-below-upright-boss}.gcode and
boss-paths.json (the paths, for the 3D preview).
"""
import json
import os

from shapely.geometry import LineString, box
from shapely.ops import unary_union

import joint_flare as F
import joint_nostop as N
import joint_shapes as J
import piece_test
import test_print as T

L, H, lh, B = J.P["L"], J.P["H"], J.P["lh"], J.B
h = B / 2


def _rings(g):
    return [q.exterior for q in getattr(g, "geoms", [g]) if q.geom_type == "Polygon" and not q.is_empty]


def loops(region, offsets):
    """the loops at the given distances inside region's edge, in order, as contours that each start where the last
    one ended (the short step between them is printed, so the pump runs on through: one spiral, one stop)"""
    out = []
    for d in offsets:
        for r in sorted(_rings(region.buffer(-d, 16)), key=lambda q: -q.length):
            c = list(r.coords)
            if out:
                e = out[-1][-1]
                k = min(range(len(c) - 1), key=lambda m: (c[m][0] - e[0]) ** 2 + (c[m][1] - e[1]) ** 2)
                c = [e] + c[k:-1] + c[:k + 1]
            out.append(c)
    return out


def lipped(base, upper_bed):
    """base: layer dicts (geom, cons, z) of a piece as printed; returns them with the bossed cells closed over the
    top layers and the boss layers on top.
    Closing layer m: the cell's walls have stepped in r = 7m. The band is printed from its inner edge out to the wall
    as loops 30 apart, one spiral per cell; the last loop overlaps the wall bead, so it runs at the flow of the new
    width only. Boss layer: loops 15, 45 ... inside the boss's edge, one spiral per boss"""
    mc = T.closing_layers(base[-1]["geom"])
    out = [dict(x) for x in base]
    for m in range(1, mc + 1):
        k = len(base) - 1 - mc + m
        r = T.STEP * m
        nj = int(-(-r // B))                     # loops in the band
        cons, flow, adds = [], [], []
        for u in T.LIP_U:
            c = T.cell(base[k]["geom"], u)
            cs = loops(c, [r - h - B * j for j in range(nj)])
            cons += cs
            flow += [None] * (len(cs) - 1) + [(r - B * (nj - 1)) / B]
            adds.append(c.difference(c.buffer(-r, 16)))
        out[k]["nbase"] = len(base[k]["cons"])
        out[k]["cons"] = list(base[k]["cons"]) + cons
        out[k]["flow"] = [None] * len(base[k]["cons"]) + flow
        out[k]["geom"] = unary_union([base[k]["geom"]] + adds)
    z = base[-1]["z"]
    bs = T.boss(base[-1]["geom"], upper_bed)
    bcons = []
    for q in getattr(bs, "geoms", [bs]):
        bcons += loops(q, [h + B * j for j in range(6)])
    for i in range(T.LIP_N):
        out.append(dict(i=len(out), z=z + (i + 1) * lh, s=z + (i + 0.5) * lh, cons=bcons, geom=bs, nbase=0))
    return out


def beam():
    """the joint piece, option 2 (no stops, tabs trimmed): joint_nostop.study_oval"""
    return N.study_oval(True)["layers"]


def column_upright():
    """the column piece below the ring printed upright: the flared piece's path with the printable curve"""
    fw = F.fillet_w                              # at least 1 mm, so the rows fill the plan-fillet pockets from the bed
    F.fillet_w = lambda s: max(1.0, T.flare_up_w(H - s))
    try:
        return F.layers()
    finally:
        F.fillet_w = fw


def above_bed():
    return F.layers()[0]["geom"]


def report(name, ls):
    keep = box(0, -1e3, L, 1e3)                  # option 2's end tabs are trimmed off: judge the piece itself
    def clip(g):
        g = g.intersection(keep)
        return unary_union([q for q in getattr(g, "geoms", [g]) if q.geom_type == "Polygon"])
    over = max(J._overhang(clip(a["geom"]), clip(b["geom"])) for a, b in zip(ls, ls[1:]))
    p = dict(L=L, layer_H=lh, bead=B, speed=J.P["speed"])
    txt, t, stops = piece_test.gcode(dict(p=p, col=ls), "col", title=name)
    return txt, dict(stops=stops, min=t / 60, over=over)


def export(sets, fn):
    """the paths for the 3D preview, in mm: per piece, per layer, the contours and which are added for the boss"""
    D = {}
    for name, ls in sets:
        D[name] = [dict(z=round(x["z"], 1), c=[[[round(p[0], 1), round(p[1], 1)] for p in c] for c in x["cons"]],
                        b=x.get("nbase", len(x["cons"])))       # contours from b on are the boss's
                   for x in ls]
    with open(fn, "w") as f:
        json.dump(D, f, separators=(",", ":"))


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    folder = os.path.normpath(os.path.join(here, "..", "details", "piece-test"))
    up = above_bed()
    bm = beam()
    bml = lipped(bm, up)
    col = column_upright()
    coll = lipped(col, bm[0]["geom"])
    res = {}
    for name, ls, title in (("beam-boss", bml, "JOINT piece, option 2, with the boss into the column piece above"),
                            ("column-below-upright-boss", coll, "COLUMN piece below the ring, printed upright, with "
                             "the boss into the beam")):
        txt, r = report(title, ls)
        with open(os.path.join(folder, name + ".gcode"), "w") as f:
            f.write(txt)
        res[name] = r
        print("{}: {} stops, {:.0f} min, worst overhang {:.1f} mm".format(name, r["stops"], r["min"], r["over"]))
    export([("beam", bml), ("below", coll), ("above", F.layers())],
           os.path.join(folder, "boss-paths.json"))
    return res


if __name__ == "__main__":
    main()
