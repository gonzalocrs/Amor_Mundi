import importlib.util, time, collections, System
import Rhino, Rhino.Geometry as G

def L_(n, p):
    s = importlib.util.spec_from_file_location(n, p); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

def run(doc, root, cx, cy, budget=230):
    J = L_("jg", r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\polyframe2\joined-pieces\joined_gen.py")
    F = L_("fg", r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\polyframe2\joined-pieces\fill_gen.py")
    lay = lambda n: doc.Layers[doc.Layers.FindByFullPath(root + "::" + n, -1)]
    ribs = [(o.Geometry, o.Geometry.GetBoundingBox(True)) for o in doc.Objects.FindByLayer(lay("ribs (final, joint fillets)"))]
    cores = [(o.Geometry, o.Geometry.GetBoundingBox(True)) for o in doc.Objects.FindByLayer(lay("cast rib cores - pushed in (bottom 4 cm showing, same sizes)"))]
    c = G.Point3d(cx, cy, 0)
    todo = [o for o in doc.Objects.FindByLayer(lay("printed pieces + rib (joined)"))
            if o.Attributes.GetUserString("join_status") == "joined" and not o.Attributes.GetUserString("fill")]
    t = time.time(); res = collections.Counter(); added = 0.0
    for o in todo:
        if time.time() - t > budget:
            break
        src = doc.Objects.FindId(System.Guid(o.Attributes.GetUserString("source_piece"))).Geometry
        j, s, dv = F.fill_piece(o.Geometry, src, c, ribs, cores, J)
        a = o.Attributes.Duplicate(); a.SetUserString("fill", s)
        if s == "filled":
            a.SetUserString("fill_added_m3", "%.5f" % dv); added += dv
            doc.Objects.Replace(o.Id, j)
        doc.Objects.ModifyAttributes(o.Id, a, True)
        res[s] += 1
        if sum(res.values()) % 5 == 0:
            open(r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\polyframe2\joined-pieces\_fill_progress.txt", "a").write("%s %s %s\n" % (root[:5], time.strftime("%H:%M:%S"), dict(res)))
    doc.ClearUndoRecords(True)
    left = sum(1 for o in doc.Objects.FindByLayer(lay("printed pieces + rib (joined)"))
               if o.Attributes.GetUserString("join_status") == "joined" and not o.Attributes.GetUserString("fill"))
    return dict(res), round(added, 3), left, round(time.time() - t)
