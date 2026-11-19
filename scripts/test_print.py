"""Desk test print of option 1 (pump stops) at 1:12, for a Bambu A1 with a 0.4 mm nozzle (Gonzalo, 2026-10-19)

Two pieces, 100 mm long: the REGULAR piece (one continuous path a layer) and the JOINT piece (oval rib + ring
tunnel, the "knot"). Each concrete layer becomes a band 0.83 mm tall, rounded like an extruded bead, so the
seams of the real print show on every face, the tunnel and the cavity included. The regular piece's rib grows out
of the wall on a 100 mm fillet (joint_shapes.P["fillet"]). The model prints
upright like the real piece, so the tunnel crown corbels at the same 35 degrees.

`python scripts/test_print.py` writes details/piece-test/test-print/{regular,joint}-1to12.stl and preview.json
(scaled layer outlines for the 3D preview).
"""
import json
import math
import os

import manifold3d as M
import numpy as np
import trimesh
from shapely.affinity import scale
from shapely.geometry import box
from shapely.geometry.polygon import orient
from shapely.ops import unary_union

import joint_flare as F
import joint_shapes as J

SHAPE = "oval"
L, H, lh = J.P["L"], J.P["H"], J.P["lh"]
S = 100.0 / L                                   # 1:12
ROUND = 0.30                                    # how far a bead's face rounds back at its top and bottom edge, mm
STEPS = 4                                       # sub-bands per half bead that make the round profile


def _parts(g):
    g = g.buffer(0.3, join_style=2).buffer(-0.3, join_style=2).intersection(box(0, -1e3, L, 1e3))   # fuse parts that only touch
    return [orient(q.simplify(0.5)) for q in getattr(g, "geoms", [g]) if q.geom_type == "Polygon" and q.area > 1]


def _cs(polys, inset=0.0):
    rings = []
    for q in polys:
        rings.append(np.array(q.exterior.coords[:-1]) * S)
        rings += [np.array(r.coords[:-1]) * S for r in q.interiors]
    cs = M.CrossSection(rings, M.FillRule.EvenOdd)
    return cs.offset(-inset, M.JoinType.Miter) if inset else cs


def slab(polys, z0):
    """one concrete layer as a rounded bead: the outline is full at mid-height and pulls back toward the top and
    bottom edges on a quarter-ellipse, so neighbouring layers meet in a soft groove (like an extruded bead)"""
    t = lh * S
    e = 0.002                                   # overlap the sub-bands a hair so the union fuses them
    hs = t / 2 / STEPS
    parts = []
    for k in range(STEPS):
        zc = (k + 0.5) / STEPS                  # 0 at the edge, 1 at mid-height
        inset = ROUND * (1 - (1 - (1 - zc) ** 2) ** 0.5)
        cs = _cs(polys, inset) if inset > 0.005 else _cs(polys)
        for z in (z0 + k * hs, z0 + t - (k + 1) * hs):
            parts.append(cs.extrude(hs + 2 * e).translate((0, 0, z - e)))
    return parts


def build(layer_geoms):
    solids = []
    for i, g in enumerate(layer_geoms):
        solids += slab(_parts(g), i * lh * S)
    m = M.Manifold.batch_boolean(solids, M.OpType.Add)
    m = m - M.Manifold.cube((1e3, 1e3, 1.0)).translate((-500, -500, -1.0))     # flat on the bed at z = 0
    mesh = m.to_mesh()
    return trimesh.Trimesh(vertices=mesh.vert_properties[:, :3], faces=mesh.tri_verts)


def beam():
    """the joint (beam) piece, its band above the tunnel crown filled flat to the piece's top (joint_shapes.P["fill"],
    Gonzalo 2026-10-19), so the ring reads as one 450 mm band and the flared piece above sits right on it"""
    return [x["geom"] for x in J.study(SHAPE)["layers"]]


def layers():
    n = int(round(H / lh))
    _, reg = J.shell_layer(SHAPE)
    return [reg] * n, beam()


def flared():
    """the column piece next to a ring (scripts/joint_flare.py): widest on the bed, narrowing as it rises; above a
    ring it prints this way up, below a ring the same piece is turned over (rotated about n)"""
    return [F.target(i) for i in range(F.N_LAYERS)]


def flare_up_w(d):
    """the column piece BELOW the ring printed upright (version 2): it has to widen as it rises, so its curve can
    step out at most 7 mm a layer. From the bed: an arc tangent to the column (R 295) that turns to a straight
    35 degree run (0.7) reaching the full 250 at the ring, like the flare above. d = distance below the ring, mm"""
    s, R = 0.7, 294.6
    e = H - d                                    # height above the bed
    th = math.atan(s)
    e1 = R * math.sin(th)                        # where the arc meets the straight run
    return R - (R * R - e * e) ** 0.5 if e < e1 else R * (1 - math.cos(th)) + s * (e - e1)


