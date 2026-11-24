"""Formwork study (Gonzalo 2026-11-24): 'if I only do ribs and consider the whole formwork as weight, does it work?
can I use the formwork as a structural element?'  Runs in the separate Rhino, on the visible 2 m Karamba canvases.
Geometry, loads and supports unchanged; ONLY the stiffness of the printed courses and fins changes:
  A  ribs only: courses and fins E = 0.33 kN/cm2 (C30/37 E 3300 x 0.0001), G = E / 2.4; weight unchanged
  B  current:   courses E x 0.02 (66), fins E x 0.3 (990)  -- the canvases as saved
  C  formwork structural: courses and fins E = 2500 kN/cm2 (25 GPa printed concrete), G = E / 2.4 (nu 0.2), bonded
Each variant: solve all 10 cases, dump forces like k_dump/k_corners (formwork/forces-<roof>-<v>.json), save the
variant canvas as its own file (the main canvases stay B), render a Karamba BeamView 'Stress/Strength Ratio' image
of the worst short-term case with courses and fins shown, baked to layer 'formwork study <roof> <v>'."""
import os, sys, json, math, time, Rhino, Grasshopper
from Grasshopper.Kernel import GH_DocumentIO
from Grasshopper.Kernel.Types import GH_Number
HERE = r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\details\karamba\2026-11-23"
OUT = os.path.join(HERE, "formwork")
PNG = r"C:\Users\gonza\AppData\Local\Temp\claude\5c622a39c96e3387\d0f96d15-672a-4d67-b7d7-f160f3f4487b\scratchpad\formwork"
PF = r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\polyframe2"
sys.path.insert(0, HERE)
import k_corners as KC
import k_beamview_render as K

SHORTS = ["W+Y", "W-Y", "W+X", "W-X", "W45", "EQX", "EQY"]
RIBS = {"15x10": {"rib_bottom": 0.22, "rib_middle": 0.16, "rib_top": 0.12}, "10x10": {"rib_bottom": 0.18, "rib_middle": 0.14, "rib_top": 0.12}}
VARIANTS = {"A": {"course": 0.33, "fin": 0.33}, "B": None, "C": {"course": 2500.0, "fin": 2500.0}}
ALL = ["rib_bottom", "rib_middle", "rib_top", "ring", "arch", "crown", "column", "course", "fin"]
os.makedirs(OUT, exist_ok=True); os.makedirs(PNG, exist_ok=True)
gh = Rhino.RhinoApp.GetPlugInObject("Grasshopper")


def setnum(d, prefix, suffix, v):
    p = [o for o in d.Objects if getattr(o, "NickName", "").startswith(prefix) and o.NickName.endswith(suffix)][0]
    p.PersistentData.Clear(); p.SetPersistentData(GH_Number(v)); p.ExpireSolution(False)


def worst_short(fname, roof):
    D = json.load(open(fname)); best = (0, "W+Y")
    for lc in SHORTS:
        f = D["forces"][lc]
        for i, (g, a, b) in enumerate(D["els"]):
            if g not in RIBS[roof]: continue
            dm = RIBS[roof][g]; A = math.pi * dm * dm / 4; W = math.pi * dm ** 3 / 32
            for t in (0, 1):
                s = (-f["N"][2 * i + t] / A + math.hypot(f["My"][2 * i + t], f["Mz"][2 * i + t]) / W) / 1000.0
                if s > best[0]: best = (s, lc)
    return best[1]


def run(roofs=("15x10", "10x10"), variants=("A", "B", "C"), log=print):
    doc = Rhino.RhinoDoc.ActiveDoc; res = {}
    for roof in roofs:
        src = os.path.join(PF, "stepped-%s-karamba-2m-2026-11-23.gh" % roof)
        for v in variants:
            t = time.time()
            gh.DisableSolver(); gh.OpenDocument(src)
            d = Grasshopper.Instances.ActiveCanvas.Document
            if VARIANTS[v]:
                for grp, pre in (("course", "Printed course"), ("fin", "Printed fins")):
                    E = VARIANTS[v][grp]
                    setnum(d, pre, "Young", E); setnum(d, pre, "In-plane Shear", E / 2.4); setnum(d, pre, "Transverse Shear", E / 2.4)
            gh.EnableSolver(); d.NewSolution(True)
            fname = os.path.join(OUT, "forces-%s-%s.json" % (roof, v))
            KC.dump(d, fname, [])
            # cross-section properties of the printed members, from the Karamba model
            an = KC.comp(d, "Component_Analyze"); m = list(an.Params.Output[0].VolatileData.AllData(True))[0].Value
            cs = {}
            for e in m.elems:
                if e.id in ("course", "fin") and e.id not in cs:
                    c = e.crosec; cs[e.id] = {"A": c.A, "Wy": abs(c.Wely_z_pos), "Wz": abs(c.Welz_y_pos), "type": type(c).__name__}
            D = json.load(open(fname)); D["crosec"] = cs; D["variant"] = v; D["E_kN_cm2"] = VARIANTS[v] or {"course": 66.0, "fin": 990.0}
            json.dump(D, open(fname, "w"))
            lc = worst_short(fname, roof)
            leg, png = K.render(doc, roof, v, lc, mode="ColoredCrossSectionUtilization", show=ALL, d=d,
                                name="formwork study %s %s" % (roof, v), png_path=os.path.join(PNG, "formwork-%s-%s.png" % (roof, v)))
            leg["case"] = lc; res["%s %s" % (roof, v)] = leg
            if v != "B":
                d.FilePath = os.path.join(PF, "stepped-%s-karamba-2m-formwork-%s-2026-11-23.gh" % (roof, v)); GH_DocumentIO(d).Save()
            Grasshopper.Instances.DocumentServer.RemoveDocument(d)
            log("%s %s done in %.0fs, worst short %s" % (roof, v, time.time() - t, lc))
    json.dump(res, open(os.path.join(OUT, "render_legends.json"), "w"), indent=1)
    gh.DisableSolver(); gh.OpenDocument(os.path.join(PF, "stepped-15x10-karamba-2m-2026-11-23.gh")); gh.EnableSolver()   # back on variant B
    return res
