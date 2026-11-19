"""Drawings for scripts/piece_test.py: the print layers (plan section, like the sketch) and the pieces in 3D.
Run `python scripts/piece_test.py`; needs matplotlib and shapely."""
import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Circle, Polygon as MPoly  # noqa: E402
from mpl_toolkits.mplot3d.art3d import Poly3DCollection, Line3DCollection  # noqa: E402
from shapely.geometry import LineString, Polygon  # noqa: E402
from shapely.ops import unary_union, triangulate  # noqa: E402

BEAD, PATH, BAR, CORE = "#c9c4bb", "#d62828", "#1d4e89", "#efe9df"
SLOPE = math.radians(53.0)


def _beads(cons, b):
    segs = [LineString([a, q]).buffer(b / 2.0, cap_style=2, join_style=2) for c in cons for a, q in zip(c, c[1:])]
    return unary_union(segs).buffer(0.5).buffer(-0.5)


def _draw_layer(ax, res, cons, title, bars, channel):
    b = res["p"]["bead"]
    shape = _beads(cons, b)
    for poly in getattr(shape, "geoms", [shape]):
        ax.add_patch(MPoly(list(poly.exterior.coords), closed=True, fc=BEAD, ec="#555", lw=0.6))
        for hole in poly.interiors:
            ax.add_patch(MPoly(list(hole.coords), closed=True, fc="white", ec="#555", lw=0.6))
    if channel is not None:
        ax.add_patch(MPoly(channel, closed=True, fc=CORE, ec="none", zorder=0.5))
    for x, y in bars:
        ax.add_patch(Circle((x, y), res["p"]["bar"] / 2.0, fc=BAR, ec=BAR, zorder=5))
    # path: red centreline, arrows along it, start and end marks, contour numbers
    for ci, c in enumerate(cons):
        xs, ys = zip(*c)
        ax.plot(xs, ys, color=PATH, lw=1.0, zorder=4)
        L = sum(math.hypot(q[0] - a[0], q[1] - a[1]) for a, q in zip(c, c[1:]))
        step, acc, nxt = max(L / 14.0, 60.0), 0.0, max(L / 28.0, 30.0)
        for a, q in zip(c, c[1:]):
            d = math.hypot(q[0] - a[0], q[1] - a[1])
            while d > 0 and acc + d >= nxt:
                t = (nxt - acc) / d
                x, y = a[0] + (q[0] - a[0]) * t, a[1] + (q[1] - a[1]) * t
                ax.annotate("", xy=(x + (q[0] - a[0]) / d * 8, y + (q[1] - a[1]) / d * 8), xytext=(x, y),
                            arrowprops=dict(arrowstyle="-|>", color=PATH, lw=0.8, mutation_scale=8), zorder=6)
                nxt += step
            acc += d
        ax.plot(*c[0], "o", color="#2a9d8f", ms=6, zorder=7)
        ax.plot(*c[-1], "s", color="black", ms=5, zorder=7)
        if len(cons) > 1:
            ax.text(c[0][0] + 12, c[0][1] - 22, "contour {}".format(ci + 1), fontsize=7, color="#2a9d8f")
    ax.set_title(title, fontsize=9, loc="left")
    ax.set_aspect("equal")
    ax.tick_params(labelsize=7)
    ax.grid(True, lw=0.3, alpha=0.4)


