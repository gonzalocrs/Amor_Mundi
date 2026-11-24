"""Slot audit (2026-11-21, Gonzalo's renders): walk the grown outer face of every course at mid-height, 1.5 cm inside
the new face (inside the new 3 cm outer wall), and report every stretch that is not inside any printed object
of that course (pieces + separate bands). A 2 mm head joint shows as ~2 mm; anything wider is a slot."""
import json, math, importlib.util
import Rhino, Rhino.Geometry as G

SAMPLES = r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\polyframe2\half-steps-course-samples.json"


def L_(n, p):
    s = importlib.util.spec_from_file_location(n, p); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


def audit(doc, rt, depth=0.015, n=4000, zfrac=0.5, gr=None):
    GR = L_("gr", r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\polyframe2\joined-pieces\grow.py")
    S = json.load(open(SAMPLES)); R = S[rt]; cs = R["courses"]; cx, cy = R["cx"], R["cy"]
    if gr is None:
        gr = GR.growth(S, rt)
        prot = json.load(open(r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\polyframe2\joined-pieces\_rib_protrusion_per_course.json"))[rt]
        for k, z, nn, mx in prot:
            if k > 0 and mx > 0.001:
                gr[k] = max(gr[k], mx + 0.01)
    root = rt + " complete v3e-ring-step::"
    jl = doc.Layers[doc.Layers.FindByFullPath(root + "printed pieces + rib (joined)", -1)]
    objs = [(o, o.Geometry.GetBoundingBox(True)) for o in doc.Objects.FindByLayer(jl)]
    out = []
    for k in range(len(cs)):
        z = cs[k]["z0"] + (cs[k]["z1"] - cs[k]["z0"]) * zfrac
        pl = G.Plane(G.Point3d(0, 0, z), G.Vector3d.ZAxis)
        crv = []
        for o, bb in objs:
            if bb.Min.Z <= z <= bb.Max.Z:
                ok, cc, pp = G.Intersect.Intersection.BrepPlane(o.Geometry, pl, 0.0005)
                if ok and cc:
                    crv += [(c, c.GetBoundingBox(True)) for c in G.Curve.JoinCurves(cc, 0.001) if c.IsClosed]
        base = GR.poly(cx, cy, cs[k]["rout"], z)
        ref = GR.offset(base, gr[k] - depth, z) if gr[k] > depth + 0.001 else GR.offset(base, -depth, z)
        if ref is None:
            out.append((k, "no ref curve")); continue
        ts = ref.DivideByCount(n, True)
        L = ref.GetLength()
        miss = []
        for t in ts:
            p = ref.PointAt(t)
            inside = False
            for c, bb in crv:
                if bb.Min.X - 1e-3 <= p.X <= bb.Max.X + 1e-3 and bb.Min.Y - 1e-3 <= p.Y <= bb.Max.Y + 1e-3:
                    if c.Contains(p, pl, 0.0005) != G.PointContainment.Outside:
                        inside = True; break
            miss.append(not inside)
        # group consecutive misses
        runs = []; i = 0; step = L / n
        while i < n:
            if miss[i]:
                j = i
                while j + 1 < n and miss[j + 1]:
                    j += 1
                p = ref.PointAt(ts[(i + j) // 2])
                runs.append(((j - i + 1) * step, round(p.X, 3), round(p.Y, 3)))
                i = j + 1
            else:
                i += 1
        out.append((k, round(z, 2), round(gr[k], 3), [r for r in runs if r[0] > 0.004]))
    return out
