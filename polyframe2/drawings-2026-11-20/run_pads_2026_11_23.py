"""2026-11-23 option A (20/16 columns on pad footings): refresh the linework that shows columns and footings, from the
new current.3dm. Runs in Rhino (scheduled on Idle). Re-runs the axon iso / worm's-eye / roof-from-below Make2D with the
same calls as v10, and replaces only the 'columns' and 'footing' items in linework-<roof>.json (plan cut at +1.20,
plan footing outlines below ground, elevation, section cut and section beyond). Everything else is kept as it is."""
import importlib.util, json, os, time, shutil
import Rhino, Rhino.Geometry as G

P = r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\polyframe2\drawings-2026-11-20"
spec = importlib.util.spec_from_file_location("rx", os.path.join(P, "run_extract.py"))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
X = m.X
log = m.log
BACKUP_TAG = "pads"


def colfoot(doc, roof):
    return [o for o in X.final_objects(doc, roof) if X.short(o[0]) in ("columns", "footing")]


def patch_linework(doc, roof, sect_off):
    cx, cy = X.ROOFS[roof]
    path = os.path.join(P, "linework-%s.json" % roof)
    shutil.copy(path, path.replace(".json", "-before-%s.json" % BACKUP_TAG))
    D = json.load(open(path))
    objs = colfoot(doc, roof)
    cols = [o for o in objs if X.short(o[0]) == "columns"]
    foot = [o for o in objs if X.short(o[0]) == "footing"]
    dr = D["drawings"]
    # plan: columns cut at the plan cut height, footings as outlines below ground
    pc = X.plane_cut(cols, G.Plane(G.Point3d(0, 0, dr["plan"]["cut_height"]), G.Vector3d.ZAxis), lambda q: (q.X - cx, q.Y - cy))
    dr["plan"]["cut"] = [i for i in dr["plan"]["cut"] if i["layer"] != "columns"] + pc
    pb = X.plane_cut(foot, G.Plane(G.Point3d(0, 0, -0.55), G.Vector3d.ZAxis), lambda q: (q.X - cx, q.Y - cy))
    for i in pb: i["layer"] = "footing (below ground)"
    dr["plan"]["below"] = [i for i in dr["plan"]["below"] if not i["layer"].startswith("footing")] + pb
    # elevation (looking +Y): columns hide only each other below the ring; keep the part above ground
    asm = importlib.util.spec_from_file_location("asm", os.path.join(P, "assemble.py")); A = importlib.util.module_from_spec(asm); asm.loader.exec_module(A)
    ev = A.clip_above(X.dedupe(X.hld(cols, G.Vector3d(0, 1, 0), G.Vector3d(0, 0, 1), G.Point3d(cx, cy, 5), lambda q: (q.X, q.Y + 5))))
    dr["elevation"]["visible"] = [i for i in dr["elevation"]["visible"] if i["layer"] != "columns"] + ev
    # section: cut and beyond
    pl = G.Plane(G.Point3d(cx, cy + sect_off, 0), G.Vector3d(0, 1, 0))
    sc = X.dedupe(X.plane_cut(objs, pl, lambda q: (q.X - cx, q.Z)))
    dr["section"]["cut"] = [i for i in dr["section"]["cut"] if i["layer"] not in ("columns", "footing")] + sc
    bv = A.clip_above(X.dedupe(X.hld(cols, G.Vector3d(0, 1, 0), G.Vector3d(0, 0, 1), G.Point3d(cx, cy, 5), lambda q: (q.X, q.Y + 5),
                                     clip=G.Plane(G.Point3d(cx, cy + sect_off, 0), G.Vector3d(0, -1, 0)))))
    for k in ("beyond", "beyond_clean"):
        if k in dr["section"]:
            dr["section"][k] = [i for i in dr["section"][k] if i["layer"] != "columns"] + bv
    D["source"] = D["source"].split(" @ ")[0] + " @ 2026-11-23 columns + rectangular strip footing"
    D["structure"] = {"15x10": "20 columns 36 x 36, rectangular strip footing 1.20 m wide x 0.5 with square corner blocks",
                      "10x10": "16 columns 30 x 30, rectangular strip footing 0.85 m wide x 0.5 with square corner blocks"}[roof]
    D["extents"] = {k: A.ext([i for grp in v.values() if isinstance(grp, list) for i in grp]) for k, v in dr.items()}
    json.dump(D, open(path, "w"), separators=(",", ":"))
    log("%s linework patched: plan cut %d, below %d, elev %d, sect cut %d, beyond %d" % (roof, len(pc), len(pb), len(ev), len(sc), len(bv)))


def run(doc, sect_off):
    for roof in ("15x10", "10x10"):
        patch_linework(doc, roof, sect_off)
    m.axon(doc, "iso", (-1, 1, -1), (0, 0, 1))
    m.axon_worm_v3(doc)
    for roof in ("15x10", "10x10"):
        m.bottom_v3(doc, roof)
    log("pads refresh done")
