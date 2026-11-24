# Rib pipes as visible Grasshopper components (2026-11-23). Reads the existing pipes only to get their input data
# (segment axes, node centres, radii, and the trim planes at the ring top / crown), internalises that data, and lets
# GH components rebuild them: Line + Pipe (flat caps), Sphere, and Solid Difference with a Center Box for the trimmed
# ends. Bakes to '... (GH rebuild, test)' layers and compares every solid with the original (volume + centroid).
import math, json, System, Rhino, Grasshopper
from Grasshopper.Kernel import GH_Document, GH_DocumentIO, GH_ParamAccess
from Grasshopper.Kernel.Types import GH_Plane, GH_Number, GH_Point, GH_Integer
from Grasshopper.Kernel.Parameters import Param_Plane, Param_Number, Param_Point, Param_Integer
G = Rhino.Geometry
rd = Rhino.RhinoDoc.ActiveDoc
GHPATH = r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\polyframe2\rib-pipes-gh-2026-11-23.gh"
srv = Grasshopper.Instances.ComponentServer
doc = GH_Document()


def outward(f, p):
    ok, u, v = f.ClosestPoint(p); n = f.NormalAt(u, v)
    if f.OrientationIsReversed: n.Reverse()
    return n


def analyse(b):
    """returns ('sphere', centre, r, cut) or ('seg', a, b, r, cut); cut = Plane at the trim face, normal out of the solid"""
    sph = cyl = None; planes = []
    for f in b.Faces:
        s = f.UnderlyingSurface()
        ok, sp = s.TryGetSphere(0.001)
        if ok: sph = sp; continue
        ok, cy = s.TryGetCylinder(0.001)
        if ok: cyl = (cy, f); continue
        ok, pl = s.TryGetPlane(0.001)
        if ok:
            amp = G.AreaMassProperties.Compute(f.DuplicateFace(False)); c = amp.Centroid
            planes.append(G.Plane(c, outward(f, c)))
    if sph is not None:
        cut = planes[0] if planes else None
        return ("sphere", sph.Center, sph.Radius, cut)
    cy, f = cyl; ax = G.Vector3d(cy.Axis); ax.Unitize(); r = cy.Radius
    caps = [p for p in planes if abs(abs(p.Normal * ax) - 1) < 1e-4]
    cuts = [p for p in planes if abs(abs(p.Normal * ax) - 1) >= 1e-4]
    ts = [(G.Point3d(v.Location) - cy.Center) * ax for v in b.Vertices]
    if len(caps) == 2:
        a, e = caps[0].Origin, caps[1].Origin
        a = cy.Center + ax * ((a - cy.Center) * ax); e = cy.Center + ax * ((e - cy.Center) * ax)
        return ("seg", a, e, r, cuts[0] if cuts else None)
    c0 = caps[0].Origin; t0 = (c0 - cy.Center) * ax
    tfar = max(ts) if abs(max(ts) - t0) > abs(min(ts) - t0) else min(ts)
    a = cy.Center + ax * t0
    e = cy.Center + ax * (tfar + (2 * r if tfar > t0 else -2 * r))      # run the pipe past the trim plane; the box cuts it back
    return ("seg", a, e, r, cuts[0])


CATS = {"Pipe": "Surface", "Sphere": "Surface", "Line": "Curve", "Center Box": "Surface", "Solid Difference": "Intersect"}


def comp(name, x, y):
    px = [p for p in srv.ObjectProxies if p.Desc.Name == name and p.Desc.Category == CATS[name] and not p.Obsolete]
    assert len(px) == 1, (name, [(p.Desc.Category, p.Desc.SubCategory) for p in srv.ObjectProxies if p.Desc.Name == name])
    c = srv.EmitObject(px[0].Guid)
    c.CreateAttributes(); c.Attributes.Pivot = System.Drawing.PointF(x, y); doc.AddObject(c, False); return c


