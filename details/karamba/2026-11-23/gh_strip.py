# New continuous ring footing (Gonzalo 2026-11-23: replace the pads with a continuous foundation; "does not have to be
# the old one"): one closed smooth strip under all columns, following the column line, columns centred on it,
# base -0.80, top -0.30, width 1.20 m (15x10) / 0.85 m (10x10), the width the tipping check needs.
# GH: column centres (internalised, at -0.80) -> Interpolate (periodic) -> Offset Curve +/- B/2 -> Boundary Surfaces
# -> Extrude 0.5 up. Baked to new test layers; the pads stay visible for comparison.
import json, System, Rhino, Grasshopper
from Grasshopper.Kernel import GH_Document, GH_DocumentIO
from Grasshopper.Kernel.Types import GH_Point, GH_Number, GH_Boolean, GH_Integer
from Grasshopper.Kernel.Parameters import Param_Point, Param_Number, Param_Boolean, Param_Integer
G = Rhino.Geometry
rd = Rhino.RhinoDoc.ActiveDoc
HERE = r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\details\karamba\2026-11-23"
GHPATH = r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\polyframe2\strip-footing-2026-11-23.gh"
WIDTH = {"15x10": 1.20, "10x10": 0.85}
LAY = json.load(open(HERE + r"\pads_layout.json"))
srv = Grasshopper.Instances.ComponentServer
CATS = {"Interpolate": "Curve", "Offset Curve": "Curve", "Boundary Surfaces": "Surface", "Extrude": "Surface", "Unit Z": "Vector"}
doc = GH_Document()


def comp(name, x, y):
    px = [p for p in srv.ObjectProxies if p.Desc.Name == name and p.Desc.Category == CATS[name] and not p.Obsolete]
    assert px, name
    c = srv.EmitObject(px[0].Guid); c.CreateAttributes(); c.Attributes.Pivot = System.Drawing.PointF(x, y); doc.AddObject(c, False); return c


def prm(cls, wrap, nick, vals, x, y):
    p = cls(); p.NickName = nick; p.CreateAttributes(); p.Attributes.Pivot = System.Drawing.PointF(x, y)
    for v in vals: p.PersistentData.Append(wrap(v))
    doc.AddObject(p, False); return p


def inp(c, name):
    return [q for q in c.Params.Input if q.Name == name or q.NickName == name][0]


outs = {}
for k, roof in enumerate(("15x10", "10x10")):
    y0 = 60 + 260 * k; B = WIDTH[roof]
    pts = [G.Point3d(c["cx"], c["cy"], -0.8) for c in LAY[roof]["cols"]]          # in order around the plan
    ip = comp("Interpolate", 300, y0)
    ip.Params.Input[0].AddSource(prm(Param_Point, GH_Point, "%s column centres at -0.80" % roof, pts, 60, y0))
    ip.Params.Input[1].AddSource(prm(Param_Integer, GH_Integer, "%s degree 3" % roof, [3], 160, y0 + 30))
    ip.Params.Input[2].AddSource(prm(Param_Boolean, GH_Boolean, "%s periodic" % roof, [True], 160, y0 + 55))
    offs = []
    for j, s in enumerate((1, -1)):
        oc = comp("Offset Curve", 500, y0 + 90 * j)
        oc.Params.Input[0].AddSource(ip.Params.Output[0])
        oc.Params.Input[1].AddSource(prm(Param_Number, GH_Number, "%s offset %+.3f" % (roof, s * B / 2), [s * B / 2], 380, y0 + 40 + 90 * j))
        offs.append(oc)
    bs = comp("Boundary Surfaces", 700, y0)
    for oc in offs: bs.Params.Input[0].AddSource(oc.Params.Output[0])
    uz = comp("Unit Z", 700, y0 + 90)
    uz.Params.Input[0].AddSource(prm(Param_Number, GH_Number, "%s depth 0.50" % roof, [0.5], 600, y0 + 110))
    ex = comp("Extrude", 880, y0); ex.Params.Input[0].AddSource(bs.Params.Output[0]); ex.Params.Input[1].AddSource(uz.Params.Output[0])
    outs[roof] = (ex, ip)

for od in list(Grasshopper.Instances.DocumentServer):
    if od.FilePath == GHPATH: Grasshopper.Instances.DocumentServer.RemoveDocument(od)
Grasshopper.Instances.DocumentServer.AddDocument(doc)
doc.Enabled = True; doc.NewSolution(True); doc.PreviewMode = Grasshopper.Kernel.GH_PreviewMode.Disabled
doc.FilePath = GHPATH; GH_DocumentIO(doc).Save()

rep = {}
for roof, (ex, ip) in outs.items():
    B = WIDTH[roof]
    nm = "ring footing %d x 50 along the column line, base -0.80 (test)" % round(B * 100)
    parent = rd.Layers.FindByFullPath("%s complete v3e-ring-step" % roof, -1)
    full = "%s complete v3e-ring-step::%s" % (roof, nm)
    for l in list(rd.Layers):                                    # clear earlier test layers of this script
        if not l.IsDeleted and l.FullPath.startswith(roof + " complete v3e-ring-step::") and ("strip footing" in l.Name or "ring footing" in l.Name) and "(test)" in l.Name:
            for ob in rd.Objects.FindByLayer(l) or []: rd.Objects.Delete(ob, True)
            rd.Layers.Delete(l.Index, True)
    lay = Rhino.DocObjects.Layer(); lay.Name = nm; lay.ParentLayerId = rd.Layers[parent].Id; lay.Color = System.Drawing.Color.FromArgb(150, 110, 60)
    li = rd.Layers.Add(lay)
    att = Rhino.DocObjects.ObjectAttributes(); att.LayerIndex = li
    crv = list(ip.Params.Output[0].VolatileData.AllData(True))[0].Value
    for gg in ex.Params.Output[0].VolatileData.AllData(True):
        b = gg.Value
        rd.Objects.AddBrep(b, att)
        rep[roof] = dict(solid=b.IsSolid, valid=b.IsValid, volume_m3=round(b.GetVolume(), 2), column_line_m=round(crv.GetLength(), 2))
rd.Views.Redraw()
json.dump(rep, open(HERE + r"\strip_result.json", "w"))
print(rep)
