"""Curved corners v3 (2026-11-23): keep each piece's own topology and replace every run of flat facets by ONE smooth face.

Longitudinal feature lines (polylines of edges running along the course) become interpolated curves through the SAME
vertices. Faces that continue each other across a facet joint (normals within KINK) are merged into one face:
  - planar runs (lid, groove floor, feet, void ceiling) -> one planar face bounded by the smooth curves;
  - sloped / vertical runs (outer face, room face, wall faces) -> one ruled surface between their two smooth long sides.
End faces, end walls and all other faces stay exactly as they are. Footprint, heights, groove, void and joints unchanged.
Run inside Rhino 8 (Python 3). Uses outer_chain() from curved_corners.py for the course direction.
"""
import math
import Rhino
import Rhino.Geometry as G

TOL = 0.0005
KINK = math.radians(20.0)


def hermite_spans(r):
    """smooth G1 curve through the polyline vertices r, one cubic Bezier span per original segment (span i runs from
    r[i] to r[i+1] exactly), tangents from the neighbouring vertices (Catmull-Rom directions)."""
    n = len(r)
    if n == 2:
        return [G.LineCurve(r[0], r[1]).ToNurbsCurve()]
    tans = [None] * n
    for i in range(1, n - 1):
        a = G.Vector3d(r[i] - r[i - 1]); a.Unitize()
        b = G.Vector3d(r[i + 1] - r[i]); b.Unitize()
        t = a + b; t.Unitize()
        tans[i] = t
    # end tangents: continue the curvature of the first / last span (constant-curvature guess), so that the
    # neighbouring piece, which makes the same guess from its side, meets it almost tangent at the head joint
    c0 = G.Vector3d(r[1] - r[0]); c0.Unitize()
    c1 = G.Vector3d(r[-1] - r[-2]); c1.Unitize()
    t0 = c0 * 2.0 - tans[1]; t0.Unitize()
    t1 = c1 * 2.0 - tans[-2]; t1.Unitize()
    tans[0], tans[-1] = t0, t1
    spans = []
    for i in range(n - 1):
        p0, p3 = r[i], r[i + 1]
        L = p0.DistanceTo(p3)
        p1 = p0 + tans[i] * (L / 3.0)
        p2 = p3 - tans[i + 1] * (L / 3.0)
        spans.append(G.NurbsCurve.Create(False, 3, [p0, p1, p2, p3]))
    return spans


