"""Flared column pieces either side of the ring course (Gonzalo, 2026-10-19: "like Masoud's bridge connections, more
organic looking, not so rough")

Seen in elevation from the room, the column meets the ring on a full quarter circle (R_NODE) above and below. The
pieces are printed and then assembled, so no piece may overhang as it prints. The joint (beam) piece stays as it
is, with its band filled flat above the crown (joint_shapes.P["fill"]), and the column pieces either side of it carry
the curve:
  - above the ring: the flared piece prints upright, widest on the bed and narrowing as it rises, so every layer
    sits inside the one below;
  - below the ring: the same piece, printed the same way and turned over (rotated about n, so the column stays at
    u = 600 and the wide end lands on the ring).
The wings stay flush with the beam's band face (BAND_FACE).

Print path: the regular piece's single path, with the run along bead A replaced, where the wings are, by strokes
across n (down to the wing's edge and back up, at most one bead apart) that join the U round the column. One path a
layer and odd layers run backwards, so there are no pump stops on any printer: options 1 and 2 both use this piece.
Option 3 has no ring beam to land on (the ring is the course itself), so it keeps plain column pieces.

`python scripts/joint_flare.py` writes details/piece-test/flared-piece.gcode.
"""
import math
import os

import numpy as np
from shapely.affinity import translate
from shapely.geometry import LineString, box
from shapely.ops import unary_union

import joint_shapes as J
import piece_test

SHAPE = "oval"
L, H, lh, B = J.P["L"], J.P["H"], J.P["lh"], J.B
h = B / 2
R_NODE = 250.0                                  # fillet radius where the column meets the ring, in elevation (mm)
N_LAYERS = int(round(H / lh))


def _band_face():
    st = J.study(SHAPE)
    top = max(i for i, x in enumerate(st["layers"]) if x["void"])           # the crown layer
    return st["layers"][top]["geom"].intersection(box(100, -1e3, 200, 1e3)).bounds[1]   # clear of the column


BAND_FACE = _band_face()                        # room face of the beam's ring at the crown, n = -131


def fillet_w(d):
    """how far the fillet reaches out along the course at distance d (mm) from the ring's edge"""
    return 0.0 if d >= R_NODE else R_NODE - (R_NODE ** 2 - (R_NODE - d) ** 2) ** 0.5


