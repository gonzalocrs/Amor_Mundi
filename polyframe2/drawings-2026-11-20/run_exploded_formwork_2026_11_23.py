"""Exploded axon of the 15x10 showing the printed 3D formwork (Gonzalo 2026-11-23: "i wanna see the exploded printed
3d formwork"). Each printed piece goes with its growth band and its rib-tube segments (printed as one piece), courses
lifted COURSE_GAP apart, pieces pulled PULL out. Cutaway: only the far (north-east) half of every course is kept, so
from the south-west we look into the room face and see the tube channels. Rib rebar under it, far half too.
In memory only: current.3dm is not changed. Output: exploded-15x10-formwork.json (+ marks for the Arctic snapshot)."""
import importlib.util, json, os, math
import Rhino, Rhino.Geometry as G

P = r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\polyframe2\drawings-2026-11-20"
OUT = r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\details\exploded-2026-11-23"
KF = r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\details\karamba\2026-11-23\forces-%s.json"
spec = importlib.util.spec_from_file_location("rx", os.path.join(P, "run_extract.py"))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
X = m.X
GAP, COURSE_GAP, PULL = 1.0, 1.20, 0.15
MODE = "rings"          # "cutaway": far half only; "faces": the roof split into its 4 faces, pulled apart
FACE_PULL = 3.5
REBAR_EXTRA = 2.0
NEAR_PULL = 4.0          # the south-west quarter (facing the viewer) is pulled further so it hides less


