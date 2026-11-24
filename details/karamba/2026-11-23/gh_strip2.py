# Ring footing v2 (2026-11-23): the centreline is the base ring step's own smooth outline (outer edge at +2.20,
# projected to -0.80) offset inward by the mean distance to the column centres, so it follows the ring and has no
# wobble. GH: ring outline (internalised) -> two Offset Curve (inner / outer edge) -> Boundary Surfaces -> Extrude 0.5.
import json, System, Rhino, Grasshopper
from Grasshopper.Kernel import GH_Document, GH_DocumentIO
from Grasshopper.Kernel.Types import GH_Curve, GH_Number
from Grasshopper.Kernel.Parameters import Param_Curve, Param_Number
G = Rhino.Geometry
rd = Rhino.RhinoDoc.ActiveDoc
HERE = r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\details\karamba\2026-11-23"
GHPATH = r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\polyframe2\strip-footing-2026-11-23.gh"
WIDTH = {"15x10": 1.20, "10x10": 0.85}
LAY = json.load(open(HERE + r"\pads_layout.json"))
srv = Grasshopper.Instances.ComponentServer
CATS = {"Offset Curve": "Curve", "Boundary Surfaces": "Surface", "Extrude": "Surface", "Unit Z": "Vector"}
doc = GH_Document()


def comp(name, x, y):
    px = [p for p in srv.ObjectProxies if p.Desc.Name == name and p.Desc.Category == CATS[name] and not p.Obsolete]
    c = srv.EmitObject(px[0].Guid); c.CreateAttributes(); c.Attributes.Pivot = System.Drawing.PointF(x, y); doc.AddObject(c, False); return c


def prm(cls, wrap, nick, vals, x, y):
    p = cls(); p.NickName = nick; p.CreateAttributes(); p.Attributes.Pivot = System.Drawing.PointF(x, y)
    for v in vals: p.PersistentData.Append(wrap(v))
    doc.AddObject(p, False); return p


def ring_outline(roof):
    objs = rd.Objects.FindByLayer(rd.Layers[rd.Layers.FindByFullPath(roof + " complete v3e-ring-step::base ring step - printed U formwork (3 cm)", -1)])
    crvs = []
    for o in objs:
        crvs += list(G.Brep.CreateContourCurves(o.Geometry, G.Plane(G.Point3d(0, 0, 2.2), G.Vector3d.ZAxis)))
    J = sorted(G.Curve.JoinCurves(crvs, 0.002), key=lambda c: -G.AreaMassProperties.Compute(c).Area)
    c = J[0].DuplicateCurve(); c.Translate(G.Vector3d(0, 0, -3.0))          # +2.20 -> -0.80
    return c


meta = {}
outs = {}
for k, roof in enumerate(("15x10", "10x10")):
    y0 = 60 + 240 * k; B = WIDTH[roof]
    rc = ring_outline(roof)
    ds = []
    for col in LAY[roof]["cols"]:
        p = G.Point3d(col["cx"], col["cy"], -0.8); ok, t = rc.ClosestPoint(p); ds.append(rc.PointAt(t).DistanceTo(p))
    m = sum(ds) / len(ds)
    # sign of an inward offset for this curve direction (GH Offset Curve: + to the left in the XY plane)
    test = rc.Offset(G.Plane.WorldXY, 0.5, 0.001, G.CurveOffsetCornerStyle.Sharp)[0]
    inward = 1 if G.AreaMassProperties.Compute(test).Area < G.AreaMassProperties.Compute(rc).Area else -1
    src = prm(Param_Curve, lambda c: GH_Curve(c), "%s base ring outline (outer edge) at -0.80" % roof, [rc], 60, y0)
    offs = []
    for j, dd in enumerate((m - B / 2, m + B / 2)):
        oc = comp("Offset Curve", 420, y0 + 90 * j)
        oc.Params.Input[0].AddSource(src)
        oc.Params.Input[1].AddSource(prm(Param_Number, GH_Number, "%s offset %.3f in (%s edge)" % (roof, dd, "outer" if j == 0 else "inner"), [inward * dd], 260, y0 + 40 + 90 * j))
        offs.append(oc)
    bs = comp("Boundary Surfaces", 620, y0)
    for oc in offs: bs.Params.Input[0].AddSource(oc.Params.Output[0])
    uz = comp("Unit Z", 620, y0 + 90); uz.Params.Input[0].AddSource(prm(Param_Number, GH_Number, "%s depth 0.50" % roof, [0.5], 520, y0 + 110))
    ex = comp("Extrude", 800, y0); ex.Params.Input[0].AddSource(bs.Params.Output[0]); ex.Params.Input[1].AddSource(uz.Params.Output[0])
    outs[roof] = ex
    meta[roof] = dict(offset_m=round(m, 3), col_dev_m=round(max(abs(x - m) for x in ds), 3))

for od in list(Grasshopper.Instances.DocumentServer):
    if od.FilePath == GHPATH: Grasshopper.Instances.DocumentServer.RemoveDocument(od)
Grasshopper.Instances.DocumentServer.AddDocument(doc)
doc.Enabled = True; doc.NewSolution(True); doc.PreviewMode = Grasshopper.Kernel.GH_PreviewMode.Disabled
doc.FilePath = GHPATH; GH_DocumentIO(doc).Save()

for roof, ex in outs.items():
    B = WIDTH[roof]
    li = [l.Index for l in rd.Layers if not l.IsDeleted and l.FullPath.startswith(roof + " complete v3e-ring-step::ring footing")][0]
    for ob in rd.Objects.FindByLayer(rd.Layers[li]) or []: rd.Objects.Delete(ob, True)
    att = Rhino.DocObjects.ObjectAttributes(); att.LayerIndex = li
    bs = [g.Value for g in ex.Params.Output[0].VolatileData.AllData(True)]
    for b in bs: rd.Objects.AddBrep(b, att)
    b = bs[0]
    # feet inside: min distance from each column foot corner to the strip side faces
    cols = rd.Objects.FindByLayer(rd.Layers[rd.Layers.FindByFullPath(roof + " complete v3e-ring-step::" + ("columns 36x36 (20)" if roof == "15x10" else "columns 30x30 (16)"), -1)])
    mind = 9; inside = 0; tot = 0
    for o in cols:
        for v in o.Geometry.Vertices:
            p = v.Location
            if abs(p.Z + 0.3) < 1e-3:
                tot += 1; q = G.Point3d(p.X, p.Y, -0.55)
                inside += b.IsPointInside(q, 0.001, True)
                mind = min(mind, b.ClosestPoint(q).DistanceTo(q))
    meta[roof].update(solids=len(bs), solid=b.IsSolid, valid=b.IsValid, volume_m3=round(b.GetVolume(), 2), feet_inside="%d/%d" % (inside, tot), min_edge_m=round(mind, 3),
                      centreline_m=round(G.AreaMassProperties.Compute(b).Area / 2 / 0 if False else b.GetVolume() / (B * 0.5), 2))
rd.Views.Redraw()
json.dump(meta, open(HERE + r"\strip_result.json", "w"))
print(meta)
