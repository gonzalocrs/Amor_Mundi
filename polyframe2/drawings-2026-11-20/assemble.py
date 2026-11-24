"""Assemble the per-roof JSON, DXFs (mm, one per drawing) and PNG previews from the _tmp_*.json pieces."""
import json, os, math
P = r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\polyframe2\drawings-2026-11-20"

def ext(items):
    xs = [p[0] for i in items for p in i["pts"]]; ys = [p[1] for i in items for p in i["pts"]]
    return [min(xs), min(ys), max(xs), max(ys)] if xs else None

def clip_above(items, z0=0.0):
    """keep only the parts of open polylines at z >= z0 (elevation and section-beyond: the ground hides the rest)"""
    out = []
    for it in items:
        pts = it["pts"]; cur = []
        segs = list(zip(pts, pts[1:])) + ([(pts[-1], pts[0])] if it["closed"] else [])
        for a, b in segs:
            ia, ib = a[1] >= z0 - 1e-6, b[1] >= z0 - 1e-6
            if ia and ib:
                if not cur: cur = [a]
                cur.append(b)
            elif ia or ib:
                t = (z0 - a[1]) / (b[1] - a[1]); m = [round(a[0] + t * (b[0] - a[0]), 4), z0]
                if ia:
                    if not cur: cur = [a]
                    cur.append(m); out.append({"layer": it["layer"], "pts": cur, "closed": False}); cur = []
                else:
                    cur = [m, b]
            else:
                if len(cur) > 1: out.append({"layer": it["layer"], "pts": cur, "closed": False})
                cur = []
        if len(cur) > 1:
            out.append({"layer": it["layer"], "pts": cur, "closed": False if len(cur) != len(pts) + (1 if it["closed"] else 0) else it["closed"]})
    return out

SOURCE = {"15x10": "final v3e layers (15x10 complete v3e-ring-step, visible sublayers) = stepped-15x10-10x10-v3e-current.3dm @ 7d1fae3",
          "10x10": "final v3e layers (10x10 complete v3e-ring-step, visible sublayers) = stepped-15x10-10x10-v3e-current.3dm @ 7d1fae3",
          "15x10-half": "0.25 m half-steps variant (layer 15x10 half-steps (0.25), visible sublayers), stepped-15x10-10x10-v3e-half-steps.3dm",
          "10x10-half": "0.25 m half-steps variant (layer 10x10 half-steps (0.25), visible sublayers), stepped-15x10-10x10-v3e-half-steps.3dm"}
PRINTED = ("printed pieces", "top course U formwork")

def clean_beyond(items, horiz=0.1):
    """section beyond without the facet / head-joint edges on the printed pieces' room face: for printed pieces and the
    top course keep only near-horizontal runs (course and step lines); every other element (ribs, rings, columns) is kept."""
    out = []
    for it in items:
        if it["layer"] not in PRINTED:
            out.append(it); continue
        pts = it["pts"]; cur = []
        for a, b in zip(pts, pts[1:]):
            dx, dz = b[0] - a[0], b[1] - a[1]
            if abs(dz) <= horiz * max(abs(dx), 1e-9):
                if not cur: cur = [a]
                cur.append(b)
            else:
                if len(cur) > 1: out.append({"layer": it["layer"], "pts": cur, "closed": False})
                cur = []
        if len(cur) > 1: out.append({"layer": it["layer"], "pts": cur, "closed": False})
    return out

def build(roof, levels):
    pl = json.load(open(os.path.join(P, "_tmp_%s_plan.json" % roof)))
    el = json.load(open(os.path.join(P, "_tmp_%s_elev.json" % roof)))
    se = json.load(open(os.path.join(P, "_tmp_%s_sect.json" % roof)))
    e_all = el["visible"]
    x0, _, x1, _ = ext(e_all)
    ground = {"layer": "ground line", "pts": [[round(x0 - 1.0, 3), 0.0], [round(x1 + 1.0, 3), 0.0]], "closed": False}
    el["visible"] = clip_above(e_all) + [ground]
    se["beyond"] = clip_above(se["beyond"]) + [dict(ground)]
    se["beyond_clean"] = clean_beyond(se["beyond"])
    rp = os.path.join(P, "_tmp_%s_ribs.json" % roof)
    if os.path.exists(rp):
        rb = json.load(open(rp))
        pl["ribs_outline"], pl["ribs_axis"] = rb["plan_ribs_outline"], rb["plan_ribs_axis"]
        se["ribs_outline"], se["ribs_axis"] = rb["section_ribs_outline"], rb["section_ribs_axis"]
    D = {"roof": roof,
         "source": SOURCE.get(roof, roof),
         "units": "m", "coords": "roof-local: origin = roof plan centre, z = 0 at ground. plan: (x, y); elevation and section: (x, z), looking +Y",
         "drawings": {"plan": {"cut_height": 1.2, **pl}, "elevation": {"view": "looking +Y (long side)", **el},
                      "section": {"plane": "y = 0, looking +Y", **se}},
         "levels": levels}
    D["extents"] = {k: ext([i for grp in v.values() if isinstance(grp, list) for i in grp]) for k, v in D["drawings"].items()}
    path = os.path.join(P, "linework-%s.json" % roof)
    json.dump(D, open(path, "w"), separators=(",", ":"))
    return D, path

