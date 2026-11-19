"""The mirrored joint piece made organic (Gonzalo 2026-10-20: "make it more like this, this one looks more organic,
then rationalize it into the slicing we need")

The design surface, before slicing:
  - the ring tunnel stays the mirrored one (scripts/joint_mirrored.py): a 250 circle with 35 degree tangents to a
    point at the floor and at the crown, so it is smooth all round except at the two points;
  - the room face of the ring wall is that outline offset by one bead and carried on along the same 35 degree
    tangents to the bottom and the top of the course, so from the side the piece swells out in one smooth lens
    instead of a stepped diamond on flat 80 mm bands;
  - in plan the wall leaves the column on a fillet (R_PLAN), so where the column stands proud of the wall (near the
    top and the bottom) it grows out of it like the rib of the regular piece.
Rationalised: cut into 10 mm layers, every face stepping at most 7 mm a layer; each layer is the option 1 path
(scripts/joint_toolpath.py: the shell path cut by the tunnel, the rest filled one bead at a time, chained).

The connecting piece (col_layer) goes between the joint piece and the regular column piece: its bed is the joint
piece's top, its top is the regular piece, and the room face eases from one to the other over the whole course,
leaving the joint piece on the same 35 degree slope. One piece: above as printed, below turned over (the joint piece
is the same at its top and bed).

`python scripts/joint_organic.py` writes details/piece-test/{joint,connector}-organic.gcode, the desk prints
details/piece-test/test-print/{joint,connector}-organic-1to12.stl, joint-organic-A1-plate.3mf and
node-organic-A1-plate.3mf, and joint-organic.json (the layers and paths, for the 3D preview).
"""
import json
import math
import os

import trimesh
from shapely.geometry import LineString, MultiLineString, Polygon, box
from shapely.ops import linemerge, unary_union

import joint_shapes as J
import joint_toolpath as TP
import piece_test
import test_print as T

L, lh, B, h = J.P["L"], J.P["lh"], J.B, J.B / 2
R = J.P["ring_d"] / 2                           # tunnel circle radius, 125
NC = 30.0 - R                                   # its centre in n: shell-side face at n = 30
TH = math.radians(35.0)                         # 7 mm a 10 mm layer
APEX = R / math.sin(TH)                         # centre to each point, 218
H = 590.0                                       # course height (joint_mirrored)
SC = H / 2                                      # tunnel centre in s
R_PLAN = 100.0                                  # plan fillet where the column meets the wall


def void(s):
    """the column channel at height s in the piece (scripts/joint_tapered.py swaps in the tapered column)"""
    return J.col_void("oval")


def shell(s, fillet=None):
    """the regular column piece's path and layer at height s, round void(s)"""
    return J.shell_layer("oval", fillet=fillet, cv=void(s))


def half_width(s):
    """half the tunnel's width in n at height s: the circle, or the 35 degree tangent toward the nearer point"""
    d = abs(s - SC)
    if d <= R * math.sin(TH):
        return (R * R - d * d) ** 0.5
    return max(0.0, (APEX - d) * math.tan(TH))


def room_face(s):
    """room face of the wall: the tunnel's room side less one bead, the tangents carried on past the points"""
    d = abs(s - SC)
    if d <= R * math.sin(TH):
        return NC - (R * R - d * d) ** 0.5 - B
    return NC - (APEX - d) * math.tan(TH) - B / math.cos(TH)


def layer_geom(i):
    s = (i + 0.5) * lh
    path, base = shell(s, fillet=0)
    cv = void(s)
    m = room_face(s)
    wall = box(0, m, L, J.nB + B / 2)
    prot = cv.buffer(B, 64).intersection(box(-1e3, -1e3, L + 1e3, m + 1))   # the column's bead below the wall
    if not prot.is_empty:                       # fillet it into the wall
        wall = wall.union(prot).buffer(R_PLAN, 32).buffer(-R_PLAN, 32).intersection(box(0, -1e3, L, 1e3))
        wall = wall.union(prot)
    g = base.union(wall)
    w = half_width(s)
    tun = (NC - w, NC + w) if w > 1.0 else None
    if tun:
        g = g.difference(box(-1, tun[0], L + 1, tun[1]))
    g = g.difference(cv).buffer(0)
    return dict(i=i, s=s, void=tun, outer=m, geom=g, path=path)


