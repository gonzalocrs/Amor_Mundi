"""Printed piece + rib joined into one printed solid, with the channel for the cast core.

For every printed piece (stepped course pieces and the top-course U formwork):
  cell   = the piece's own slot: between its two end planes (head joints), between its bed planes z0..z1,
           from 0.6 m on the room side out to its outer face (+5 mm). Rib parts beyond the outer face are NOT
           added, so the outer shell does not change.
  joined = piece  UNION  (rib tubes  INTERSECT  cell)  MINUS  cast cores
Ribs, cores and pieces are read from the live layers; nothing is moved or resized.
A piece whose booleans fail is reported and kept as the plain piece (never fudged)."""
import math
import Rhino.Geometry as G

TOL = 0.0005

def _end_faces(b, c):
    """the two outer end faces (head joints) of a piece: planar, vertical, normal along the course tangent"""
    cands = []
    for f in b.Faces:
        if not f.IsPlanar(0.001):
            continue
        ok, pl = f.TryGetPlane(0.001)
        if not ok:
            continue
        n = pl.Normal
        if abs(n.Z) > 0.1:
            continue
        amp = G.AreaMassProperties.Compute(f.DuplicateFace(False))
        if amp is None or amp.Area < 0.02:
            continue
        cp = amp.Centroid
        rad = G.Vector3d(cp.X - c.X, cp.Y - c.Y, 0); rad.Unitize()
        tan = G.Vector3d.CrossProduct(G.Vector3d.ZAxis, rad)
        if abs(n * tan) < 0.7:
            continue
        cands.append((cp, n, amp.Area))
    if len(cands) < 2:
        return None
    # pair: the two faces farthest apart (outer end walls, not the void end faces)
    best = None
    for i in range(len(cands)):
        for j in range(i + 1, len(cands)):
            d = cands[i][0].DistanceTo(cands[j][0])
            if best is None or d > best[0]:
                best = (d, cands[i], cands[j])
    return best[1], best[2]

def _outer_hit(b, p, d, z):
    """farthest intersection of a horizontal ray from p along d (unit, outward) with brep b at height z"""
    a = G.Point3d(p.X, p.Y, z)
    ln = G.LineCurve(a - d * 0.05, a + d * 1.5)
    ok, crvs, pts = G.Intersect.Intersection.CurveBrep(ln, b, 0.0005)
    if not ok or pts is None or len(pts) == 0:
        return None
    return max(pts, key=lambda q: (q - a) * d)

def cell(piece, c, inward=0.6, out_pad=0.005, inset=0.001):
    bb = piece.GetBoundingBox(True)
    z0, z1 = bb.Min.Z, bb.Max.Z
    ef = _end_faces(piece, c)
    if ef is None:
        return None, "no end faces"
    (ca, na, _), (cb, nb, _) = ef
    zm = 0.5 * (z0 + z1)
    pts_out = []
    rad_of = lambda p: (lambda v: (v.Unitize(), v)[1])(G.Vector3d(p.X - c.X, p.Y - c.Y, 0))
    ends = []
    for cp, n in ((ca, na), (cb, nb)):
        # direction in the end plane, horizontal, pointing away from the centre
        d = G.Vector3d.CrossProduct(G.Vector3d.ZAxis, n); d.Unitize()
        if d * rad_of(cp) < 0:
            d.Reverse()
        # ray just inside the piece (1 cm off the end face, into the piece)
        into = -n if (G.Point3d(bb.Center.X, bb.Center.Y, 0) - G.Point3d(cp.X, cp.Y, 0)) * n < 0 else n
        q = _outer_hit(piece, cp + into * 0.01, d, zm)
        if q is None:
            return None, "no outer hit"
        q = q - into * 0.01 + d * out_pad          # back on the end plane, padded
        ends.append((cp, d, q))
    # mid point of the outer face
    m = G.Point3d(0.5 * (ca.X + cb.X), 0.5 * (ca.Y + cb.Y), zm)
    dm = rad_of(m)
    qm = _outer_hit(piece, m, dm, zm)
    if qm is None:
        return None, "no mid hit"
    qm = qm + dm * out_pad
    (pa, da, qa), (pb, db, qb) = ends
    ia = qa - da * (qa - G.Point3d(pa.X, pa.Y, zm)).Length - da * inward
    ib = qb - db * (qb - G.Point3d(pb.X, pb.Y, zm)).Length - db * inward
    # pull the head-joint faces in by `inset` so no rib face is coplanar with the piece's end walls
    ua = qb - qa; ua.Unitize()
    qa2, ia2 = qa + ua * inset, ia + ua * inset
    qb2, ib2 = qb - ua * inset, ib - ua * inset
    z0 += inset; z1 -= inset
    poly = [G.Point3d(p.X, p.Y, z0) for p in (qa2, qm, qb2, ib2, ia2)]
    poly.append(poly[0])
    crv = G.PolylineCurve(poly)
    ex = G.Extrusion.Create(crv, -(z1 - z0), True)
    if ex is None:
        ex = G.Extrusion.Create(crv, (z1 - z0), True)
    cb_ = ex.ToBrep()
    cbb = cb_.GetBoundingBox(True)
    if cbb.Max.Z < z1:  # extruded the wrong way
        ex = G.Extrusion.Create(crv, (z1 - z0), True); cb_ = ex.ToBrep()
    if cb_.SolidOrientation == G.BrepSolidOrientation.Inward:
        cb_.Flip()
    return cb_, None