def build(doc, roof="15x10"):
    cx, cy = {"15x10": (85.0, 0.0), "10x10": (85.0, -20.0)}[roof]
    objs = X.final_objects(doc, roof)
    sel = lambda keys: [g for ln, g in objs if X.short(ln) in keys]
    footing = sel(("footing",)); cols = sel(("columns",)); ring = sel(("base ring formwork", "base ring cast"))
    pieces = [g for ln, g in objs if X.short(ln) == "printed pieces" and "growth" not in ln.lower()]
    bands = [g for ln, g in objs if "growth bands" in ln.lower()]
    tubes = sel(("ribs",)); cores = sel(("rib cores",))
    crown = sel(("crown ring cast", "crown ring printed band", "top course U formwork"))
    bbx = lambda gs: [g.GetBoundingBox(True) for g in gs]
    top = lambda gs: max(b.Max.Z for b in bbx(gs)); bot = lambda gs: min(b.Min.Z for b in bbx(gs))
    hx = max(abs(b.Center.X - cx) for b in bbx(pieces)); hy = max(abs(b.Center.Y - cy) for b in bbx(pieces))
    far = (lambda p: True) if MODE in ("faces", "quarters", "rings") else (lambda p: (p.X - cx) / hx + (p.Y - cy) / hy > 0.0)   # cutaway: north-east half
    def face(p):
        if MODE == "quarters":                      # quarters along the two plan axes, pulled out diagonally
            sx, sy = math.copysign(1, p.X - cx), math.copysign(1, p.Y - cy)
            k = (NEAR_PULL if (sx < 0 and sy < 0) else FACE_PULL) / math.sqrt(2)
            return (sx * k, sy * k)
        nx, ny = (p.X - cx) / hx, (p.Y - cy) / hy   # faces: the 4 roof faces, split along the hips (plan diagonals)
        return (math.copysign(FACE_PULL, nx), 0.0) if abs(nx) >= abs(ny) else (0.0, math.copysign(FACE_PULL, ny))
    fp = face if MODE in ("quarters", "faces") else (lambda p: (0.0, 0.0))
    L = {"rectangular strip footing": 0.0}
    L["columns"] = top(footing) + GAP - bot(cols)
    L["base ring step"] = top(cols) + L["columns"] + GAP - bot(ring)
    L["rib rebar"] = top(ring) + L["base ring step"] + GAP + REBAR_EXTRA - 2.4      # extra so the net clears the ring in the view
    raw = sorted(b.Min.Z for b in bbx(pieces)); levels = []
    for z in raw:                                   # cluster the piece bases into courses (5 cm tolerance)
        if not levels or z - levels[-1] > 0.05: levels.append(z)
    L["printed formwork"] = top(cores) + L["rib rebar"] + GAP - bot(pieces)
    L["crown ring"] = top(pieces) + L["printed formwork"] + COURSE_GAP * (len(levels) - 1) + GAP - bot(crown)
    course = lambda z: min(range(len(levels)), key=lambda i: abs(levels[i] - z))
    out = []

    def add(layer, g, dz, dx=0.0, dy=0.0):
        h = g.DuplicateBrep() if isinstance(g, G.Brep) else g.Duplicate()
        h.Transform(G.Transform.Translation(dx, dy, dz)); out.append((layer, h))

    for name, grp in (("rectangular strip footing", footing), ("columns", cols), ("base ring step", ring)):
        for g in grp: add(name, g, L[name])
    # crown ring + top-course U: cut into the same four quarters (boolean with quadrant boxes) and pulled with them
    for g in crown:
        bb = g.GetBoundingBox(True)
        if MODE == "faces":                        # cut by the four hip wedges (triangles from the centre to the corners)
            corners = [(-hx * 3, -hy * 3), (hx * 3, -hy * 3), (hx * 3, hy * 3), (-hx * 3, hy * 3)]
            for i in range(4):
                a, b = corners[i], corners[(i + 1) % 4]
                tri = G.Polyline([G.Point3d(cx, cy, bb.Min.Z - 1), G.Point3d(cx + a[0], cy + a[1], bb.Min.Z - 1), G.Point3d(cx + b[0], cy + b[1], bb.Min.Z - 1), G.Point3d(cx, cy, bb.Min.Z - 1)])
                wedge = G.Extrusion.Create(tri.ToNurbsCurve(), bb.Max.Z - bb.Min.Z + 2, True).ToBrep()
                if wedge.SolidOrientation == G.BrepSolidOrientation.Inward: wedge.Flip()
                mid = G.Point3d(cx + (a[0] + b[0]) / 2, cy + (a[1] + b[1]) / 2, 0)
                fx, fy = face(mid)
                for q in (G.Brep.CreateBooleanIntersection(g, wedge, 0.001) or []): add("crown ring", q, L["crown ring"], fx, fy)
            continue
        if MODE != "quarters":
            add("crown ring", g, L["crown ring"]); continue
        for sx in (-1, 1):
            for sy in (-1, 1):
                qb = G.Box(G.BoundingBox(G.Point3d(min(cx, cx + sx * 20), min(cy, cy + sy * 20), bb.Min.Z - 1), G.Point3d(max(cx, cx + sx * 20), max(cy, cy + sy * 20), bb.Max.Z + 1))).ToBrep()
                for q in (G.Brep.CreateBooleanIntersection(g, qb, 0.001) or []):
                    fx, fy = face(G.Point3d(cx + sx, cy + sy, 0)); add("crown ring", q, L["crown ring"], fx, fy)
    # printed formwork: piece + growth band + tube segments of that course next to it, moved together; far half only
    allpc = []
    for g in pieces:
        b = g.GetBoundingBox(True)
        allpc.append((course(b.Min.Z), g, b.Center))
    pc = [t for t in allpc if far(t[2])]          # the cut is decided by the piece; its band and tubes follow it

    def mv(c):
        vx, vy = c.X - cx, c.Y - cy; r = math.hypot(vx, vy) or 1.0
        fx, fy = fp(c)
        return PULL * vx / r + fx, PULL * vy / r + fy

    def owner(c, k=None):
        cand = [t for t in allpc if k is None or t[0] == k] or allpc
        return min(cand, key=lambda t: t[2].DistanceTo(c))

    for k, g, c in pc:
        dx, dy = mv(c); add("printed formwork/course %02d" % (k + 1), g, L["printed formwork"] + COURSE_GAP * k, dx, dy)
    for b in bands:
        cb = b.GetBoundingBox(True).Center
        k, g, c = owner(cb)
        if not far(c): continue
        dx, dy = mv(c); add("printed formwork/course %02d" % (k + 1), b, L["printed formwork"] + COURSE_GAP * k, dx, dy)
    ntube = 0
    for t in tubes:
        tb = t.GetBoundingBox(True)
        for k in range(len(levels)):
            z0 = levels[k] if k else -10.0; z1 = levels[k + 1] if k + 1 < len(levels) else 99.0
            if tb.Max.Z <= z0 or tb.Min.Z >= z1: continue
            if tb.Min.Z >= z0 and tb.Max.Z <= z1: parts = [t]
            else:
                box = G.Box(G.BoundingBox(G.Point3d(tb.Min.X - 1, tb.Min.Y - 1, z0), G.Point3d(tb.Max.X + 1, tb.Max.Y + 1, z1))).ToBrep()
                parts = G.Brep.CreateBooleanIntersection(t, box, 0.001) or []
            for q in parts:
                qc = q.GetBoundingBox(True).Center
                kk, g, c = owner(qc, k)
                if not far(c): continue
                dx, dy = mv(c)
                add("printed formwork/course %02d" % (k + 1), q, L["printed formwork"] + COURSE_GAP * k, dx, dy); ntube += 1
    # rib rebar, far half
    K = json.load(open(KF % roof))
    OFF = {"15x10": {"rib_bottom": 0.07, "rib_middle": 0.04, "rib_top": 0.02}, "10x10": {"rib_bottom": 0.05, "rib_middle": 0.03, "rib_top": 0.02}}[roof]
    for gname, a, b in K["els"]:
        if not gname.startswith("rib"): continue
        pa, pb = G.Point3d(*K["nodes"][a]), G.Point3d(*K["nodes"][b])
        if not far((pa + pb) / 2): continue
        ax = pb - pa; ax.Unitize(); md = (pa + pb) / 2; rad = G.Vector3d(md.X - cx, md.Y - cy, 0); rad.Unitize()
        side = G.Vector3d.CrossProduct(ax, rad); side.Unitize(); o = OFF[gname]
        for sgn in ((1, -1) if o >= 0.03 else (0,)):
            fx, fy = fp((pa + pb) / 2)
            v = side * (sgn * o) + G.Vector3d(fx, fy, L["rib rebar"]); out.append(("rib rebar", G.LineCurve(pa + v, pb + v)))
    # anchor points (south-east outer corner at mid height of each lifted group)
    def mark(gs, name, extra=0.0, pull=0.0):
        bb = G.BoundingBox.Empty
        for g in gs: bb.Union(g.GetBoundingBox(True))
        return G.Point3d(bb.Max.X + pull, bb.Min.Y, (bb.Min.Z + bb.Max.Z) / 2 + L[name] + extra)
    marks = {"rectangular strip footing": mark(footing, "rectangular strip footing"), "columns": mark(cols, "columns"), "base ring step": mark(ring, "base ring step"),
             "rib rebar": mark(cores, "rib rebar"), "printed formwork": mark(pieces, "printed formwork", COURSE_GAP * (len(levels) - 1) / 2, PULL), "crown ring": mark(crown, "crown ring")}
    height = top(crown) + L["crown ring"] - bot(footing)
    return out, L, marks, len(levels), ntube, height, (cx, cy)