def draw_layers(res, path):
    p, S = res["p"], res["S"]
    Hr = res["Hr"]
    from piece_test import _bars
    fig = plt.figure(figsize=(14, 8.2))
    gs = fig.add_gridspec(2, 3, height_ratios=[1.0, 1.15], width_ratios=[1, 1, 1])
    ax = fig.add_subplot(gs[0, :])
    uc, w = p["u_col"], p["rib_w"]
    chan = [(uc - w / 2, S.bot), (uc + w / 2, S.bot), (uc + w / 2, S.top), (uc - w / 2, S.top)]
    _draw_layer(ax, res, res["col"][0]["cons"],
                "COLUMN PIECE, print layer (every layer the same; plan section square to the slope, room side down). "
                "u along the course, n out of the roof", _bars(p, S, uc), chan)
    ax.set_xlim(-40, p["L"] + 40)
    ax.set_ylim(S.nU - 60, S.T + 50)
    ax.text(p["L"] + 10, S.T / 2, "shell\n{:.0f}".format(S.T), fontsize=7, va="center")
    ax.text(uc + w / 2 + 40, S.bot / 2, "downstand {:.0f}\nchannel {:.0f} x {:.0f}\n4 x D{:.0f}".format(
        S.down, w, p["rib_d"], p["bar"]), fontsize=7, va="center")
    ax.text(-30, S.T + 15, "outer face", fontsize=7)
    ax.text(-30, S.nU - 45, "room", fontsize=7)
    ring_n = [x for x in res["ring"] if not x["gap"]][0]
    ring_g = [x for x in res["ring"] if x["gap"]][0]
    chan_r = [(S.b, S.bot), (Hr - S.b, S.bot), (Hr - S.b, S.top), (S.b, S.top)]
    ax2 = fig.add_subplot(gs[1, 0])
    _draw_layer(ax2, res, ring_n["cons"], "RING PIECE, layer outside the gap\n(s up the slope, n out; printed on end)",
                _bars(p, S, Hr / 2), chan_r)
    ax3 = fig.add_subplot(gs[1, 1])
    _draw_layer(ax3, res, ring_g["cons"], "RING PIECE, layer in the gap (column crosses)\nU walls left out, "
                + ("U bottom = 2nd contour" if p["gap_floor"] else "U bottom left out"), _bars(p, S, Hr / 2), chan_r)
    for a in (ax2, ax3):
        a.set_xlim(-60, Hr + 60)
        a.set_ylim(S.nU - 40, S.T + 30)
    ax4 = fig.add_subplot(gs[1, 2])
    ax4.axis("off")
    ch = res["check"]
    txt = "\n".join(_wrap(x, 62) for x in ch["lines"] + ch["flags"])
    ax4.text(0, 1, "red = print path (bead centre), arrows = direction; green dot = start,\n"
             "black square = end. Odd layers run the same path backwards, so each\n"
             "layer starts where the last one ended. Blue = 4 bars.", fontsize=7, va="top")
    ax4.text(0, 0.86, "CHECK\n" + txt, va="top", fontsize=7.0, family="monospace")
    fig.suptitle("One-piece print test: downstand rib, ring printed on end and flipped (all mm)", fontsize=11,
                 x=0.01, ha="left")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def _wrap(s, n):
    words, out, line = s.split(), [], ""
    for w in words:
        if len(line) + len(w) + 1 > n:
            out.append(line)
            line = "  " + w
        else:
            line = (line + " " + w) if line else w
    out.append(line)
    return "\n".join(out)


# ------------------------------------------------ 3D ------------------------------------------------
def _prism(shape, z0, z1):
    """faces of a polygon (with holes) extruded from z0 to z1, in (x, y, z)"""
    faces = []
    for poly in getattr(shape, "geoms", [shape]):
        poly = poly.simplify(1.0)
        for tri in triangulate(poly):
            if poly.contains(tri.representative_point()):
                c = list(tri.exterior.coords)[:3]
                faces.append([(x, y, z1) for x, y in c])
                faces.append([(x, y, z0) for x, y in c])
        for ring in [poly.exterior] + list(poly.interiors):
            c = list(ring.coords)
            for a, q in zip(c, c[1:]):
                faces.append([(a[0], a[1], z0), (q[0], q[1], z0), (q[0], q[1], z1), (a[0], a[1], z1)])
    return faces


def _blocks(res, which):
    """the piece as prisms of identical layers, print frame"""
    b = res["p"]["bead"]
    lays = res[which]
    out, start = [], 0
    for i in range(1, len(lays) + 1):
        if i == len(lays) or lays[i].get("gap") != lays[start].get("gap"):
            z0 = lays[start]["z"] - res["p"]["layer_H"]
            out.append(_prism(_beads(lays[start]["cons"], b), z0, lays[i - 1]["z"]))
            start = i
    return [f for blk in out for f in blk]


def _col_to_face(f, ds=0.0):
    return [(x, z + ds, y) for x, y, z in f]                    # (u, s, n)


