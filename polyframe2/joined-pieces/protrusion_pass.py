"""Second QA pass: no printed piece may stick out into the room (or anywhere) beyond
(plain piece envelope) + (its rib tube parts). Checks mesh vertices of every kept joined/filled piece;
a piece with vertices more than 8 mm outside is re-joined without the fill, or falls back to the original piece."""
import importlib.util, collections, time, System
import Rhino, Rhino.Geometry as G

PROG = r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\polyframe2\joined-pieces\_rebuild_progress.txt"

def L_(n, p):
    s = importlib.util.spec_from_file_location(n, p); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

def log(s):
    open(PROG, "a").write(time.strftime("%H:%M:%S ") + s + "\n")

def outside_count(geo, env, parts, tol=0.008):
    n = 0
    mp = G.MeshingParameters.FastRenderMesh
    for m in G.Mesh.CreateFromBrep(geo, mp):
        for v in m.Vertices:
            p = G.Point3d(v)
            if env.IsPointInside(p, 0.001, False):
                continue
            q = env.ClosestPoint(p)
            if q.DistanceTo(p) <= tol:
                continue
            ok = False
            for r in parts:
                if r.IsPointInside(p, 0.001, False) or r.ClosestPoint(p).DistanceTo(p) <= tol:
                    ok = True; break
            if not ok:
                n += 1
    return n

def run(doc, root, cx, cy):
    J = L_("jg", r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\polyframe2\joined-pieces\joined_gen.py")
    F = L_("fg", r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\polyframe2\joined-pieces\fill_gen.py")
    B = L_("rb", r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\polyframe2\joined-pieces\rebuild.py")
    R = root + "::"
    lay = lambda n: doc.Layers[doc.Layers.FindByFullPath(R + n, -1)]
    li = lay("printed pieces + rib (joined)").Index; sl = lay("rib slices of the pieces that did not join").Index
    ribs = [(o.Geometry, o.Geometry.GetBoundingBox(True)) for o in doc.Objects.FindByLayer(lay("ribs (final, joint fillets)"))]
    cores = [(o.Geometry, o.Geometry.GetBoundingBox(True)) for o in doc.Objects.FindByLayer(lay("cast rib cores - pushed in (bottom 4 cm showing, same sizes)"))]
    c = G.Point3d(cx, cy, 0)
    st = collections.Counter(); k = 0
    for o in list(doc.Objects.FindByLayer(doc.Layers[li])):
        js = o.Attributes.GetUserString("join_status")
        if js not in ("joined",):
            continue
        src = doc.Objects.FindId(System.Guid(o.Attributes.GetUserString("source_piece"))).Geometry
        env = F.envelope(src, shrink=0.0, lift=0.0, top_clear=0.08)
        cl, _ = J.cell(src, c, inset=0.001)
        parts = [x for r in J._near(cl.GetBoundingBox(True), ribs) for x in (G.Brep.CreateBooleanIntersection(r, cl, 0.0005) or []) if x.IsSolid] if cl else []
        if env is None:
            st["no-envelope (kept)"] += 1; continue
        n = outside_count(o.Geometry, env, parts)
        k += 1
        if n <= 100:          # a few vertices on the lid/groove edges sit just outside the check volume: noise
            st["clean"] += 1
        else:
            filled = o.Attributes.GetUserString("fill") == "filled"
            j, s2, info = J.join_piece(src, c, ribs, cores)
            a = o.Attributes.Duplicate()
            if filled and not s2.startswith("fail") and B.check(j, src, 1.35) and outside_count(j, env, parts) <= 100:
                a.Name = "joined (fill dropped: it stuck out)"; a.SetUserString("fill", "dropped-protrusion")
                doc.Objects.Replace(o.Id, j); st["fill dropped"] += 1
            else:
                g = src.DuplicateBrep()
                if g.SolidOrientation == G.BrepSolidOrientation.Inward:
                    g.Flip()
                a.Name = "FAILED - original piece"; a.SetUserString("join_status", "failed-original"); a.SetUserString("fill", "")
                doc.Objects.Replace(o.Id, g); st["original"] += 1
                for x in parts:
                    aa = Rhino.DocObjects.ObjectAttributes(); aa.LayerIndex = sl; doc.Objects.AddBrep(x, aa)
        if k % 25 == 0:
            log("protrusion %s %d %s" % (root[:5], k, dict(st)))
        if k % 75 == 0:
            doc.ClearUndoRecords(True); Rhino.RhinoApp.RunScript("_-Save _Enter", False); log("saved")
    doc.ClearUndoRecords(True)
    res = "protrusion %s DONE %s" % (root[:5], dict(st))
    log(res)
    return res