STYLE = {  # class -> (lineweight mm on screen-ish px, dash, colour index)
    "cut": (2.2, None, 7), "below": (0.6, None, 8), "above": (0.6, (6, 4), 8), "beyond_clean": (0.5, None, 8), "ribs_outline": (1.1, None, 1), "ribs_axis": (0.6, (8, 3), 1),
    "visible": (0.7, None, 7), "beyond": (0.5, None, 8)}

def dxf(D):
    import ezdxf
    out = []
    for dname, d in D["drawings"].items():
        doc = ezdxf.new("R2018", setup=True); doc.header["$INSUNITS"] = 4
        msp = doc.modelspace()
        for cls, items in d.items():
            if not isinstance(items, list):
                continue
            for it in items:
                lay = "%s - %s" % (cls, it["layer"])
                if lay not in doc.layers:
                    l = doc.layers.add(lay, color=STYLE.get(cls, (0, None, 7))[2])
                    if cls == "above":
                        l.dxf.linetype = "DASHED"
                    if cls == "cut":
                        l.dxf.lineweight = 50
                msp.add_lwpolyline([(p[0] * 1000.0, p[1] * 1000.0) for p in it["pts"]], close=it["closed"], dxfattribs={"layer": lay})
        f = os.path.join(P, "%s-%s.dxf" % (D["roof"], dname)); doc.saveas(f); out.append(f)
    return out

def png(D, scale_px=60):
    import System
    from System.Drawing import Bitmap, Graphics, Pen, Color, SolidBrush, PointF
    from System.Drawing.Drawing2D import SmoothingMode, DashStyle
    files = []
    views = list(D["drawings"].items())
    if "beyond_clean" in D["drawings"]["section"]:
        sc = dict(D["drawings"]["section"]); sc["beyond"] = sc.pop("beyond_clean")
        views.append(("section-clean", sc))
    for dname, d in views:
        e = D["extents"]["section" if dname.startswith("section") else dname]
        m = 0.8
        W = int((e[2] - e[0] + 2 * m) * scale_px); H = int((e[3] - e[1] + 2 * m) * scale_px)
        bmp = Bitmap(W, H); g = Graphics.FromImage(bmp); g.SmoothingMode = SmoothingMode.AntiAlias; g.Clear(Color.White)
        T = lambda p: PointF(float((p[0] - e[0] + m) * scale_px), float(H - (p[1] - e[1] + m) * scale_px))
        order = ["below", "beyond", "visible", "above", "ribs_axis", "ribs_outline", "cut"]
        for cls in order:
            if cls not in d:
                continue
            lw, dash, _ = STYLE[cls]
            col = Color.FromArgb(0, 0, 0) if cls in ("cut", "visible", "ribs_outline") else (Color.FromArgb(180, 40, 40) if cls == "ribs_axis" else Color.FromArgb(110, 110, 110))
            pen = Pen(col, float(lw))
            if dash:
                pen.DashStyle = DashStyle.Dash
            fill = SolidBrush(Color.FromArgb(200, 200, 200))
            for it in d[cls]:
                pts = System.Array[PointF]([T(p) for p in it["pts"]])
                if len(pts) < 2:
                    continue
                if cls == "cut" and it["closed"]:
                    g.FillPolygon(fill, pts)
                    g.DrawPolygon(pen, pts)
                else:
                    g.DrawLines(pen, pts)
        g.Dispose()
        f = os.path.join(P, "%s-%s.png" % (D["roof"], dname)); bmp.Save(f, System.Drawing.Imaging.ImageFormat.Png); files.append(f)
    return files
