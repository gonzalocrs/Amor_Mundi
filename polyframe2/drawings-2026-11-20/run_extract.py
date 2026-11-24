"""v07 linework from the rebuilt model (2026-11-21: approved pieces + growth bands, rib pipes). Runs in Rhino.
Writes _tmp_<roof>_{ribs,sect,elev}.json (plan cut is unchanged: columns, rings, crown) and _tmp_axon_{iso,worm}.json."""
import importlib.util, json, os, time, math
import Rhino, Rhino.Geometry as G

P = r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\polyframe2\drawings-2026-11-20"
LOG = os.path.join(P, "_extract_progress.txt")
spec = importlib.util.spec_from_file_location("xl", os.path.join(P, "extract_linework.py"))
X = importlib.util.module_from_spec(spec); spec.loader.exec_module(X)


def log(s):
    open(LOG, "a").write(time.strftime("%H:%M:%S ") + s + "\n")


def ribs(doc, roof):
    cx, cy = X.ROOFS[roof]
    allo = X.final_objects(doc, roof)
    rb = [o for o in allo if X.short(o[0]) == "ribs"]
    cores = [o for o in allo if X.short(o[0]) == "rib cores"]
    po = X.hld(rb, G.Vector3d(0, 0, -1), G.Vector3d(0, 1, 0), G.Point3d(cx, cy, 5), lambda q: (q.X, q.Y))
    pa = X.rib_axes(cores, lambda q: (q.X - cx, q.Y - cy))
    so = X.hld(rb, G.Vector3d(0, 1, 0), G.Vector3d(0, 0, 1), G.Point3d(cx, cy, 5), lambda q: (q.X, q.Y + 5),
               clip=G.Plane(G.Point3d(cx, cy, 0), G.Vector3d(0, -1, 0)))
    sa = []
    for it in X.rib_axes(cores, lambda q: (q.X - cx, q.Y - cy, q.Z)):
        (x0, y0, z0), (x1, y1, z1) = it["pts"][0], it["pts"][1]
        if y0 < 0 and y1 < 0:
            continue
        if (y0 < 0) != (y1 < 0):
            tt = (0 - y0) / (y1 - y0); xm, zm = x0 + tt * (x1 - x0), z0 + tt * (z1 - z0)
            if y0 < 0: x0, z0 = xm, zm
            else: x1, z1 = xm, zm
        sa.append(X.item("rib net centrelines", [(round(x0, 4), round(z0, 4)), (round(x1, 4), round(z1, 4))], False))
    for i in po + so:
        i["layer"] = "ribs"
    json.dump({"plan_ribs_outline": X.dedupe(po), "plan_ribs_axis": pa, "section_ribs_outline": X.dedupe(so), "section_ribs_axis": sa},
              open(os.path.join(P, "_tmp_%s_ribs.json" % roof), "w"))
    log("%s ribs: plan %d, axes %d, section %d" % (roof, len(po), len(pa), len(so)))


def sect(doc, roof, off=0.0):
    cx, cy = X.ROOFS[roof]
    allo = X.final_objects(doc, roof)
    noc = [o for o in allo if X.short(o[0]) != "rib cores"]
    xz = lambda q: (q.X - cx, q.Z)
    pl = G.Plane(G.Point3d(cx, cy + off, 0), G.Vector3d(0, 1, 0))
    scut = X.dedupe(X.plane_cut(allo, pl, xz))
    beyond = X.dedupe(X.hld(noc, G.Vector3d(0, 1, 0), G.Vector3d(0, 0, 1), G.Point3d(cx, cy, 5), lambda q: (q.X, q.Y + 5),
                            clip=G.Plane(G.Point3d(cx, cy + off, 0), G.Vector3d(0, -1, 0))))
    json.dump({"cut": scut, "beyond": beyond}, open(os.path.join(P, "_tmp_%s_sect.json" % roof), "w"))
    log("%s section: cut %d, beyond %d" % (roof, len(scut), len(beyond)))