def param(cls, wrap, nick, vals, x, y, graft=False):
    p = cls(); p.NickName = nick; p.CreateAttributes(); p.Attributes.Pivot = System.Drawing.PointF(x, y)
    for v in vals: p.PersistentData.Append(wrap(v))
    doc.AddObject(p, False); return p


def graft(inp):
    inp.DataMapping = Grasshopper.Kernel.GH_DataMapping.Graft


groups = {}
row = 0
for roof in ("15x10", "10x10"):
    for ln in ("rib pipes - cast core", "rib pipes - printed tube"):
        full = "%s complete v3e-ring-step::%s" % (roof, ln)
        objs = rd.Objects.FindByLayer(rd.Layers[rd.Layers.FindByFullPath(full, -1)])
        S, Sc, L, Lc = [], [], [], []
        orig = []
        for o in objs:
            b = o.Geometry.ToBrep() if isinstance(o.Geometry, G.Extrusion) else o.Geometry
            vm = G.VolumeMassProperties.Compute(b); orig.append((vm.Volume, vm.Centroid))
            k = analyse(b)
            if k[0] == "sphere":
                (Sc if k[3] else S).append(k)
            else:
                (Lc if k[4] else L).append(k)
        y0 = 60 + row * 420; row += 1
        tag = "%s %s" % (roof, ln.replace("rib pipes - ", ""))
        outs = []
        # whole node balls
        sp = comp("Sphere", 420, y0)
        sp.Params.Input[0].AddSource(param(Param_Plane, GH_Plane, tag + " ball centres", [G.Plane(k[1], G.Vector3d.ZAxis) for k in S], 60, y0))
        sp.Params.Input[1].AddSource(param(Param_Number, GH_Number, tag + " ball r", [k[2] for k in S], 240, y0 + 20))
        outs.append(sp.Params.Output[0])
        # straight segments
        ln_ = comp("Line", 420, y0 + 80)
        ln_.Params.Input[0].AddSource(param(Param_Point, GH_Point, tag + " seg start", [k[1] for k in L], 60, y0 + 70))
        ln_.Params.Input[1].AddSource(param(Param_Point, GH_Point, tag + " seg end", [k[2] for k in L], 60, y0 + 100))
        pp = comp("Pipe", 600, y0 + 80)
        pp.Params.Input[0].AddSource(ln_.Params.Output[0])
        pp.Params.Input[1].AddSource(param(Param_Number, GH_Number, tag + " seg r", [k[3] for k in L], 420, y0 + 130))
        pp.Params.Input[2].AddSource(param(Param_Integer, GH_Integer, tag + " caps flat", [1], 420, y0 + 160))
        outs.append(pp.Params.Output[0])
        # trimmed segments (ring top / crown): pipe past the plane, minus a box on the far side of the trim plane
        ln2 = comp("Line", 420, y0 + 220)
        ln2.Params.Input[0].AddSource(param(Param_Point, GH_Point, tag + " trimmed start", [k[1] for k in Lc], 60, y0 + 210))
        ln2.Params.Input[1].AddSource(param(Param_Point, GH_Point, tag + " trimmed end", [k[2] for k in Lc], 60, y0 + 240))
        pp2 = comp("Pipe", 600, y0 + 220)
        pp2.Params.Input[0].AddSource(ln2.Params.Output[0])
        pp2.Params.Input[1].AddSource(param(Param_Number, GH_Number, tag + " trimmed r", [k[3] for k in Lc], 420, y0 + 270))
        pp2.Params.Input[2].AddSource(param(Param_Integer, GH_Integer, tag + " caps flat 2", [1], 420, y0 + 300))
        # cut balls
        sp2 = comp("Sphere", 600, y0 + 340)
        sp2.Params.Input[0].AddSource(param(Param_Plane, GH_Plane, tag + " cut ball centres", [G.Plane(k[1], G.Vector3d.ZAxis) for k in Sc], 60, y0 + 330))
        sp2.Params.Input[1].AddSource(param(Param_Number, GH_Number, tag + " cut ball r", [k[2] for k in Sc], 240, y0 + 360))
        # cutter boxes: centred 1 m beyond each trim plane, 2 x 2 x 2 m
        for src, cuts, yy, nm in ((pp2, [k[4] for k in Lc], y0 + 220, "trimmed"), (sp2, [k[3] for k in Sc], y0 + 340, "cut ball")):
            pls = []
            for c in cuts:
                pl = G.Plane(c.Origin + c.Normal * 1.0, c.Normal); pls.append(pl)
            bx = comp("Center Box", 800, yy + 40)
            bx.Params.Input[0].AddSource(param(Param_Plane, GH_Plane, tag + " %s cutter planes" % nm, pls, 600, yy + 60))
            for i in (1, 2, 3):
                bx.Params.Input[i].AddSource(param(Param_Number, GH_Number, tag + " %s box %s" % (nm, "XYZ"[i - 1]), [1.0], 640, yy + 60 + 25 * i))
            sd = comp("Solid Difference", 1000, yy)
            sd.Params.Input[0].AddSource(src.Params.Output[0] if src is pp2 else src.Params.Output[0]); graft(sd.Params.Input[0])
            sd.Params.Input[1].AddSource(bx.Params.Output[0]); graft(sd.Params.Input[1])
            outs.append(sd.Params.Output[0])
        groups[(roof, ln)] = (outs, orig, (len(S), len(L), len(Lc), len(Sc)))

