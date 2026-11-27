# Corner-leg removal study (Gonzalo 2026-11-23: "test each structure taking out 1, 2, 3 and 4 legs in the corners").
# Runs inside the private Rhino. For each roof and case: open the 2 m canvas, take the corner columns out of the
# 'column stubs' lines and the supports, solve all 10 load cases, dump forces like k_dump.py, save the canvas as a new
# file (the main canvases are not changed). Usage: exec with ROOFS = [...] (optional).
import os, json, math, time, Rhino, Grasshopper
from Grasshopper.Kernel import GH_DocumentIO
from Grasshopper.Kernel.Types import GH_String
OUT = r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\details\karamba\2026-11-27\corners"
PF = r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\polyframe2"
LCS = ["LONG", "W+Y", "W-Y", "W+X", "W-X", "W45", "LIVEX", "LIVEY", "EQX", "EQY"]
CEN = {"15x10": (85.0, 0.0), "10x10": (85.0, -20.0)}
# corners named by compass: SW (-,-), SE (+,-), NE (+,+), NW (-,+); "adjacent" = the two on the south long side
CASES = [("0", []), ("1", ["SW"]), ("2adj", ["SW", "SE"]), ("2diag", ["SW", "NE"]), ("3", ["SW", "SE", "NE"]), ("4", ["SW", "SE", "NE", "NW"])]
os.makedirs(OUT, exist_ok=True)
gh = Rhino.RhinoApp.GetPlugInObject("Grasshopper")


def comp(d, t):
    return [o for o in d.Objects if o.GetType().Name == t][0]


def param(d, nick):
    return [o for o in d.Objects if getattr(o, "NickName", "") == nick][0]


def corner_xy(sup_pts, roof):
    cx, cy = CEN[roof]
    res = {}
    for name, sx, sy in (("SW", -1, -1), ("SE", 1, -1), ("NE", 1, 1), ("NW", -1, 1)):
        # diagonal corner support: the one furthest along the (sx, sy) diagonal, normalised by the plan half-sizes
        hx = max(abs(p.X - cx) for p in sup_pts); hy = max(abs(p.Y - cy) for p in sup_pts)
        res[name] = max(sup_pts, key=lambda p: sx * (p.X - cx) / hx + sy * (p.Y - cy) / hy)
    return res


def dump(d, fname, removed):
    an = comp(d, "Component_Analyze"); bf = comp(d, "Component_BeamForces"); rc = comp(d, "Component_Reaction")
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
    md2 = [x.Value for x in list(comp(d, "Component_AnalyzeThII").Params.Output)[1].VolatileData.AllData(True)]
    bk = [x.Value for x in list(comp(d, "Component_Buckling").Params.Output)[1].VolatileData.AllData(True)]
    json.dump({"nodes": nodes, "els": els, "forces": forces, "reactions": reac, "removed": removed,
               "maxdisp_cm": dict(zip(LCS, md)), "maxdisp_ThII_cm": dict(zip(LCS, md2)),
               "sumF": {lc: (round(f.X, 1), round(f.Y, 1), round(f.Z, 1)) for lc, f in zip(LCS, fr)}, "buckling": bk},
              open(fname, "w"))


def run(roofs=("15x10", "10x10"), log=print):
    for roof in roofs:
        src = os.path.join(PF, "stepped-%s-karamba-2m-2026-11-27.gh" % roof)
        for case, corners in CASES:
            t = time.time()
            gh.DisableSolver(); gh.OpenDocument(src)
            d = Grasshopper.Instances.ActiveCanvas.Document
            sup = param(d, "20 column tops" if roof == "15x10" else [o.NickName for o in d.Objects if o.GetType().Name == "Param_Point" and "column" in o.NickName][0])
            col = [o for o in d.Objects if o.GetType().Name == "Param_Line" and o.NickName.startswith("column")][0]
            pts = [g.Value for g in sup.PersistentData.AllData(True)]
            cxy = corner_xy(pts, roof)
            rem = [cxy[c] for c in corners]
            keep_pts = [p for p in pts if all(p.DistanceTo(r) > 0.05 for r in rem)]
            lines = [g.Value for g in col.PersistentData.AllData(True)]
            keep_lines = [l for l in lines if all(math.hypot(l.From.X - r.X, l.From.Y - r.Y) > 0.05 for r in rem)]
            from Grasshopper.Kernel.Types import GH_Point, GH_Line
            sup.PersistentData.Clear(); [sup.PersistentData.Append(GH_Point(p)) for p in keep_pts]
            col.PersistentData.Clear(); [col.PersistentData.Append(GH_Line(l)) for l in keep_lines]
            gh.EnableSolver(); d.NewSolution(True)
            dump(d, os.path.join(OUT, "forces-%s-%s.json" % (roof, case)), [(r.X, r.Y) for r in rem])
            d.FilePath = os.path.join(PF, "stepped-%s-karamba-2m-corners-%s-2026-11-27.gh" % (roof, case)); GH_DocumentIO(d).Save()
            Grasshopper.Instances.DocumentServer.RemoveDocument(d)
            log("%s case %s: removed %s, supports %d, column lines %d, %.0fs" % (roof, case, corners, len(keep_pts), len(keep_lines), time.time() - t))
