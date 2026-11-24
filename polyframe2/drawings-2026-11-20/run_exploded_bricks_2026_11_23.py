"""Exploded axon of the 15x10 with the printed courses taken apart too (Gonzalo 2026-11-23: "explode the bricks as
well"). Same view and groups as run_exploded_2026_11_23.py; each course is lifted COURSE_GAP above the one below and
each piece (with its growth band) is pulled PULL out from the roof centre in plan, so courses and head joints open up.
In memory only: current.3dm is not changed. Output: exploded-15x10-bricks.json (layer per course)."""
import importlib.util, json, os, math
import Rhino, Rhino.Geometry as G

P = r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\polyframe2\drawings-2026-11-20"
OUT = r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\details\exploded-2026-11-23"
spec = importlib.util.spec_from_file_location("rx", os.path.join(P, "run_extract.py"))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
X = m.X
KFORCES = r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\details\karamba\2026-11-23\forces-%s.json"
GAP, COURSE_GAP, PULL = 1.2, 0.30, 0.15


def run(doc, roof="15x10"):
    cx, cy = {"15x10": (85.0, 0.0), "10x10": (85.0, -20.0)}[roof]
    objs = X.final_objects(doc, roof)
    pick = lambda keys: [(ln, g) for ln, g in objs if X.short(ln) in keys and (keys != ("printed pieces",) or "growth" not in ln.lower())]
    footing = pick(("footing",)); cols = pick(("columns",)); ring = pick(("base ring formwork", "base ring cast")); ribs = pick(("rib cores",)); tubes = pick(("ribs",))
    pieces = [(ln, g) for ln, g in objs if X.short(ln) == "printed pieces" and "growth" not in ln.lower()]
    bands = [(ln, g) for ln, g in objs if "growth bands" in ln.lower()]
    crown = pick(("crown ring cast", "crown ring printed band", "top course U formwork"))
    top = lambda grp: max(g.GetBoundingBox(True).Max.Z for _, g in grp)
    bot = lambda grp: min(g.GetBoundingBox(True).Min.Z for _, g in grp)
    L = {"rectangular strip footing": 0.0}
    L["columns"] = (top(footing) + GAP) - bot(cols)
    L["base ring step"] = (top(cols) + L["columns"] + GAP) - bot(ring)
    L["rib net"] = (top(ring) + L["base ring step"] + GAP) - bot(ribs)
    # courses: cluster the pieces by their bottom level
    levels = sorted(set(round(g.GetBoundingBox(True).Min.Z, 2) for _, g in pieces))
    L["rib formwork"] = (top(ribs) + L["rib net"] + GAP) - bot(tubes)
    L["printed courses"] = (top(tubes) + L["rib formwork"] + COURSE_GAP * (len(levels) - 1) + GAP) - bot(pieces)
    course = lambda z: min(range(len(levels)), key=lambda i: abs(levels[i] - z))
    pc = [(course(g.GetBoundingBox(True).Min.Z), g, g.GetBoundingBox(True).Center) for _, g in pieces]
    L["crown ring"] = (top(pieces) + L["printed courses"] + COURSE_GAP * (len(levels) - 1) + GAP) - bot(crown)
    lifted = []

    def add(layer, g, dz, dx=0.0, dy=0.0):
        h = g.DuplicateBrep(); h.Transform(G.Transform.Translation(dx, dy, dz)); lifted.append((layer, h))

    for name, grp in (("rectangular strip footing", footing), ("columns", cols), ("base ring step", ring), ("crown ring", crown)):
        for _, g in grp: add(name, g, L[name])
    # rib rebar instead of the cast cores (Gonzalo 2026-11-23): 2 bars per rib on the Karamba rib centrelines, offset
    # sideways in the shell by (core radius - 40 mm cover); a single centreline where that is under 30 mm
    K = json.load(open(KFORCES % roof))
    OFF = {"15x10": {"rib_bottom": 0.07, "rib_middle": 0.04, "rib_top": 0.02}, "10x10": {"rib_bottom": 0.05, "rib_middle": 0.03, "rib_top": 0.02}}[roof]
    nbar = 0
    for gname, a, b in K["els"]:
        if not gname.startswith("rib"): continue
        pa, pb = G.Point3d(*K["nodes"][a]), G.Point3d(*K["nodes"][b])
        ax = pb - pa; ax.Unitize()
        mid = (pa + pb) / 2; rad = G.Vector3d(mid.X - cx, mid.Y - cy, 0); rad.Unitize()
        side = G.Vector3d.CrossProduct(ax, rad); side.Unitize()
        o = OFF[gname]
        for sgn in ((1, -1) if o >= 0.03 else (0,)):
            v = side * (sgn * o) + G.Vector3d(0, 0, L["rib net"])
            lifted.append(("rib rebar", G.LineCurve(pa + v, pb + v))); nbar += 1

    def pull(c):
        vx, vy = c.X - cx, c.Y - cy; r = math.hypot(vx, vy) or 1.0
        return PULL * vx / r, PULL * vy / r

    # printed rib tubes cut at the course joints (as printed with each course), exploded with the same course lifts
    ntube = 0
    for _, t in tubes:
        tb = t.GetBoundingBox(True)
        for k in range(len(levels)):
            z0 = levels[k] if k else -10.0; z1 = levels[k + 1] if k + 1 < len(levels) else 99.0
            if tb.Max.Z <= z0 or tb.Min.Z >= z1: continue
            if tb.Min.Z >= z0 and tb.Max.Z <= z1:
                parts = [t]
            else:
                box = G.Box(G.BoundingBox(G.Point3d(tb.Min.X - 1, tb.Min.Y - 1, z0), G.Point3d(tb.Max.X + 1, tb.Max.Y + 1, z1))).ToBrep()
                parts = G.Brep.CreateBooleanIntersection(t, box, 0.001) or []
            for q in parts:
                add("rib formwork/course %02d" % (k + 1), q, L["rib formwork"] + COURSE_GAP * k); ntube += 1
    for k, g, c in pc:
        dx, dy = pull(c); add("printed courses/course %02d" % (k + 1), g, L["printed courses"] + COURSE_GAP * k, dx, dy)
    for _, b in bands:                               # each growth band goes with the nearest piece
        cb = b.GetBoundingBox(True).Center
        k, g, c = min(pc, key=lambda t: t[2].DistanceTo(cb))
        dx, dy = pull(c); add("printed courses/course %02d" % (k + 1), b, L["printed courses"] + COURSE_GAP * k, dx, dy)
    # label anchors (south-east outer corner at mid height of each lifted group)
    marks = {}
    for name, grp in (("rectangular strip footing", footing), ("columns", cols), ("base ring step", ring), ("rib rebar", ribs), ("rib formwork", tubes), ("printed courses", pieces), ("crown ring", crown)):
        bb = G.BoundingBox.Empty
        for _, g in grp: bb.Union(g.GetBoundingBox(True))
        extra = COURSE_GAP * (len(levels) - 1) / 2 if name in ("printed courses", "rib formwork") else 0.0
        marks[name] = G.Point3d(bb.Max.X + (PULL if name == "printed courses" else 0), bb.Min.Y, (bb.Min.Z + bb.Max.Z) / 2 + L["rib net" if name == "rib rebar" else name] + extra)
    d = G.Vector3d(1, 1, -1); d.Unitize()
    vis = X.hld(lifted, d, G.Vector3d(0, 0, 1), G.Point3d(cx, cy, 10), lambda q: (q.X, q.Y))
    # project the anchors with the same view (parallel): screen axes from the view direction
    right = G.Vector3d.CrossProduct(d, G.Vector3d(0, 0, 1)); right.Unitize(); up = G.Vector3d.CrossProduct(right, d); up.Unitize()
    t0 = G.Point3d(cx, cy, 10)
    anchors = {n: [round((p - t0) * right, 4), round((p - t0) * up, 4)] for n, p in marks.items()}
    height = top(crown) + L["crown ring"] - bot(footing)
    json.dump({"roof": roof, "units": "m", "view": "parallel, from the south-west and above (direction 1,1,-1), z up; 2D screen coordinates",
               "groups": [(n, round(v, 2)) for n, v in L.items()], "course_gap_m": COURSE_GAP, "piece_pull_m": PULL, "courses": len(levels),
               "exploded_height_m": round(height, 2), "anchors": anchors, "items": X.dedupe(vis)},
              open(os.path.join(OUT, "exploded-%s-bricks.json" % roof), "w"), separators=(",", ":"))
    m.log("exploded bricks %s: %d lines, %d courses, %d tube parts, %d rebar lines, height %.1f m" % (roof, len(vis), len(levels), ntube, nbar, height))