def layers():
    return [layer_geom(i) for i in range(int(round(H / lh)))]


def paths(ls):
    """the option 1 path of each layer (joint_toolpath.layer_paths, on these layers)"""
    pos, res = ls[0]["path"][0], []
    for x in ls:
        g, path = x["geom"], x["path"]
        line = LineString(path)
        if x["void"]:
            sh = line.intersection(g.buffer(0.5))
            sh = linemerge(sh) if isinstance(sh, MultiLineString) else sh
            shell = [list(q.coords) for q in TP._parts(sh) if q.length > B]
        else:
            shell = [list(path)]
        cover = unary_union([LineString(c).buffer(h, cap_style=2, join_style=2) for c in shell])
        rest = g.difference(cover.buffer(0.5)).buffer(-3).buffer(3)
        cons = TP._chain(shell + TP._fill(rest), pos, g)
        pos = cons[-1][-1]
        res.append(dict(x, z=(x["i"] + 1) * lh, cons=cons))
    return res


# ---- the connecting piece above and below (Gonzalo 2026-10-20: "leave the organic piece for the middle piece or
# beam. Then only create a connecting piece that goes on top or at the bottom"): the organic piece stays the beam, the
# regular column pieces stay as they are (joint_shapes.shell_layer, rib on the 100 mm fillet), and one connecting
# piece takes the swell from one to the other
H_COL = J.P["H"]                                # a regular course, 450
D0 = -room_face(H)                              # how far the joint piece's room face stands out at its top: 78
K_EASE = math.tan(TH) * H_COL / D0              # exponent of the ease, so it leaves the joint piece at 35 degrees
R_TOP = 85.0                                    # plan fillet that matches the regular piece's rib (centreline 100)


def lip_depth(s):
    """how far the room face stands proud of the shell at height s above the joint piece: it leaves the joint piece
    on the same 35 degree slope and eases off over the whole piece, reaching the regular wall flat (tangent) at the
    top, D0 (1 - s/H)^k. Read one layer lower, so the bed layer stands out as far as the joint piece's top layer and
    the two meet flush"""
    return D0 * max(0.0, 1.0 - (s - lh) / H_COL) ** K_EASE


def col_layer(i):
    """connecting piece layer i, printed upright with its bed on the joint piece: the bed is the joint piece's top
    (wall face at -78, column on the R_PLAN fillet), the top is the regular piece (wall face at 0, rib on its fillet),
    and the room face eases between them over the whole course. Everything recedes as it rises, so nothing
    overhangs. Below the joint piece the same piece is turned over."""
    s = (i + 0.5) * lh
    _, reg = shell(s)
    path, base = shell(s, fillet=0)
    cv = void(s)
    d = lip_depth(s)
    r = R_TOP + (R_PLAN - R_TOP) * d / D0
    room = cv.buffer(B, 64).intersection(box(-1e3, -1e3, L + 1e3, 1.0)).union(box(0, -d, L, 1.0))
    room = room.buffer(r, 32).buffer(-r, 32).intersection(box(0, -1e3, L, 1.0))
    g = reg.union(base).union(room).difference(cv)
    p = cv.representative_point()                   # the regular piece's hole round the column, with the pockets its
    pocket = [Polygon(r) for q in getattr(reg, "geoms", [reg]) for r in q.interiors if Polygon(r).contains(p)]
    if s > H_COL / 2:                               # fillet leaves: open in the top half, so the piece above sits on
        g = g.difference(unary_union(pocket))       # bead, and solid below, so the joint piece's bed is carried
    g = g.buffer(0)
    return dict(i=i, s=s, void=None, outer=-d, geom=g, path=path)


def col_layers():
    return [col_layer(i) for i in range(int(round(H_COL / lh)))]


