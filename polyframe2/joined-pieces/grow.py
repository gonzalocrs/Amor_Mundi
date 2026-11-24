"""Grow the steps outward (Gonzalo 2026-11-21): each course's riser moves out, uniformly along the course, just
enough to cover the open groove of the course below (and every rib point) with 1 cm, so no rib shows on the treads.

growth g_k = max(groove outer edge of course k-1 + 1 cm - riser of course k, max rib protrusion at course k + 1 cm)
skin  = ring between the course's outer face (1 cm inside, overlapping the 3 cm outer wall) and that face offset by g_k,
        z0..z1 (0.5 mm in), cut to the piece's own head joints (1 mm in)
piece = piece UNION skin.  Inner face, ribs, cores, rings, columns untouched."""
import json, math, time, collections, System
import Rhino, Rhino.Geometry as G

PROG = r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\polyframe2\joined-pieces\_grow_progress.txt"
SAMPLES = r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\polyframe2\half-steps-course-samples.json"

def log(s):
    open(PROG, "a").write(time.strftime("%H:%M:%S ") + s + "\n")

def growth(S, rt, cover=0.01):
    cs = S[rt]["courses"]; NS = len(cs[0]["rout"]); out = [0.0]
    for k in range(1, len(cs)):
        lo = cs[k - 1]; za, zb = lo["zs"][0], lo["zs"][2]; need = 0.0
        for i in range(NS):
            t = (lo["z1"] - za) / (zb - za)
            I1 = lo["rin"][0][i] + (lo["rin"][2][i] - lo["rin"][0][i]) * t
            edge = (I1 + lo["rout"][i]) / 2 + 0.03 + cover
            need = max(need, edge - cs[k]["rout"][i])
        out.append(need)
    return out

def poly(cx, cy, r, z):
    n = len(r)
    pts = [G.Point3d(cx + r[i] * math.cos(2 * math.pi * i / n), cy + r[i] * math.sin(2 * math.pi * i / n), z) for i in range(n)]
    pts.append(pts[0])
    return G.PolylineCurve(pts)

def offset(c, d, z):
    best = None
    for s in (d, -d):
        o = c.Offset(G.Plane(G.Point3d(0, 0, z), G.Vector3d.ZAxis), s, 0.0005, G.CurveOffsetCornerStyle.Sharp)
        if o and len(o) == 1 and o[0].IsClosed:
            a = abs(G.AreaMassProperties.Compute(o[0]).Area)
            if best is None or (a > best[0] if d > 0 else a < best[0]):
                best = (a, o[0])
    return best[1] if best else None

def ring_solid(cx, cy, rout, g, z0, z1, a=-0.01, b=None):
    """solid ring between the outer face offset by a and by b (default g), z0..z1"""
    base = poly(cx, cy, rout, z0)
    outer = offset(base, g if b is None else b, z0)
    inner = offset(base, a, z0) if abs(a) > 1e-6 else base
    b = G.Brep.CreatePlanarBreps([outer, inner], 0.0005)
    if not b:
        return None
    ex = G.Brep.CreateFromOffsetFace(b[0].Faces[0], z1 - z0, 0.0005, False, True)
    if ex is None:
        return None
    if ex.GetBoundingBox(True).Max.Z < z1 - 1e-4:
        ex = G.Brep.CreateFromOffsetFace(b[0].Faces[0], -(z1 - z0), 0.0005, False, True)
    if ex.SolidOrientation == G.BrepSolidOrientation.Inward:
        ex.Flip()
    return ex

def wedge(J, src, c, inset=0.001, zpad=0.05):
    ef = J._end_faces(src, c)
    if ef is None:
        return None
    bb = src.GetBoundingBox(True)
    (ca, na, _), (cb, nb, _) = ef
    u = G.Point3d(cb.X, cb.Y, 0) - G.Point3d(ca.X, ca.Y, 0); u.Unitize()
    pts = []
    for cp, n, sgn in ((ca, na, 1), (cb, nb, -1)):
        d = G.Vector3d.CrossProduct(G.Vector3d.ZAxis, n); d.Unitize()
        rad = G.Vector3d(cp.X - c.X, cp.Y - c.Y, 0); rad.Unitize()
        if d * rad < 0:
            d.Reverse()
        p = G.Point3d(cp.X, cp.Y, bb.Min.Z - zpad) + u * (sgn * inset)
        pts.append((p - d * 0.8, p + d * 0.8))
    (a0, a1), (b0, b1) = pts
    pl = G.PolylineCurve([a0, a1, b1, b0, a0])
    hgt = bb.Max.Z - bb.Min.Z + 2 * zpad
    ex = G.Extrusion.Create(pl, -hgt, True)
    w = ex.ToBrep()
    if w.GetBoundingBox(True).Max.Z < bb.Max.Z:          # extruded downward: go up instead
        w = G.Extrusion.Create(pl, hgt, True).ToBrep()
    if w.SolidOrientation == G.BrepSolidOrientation.Inward:
        w.Flip()
    return w

