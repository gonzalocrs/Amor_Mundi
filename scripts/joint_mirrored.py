"""The joint piece with the mirrored ring tunnel (Gonzalo's sketch, drawn as "c - RIB + RING: THE JOINT PIECE OF
OPTION A" in presentation/v2/pages.py mirrored_drop): the option 1 joint piece (scripts/joint_shapes.py, oval rib,
250 x 250 ring) above its widest layer (s = 155) is kept and mirrored under it, so the course is 2 x (450 - 155) =
590 tall, the tunnel is a pointed diamond (floor opens out and crown closes in, both 7 mm a layer) and the band
above the crown is repeated under the floor.

The layers are the same plan shapes in a new order, so each keeps its option 1 path (scripts/joint_toolpath.py,
with pump stops).

`python scripts/joint_mirrored.py` writes details/piece-test/joint-mirrored.gcode and
details/piece-test/test-print/joint-mirrored-1to12.stl and joint-mirrored-A1-plate.3mf (desk print, as
scripts/test_print.py).
"""
import os

import trimesh

import joint_shapes as J
import joint_toolpath as TP
import piece_test
import test_print as T

lh = J.P["lh"]
AXIS = 155.0                                    # s of the widest tunnel layer (the centre of the 250 circle)


def order(n):
    """layer indices of the mirrored piece, bottom to top: the top part reversed, the widest layer once, the top"""
    k = int(round(AXIS / lh - 0.5))             # layer 15 spans s 150..160
    top = list(range(k + 1, n))
    return list(reversed(top)) + [k] + top


def layers():
    src = TP.layer_paths("oval")
    out = []
    for j, i in enumerate(order(len(src))):
        x = dict(src[i])
        x["z"] = (j + 1) * lh
        x["src"] = i
        out.append(x)
    return out


def main():
    ls = layers()
    over = max(J._overhang(a["geom"], b["geom"]) for a, b in zip(ls, ls[1:]))
    p = dict(L=J.P["L"], layer_H=lh, bead=J.B, speed=J.P["speed"])
    txt, t, stops = piece_test.gcode(dict(p=p, col=ls), "col", title="JOINT piece, mirrored ring tunnel (590 tall), "
                                     "option 1 paths with pump stops (x = u along the course, y = n, z = s up the slope)")
    here = os.path.dirname(os.path.abspath(__file__))
    folder = os.path.normpath(os.path.join(here, "..", "details", "piece-test"))
    with open(os.path.join(folder, "joint-mirrored.gcode"), "w") as f:
        f.write(txt)
    mass = sum(x["geom"].area for x in ls) * lh * J.P["density"] / 1e6
    print("{} layers, {:.0f} mm tall, {:.0f} kg, {:.0f} min, {} pump stops, worst overhang {:.1f} mm".format(
        len(ls), len(ls) * lh, mass, t / 60, stops, over))
    tm = T.build([x["geom"] for x in ls])
    desk = os.path.join(folder, "test-print")
    tm.export(os.path.join(desk, "joint-mirrored-1to12.stl"))
    sc = trimesh.Scene()
    sc.add_geometry(tm, geom_name="joint piece, mirrored tunnel")
    sc.export(os.path.join(desk, "joint-mirrored-A1-plate.3mf"))
    print("desk print {:.1f} x {:.1f} x {:.1f} mm, {:.0f} g PLA if solid".format(*tm.extents, tm.volume / 1e3 * 1.24))


if __name__ == "__main__":
    main()
