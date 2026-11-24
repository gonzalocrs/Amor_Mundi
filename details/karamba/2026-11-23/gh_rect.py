# Rectangular strip footing (Gonzalo 2026-11-23: "it should be rectangular", "no one is going to excavate that"):
# four straight strips on the side column lines, square outer corners, a plain square block filling each corner so the
# diagonal corner column stands fully on footing (>= 20 cm margin). 15x10 1.20 m wide, 10x10 0.85 m, -0.80..-0.30.
# GH: outer rectangle + inner outline (internalised polylines) -> Boundary Surfaces -> Extrude 0.5. New test layers.
import json, math, System, Rhino, Grasshopper
from Grasshopper.Kernel import GH_Document, GH_DocumentIO
from Grasshopper.Kernel.Types import GH_Curve, GH_Number
from Grasshopper.Kernel.Parameters import Param_Curve, Param_Number
G = Rhino.Geometry
rd = Rhino.RhinoDoc.ActiveDoc
HERE = r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\details\karamba\2026-11-23"
GHPATH = r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\polyframe2\rect-footing-2026-11-23.gh"
WIDTH = {"15x10": 1.20, "10x10": 0.85}
BLOCK = {"15x10": 0.60, "10x10": 0.50}          # corner block reaches this far past the corner column centre
LAY = json.load(open(HERE + r"\pads_layout.json"))
CEN = {"15x10": (85.0, 0.0), "10x10": (85.0, -20.0)}
srv = Grasshopper.Instances.ComponentServer
CATS = {"Boundary Surfaces": "Surface", "Extrude": "Surface", "Unit Z": "Vector"}
doc = GH_Document()


def comp(name, x, y):
    px = [p for p in srv.ObjectProxies if p.Desc.Name == name and p.Desc.Category == CATS[name] and not p.Obsolete]
    c = srv.EmitObject(px[0].Guid); c.CreateAttributes(); c.Attributes.Pivot = System.Drawing.PointF(x, y); doc.AddObject(c, False); return c


def prm(cls, wrap, nick, vals, x, y):
    p = cls(); p.NickName = nick; p.CreateAttributes(); p.Attributes.Pivot = System.Drawing.PointF(x, y)
    for v in vals: p.PersistentData.Append(wrap(v))
    doc.AddObject(p, False); return p


def geometry(roof):
    cx, cy = CEN[roof]; B = WIDTH[roof]; m = BLOCK[roof]
    cols = [(c["cx"] - cx, c["cy"] - cy) for c in LAY[roof]["cols"]]
    xl = max(abs(x) for x, y in cols if abs(y) < 0.01)          # short-side column line (columns on the axis)
    yl = max(abs(y) for x, y in cols if abs(x) < 0.01)          # long-side column line
    corner = [p for p in cols if abs(p[0]) > 0.5 and abs(p[1]) > 0.5]
    cc = max(corner, key=lambda p: math.hypot(p[0] / xl, p[1] / yl))     # the diagonal corner column
    dxb, yb = abs(cc[0]) - m, abs(cc[1]) - m
    dxo, yo = xl + B / 2, yl + B / 2; dxf, yf = xl - B / 2, yl - B / 2
    inner = [(-dxb, -yf), (dxb, -yf), (dxb, -yb), (dxf, -yb), (dxf, yb), (dxb, yb), (dxb, yf), (-dxb, yf), (-dxb, yb), (-dxf, yb), (-dxf, -yb), (-dxb, -yb), (-dxb, -yf)]
    outer = [(-dxo, -yo), (dxo, -yo), (dxo, yo), (-dxo, yo), (-dxo, -yo)]
    pl = lambda pts: G.Polyline([G.Point3d(cx + x, cy + y, -0.8) for x, y in pts]).ToNurbsCurve()
    return pl(outer), pl(inner), dict(xl=xl, yl=yl, corner_col=cc, outer_m=(round(2 * dxo, 3), round(2 * yo, 3)), block_m=(round(dxo - dxb, 3), round(yo - yb, 3)))


