"""Fix the wedge-shaped growth-band joints (Gonzalo 2026-11-24: 'error here' - a dark slit on the 15x10).
At a few joints one growth band ends on a slanted cut instead of square, so the joint is 2 mm at the inner face but
opens to 10-31 mm at the outer face. For every band joint whose outer opening is above 5 mm:
- the 'good' band is the one whose end faces are all parallel (square end); its largest end face gives the joint plane;
- the 'bad' band is rebuilt only at that end: its own cross-section, cut 35 mm inside the end, is extruded square to
  the joint plane and unioned with the band, and everything beyond a plane 2.0 mm off the good band's end face is cut
  away (this also removes the triangular leftover). Nothing else is touched: no other band, no printed piece, no shell.
Checks per joint: valid closed solid, gaps to the neighbour at the end corners (target 2.0 mm), radial step of the
outer face across the joint. Runs in Rhino on whatever document is active; returns a report list."""
import math, System, Rhino
import Rhino.Geometry as G
TOL = 0.001
CEN = {"15x10": (85.0, 0.0), "10x10": (85.0, -20.0)}
BANDS = "%s complete v3e-ring-step::growth bands (outer face, per piece)"


def end_faces(b, J, r=0.35):
    out = []
    for f in b.Faces:
        ok, pl = f.TryGetPlane(0.0005)
        if not ok or abs(pl.Normal.Z) > 0.2: continue
        am = G.AreaMassProperties.Compute(f); c = am.Centroid
        if c.DistanceTo(J) < r: out.append((am.Area, pl, c))
    return out


def spread(es):
    if not es: return 9.0
    n0 = es[0][1].Normal
    return max(1 - abs(e[1].Normal * n0) for e in es)


def joint_point(b1, b2):
    best = None
    for v in b1.Vertices:
        dd = v.Location.DistanceTo(b2.ClosestPoint(v.Location))
        if best is None or dd < best[0]: best = (dd, v.Location)
    return best[1]


def corner_gaps(b, other):
    ds = sorted(v.Location.DistanceTo(other.ClosestPoint(v.Location)) for v in b.Vertices)
    return [round(x * 1000, 2) for x in ds[:4]]


def section_loops(B, n, P0, inset):
    Q = G.Plane(P0 + n * inset, n)
    ok, crvs, pts = G.Intersect.Intersection.BrepPlane(B, Q, TOL)
    return [c for c in (G.Curve.JoinCurves(crvs, 0.002) if crvs else []) if c.IsClosed]


def rebuild(B, n, P0, inset=None):
    """extend the band's own full cross-section (outer loop with any holes, taken where the section is complete) square
    up to the target plane, union, and cut everything beyond the plane"""
    ref = section_loops(B, n, P0, 0.15); L = sum(c.GetLength() for c in ref)
    for ins in ((inset,) if inset else (0.04, 0.06, 0.08, 0.10, 0.12)):
        loops = section_loops(B, n, P0, ins)
        if loops and len(loops) == len(ref) and abs(sum(c.GetLength() for c in loops) - L) < 0.02 * L: break
    else:
        return None, "no complete section"
    faces = G.Brep.CreatePlanarBreps(loops, TOL)
    if not faces: return None, "planar section failed"
    fills = []
    for fb in faces:
        for f in fb.Faces:
            c = G.AreaMassProperties.Compute(f).Centroid
            path = G.LineCurve(c, c - n * (ins + 0.01))
            e = f.CreateExtrusion(path, True)
            if e is None: return None, "extrusion failed"
            if e.SolidOrientation == G.BrepSolidOrientation.Inward: e.Flip()
            fills.append(e)
    U = G.Brep.CreateBooleanUnion([B] + fills, TOL)
    if not U: return None, "union failed"
    box = G.Box(G.Plane(P0, -n), G.Interval(-0.6, 0.6), G.Interval(-0.6, 0.6), G.Interval(0, 0.4)).ToBrep()
    D = G.Brep.CreateBooleanDifference(U[0], box, TOL)
    if not D: return None, "difference failed"
    D = [x for x in D if x.IsSolid and x.IsValid and G.VolumeMassProperties.Compute(x) is not None]
    if not D: return None, "no valid solid"
    D = max(D, key=lambda x: G.VolumeMassProperties.Compute(x).Volume)
    D.MergeCoplanarFaces(TOL)
    return D, "ok (section %d mm in)" % round(ins * 1000)


