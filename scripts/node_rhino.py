"""Rhino file of the node lock, both versions side by side (Gonzalo 2026-10-19)

Full scale, mm, in the print frame: x = along the course (u), y = through the roof (n, room side negative), z = up
the slope (s), the three pieces stacked as they go together. Version 1 at x = 0, version 2 at x = 1600.
  1: column piece below the ring = the flared piece turned over (bed to bed under the beam, no boss there); the
     beam carries the bosses into the column piece above.
  2: column piece below the ring printed upright on a printable flare, with its own bosses into the beam.
Each piece is a mesh, one flat band per 10 mm layer; the bosses are on their own layer, and the print paths are
polylines, one per contour, as printed (the ones added for the boss on their own sublayer).

`python scripts/node_rhino.py` writes details/piece-test/node-boss-lock.3dm.
"""
import os

import rhino3dm as r3
import trimesh
from shapely.affinity import scale as sscale

import joint_boss as JB
import joint_flare as F
import joint_shapes as J
import test_print as T

L, H, lh = J.P["L"], J.P["H"], J.P["lh"]
GAP = 1600.0


def mesh(lays, z0, flip=False):
    """one flat band per layer, stacked from z0 (flip: the piece turned over, about the course's mid point)"""
    parts = []
    for i, g in enumerate(lays):
        z = z0 + i * lh
        for q in getattr(g, "geoms", [g]):
            if q.geom_type == "Polygon" and q.area > 1:
                m = trimesh.creation.extrude_polygon(q, lh)
                m.apply_translation((0, 0, z))
                parts.append(m)
    m = trimesh.util.concatenate(parts)
    rm = r3.Mesh()
    for v in m.vertices:
        rm.Vertices.Add(float(v[0]), float(v[1]), float(v[2]))
    for f in m.faces:
        rm.Faces.AddFace(int(f[0]), int(f[1]), int(f[2]))
    rm.Normals.ComputeNormals()
    rm.Compact()
    return rm


def layer(model, name, color, parent=None):
    ly = r3.Layer()
    ly.Name = name
    ly.Color = color
    if parent is not None:
        ly.ParentLayerId = model.Layers.FindIndex(parent).Id
    return model.Layers.Add(ly)


def add_mesh(model, m, li, dx):
    m.Translate(r3.Vector3d(dx, 0, 0))
    a = r3.ObjectAttributes()
    a.LayerIndex = li
    model.Objects.AddMesh(m, a)


def add_paths(model, ls, z0, dx, li_main, li_boss, flip=False):
    for x in ls:
        nb = x.get("nbase", len(x["cons"]))
        for j, c in enumerate(x["cons"]):
            z = x["z"] - lh / 2
            if flip:
                pts = [r3.Point3d(L - p[0] + dx, p[1], z0 + H - z) for p in c]
            else:
                pts = [r3.Point3d(p[0] + dx, p[1], z0 + z) for p in c]
            a = r3.ObjectAttributes()
            a.LayerIndex = li_boss if j >= nb else li_main
            model.Objects.AddPolyline(r3.Point3dList(pts), a)


def main():
    nd, fl, bm = T.node()
    up = T.flared_upright()
    bm2, bsm = T.lipped(bm, fl[0])
    up2, bsu = T.lipped(up, bm[0])
    below1 = [sscale(g, -1, 1, origin=(L / 2, 0)) for g in reversed(fl)]
    pb = JB.lipped(JB.beam(), fl[0])                 # paths
    pu = JB.lipped(JB.column_upright(), bm[0])
    pf = F.layers()

    model = r3.File3dm()
    model.Settings.ModelUnitSystem = r3.UnitSystem.Millimeters
    grey, orange, dark = (190, 186, 175, 255), (184, 70, 46, 255), (80, 80, 74, 255)
    for v, title in ((1, "Version 1 - column below turned over"), (2, "Version 2 - column below printed upright")):
        dx = (v - 1) * GAP
        top = layer(model, title, dark)
        lp = layer(model, "pieces", grey, top)
        lb = layer(model, "bosses", orange, top)
        lpath = layer(model, "print paths", dark, top)
        lpb = layer(model, "print paths - boss", orange, top)
        if v == 1:
            add_mesh(model, mesh(below1, 0), lp, dx)
            add_paths(model, pf, 0, dx, lpath, lpb, flip=True)
        else:
            add_mesh(model, mesh(up2, 0), lp, dx)
            add_mesh(model, mesh(bsu, H), lb, dx)
            add_paths(model, pu, 0, dx, lpath, lpb)
        add_mesh(model, mesh(bm2, H), lp, dx)
        add_mesh(model, mesh(bsm, 2 * H), lb, dx)
        add_paths(model, pb, H, dx, lpath, lpb)
        add_mesh(model, mesh(fl, 2 * H), lp, dx)
        add_paths(model, pf, 2 * H, dx, lpath, lpb)
    here = os.path.dirname(os.path.abspath(__file__))
    fn = os.path.normpath(os.path.join(here, "..", "details", "piece-test", "node-boss-lock.3dm"))
    model.Write(fn, 7)
    print("wrote", fn, os.path.getsize(fn) // 1024, "kB")


if __name__ == "__main__":
    main()
