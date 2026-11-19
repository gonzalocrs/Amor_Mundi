"""The organic node with the column sized to Karamba's tapered rib (Gonzalo 2026-10-20: "make a new iteration based on
the tapering")

Karamba (grasshopper/findings-2026-10-18.md, commit 0fad7fa on gonzalo): columns 150 wide, depth tapering linearly
from 350 at the eave to 150 at the crown, protruding into the room. Here the column hole is that section: 150 along
the course, d deep through the roof, its shell-side face at n = 30 as before (bead B), corners rounded R_CORNER
(the bar cover), so it reaches n = 30 - d on the room side. d is read off the slope position of every layer, so the
hole narrows 0.27 mm a layer up the slope and every piece is a little different.

The node at the lower middle ring (+4.80, the one at 97%) as it goes together, bottom to top:
  regular piece, connecting piece (printed turned over), organic joint piece, connecting piece, regular piece.
The pieces are scripts/joint_organic.py's, cut round the tapered hole. With the taper the joint piece is no longer the
same at its bed and top, so the connecting piece below is its own piece, printed turned over: its layers are mirrored
along the course (the wave web is not symmetric), and its hole deepens 0.27 mm a layer as it rises, well inside the
7 mm step.

`python scripts/joint_tapered.py` writes details/piece-test/tapered/*.gcode, the 1:12 desk prints
details/piece-test/test-print/tapered-node-3pieces-1to12.stl and tapered-node-A1-plate.3mf, and
details/piece-test/tapered/tapered-node.json (outlines for the 3D preview).
"""
import json
import math
import os

import trimesh
from shapely.affinity import scale as sscale
from shapely.geometry import LineString, Point, box

import joint_organic as O
import joint_shapes as J
import piece_test
import test_print as T

L, lh, B = J.P["L"], J.P["lh"], J.B
TOP = J.TOP                                     # shell-side face of the hole, n = 30
W_COL = 150.0                                   # column width along the course
D_EAVE, D_CROWN = 350.0, 150.0                  # column depth at the eave and at the crown
R_CORNER = 40.0                                 # rounded corners of the hole

# roof geometry, scripts/karamba_model.py defaults with the final model (clear 10000, wall 400, eave +2.50, base ring
# 300, rise 6000, crown opening 1000): the slope runs from z_b = 2650 to z_c = 8500
Z_B, Z_C = 2500.0 + 300.0 / 2, 2500.0 + 6000.0
RUN = 10000.0 / 2 + 400.0 / 2 - 1000.0 / 2
SLANT = math.hypot(RUN, Z_C - Z_B)              # 7504 along the slope
Z_RING = 4800.0                                 # the lower middle ring
S_RING = (Z_RING - Z_B) / (Z_C - Z_B) * SLANT   # 2758 up the slope from the eave
H_REG, H_J = J.P["H"], O.H


def depth(sg):
    """column depth at sg mm up the slope from the eave"""
    return D_EAVE + (D_CROWN - D_EAVE) * min(max(sg / SLANT, 0.0), 1.0)


def hole(d):
    """the column hole, W_COL x d, rounded corners, shell-side face at n = TOP"""
    r = R_CORNER
    return box(J.P["uc"] - W_COL / 2 + r, TOP - d + r, J.P["uc"] + W_COL / 2 - r, TOP - r).buffer(r, 32)


def piece(kind, s0, down=False):
    """layers of one piece; s0 = slope position of its bed, down = printed turned over (layer i at s0 - s)"""
    n = int(round((H_J if kind == "joint" else H_REG) / lh))
    sg = lambda s: s0 - s if down else s0 + s
    O.void = lambda s: hole(depth(sg(s)))
    if kind == "joint":
        ls = O.layers()
    elif kind == "conn":
        ls = O.col_layers()
    else:
        ls = []
        for i in range(n):
            s = (i + 0.5) * lh
            path, g = O.shell(s)
            ls.append(dict(i=i, s=s, void=None, outer=0.0, geom=g, path=path))
    if down:                                    # turned over = turned about n, so print it mirrored along the course
        mir = lambda g: sscale(g, -1, 1, origin=(L / 2, 0))
        ls = [dict(x, geom=mir(x["geom"]), path=[(L - u, v) for u, v in x["path"]][::-1]) for x in ls]
    return ls