def _near(bb, items, pad=0.05):
    bx = G.BoundingBox(bb.Min - G.Vector3d(pad, pad, pad), bb.Max + G.Vector3d(pad, pad, pad))
    out = []
    for g, gb in items:
        if gb.Min.X > bx.Max.X or gb.Max.X < bx.Min.X or gb.Min.Y > bx.Max.Y or gb.Max.Y < bx.Min.Y or gb.Min.Z > bx.Max.Z or gb.Max.Z < bx.Min.Z:
            continue
        out.append(g)
    return out

def _union(piece, parts, tol):
    u = G.Brep.CreateBooleanUnion([piece] + parts, tol)
    if u and len(u) == 1 and u[0].IsValid:
        return u[0]
    cur = piece                      # sequential, part by part
    for p in parts:
        u = G.Brep.CreateBooleanUnion([cur, p], tol)
        if not u or len(u) != 1 or not u[0].IsValid:
            return None
        cur = u[0]
    return cur

def _diff(b, cutters, tol):
    d = G.Brep.CreateBooleanDifference([b], cutters, tol)
    if d and len(d) == 1 and d[0].IsValid and d[0].IsSolid:
        return d[0]
    cur = b
    for c in cutters:                # one core at a time
        d = G.Brep.CreateBooleanDifference([cur], [c], tol)
        if d is None:
            return None
        if len(d) == 0:
            ok, cv, pt = G.Intersect.Intersection.BrepBrep(cur, c, tol)
            if ok and cv is not None and len(cv) > 0:
                return None          # they do intersect: the boolean failed
            continue                 # core does not reach this solid
        if len(d) != 1 or not d[0].IsValid:
            return None
        cur = d[0]
    return cur if cur.IsSolid else None

def _core_via_box(u, cores, tol):
    """method D: intersect the joined solid with (box around it MINUS the cores) instead of subtracting the cores from it"""
    bb = u.GetBoundingBox(True); bb.Inflate(0.05)
    K = G.Box(bb).ToBrep()
    cs = _near(bb, cores)
    if not cs:
        return u
    Kc = _diff(K, cs, tol)
    if Kc is None:
        return None
    r = G.Brep.CreateBooleanIntersection(u, Kc, tol)
    if r and len(r) == 1 and r[0].IsValid and r[0].IsSolid:
        return r[0]
    return None

def join_piece(piece, c, ribs, cores):
    """ribs / cores: lists of (brep, bbox). Returns (brep, status, info).
    Strategies per (joint inset, tolerance): A = union then subtract cores; D = union then intersect with (box - cores).
    Never changes the inputs; a piece that fails every strategy is returned plain and flagged."""
    last = "?"
    for inset, tol in ((0.001, 0.0005), (0.0025, 0.001), (0.004, 0.002)):
        cl, err = cell(piece, c, inset=inset)
        if cl is None:
            return piece, "fail-cell", err
        cbb = cl.GetBoundingBox(True)
        parts, bad = [], 0
        for r in _near(cbb, ribs):
            res = G.Brep.CreateBooleanIntersection(r, cl, tol)
            for x in (res or []):
                vm = G.VolumeMassProperties.Compute(x) if x.IsSolid else None
                if x.IsValid and vm is not None and abs(vm.Volume) > 1e-7:
                    parts.append(x)
                elif x.GetBoundingBox(True).Diagonal.Length > 0.01:
                    bad += 1
        if bad:
            last = "fail-intersect"; continue
        if parts:
            u = _union(piece, parts, tol)
            if u is None:
                last = "fail-union"; continue
            status = "joined"
        else:
            u, status = piece.DuplicateBrep(), "no-rib"
        cs = _near(u.GetBoundingBox(True), cores)
        j = _diff(u, cs, tol) if cs else u
        how = "A"
        if j is None:
            j = _core_via_box(u, cores, tol); how = "D"
        if j is None or not (j.IsValid and j.IsSolid):
            last = "fail-core"; continue
        vj = G.VolumeMassProperties.Compute(j); vp = G.VolumeMassProperties.Compute(piece)
        if vj is None or abs(vj.Volume) < 0.8 * abs(vp.Volume):
            last = "fail-volume"; continue          # a boolean returned the wrong body
        if j.SolidOrientation == G.BrepSolidOrientation.Inward:
            j.Flip()
        return j, status, "%d rib parts, %d cores, inset %g tol %g, %s" % (len(parts), len(cs), inset, tol, how)
    return piece, last, "all strategies failed"