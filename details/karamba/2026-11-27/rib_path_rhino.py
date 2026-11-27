"""Bake the 15x10 rib path for the visible Rhino: layer 'rib path analysis 15x10' with sublayers 'rib net' (every
rib bar as a grey solid of its core D, base and crown rings faint) and 'path' (the analysed rib in strong red).
Reads forces-15x10.json + rib-path/rib-path-15x10.json. Run inside Rhino; returns the bounding box."""
import os, json, math, System, Rhino
import Rhino.Geometry as G
HERE = r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\details\karamba\2026-11-27"
RIB_D = {"rib_bottom": 0.22, "rib_middle": 0.16, "rib_top": 0.12}


def tube(pa, pb, r, n=16):
    ax = pb - pa; ax.Unitize()
    ref = G.Vector3d.ZAxis if abs(ax.Z) < 0.95 else G.Vector3d.XAxis
    y = G.Vector3d.CrossProduct(ref, ax); y.Unitize(); z = G.Vector3d.CrossProduct(ax, y); z.Unitize()
    m = G.Mesh()
    for p in (pa, pb):
        for k in range(n):
            a = 2 * math.pi * k / n; m.Vertices.Add(p + y * (r * math.cos(a)) + z * (r * math.sin(a)))
    for k in range(n): m.Faces.AddFace(k, (k + 1) % n, n + (k + 1) % n, n + k)
    m.Normals.ComputeNormals(); m.Compact(); return m


def box(pa, pb, b, h):
    ax = pb - pa; ax.Unitize(); y = G.Vector3d.CrossProduct(G.Vector3d.ZAxis, ax); y.Unitize(); z = G.Vector3d.CrossProduct(ax, y)
    pl = G.Plane(pa, y, z); L = pa.DistanceTo(pb)
    bx = G.Box(pl, G.Interval(-b / 2, b / 2), G.Interval(-h / 2, h / 2), G.Interval(0, L))
    return G.Mesh.CreateFromBox(bx, 1, 1, 1)


def layer(doc, path, colour):
    i = doc.Layers.FindByFullPath(path, -1)
    if i < 0:
        parent = None
        if "::" in path:
            pp = path.rsplit("::", 1)[0]; parent = doc.Layers.FindByFullPath(pp, -1)
            if parent < 0: parent = layer(doc, pp, System.Drawing.Color.Black)
        l = Rhino.DocObjects.Layer(); l.Name = path.split("::")[-1]; l.Color = colour
        if parent is not None: l.ParentLayerId = doc.Layers[parent].Id
        i = doc.Layers.Add(l)
    else:
        for o in doc.Objects.FindByLayer(doc.Layers[i]) or []: doc.Objects.Delete(o, True)
    return i


def bake(doc):
    D = json.load(open(os.path.join(HERE, "forces-15x10.json"))); P = json.load(open(os.path.join(HERE, "rib-path", "rib-path-15x10.json")))
    N, E = D["nodes"], D["els"]; path = set(b["element"] for b in P["bars"])
    root = "rib path analysis 15x10"
    ln = layer(doc, root + "::rib net", System.Drawing.Color.FromArgb(205, 205, 205))
    lp = layer(doc, root + "::path", System.Drawing.Color.FromArgb(215, 0, 20))
    an = Rhino.DocObjects.ObjectAttributes(); an.LayerIndex = ln
    ap = Rhino.DocObjects.ObjectAttributes(); ap.LayerIndex = lp
    bb = G.BoundingBox.Empty
    for i, (g, a, b) in enumerate(E):
        pa, pb = G.Point3d(*N[a]), G.Point3d(*N[b])
        if g in RIB_D:
            m = tube(pa, pb, RIB_D[g] / 2 * (1.25 if i in path else 1.0))   # path drawn a touch fatter so it reads in front
            doc.Objects.AddMesh(m, ap if i in path else an); bb.Union(m.GetBoundingBox(True))
        elif g in ("ring", "crown"):
            s = 0.40 if g == "ring" else 0.25
            m = box(pa, pb, s, s); doc.Objects.AddMesh(m, an); bb.Union(m.GetBoundingBox(True))
    for l in doc.Layers:
        if l.IsDeleted: continue
        l.IsVisible = l.FullPath == root or l.FullPath.startswith(root + "::")
    return bb
