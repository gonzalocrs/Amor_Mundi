"""Karamba-model renders from Karamba's own BeamView (second pass, 2026-11-23/24).
For each roof the 2 m Karamba canvas is opened in Grasshopper; a ModelView (load case from a panel, view selection
= every element group except printed courses and fins) feeds the BeamView, which is set to 'Axial Stress' coloured
cross sections. Karamba colours the meshes and scales its own legend to the actual min/max of the case shown.
The coloured BeamView mesh is baked to a visible layer 'karamba render <roof> <case>' with the footing in light grey,
then captured in a two-point perspective from the south-west (horizontal view direction, eye just above the ring),
cropped to the structure and put on a white 3200 x 2000 sheet. Run inside Rhino (separate Rhino only)."""
import os, json, System, Rhino
import Rhino.Geometry as G
import Grasshopper
from Grasshopper.Kernel.Special import GH_Panel

REPO = r"C:\Users\gonza\Documents\GitHub\Amor_Mundi"
OUT = r"C:\Users\gonza\AppData\Local\Temp\claude\5c622a39c96e3387\d0f96d15-672a-4d67-b7d7-f160f3f4487b\scratchpad\kmodel"
GH = {r: os.path.join(REPO, "polyframe2", "stepped-%s-karamba-2m-2026-11-27.gh" % r) for r in ("15x10", "10x10")}
SHOW = ["rib_bottom", "rib_middle", "rib_top", "ring", "arch", "crown", "column"]
MV_GUID = "9d80a84e-fd16-4443-bacb-36997a977226"
F = System.Reflection.BindingFlags
FL = F.Instance | F.Public | F.NonPublic
W, H = 3200, 2000
DIST, CAP = 26.0, 6400                               # camera distance from the plan centre (m), square capture size (px)


def canvas(roof):
    gh = Rhino.RhinoApp.GetPlugInObject("Grasshopper")
    d = Grasshopper.Instances.ActiveCanvas.Document if Grasshopper.Instances.ActiveCanvas else None
    if d is None or not (d.FilePath or "").lower().endswith(os.path.basename(GH[roof]).lower()):
        gh.DisableSolver(); gh.OpenDocument(GH[roof]); gh.EnableSolver()
        d = Grasshopper.Instances.ActiveCanvas.Document
    return d


def panel(d, name, text, pivot):
    p = [o for o in d.Objects if isinstance(o, GH_Panel) and o.NickName == name]
    if p:
        p = p[0]
    else:
        p = GH_Panel(); p.CreateAttributes(); p.NickName = name; p.Attributes.Pivot = pivot; d.AddObject(p, False)
    p.UserText = text; p.ExpireSolution(False)
    return p


def setup(d, mode="ColoredCrossSectionStress", show=None):
    """ModelView between Analyze and BeamView, panels for case and view selection, BeamView in axial-stress mode"""
    bv = [o for o in d.Objects if o.GetType().Name == "Component_BeamView"][0]
    mv = [o for o in d.Objects if o.GetType().Name == "Component_ModelView"]
    if mv:
        mv = mv[0]
    else:
        an = bv.Params.Input[0].Sources[0]
        mv = Grasshopper.Instances.ComponentServer.EmitObject(System.Guid(MV_GUID)); mv.CreateAttributes()
        pv = bv.Attributes.Pivot; mv.Attributes.Pivot = System.Drawing.PointF(pv.X - 220, pv.Y); mv.NickName = "ModelView (render case)"
        d.AddObject(mv, False); mv.Params.Input[0].AddSource(an)
        bv.Params.Input[0].RemoveAllSources(); bv.Params.Input[0].AddSource(mv.Params.Output[0])
    pv = mv.Attributes.Pivot
    p1 = panel(d, "render load case", "LONG", System.Drawing.PointF(pv.X - 220, pv.Y - 40))
    old = [o for o in d.Objects if isinstance(o, GH_Panel) and o.NickName.startswith("render elements")]
    p2 = old[0] if old else panel(d, "render elements", "", System.Drawing.PointF(pv.X - 220, pv.Y + 40))
    p2.NickName = "render elements"; p2.UserText = "\n".join(show or SHOW); p2.ExpireSolution(False)
    if mv.Params.Input[1].SourceCount == 0: mv.Params.Input[1].AddSource(p1)
    if mv.Params.Input[3].SourceCount == 0: mv.Params.Input[3].AddSource(p2)
    p2.Properties.Multiline = False                  # one identifier per line = one item each
    db = bv.GetType().GetField("displayButtons", FL).GetValue(bv)
    for b in db:
        if str(b.GetType().GetField("Item2").GetValue(b)) == mode:
            tgt = b.GetType().GetField("Item1").GetValue(b)
    grp = tgt.GetType().BaseType.GetField("parent", FL).GetValue(tgt)
    btns = list(grp.GetType().GetField("_buttons", FL).GetValue(grp))
    for x in btns: x.GetType().GetProperty("Active").SetValue(x, x.Equals(tgt))   # clear the default "Cross section" button
    grp.SetActive([i for i, x in enumerate(btns) if x.Equals(tgt)][0])
    bv.GetType().GetMethod("RenderGroupValueChanged", FL).Invoke(bv, [grp, System.EventArgs.Empty])
    et = bv.Preferences.BeamEntityToDraw.GetType()
    bv.Preferences.BeamEntityToDraw = System.Enum.Parse(et, mode)   # belt and braces on a freshly opened canvas
    bv.ExpireSolution(False)
    for o in d.Objects:                              # only the BeamView preview stays on in the canvas
        if hasattr(o, "Hidden"): o.Hidden = (o is not bv)
    return bv, mv, p1


