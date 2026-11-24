"""Ribs as clean pipes (Gonzalo 2026-11-21: "if we have the tubes it should be easy. is like make a pipe").
Source: the approved rib net, "cast rib cores - pushed in" and "printed rib tubes - pushed in" (one straight cylinder
per segment, approved diameters and push-in depth, untouched). Pipe = the segment's cylinder (same axis, same radius)
+ a ball of the same radius at both ends, so every fork and every bend is closed (no wedge gaps, no booleans between
pipes). Ends: nothing above the crown top (balls there are cut flush 2 mm below it), nothing below the base ring top.
Baked to "rib pipes - printed tube" and "rib pipes - cast core" under each roof, grouped per segment."""
import Rhino, Rhino.Geometry as G
import scriptcontext

TOL = 0.0005
SRC = {"tube": "printed rib tubes - pushed in (bottom 4 cm showing, same sizes)",
       "core": "cast rib cores - pushed in (bottom 4 cm showing, same sizes)"}
DST = {"tube": "rib pipes - printed tube", "core": "rib pipes - cast core"}
LEVELS = {"15x10": (2.40, 11.90), "10x10": (2.40, 7.792)}   # 2026-11-23: columns 2.0 m, roofs moved down 400 mm (were 2.80 / 12.30 / 8.192)


def axis_of(brep):
    for f in brep.Faces:
        ok, cyl = f.UnderlyingSurface().TryGetCylinder(0.002)
        if ok:
            ax = cyl.Axis; ax.Unitize(); c = cyl.Center
            ts = [(G.Point3d(v.Location) - c) * ax for v in brep.Vertices]
            if not ts:
                bb = brep.GetBoundingBox(True); ts = [(p - c) * ax for p in bb.GetCorners()]
            return c + ax * min(ts), c + ax * max(ts), cyl.Radius
    return None


def clip(b, zlo, zhi):
    bb = b.GetBoundingBox(True)
    if bb.Min.Z >= zlo and bb.Max.Z <= zhi:
        return [b]
    box = G.Box(G.BoundingBox(bb.Min.X - 1, bb.Min.Y - 1, zlo, bb.Max.X + 1, bb.Max.Y + 1, zhi)).ToBrep()
    r = G.Brep.CreateBooleanIntersection(b, box, TOL)
    return [x for x in (r or []) if x.IsSolid]


def layer(doc, path, color):
    i = doc.Layers.FindByFullPath(path, -1)
    if i >= 0:
        return i
    parent, name = path.rsplit("::", 1)
    L = Rhino.DocObjects.Layer(); L.Name = name; L.Color = color
    L.ParentLayerId = doc.Layers[doc.Layers.FindByFullPath(parent, -1)].Id
    return doc.Layers.Add(L)


def run(doc, rt):
    root = rt + " complete v3e-ring-step"
    zlo, zhi = LEVELS[rt]
    zhi -= 0.002
    stats = {}
    import System.Drawing as SD
    for kind in ("core", "tube"):
        src = doc.Layers[doc.Layers.FindByFullPath(root + "::" + SRC[kind], -1)]
        li = layer(doc, root + "::" + DST[kind], SD.Color.FromArgb(235, 232, 225) if kind == "tube" else SD.Color.FromArgb(150, 150, 150))
        n_seg = n_ball = n_clip = 0
        for o in doc.Objects.FindByLayer(src):
            ax = axis_of(o.Geometry)
            if ax is None:
                continue
            a, b, r = ax
            gi = doc.Groups.Add()
            at = Rhino.DocObjects.ObjectAttributes(); at.LayerIndex = li; at.AddToGroup(gi)
            at.SetUserString("source_segment", str(o.Id))
            seg = o.Geometry.DuplicateBrep()
            if seg.SolidOrientation == G.BrepSolidOrientation.Inward:
                seg.Flip()
            for x in clip(seg, zlo, zhi):
                doc.Objects.AddBrep(x, at); n_seg += 1
            for p in (a, b):
                sp = G.Sphere(p, r).ToBrep()
                cl = clip(sp, zlo, zhi)
                if len(cl) != 1 or cl[0].GetBoundingBox(True).Diagonal.Length < sp.GetBoundingBox(True).Diagonal.Length - 1e-4:
                    n_clip += 1
                for x in cl:
                    doc.Objects.AddBrep(x, at); n_ball += 1
        stats[kind] = (n_seg, n_ball, n_clip)
    doc.Views.Redraw()
    return stats
