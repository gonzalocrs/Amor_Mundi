"""Karamba re-run on the FINAL model sizes (Gonzalo 2026-11-27: "update the pdf report" after the ring and columns
grew inward to the rib landings). Canvases polyframe2/stepped-<roof>-karamba-2m-2026-11-27.gh = the D2 canvases of
2026-11-23 with only two changes, made on the canvas (visible Param_Number / Param_Vector inputs):
  - base ring 52.8 x 40 cm (15x10) / 55.2 x 40 cm (10x10): typical cast width x real depth of the final model
    (was 40 x 40 / 40 wide x 30 deep);
  - columns 42 (radial) x 36 cm (15x10) / 36.2 x 30 cm (10x10), long side radial through a Z-Orientation vector per
    column taken from the final model (was 36 x 36 / 30 x 30).
Ribs, pieces, loads, supports and the D2 joint model (fins compression-only via TenComElim, per load case) unchanged.
Writes, in details/karamba/2026-11-27:
  forces-<roof>.json                 design model D2, k_dump_D2 format (stress_pdf, rect_check, rib_path, renders)
  formwork/forces-<roof>-D2.json     the same solve in k_variant_D format (variant_D_report -> page 09)
  formwork/forces-<roof>-D1.json     bound with stiff head joints (courses E 25 GPa), same new sizes
  corners/forces-<roof>-<case>.json  corner columns taken out (page 07), now on D2 with the new sizes
Runs inside Rhino (Karamba licence first); call start() - the work runs in Rhino's Idle loop and logs to k_run_final.log."""
import os, json, math, time, Rhino, Grasshopper
from Grasshopper.Kernel import GH_DocumentIO
from Grasshopper.Kernel.Types import GH_String, GH_Number, GH_Point, GH_Line
from Grasshopper.Kernel.Special import GH_Panel
HERE = r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\details\karamba\2026-11-27"
PF = r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\polyframe2"
LOG = os.path.join(HERE, "k_run_final.log")
LCS = ["LONG", "W+Y", "W-Y", "W+X", "W-X", "W45", "LIVEX", "LIVEY", "EQX", "EQY"]
CEN = {"15x10": (85.0, 0.0), "10x10": (85.0, -20.0)}
CASES = [("0", []), ("1", ["SW"]), ("2adj", ["SW", "SE"]), ("2diag", ["SW", "NE"]), ("3", ["SW", "SE", "NE"]), ("4", ["SW", "SE", "NE", "NW"])]
gh = Rhino.RhinoApp.GetPlugInObject("Grasshopper")
for sub in ("formwork", "corners"):
    os.makedirs(os.path.join(HERE, sub), exist_ok=True)


def log(msg):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(time.strftime("%H:%M:%S ") + msg + "\n")


def comp(d, t): return [o for o in d.Objects if o.GetType().Name == t][0]


def canvas(roof): return os.path.join(PF, "stepped-%s-karamba-2m-2026-11-27.gh" % roof)


def open_doc(path):
    gh.DisableSolver(); gh.OpenDocument(path); gh.EnableSolver()
    d = Grasshopper.Instances.ActiveCanvas.Document; d.NewSolution(True); return d


def setnum(d, prefix, suffix, v):
    p = [o for o in d.Objects if getattr(o, "NickName", "").startswith(prefix) and o.NickName.endswith(suffix) and o.GetType().Name == "Param_Number"][0]
    p.PersistentData.Clear(); p.SetPersistentData(GH_Number(v)); p.ExpireSolution(False)


