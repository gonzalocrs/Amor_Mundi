"""Growth bands (Gonzalo 2026-11-21): the approved printed pieces stay untouched; each piece gets its own band on the
outer face, grown by the per-course amount (just enough to cover the groove below and every rib by 1 cm), printed like
the pieces (3 cm outer wall, lid, 3 cm end walls, open at the bottom), cut to the piece's own head joints (1 mm in,
so neighbouring bands meet with a 2 mm joint). Separate object, grouped with its piece, NOT boolean-merged.
If the hollow fails the band is kept solid (logged)."""
import json, time, importlib.util, collections
import Rhino, Rhino.Geometry as G

PROG = r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\polyframe2\rib-pipes\_bands_progress.txt"
TOL = 0.0005
PIECES = ("printed pieces (closed solids, 3 cm walls, lid 3, groove 6x4)", "top course = printed U formwork for the crown ring")


def log(s):
    open(PROG, "a").write(time.strftime("%H:%M:%S ") + s + "\n")


def L_(n, p):
    s = importlib.util.spec_from_file_location(n, p); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


def run(doc, rt):
    GR = L_("gr", r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\polyframe2\joined-pieces\grow.py")
    J = L_("jg", r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\polyframe2\joined-pieces\joined_gen.py")
    S = json.load(open(GR.SAMPLES)); R = S[rt]; cs = R["courses"]; cx, cy = R["cx"], R["cy"]; c = G.Point3d(cx, cy, 0)
    gr = GR.growth(S, rt)
    prot = json.load(open(r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\polyframe2\joined-pieces\_rib_protrusion_per_course.json"))[rt]
    for k, z, n, mx in prot:
        if k > 0 and mx > 0.001:
            gr[k] = max(gr[k], mx + 0.01)
    root = rt + " complete v3e-ring-step"
    i = doc.Layers.FindByFullPath(root + "::growth bands (outer face, per piece)", -1)
    if i < 0:
        Ly = Rhino.DocObjects.Layer(); Ly.Name = "growth bands (outer face, per piece)"
        Ly.ParentLayerId = doc.Layers[doc.Layers.FindByFullPath(root, -1)].Id
        i = doc.Layers.Add(Ly)
    bl = i
    rings = {}
    st = collections.Counter(); kd = 0
    for pn in PIECES:
        pl = doc.Layers[doc.Layers.FindByFullPath(root + "::" + pn, -1)]
        for o in list(doc.Objects.FindByLayer(pl)):
            src = o.Geometry
            if isinstance(src, G.Extrusion):
                src = src.ToBrep()
            z0 = src.GetBoundingBox(True).Min.Z
            k = min(range(len(cs)), key=lambda q: abs(cs[q]["z0"] - z0))
            g = gr[k]
            if g <= 0.001:
                st["no growth (course %d)" % k] += 1; continue
            if k not in rings:
                z0k, z1k = cs[k]["z0"], cs[k]["z1"]
                rings[k] = (GR.ring_solid(cx, cy, cs[k]["rout"], g, z0k + 0.0005, z1k - 0.0005),
                            GR.ring_solid(cx, cy, cs[k]["rout"], g, z0k - 0.02, z1k - 0.03, a=0.002, b=g - 0.03))
            band, hole = rings[k]
            w = GR.wedge(J, src, c); wi = GR.wedge(J, src, c, inset=0.031, zpad=0.06)
            res = None; kind = ""
            if band is not None and w is not None:
                sk = G.Brep.CreateBooleanIntersection(band, w, TOL)
                if sk and len(sk) == 1 and sk[0].IsSolid:
                    res = sk[0]; kind = "solid"
                    if hole is not None and wi is not None:
                        hv = G.Brep.CreateBooleanIntersection(hole, wi, TOL)
                        if hv:
                            d = G.Brep.CreateBooleanDifference([sk[0]], list(hv), TOL)
                            if d and len(d) == 1 and d[0].IsSolid:
                                res = d[0]; kind = "hollow"
            if res is None:
                st["FAILED"] += 1; log("%s FAILED piece %s course %d" % (rt, o.Id, k)); continue
            gi = o.Attributes.GroupCount and o.Attributes.GetGroupList()[0] or doc.Groups.Add()
            if not o.Attributes.GroupCount:
                a0 = o.Attributes.Duplicate(); a0.AddToGroup(gi); doc.Objects.ModifyAttributes(o.Id, a0, True)
            at = Rhino.DocObjects.ObjectAttributes(); at.LayerIndex = bl; at.AddToGroup(gi)
            at.Name = "growth band %.3f m (%s)" % (g, kind); at.SetUserString("band_for_piece", str(o.Id)); at.SetUserString("course", str(k))
            doc.Objects.AddBrep(res, at)
            st[kind] += 1; kd += 1
            if kd % 50 == 0:
                log("%s %d %s" % (rt, kd, dict(st)))
    doc.ClearUndoRecords(True)
    log("%s DONE %s" % (rt, dict(st)))
    return dict(st)