def column_main(folder, joint_tm):
    """the connecting piece: G-code, desk print, and the three-piece node plate (the connecting piece twice: the one
    below the joint piece is the same piece turned over, since the joint piece is the same at its top and its bed)"""
    cs = paths(col_layers())
    _, reg = J.shell_layer("oval")
    over = max(J._overhang(a["geom"], b["geom"]) for a, b in zip(cs, cs[1:] + [dict(geom=reg)]))
    print("bed past the joint piece's top: {:.0f} mm2".format(cs[0]["geom"].difference(layer_geom(58)["geom"]).area))
    p = dict(L=L, layer_H=lh, bead=B, speed=J.P["speed"])
    txt, t, stops = piece_test.gcode(dict(p=p, col=cs), "col", title="CONNECTING piece between the organic joint piece and "
                                     "the regular column piece (above as printed, below turned over)")
    with open(os.path.join(folder, "connector-organic.gcode"), "w") as f:
        f.write(txt)
    mass = sum(x["geom"].area for x in cs) * lh * J.P["density"] / 1e6
    print("connecting piece: {} layers, {:.0f} kg, {:.0f} min, {} pump stops, worst overhang {:.1f} mm".format(
        len(cs), mass, t / 60, stops, over))
    tm = T.build([x["geom"] for x in cs])
    desk = os.path.join(folder, "test-print")
    tm.export(os.path.join(desk, "connector-organic-1to12.stl"))
    sc = trimesh.Scene()
    y = 0.0
    for name, m in (("1 connector below (turn over)", tm), ("2 joint piece", joint_tm), ("3 connector above", tm)):
        m = m.copy()
        b = m.bounds
        m.apply_translation((-b[0][0], y - b[0][1], -b[0][2]))
        sc.add_geometry(m, geom_name=name)
        y += m.extents[1] + 8
    sc.export(os.path.join(desk, "node-organic-A1-plate.3mf"))
    sc.to_mesh().export(os.path.join(desk, "node-organic-3pieces-1to12.stl"))   # the same plate, one STL
    return cs, dict(stops=stops, minutes=round(t / 60), mass=round(mass), over=round(over, 1))


def main():
    ls = paths(layers())
    over = max(J._overhang(a["geom"], b["geom"]) for a, b in zip(ls, ls[1:]))
    tun = [(x["s"], x["void"]) for x in ls if x["void"]]
    area = sum(v[1] - v[0] for _, v in tun) * lh
    p = dict(L=L, layer_H=lh, bead=B, speed=J.P["speed"])
    txt, t, stops = piece_test.gcode(dict(p=p, col=ls), "col", title="JOINT piece, organic (590 tall), option 1 "
                                     "paths with pump stops (x = u along the course, y = n, z = s up the slope)")
    here = os.path.dirname(os.path.abspath(__file__))
    folder = os.path.normpath(os.path.join(here, "..", "details", "piece-test"))
    with open(os.path.join(folder, "joint-organic.gcode"), "w") as f:
        f.write(txt)
    mass = sum(x["geom"].area for x in ls) * lh * J.P["density"] / 1e6
    print("{} layers, {:.0f} kg, {:.0f} min, {} pump stops, worst overhang {:.1f} mm, ring {:.0f} mm2, "
          "room face {:.0f} .. {:.0f}".format(len(ls), mass, t / 60, stops, over, area,
                                              min(x["outer"] for x in ls), max(x["outer"] for x in ls)))
    tm = T.build([x["geom"] for x in ls])
    desk = os.path.join(folder, "test-print")
    tm.export(os.path.join(desk, "joint-organic-1to12.stl"))
    sc = trimesh.Scene()
    sc.add_geometry(tm, geom_name="joint piece, organic")
    sc.export(os.path.join(desk, "joint-organic-A1-plate.3mf"))
    print("desk print {:.1f} x {:.1f} x {:.1f} mm".format(*tm.extents))
    cs, cinfo = column_main(folder, tm)
    pts = lambda xs: [[[[round(a, 1), round(b, 1)] for a, b in LineString(c).simplify(0.5).coords]
                       for c in x["cons"]] for x in xs]
    with open(os.path.join(folder, "joint-organic.json"), "w") as f:
        json.dump(dict(lh=lh, layers=[T.outline(x["geom"], tol=0.8) for x in ls], paths=pts(ls), stops=stops,
                       minutes=round(t / 60), mass=round(mass), over=round(over, 1),
                       column=dict(cinfo, layers=[T.outline(x["geom"], tol=0.8) for x in cs], paths=pts(cs)),
                       regular=T.outline(J.shell_layer("oval")[1], tol=0.8)),
                  f, separators=(",", ":"))
    return ls


if __name__ == "__main__":
    main()
