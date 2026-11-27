"""Variant D (Gonzalo 2026-11-24: 'the pieces already have the rib to tie them'). Each printed piece is printed around
its rib tube and the cast core runs through, so the pieces are tied to the ribs; only the bed joints between courses
cannot take tension. Built on the variant C canvas (printed courses and fins E = 25 GPa, bonded to the ribs).
The fins are the members that cross the bed joints (piece end walls between one course and the next). In variants B/C
the tension across a bed joint came from the fins' BENDING (their axial force is compression), so in D the fins are
first made trusses (pin-ended, Bending = False: no moment across a joint) and then made
compression-only with Karamba 3.1's 'Tension/Compression Eliminator' (6.Algorithms, TenComElim: Compr = True, BeamIds =
fin, MaxIter 20), which removes the members in tension and re-solves until none is left; it is run once PER LOAD CASE
(LCase input), and the Analyze / BeamForces / Reaction / AnalyzeThII / Buckling of that case read the reduced model.
Head joints along a course cannot be singled out in this model (a course bar spans between rib nodes), so the hoops are
bracketed: D1 courses full E (25 GPa), D2 courses E x 0.02 (66 kN/cm2, open head joints).
Saves stepped-<roof>-karamba-2m-formwork-D1/D2-2026-11-23.gh; main canvases untouched."""
import os, sys, json, math, time, System, Rhino, Grasshopper
from Grasshopper.Kernel import GH_DocumentIO
from Grasshopper.Kernel.Types import GH_Number, GH_String, GH_Boolean, GH_Integer
from Grasshopper.Kernel.Special import GH_Panel
HERE = r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\details\karamba\2026-11-27"
OUT = os.path.join(HERE, "formwork")
PF = r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\polyframe2"
LCS = ["LONG", "W+Y", "W-Y", "W+X", "W-X", "W45", "LIVEX", "LIVEY", "EQX", "EQY"]
TCE = "72a5334b-c9fc-4c01-89d6-b6724828bb98"
gh = Rhino.RhinoApp.GetPlugInObject("Grasshopper")


def comp(d, t): return [o for o in d.Objects if o.GetType().Name == t][0]


def setnum(d, prefix, suffix, v):
    p = [o for o in d.Objects if getattr(o, "NickName", "").startswith(prefix) and o.NickName.endswith(suffix) and o.GetType().Name == "Param_Number"][0]
    p.PersistentData.Clear(); p.SetPersistentData(GH_Number(v)); p.ExpireSolution(False)


def fins_truss(d):
    """fins as trusses (Bending = False on their Create Linear Element): pin-ended, axial force only, so no bending is
    carried across a bed joint; TenComElim then removes the ones in axial tension"""
    for o in d.Objects:
        if o.GetType().Name != "Component_CreateLineElement": continue
        idp = [p for p in o.Params.Input if p.Name == "Identifier"][0]
        if [str(x) for x in idp.VolatileData.AllData(True)][:1] == ["fin"]:
            bp = [p for p in o.Params.Input if p.NickName == "Bending"][0]
            bp.RemoveAllSources(); bp.PersistentData.Clear(); bp.SetPersistentData(GH_Boolean(False)); o.ExpireSolution(False)
            o.NickName = "LineToBeam (fins as trusses, variant D)"
    d.NewSolution(False)


def insert_tce(d):
    asm = comp(d, "Component_AssembleModel_6"); an = comp(d, "Component_Analyze"); th = comp(d, "Component_AnalyzeThII")
    t = Grasshopper.Instances.ComponentServer.EmitObject(System.Guid(TCE)); t.CreateAttributes()
    pv = an.Attributes.Pivot; t.Attributes.Pivot = System.Drawing.PointF(pv.X - 160, pv.Y - 120); t.NickName = "bed joints compression-only (fins)"
    d.AddObject(t, False)
    ins = {p.NickName: p for p in t.Params.Input}
    ins["Model"].AddSource(asm.Params.Output[0])
    ins["MaxIter"].PersistentData.Clear(); ins["MaxIter"].SetPersistentData(GH_Integer(20))
    ins["BeamIds"].PersistentData.Clear(); ins["BeamIds"].SetPersistentData(GH_String("fin"))
    ins["Compr"].PersistentData.Clear(); ins["Compr"].SetPersistentData(GH_Boolean(True))
    pn = GH_Panel(); pn.CreateAttributes(); pn.NickName = "TenComElim load case"; pn.UserText = "LONG"
    pn.Attributes.Pivot = System.Drawing.PointF(pv.X - 360, pv.Y - 100); d.AddObject(pn, False); ins["LCase"].AddSource(pn)
    for c in (an, th):
        c.Params.Input[0].RemoveAllSources(); c.Params.Input[0].AddSource(t.Params.Output[1])
    return t, pn