def stats(name, ls, folder, single=False):
    if single:                                  # the regular piece: its shell path is the whole layer
        cs = [dict(x, z=(x["i"] + 1) * lh, cons=[x["path"]]) for x in ls]
    else:
        cs = O.paths(ls)
    over = max(J._overhang(a["geom"], b["geom"]) for a, b in zip(cs, cs[1:]))
    p = dict(L=L, layer_H=lh, bead=B, speed=J.P["speed"])
    txt, t, stops = piece_test.gcode(dict(p=p, col=cs), "col", title="TAPERED column node: " + name)
    with open(os.path.join(folder, name + ".gcode"), "w") as f:
        f.write(txt)
    mass = sum(x["geom"].area for x in cs) * lh * J.P["density"] / 1e6
    return cs, dict(mass=round(mass), minutes=round(t / 60), stops=stops, over=round(over, 1))


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.normpath(os.path.join(here, "..", "details", "piece-test"))
    folder = os.path.join(root, "tapered")
    os.makedirs(folder, exist_ok=True)
    jb, jt = S_RING - H_J / 2, S_RING + H_J / 2  # joint piece bed and top on the slope
    pieces = [                                   # name, kind, bed position, turned over, layers as built, bottom up
        ("1-regular-below", "reg", jb - 2 * H_REG, False),
        ("2-connector-below", "conn", jb, True),
        ("3-joint", "joint", jb, False),
        ("4-connector-above", "conn", jt, False),
        ("5-regular-above", "reg", jt + H_REG, False),
    ]
    out, info, geo = {}, {}, {}
    for name, kind, s0, down in pieces:
        ls = piece(kind, s0, down)
        cs, inf = stats(name, ls, folder, single=kind == "reg")
        d0, d1 = depth(s0), depth(s0 - len(ls) * lh if down else s0 + len(ls) * lh)
        inf.update(depth=[round(d0), round(d1)])
        info[name] = inf
        geo[name] = [x["geom"] for x in cs]
        out[name] = [T.outline(x["geom"], tol=0.8) for x in cs]
        print("{:20s} {:4d} kg {:3d} min {:4d} stops, overhang {:4.1f} mm, column {:.0f} -> {:.0f} deep".format(
            name, inf["mass"], inf["minutes"], inf["stops"], inf["over"], d0, d1))
    # the joints between pieces as they go together: what of each upper bed stands past the layer below it
    flip = lambda gs: [sscale(g, -1, 1, origin=(L / 2, 0)) for g in reversed(gs)]
    stack = [geo["1-regular-below"], flip(geo["2-connector-below"]), geo["3-joint"], geo["4-connector-above"],
             geo["5-regular-above"]]
    for a, b in zip(stack, stack[1:]):
        print("  bed past the piece below: {:.0f} mm2, max {:.1f} mm".format(b[0].difference(a[-1]).area,
                                                                             J._overhang(a[-1], b[0])))
    # desk print, 1:12: the three node pieces, each upright as printed
    desk = os.path.join(root, "test-print")
    sc = trimesh.Scene()
    y = 0.0
    for name in ("2-connector-below", "3-joint", "4-connector-above"):
        m = T.build(geo[name])
        m.apply_translation((-m.bounds[0][0], y - m.bounds[0][1], -m.bounds[0][2]))
        sc.add_geometry(m, geom_name=name)
        y += m.extents[1] + 8
    sc.export(os.path.join(desk, "tapered-node-A1-plate.3mf"))
    sc.to_mesh().export(os.path.join(desk, "tapered-node-3pieces-1to12.stl"))
    print("desk plate {:.1f} x {:.1f} x {:.1f} mm".format(*sc.to_mesh().extents))
    with open(os.path.join(folder, "tapered-node.json"), "w") as f:
        json.dump(dict(lh=lh, s_ring=round(S_RING), slant=round(SLANT), info=info, pieces=out), f,
                  separators=(",", ":"))


if __name__ == "__main__":
    main()
