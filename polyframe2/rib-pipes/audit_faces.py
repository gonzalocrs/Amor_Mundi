"""Joint audit of the grown outer face: offset curves of each course outline (3 mm and 3 cm inside the grown face) at
3 heights; every stretch outside all printed objects (pieces + bands) is listed with its length. 2 mm = head joint."""
import json, importlib.util
import Rhino.Geometry as G

TOL = 0.0005
LAYERS = ("printed pieces (closed solids, 3 cm walls, lid 3, groove 6x4)", "top course = printed U formwork for the crown ring",
          "growth bands (outer face, per piece)")


def L_(n, p):
    s = importlib.util.spec_from_file_location(n, p); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


def run(doc, rt):
    GR = L_("gr", r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\polyframe2\joined-pieces\grow.py")
    S = json.load(open(GR.SAMPLES)); R = S[rt]; cs = R["courses"]; cx, cy = R["cx"], R["cy"]
    gr = GR.growth(S, rt)
    prot = json.load(open(r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\polyframe2\joined-pieces\_rib_protrusion_per_course.json"))[rt]
    for k, z, n, mx in prot:
        if k > 0 and mx > 0.001:
            gr[k] = max(gr[k], mx + 0.01)
    objs = []
    for ln in LAYERS:
        l = doc.Layers[doc.Layers.FindByFullPath(rt + " complete v3e-ring-step::" + ln, -1)]
        for o in doc.Objects.FindByLayer(l):
            g = o.Geometry.ToBrep() if isinstance(o.Geometry, G.Extrusion) else o.Geometry
            objs.append((g, g.GetBoundingBox(True)))
    out = []
    for k in range(len(cs)):
        joints = []; slots = []
        for f in (0.15, 0.5, 0.85):
            z = cs[k]["z0"] + (cs[k]["z1"] - cs[k]["z0"]) * f
            pl = G.Plane(G.Point3d(0, 0, z), G.Vector3d.ZAxis)
            crv = []
            for g, bb in objs:
                if bb.Min.Z <= z <= bb.Max.Z:
                    ok, cc, pp = G.Intersect.Intersection.BrepPlane(g, pl, TOL)
                    if ok and cc:
                        crv += [x for x in G.Curve.JoinCurves(cc, 0.001) if x.IsClosed]
            base = GR.poly(cx, cy, cs[k]["rout"], z)
            for dep in (0.003, 0.03):
                ref = GR.offset(base, gr[k] - dep, z) if gr[k] > dep else GR.offset(base, -dep, z)
                ts = []
                for x in crv:
                    ii = G.Intersect.Intersection.CurveCurve(ref, x, 0.0002, 0.0002)
                    if ii:
                        ts += [e.ParameterA for e in ii]
                ts = sorted(set(ts)); dom = ref.Domain; Lt = ref.GetLength()
                for i in range(len(ts)):
                    a = ts[i]; b = ts[(i + 1) % len(ts)]
                    L = ref.GetLength(G.Interval(a, b)) if b > a else Lt - ref.GetLength(G.Interval(b, a))
                    if L < 0.0005:
                        continue
                    mid = (a + b) / 2 if b > a else (a + (b + dom.Length)) / 2
                    if mid > dom.T1:
                        mid -= dom.Length
                    p = ref.PointAt(mid)
                    if all(x.Contains(p, pl, 0.0003) == G.PointContainment.Outside for x in crv):
                        (slots if L > 0.004 else joints).append((round(L * 1000, 1), round(p.X, 2), round(p.Y, 2), f, dep))
        out.append((k, len(joints), max([j[0] for j in joints] or [0]), slots))
    return out
