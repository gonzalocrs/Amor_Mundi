"""Fill the hollow around the rib tube inside a joined piece (Gonzalo 2026-11-21: "fill solid around the tube").

web  = vertical prism over the plan footprint of the rib tube inside the piece  INTERSECT  piece envelope
       (envelope = loft of the piece's outer section loops: walls + hollow, no room-side bulge),
       MINUS the cast cores (the channel stays open)
new  = joined piece UNION web
So the hollow becomes solid only in a narrow pier around the tube, from the bed to the lid: no internal
overhang is left whichever way the piece is printed. Ribs, cores and outer/room faces do not change."""
import math
import Rhino.Geometry as G

TOL = 0.0005

def envelope(piece, n=5, shrink=0.015, lift=0.001, top_clear=0.002):
    """top_clear: keep the top section below the lid groove (0.08) when the envelope is used as a check volume"""
    bb = piece.GetBoundingBox(True)
    z0, z1 = bb.Min.Z, bb.Max.Z
    secs = []
    for i in range(n):
        z = z0 + 0.002 + (z1 - z0 - 0.002 - top_clear) * i / (n - 1.0)
        ok, crvs, _ = G.Intersect.Intersection.BrepPlane(piece, G.Plane(G.Point3d(0, 0, z), G.Vector3d.ZAxis), TOL)
        if not crvs:
            return None
        loops = [c for c in G.Curve.JoinCurves(crvs, 0.001) if c.IsClosed]
        if not loops:
            return None
        outer = max(loops, key=lambda c: abs(G.AreaMassProperties.Compute(c).Area))
        if shrink:
            # pull the envelope inside the walls so the web never touches an outer face (no coincident faces)
            cen = G.AreaMassProperties.Compute(outer).Centroid
            best = None
            for d in (shrink, -shrink):
                off = outer.Offset(G.Plane(G.Point3d(0, 0, z), G.Vector3d.ZAxis), d, 0.0005, G.CurveOffsetCornerStyle.Sharp)
                if off and len(off) == 1 and off[0].IsClosed:
                    a = abs(G.AreaMassProperties.Compute(off[0]).Area)
                    if best is None or a < best[0]:
                        best = (a, off[0])
            if best is None:
                return None
            outer = best[1]
        secs.append(outer)
    # extend to the exact bed planes by moving the end sections
    s0 = secs[0].DuplicateCurve(); s0.Translate(G.Vector3d(0, 0, (z0 + lift) - (z0 + 0.002)))
    s1 = secs[-1].DuplicateCurve(); s1.Translate(G.Vector3d(0, 0, (z1 - shrink) - (z1 - top_clear)))
    secs = [s0] + secs + [s1]
    lo = G.Brep.CreateFromLoft(secs, G.Point3d.Unset, G.Point3d.Unset, G.LoftType.Straight, False)
    if not lo:
        return None
    b = lo[0].CapPlanarHoles(0.001)
    if b is None:
        return None
    if b.SolidOrientation == G.BrepSolidOrientation.Inward:
        b.Flip()
    return b

def footprint_prism(parts, z0, z1, grow=0.005):
    prisms = []
    for p in parts:
        m = G.Mesh()
        for mm in G.Mesh.CreateFromBrep(p, G.MeshingParameters.FastRenderMesh):
            m.Append(mm)
        outs = m.GetOutlines(G.Plane(G.Point3d(0, 0, z0 - 0.01), G.Vector3d.ZAxis))
        for pl in outs or []:
            if pl.Count < 4:
                continue
            c = G.PolylineCurve(pl)
            c = c.Simplify(G.CurveSimplifyOptions.All, 0.001, 0.01) or c
            if grow:
                # 5 mm wider than the tube: prism sides are not tangent to the tube (tangency breaks booleans)
                pl0 = G.Plane(G.Point3d(0, 0, z0 - 0.01), G.Vector3d.ZAxis)
                best = None
                for d in (grow, -grow):
                    off = c.Offset(pl0, d, 0.0005, G.CurveOffsetCornerStyle.Round)
                    if off and len(off) == 1 and off[0].IsClosed:
                        a = abs(G.AreaMassProperties.Compute(off[0]).Area)
                        if best is None or a > best[0]:
                            best = (a, off[0])
                if best is not None:
                    c = best[1]
            ex = G.Extrusion.Create(c, (z1 - z0) + 0.02, True)
            if ex is None:
                continue
            b = ex.ToBrep()
            if b.GetBoundingBox(True).Max.Z < z1:
                ex = G.Extrusion.Create(c, -((z1 - z0) + 0.02), True); b = ex.ToBrep()
            if b.SolidOrientation == G.BrepSolidOrientation.Inward:
                b.Flip()
            prisms.append(b)
    return prisms


def fill_piece(joined, src, c, ribs, cores, J):
    """returns (brep, status, added_volume). Retries 3 shrink/grow/tolerance combos; never changes ribs/cores/faces."""
    bb = src.GetBoundingBox(True)
    cl, _ = J.cell(src, c, inset=0.001)
    if cl is None:
        return joined, "fill-fail-cell", 0.0
    parts = [x for r in J._near(cl.GetBoundingBox(True), ribs) for x in (G.Brep.CreateBooleanIntersection(r, cl, 0.0005) or []) if x.IsSolid]
    if not parts:
        return joined, "no-rib", 0.0
    v0 = abs(G.VolumeMassProperties.Compute(joined).Volume)
    last = "fill-fail"
    for shrink, grow, tol in ((0.015, 0.005, 0.0005), (0.012, 0.008, 0.001), (0.018, 0.004, 0.002)):
        env = envelope(src, shrink=shrink)
        if env is None:
            last = "fill-fail-envelope"; continue
        web = [w for p in footprint_prism(parts, bb.Min.Z, bb.Max.Z, grow=grow) for w in (G.Brep.CreateBooleanIntersection(p, env, tol) or []) if w.IsValid and w.IsSolid]
        if not web:
            return joined, "no-web", 0.0
        u = J._union(joined, web, tol)
        if u is None:
            last = "fill-fail-union"; continue
        cs = J._near(u.GetBoundingBox(True), cores)
        j = J._diff(u, cs, tol) if cs else u
        if j is None:
            j = J._core_via_box(u, cores, tol)
        if j is None or not (j.IsValid and j.IsSolid):
            last = "fill-fail-core"; continue
        v1 = abs(G.VolumeMassProperties.Compute(j).Volume)
        if v1 < v0 * 0.98:
            last = "fill-fail-volume"; continue
        if j.SolidOrientation == G.BrepSolidOrientation.Inward:
            j.Flip()
        return j, "filled", v1 - v0
    return joined, last, 0.0
