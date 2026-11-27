"""Mitre the corner band joints (Gonzalo 2026-11-27: 'hand-mitre the 13 remaining ~10 mm joints').
At the plan corners two growth bands meet with both ends cut square but at slightly different angles, so the joint is
2 mm at the inner face and opens to ~10-13 mm at the outer face. Each such joint is closed on a mitre:
- the bisecting plane of the two end faces, through the inner contact point;
- each band is rebuilt only at that end (fix_band_joints_2026_11_24.rebuild: its own full cross-section extended to
  the plane, everything beyond cut away), 1.0 mm short of the bisecting plane, so the joint is 2.0 mm all the way.
Nothing else is touched. A joint is accepted only if both rebuilt bands are valid closed solids, every end corner sits
1.6-2.2 mm from the neighbour, and the outer face of the rebuilt ends lies on the bands' own untrimmed surfaces
(deviation reported). Otherwise the joint is left as it was."""
import sys, math, System, Rhino
import Rhino.Geometry as G
sys.path.insert(0, r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\polyframe2")
import fix_band_joints_2026_11_24 as F


def pair_gaps(a, b):
    return F.corner_gaps(a, b) + F.corner_gaps(b, a)


def surface_dev(new, old, J, r=0.08):
    """largest distance from the rebuilt band's vertices near the joint to the original band's own (untrimmed)
    surfaces: 0 means the new end lies on the original geometry, extended"""
    srfs = [f.UnderlyingSurface() for f in old.Faces]
    worst = 0.0
    for v in new.Vertices:
        p = v.Location
        if p.DistanceTo(J) > r: continue
        best = 9.0
        for s in srfs:
            ok, u, w = s.ClosestPoint(p)
            if ok: best = min(best, p.DistanceTo(s.PointAt(u, w)))
        worst = max(worst, best)
    return worst


def mitre(doc, o1, o2):
    b1, b2 = o1.Geometry, o2.Geometry
    J = F.joint_point(b1, b2)
    n1, _ = F.outward_normal(b1, J); n2, _ = F.outward_normal(b2, J)
    m = n1 - n2; m.Unitize()                                   # bisecting-plane normal, from band 1 towards band 2
    T1, msg1 = F.rebuild(b1, -m, J - m * 0.001)
    T2, msg2 = F.rebuild(b2, m, J + m * 0.001)
    rec = {"joint_xyz": [round(J.X, 3), round(J.Y, 3), round(J.Z, 3)], "bands": [str(o1.Id), str(o2.Id)],
           "before_mm": pair_gaps(b1, b2), "msgs": [msg1, msg2]}
    if T1 is None or T2 is None:
        rec["result"] = "not rebuilt"; return rec, None
    g = pair_gaps(T1, T2)
    dev = max(surface_dev(T1, b1, J), surface_dev(T2, b2, J))
    ok = T1.IsSolid and T1.IsValid and T2.IsSolid and T2.IsValid and 1.6 <= min(g) and max(g) <= 2.2
    rec.update({"after_mm": g, "outer_face_dev_mm": round(dev * 1000, 3), "result": "accepted" if ok else "rejected"})
    return rec, ((o1.Id, T1), (o2.Id, T2)) if ok else None


def run(doc, apply=True):
    out = []
    for roof in ("15x10", "10x10"):
        for z, o1, o2, gmax in F.scan(doc, roof, limit=0.0026):
            rec, rep = mitre(doc, o1, o2)
            rec.update({"roof": roof, "z": z})
            if rep and apply:
                for gid, T in rep: doc.Objects.Replace(gid, T)
            out.append(rec)
    return out


# ---- what the joints turned out to be (2026-11-27 check) -------------------------------------------------------------
# 12 of the 13 flagged joints (15x10 z4.0 x4, 10x10 z4.5 x4 and z5.9 x4) are NOT open: both end faces are parallel and
# 1.7-2.0 mm apart over their whole area, and the outer faces are flush (0.0-0.6 mm). The ~10 mm the scan reported is a
# step on the INNER face: one band is ~10 mm deeper than its neighbour. corner_gaps measures vertex -> nearest point of
# the neighbour, so the deeper band's two inner corners read ~10 mm. Nothing to mitre there.
# Real defects: 15x10 z8.0 and z10.0 (a triangular sliver left inside the hollow of one band by the 11-24 fix) and
# 15x10 z11.4 (a 4 cm filler block turned 8.5 deg against its neighbour: clashes ~2 mm at the outer face, opens ~12 mm
# at the inner face).

def apply_rebuilt(doc, path=r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\polyframe2\mitre-2026-11-27-rebuilt-bands.3dm"):
    """apply the 3 rebuilt bands (15x10 z8.0, z10.0, z11.4) saved by the 2026-11-27 check: each object in the file is
    named 'replaces <guid>' and replaces that growth band in the open document (same layer, same attributes)"""
    f = Rhino.FileIO.File3dm.Read(path); done = []
    for o in f.Objects:
        gid = System.Guid(o.Attributes.Name.split()[-1])
        done.append((str(gid), doc.Objects.FindId(gid) is not None and doc.Objects.Replace(gid, o.Geometry)))
    return done

def rebuild_end(B, n, P0, insets=(0.06, 0.08, 0.10, 0.12)):
    """replace the band's last few cm by a clean prism of its own complete cross-section: cut the band at a plane
    `ins` inside the end (n points INTO the band, P0 on the end plane), extrude that section square to the end plane,
    union. Removes anything left inside the end region (slivers in the hollow) and keeps the end plane where it is."""
    ref = F.section_loops(B, n, P0, 0.15); L = sum(c.GetLength() for c in ref)
    for ins in insets:
        loops = F.section_loops(B, n, P0, ins)
        if loops and len(loops) == len(ref) and abs(sum(c.GetLength() for c in loops) - L) < 0.02 * L: break
    else:
        return None, "no complete section"
    Q = G.Plane(P0 + n * ins, n)
    box = G.Box(G.Plane(Q.Origin, -n), G.Interval(-0.6, 0.6), G.Interval(-0.6, 0.6), G.Interval(0, 0.5)).ToBrep()
    K = G.Brep.CreateBooleanDifference(B, box, F.TOL)
    K = [x for x in (K or []) if x.IsValid and G.VolumeMassProperties.Compute(x) is not None]
    if not K: return None, "cut failed"
    K = max(K, key=lambda x: G.VolumeMassProperties.Compute(x).Volume)
    faces = G.Brep.CreatePlanarBreps(loops, F.TOL)
    if not faces: return None, "planar section failed"
    prisms = []
    for fb in faces:
        for f in fb.Faces:
            c = G.AreaMassProperties.Compute(f).Centroid
            e = f.CreateExtrusion(G.LineCurve(c, c - n * ins), True)
            if e is None: return None, "extrusion failed"
            if e.SolidOrientation == G.BrepSolidOrientation.Inward: e.Flip()
            prisms.append(e)
    U = G.Brep.CreateBooleanUnion([K] + prisms, F.TOL)
    U = [x for x in (U or []) if x.IsSolid and x.IsValid]
    if not U: return None, "union failed"
    U = max(U, key=lambda x: G.VolumeMassProperties.Compute(x).Volume)
    U.MergeCoplanarFaces(F.TOL)
    return U, "ok (last %d mm rebuilt)" % round(ins * 1000)


def solid_from_surfaces(B, keep_faces, planes, ext=0.06):
    """rebuild a small block from its own side surfaces (extended) closed by the given planes (Rhino CreateSolid)"""
    parts = []
    for i in keep_faces:
        s = B.Faces[i].UnderlyingSurface().Duplicate()
        for side in (G.IsoStatus.West, G.IsoStatus.East, G.IsoStatus.South, G.IsoStatus.North):
            s2 = s.Extend(side, ext, False)
            if s2: s = s2
        parts.append(G.Brep.CreateFromSurface(s))
    for pl in planes:
        parts.append(G.Brep.CreateFromSurface(G.PlaneSurface(pl, G.Interval(-0.5, 0.5), G.Interval(-0.5, 0.5))))
    S = G.Brep.CreateSolid(parts, F.TOL)
    S = [x for x in (S or []) if x.IsSolid and x.IsValid]
    return S