def elev(doc, roof):
    cx, cy = X.ROOFS[roof]
    allo = [o for o in X.final_objects(doc, roof) if X.short(o[0]) not in ("rib cores", "ribs")]
    vis = X.dedupe(X.hld(allo, G.Vector3d(0, 1, 0), G.Vector3d(0, 0, 1), G.Point3d(cx, cy, 5), lambda q: (q.X, q.Y + 5)))
    json.dump({"visible": vis}, open(os.path.join(P, "_tmp_%s_elev.json" % roof), "w"))
    log("%s elevation: %d" % (roof, len(vis)))


def rib_crowns(doc, roof):
    """the room-side crown line of every rib tube (the tubes are pushed into the room face, so Make2D hides their
    silhouettes): segment axis offset towards the room by the tube radius plus 3 mm"""
    cx, cy = X.ROOFS[roof]
    out = []
    for lname, g in X.final_objects(doc, roof):
        if lname != "rib pipes - printed tube":
            continue
        for f in g.Faces:
            ok, cyl = f.UnderlyingSurface().TryGetCylinder(0.002)
            if not ok:
                continue
            ax = cyl.Axis; ax.Unitize(); c = cyl.Center
            ts = [(G.Point3d(v.Location) - c) * ax for v in g.Vertices]
            if len(ts) < 2:
                break
            a, b = c + ax * min(ts), c + ax * max(ts)
            m = (a + b) / 2
            inw = G.Vector3d(cx - m.X, cy - m.Y, -0.6 * math.hypot(cx - m.X, cy - m.Y) / max(abs(m.Z - 2.4), 1.0))
            n = inw - ax * (inw * ax); n.Unitize()
            off = n * (cyl.Radius + 0.003)        # just outside the tube apex, so the tube itself does not hide it
            out.append((lname, G.LineCurve(a + off, b + off)))
            break
    return out


def topbottom(doc, roof):
    """roof from straight above (looking down) and from straight below (looking up), roof only (no columns/footing)"""
    cx, cy = X.ROOFS[roof]
    keep_top = [o for o in X.final_objects(doc, roof) if X.short(o[0]) not in ("rib cores", "ribs", "columns", "footing")]
    top = X.hld(keep_top, G.Vector3d(0, 0, -1), G.Vector3d(0, 1, 0), G.Point3d(cx, cy, 5), lambda q: (q.X, q.Y))
    keep_bot = [o for o in X.final_objects(doc, roof) if X.short(o[0]) not in ("rib cores", "ribs", "footing")] + rib_edges(doc, roof)
    bot = X.hld(keep_bot, G.Vector3d(0, 0, 1), G.Vector3d(0, 1, 0), G.Point3d(cx, cy, 5), lambda q: (q.X, q.Y))
    json.dump({"top": X.dedupe(top), "bottom": X.dedupe(bot)}, open(os.path.join(P, "_tmp_%s_topbottom.json" % roof), "w"))
    log("%s top %d bottom %d" % (roof, len(top), len(bot)))


def rib_edges(doc, roof, proud=0.04):
    """the two lines where each rib tube leaves the room face (tubes are pushed in, `proud` m showing): axis offset
    towards the room by (r - proud) and sideways by the half chord; 3 mm proud of the face so Make2D keeps them"""
    cx, cy = X.ROOFS[roof]
    out = []
    allo = X.final_objects(doc, roof)
    pieces = [(g, g.GetBoundingBox(True)) for ln, g in allo if X.short(ln) in ("printed pieces", "top course U formwork") and "growth" not in ln.lower()]

    def room_normal(m):
        """2026-11-23: the REAL room-face normal next to the rib (closest point on the printed pieces), pointing into the room"""
        best = None
        for g, bb in pieces:
            bi = G.BoundingBox(bb.Min - G.Vector3d(0.4, 0.4, 0.4), bb.Max + G.Vector3d(0.4, 0.4, 0.4))
            if not bi.Contains(m):
                continue
            ok, cp, ci, s, t, nn = g.ClosestPoint(m, 0.6)
            if ok and (best is None or cp.DistanceTo(m) < best[0]):
                best = (cp.DistanceTo(m), nn)
        if best is None:
            return None
        nn = G.Vector3d(best[1])
        if nn * G.Vector3d(cx - m.X, cy - m.Y, 0) < 0:
            nn.Reverse()
        return nn

    for lname, g in allo:
        if lname != "rib pipes - printed tube":
            continue
        for f in g.Faces:
            ok, cyl = f.UnderlyingSurface().TryGetCylinder(0.002)
            if not ok:
                continue
            ax = cyl.Axis; ax.Unitize(); c = cyl.Center; r = cyl.Radius
            ts = [(G.Point3d(v.Location) - c) * ax for v in g.Vertices]
            if len(ts) < 2:
                break
            a, b = c + ax * min(ts), c + ax * max(ts)
            m = (a + b) / 2
            inw = room_normal(m)
            if inw is None:
                inw = G.Vector3d(cx - m.X, cy - m.Y, -0.6 * math.hypot(cx - m.X, cy - m.Y) / max(abs(m.Z - 2.4), 1.0))
            n = inw - ax * (inw * ax); n.Unitize()
            side = G.Vector3d.CrossProduct(ax, n); side.Unitize()
            hw = math.sqrt(max(r * r - (r - proud) ** 2, 0.0))
            for sg in (1, -1):
                off = n * (r - proud + 0.025) + side * (sg * hw)
                out.append((lname, G.LineCurve(a + off, b + off)))
            break
    return out


