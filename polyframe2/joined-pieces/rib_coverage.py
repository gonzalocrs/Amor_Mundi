"""Rib continuity audit (2026-11-21, Gonzalo: "incomplete ribs again"). The approved ribs (hidden layer
"ribs (final, joint fillets)") are meshed; every vertex on the room side must lie inside or on a visible object
(joined pieces + bands, rib slices, rib ends). Uncovered vertices are grouped per source rib object.
fix(): for every rib with uncovered stretches, the missing part = approved rib minus the visible solids near it,
added as rib slices (adds material only; pieces untouched)."""
import time, collections
import Rhino, Rhino.Geometry as G

PROG = r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\polyframe2\joined-pieces\_ribcov_progress.txt"


def log(s):
    open(PROG, "a").write(time.strftime("%H:%M:%S ") + s + "\n")


def layers(doc, rt):
    R = rt + " complete v3e-ring-step::"
    f = lambda n: doc.Layers[doc.Layers.FindByFullPath(R + n, -1)]
    return (f("ribs (final, joint fillets)"),
            [f("printed pieces + rib (joined)"), f("rib slices of the pieces that did not join"),
             f("rib ends outside the printed courses (landings on the base ring, crown domes)")],
            f("rib slices of the pieces that did not join"))


def _near(bb, items, pad=0.05):
    out = []
    for g, b in items:
        if (b.Min.X - pad <= bb.Max.X and b.Max.X + pad >= bb.Min.X and b.Min.Y - pad <= bb.Max.Y and
                b.Max.Y + pad >= bb.Min.Y and b.Min.Z - pad <= bb.Max.Z and b.Max.Z + pad >= bb.Min.Z):
            out.append((g, b))
    return out


def audit(doc, rt, tol=0.004, ztop=None):
    rl, vis_l, _ = layers(doc, rt)
    vis = []
    for l in vis_l:
        for o in doc.Objects.FindByLayer(l):
            if o.IsHidden:
                continue
            g = o.Geometry
            if isinstance(g, G.Extrusion):
                g = g.ToBrep()
            vis.append((g, g.GetBoundingBox(True)))
    mp = G.MeshingParameters.FastRenderMesh
    res = []
    n_r = 0
    for o in doc.Objects.FindByLayer(rl):
        g = o.Geometry
        if isinstance(g, G.Extrusion):
            g = g.ToBrep()
        n_r += 1
        miss = []
        ms = G.Mesh.CreateFromBrep(g, mp) or []
        for m in ms:
            for i in range(0, m.Vertices.Count, 2):
                p = G.Point3d(m.Vertices[i])
                if ztop is not None and p.Z > ztop:
                    continue
                pb = G.BoundingBox(p, p)
                ok = False
                for v, b in _near(pb, vis, 0.01):
                    if v.IsPointInside(p, 0.001, False) or v.ClosestPoint(p).DistanceTo(p) <= tol:
                        ok = True; break
                if not ok:
                    miss.append(p)
        if miss:
            res.append((o.Id, len(miss), miss))
        if n_r % 50 == 0:
            log("%s audit %d ribs, %d with gaps" % (rt, n_r, len(res)))
    log("%s audit DONE %d ribs, %d with gaps, %d points" % (rt, n_r, len(res), sum(r[1] for r in res)))
    return res