def widen(g, w):
    """the column's room-side protrusion widened by w each way along the course (the fillet seen in elevation)"""
    cv = J.col_void(SHAPE)
    prot = g.union(cv).intersection(box(-1e3, -1e3, L + 1e3, 0.0))
    near = prot.intersection(box(cv.bounds[0] - 150, -1e3, cv.bounds[2] + 150, 1e3))
    k = max(2, int(w // 5) + 1)
    wide = unary_union([translate(near, dx) for dx in np.linspace(-w, w, 2 * k + 1)]).buffer(2).buffer(-2)
    return g.union(wide).difference(cv)


def target(i):
    """the flared layer i as a region (what the desk model prints): wings flush with the band face"""
    _, reg = J.shell_layer(SHAPE)
    w = fillet_w((i + 0.5) * lh)
    return widen(reg, w).intersection(box(-1e3, BAND_FACE, L + 1e3, 1e3)).union(reg)


ROWS = 4                                        # rows across each wing below bead A
ROW_W = (J.nA - h - BAND_FACE) / ROWS             # 32.75 apart: printed as a 33 mm bead
ROW_N = [J.nA - h - ROW_W * (k + 0.5) for k in range(ROWS)]                              # -16.4 ... -114.6


def _cross_ring(ring, n):
    c = ring.intersection(LineString([(-1e3, n), (L + 1e3, n)]))
    xs = sorted(q.x for q in getattr(c, "geoms", [c]))
    return xs[0], xs[-1]


def _edges(region, n, ul, ur):
    """where the wing ends along the course on the row at n: left and right bead-centre ends"""
    c = region.intersection(LineString([(-1e3, n), (L + 1e3, n)]))
    segs = [q for q in getattr(c, "geoms", [c]) if q.length > 0]
    left = [q for q in segs if min(x for x, _ in q.coords) < ul]
    right = [q for q in segs if max(x for x, _ in q.coords) > ur]
    el = min(min(x for x, _ in q.coords) for q in left) + ROW_W / 2 if left else ul
    er = max(max(x for x, _ in q.coords) for q in right) - ROW_W / 2 if right else ur
    return min(el, ul), max(er, ur)


def _ring_run(ring, p, q, side):
    """points along the bead ring round the column from p to q, the way that stays on the left (side -1) or right
    (+1) flank or under the column, never over its top"""
    from shapely.geometry import Point
    a, b = ring.project(Point(p)), ring.project(Point(q))
    n = 16
    for d in (b - a, b - a - ring.length if b > a else b - a + ring.length):
        pts = [ring.interpolate((a + d * k / n) % ring.length) for k in range(n + 1)]
        if all(x.y <= J.nA + 0.5 for x in pts):
            return [(x.x, x.y) for x in pts]
    raise ValueError("no way round the column")


def _side(ns, xs, ed, sgn):
    """one wing, traversed from bead A in toward the column: A, then rows out, in, out, in"""
    out, rows = [], []
    end = h if sgn < 0 else L - h
    ring_u = [x[0] if sgn < 0 else x[1] for x in xs]
    edge_u = [e[0] if sgn < 0 else e[1] for e in ed]
    for k, n in enumerate(ns):
        seg = [(end if k == 0 else edge_u[k], n), (ring_u[k], n)]
        if k:
            rows.append(list(seg))
        if k % 2:
            seg = seg[::-1]                        # out: from the column to the wing's edge
            out += _ring_run(RING, out[-1], seg[0], sgn)[1:-1]     # joined along the column's bead ring
        out += seg                                 # (in: joined straight down the wing's edge)
    return out, rows


RING = J.col_void(SHAPE).buffer(h, 64).exterior


def layer_path(i):
    """the regular path, or where the column flares: bead A runs to the column, each wing is filled with ROWS rows
    along the course (out, in, out, in) joined along the column's bead ring and down the wing's edge, the column's U
    takes the path under the column to the other wing, and the mirrored rows bring it back to bead A.
    Returns (path, rows)"""
    path, reg = J.shell_layer(SHAPE)
    w = fillet_w((i + 0.5) * lh)
    if w < 1.0:
        return path, []
    cv = J.col_void(SHAPE)
    region = target(i)
    ns = [J.nA] + ROW_N
    xs = [_cross_ring(RING, n) for n in ns]
    ed = [_edges(region, n, *x) for n, x in zip(ns, xs)]
    left, rl = _side(ns, xs, ed, -1)
    right, rr = _side(ns, xs, ed, 1)
    U = _ring_run(RING, left[-1], right[-1], 0)
    run = left + U[1:-1] + right[::-1]
    a = path.index((h, J.nA))
    b = path.index((L - h, J.nA))
    return path[:a] + run + path[b + 1:], rl + rr


def bead_geom(p, rows=()):
    cv = J.col_void(SHAPE)
    g = LineString(p).buffer(h, cap_style=2, join_style=2, mitre_limit=1.5).union(box(0, 0, L, B))
    for r in rows:
        g = g.union(LineString(r).buffer(ROW_W / 2, cap_style=2))
    return g.difference(cv)


def layers():
    out = []
    for i in range(N_LAYERS):
        p, rows = layer_path(i)
        out.append(dict(i=i, s=(i + 0.5) * lh, z=(i + 1) * lh, geom=bead_geom(p, rows),
                        cons=[p if i % 2 == 0 else list(reversed(p))]))
    return out


def study():
    ls = layers()
    over = [0.0] + [J._overhang(a["geom"], b["geom"]) for a, b in zip(ls, ls[1:])]
    _, reg = J.shell_layer(SHAPE)
    mass = sum(x["geom"].area for x in ls) * lh * J.P["density"] / 1e6
    reg_mass = reg.area * H * J.P["density"] / 1e6
    t = sum(LineString(x["cons"][0]).length for x in ls) / J.P["speed"]
    wings = [fillet_w(x["s"]) for x in ls]
    return dict(layers=ls, over=over, max_over=max(over), mass=mass, extra=mass - reg_mass, time=t / 60,
                reach=max(wings), rise=max(x["z"] for x, w in zip(ls, wings) if w > 0))


def main():
    r = study()
    p = dict(L=L, layer_H=lh, bead=B, speed=J.P["speed"])
    txt, t, s = piece_test.gcode(dict(p=p, col=r["layers"]), "col", title="flared column piece next to the ring")
    here = os.path.dirname(os.path.abspath(__file__))
    fn = os.path.normpath(os.path.join(here, "..", "details", "piece-test", "flared-piece.gcode"))
    with open(fn, "w") as f:
        f.write(txt)
    print("band face {:.0f}, wings reach {:.0f} at the bed and end at s = {:.0f}".format(BAND_FACE, r["reach"], r["rise"]))
    print("{} stops {:.0f} min {:.0f} kg ({:+.0f} kg on a regular piece), worst overhang {:.1f} mm".format(
        s, t / 60, r["mass"], r["extra"], r["max_over"]))
    print("wrote", fn)


if __name__ == "__main__":
    main()