END_COLOURS = ["254,0,73", "254,53,111", "254,102,146", "254,156,184", "254,205,219", "250,250,253",
               "214,208,244", "174,162,233", "138,120,223", "97,74,212", "66,38,204"]   # Karamba's default gradient


def set_range(d, mv, lo, hi):
    """ModelView: no displacement scaling; result colours over a fixed absolute range [lo, hi] (kN/cm2); values beyond
    the range get the end colours (the out-of-range colours, yellow / lime by default, are replaced by the ends)"""
    t = mv.GetType(); ea = System.EventArgs.Empty
    ds = t.GetField("_scalingFactorDisplacementsSlider", FL).GetValue(mv); ds.Value = 0.0
    t.GetMethod("_dispSlider__valueChanged", FL).Invoke(mv, [ds, ea])
    grp = t.GetField("_resultThresholdsButtonGroup", FL).GetValue(mv)
    btns = list(grp.GetType().GetField("_buttons", FL).GetValue(grp))
    for i, b in enumerate(btns): b.GetType().GetProperty("Active").SetValue(b, i == 1)        # 'absolute value'
    grp.SetActive(1); t.GetMethod("ResultThresholdsButtonGroupValueChanged", FL).Invoke(mv, [grp, ea])
    for nm, v, h in (("_resultsRangeUpperLimitSlider", hi, "ResultsRangeUpperLimitSliderValueChanged"), ("_resultsRangeLowerLimitSlider", lo, "ResultsRangeLowerLimitSliderValueChanged")):
        s = t.GetField(nm, FL).GetValue(mv); s.MinValue = min(s.MinValue, lo, -100.0); s.MaxValue = max(s.MaxValue, hi, 100.0); s.Value = v
        t.GetMethod(h, FL).Invoke(mv, [s, ea])
    rr = mv.Preferences.ResultsRange; rr.AsPercentage = False; rr.LowerLimit = lo; rr.UpperLimit = hi
    pv = mv.Attributes.Pivot
    pc = panel(d, "render colours (out-of-range = end colours)", "\n".join([END_COLOURS[0]] + END_COLOURS + [END_COLOURS[-1]]), System.Drawing.PointF(pv.X - 220, pv.Y + 120))
    pc.Properties.Multiline = False
    if mv.Params.Input[2].SourceCount == 0: mv.Params.Input[2].AddSource(pc)
    mv.ExpireSolution(False)


def layer(doc, name, colour=None):
    i = doc.Layers.FindByFullPath(name, -1)
    if i < 0:
        l = Rhino.DocObjects.Layer(); l.Name = name
        if colour: l.Color = colour
        i = doc.Layers.Add(l)
    else:
        if colour: doc.Layers[i].Color = colour
        for o in doc.Objects.FindByLayer(doc.Layers[i]) or []: doc.Objects.Delete(o, True)
    return i


