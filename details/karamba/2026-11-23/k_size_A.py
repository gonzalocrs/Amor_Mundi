"""Variant A sizing (Gonzalo 2026-11-24: 'dimension quickly how big the ribs should be for A').
Formwork = pure weight (courses and fins E = 0.33 kN/cm2). Rib pattern and geometry unchanged; only the solid cast core
diameters per band change, in 20 mm steps, until every band passes in all 10 cases:
  worst fibre -N/A + M/W <= 12 MPa (LONG, LIVEX, LIVEY) and <= 24 MPa (W+-X, W+-Y, W45, EQX, EQY),
  first buckling factor >= 5, max displacement <= span / 250 with span = 10.0 m (the short plan side, both roofs) = 40 mm.
Printed tube = core + 60 mm (3 cm walls). The extra weight of the bigger core comes from Karamba's gravity on the new
section; the extra weight of the bigger printed tube is added by giving each band its own copy of the C30/37 material
with an effective specific weight gamma_eff = 24 x (A_core + extra tube area) / A_core.
EQ point loads are fixed loads in the canvas (not recomputed from mass), so the added mass is not in EQX/EQY: noted.
Saves stepped-<roof>-karamba-2m-formwork-A-sized-2026-11-23.gh; the main canvases and current.3dm are not touched."""
import os, sys, json, math, time, System, Rhino, Grasshopper
from Grasshopper.Kernel import GH_DocumentIO
from Grasshopper.Kernel.Types import GH_Number, GH_String
HERE = r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\details\karamba\2026-11-23"
OUT = os.path.join(HERE, "formwork")
PF = r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\polyframe2"
sys.path.insert(0, HERE)
import k_corners as KC
LONGS = ["LONG", "LIVEX", "LIVEY"]; SHORTS = ["W+Y", "W-Y", "W+X", "W-X", "W45", "EQX", "EQY"]
BANDS = {"rib_bottom": "Rib bottom", "rib_middle": "Rib middle", "rib_top": "Rib top"}
START = {"15x10": {"rib_bottom": 22, "rib_middle": 16, "rib_top": 12}, "10x10": {"rib_bottom": 18, "rib_middle": 14, "rib_top": 12}}
SPAN, BUCK = 10.0, 5.0
gh = Rhino.RhinoApp.GetPlugInObject("Grasshopper")


def setnum(d, prefix, suffix, v):
    p = [o for o in d.Objects if getattr(o, "NickName", "").startswith(prefix) and o.NickName.endswith(suffix) and o.GetType().Name == "Param_Number"][0]
    p.PersistentData.Clear(); p.SetPersistentData(GH_Number(v)); p.ExpireSolution(False)


def band_materials(d):
    """one material per rib band (copy of C30/37 cast), wired to that band's O-Section; returns {band: gamma Param}"""
    src = [o for o in d.Objects if o.GetType().Name == "Component_MaterialProps" and "C30/37" in str(list(o.Params.Input[1].VolatileData.AllData(True))[0])][0]
    mats = {}
    for o in list(d.Objects):                        # copy: materials are added inside the loop
        if o.GetType().Name == "Component_CroSec_3" and o.NickName == "O-Section":
            dia = [p for p in o.Params.Input if p.NickName == "Diameter"][0]
            nick = dia.Sources[0].NickName
            band = [b for b, pre in BANDS.items() if nick.startswith(pre)][0]
            m = Grasshopper.Instances.ComponentServer.EmitObject(src.ComponentGuid); m.CreateAttributes()
            pv = o.Attributes.Pivot; m.Attributes.Pivot = System.Drawing.PointF(pv.X - 180, pv.Y - 60); m.NickName = "C30/37 cast + tube weight, " + band
            d.AddObject(m, False)
            vals = {"Family": GH_String("Concrete"), "Name": GH_String("C30/37 cast, %s (gamma incl. printed tube)" % band),
                    "E": GH_Number(3300.0), "G12": GH_Number(1375.0), "G3": GH_Number(1375.0), "gamma": GH_Number(24.0),
                    "alphaT": GH_Number(1e-5), "ft": GH_Number(0.29), "fc": GH_Number(-2.0)}          # = the cast C30/37 of the canvas
            for q in m.Params.Input:
                if q.NickName in vals: q.PersistentData.Clear(); q.SetPersistentData(vals[q.NickName])
            matp = [p for p in o.Params.Input if p.NickName == "Mat"][0]
            matp.RemoveAllSources(); matp.AddSource(m.Params.Output[0])
            mats[band] = [p for p in m.Params.Input if p.NickName == "gamma"][0]
    return mats


def gamma_eff(D0, D):
    """core D (m); tube = core + 0.06; extra tube area vs the original tube carried by the core's specific weight"""
    tube = lambda c: math.pi / 4 * ((c + 0.06) ** 2 - c ** 2)
    core = math.pi / 4 * D * D
    return 24.0 * (core + tube(D) - tube(D0)) / core