def solve(d, tag):
    """all 10 load cases, each from its own compression-only reduced model (as k_dump_D2.py)"""
    pn = [o for o in d.Objects if isinstance(o, GH_Panel) and o.NickName == "TenComElim load case"][0]
    tce = [o for o in d.Objects if o.GetType().Name == "Component_TenComElim"][0]
    an = comp(d, "Component_Analyze"); th = comp(d, "Component_AnalyzeThII"); bf = comp(d, "Component_BeamForces"); rc = comp(d, "Component_Reaction")
    asm = comp(d, "Component_AssembleModel_6")
    m0 = list(asm.Params.Output[0].VolatileData.AllData(True))[0].Value
    nodes = [(round(n.pos.X, 4), round(n.pos.Y, 4), round(n.pos.Z, 4)) for n in m0.nodes]
    els = [(e.id, list(e.node_inds)[0], list(e.node_inds)[1]) for e in m0.elems]
    cs = {}
    for e in m0.elems:
        if e.id not in cs:
            c = e.crosec; cs[e.id] = {"A": c.A, "Wy": abs(c.Wely_z_pos), "Wz": abs(c.Welz_y_pos), "name": str(c.name)}
    n = len(els)
    R = {"nodes": nodes, "els": els, "crosec": cs, "full": {}, "red": {}, "reac": {}, "md": {}, "md2": {}, "sumF": {}, "active": {}, "bk_lc": {}}
    for lc in LCS:
        t0 = time.time()
        pn.UserText = lc; pn.ExpireSolution(False); d.NewSolution(False)
        act = [bool(x.Value) for x in tce.Params.Output[2].VolatileData.AllData(True)]
        ids = [i for i in range(n) if act[i]]
        ins = list(bf.Params.Input); outs = list(bf.Params.Output)
        ins[2].RemoveAllSources(); ins[1].RemoveAllSources(); ins[1].PersistentData.Clear()
        ins[2].PersistentData.Clear(); ins[2].SetPersistentData(GH_String(lc)); bf.ExpireSolution(False); bf.CollectData(); bf.ComputeData()
        full = {}; red = {}
        for p in outs[1:7]:
            vals = [round(x.Value, 3) for x in p.VolatileData.AllData(True)]
            red[p.NickName] = vals
            f = [0.0] * (2 * n)
            for j, i in enumerate(ids):
                f[2 * i] = vals[2 * j]; f[2 * i + 1] = vals[2 * j + 1]
            full[p.NickName] = f
        R["full"][lc] = full; R["red"][lc] = red
        rins = list(rc.Params.Input); rins[2].RemoveAllSources(); rins[2].PersistentData.Clear(); rins[2].SetPersistentData(GH_String(lc))
        rc.ExpireSolution(False); rc.CollectData(); rc.ComputeData()
        o = list(rc.Params.Output)
        RF = [x.Value for x in o[1].VolatileData.AllData(True)]; RM = [x.Value for x in o[2].VolatileData.AllData(True)]
        R["reac"][lc] = {"RF": [(round(f.X, 2), round(f.Y, 2), round(f.Z, 2)) for f in RF], "RM": [(round(v.X, 2), round(v.Y, 2), round(v.Z, 2)) for v in RM]}
        k = LCS.index(lc)
        mdl = [x.Value for x in an.Params.Output[1].VolatileData.AllData(True)]; R["md"][lc] = mdl[k]
        fr = [x.Value for x in an.Params.Output[2].VolatileData.AllData(True)]; R["sumF"][lc] = (round(fr[k].X, 1), round(fr[k].Y, 1), round(fr[k].Z, 1))
        mdt = [x.Value for x in th.Params.Output[1].VolatileData.AllData(True)]; R["md2"][lc] = mdt[k]
        R["active"][lc] = act
        R["bk_lc"][lc] = [x.Value for x in comp(d, "Component_Buckling").Params.Output[1].VolatileData.AllData(True)][:3]
        log("%s %s: %d members removed, disp %.2f cm, %.0fs" % (tag, lc, n - len(ids), R["md"][lc], time.time() - t0))
    R["bk"] = R["bk_lc"]["LONG"]
    R["mass"] = [x.Value for x in asm.Params.Output[2].VolatileData.AllData(True)]
    pn.UserText = "LONG"; pn.ExpireSolution(False)
    return R


def write_main(R, roof):
    J = {"roof": roof, "model": "D2 final sizes 2026-11-27", "nodes": R["nodes"], "els": R["els"], "forces": R["full"], "reactions": R["reac"],
         "maxdisp_cm": R["md"], "maxdisp_ThII_cm": R["md2"], "sumF": R["sumF"], "buckling": R["bk"], "mass_kg": R["mass"], "active": R["active"], "crosec": R["crosec"]}
    json.dump(J, open(os.path.join(HERE, "forces-%s.json" % roof), "w"))


def write_formwork(R, roof, v):
    cases = {lc: {"forces": R["red"][lc], "RF": R["reac"][lc]["RF"], "active": R["active"][lc], "maxdisp_cm": R["md"][lc], "buckling": R["bk_lc"][lc], "tce_msgs": []} for lc in LCS}
    cs = {g: R["crosec"][g] for g in ("course", "fin")}
    json.dump({"roof": roof, "variant": v, "nodes": R["nodes"], "els": R["els"], "crosec": cs, "cases": cases}, open(os.path.join(HERE, "formwork", "forces-%s-%s.json" % (roof, v)), "w"))