outs = {}; meta = {}
for k, roof in enumerate(("15x10", "10x10")):
    y0 = 60 + 220 * k
    o, i, info = geometry(roof); meta[roof] = info
    src = prm(Param_Curve, lambda c: GH_Curve(c), "%s footing outline at -0.80 (outer rectangle, inner edge with corner blocks)" % roof, [o, i], 60, y0)
    bs = comp("Boundary Surfaces", 320, y0); bs.Params.Input[0].AddSource(src)
    uz = comp("Unit Z", 320, y0 + 80); uz.Params.Input[0].AddSource(prm(Param_Number, GH_Number, "%s depth 0.50" % roof, [0.5], 200, y0 + 100))
    ex = comp("Extrude", 500, y0); ex.Params.Input[0].AddSource(bs.Params.Output[0]); ex.Params.Input[1].AddSource(uz.Params.Output[0])
    outs[roof] = ex

for od in list(Grasshopper.Instances.DocumentServer):
    if od.FilePath == GHPATH: Grasshopper.Instances.DocumentServer.RemoveDocument(od)
Grasshopper.Instances.DocumentServer.AddDocument(doc)
doc.Enabled = True; doc.NewSolution(True); doc.PreviewMode = Grasshopper.Kernel.GH_PreviewMode.Disabled
doc.FilePath = GHPATH; GH_DocumentIO(doc).Save()

for roof, ex in outs.items():
    B = WIDTH[roof]
    nm = "rectangular strip footing %d x 50, square corner blocks, base -0.80 (test)" % round(B * 100)
    for l in list(rd.Layers):
        if not l.IsDeleted and l.FullPath.startswith(roof + " complete v3e-ring-step::rectangular strip footing"):
            for ob in rd.Objects.FindByLayer(l) or []: rd.Objects.Delete(ob, True)
            rd.Layers.Delete(l.Index, True)
    parent = rd.Layers.FindByFullPath("%s complete v3e-ring-step" % roof, -1)
    lay = Rhino.DocObjects.Layer(); lay.Name = nm; lay.ParentLayerId = rd.Layers[parent].Id; lay.Color = System.Drawing.Color.FromArgb(150, 110, 60)
    li = rd.Layers.Add(lay); att = Rhino.DocObjects.ObjectAttributes(); att.LayerIndex = li
    bs = [g.Value for g in ex.Params.Output[0].VolatileData.AllData(True)]
    for b in bs: rd.Objects.AddBrep(b, att)
    b = bs[0]
    plan = G.Curve.JoinCurves(G.Brep.CreateContourCurves(b, G.Plane(G.Point3d(0, 0, -0.55), G.Vector3d.ZAxis)))
    cols = rd.Objects.FindByLayer(rd.Layers[rd.Layers.FindByFullPath(roof + " complete v3e-ring-step::" + ("columns 36x36 (20)" if roof == "15x10" else "columns 30x30 (16)"), -1)])
    inside = tot = 0; mind = 9
    for ob in cols:
        for v in ob.Geometry.Vertices:
            p = v.Location
            if abs(p.Z + 0.3) < 1e-3:
                tot += 1; q = G.Point3d(p.X, p.Y, -0.55)
                inside += b.IsPointInside(q, 0.001, True)
                for c in plan:
                    ok, t = c.ClosestPoint(q); mind = min(mind, c.PointAt(t).DistanceTo(q))
    # column offset from its strip centreline (for the tipping check)
    cx, cy = CEN[roof]; offs = []
    for c in LAY[roof]["cols"]:
        x, y = c["cx"] - cx, c["cy"] - cy
        if abs(abs(x) - meta[roof]["corner_col"][0]) < 1e-3 and abs(abs(y) - abs(meta[roof]["corner_col"][1])) < 1e-3:
            offs.append(0.0); continue          # corner columns stand in the solid block
        offs.append(min(abs(abs(x) - meta[roof]["xl"]), abs(abs(y) - meta[roof]["yl"])))
    meta[roof].update(solids=len(bs), solid=b.IsSolid, valid=b.IsValid, volume_m3=round(b.GetVolume(), 2), feet_inside="%d/%d" % (inside, tot),
                      min_plan_edge_m=round(mind, 3), col_offsets=[round(v, 3) for v in offs], centreline_m=round(2 * (2 * meta[roof]["xl"] + 2 * meta[roof]["yl"]) / 2, 2))
rd.Views.Redraw()
json.dump(meta, open(HERE + r"\rect_result.json", "w"))
print(json.dumps(meta))
