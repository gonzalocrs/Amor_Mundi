"""Second pass: re-run the failed pieces of a roof's joined layer with the current joined_gen strategies, replace in place."""
import importlib.util, collections, time, System
import Rhino, Rhino.Geometry as G

def run(doc, root, cx, cy, limit=1000, budget=240):
    spec = importlib.util.spec_from_file_location("jg", r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\polyframe2\joined-pieces\joined_gen.py")
    J = importlib.util.module_from_spec(spec); spec.loader.exec_module(J)
    lay = lambda n: doc.Layers[doc.Layers.FindByFullPath(root + "::" + n, -1)]
    ribs = [(o.Geometry, o.Geometry.GetBoundingBox(True)) for o in doc.Objects.FindByLayer(lay("ribs (final, joint fillets)"))]
    cores = [(o.Geometry, o.Geometry.GetBoundingBox(True)) for o in doc.Objects.FindByLayer(lay("cast rib cores - pushed in (bottom 4 cm showing, same sizes)"))]
    jl = lay("printed pieces + rib (joined)")
    fails = [o for o in doc.Objects.FindByLayer(jl) if (o.Attributes.GetUserString("join_status") or "").startswith("fail")
             and o.Attributes.GetUserString("pass2") != "tried"]
    c = G.Point3d(cx, cy, 0); res = collections.Counter(); t = time.time()
    for o in fails[:limit]:
        if time.time() - t > budget:
            break
        src = doc.Objects.FindId(System.Guid(o.Attributes.GetUserString("source_piece"))).Geometry
        j, s, info = J.join_piece(src, c, ribs, cores)
        a = o.Attributes.Duplicate(); a.SetUserString("pass2", "tried")
        if not s.startswith("fail"):
            a.Name = s; a.SetUserString("join_status", s)
            doc.Objects.Replace(o.Id, j)
        else:
            a.SetUserString("join_status", s); a.Name = "FAILED (" + s + ") - plain piece"
        doc.Objects.ModifyAttributes(o.Id, a, True)
        res[s] += 1
    doc.ClearUndoRecords(True)
    left = sum(1 for o in doc.Objects.FindByLayer(jl) if (o.Attributes.GetUserString("join_status") or "").startswith("fail") and o.Attributes.GetUserString("pass2") != "tried")
    return dict(res), left, round(time.time() - t)