def write_corner(R, roof, case, removed):
    json.dump({"nodes": R["nodes"], "els": R["els"], "forces": R["full"], "reactions": R["reac"], "removed": removed,
               "maxdisp_cm": R["md"], "maxdisp_ThII_cm": R["md2"], "sumF": R["sumF"], "buckling": R["bk"], "active": R["active"]},
              open(os.path.join(HERE, "corners", "forces-%s-%s.json" % (roof, case)), "w"))


def corner_xy(pts, roof):
    cx, cy = CEN[roof]; res = {}
    hx = max(abs(p.X - cx) for p in pts); hy = max(abs(p.Y - cy) for p in pts)
    for name, sx, sy in (("SW", -1, -1), ("SE", 1, -1), ("NE", 1, 1), ("NW", -1, 1)):
        res[name] = max(pts, key=lambda p: sx * (p.X - cx) / hx + sy * (p.Y - cy) / hy)
    return res


def take_out_corners(d, roof, corners):
    sup = [o for o in d.Objects if o.GetType().Name == "Param_Point" and ("column tops" in o.NickName or "column" in o.NickName)][0]
    col = [o for o in d.Objects if o.GetType().Name == "Param_Line" and o.NickName.startswith("column stubs")][0]
    vec = [o for o in d.Objects if o.GetType().Name == "Param_Vector" and o.NickName.startswith("column z-orientation")][0]
    pts = [g.Value for g in sup.PersistentData.AllData(True)]
    cxy = corner_xy(pts, roof); rem = [cxy[c] for c in corners]
    keep_pts = [p for p in pts if all(p.DistanceTo(r) > 0.05 for r in rem)]
    lines = [g.Value for g in col.PersistentData.AllData(True)]; vecs = list(vec.PersistentData.AllData(True))
    keep = [(l, v) for l, v in zip(lines, vecs) if all(math.hypot(l.From.X - r.X, l.From.Y - r.Y) > 0.05 for r in rem)]
    sup.PersistentData.Clear(); [sup.PersistentData.Append(GH_Point(p)) for p in keep_pts]
    col.PersistentData.Clear(); [col.PersistentData.Append(GH_Line(l)) for l, v in keep]
    vec.PersistentData.Clear(); [vec.PersistentData.Append(v) for l, v in keep]
    for p in (sup, col, vec): p.ExpireSolution(False)
    d.NewSolution(True)
    return [(r.X, r.Y) for r in rem], len(keep_pts), len(keep)


def jobs():
    for roof in ("15x10", "10x10"):
        yield ("main", roof, None)
        yield ("D1", roof, None)
        for case, corners in CASES[1:]:
            yield ("corner", roof, (case, corners))


def do(job):
    kind, roof, extra = job; t0 = time.time()
    d = open_doc(canvas(roof))
    if kind == "main":
        R = solve(d, roof + " D2"); write_main(R, roof); write_formwork(R, roof, "D2"); write_corner(R, roof, "0", [])
    elif kind == "D1":
        setnum(d, "Printed course", "Young", 2500.0); setnum(d, "Printed course", "In-plane Shear", 1041.6666666666667); setnum(d, "Printed course", "Transverse Shear", 1041.6666666666667)
        d.NewSolution(True); R = solve(d, roof + " D1"); write_formwork(R, roof, "D1")
    else:
        case, corners = extra
        rem, ns, nl = take_out_corners(d, roof, corners)
        R = solve(d, "%s corners %s" % (roof, case)); write_corner(R, roof, case, rem)
        p = os.path.join(PF, "stepped-%s-karamba-2m-corners-%s-2026-11-27.gh" % (roof, case)); d.FilePath = p; GH_DocumentIO(d).SaveQuiet(p)
        log("%s corners %s: supports %d, column bars %d" % (roof, case, ns, nl))
    Grasshopper.Instances.DocumentServer.RemoveDocument(d)
    log("DONE %s %s %s in %.0fs" % (kind, roof, extra[0] if extra else "", time.time() - t0))


_state = {"it": None, "busy": False}


def _idle(sender, e):
    if _state["busy"]: return
    _state["busy"] = True
    try:
        job = next(_state["it"])
        try: do(job)
        except Exception as ex:
            import traceback; log("ERROR %s: %s" % (job[:2], traceback.format_exc()))
    except StopIteration:
        Rhino.RhinoApp.Idle -= _idle; log("ALL DONE")
    finally:
        _state["busy"] = False


def start(only=None):
    open(LOG, "w").close()
    js = list(jobs())
    if only: js = [j for j in js if only(j)]
    _state["it"] = iter(js)
    Rhino.RhinoApp.Idle += _idle
    log("started %d jobs" % len(js))
