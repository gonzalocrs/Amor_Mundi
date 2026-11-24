"""Curved corners (Gonzalo / reviewer, 2026-11-23): the corner pieces and growth bands of the stepped roofs were built as
flat strips (a profile swept along a polyline, ~22 cm facets), so drawings print every strip seam.
This rebuilds one faceted solid as the SAME profile swept along a smooth curve through the SAME polyline vertices
(rail = outer bottom edge), road-like (profile stays vertical), then cut back to the SAME two end planes and capped.
Footprint, heights, groove, void, end joints unchanged; only the facets become one curved surface.
Run inside Rhino 8 (Python 3); __rhino_doc__ is the document."""
import math
import Rhino
import Rhino.Geometry as G

TOL = 0.0005
CENTRES = {"15x10": G.Point3d(85, 0, 0), "10x10": G.Point3d(85, -20, 0)}


def outer_chain(br, centre):
    """bottom horizontal section just above the base; outer loop split at its two end segments; the chain farther
    from the module centre is the outer-face bottom edge (the sweep rail polyline)."""
    bb = br.GetBoundingBox(True)
    z = bb.Min.Z + 0.01
    ok, crv, pts = Rhino.Geometry.Intersect.Intersection.BrepPlane(br, G.Plane(G.Point3d(0, 0, z), G.Vector3d.ZAxis), TOL)
    if not ok or not crv:
        return None
    loops = [c for c in G.Curve.JoinCurves(crv, 0.001) if c.IsClosed]
    loops = [max(loops, key=lambda c: c.GetLength())] if loops else []      # outer loop (the inner one is the void)
    best = None
    for c in loops:
        okp, poly = c.TryGetPolyline()
        if not okp:
            continue
        poly = list(poly)[:-1]
        n = len(poly)
        if n < 6:
            continue
        def radial(i):
            p, q = poly[i], poly[(i + 1) % n]
            v = G.Vector3d(q - p); v.Z = 0; v.Unitize()
            r = G.Vector3d((p.X + q.X) / 2 - centre.X, (p.Y + q.Y) / 2 - centre.Y, 0); r.Unitize()
            return abs(v * r)
        segs = sorted(range(n), key=radial, reverse=True)
        a, b = sorted(segs[:2])                                   # the two end segments (most radial: the joints)
        ch1 = [poly[(i) % n] for i in range(b + 1, a + n + 1)]     # from end of seg b round to start of seg a
        ch2 = [poly[i] for i in range(a + 1, b + 1)]
        for ch in (ch1, ch2):
            if len(ch) < 2:
                continue
            r = sum(math.hypot(p.X - centre.X, p.Y - centre.Y) for p in ch) / len(ch)
            if best is None or r > best[0]:
                best = (r, ch, (poly[a], poly[(a + 1) % n]), (poly[b], poly[(b + 1) % n]))
    return best


def horiz_normal(t, p, centre):
    n = G.Vector3d.CrossProduct(t, G.Vector3d.ZAxis); n.Unitize()
    if n * G.Vector3d(p.X - centre.X, p.Y - centre.Y, 0) < 0:
        n.Reverse()
    return n


def end_plane(seg, mid_of_piece):
    p0, p1 = seg
    v = G.Vector3d(p1 - p0); v.Z = 0; v.Unitize()
    n = G.Vector3d.CrossProduct(v, G.Vector3d.ZAxis); n.Unitize()
    o = G.Point3d((p0.X + p1.X) / 2, (p0.Y + p1.Y) / 2, (p0.Z + p1.Z) / 2)
    if n * G.Vector3d(o - mid_of_piece) < 0:
        n.Reverse()                                              # normal points away from the piece -> Trim keeps the piece side
    return G.Plane(o, n)


def rebuild(br, centre):
    oc = outer_chain(br, centre)
    if oc is None:
        return None, "no outer chain"
    r, ch, segA, segB = oc
    bb = br.GetBoundingBox(True)
    z0 = bb.Min.Z
    pts = [G.Point3d(p.X, p.Y, z0) for p in ch]
    if len(pts) < 3:
        return None, "straight (no facets)"
    rail = G.Curve.CreateInterpolatedCurve(pts, 3)
    rail = rail.Extend(G.CurveEnd.Both, 0.15, G.CurveExtensionStyle.Smooth)
    # profile: section square to the first facet, at its midpoint
    a, b = pts[0], pts[1]
    t = G.Vector3d(b - a); t.Unitize()
    m = G.Point3d((a.X + b.X) / 2, (a.Y + b.Y) / 2, z0)
    nrm = horiz_normal(t, m, centre)
    ps = G.Plane(m, nrm, G.Vector3d.ZAxis)                       # x = outward, y = up, normal = along the facet
    ok, crv, ip = Rhino.Geometry.Intersect.Intersection.BrepPlane(br, G.Plane(m, t), TOL)
    if not ok or not crv:
        return None, "no profile"
    loops = [c for c in G.Curve.JoinCurves(crv, 0.001) if c.IsClosed]
    if not loops:
        return None, "profile not closed"
    prof = min(loops, key=lambda c: c.GetBoundingBox(True).Center.DistanceTo(G.Point3d(m.X, m.Y, bb.Center.Z)))
    s0 = rail.PointAtStart
    t0 = rail.TangentAtStart
    pt = G.Plane(s0, horiz_normal(t0, s0, centre), G.Vector3d.ZAxis)
    prof = prof.DuplicateCurve()
    prof.Transform(G.Transform.PlaneToPlane(ps, pt))
    sw = G.SweepOneRail(); sw.SetToRoadlikeTop(); sw.SweepTolerance = TOL; sw.AngleToleranceRadians = math.radians(0.5)
    res = sw.PerformSweep(rail, prof)
    if not res:
        return None, "sweep failed"
    s = res[0].CapPlanarHoles(TOL) or res[0]
    mid = bb.Center
    for seg in (segA, segB):
        pl = end_plane(seg, mid)
        cut = s.Trim(pl, TOL)
        if not cut:
            return None, "trim failed"
        s = max(cut, key=lambda x: x.GetBoundingBox(True).Diagonal.Length)
        s = s.CapPlanarHoles(TOL) or s
    if not s.IsSolid:
        return None, "not closed"
    if s.SolidOrientation == G.BrepSolidOrientation.Inward:
        s.Flip()
    return s, "ok"


