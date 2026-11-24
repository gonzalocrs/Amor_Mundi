"""light check: sample points on every rib pipe (cylinders: 9 along x 16 around; balls: 26 points) vs the grown
outer face of the course at that height (plan containment). One roof per call."""
import json, math, importlib.util, collections
import Rhino.Geometry as G


def samples(brep):
    pts = []
    for f in brep.Faces:
        s = f.UnderlyingSurface()
        ok, cyl = s.TryGetCylinder(0.002)
        if ok or True:
            du, dv = f.Domain(0), f.Domain(1)
            for i in range(9):
                for j in range(16):
                    u = du.ParameterAt(i / 8.0); v = dv.ParameterAt(j / 16.0)
                    if f.IsPointOnFace(u, v) != G.PointFaceRelation.Exterior:
                        pts.append(f.PointAt(u, v))
    return pts


def run(doc, rt):
    s = importlib.util.spec_from_file_location("gr", r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\polyframe2\joined-pieces\grow.py")
    GR = importlib.util.module_from_spec(s); s.loader.exec_module(GR)
    S = json.load(open(GR.SAMPLES)); R = S[rt]; cs = R["courses"]; cx, cy = R["cx"], R["cy"]
    gr = GR.growth(S, rt)
    prot = json.load(open(r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\polyframe2\joined-pieces\_rib_protrusion_per_course.json"))[rt]
    for k, z, n, mx in prot:
        if k > 0 and mx > 0.001:
            gr[k] = max(gr[k], mx + 0.01)
    faces = {k: (GR.offset(GR.poly(cx, cy, cs[k]["rout"], 0), gr[k], 0) if gr[k] > 0.001 else GR.poly(cx, cy, cs[k]["rout"], 0)) for k in range(len(cs))}
    z0s = [c["z0"] for c in cs]
    L = doc.Layers[doc.Layers.FindByFullPath(rt + " complete v3e-ring-step::rib pipes - printed tube", -1)]
    out = collections.Counter(); worst = 0.0; n = 0; where = []
    pl = G.Plane.WorldXY
    for o in doc.Objects.FindByLayer(L):
        for p in samples(o.Geometry):
            n += 1
            if p.Z < z0s[0]:
                continue
            k = max(i for i in range(len(cs)) if z0s[i] <= p.Z + 1e-6)
            q = G.Point3d(p.X, p.Y, 0)
            if faces[k].Contains(q, pl, 0.0005) == G.PointContainment.Outside:
                ok, t = faces[k].ClosestPoint(q)
                dd = faces[k].PointAt(t).DistanceTo(q)
                if dd > 0.001:
                    out[k] += 1
                    if dd > worst:
                        worst = dd; where = (round(p.X, 2), round(p.Y, 2), round(p.Z, 2))
    return "%s pipe sample points %d, outside the grown face %d %s, worst %.1f mm at %s" % (rt, n, sum(out.values()), dict(out), worst * 1000, where)
