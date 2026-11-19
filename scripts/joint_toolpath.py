"""Print path and G-code for the one-piece joint (scripts/joint_shapes.py), oval rib and ring (Gonzalo, 2026-10-18)

Each layer:
  1. the column piece's own continuous path (Gonzalo's sketch, U round the oval rib), cut where the ring tunnel runs;
  2. what the shell path does not cover (the floor under the tunnel, the room-side wall of the tunnel, the crown) is
     filled with contours offset one bead at a time from its edge; a strip one bead wide gets a single centre line;
  3. contours are chained nearest-first; a gap up to JOIN is printed through (no stop), and up to REACH when the link
     runs over the layer's own material; anything else is a stop (pump off, lift, travel, pump on).
`python scripts/joint_toolpath.py [shape]` writes details/piece-test/joint-<shape>.gcode and joint-<shape>-paths.png.
"""
import json
import math
import os
import sys

from shapely.geometry import LineString, MultiLineString, Point
from shapely.ops import unary_union, linemerge

import joint_shapes as J
import piece_test

B, h = J.B, J.B / 2
JOIN = 35.0                                     # print through a gap this short instead of stopping
REACH = 80.0                                    # or this long, when the link runs over the layer's own material


def _parts(g):
    return [x for x in getattr(g, "geoms", [g]) if not x.is_empty]