# ---- v2: loft through the piece's own joint sections (exact at every facet joint, smooth in between) ----

def section_poly(br, plane, near, xaxis):
    """closed section of br in plane, as a simplified polyline starting at the vertex nearest `near`,
    oriented counter-clockwise in the local frame (x = xaxis, y = up)."""
    ok, crv, ip = Rhino.Geometry.Intersect.Intersection.BrepPlane(br, plane, TOL)
    if not ok or not crv:
        return None
    loops = [c for c in G.Curve.JoinCurves(crv, 0.001) if c.IsClosed]
    if not loops:
        return None
    c = max(loops, key=lambda c: c.GetLength())
    pl = c.ToPolyline(0.0002, 0.0, 0.0, 0).ToPolyline()
    pts = list(pl)[:-1]
    # drop collinear / duplicate points
    out = []
    n = len(pts)
    for i in range(n):
        p0, p1, p2 = pts[i - 1], pts[i], pts[(i + 1) % n]
        if p1.DistanceTo(p0) < 1e-5:
            continue
        v1 = G.Vector3d(p1 - p0); v2 = G.Vector3d(p2 - p1)
        if v1.Length < 1e-9 or v2.Length < 1e-9:
            continue
        if G.Vector3d.CrossProduct(v1, v2).Length / (v1.Length * v2.Length) < 1e-4 and v1 * v2 > 0:
            continue
        out.append(p1)
    if len(out) < 3:
        return None
    k = min(range(len(out)), key=lambda i: out[i].DistanceTo(near))
    out = out[k:] + out[:k]
    lp = G.Plane(out[0], xaxis, G.Vector3d.ZAxis)
    area = 0.0
    uv = [lp.ClosestParameter(p)[1:] for p in out]
    for i in range(len(uv)):
        (x1, y1), (x2, y2) = uv[i], uv[(i + 1) % len(uv)]
        area += x1 * y2 - x2 * y1
    if area < 0:
        out = [out[0]] + out[1:][::-1]
    return out


def rebuild2(br, centre):
    oc = outer_chain(br, centre)
    if oc is None:
        return None, "no outer chain"
    r, ch, segA, segB = oc
    if len(ch) < 3:
        return None, "straight"
    bb = br.GetBoundingBox(True)
    z0 = bb.Min.Z
    ch = [G.Point3d(p.X, p.Y, z0) for p in ch]
    mid = bb.Center
    # order the chain from the end next to segA to the end next to segB
    secs = []
    n = len(ch)
    for i, p in enumerate(ch):
        if i == 0 or i == n - 1:
            seg = segA if min(p.DistanceTo(segA[0]), p.DistanceTo(segA[1])) < min(p.DistanceTo(segB[0]), p.DistanceTo(segB[1])) else segB
            pl = end_plane(seg, mid)
            pl = G.Plane(pl.Origin - pl.Normal * 0.0002, pl.Normal)          # a hair inside the end face
            t = G.Vector3d(ch[1] - ch[0]) if i == 0 else G.Vector3d(ch[-1] - ch[-2])
        else:
            t1 = G.Vector3d(ch[i] - ch[i - 1]); t1.Unitize()
            t2 = G.Vector3d(ch[i + 1] - ch[i]); t2.Unitize()
            t = t1 + t2; t.Unitize()
            pl = G.Plane(p, t)
        x = horiz_normal(t, p, centre)
        s = section_poly(br, pl, p, x)
        if s is None:
            return None, "section %d failed" % i
        secs.append(s)
    counts = set(len(s) for s in secs)
    if len(counts) != 1:
        return None, "section vertex counts differ %s" % sorted(counts)
    # end sections exactly on the end faces: push the hair back out
    for i in (0, n - 1):
        p = ch[i]
        seg = segA if min(p.DistanceTo(segA[0]), p.DistanceTo(segA[1])) < min(p.DistanceTo(segB[0]), p.DistanceTo(segB[1])) else segB
        pl = end_plane(seg, mid)
        secs[i] = [pl.ClosestPoint(q) for q in secs[i]]
    curves = [G.PolylineCurve(s + [s[0]]) for s in secs]
    lofts = G.Brep.CreateFromLoft(curves, G.Point3d.Unset, G.Point3d.Unset, G.LoftType.Normal, False)
    if not lofts:
        return None, "loft failed"
    b = lofts[0].CapPlanarHoles(TOL)
    if b is None or not b.IsSolid:
        return None, "not closed"
    if b.SolidOrientation == G.BrepSolidOrientation.Inward:
        b.Flip()
    return b, "ok"
