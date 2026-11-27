"""Karamba-model renders at the final sizes (2026-11-27), same style as the 2026-11-24 set: ribs from Karamba's own
BeamView ('Axial Stress' coloured cross sections, fixed legend +-0.4 kN/cm2 LONG / +-0.7 kN/cm2 SHORT, Karamba's
gradient), base ring / crown / columns drawn as continuous mitred boxes from the same forces (k_mitre_rings.py, now
52.8 x 40 / 55.2 x 40 rings and radial 42 x 36 / 36.2 x 30 columns), footing in light grey. Two images per roof and case:
'-frame-only' (structure only) and the full one with the printed casing of the final model as a transparent ghost.
Run inside the separate Rhino with the final model imported (footing and casing are taken from it)."""
import os, json, System, Rhino
import Rhino.Geometry as G
import k_beamview_render as K
import k_mitre_rings as M
OUT = r"C:\Users\gonza\AppData\Local\Temp\claude\5c622a39c96e3387\d0f96d15-672a-4d67-b7d7-f160f3f4487b\scratchpad\kmodel27"
CASES = {("15x10", "LONG"): ("LONG", 0.4), ("15x10", "SHORT"): ("W-Y", 0.7), ("10x10", "LONG"): ("LONG", 0.4), ("10x10", "SHORT"): ("W+Y", 0.7)}
RIBS = ["rib_bottom", "rib_middle", "rib_top"]


def column_stubs(doc, roof, li):
    """the part of each column below the Karamba supports (+-0.00) down to the top of the footing (-0.30), at the
    column's real section (long side radial), plain light grey like the footing: it carries no Karamba stress colour,
    it only shows that the columns stand on the footing (Gonzalo 2026-11-27: 'why is this levitating?')"""
    here = os.path.dirname(os.path.abspath(__file__))
    D = json.load(open(os.path.join(here, "forces-%s.json" % roof)))
    cols = json.load(open(os.path.join(here, "model_columns_final.json")))[roof]["cols"]
    feet = sorted({tuple(D["nodes"][n]) for g, a, b in D["els"] if g == "column" for n in (a, b) if abs(D["nodes"][n][2]) < 1e-6})
    grey = System.Drawing.Color.FromArgb(222, 222, 222)
    att = Rhino.DocObjects.ObjectAttributes(); att.LayerIndex = li
    att.ColorSource = Rhino.DocObjects.ObjectColorSource.ColorFromObject; att.ObjectColor = grey
    ids = []
    for (x, y, z) in feet:
        c = min(cols, key=lambda c: (c["cx"] - x) ** 2 + (c["cy"] - y) ** 2)
        u = G.Vector3d(c["long_dir"][0], c["long_dir"][1], 0); u.Unitize(); v = G.Vector3d.CrossProduct(G.Vector3d.ZAxis, u)
        pl = G.Plane(G.Point3d(x, y, -0.30), u, v)
        box = G.Box(pl, G.Interval(-c["radial_m"] / 2, c["radial_m"] / 2), G.Interval(-c["width_m"] / 2, c["width_m"] / 2), G.Interval(0, 0.30))
        m = G.Mesh.CreateFromBox(box, 1, 1, 1)
        for _k in range(m.Vertices.Count): m.VertexColors.Add(grey)
        m.Normals.ComputeNormals()
        ids.append(doc.Objects.AddMesh(m, att))
    return ids


_GHOST = {}


def ghost_material(doc):
    """one transparent material for the casing ghost (set after Add + CommitChanges, so Rhino 8 shows the transparency)"""
    i = _GHOST.get(doc.RuntimeSerialNumber)
    if i is None:
        m = Rhino.DocObjects.Material(); m.Name = "karamba ghost casing"; i = doc.Materials.Add(m)
        mm = doc.Materials[i]; mm.DiffuseColor = System.Drawing.Color.FromArgb(235, 235, 235); mm.Transparency = 0.6; mm.CommitChanges()
        _GHOST[doc.RuntimeSerialNumber] = i
    return i


def shoot(doc, bb, path):
    """shaded capture without mesh wires; captured twice because a display-mode change only shows from the next
    capture on (the first one is overwritten)"""
    K.capture(doc, bb, path, wires=False)
    K.capture(doc, bb, path, wires=False)


def run(doc, cases=None, log=print):
    os.makedirs(OUT, exist_ok=True)
    legends = {}
    for (roof, case), (lc, lim) in (cases or CASES).items():
        d = K.canvas(roof)
        info, _ = K.render(doc, roof, case, lc, show=RIBS, d=d, rng=(-lim, lim), capture_it=False)
        li = doc.Layers.FindByFullPath("karamba render %s %s" % (roof, case), -1)
        M.build(doc, roof, lc, lim, li)
        bb = G.BoundingBox.Empty
        for o in doc.Objects.FindByLayer(doc.Layers[li]) or []: bb.Union(o.Geometry.GetBoundingBox(True))
        for l in doc.Layers:
            if not l.IsDeleted: l.IsVisible = (l.Index == li)
        shoot(doc, bb, os.path.join(OUT, "karamba-model-%s-%s-frame-only.png" % (roof, case)))
        # full: printed casing of the final model as a ghost on the same layer
        mi = ghost_material(doc); ids = []
        att = Rhino.DocObjects.ObjectAttributes(); att.LayerIndex = li
        att.MaterialSource = Rhino.DocObjects.ObjectMaterialSource.MaterialFromObject; att.MaterialIndex = mi
        att.ColorSource = Rhino.DocObjects.ObjectColorSource.ColorFromObject; att.ObjectColor = System.Drawing.Color.FromArgb(195, 195, 195)
        for l in doc.Layers:
            if not l.IsDeleted and l.FullPath.startswith(roof + " complete v3e-ring-step::") and ("printed pieces" in l.Name or "top course" in l.Name or "printed U formwork" in l.Name):
                for o in doc.Objects.FindByLayer(l) or []:
                    # ghost = the piece outlines as thin light-grey lines (a transparent material is not shown by
                    # every display mode; lines read the same everywhere and keep the structure visible)
                    for c in G.Curve.JoinCurves(o.Geometry.DuplicateEdgeCurves(False), 0.001):
                        ids.append(doc.Objects.AddCurve(c, att))
        for l in doc.Layers:
            if not l.IsDeleted: l.IsVisible = (l.Index == li)
        shoot(doc, bb, os.path.join(OUT, "karamba-model-%s-%s.png" % (roof, case)))
        for i in ids: doc.Objects.Delete(i, True)
        info["legend_min_kN_cm2"], info["legend_max_kN_cm2"] = -lim, lim
        legends["%s %s" % (roof, case)] = info
        log("%s %s (%s) rendered" % (roof, case, lc))
    json.dump(legends, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "legends-2026-11-27.json"), "w"), indent=1)
    return legends
