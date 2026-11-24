"""Close the slots in the grown outer face (Gonzalo's renders 2026-11-21). Per course, walk offset curves of the
course outline from the grown face inward (every 5 mm, down to 1 cm inside the old face) at 3 heights; any stretch
wider than 4 mm (a head joint is 2 mm) not inside a printed object at all 3 heights is a slot cell. The cells of each
level are turned into thin strips, extruded over the course (0.5 mm in) and unioned into one filler per slot. Strict
union with the neighbouring piece if the volume adds up, else kept as its own object "slot filler". Adds material only."""
import json, time, importlib.util
import Rhino, Rhino.Geometry as G

PROG = r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\polyframe2\joined-pieces\_fixslots_progress.txt"
TOL = 0.0005


def log(s):
    open(PROG, "a").write(time.strftime("%H:%M:%S ") + s + "\n")


def L_(n, p):
    s = importlib.util.spec_from_file_location(n, p); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


def vol(b):
    return abs(G.VolumeMassProperties.Compute(b, True, False, False, False).Volume)


def sections(objs, z):
    pl = G.Plane(G.Point3d(0, 0, z), G.Vector3d.ZAxis)
    out = []
    for o, bb in objs:
        if bb.Min.Z <= z <= bb.Max.Z:
            ok, cc, pp = G.Intersect.Intersection.BrepPlane(o.Geometry, pl, TOL)
            if ok and cc:
                out += [c for c in G.Curve.JoinCurves(cc, 0.001) if c.IsClosed]
    return out


def outside_mask(ref, secs_by_h, n):
    """True per sample where the point is outside every section at every height"""
    ts = ref.DivideByCount(n, True)
    res = []
    for t in ts:
        p = ref.PointAt(t); out_all = True
        for z, secs in secs_by_h:
            q = G.Point3d(p.X, p.Y, z); pl = G.Plane(q, G.Vector3d.ZAxis)
            for c, bb in secs:
                if bb.Min.X - 1e-3 <= q.X <= bb.Max.X + 1e-3 and bb.Min.Y - 1e-3 <= q.Y <= bb.Max.Y + 1e-3:
                    if c.Contains(q, pl, 0.0003) != G.PointContainment.Outside:
                        out_all = False; break
            if not out_all:
                break
        res.append(out_all)
    return ts, res