for od in list(Grasshopper.Instances.DocumentServer):
    if od.FilePath == GHPATH: Grasshopper.Instances.DocumentServer.RemoveDocument(od)
Grasshopper.Instances.DocumentServer.AddDocument(doc)
doc.Enabled = True
doc.NewSolution(True)
doc.PreviewMode = Grasshopper.Kernel.GH_PreviewMode.Disabled
doc.FilePath = GHPATH; GH_DocumentIO(doc).Save()

report = {}
for (roof, ln), (outs, orig, counts) in groups.items():
    full = "%s complete v3e-ring-step::%s (GH rebuild, test)" % (roof, ln)
    parent = rd.Layers.FindByFullPath("%s complete v3e-ring-step" % roof, -1)
    li = rd.Layers.FindByFullPath(full, -1)
    if li < 0:
        lay = Rhino.DocObjects.Layer(); lay.Name = ln + " (GH rebuild, test)"; lay.ParentLayerId = rd.Layers[parent].Id
        lay.Color = System.Drawing.Color.FromArgb(200, 60, 60); li = rd.Layers.Add(lay)
    else:
        for o in rd.Objects.FindByLayer(rd.Layers[li]) or []: rd.Objects.Delete(o, True)
    att = Rhino.DocObjects.ObjectAttributes(); att.LayerIndex = li
    new = []
    for op in outs:
        for gg in op.VolatileData.AllData(True):
            b = gg.Value
            if isinstance(b, G.Box): b = b.ToBrep()
            rd.Objects.AddBrep(b, att)
            vm = G.VolumeMassProperties.Compute(b); new.append((vm.Volume, vm.Centroid, b.IsSolid and b.IsValid))
    # match every original to the nearest new solid
    worst_dv = 0; worst_dc = 0; unmatched = 0; used = set()
    for v, c in orig:
        best = min(range(len(new)), key=lambda i: new[i][1].DistanceTo(c)) if new else None
        if best is None: unmatched += 1; continue
        used.add(best)
        worst_dc = max(worst_dc, new[best][1].DistanceTo(c)); worst_dv = max(worst_dv, abs(new[best][0] - v) / v)
    report["%s | %s" % (roof, ln)] = dict(orig=len(orig), new=len(new), counts=counts, distinct_matches=len(used),
                                          worst_centroid_mm=round(worst_dc * 1000, 3), worst_volume_pct=round(worst_dv * 100, 4),
                                          invalid=sum(1 for n in new if not n[2]))
rd.Views.Redraw()
print(json.dumps(report, indent=1))