def flared_upright():
    _, reg = J.shell_layer(SHAPE)
    out = []
    for i in range(F.N_LAYERS):
        w = flare_up_w(H - (i + 0.5) * lh)
        g = F.widen(reg, w).intersection(box(-1e3, F.BAND_FACE, L + 1e3, 1e3)).union(reg) if w >= 1 else reg
        if out:                                  # the plan-fillet pockets by the column fill 7 mm a layer too
            g = g.intersection(out[-1].buffer(STEP, 16)).union(reg)
        out.append(g)
    return out


LIP_CL = 4.0                                    # play between the boss and the cell above (0.33 mm at 1:12)
LIP_N = 4                                       # layers the boss stands above the piece (40 mm)
LIP_U = (267.0, 933.0)                          # the two cavity cells that get a boss, clear of the column
STEP = J.P["step"]
_ENV = box(30, J.nB, L - 30, J.nO2)             # between bead B and bead O2, inside the end beads


def cell(g, u):
    """the hollow cavity cell of layer g that holds u = u (between bead B, the web and bead O2)"""
    c = _ENV.difference(g)
    return min(getattr(c, "geoms", [c]), key=lambda q: abs(q.centroid.x - u))


def boss(lower_top, upper_bed):
    """the boss on top of a piece (Gonzalo 2026-10-19: lock the pieces to each other, no dowels; a thin ring looked
    fragile): a solid block that stands LIP_N layers proud of the lower piece, filling each cell it shares with the
    piece above less LIP_CL of play all round"""
    return unary_union([cell(lower_top, u).intersection(cell(upper_bed, u)).buffer(-LIP_CL, 16) for u in LIP_U])


def closing_layers(g):
    """how many layers it takes to close the bossed cells of layer g, walls stepping in 7 mm a layer from all sides"""
    m = 1
    while any(not cell(g, u).buffer(-STEP * m, 16).is_empty for u in LIP_U):
        m += 1
    return m


def lipped(lays, upper_bed):
    """the piece with the bossed cells closed over its top layers (the walls step in 7 mm a layer, out of sight
    inside the cell) and the boss printed on top: (layers, boss layers)"""
    mc = closing_layers(lays[-1])
    out = list(lays)
    for m in range(1, mc + 1):
        k = len(lays) - 1 - mc + m
        c = unary_union([cell(lays[k], u) for u in LIP_U])
        out[k] = lays[k].union(c.difference(c.buffer(-STEP * m, 16)))
    return out, [boss(lays[-1], upper_bed)] * LIP_N


def node():
    """three courses stacked: flared piece turned over / joint piece / flared piece as printed"""
    fl, bm = flared(), [x["geom"] for x in J.study(SHAPE)["layers"]]
    below = [scale(g, -1, 1, origin=(L / 2, 0)) for g in reversed(fl)]
    return below + bm + fl, fl, bm


def outline(g, tol=0.4):
    out = []
    for q in _parts(g):
        q = q.simplify(tol)
        out.append([[[round(x * S, 2), round(y * S, 2)] for x, y in r.coords[:-1]]
                    for r in [q.exterior] + list(q.interiors)])
    return out


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    folder = os.path.normpath(os.path.join(here, "..", "details", "piece-test", "test-print"))
    os.makedirs(folder, exist_ok=True)
    reg, jnt = layers()
    nd, fl, _ = node()
    info = {}
    for name, lays in (("regular", reg), ("joint", jnt), ("flared", fl), ("node", nd)):
        tm = build(lays)
        fn = os.path.join(folder, "{}-1to12.stl".format(name))
        tm.export(fn)
        ext = tm.extents
        info[name] = dict(size=[round(float(v), 1) for v in ext], vol=round(float(tm.volume) / 1e3, 1),
                          grams=round(float(tm.volume) / 1e3 * 1.24, 0), watertight=bool(tm.is_watertight),
                          layers=[outline(g) for g in lays])
        print("{}: {} x {} x {} mm, {:.1f} cm3, {:.0f} g PLA solid, watertight {}, {} triangles".format(
            name, *info[name]["size"], info[name]["vol"], info[name]["grams"], tm.is_watertight, len(tm.faces)))
    info.update(scale=S, lh=round(lh * S, 4), seam=[ROUND, STEPS], L=round(L * S, 2))
    with open(os.path.join(folder, "preview.json"), "w") as f:
        json.dump(info, f, separators=(",", ":"))


if __name__ == "__main__":
    main()