def scan(doc, roof, limit=0.005):
    li = doc.Layers.FindByFullPath(BANDS % roof, -1)
    objs = list(doc.Objects.FindByLayer(doc.Layers[li]))
    cx, cy = CEN[roof]; courses = {}
    for o in objs:
        bb = o.Geometry.GetBoundingBox(True); c = bb.Center
        courses.setdefault(round(bb.Min.Z, 1), []).append((math.atan2(c.Y - cy, c.X - cx), o))
    bad = []
    for z in sorted(courses):
        L = sorted(courses[z], key=lambda t: t[0])
        for j in range(len(L)):
            o1 = L[j][1]; o2 = L[(j + 1) % len(L)][1]
            if o1.Id == o2.Id: continue
            g = corner_gaps(o1.Geometry, o2.Geometry) + corner_gaps(o2.Geometry, o1.Geometry)
            if max(g) > limit * 1000: bad.append((z, o1, o2, max(g)))
    return bad


def outward_normal(b, J):
    es = end_faces(b, J); big = max(es, key=lambda e: e[0])
    n = G.Vector3d(big[1].Normal); n.Unitize()
    if (big[2] - b.GetBoundingBox(True).Center) * n < 0: n = -n          # out of the band, towards the joint
    return n, big


def ok_after(T, other):
    g = corner_gaps(T, other)
    return T.IsSolid and T.IsValid and max(g) <= 2.6 and min(g) >= 1.4, g


def fix_all(doc, roof, apply=True):
    """slanted end (one band has an end face at another angle): rebuild that band square to its neighbour's end face,
    2.0 mm off it. V-joint (both ends square but at different angles, the joint opens towards the outer face): mitre
    both band ends on the bisector plane through the inner contact point, 1.0 mm each side (2.0 mm joint).
    A rebuilt band replaces the old one only if it is a valid closed solid and its end corners sit 1.4-2.6 mm from
    the neighbour; otherwise the joint is left as it was and reported."""
    report = []
    for z, o1, o2, gmax in scan(doc, roof):
        b1, b2 = o1.Geometry, o2.Geometry
        J = joint_point(b1, b2)
        e1, e2 = end_faces(b1, J), end_faces(b2, J)
        s1, s2 = spread(e1), spread(e2)
        rec = {"roof": roof, "z": z, "joint_xyz": [round(J.X, 3), round(J.Y, 3), round(J.Z, 3)], "bands": [str(o1.Id), str(o2.Id)], "before_max_mm": gmax}
        jobs = []
        if max(s1, s2) > 0.01:
            good, bad = (o1, o2) if s1 < s2 else (o2, o1)
            ng, big = outward_normal(good.Geometry, J)               # out of the good band = into the bad one
            jobs.append((bad, good, ng, big[2] + ng * 0.002)); rec["kind"] = "slanted end"
        else:
            n1, _ = outward_normal(b1, J); n2, _ = outward_normal(b2, J)
            m = n1 - n2; m.Unitize()                                  # bisector normal, from band 1 to band 2
            jobs.append((o1, o2, -m, J - m * 0.001)); jobs.append((o2, o1, m, J + m * 0.001)); rec["kind"] = "V joint, mitred"
        done = []
        for tgt, other, n, P0 in jobs:
            T, msg = rebuild(tgt.Geometry, n, P0)
            if T is None: done.append((str(tgt.Id), msg)); continue
            good_after, g = ok_after(T, other.Geometry)
            if good_after and apply: doc.Objects.Replace(tgt.Id, T)
            done.append((str(tgt.Id), "replaced" if (good_after and apply) else "rejected", g))
        rec["result"] = done
        report.append(rec)
    return report
