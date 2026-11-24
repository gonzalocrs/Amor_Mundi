"""Dump of the design model D2 (2026-11-24) in the k_dump.py format, so stress_pdf.py, rect_check.py, rib_path.py and the
renders read D2: forces-<roof>.json (variant B kept as forces-<roof>-variantB.json).
D2 = printed pieces tied to the ribs through the tube (printed concrete E 25 GPa), courses E x 0.02 (open head joints),
fins (end walls across the bed joints) pin-ended trusses made compression-only by Karamba's Tension/Compression
Eliminator, run per load case. For each case the eliminator panel is set, the canvas solved, and that case's forces,
reactions, displacements are read from the reduced model; members removed in a case get zero forces there.
Buckling from the LONG model (the fins all stay active under LONG)."""
import os, json, Rhino, Grasshopper
from Grasshopper.Kernel.Types import GH_String
from Grasshopper.Kernel.Special import GH_Panel
HERE = r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\details\karamba\2026-11-23"
PF = r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\polyframe2"
LCS = ["LONG", "W+Y", "W-Y", "W+X", "W-X", "W45", "LIVEX", "LIVEY", "EQX", "EQY"]
gh = Rhino.RhinoApp.GetPlugInObject("Grasshopper")


def comp(d, t): return [o for o in d.Objects if o.GetType().Name == t][0]


def run(roofs=("15x10", "10x10"), log=print):
    out = {}
    for roof in roofs:
        gh.DisableSolver(); gh.OpenDocument(os.path.join(PF, "stepped-%s-karamba-2m-2026-11-23.gh" % roof)); gh.EnableSolver()
        d = Grasshopper.Instances.ActiveCanvas.Document; d.NewSolution(True)
        pn = [o for o in d.Objects if isinstance(o, GH_Panel) and o.NickName == "TenComElim load case"][0]
        tce = [o for o in d.Objects if o.GetType().Name == "Component_TensionCompressionEliminator" or "Elim" in o.GetType().Name][0]
        an = comp(d, "Component_Analyze"); th = comp(d, "Component_AnalyzeThII"); bf = comp(d, "Component_BeamForces"); rc = comp(d, "Component_Reaction")
        asm = comp(d, "Component_AssembleModel_6")
        m0 = list(asm.Params.Output[0].VolatileData.AllData(True))[0].Value
        nodes = [(round(n.pos.X, 4), round(n.pos.Y, 4), round(n.pos.Z, 4)) for n in m0.nodes]
        els = [(e.id, list(e.node_inds)[0], list(e.node_inds)[1]) for e in m0.elems]
        n = len(els)
        forces, reac, md, md2, sumF, active = {}, {}, {}, {}, {}, {}
        bk = None
        for lc in LCS:
            pn.UserText = lc; pn.ExpireSolution(False); d.NewSolution(False)
            act = [bool(x.Value) for x in tce.Params.Output[2].VolatileData.AllData(True)]
            ids = [i for i in range(n) if act[i]]
            ins = list(bf.Params.Input); outs = list(bf.Params.Output)
            ins[2].RemoveAllSources(); ins[1].RemoveAllSources(); ins[1].PersistentData.Clear()
            ins[2].PersistentData.Clear(); ins[2].SetPersistentData(GH_String(lc)); bf.ExpireSolution(False); bf.CollectData(); bf.ComputeData()
            fz = {}
            for p in outs[1:7]:
                vals = [round(x.Value, 3) for x in p.VolatileData.AllData(True)]
                full = [0.0] * (2 * n)
                for j, i in enumerate(ids):
                    full[2 * i] = vals[2 * j]; full[2 * i + 1] = vals[2 * j + 1]
                fz[p.NickName] = full
            forces[lc] = fz
            rins = list(rc.Params.Input); rins[2].RemoveAllSources(); rins[2].PersistentData.Clear(); rins[2].SetPersistentData(GH_String(lc))
            rc.ExpireSolution(False); rc.CollectData(); rc.ComputeData()
            o = list(rc.Params.Output)
            RF = [x.Value for x in o[1].VolatileData.AllData(True)]; RM = [x.Value for x in o[2].VolatileData.AllData(True)]
            reac[lc] = {"RF": [(round(f.X, 2), round(f.Y, 2), round(f.Z, 2)) for f in RF], "RM": [(round(v.X, 2), round(v.Y, 2), round(v.Z, 2)) for v in RM]}
            k = LCS.index(lc)
            mdl = [x.Value for x in an.Params.Output[1].VolatileData.AllData(True)]; md[lc] = mdl[k]
            fr = [x.Value for x in an.Params.Output[2].VolatileData.AllData(True)]; sumF[lc] = (round(fr[k].X, 1), round(fr[k].Y, 1), round(fr[k].Z, 1))
            mdt = [x.Value for x in th.Params.Output[1].VolatileData.AllData(True)]; md2[lc] = mdt[k]
            active[lc] = act
            if lc == "LONG":
                bk = [x.Value for x in comp(d, "Component_Buckling").Params.Output[1].VolatileData.AllData(True)]
            log("%s %s: removed %d" % (roof, lc, n - len(ids)))
        mass = [x.Value for x in asm.Params.Output[2].VolatileData.AllData(True)]
        J = {"roof": roof, "model": "D2", "nodes": nodes, "els": els, "forces": forces, "reactions": reac, "maxdisp_cm": md, "maxdisp_ThII_cm": md2,
             "sumF": sumF, "buckling": bk, "mass_kg": mass, "active": active}
        json.dump(J, open(os.path.join(HERE, "forces-%s.json" % roof), "w"))
        pn.UserText = "LONG"; pn.ExpireSolution(False); d.NewSolution(False)
        out[roof] = {lc: sum(1 for a in active[lc] if not a) for lc in LCS}
    return out
