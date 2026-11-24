"""Rib landings below the first course: keep only the part on the room side of the base ring (what you see),
so nothing lies on the ring's top, soffit or faces (the orange fans). Ring and ribs untouched."""
import time
import Rhino, Rhino.Geometry as G

PROG = r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\polyframe2\joined-pieces\_rebuild_progress.txt"

def log(s):
    open(PROG, "a").write(time.strftime("%H:%M:%S ") + s + "\n")

def run(doc, root):
    R = root + "::"
    lay = lambda n: doc.Layers[doc.Layers.FindByFullPath(R + n, -1)]
    fw = [o.Geometry for o in doc.Objects.FindByLayer(lay("base ring step - printed U formwork (3 cm)"))]
    fw = [g.ToBrep() if isinstance(g, G.Extrusion) else g for g in fw]
    loops = []
    for g in fw:
        ok, crvs, _ = G.Intersect.Intersection.BrepPlane(g, G.Plane(G.Point3d(0, 0, 2.6), G.Vector3d.ZAxis), 0.0005)
        loops += [c for c in G.Curve.JoinCurves(crvs or [], 0.001) if c.IsClosed]
    inner = min(loops, key=lambda c: abs(G.AreaMassProperties.Compute(c).Area))
    inner.Translate(G.Vector3d(0, 0, 2.0 - 2.6))
    ex = G.Extrusion.Create(inner, -0.799, True)
    room = ex.ToBrep()
    if room.GetBoundingBox(True).Max.Z < 2.7:
        room = G.Extrusion.Create(inner, 0.799, True).ToBrep()
    if room.SolidOrientation == G.BrepSolidOrientation.Inward:
        room.Flip()
    el = lay("rib ends outside the printed courses (landings on the base ring, crown domes)")
    done = fail = 0
    for o in list(doc.Objects.FindByLayer(el)):
        if o.Geometry.GetBoundingBox(True).Max.Z > 2.81:
            continue
        r = G.Brep.CreateBooleanIntersection(o.Geometry, room, 0.0005)
        if r:
            a = o.Attributes.Duplicate()
            doc.Objects.Delete(o, True)
            for x in r:
                if x.IsValid and x.IsSolid:
                    doc.Objects.AddBrep(x, a)
            done += 1
        else:
            fail += 1
    doc.ClearUndoRecords(True)
    res = "landings %s trimmed %d failed %d" % (root[:5], done, fail)
    log(res)
    return res