def run(doc, rt, dry=False, step=0.004):
    GR = L_("gr", r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\polyframe2\joined-pieces\grow.py")
    S = json.load(open(GR.SAMPLES)); R = S[rt]; cs = R["courses"]; cx, cy = R["cx"], R["cy"]
    gr = GR.growth(S, rt)
    prot = json.load(open(r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\polyframe2\joined-pieces\_rib_protrusion_per_course.json"))[rt]
    for k, z, nn, mx in prot:
        if k > 0 and mx > 0.001:
            gr[k] = max(gr[k], mx + 0.01)
    jl = doc.Layers[doc.Layers.FindByFullPath(rt + " complete v3e-ring-step::printed pieces + rib (joined)", -1)]
    objs = [(o, o.Geometry.GetBoundingBox(True)) for o in doc.Objects.FindByLayer(jl)]
    report = []
    for k in range(1, len(cs)):
        z0, z1 = cs[k]["z0"], cs[k]["z1"]
        secs_by_h = []
        for f in (0.5, 0.15, 0.85):
            z = z0 + (z1 - z0) * f
            secs_by_h.append((z, [(c, c.GetBoundingBox(True)) for c in sections(objs, z)]))
        base = GR.poly(cx, cy, cs[k]["rout"], z0)
        strips = []
        d = gr[k] - 0.0025
        lv = []
        while d > -0.01:
            lv.append(d); d -= 0.01
        for d in lv:
            ref = GR.offset(base, d, z0)
            if ref is None:
                continue
            L = ref.GetLength(); n = int(L / step)
            ts, mask = outside_mask(ref, secs_by_h, n)
            i = 0
            while i < n:
                if mask[i]:
                    j = i
                    while j + 1 < n and mask[j + 1]:
                        j += 1
                    w = (j - i + 1) * step
                    if w > 0.004:
                        ta = ts[max(i - 2, 0)]; tb = ts[min(j + 2, n - 1)]
                        a = ref.Trim(ta, tb)
                        if a is not None:
                            o1 = a.DuplicateCurve(); o1.Translate(G.Vector3d(0, 0, 0))
                            pa, pb = a.PointAtStart, a.PointAtEnd
                            ctr = G.Point3d(cx, cy, z0)
                            strips.append((d, a, w, a.PointAt(a.Domain.Mid)))
                    i = j + 1
                else:
                    i += 1
        # group strips by position (slot) and build a solid from each strip: offset band +-2.5 mm around the level
        groups = []
        for s in strips:
            for g in groups:
                if g[0][3].DistanceTo(s[3]) < max(0.15, s[2] + 0.05) or any(x[3].DistanceTo(s[3]) < 0.03 + s[2] for x in g):
                    g.append(s); break
            else:
                groups.append([s])
        for g in groups:
            w = max(s[2] for s in g); c = g[0][3]
            rec = (k, len(g), round(w * 1000), round(c.X, 2), round(c.Y, 2))
            if dry:
                report.append(rec); continue
            parts = []
            for d, a, ww, mid in g:
                pl = G.Plane(G.Point3d(0, 0, z0), G.Vector3d.ZAxis)
                oa = a.Offset(pl, 0.0055, TOL, G.CurveOffsetCornerStyle.Sharp)
                ob = a.Offset(pl, -0.0055, TOL, G.CurveOffsetCornerStyle.Sharp)
                if not oa or not ob:
                    continue
                A, B = oa[0], ob[0]
                B.Reverse()
                pts = [A.PointAtStart, A.PointAtEnd, B.PointAtStart, B.PointAtEnd]
                loop = G.Curve.JoinCurves([A, G.LineCurve(A.PointAtEnd, B.PointAtStart), B, G.LineCurve(B.PointAtEnd, A.PointAtStart)], 0.0005)
                if not loop or not loop[0].IsClosed:
                    continue
                lp = loop[0]; lp.Translate(G.Vector3d(0, 0, 0.0005))
                ex = G.Extrusion.Create(lp, z1 - z0 - 0.001, True)
                b = ex.ToBrep() if ex else None
                if b is None:
                    continue
                if b.GetBoundingBox(True).Max.Z < z0 + 0.01:
                    b = G.Extrusion.Create(lp, -(z1 - z0 - 0.001), True).ToBrep()
                if b.SolidOrientation == G.BrepSolidOrientation.Inward:
                    b.Flip()
                parts.append(b)
            if not parts:
                report.append(rec + ("no parts",)); continue
            fu = G.Brep.CreateBooleanUnion(parts, TOL) if len(parts) > 1 else parts
            fills = [x for x in (fu or parts) if x.IsSolid]
            for fb in fills:
                vf = vol(fb); done = False
                fbb = fb.GetBoundingBox(True); fbb.Inflate(0.003)
                for o, bb in objs:
                    if o.Attributes.GetUserString("band_for_piece") or not G.BoundingBox.Intersection(bb, fbb).IsValid:
                        continue
                    u = G.Brep.CreateBooleanUnion([o.Geometry, fb], TOL)
                    if u and len(u) == 1 and u[0].IsSolid and u[0].IsValid:
                        vp = vol(o.Geometry); vu = vol(u[0])
                        if vp + 0.3 * vf <= vu <= (vp + vf) * 1.005:
                            a_ = o.Attributes.Duplicate(); a_.SetUserString("slot_filled", "1")
                            doc.Objects.Replace(o.Id, u[0]); doc.Objects.ModifyAttributes(o.Id, a_, True)
                            done = True; report.append(rec + ("merged", str(o.Id)[:8], round(vf * 1e6))); break
                if not done:
                    at = Rhino.DocObjects.ObjectAttributes(); at.LayerIndex = jl.Index; at.Name = "slot filler (separate)"
                    doc.Objects.AddBrep(fb, at); report.append(rec + ("separate", round(vf * 1e6)))
        log("%s course %d: %d slots %s" % (rt, k, len(groups), [r for r in report if r[0] == k]))
    doc.ClearUndoRecords(True)
    log("%s DONE" % rt)
    return report