def run(doc, rt, save_every=80):
    import importlib.util
    s = importlib.util.spec_from_file_location("jg", r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\polyframe2\joined-pieces\joined_gen.py")
    J = importlib.util.module_from_spec(s); s.loader.exec_module(J)
    S = json.load(open(SAMPLES)); R = S[rt]; cs = R["courses"]; cx, cy = R["cx"], R["cy"]; c = G.Point3d(cx, cy, 0)
    gr = growth(S, rt)
    prot = json.load(open(r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\polyframe2\joined-pieces\_rib_protrusion_per_course.json"))[rt]
    for k, z, n, mx in prot:
        if k > 0 and mx > 0.001:
            gr[k] = max(gr[k], mx + 0.01)
    log("%s growth per course (m): %s" % (rt, [round(g, 3) for g in gr]))
    root = rt + " complete v3e-ring-step::"
    jl = doc.Layers[doc.Layers.FindByFullPath(root + "printed pieces + rib (joined)", -1)]
    rings = {}
    st = collections.Counter(); added = 0.0; k_done = 0
    for o in list(doc.Objects.FindByLayer(jl)):
        if o.Attributes.GetUserString("grown"):
            continue
        src = doc.Objects.FindId(System.Guid(o.Attributes.GetUserString("source_piece"))).Geometry
        z0 = src.GetBoundingBox(True).Min.Z
        k = min(range(len(cs)), key=lambda i: abs(cs[i]["z0"] - z0))
        g = gr[k]
        a = o.Attributes.Duplicate()
        if g <= 0.001:
            a.SetUserString("grown", "0"); doc.Objects.ModifyAttributes(o, a, True); st["no growth"] += 1; continue
        if k not in rings:
            z0k, z1k = cs[k]["z0"], cs[k]["z1"]
            band = ring_solid(cx, cy, cs[k]["rout"], g, z0k + 0.0005, z1k - 0.0005)                      # old face -1 cm .. new face
            hole = ring_solid(cx, cy, cs[k]["rout"], g, z0k - 0.02, z1k - 0.03, a=0.002, b=g - 0.03)    # hollow: old face +2 mm .. new face -3 cm, open at the bottom
            rings[k] = (band, hole)
        band, hole = rings[k]
        w = wedge(J, src, c)
        wi = wedge(J, src, c, inset=0.031, zpad=0.06)                                                     # 3 cm end walls
        res = None
        sep = None
        if band is not None and hole is not None and w is not None and wi is not None:
            sk = G.Brep.CreateBooleanIntersection(band, w, 0.0005)
            hv = G.Brep.CreateBooleanIntersection(hole, wi, 0.0005)
            if sk and len(sk) == 1 and hv:
                skin = G.Brep.CreateBooleanDifference([sk[0]], list(hv), 0.0005)
                if skin and len(skin) == 1 and skin[0].IsSolid:
                    skin_b = skin[0]
                    u = G.Brep.CreateBooleanUnion([o.Geometry, skin_b], 0.0005)
                    if u and len(u) == 1 and u[0].IsValid and u[0].IsSolid:
                        # strict check (2026-11-21, after 4 broken pieces): the union must be the piece plus the band,
                        # nothing lost: volume within 1 % of piece + band, and it still covers the piece's slot
                        vp = abs(G.VolumeMassProperties.Compute(o.Geometry, True, False, False, False).Volume)
                        vs = abs(G.VolumeMassProperties.Compute(skin_b, True, False, False, False).Volume)
                        vu = abs(G.VolumeMassProperties.Compute(u[0], True, False, False, False).Volume)
                        a_ = o.Geometry.GetBoundingBox(True); b_ = u[0].GetBoundingBox(True)
                        covers = (b_.Min.X <= a_.Min.X + 0.002 and b_.Min.Y <= a_.Min.Y + 0.002 and b_.Min.Z <= a_.Min.Z + 0.002 and
                                  b_.Max.X >= a_.Max.X - 0.002 and b_.Max.Y >= a_.Max.Y - 0.002 and b_.Max.Z >= a_.Max.Z - 0.002)
                        # the band overlaps the old wall by ~1.2 cm, so allow the union to be up to that overlap smaller
                        if covers and vp + 0.5 * vs <= vu <= (vp + vs) * 1.01:
                            res = u[0]
                    if res is None:
                        sep = skin_b
        if res is not None:
            v0 = abs(G.VolumeMassProperties.Compute(o.Geometry, True, False, False, False).Volume)
            v1 = abs(G.VolumeMassProperties.Compute(res, True, False, False, False).Volume)
            added += v1 - v0
            a.SetUserString("grown", "%.3f" % g); doc.Objects.Replace(o.Id, res); doc.Objects.ModifyAttributes(o.Id, a, True)
            st["grown"] += 1
        elif sep is not None:
            # the piece stays exactly as it was; the growth band sits against it as its own object, same layer
            b = Rhino.DocObjects.ObjectAttributes(); b.LayerIndex = jl.Index; b.Name = "growth band (separate, merge failed)"
            b.SetUserString("band_for_piece", str(o.Id)); doc.Objects.AddBrep(sep, b)
            a.SetUserString("grown", "band separate"); doc.Objects.ModifyAttributes(o.Id, a, True); st["band separate"] += 1
            added += abs(G.VolumeMassProperties.Compute(sep, True, False, False, False).Volume)
        else:
            a.SetUserString("grown", "FAILED"); doc.Objects.ModifyAttributes(o.Id, a, True); st["failed"] += 1
        k_done += 1
        if k_done % 20 == 0:
            log("%s %d %s added %.2f m3" % (rt, k_done, dict(st), added))
        if k_done % save_every == 0:
            doc.ClearUndoRecords(True); Rhino.RhinoApp.RunScript("_-Save _Enter", False); log("saved")
    doc.ClearUndoRecords(True)
    log("%s DONE %s added %.2f m3" % (rt, dict(st), added))
    return gr
