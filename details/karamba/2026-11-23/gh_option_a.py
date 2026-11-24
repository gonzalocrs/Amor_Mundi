# Places the option-A canvas in the private Rhino (runs inside Rhino, Python 3). It only places components and wires
# and internalises the plane data from pads_layout.json; Center Box and Solid Union do the work. Then the outputs are
# baked to new layers (old columns and strip footing are left as they are).
import json, math, System, Rhino, Grasshopper
from Grasshopper.Kernel import GH_Document, GH_DocumentIO
from Grasshopper.Kernel.Types import GH_Plane, GH_Number
from Grasshopper.Kernel.Parameters import Param_Plane, Param_Number
G = Rhino.Geometry
HERE = r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\details\karamba\2026-11-23"
GHPATH = r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\polyframe2\option-A-columns-pads-2026-11-23.gh"
L = json.load(open(HERE + r"\pads_layout.json"))
srv = Grasshopper.Instances.ComponentServer
doc = GH_Document()

def comp(name, x, y):
    c = srv.EmitObject(srv.FindObjectByName(name, True, True).Guid)
    c.CreateAttributes(); c.Attributes.Pivot = System.Drawing.PointF(x, y); doc.AddObject(c, False); return c

def planes(nick, pls, x, y):
    p = Param_Plane(); p.NickName = nick; p.CreateAttributes(); p.Attributes.Pivot = System.Drawing.PointF(x, y)
    for pl in pls: p.PersistentData.Append(GH_Plane(pl))
    doc.AddObject(p, False); return p

def num(nick, v, x, y):
    p = Param_Number(); p.NickName = nick; p.CreateAttributes(); p.Attributes.Pivot = System.Drawing.PointF(x, y)
    p.PersistentData.Append(GH_Number(v)); doc.AddObject(p, False); return p

def plane_at(cx, cy, z, ang):
    t = math.radians(ang)
    return G.Plane(G.Point3d(cx, cy, z), G.Vector3d(math.cos(t), math.sin(t), 0), G.Vector3d(-math.sin(t), math.cos(t), 0))

outs = {}
for k, (roof, padsz) in enumerate((("15x10", 1.8), ("10x10", 1.4))):
    y0 = 60 + 260 * k
    R = L[roof]; h = R["cols"][0]["h"]
    # columns: -0.30 (in the pad) to +2.00 (underside of the ring step), centred under the step
    cp = planes("%s column planes (z 0.85)" % roof, [plane_at(c["cx"], c["cy"], 0.85, c["ang"]) for c in R["cols"]], 60, y0)
    cb = comp("Center Box", 360, y0)
    cb.Params.Input[0].AddSource(cp)
    for i, v in ((1, h), (2, h), (3, 1.15)):
        cb.Params.Input[i].AddSource(num("%s col %s" % (roof, "XYZ"[i - 1]), v, 200, y0 + 30 * i))
    # pads: base -0.80, top -0.30, one per column; Solid Union merges only the ones that overlap (corner pairs)
    pp = planes("%s pad planes (z -0.55)" % roof, [plane_at(c["cx"], c["cy"], -0.55, c["ang"]) for c in R["cols"]], 60, y0 + 130)
    pb = comp("Center Box", 360, y0 + 130)
    pb.Params.Input[0].AddSource(pp)
    for i, v in ((1, padsz / 2), (2, padsz / 2), (3, 0.25)):
        pb.Params.Input[i].AddSource(num("%s pad %s" % (roof, "XYZ"[i - 1]), v, 200, y0 + 130 + 30 * i))
    su = comp("Solid Union", 560, y0 + 130)
    su.Params.Input[0].AddSource(pb.Params.Output[0])
    outs[roof] = (cb, su)

Grasshopper.Instances.DocumentServer.AddDocument(doc)
doc.Enabled = True
doc.NewSolution(True)
doc.FilePath = GHPATH; GH_DocumentIO(doc).Save()
try:
    Grasshopper.Instances.ActiveCanvas.Document = doc
except Exception:
    pass

rd = Rhino.RhinoDoc.ActiveDoc
LAYERS = {"15x10": ("option A - columns 36x36 (20, test)", "option A - pad footings 1.8x1.8x0.5, base -0.80, corner pairs as one (test)"),
          "10x10": ("option A - columns 30x30 (16, test)", "option A - pad footings 1.4x1.4x0.5, base -0.80 (test)")}
report = []
for roof, (cb, su) in outs.items():
    parent = rd.Layers.FindByFullPath("%s complete v3e-ring-step" % roof, -1)
    for nm, src, col in ((LAYERS[roof][0], cb.Params.Output[0], System.Drawing.Color.FromArgb(90, 90, 90)),
                         (LAYERS[roof][1], su.Params.Output[0], System.Drawing.Color.FromArgb(150, 110, 60))):
        full = "%s complete v3e-ring-step::%s" % (roof, nm)
        li = rd.Layers.FindByFullPath(full, -1)
        if li < 0:
            lay = Rhino.DocObjects.Layer(); lay.Name = nm; lay.ParentLayerId = rd.Layers[parent].Id; lay.Color = col
            li = rd.Layers.Add(lay)
        else:
            for o in rd.Objects.FindByLayer(rd.Layers[li]) or []: rd.Objects.Delete(o, True)
        att = Rhino.DocObjects.ObjectAttributes(); att.LayerIndex = li
        n = 0; vol = 0
        for g in src.VolatileData.AllData(True):
            b = g.Value if hasattr(g, "Value") else g
            if isinstance(b, G.Box): b = b.ToBrep()
            rd.Objects.AddBrep(b, att); n += 1; vol += b.GetVolume()
        report.append("%s: %d solids, %.2f m3" % (full, n, vol))
rd.Views.Redraw()
print("\n".join(report))
