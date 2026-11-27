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


def ghost_material(doc):
    i = doc.Materials.Find("karamba ghost casing", True)
    if i < 0:
        m = Rhino.DocObjects.Material(); m.Name = "karamba ghost casing"; m.DiffuseColor = System.Drawing.Color.FromArgb(235, 235, 235)
        m.Transparency = 0.82; i = doc.Materials.Add(m)
    return i


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
        K.capture2(doc, bb, os.path.join(OUT, "karamba-model-%s-%s-frame-only.png" % (roof, case)), li)
        # full: printed casing of the final model as a ghost on the same layer
        mi = ghost_material(doc); ids = []
        att = Rhino.DocObjects.ObjectAttributes(); att.LayerIndex = li
        att.MaterialSource = Rhino.DocObjects.ObjectMaterialSource.MaterialFromObject; att.MaterialIndex = mi
        att.ColorSource = Rhino.DocObjects.ObjectColorSource.ColorFromObject; att.ObjectColor = System.Drawing.Color.FromArgb(235, 235, 235)
        for l in doc.Layers:
            if not l.IsDeleted and l.FullPath.startswith(roof + " complete v3e-ring-step::") and ("printed pieces" in l.Name or "top course" in l.Name or "printed U formwork" in l.Name):
                for o in doc.Objects.FindByLayer(l) or []:
                    ids.append(doc.Objects.Add(o.Geometry.Duplicate(), att))
        for l in doc.Layers:
            if not l.IsDeleted: l.IsVisible = (l.Index == li)
        K.capture2(doc, bb, os.path.join(OUT, "karamba-model-%s-%s.png" % (roof, case)), li)
        for i in ids: doc.Objects.Delete(i, True)
        info["legend_min_kN_cm2"], info["legend_max_kN_cm2"] = -lim, lim
        legends["%s %s" % (roof, case)] = info
        log("%s %s (%s) rendered" % (roof, case, lc))
    json.dump(legends, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "legends-2026-11-27.json"), "w"), indent=1)
    return legends
