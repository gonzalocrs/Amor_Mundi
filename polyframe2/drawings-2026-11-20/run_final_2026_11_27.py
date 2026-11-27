"""2026-11-27 final model (stepped-roofs-final-2026-11-27.3dm): base ring grown 60 / 62 mm inward, columns 420 x 360 /
362 x 300 (long side radial), strip footing shifted 30 mm inward, corner band joints fixed. Refreshes, with the same
calls as the 2026-11-23 sheets, everything those changes touch and keeps the rest of linework-<roof>.json:
  plan: columns cut at +1.20, footing outline below ground (-0.55), base ring outlines above (+2.20);
  elevation: columns; section: whole re-cut 0.10 m north of the centre line (as on 2026-11-23, 'ring edges kept');
  then the axon iso, worm's-eye and roof-from-below Make2D (run_extract.axon / axon_worm_v3 / bottom_v3).
Runs in Rhino with the final model's layers visible. Backups: linework-<roof>-before-final-2026-11-27.json."""
import importlib.util, json, os, shutil
import Rhino, Rhino.Geometry as G

P = r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\polyframe2\drawings-2026-11-20"
spec = importlib.util.spec_from_file_location("rx", os.path.join(P, "run_extract.py"))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
X = m.X; log = m.log
asm = importlib.util.spec_from_file_location("asm", os.path.join(P, "assemble.py")); A = importlib.util.module_from_spec(asm); asm.loader.exec_module(A)
SECT_OFF = 0.10
STRUCT = {"15x10": "20 columns 420 (radial) x 360, base ring 528 x 400 (cast, typical), rectangular strip footing 1.20 m wide x 0.5 with square corner blocks (30 mm inward of 2026-11-23)",
          "10x10": "16 columns 362 (radial) x 300, base ring 552 x 400 (cast, typical), rectangular strip footing 0.85 m wide x 0.5 with square corner blocks (30 mm inward of 2026-11-23)"}


def patch(doc, roof):
    cx, cy = X.ROOFS[roof]
    path = os.path.join(P, "linework-%s.json" % roof)
    bk = path.replace(".json", "-before-final-2026-11-27.json")
    if not os.path.exists(bk): shutil.copy(path, bk)
    D = json.load(open(bk)); dr = D["drawings"]
    objs = X.final_objects(doc, roof)
    cols = [o for o in objs if X.short(o[0]) == "columns"]
    foot = [o for o in objs if X.short(o[0]) == "footing"]
    ring = [o for o in objs if X.short(o[0]) in ("base ring formwork", "base ring cast")]
    xy = lambda q: (q.X - cx, q.Y - cy)
    pc = X.plane_cut(cols, G.Plane(G.Point3d(0, 0, dr["plan"]["cut_height"]), G.Vector3d.ZAxis), xy)
    dr["plan"]["cut"] = [i for i in dr["plan"]["cut"] if i["layer"] != "columns"] + pc
    pb = X.plane_cut(foot, G.Plane(G.Point3d(0, 0, -0.55), G.Vector3d.ZAxis), xy)
    for i in pb: i["layer"] = "footing (below ground)"
    dr["plan"]["below"] = [i for i in dr["plan"]["below"] if not i["layer"].startswith("footing")] + pb
    ra = X.dedupe(X.plane_cut(ring, G.Plane(G.Point3d(0, 0, 2.2), G.Vector3d.ZAxis), xy))
    for i in ra: i["layer"] = "base ring (above)"
    dr["plan"]["above"] = [i for i in dr["plan"]["above"] if i["layer"] != "base ring (above)"] + ra
    ev = A.clip_above(X.dedupe(X.hld(cols, G.Vector3d(0, 1, 0), G.Vector3d(0, 0, 1), G.Point3d(cx, cy, 5), lambda q: (q.X, q.Y + 5))))
    dr["elevation"]["visible"] = [i for i in dr["elevation"]["visible"] if i["layer"] != "columns"] + ev
    m.sect(doc, roof, SECT_OFF)
    se = json.load(open(os.path.join(P, "_tmp_%s_sect.json" % roof)))
    gl = [i for i in dr["section"]["beyond"] if i["layer"] == "ground line"]
    dr["section"]["cut"] = se["cut"]
    dr["section"]["beyond"] = A.clip_above(se["beyond"]) + gl
    dr["section"]["beyond_clean"] = A.clean_beyond(dr["section"]["beyond"])
    D["source"] = D["source"].split(" @ ")[0] + " @ 2026-11-27 final (stepped-roofs-final-2026-11-27.3dm)"
    D["structure"] = STRUCT[roof]
    D["extents"] = {k: A.ext([i for grp in v.values() if isinstance(grp, list) for i in grp]) for k, v in dr.items()}
    json.dump(D, open(path, "w"), separators=(",", ":"))
    log("%s final patch: plan cut %d, below %d, ring above %d, elev cols %d, sect cut %d, beyond %d" % (roof, len(pc), len(pb), len(ra), len(ev), len(se["cut"]), len(se["beyond"])))


def run(doc):
    for roof in ("15x10", "10x10"):
        patch(doc, roof)
    m.axon(doc, "iso", (-1, 1, -1), (0, 0, 1))
    m.axon_worm_v3(doc)
    for roof in ("15x10", "10x10"):
        m.bottom_v3(doc, roof)
    log("final 2026-11-27 refresh done")