def one_case(d, t, pn, lc):
    pn.UserText = lc; pn.ExpireSolution(False); d.NewSolution(False)
    an = comp(d, "Component_Analyze"); bf = comp(d, "Component_BeamForces"); rc = comp(d, "Component_Reaction")
    ins = list(bf.Params.Input); outs = list(bf.Params.Output)
    ins[2].RemoveAllSources(); ins[1].RemoveAllSources(); ins[1].PersistentData.Clear()
    ins[2].PersistentData.Clear(); ins[2].SetPersistentData(GH_String(lc)); bf.ExpireSolution(False); bf.CollectData(); bf.ComputeData()
    forces = {p.NickName: [round(x.Value, 3) for x in p.VolatileData.AllData(True)] for p in outs[1:7]}
    rins = list(rc.Params.Input); rins[2].RemoveAllSources(); rins[2].PersistentData.Clear(); rins[2].SetPersistentData(GH_String(lc))
    rc.ExpireSolution(False); rc.CollectData(); rc.ComputeData()
    RF = [x.Value for x in list(rc.Params.Output)[1].VolatileData.AllData(True)]
    active = [bool(x.Value) for x in t.Params.Output[2].VolatileData.AllData(True)]
    md = [x.Value for x in an.Params.Output[1].VolatileData.AllData(True)]
    bk = [x.Value for x in comp(d, "Component_Buckling").Params.Output[1].VolatileData.AllData(True)]
    msg = [str(m) for m in t.RuntimeMessages(Grasshopper.Kernel.GH_RuntimeMessageLevel.Warning)] + [str(m) for m in t.RuntimeMessages(Grasshopper.Kernel.GH_RuntimeMessageLevel.Error)]
    return {"forces": forces, "RF": [(round(f.X, 2), round(f.Y, 2), round(f.Z, 2)) for f in RF], "active": active,
            "maxdisp_cm": md[LCS.index(lc)] if len(md) == len(LCS) else (md[0] if md else None), "buckling": bk[:3], "tce_msgs": msg}


def run(roofs=("15x10", "10x10"), variants=("D1", "D2"), log=print):
    for roof in roofs:
        for v in variants:
            t0 = time.time()
            gh.DisableSolver(); gh.OpenDocument(os.path.join(PF, "stepped-%s-karamba-2m-formwork-C-2026-11-23.gh" % roof))
            d = Grasshopper.Instances.ActiveCanvas.Document
            if v == "D2":
                setnum(d, "Printed course", "Young", 66.0); setnum(d, "Printed course", "In-plane Shear", 27.5); setnum(d, "Printed course", "Transverse Shear", 27.5)
            gh.EnableSolver(); d.NewSolution(True)
            fins_truss(d)
            t, pn = insert_tce(d)
            an = comp(d, "Component_Analyze"); m = list(an.Params.Output[0].VolatileData.AllData(True))
            res = {}
            for lc in LCS:
                res[lc] = one_case(d, t, pn, lc)
                if lc == "LONG":
                    m = list(an.Params.Output[0].VolatileData.AllData(True))[0].Value
                    nodes = [(round(n.pos.X, 4), round(n.pos.Y, 4), round(n.pos.Z, 4)) for n in m.nodes]
                    els = [(e.id, list(e.node_inds)[0], list(e.node_inds)[1]) for e in m.elems]
                    cs = {}
                    for e in m.elems:
                        if e.id in ("course", "fin") and e.id not in cs:
                            c = e.crosec; cs[e.id] = {"A": c.A, "Wy": abs(c.Wely_z_pos), "Wz": abs(c.Welz_y_pos)}
                nf = sum(1 for i, (g, a, b) in enumerate(els) if g == "fin" and not res[lc]["active"][i]) if len(res[lc]["active"]) == len(els) else None
                log("%s %s %s: fins out %s, disp %s cm, msgs %s" % (roof, v, lc, nf, res[lc]["maxdisp_cm"], res[lc]["tce_msgs"][:1]))
            json.dump({"roof": roof, "variant": v, "nodes": nodes, "els": els, "crosec": cs, "cases": res}, open(os.path.join(OUT, "forces-%s-%s.json" % (roof, v)), "w"))
            pn.UserText = "LONG"; pn.ExpireSolution(False)
            d.FilePath = os.path.join(PF, "stepped-%s-karamba-2m-formwork-%s-2026-11-27.gh" % (roof, v)); GH_DocumentIO(d).Save()
            Grasshopper.Instances.DocumentServer.RemoveDocument(d)
            log("%s %s saved, %.0fs" % (roof, v, time.time() - t0))