class Rebuilder:
    def __init__(self, br, centre, outer_chain, ring=False):
        self.br = br
        self.c = centre
        oc = outer_chain(br, centre)
        self.chain = [G.Point3d(p.X, p.Y, 0) for p in oc[1]] if oc else None
        if ring or self.chain is None or len(self.chain) < 3:   # closed ring, or ends not found: course from the whole outer loop
            bb = br.GetBoundingBox(True)
            ok, crv, ip = Rhino.Geometry.Intersect.Intersection.BrepPlane(br, G.Plane(G.Point3d(0, 0, (bb.Min.Z + bb.Max.Z) / 2), G.Vector3d.ZAxis), TOL)
            lp = max(G.Curve.JoinCurves(crv, 0.001), key=lambda c: c.GetLength())
            okp, pl = lp.TryGetPolyline()
            self.chain = [G.Point3d(p.X, p.Y, 0) for p in pl] if okp else [G.Point3d(p.X, p.Y, 0) for p in lp.ToPolyline(0.001, 0, 0, 0).ToPolyline()]

    def tangent_at(self, p):
        best = None
        q0 = G.Point3d(p.X, p.Y, 0)
        for i in range(len(self.chain) - 1):
            a, b = self.chain[i], self.chain[i + 1]
            q = G.Line(a, b).ClosestPoint(q0, True)
            dd = q.DistanceTo(q0)
            if best is None or dd < best[0]:
                v = G.Vector3d(b - a); v.Unitize(); best = (dd, v)
        return best[1]

    def is_long_curve(self, c):
        cb = c.GetBoundingBox(True)
        return cb.Max.Z - cb.Min.Z < 1e-4 and self.is_long_pts(c.PointAtStart, c.PointAtEnd)

    def is_long_pts(self, a, b):
        v = G.Vector3d(b - a)
        if v.Length < 1e-6:
            return False
        vh = G.Vector3d(v.X, v.Y, 0)
        if vh.Length < 0.3 * v.Length:
            return False
        vh.Unitize()
        return abs(vh * self.tangent_at(G.Point3d((a.X + b.X) / 2, (a.Y + b.Y) / 2, 0))) > 0.8

    def keep(self, out, fl):
        for i in fl:
            out.append(self.br.Faces[i].DuplicateFace(False))

    def run(self):
        """try with every feature line smooth; where a run cannot be rebuilt (stepped/notched faces, bed faces whose
        smoothed loops would cross), freeze the feature lines on its boundary (they keep their original straight
        segments, so the neighbouring faces still meet them exactly) and try again."""
        self.frozen = set()
        for attempt in range(12):
            self.fail_runs = None
            res = self._run()
            if res[0] is not None or not self.fail_runs:
                return res
            new = set(self.fail_runs) - self.frozen
            if not new:
                break
            self.frozen |= new
        # last resort: keep every feature line as it was (faces still merged where possible)
        self.frozen = set(range(1000))
        self.fail_runs = None
        res2 = self._run()
        return res2 if res2[0] is not None else res

    def _run(self):
        br = self.br
        if self.chain is None or len(self.chain) < 3:
            return None, "straight"
        nF = br.Faces.Count
        normals = []
        for f in br.Faces:
            n = f.NormalAt(f.Domain(0).Mid, f.Domain(1).Mid)      # BrepFace.NormalAt already follows the face orientation
            normals.append(n)
        longE = []
        eseg = []                                  # each edge as straight segments (edges may be polylines)
        for e in br.Edges:
            pts = None
            if e.IsLinear(1e-5):
                pts = [e.PointAtStart, e.PointAtEnd]
            else:
                okp, pl = e.DuplicateCurve().TryGetPolyline()
                if okp:
                    pts = list(pl)
                    if pts[0].DistanceTo(e.PointAtStart) > 1e-5:
                        pts.reverse()
            ok = pts is not None and all(self.is_long_pts(pts[k], pts[k + 1]) for k in range(len(pts) - 1))
            if pts is None and self.is_long_curve(e.DuplicateCurve()):
                ok = True                          # an already curved horizontal edge along the course: kept as it is
            longE.append(ok)
            eseg.append(pts)
        par = list(range(nF))

        def find(i):
            while par[i] != i:
                par[i] = par[par[i]]
                i = par[i]
            return i

        def has_long(fi):
            return any(longE[k] for k in br.Faces[fi].AdjacentEdges())
        for e in br.Edges:
            if longE[e.EdgeIndex]:
                continue
            fs = list(e.AdjacentFaces())
            if len(fs) != 2:
                continue
            a, b = fs
            if G.Vector3d.VectorAngle(normals[a], normals[b]) < KINK and has_long(a) and has_long(b):
                par[find(a)] = find(b)
        groups = {}
        for i in range(nF):
            groups.setdefault(find(i), []).append(i)
        # smooth curves for longitudinal polylines (split at real corners)
        lcurves = [G.LineCurve(eseg[i][k], eseg[i][k + 1]) for i in range(br.Edges.Count) if longE[i] and eseg[i] for k in range(len(eseg[i]) - 1)]
        smooth = []
        for jc in G.Curve.JoinCurves(lcurves, 1e-5, True):
            ok, pl = jc.TryGetPolyline()
            if not ok:
                continue
            pts = list(pl)
            runs, cur = [], [pts[0]]
            for k in range(1, len(pts)):
                cur.append(pts[k])
                if k < len(pts) - 1:
                    v1 = G.Vector3d(pts[k] - pts[k - 1]); v2 = G.Vector3d(pts[k + 1] - pts[k])
                    if G.Vector3d.VectorAngle(v1, v2) > KINK:
                        runs.append(cur); cur = [pts[k]]
            runs.append(cur)
            for r in runs:
                if len(r) >= 2:
                    # add any vertex of the solid that lies on a segment (T-junctions), so that every face that
                    # touches this line uses the same vertex set
                    rr = [r[0]]
                    for k in range(len(r) - 1):
                        a, b = r[k], r[k + 1]
                        ln = G.Line(a, b)
                        ins = [v.Location for v in br.Vertices
                               if 1e-5 < a.DistanceTo(v.Location) and 1e-5 < b.DistanceTo(v.Location)
                               and ln.DistanceTo(v.Location, True) < 1e-5]
                        ins.sort(key=lambda q: a.DistanceTo(q))
                        rr.extend(ins)
                        rr.append(b)
                    smooth.append((rr, hermite_spans(rr)))

        def idx(pts, p):
            for i, x in enumerate(pts):
                if x.DistanceTo(p) < 1e-5:
                    return i
            return -1

        def run_of(a, b):
            """index of the smooth feature line on which a and b are consecutive vertices"""
            for k, (pts, crv) in enumerate(smooth):
                i, j = idx(pts, a), idx(pts, b)
                if i >= 0 and j >= 0 and i != j:
                    return k
            return -1                        # long edge not on any feature line (should not happen)

        def smooth_sub(k, p, q):
            if k < 0:
                return G.LineCurve(p, q)
            pts, spans = smooth[k]
            i, j = idx(pts, p), idx(pts, q)
            if i < 0 or j < 0:
                return None
            if i == j:
                if pts[0].DistanceTo(pts[-1]) > 1e-5:
                    return None
                whole = G.Curve.JoinCurves([s.DuplicateCurve() for s in spans] if k not in self.frozen else [G.PolylineCurve(pts)], 1e-6)
                if len(whole) != 1:
                    return None
                w = whole[0]
                ok, t = w.ClosestPoint(p)
                w.ChangeClosedCurveSeam(t)
                return w
            lo, hi = min(i, j), max(i, j)
            if k in self.frozen:                      # this feature line keeps its original straight segments
                sub = G.PolylineCurve(pts[lo:hi + 1])
                if i > j:
                    sub.Reverse()
                return sub
            cs = [spans[m].DuplicateCurve() for m in range(lo, hi)]
            jc = G.Curve.JoinCurves(cs, 1e-6)
            if len(jc) != 1:
                return None
            sub = jc[0]
            if i > j:
                sub.Reverse()
            return sub

        if all(len(fl) == 1 for fl in groups.values()):
            return None, "no facets"                 # straight piece: nothing to smooth
        out = []
        merged = 0
        for root, fl in groups.items():
            sub = br.DuplicateSubBrep(fl)
            loops = G.Curve.JoinCurves(sub.DuplicateNakedEdgeCurves(True, True), 1e-5)
            if not any(longE[k] for i in fl for k in br.Faces[i].AdjacentEdges()):
                self.keep(out, fl); continue
            horizontal = all(abs(normals[i].Z) > 0.9999 for i in fl)
            face = None
            if horizontal:
                bnds = []
                for lp in loops:
                    cs = self.loop_curves(lp, run_of, smooth_sub)
                    if cs is None:
                        bnds = None; break
                    jb = G.Curve.JoinCurves(cs, 1e-5)
                    if len(jb) != 1 or not jb[0].IsClosed:
                        bnds = None; break
                    bnds.append(jb[0])
                if bnds:
                    if len(bnds) == 1:
                        pb = G.Brep.CreatePlanarBreps(bnds, TOL)
                        face = pb[0] if pb and len(pb) == 1 else None
                    else:
                        pb = G.Brep.CreatePlanarBreps(bnds, TOL)
                        if pb and len(pb) == 1 and pb[0].Faces[0].Loops.Count == len(bnds):
                            face = pb[0]
                    if face is None and len(bnds) > 1 and len(fl) > 1:
                        # ring-shaped run (the bed face round the open bottom of the void): rebuild its faces one by
                        # one with the smooth edges (seams stay only on the hidden bed face)
                        fs = []
                        for i in fl:
                            lp1 = G.Curve.JoinCurves(br.Faces[i].DuplicateFace(False).DuplicateNakedEdgeCurves(True, True), 1e-5)
                            cs = self.loop_curves(lp1[0], run_of, smooth_sub) if len(lp1) == 1 else None
                            jb = G.Curve.JoinCurves(cs, 1e-5) if cs else None
                            pb = G.Brep.CreatePlanarBreps([jb[0]], TOL) if jb and len(jb) == 1 else None
                            if not pb or len(pb) != 1:
                                fs = None; break
                            fs.append(pb[0])
                        if fs:
                            out.extend(fs[1:])
                            face = fs[0]
            elif len(loops) == 1:
                parts = self.loop_parts(loops[0], run_of, smooth_sub)
                if parts is not None:
                    lng = [c for k, c in parts if k]
                    if len(parts) == 4 and parts[0][0] and parts[2][0] and len(lng) == 2:
                        s1 = lng[0].DuplicateCurve(); s2 = lng[1].DuplicateCurve(); s2.Reverse()
                        lf = G.Brep.CreateFromLoft([s1, s2], G.Point3d.Unset, G.Point3d.Unset, G.LoftType.Straight, False)
                        face = lf[0] if lf else None
                    vertical = all(abs(normals[i].Z) < 1e-3 for i in fl)
                    if face is None and vertical:
                        face = self.vertical_face(parts, br, fl)
            elif len(loops) == 2:
                # closed band round a ring (crown ring faces): loft between the two smoothed closed loops
                cl = []
                for lp in loops:
                    cs = self.loop_curves(lp, run_of, smooth_sub)
                    jb = G.Curve.JoinCurves(cs, 1e-5) if cs else None
                    if not jb or len(jb) != 1 or not jb[0].IsClosed:
                        cl = None; break
                    cl.append(jb[0])
                if cl:
                    a, b = cl[0].DuplicateCurve(), cl[1].DuplicateCurve()
                    if a.ClosedCurveOrientation(G.Vector3d.ZAxis) != b.ClosedCurveOrientation(G.Vector3d.ZAxis):
                        b.Reverse()
                    ok, t = b.ClosestPoint(a.PointAtStart)
                    b.ChangeClosedCurveSeam(t)
                    lf = G.Brep.CreateFromLoft([a, b], G.Point3d.Unset, G.Point3d.Unset, G.LoftType.Straight, False)
                    face = lf[0] if lf and lf[0].Faces.Count == 1 else (lf[0] if lf else None)
                    if face is not None and face.Faces.Count != 1:
                        out.extend([face.Faces[k].DuplicateFace(False) for k in range(1, face.Faces.Count)])
                        face = face.Faces[0].DuplicateFace(False)
            if face is None:
                runs = set()
                for i in fl:
                    for k in br.Faces[i].AdjacentEdges():
                        if longE[k] and eseg[k]:
                            for m in range(len(eseg[k]) - 1):
                                r = run_of(eseg[k][m], eseg[k][m + 1])
                                if r >= 0:
                                    runs.add(r)
                if runs and not runs <= self.frozen:
                    self.fail_runs = runs
                    return None, "could not rebuild a run of %d faces (%s)" % (len(fl), fl[:6])
                self.keep(out, fl)                   # its lines are frozen: keep the original faces, they still fit
                continue
            out.append(face)
            merged += 1
        j = G.Brep.JoinBreps(out, 0.002)
        if not j or len(j) != 1 or not j[0].IsSolid:
            j2 = G.Brep.JoinBreps(out, 0.01)              # the model tolerance (some original bands are only closed at 1 cm)
            if j2 and len(j2) == 1 and j2[0].IsSolid:
                j = j2
            elif j and len(j) == 1:
                cp = j[0].CapPlanarHoles(0.002)          # a planar sliver left between a chord and its polyline
                if cp is not None and cp.IsSolid:
                    j = [cp]
        if not j or len(j) != 1 or not j[0].IsSolid:
            runs = set()
            for part in (j or []):
                for nc in part.DuplicateNakedEdgeCurves(True, True):
                    for t in (0.0, 0.5, 1.0):
                        p = nc.PointAtNormalizedLength(t)
                        for k, (pts, spans) in enumerate(smooth):
                            if any(sp.ClosestPoint(p)[0] and sp.PointAt(sp.ClosestPoint(p)[1]).DistanceTo(p) < 0.002 for sp in spans):
                                runs.add(k)
            self.fail_runs = runs
            return None, "join failed (%s parts, %d runs merged)" % (len(j) if j else 0, merged)
        b = j[0]
        if b.SolidOrientation == G.BrepSolidOrientation.Inward:
            b.Flip()
        return b, "ok (%d runs rebuilt, %d -> %d faces)" % (merged, nF, b.Faces.Count)

    def vertical_face(self, parts, br, fl):
        """vertical run with a stepped outline (notches at the ends): vertical extrusion of the smooth plan curve,
        trimmed by the run's own (smoothed) outline"""
        bb = br.DuplicateSubBrep(fl).GetBoundingBox(True)
        z0, z1 = bb.Min.Z - 0.01, bb.Max.Z + 0.01
        flat = []
        for k, c in parts:
            for seg in c.DuplicateSegments() if isinstance(c, G.PolyCurve) or isinstance(c, G.PolylineCurve) else [c]:
                cb = seg.GetBoundingBox(True)
                if cb.Max.Z - cb.Min.Z < 1e-4:
                    s2 = seg.DuplicateCurve()
                    s2.Transform(G.Transform.Translation(0, 0, z0 - cb.Min.Z))
                    flat.append(s2)
        if not flat:
            return None
        chains = G.Curve.JoinCurves(flat, 1e-5)
        base = max(chains, key=lambda c: c.GetLength()).DuplicateCurve()
        base = base.Extend(G.CurveEnd.Both, 0.05, G.CurveExtensionStyle.Smooth) or base
        srf = G.Surface.CreateExtrusion(base, G.Vector3d(0, 0, z1 - z0))
        if srf is None:
            return None
        sb = srf.ToBrep()
        loop = G.Curve.JoinCurves([c for k, c in parts], 1e-5)
        if len(loop) != 1:
            return None
        sp = sb.Faces[0].Split([loop[0]], 0.001)
        if sp is None or sp.Faces.Count < 2:
            return None
        ref = G.AreaMassProperties.Compute(br.DuplicateSubBrep(fl)).Centroid
        best = None
        for i in range(sp.Faces.Count):
            f = sp.Faces[i].DuplicateFace(False)
            amp = G.AreaMassProperties.Compute(f)
            if amp is None:
                continue
            ok_in = all(f.ClosestPoint(c.PointAtNormalizedLength(0.5)).DistanceTo(c.PointAtNormalizedLength(0.5)) < 2e-3 for k, c in parts)
            if ok_in and (best is None or amp.Centroid.DistanceTo(ref) < best[0]):
                best = (amp.Centroid.DistanceTo(ref), f)
        if not best:
            return None
        f = best[1]
        L0 = sum(c.GetLength() for k, c in parts)
        L1 = sum(c.GetLength() for c in f.DuplicateNakedEdgeCurves(True, True))
        return f if abs(L1 - L0) < 0.002 * L0 + 0.002 else None

    def loop_parts(self, lp, run_of, smooth_sub):
        """closed polyline loop -> [(is_long, curve)], long runs on one feature line replaced by the smooth sub-curve"""
        # split the loop into straight segments (polyline pieces) and curved pieces (kept as they are, transverse)
        segs = []                                   # (start, end, curve or None for straight)
        for sg in lp.DuplicateSegments() if lp.SpanCount > 1 or isinstance(lp, G.PolyCurve) else [lp]:
            okp, pl = sg.TryGetPolyline()
            if okp:
                pts = list(pl)
                for i in range(len(pts) - 1):
                    if pts[i].DistanceTo(pts[i + 1]) > 1e-9:
                        segs.append((pts[i], pts[i + 1], None))
            elif sg.IsLinear(1e-6):
                segs.append((sg.PointAtStart, sg.PointAtEnd, None))
            else:
                segs.append((sg.PointAtStart, sg.PointAtEnd, sg))
        n = len(segs)
        if n == 0:
            return None
        ids = []
        for a, b, c in segs:
            if c is None:
                ids.append(run_of(a, b) if self.is_long_pts(a, b) else None)
            else:
                ids.append(("C", len(ids)) if self.is_long_curve(c) else None)
        if all(x is not None for x in ids):
            s = next((i for i in range(n) if ids[i] != ids[i - 1]), 0)
        else:
            s = next(i for i in range(n) if ids[i] is not None and ids[i - 1] is None) if any(x is not None for x in ids) else 0
        segs = segs[s:] + segs[:s]; ids = ids[s:] + ids[:s]
        groups = []                                  # [rid, [points], [curves for transverse]]
        for i in range(n):
            a, b, c = segs[i]
            if groups and groups[-1][0] == ids[i] and (ids[i] is not None or groups[-1][0] is None):
                groups[-1][1].append(b); groups[-1][2].append(c if c is not None else G.LineCurve(a, b))
            else:
                groups.append([ids[i], [a, b], [c if c is not None else G.LineCurve(a, b)]])
        res = []
        for rid, pts, crvs in groups:
            if rid is None:
                jc = G.Curve.JoinCurves(crvs, 1e-6)
                if len(jc) != 1:
                    return None
                res.append((False, jc[0]))
            elif isinstance(rid, tuple):
                jc = G.Curve.JoinCurves(crvs, 1e-6)
                if len(jc) != 1:
                    return None
                res.append((True, jc[0]))
            else:
                c = smooth_sub(rid, pts[0], pts[-1])
                if c is None:
                    return None
                res.append((True, c))
        # a long side may run over several feature lines (T-junctions): join them into one side curve
        merged = []
        for k, c in res:
            if merged and merged[-1][0] and k:
                jc = G.Curve.JoinCurves([merged[-1][1], c], 1e-5)
                if len(jc) != 1:
                    return None
                merged[-1] = (True, jc[0])
            else:
                merged.append((k, c))
        return merged

    def loop_curves(self, lp, run_of, smooth_sub):
        parts = self.loop_parts(lp, run_of, smooth_sub)
        return None if parts is None else [c for k, c in parts]