def axon(doc, name, d, up, skip=(), crowns=False):
    objs = []
    for roof in ("15x10", "10x10"):
        objs += [o for o in X.final_objects(doc, roof) if X.short(o[0]) not in ("rib cores",) + tuple(skip)]
        if crowns:
            objs += rib_edges(doc, roof)          # tubes drawn with their two outlines (Gonzalo 2026-11-21)
    d = G.Vector3d(*d); d.Unitize()
    vis = X.hld(objs, d, G.Vector3d(*up), G.Point3d(85, -10, 5), lambda q: (q.X, q.Y))
    json.dump({"visible": X.dedupe(vis)}, open(os.path.join(P, "_tmp_axon_%s.json" % name), "w"))
    log("axon %s: %d" % (name, len(vis)))


# ---- 2026-11-23 v3: ribs drawn like the plan (true outlines of the rib tubes from a hidden-line drawing), hidden only by
# the rings and columns (not by the printed pieces they are pushed into), laid over the roof drawing ----

def rib_tubes_view(doc, roofs, d, up, target):
    objs = []
    for roof in roofs:
        for o in X.final_objects(doc, roof):
            if X.short(o[0]) in ("ribs", "base ring formwork", "base ring cast", "crown ring cast", "crown ring printed band", "columns"):
                objs.append(o)
    vis = X.hld(objs, d, up, target, lambda q: (q.X, q.Y))
    return [it for it in vis if it["layer"] == "ribs"]


def axon_worm_v3(doc):
    objs = []
    for roof in ("15x10", "10x10"):
        objs += [o for o in X.final_objects(doc, roof) if X.short(o[0]) not in ("rib cores", "footing", "ribs")]
    d = G.Vector3d(-1, 1, 1.7); d.Unitize(); up = G.Vector3d(0, 0, 1)
    vis = X.hld(objs, d, up, G.Point3d(85, -10, 5), lambda q: (q.X, q.Y))
    rib = rib_tubes_view(doc, ("15x10", "10x10"), d, up, G.Point3d(85, -10, 5))
    json.dump({"visible": X.dedupe(vis) + X.dedupe(rib)}, open(os.path.join(P, "_tmp_axon_worm.json"), "w"))
    log("axon worm v3: %d + ribs %d" % (len(vis), len(rib)))


def bottom_v3(doc, roof):
    cx, cy = X.ROOFS[roof]
    keep_bot = [o for o in X.final_objects(doc, roof) if X.short(o[0]) not in ("rib cores", "ribs", "footing")]
    d = G.Vector3d(0, 0, 1); up = G.Vector3d(0, 1, 0)
    bot = X.hld(keep_bot, d, up, G.Point3d(cx, cy, 5), lambda q: (q.X, q.Y))
    rib = rib_tubes_view(doc, (roof,), d, up, G.Point3d(cx, cy, 5))
    p = os.path.join(P, "_tmp_%s_topbottom.json" % roof)
    D = json.load(open(p))
    D["bottom"] = X.dedupe(bot) + X.dedupe(rib)
    json.dump(D, open(p, "w"))
    log("%s bottom v3: %d + ribs %d" % (roof, len(bot), len(rib)))