def _ring_to_face(f, Hr, ds):
    return [(z, Hr - x + ds, y) for x, y, z in f]               # flip: u = z, s = Hr - x


def _face_to_world(f):
    ca, sa = math.cos(SLOPE), math.sin(SLOPE)
    return [(u, s * ca - n * sa, s * sa + n * ca) for u, s, n in f]


def _add(ax, faces, color, alpha=1.0, z=None):
    pc = Poly3DCollection(faces, facecolor=color, edgecolor=(0, 0, 0, 0.08), lw=0.2, alpha=alpha)
    if z is not None:
        pc.set_zorder(z)
    ax.add_collection3d(pc)


def _frame(ax, pts, elev, azim):
    xs, ys, zs = zip(*pts)
    c = [(max(v) + min(v)) / 2 for v in (xs, ys, zs)]
    r = max(max(v) - min(v) for v in (xs, ys, zs)) / 2
    ax.set_xlim(c[0] - r, c[0] + r)
    ax.set_ylim(c[1] - r, c[1] + r)
    ax.set_zlim(c[2] - r, c[2] + r)
    ax.view_init(elev=elev, azim=azim)
    ax.set_box_aspect((1, 1, 1))
    ax.tick_params(labelsize=6)


def draw_3d(res, path):
    p, S = res["p"], res["S"]
    Hr = res["Hr"]
    from piece_test import _bars
    col, ring = _blocks(res, "col"), _blocks(res, "ring")
    fig = plt.figure(figsize=(15, 6.2))
    ax = fig.add_subplot(1, 3, 1, projection="3d")
    _add(ax, col, "#bdb6aa")
    _frame(ax, [v for f in col for v in f], 28, -60)
    ax.set_title("1  COLUMN PIECE on the bed\n{:.0f} tall, channel = vertical tube".format(p["H"]), fontsize=9)
    ax = fig.add_subplot(1, 3, 2, projection="3d")
    _add(ax, ring, "#9fb4c7")
    _frame(ax, [v for f in ring for v in f], 22, -50)
    ax.set_title("2  RING PIECE on the bed, printed on end\n{:.0f} tall, ring = vertical tube, gap for the column"
                 .format(p["Lr"]), fontsize=9)
    ax = fig.add_subplot(1, 3, 3, projection="3d", computed_zorder=False)
    gap = 150.0                                                  # exploded: pieces pulled apart along the slope
    sr, sa = p["H"] + gap, p["H"] + Hr + 2 * gap
    below, above = [_col_to_face(f) for f in col], [_col_to_face(f, sa) for f in col]
    faces = below + above
    rf = [_ring_to_face(f, Hr, sr) for f in ring]
    _add(ax, above, "#bdb6aa", z=1)                              # seen from the room: far piece first
    _add(ax, rf, "#9fb4c7", z=2)
    _add(ax, below, "#bdb6aa", z=3)
    segs = []
    top = sa + p["H"]
    for x, n in _bars(p, S, p["u_col"]):                         # column bars, up the slope
        segs.append([(x, -100, n), (x, top + 100, n)])
    for s_, n in _bars(p, S, Hr / 2):                            # ring bars, along the course
        segs.append([(-100, sr + Hr - s_, n), (p["Lr"] + 100, sr + Hr - s_, n)])
    lc = Line3DCollection(segs, colors=BAR, lw=1.6)
    lc.set_zorder(4)
    ax.add_collection3d(lc)
    _frame(ax, [v for f in faces + rf for v in f], -38, -62)
    ax.set_xlabel("u (course)", fontsize=7)
    ax.set_ylabel("s (up the slope)", fontsize=7)
    ax.set_zlabel("n (out)", fontsize=7)
    ax.set_title("3  ASSEMBLY, exploded, seen from the room\ncolumn piece, ring flipped onto it, next column piece; "
                 "bars in blue", fontsize=9)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def draw(res, folder):
    os.makedirs(folder, exist_ok=True)
    a = os.path.join(folder, "piece-test-layers.png")
    b = os.path.join(folder, "piece-test-3d.png")
    draw_layers(res, a)
    draw_3d(res, b)
    return [os.path.normpath(a), os.path.normpath(b)]
