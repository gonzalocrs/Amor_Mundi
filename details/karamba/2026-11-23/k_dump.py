# Runs inside the private Rhino (Karamba canvas already solved): dumps nodes, elements and per-load-case beam forces,
# group summaries, displacements, buckling and support reactions to JSON for the stress PDF.  Usage: set ROOF, exec.
import Grasshopper, json, math
from Grasshopper.Kernel.Types import GH_String
OUT = r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\details\karamba\2026-11-23"
LCS = ["LONG", "W+Y", "W-Y", "W+X", "W-X", "W45", "LIVEX", "LIVEY", "EQX", "EQY"]
LONGS = ["LONG", "LIVEX", "LIVEY"]
d = Grasshopper.Instances.ActiveCanvas.Document
def comp(t): return [o for o in d.Objects if o.GetType().Name == t][0]
an = comp("Component_Analyze"); bf = comp("Component_BeamForces"); rc = comp("Component_Reaction")
m = list(an.Params.Output[0].VolatileData.AllData(True))[0].Value
nodes = [(round(n.pos.X, 4), round(n.pos.Y, 4), round(n.pos.Z, 4)) for n in m.nodes]
els = [(e.id, list(e.node_inds)[0], list(e.node_inds)[1]) for e in m.elems]
ins = list(bf.Params.Input); outs = list(bf.Params.Output)
ins[2].RemoveAllSources(); ins[1].RemoveAllSources(); ins[1].PersistentData.Clear()
forces = {}
for lc in LCS:
    ins[2].PersistentData.Clear(); ins[2].SetPersistentData(GH_String(lc))
    bf.ExpireSolution(False); bf.CollectData(); bf.ComputeData()
    forces[lc] = {p.NickName: [round(x.Value, 3) for x in p.VolatileData.AllData(True)] for p in outs[1:7]}
rins = list(rc.Params.Input); lcp = rins[2]; lcp.RemoveAllSources()
reac = {}
for lc in LCS:
    lcp.PersistentData.Clear(); lcp.SetPersistentData(GH_String(lc))
    rc.ExpireSolution(False); rc.CollectData(); rc.ComputeData()
    o = list(rc.Params.Output)
    RF = [x.Value for x in o[1].VolatileData.AllData(True)]; RM = [x.Value for x in o[2].VolatileData.AllData(True)]
    reac[lc] = {"RF": [(round(f.X, 2), round(f.Y, 2), round(f.Z, 2)) for f in RF], "RM": [(round(v.X, 2), round(v.Y, 2), round(v.Z, 2)) for v in RM]}
md = [x.Value for x in list(an.Params.Output)[1].VolatileData.AllData(True)]
fr = [x.Value for x in list(an.Params.Output)[2].VolatileData.AllData(True)]
md2 = [x.Value for x in list(comp("Component_AnalyzeThII").Params.Output)[1].VolatileData.AllData(True)]
bk = [x.Value for x in list(comp("Component_Buckling").Params.Output)[1].VolatileData.AllData(True)]
asm = comp("Component_AssembleModel_6")
mass = [x.Value for x in list(asm.Params.Output)[2].VolatileData.AllData(True)]
json.dump({"roof": ROOF, "nodes": nodes, "els": els, "forces": forces, "reactions": reac,
           "maxdisp_cm": dict(zip(LCS, md)), "maxdisp_ThII_cm": dict(zip(LCS, md2)),
           "sumF": {lc: (round(f.X, 1), round(f.Y, 1), round(f.Z, 1)) for lc, f in zip(LCS, fr)},
           "buckling": bk, "mass_kg": mass}, open(OUT + "\\forces-%s.json" % ROOF, "w"))
print("dumped", ROOF, len(els), len(nodes))