def check(fname, roof, D):
    J = json.load(open(fname)); f = J["forces"]; res = {}
    for g in BANDS:
        dm = D[g] / 100.0; A = math.pi * dm * dm / 4; W = math.pi * dm ** 3 / 32; best = (0, None, 0, 0)
        for lcs, al in ((LONGS, 12.0), (SHORTS, 24.0)):
            for lc in lcs:
                for i, (gg, a, b) in enumerate(J["els"]):
                    if gg != g: continue
                    for t in (0, 1):
                        N = f[lc]["N"][2 * i + t]; M = math.hypot(f[lc]["My"][2 * i + t], f[lc]["Mz"][2 * i + t])
                        u = (-N / A + M / W) / 1000.0 / al
                        if u > best[0]: best = (u, lc, round(-N / A / 1000.0, 2), round(M / W / 1000.0, 2))
        res[g] = {"util": round(best[0], 3), "case": best[1], "axial_MPa": best[2], "bending_MPa": best[3]}
    disp = max(J["maxdisp_cm"].values()) * 10; buck = J["buckling"][0]
    vol = {g: sum(math.dist(J["nodes"][a], J["nodes"][b]) for gg, a, b in J["els"] if gg == g) for g in BANDS}
    return res, round(disp, 1), round(buck, 2), vol, round(sum(f[2] for f in J["reactions"]["LONG"]["RF"]), 1)


def run(roofs=("15x10", "10x10"), log=print, maxit=12):
    out = {}
    for roof in roofs:
        t0 = time.time()
        gh.DisableSolver(); gh.OpenDocument(os.path.join(PF, "stepped-%s-karamba-2m-formwork-A-2026-11-23.gh" % roof))
        d = Grasshopper.Instances.ActiveCanvas.Document
        gh.EnableSolver(); d.NewSolution(True)          # solve once so the material inputs carry their values
        mats = band_materials(d)
        D = dict(START[roof]); hist = []
        for it in range(maxit):
            for g, pre in BANDS.items():
                setnum(d, pre, "Diameter", float(D[g])); setnum(d, pre, "Wall thickness", D[g] / 2.0)
                mats[g].PersistentData.Clear(); mats[g].SetPersistentData(GH_Number(gamma_eff(START[roof][g] / 100.0, D[g] / 100.0))); mats[g].ExpireSolution(False)
            gh.EnableSolver(); d.NewSolution(True)
            fname = os.path.join(OUT, "forces-%s-A-sized.json" % roof)
            KC.dump(d, fname, [])
            res, disp, buck, lens, rz = check(fname, roof, D)
            hist.append({"D_cm": dict(D), "util": {g: r["util"] for g, r in res.items()}, "disp_mm": disp, "buckling": buck, "Rz_LONG_kN": rz})
            log("%s it%d D=%s util=%s disp=%.1f buck=%.2f Rz=%.0f" % (roof, it, D, {g: r["util"] for g, r in res.items()}, disp, buck, rz))
            fail = [g for g, r in res.items() if r["util"] > 1.0]
            if not fail and (disp > SPAN * 1000 / 250 or buck < BUCK):
                fail = [max(res, key=lambda g: res[g]["util"])]          # global criterion: grow the most stressed band
            if not fail: break
            for g in fail: D[g] += 2
            ins = list(KC.comp(d, "Component_BeamForces").Params.Input)   # dump() unplugged these; the solve re-reads PersistentData, fine
        S = START[roof]
        added = {}
        for g in BANDS:
            core = lambda c: math.pi / 4 * (c / 100.0) ** 2
            tube = lambda c: math.pi / 4 * (((c + 6) / 100.0) ** 2 - (c / 100.0) ** 2)
            dv = (core(D[g]) - core(S[g]) + tube(D[g]) - tube(S[g])) * lens[g]
            added[g] = {"m3": round(dv, 3), "kN": round(24.0 * dv, 1)}
        out[roof] = {"final_D_cm": D, "start_D_cm": S, "bands": res, "disp_mm": disp, "disp_limit_mm": SPAN * 1000 / 250, "buckling": buck,
                     "Rz_LONG_kN": rz, "added": added, "lengths_m": {g: round(v, 2) for g, v in lens.items()}, "history": hist}
        d.FilePath = os.path.join(PF, "stepped-%s-karamba-2m-formwork-A-sized-2026-11-23.gh" % roof); GH_DocumentIO(d).Save()
        Grasshopper.Instances.DocumentServer.RemoveDocument(d)
        log("%s done %.0fs" % (roof, time.time() - t0))
    json.dump(out, open(os.path.join(OUT, "sizing-A.json"), "w"), indent=1)
    return out