def render(doc, roof, case, lc, mode="ColoredCrossSectionStress", show=None, d=None, name=None, png_path=None, rng=None, capture_it=True):
    d = d or canvas(roof)
    bv, mv, p1 = setup(d, mode, show)
    if rng: set_range(d, mv, *rng)
    p1.UserText = lc; p1.ExpireSolution(False); bv.ExpireSolution(False)
    for o in d.Objects:                              # design model D2: the compression-only eliminator runs per load case
        if isinstance(o, GH_Panel) and o.NickName == "TenComElim load case": o.UserText = lc; o.ExpireSolution(False)
    d.NewSolution(False)
    meshes = [x.Value for x in bv.Params.Output[1].VolatileData.AllData(True)]
    cols = [str(x.Value) for x in bv.Params.Output[3].VolatileData.AllData(True)]
    tags = [str(x.Value) for x in bv.Params.Output[4].VolatileData.AllData(True)]
    li = layer(doc, name or "karamba render %s %s" % (roof, case), System.Drawing.Color.FromArgb(200, 200, 200))   # layer colour = mesh-edge colour
    att = Rhino.DocObjects.ObjectAttributes(); att.LayerIndex = li
    bb = G.BoundingBox.Empty
    for m in meshes:
        doc.Objects.AddMesh(m, att); bb.Union(m.GetBoundingBox(True))
    att.ColorSource = Rhino.DocObjects.ObjectColorSource.ColorFromObject; att.ObjectColor = System.Drawing.Color.FromArgb(222, 222, 222)
    for l in doc.Layers:                             # footing from the model, light grey
        if not l.IsDeleted and l.FullPath.startswith(roof + " complete v3e-ring-step::") and "footing" in l.Name:
            for o in doc.Objects.FindByLayer(l) or []:
                doc.Objects.Add(o.Geometry.Duplicate(), att); bb.Union(o.Geometry.GetBoundingBox(True))
    for l in doc.Layers:
        if not l.IsDeleted: l.IsVisible = (l.Index == li)
    d.PreviewMode = Grasshopper.Kernel.GH_PreviewMode.Disabled
    png = capture2(doc, bb, png_path or os.path.join(OUT, "karamba-model-%s-%s.png" % (roof, case)), li) if capture_it else None
    vals = [float(t.replace("%", "")) for t in tags[1:] if t.strip()]   # utilisation tags come as "-309.2%"
    return {"load_case": lc, "mode": mode, "legend_source": "Karamba BeamView 'Axial Stress' legend, auto-scaled by Karamba to the case's own extremes",
            "legend_unit": tags[0] if tags else "", "legend_min_kN_cm2": min(vals) if vals else None, "legend_max_kN_cm2": max(vals) if vals else None,
            "legend_min_MPa": round(min(vals) * 10, 2) if vals else None, "legend_max_MPa": round(max(vals) * 10, 2) if vals else None,
            "legend_tags": tags, "legend_colours": cols, "sign": "negative = compression (Karamba convention)"}, png


def capture(doc, bb, path, wires=True, suffix="-raw.png"):
    v = doc.Views.ActiveView; vp = v.ActiveViewport
    # two fixed display modes, set up once (copies of Shaded): "Karamba nowire" (mesh wires off) and "Karamba wire"
    # (mesh wires on, black). Editing a mode's attributes right before a capture only shows a capture later, so the
    # modes are switched instead of edited.
    dm = Rhino.Display.DisplayModeDescription.FindByName("Karamba wire" if wires else "Karamba nowire")
    vp.DisplayMode = dm
    c = bb.Center
    eye_z = 2.4 + 0.8                                 # eye just above the base ring (top of ring 2.4 m)
    tgt = G.Point3d(c.X, c.Y, eye_z)
    dirv = G.Vector3d(1.0, 0.75, 0.0); dirv.Unitize()  # horizontal view: verticals stay vertical (two-point)
    vp.ChangeToPerspectiveProjection(True, 24.0)
    vp.Camera35mmLensLength = 24.0
    vp.SetCameraLocations(tgt, tgt - dirv * DIST); vp.CameraUp = G.Vector3d.ZAxis
    v.Redraw()
    w0 = Rhino.Display.ViewCapture(); w0.Width = 64; w0.Height = 64; w0.CaptureToBitmap(v)   # flush: a display-mode change only shows from the next capture on
    vc = Rhino.Display.ViewCapture(); vc.Width = CAP; vc.Height = CAP
    vc.DrawAxes = False; vc.DrawGrid = False; vc.DrawGridAxes = False; vc.TransparentBackground = True
    bmp = vc.CaptureToBitmap(v)
    bmp.Save(path.replace(".png", suffix), System.Drawing.Imaging.ImageFormat.Png)   # cropped onto white by crop_white.ps1
    return path

def capture2(doc, bb, path, li):
    """two passes for the coloured-wireframe look: shaded without mesh wires (-raw.png), then the same view with black
    mesh wires (-wire.png); edge_colour.ps1 darkens the shaded colour by 25 % wherever the second pass shows a wire"""
    lay = doc.Layers[li]; old = lay.Color
    capture(doc, bb, path, wires=False, suffix="-raw.png")
    lay.Color = System.Drawing.Color.Black
    capture(doc, bb, path, wires=True, suffix="-wire.png")
    lay.Color = old
    return path

# crop: see crop_white.ps1 (alpha-bbox crop, centred on a white 3200 x 2000 sheet, ~90 % fill)