def _centreline(q):
    """centre line of a thin polygon: half of its outline, between its two farthest points"""
    c = list(q.exterior.coords)[:-1]
    if len(c) < 4:
        return None
    step = max(1, len(c) // 200)
    idx = range(0, len(c), step)
    best = max(((i, j) for i in idx for j in idx if i < j),
               key=lambda ij: (c[ij[0]][0] - c[ij[1]][0]) ** 2 + (c[ij[0]][1] - c[ij[1]][1]) ** 2)
    i, j = best
    half = c[i:j + 1]
    return half if LineString(half).length > B else None


def _fill(R):
    """contour-parallel fill of region R, one bead apart"""
    out, k = [], 0
    while True:
        g = R.buffer(-(h - 0.5) - B * k, join_style=2)
        if g.is_empty:
            break
        for q in _parts(g):
            width = 2 * q.area / max(q.exterior.length, 1e-9)
            if width < 4.0:                          # thinner than ~1 bead left: one centre line
                cl = _centreline(q)
                if cl:
                    out.append(cl)
                continue
            out.append(list(q.exterior.coords))
            out += [list(r.coords) for r in q.interiors]
        k += 1
    return out


def _chain(cons, start, g):
    """nearest-first order (either direction); join contours closer than JOIN, or up to REACH when the link runs
    over printed material (it lands on beads of this layer: a short double deposit instead of a stop)"""
    cons = [c for c in cons if len(c) > 1]
    out, pos = [], start
    while cons:
        best = None
        for k, c in enumerate(cons):
            if math.hypot(c[0][0] - c[-1][0], c[0][1] - c[-1][1]) < 1e-6:      # closed loop: start anywhere
                j = min(range(len(c)), key=lambda m: math.hypot(c[m][0] - pos[0], c[m][1] - pos[1]))
                d = math.hypot(c[j][0] - pos[0], c[j][1] - pos[1])
                if best is None or d < best[0]:
                    best = (d, k, ("loop", j))
                continue
            for rev in (False, True):
                p0 = c[-1] if rev else c[0]
                d = math.hypot(p0[0] - pos[0], p0[1] - pos[1])
                if best is None or d < best[0]:
                    best = (d, k, rev)
        d, k, rev = best
        c = cons.pop(k)
        if isinstance(rev, tuple):
            j = rev[1]
            c = c[j:-1] + c[:j + 1]
        else:
            c = list(reversed(c)) if rev else c
        link = d <= JOIN or (d <= REACH and LineString([pos, c[0]]).within(g.buffer(2)))
        if out and link:
            out[-1] = out[-1] + c
        else:
            out.append(c)
        pos = c[-1]
    return out


def layer_paths(shape="oval"):
    ls, path = J.layers(shape)
    line = LineString(path)
    res = []
    pos = path[0]
    for x in ls:
        g = x["geom"]
        if x["void"]:                           # the tunnel cuts the shell path
            sh = line.intersection(g.buffer(0.5))
            sh = linemerge(sh) if isinstance(sh, MultiLineString) else sh
            shell = [list(s.coords) for s in _parts(sh) if s.length > B]
        else:
            shell = [list(path)]
        cover = unary_union([LineString(c).buffer(h, cap_style=2, join_style=2) for c in shell])
        R = g.difference(cover.buffer(0.5)).buffer(-3).buffer(3)          # drop slivers
        cons = shell + _fill(R)
        cons = _chain(cons, pos, g)
        pos = cons[-1][-1]
        beads = unary_union([LineString(c).buffer(h, cap_style=2, join_style=2) for c in cons])
        res.append(dict(z=(x["i"] + 1) * J.P["lh"], cons=cons, geom=g,
                        cover=beads.intersection(g).area / g.area, spill=beads.difference(g.buffer(2)).area / g.area))
    return res


def main(shape="oval"):
    lays = layer_paths(shape)
    p = dict(L=J.P["L"], layer_H=J.P["lh"], bead=B, speed=J.P["speed"])
    txt, t, stops = piece_test.gcode(dict(p=p, col=lays), "col", title="ONE-PIECE JOINT, {} rib and ring, printed "
                                     "upright (x = u along the course, y = n, z = s up the slope)".format(shape))
    here = os.path.dirname(os.path.abspath(__file__))
    folder = os.path.normpath(os.path.join(here, "..", "details", "piece-test"))
    fn = os.path.join(folder, "joint-{}.gcode".format(shape))
    with open(fn, "w") as f:
        f.write(txt)
    lt = [sum(LineString(c).length for c in l["cons"]) / J.P["speed"] for l in lays]
    length = sum(LineString(c).length for l in lays for c in l["cons"])
    mass = length * B * J.P["lh"] * J.P["density"] / 1e6
    print("{}: {:.0f} min, {} pump stops, layers {:.0f}-{:.0f} s, {:.0f} kg of beads".format(
        fn, t / 60, stops, min(lt), max(lt), mass))
    print("bead cover of the layer shape: worst {:.0%}, spill outside worst {:.1%}".format(
        min(l["cover"] for l in lays), max(l["spill"] for l in lays)))
    print("contours per layer:", [len(l["cons"]) for l in lays])
    draw(lays, shape, os.path.join(folder, "joint-{}-paths.png".format(shape)))
    with open(os.path.join(folder, "joint-{}-paths.json".format(shape)), "w") as f:     # for the 3D view
        json.dump(dict(paths=[[[[round(x), round(y)] for x, y in LineString(c).simplify(0.5).coords] for c in l["cons"]]
                              for l in lays], stops=stops, time=round(t / 60), t=[round(x) for x in lt]), f,
                  separators=(",", ":"))
    return lays, t, stops


def draw(lays, shape, fn):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon as MP

    tun = [i for i, l in enumerate(lays) if len(l["cons"]) > 1]
    picks = [(1, "floor"), (tun[len(tun) // 3] if tun else 10, "ring tunnel"),
             (max(tun) if tun else 25, "crown closing"), (len(lays) - 1, "shell only")]
    fig, ax = plt.subplots(4, 1, figsize=(15, 17))
    for a, (i, name) in zip(ax, picks):
        l = lays[i]
        for q in _parts(l["geom"]):
            a.add_patch(MP(list(q.exterior.coords), closed=True, fc="#e4dfd6", ec="none"))
            for r in q.interiors:
                a.add_patch(MP(list(r.coords), closed=True, fc="white", ec="none"))
        cols = plt.cm.tab10.colors
        for k, c in enumerate(l["cons"]):
            xs, ys = zip(*c)
            a.plot(xs, ys, color=cols[k % 10], lw=1.4)
            a.plot(xs[0], ys[0], "o", color=cols[k % 10], ms=5)
            a.plot(xs[-1], ys[-1], "s", color=cols[k % 10], ms=5)
        lt = sum(LineString(c).length for c in l["cons"]) / J.P["speed"]
        a.set_title("Layer {} (s = {:.0f}-{:.0f} mm), {}: {} contour{}, {:.0f} s".format(
            i + 1, i * 10, i * 10 + 10, name, len(l["cons"]), "s" if len(l["cons"]) > 1 else "", lt), fontsize=10)
        a.set_xlim(-20, J.P["L"] + 20)
        a.set_ylim(-190, 260)
        a.set_aspect("equal")
        a.set_ylabel("n (mm)")
    ax[-1].set_xlabel("u (mm). Grey: the layer's shape. Lines: print path, one colour per contour, "
                      "circle = start, square = end (each extra contour is one pump stop)")
    fig.suptitle("One-piece joint, {} rib and ring: print path".format(shape), fontsize=13)
    fig.tight_layout()
    fig.savefig(fn, dpi=100)
    plt.close(fig)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "oval")