def run(doc, roof="15x10"):
    out, L, marks, ncourse, ntube, height, (cx, cy) = build(doc, roof)
    d = G.Vector3d(1, 1, -1); d.Unitize()
    vis = X.hld(out, d, G.Vector3d(0, 0, 1), G.Point3d(cx, cy, 10), lambda q: (q.X, q.Y))
    right = G.Vector3d.CrossProduct(d, G.Vector3d(0, 0, 1)); right.Unitize(); up = G.Vector3d.CrossProduct(right, d); up.Unitize()
    t0 = G.Point3d(cx, cy, 10)
    anchors = {n: [round((p - t0) * right, 4), round((p - t0) * up, 4)] for n, p in marks.items()}
    for it in vis: it["pts"] = [[round(p[0], 4), round(p[1], 4)] for p in it["pts"]]
    json.dump({"roof": roof, "units": "m", "view": "parallel, from the south-west and above (direction 1,1,-1), z up; 2D screen coordinates",
               "groups": [(n, round(v, 2)) for n, v in L.items()], "course_gap_m": COURSE_GAP, "piece_pull_m": PULL, "courses": ncourse,
               "cutaway": "printed formwork and rib rebar: north-east half only (the half facing away from the viewer), so the room face and tube channels show",
               "exploded_height_m": round(height, 2), "anchors": anchors, "items": X.dedupe(vis)},
              open(os.path.join(OUT, "exploded-%s-%s.json" % (roof, {"faces": "formwork-v3", "quarters": "formwork-v3-quarters", "rings": "formwork-v4"}.get(MODE, "formwork"))), "w"), separators=(",", ":"))
    m.log("exploded formwork %s: %d lines, %d courses, %d tube parts, height %.1f m" % (roof, len(vis), ncourse, ntube, height))
