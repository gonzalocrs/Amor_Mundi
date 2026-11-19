"""The two pieces of the roof, oval rib (Gonzalo, 2026-10-18: "keep only the one piece joint version, oval one"):

  REGULAR piece  the column piece with the oval rib (no ring): every layer the same single continuous path.
  JOINT piece    rib + ring + node in one print (scripts/joint_shapes.py, path from scripts/joint_toolpath.py).

Both print upright, s (up the slope) vertical, 1200 long x 450 high. On the roof they stack in courses: regular
courses, and a joint course wherever a ring runs. The column channels line up from course to course (head joints
do not stagger), and the ring tunnels line up along the course.

  JOINT piece, no stops (scripts/joint_nostop.py): the same joint printed as one continuous path; the two tunnel end
                 beads are cut out green.

`python scripts/joint_pieces.py` writes details/piece-test/regular-oval.gcode, joint-oval.gcode,
joint-oval-nostop.gcode and joint-viewer.json (data for the 3D view).
"""
import json
import os

from shapely.geometry import LineString, box
from shapely.ops import unary_union

import joint_shapes as J
import joint_toolpath as T
import piece_test

SHAPE = "oval"


def _r(g):
    return J._round(g)


def regular():
    path, poly = J.shell_layer(SHAPE)
    n = int(round(J.P["H"] / J.P["lh"]))
    lays = [dict(z=(i + 1) * J.P["lh"], cons=[path if i % 2 == 0 else list(reversed(path))]) for i in range(n)]
    return path, poly, lays


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    folder = os.path.normpath(os.path.join(here, "..", "details", "piece-test"))
    p = dict(L=J.P["L"], layer_H=J.P["lh"], bead=J.B, speed=J.P["speed"])
    out = {}

    # regular piece
    path, poly, rl = regular()
    txt, t, stops = piece_test.gcode(dict(p=p, col=rl), "col", title="REGULAR piece, oval rib, printed upright "
                                     "(x = u along the course, y = n, z = s up the slope)")
    with open(os.path.join(folder, "regular-oval.gcode"), "w") as f:
        f.write(txt)
    lt = LineString(path).length / J.P["speed"]
    mass = poly.area * J.P["H"] * J.P["density"] / 1e6
    out["regular"] = dict(poly=_r(poly), path=[[round(x), round(y)] for x, y in LineString(path).simplify(0.5).coords],
                          time=round(t / 60), stops=stops, mass=round(mass), t=round(lt))
    print("regular: {:.0f} min, {} stops, {:.0f} s a layer, {:.0f} kg".format(t / 60, stops, lt, mass))

    # joint piece
    lays, tj, sj = T.main(SHAPE)
    st = J.study(SHAPE)
    kinds, seq, seqcut = [], [], []
    cut = box(300, -1e3, J.P["L"] + 1, 1e3)
    for x in st["layers"]:
        for g, sq in ((x["geom"], seq), (x["geom"].intersection(cut), seqcut)):
            k = json.dumps(_r(g))
            if k not in kinds:
                kinds.append(k)
            sq.append(kinds.index(k))
    lh = J.P["lh"]
    ringsec = unary_union([box(x["void"][0], x["s"] - lh / 2, x["void"][1], x["s"] + lh / 2)
                           for x in st["layers"] if x["void"]]).simplify(0.5)
    c = st["cages"]
    out["joint"] = dict(
        kinds=[json.loads(k) for k in kinds], seq=seq, seqcut=seqcut,
        paths=[[[[round(a), round(b)] for a, b in LineString(cc).simplify(0.5).coords] for cc in l["cons"]] for l in lays],
        t=[round(sum(LineString(cc).length for cc in l["cons"]) / J.P["speed"]) for l in lays],
        over=[round(o, 1) for o in st["overhang"]], tunnel=st["tunnel"],
        time=round(tj / 60), stops=sj, mass=round(st["mass"]), pour=round(st["pour"]))
    # joint piece without pump stops
    import joint_nostop as N
    r, tn, sn = N.main()
    kinds, seq, seqcut = [], [], []
    for x in r["layers"]:
        for g, sq in ((x["geom"], seq), (x["geom"].intersection(cut), seqcut)):
            k = json.dumps(_r(g))
            if k not in kinds:
                kinds.append(k)
            sq.append(kinds.index(k))
    out["nostop"] = dict(
        kinds=[json.loads(k) for k in kinds], seq=seq, seqcut=seqcut,
        paths=[[[[round(a), round(b)] for a, b in LineString(cc).simplify(0.5).coords] for cc in x["cons"]]
               for x in r["layers"]],
        t=[round(v) for v in r["t"]], over=[round(o, 1) for o in r["over"]], tunnel=r["tunnel"],
        time=round(tn / 60), stops=sn, mass=round(r["mass"]), worst=round(r["max_over"], 1),
        tunnel_area=round(r["sec"].area / 100))
    out.update(
        L=J.P["L"], H=J.P["H"], lh=lh, bead=J.B, speed=J.P["speed"], bar=J.P["bar"],
        colvoid=[[round(a, 1), round(b, 1)] for a, b in J.col_void(SHAPE).simplify(0.5).exterior.coords[:-1]],
        ringsec=[[round(a, 1), round(b, 1)] for a, b in ringsec.exterior.coords[:-1]],
        colbars=[[round(u, 1), round(n, 1)] for u, n in c["col"]],
        ringbars=[[round(n, 1), round(s, 1)] for n, s in c["ring"]])
    with open(os.path.join(folder, "joint-viewer.json"), "w") as f:
        json.dump(out, f, separators=(",", ":"))
    print("wrote", folder)


if __name__ == "__main__":
    main()
