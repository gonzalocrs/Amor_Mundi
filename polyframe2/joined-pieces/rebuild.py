"""Clean rebuild of the visible printed-piece layer, one object per slot (QA after Gonzalo's screenshots 2026-11-21).

Per original piece (slot):
  keep the current joined/filled object only if it is a valid closed solid, covers its slot, does not reach more than
  6 cm beyond it, and its volume is plausible (joined 0.95-1.35 x, filled 0.95-2.3 x the plain piece);
  else re-join without the fill (same checks, 0.95-1.35 x);
  else put the original piece back ("FAILED - original piece") and keep its rib slice next to it.
Then: all printed / rib layers in the piece colour, rib ends below the ring trimmed to what sticks out of the ring
(no coincident faces under the soffit), all solids oriented outward. Ribs, cores, rings and outer faces untouched."""
import importlib.util, collections, time, System
import Rhino, Rhino.Geometry as G

PROG = r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\polyframe2\joined-pieces\_rebuild_progress.txt"
PIECE_COLOUR = System.Drawing.Color.FromArgb(236, 229, 214)

def L_(n, p):
    s = importlib.util.spec_from_file_location(n, p); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

def vol(b):
    vm = G.VolumeMassProperties.Compute(b, True, False, False, False)
    return abs(vm.Volume) if vm else 0.0

def check(o_geo, s_geo, vmax):
    if o_geo is None or not (o_geo.IsValid and o_geo.IsSolid):
        return False
    a = s_geo.GetBoundingBox(True); b = o_geo.GetBoundingBox(True)
    grow = max(a.Min.X - b.Min.X, b.Max.X - a.Max.X, a.Min.Y - b.Min.Y, b.Max.Y - a.Max.Y, a.Min.Z - b.Min.Z, b.Max.Z - a.Max.Z)
    shrink = max(b.Min.X - a.Min.X, a.Max.X - b.Max.X, b.Min.Y - a.Min.Y, a.Max.Y - b.Max.Y, b.Min.Z - a.Min.Z, a.Max.Z - b.Max.Z)
    if grow > 0.06 or shrink > 0.01:
        return False
    vr = vol(o_geo) / max(vol(s_geo), 1e-9)
    return 0.95 <= vr <= vmax

def log(s):
    open(PROG, "a").write(time.strftime("%H:%M:%S ") + s + "\n")

def run(doc, root, cx, cy):
    J = L_("jg", r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\polyframe2\joined-pieces\joined_gen.py")
    R = root + "::"
    lay = lambda n: doc.Layers[doc.Layers.FindByFullPath(R + n, -1)]
    li = lay("printed pieces + rib (joined)").Index
    sl = lay("rib slices of the pieces that did not join").Index
    el = lay("rib ends outside the printed courses (landings on the base ring, crown domes)").Index
    ribs = [(o.Geometry, o.Geometry.GetBoundingBox(True)) for o in doc.Objects.FindByLayer(lay("ribs (final, joint fillets)"))]
    cores = [(o.Geometry, o.Geometry.GetBoundingBox(True)) for o in doc.Objects.FindByLayer(lay("cast rib cores - pushed in (bottom 4 cm showing, same sizes)"))]
    srcs = list(doc.Objects.FindByLayer(lay("printed pieces (closed solids, 3 cm walls, lid 3, groove 6x4)"))) + \
           list(doc.Objects.FindByLayer(lay("top course = printed U formwork for the crown ring")))
    cur = collections.defaultdict(list)
    for o in doc.Objects.FindByLayer(doc.Layers[li]):
        cur[o.Attributes.GetUserString("source_piece")].append(o)
    c = G.Point3d(cx, cy, 0)
    st = collections.Counter()
    fallback = []
    for k, s in enumerate(srcs):
        sg = s.Geometry
        objs = cur.get(str(s.Id), [])
        keep = None
        for o in objs:
            filled = o.Attributes.GetUserString("fill") == "filled"
            js = o.Attributes.GetUserString("join_status")
            if js in ("joined", "no-rib") and check(o.Geometry, sg, 2.3 if filled else 1.35):
                keep = o; break
        for o in objs:
            if o is not keep:
                doc.Objects.Delete(o, True)
        if keep is not None:
            st["kept " + ("filled" if keep.Attributes.GetUserString("fill") == "filled" else keep.Attributes.GetUserString("join_status"))] += 1
            if keep.Geometry.SolidOrientation == G.BrepSolidOrientation.Inward:
                g = keep.Geometry.DuplicateBrep(); g.Flip(); doc.Objects.Replace(keep.Id, g)
        else:
            j, s2, info = J.join_piece(sg, c, ribs, cores)
            a = Rhino.DocObjects.ObjectAttributes(); a.LayerIndex = li; a.SetUserString("source_piece", str(s.Id))
            if not s2.startswith("fail") and check(j, sg, 1.35):
                a.Name = "joined (fill dropped)" if s2 == "joined" else s2
                a.SetUserString("join_status", s2); a.SetUserString("fill", "dropped" if s2 == "joined" else "")
                doc.Objects.AddBrep(j, a); st["rejoined"] += 1
            else:
                g = sg.DuplicateBrep()
                if g.SolidOrientation == G.BrepSolidOrientation.Inward:
                    g.Flip()
                a.Name = "FAILED - original piece"; a.SetUserString("join_status", "failed-original")
                doc.Objects.AddBrep(g, a); st["original"] += 1; fallback.append(sg)
        if k % 20 == 0:
            log("%s %d/%d %s" % (root[:5], k, len(srcs), dict(st)))
    # rib slices only for the slots that fell back to the original piece
    for o in list(doc.Objects.FindByLayer(doc.Layers[sl])):
        doc.Objects.Delete(o, True)
    ns = 0
    for sg in fallback:
        cl, _ = J.cell(sg, c, inset=0.001)
        if cl is None:
            continue
        for r in J._near(cl.GetBoundingBox(True), ribs):
            for x in (G.Brep.CreateBooleanIntersection(r, cl, 0.0005) or []):
                if x.IsValid and x.IsSolid:
                    a = Rhino.DocObjects.ObjectAttributes(); a.LayerIndex = sl; doc.Objects.AddBrep(x, a); ns += 1
    # rib ends below the ring: keep only what sticks out of the base ring (no coincident faces under the soffit)
    ring = [o.Geometry for nm in ("base ring step - printed U formwork (3 cm)", "base ring step - cast ring inside")
            for o in doc.Objects.FindByLayer(lay(nm))]
    ring = [g.ToBrep() if isinstance(g, G.Extrusion) else g for g in ring]
    trimmed = kept = 0
    for o in list(doc.Objects.FindByLayer(doc.Layers[el])):
        if o.Geometry.GetBoundingBox(True).Max.Z > 2.81:
            continue
        d = G.Brep.CreateBooleanDifference([o.Geometry], ring, 0.0005)
        if d is not None:
            doc.Objects.Delete(o, True)
            for x in d:
                if x.IsValid and vol(x) > 1e-6:
                    a = o.Attributes.Duplicate(); doc.Objects.AddBrep(x, a)
            trimmed += 1
        else:
            kept += 1
    # one colour for every printed / rib layer
    for i in (li, sl, el):
        L = doc.Layers[i]; L.Color = PIECE_COLOUR; doc.Layers.Modify(L, i, True)
    doc.ClearUndoRecords(True)
    n = len(doc.Objects.FindByLayer(doc.Layers[li]))
    res = "%s DONE slots %d visible %d %s slices %d ends trimmed %d kept %d" % (root[:5], len(srcs), n, dict(st), ns, trimmed, kept)
    log(res)
    return res
