"""2D linework for the drawing set (plan / elevation / section) cut from the final v3e roofs.
Source: the final layers ("<roof> complete v3e-ring-step::*", visible sublayers only), identical to
stepped-15x10-10x10-v3e-current.3dm (7d1fae3). Output in metres, roof-local coordinates
(origin = roof plan centre, z = 0 at ground). Runs inside Rhino 8 (CPython)."""
import math, json, os
import Rhino
import Rhino.Geometry as G

OUT = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\polyframe2\drawings-2026-11-20"
TOL = 0.005
ROOFS = {"15x10": (85.0, 0.0), "10x10": (85.0, -20.0), "15x10-half": (105.0, 0.0), "10x10-half": (105.0, -20.0)}
ROOT = {"15x10": "15x10 complete v3e-ring-step", "10x10": "10x10 complete v3e-ring-step",
        "15x10-half": "15x10 half-steps (0.25)", "10x10-half": "10x10 half-steps (0.25)"}

def final_objects(doc, roof):
    root = doc.Layers[doc.Layers.FindByFullPath(ROOT[roof], -1)]
    res = []
    for ch in root.GetChildren():
        if not ch.IsVisible:
            continue
        for o in doc.Objects.FindByLayer(ch) or []:
            g = o.Geometry
            if isinstance(g, G.Extrusion):
                g = g.ToBrep()
            res.append((ch.Name, g))
    return res

def short(layer):
    l = layer.lower()
    for key, tag in (("rib pipes - cast core", "rib cores"), ("rib pipes - printed tube", "ribs"), ("growth bands", "printed pieces"),
                     ("rib slices", "ribs (piece not joined)"), ("rib ends outside", "rib ends (landings, crown domes)"), ("printed pieces + rib", "printed pieces + rib (joined)"), ("printed pieces", "printed pieces"), ("crown ring - cast", "crown ring cast"),
                     ("printed band", "crown ring printed band"), ("top course", "top course U formwork"),
                     ("u formwork (3 cm)", "base ring formwork"), ("cast ring inside", "base ring cast"),
                     ("columns", "columns"), ("footing", "footing"), ("rib cores", "rib cores"), ("ribs", "ribs")):
        if key in l:
            return tag
    return layer

def poly(crv, xf2d):
    """curve -> list of 2D points (tolerance TOL), xf2d maps Point3d -> (a, b)"""
    pl = crv.ToPolyline(TOL, math.radians(5), 0.001, 0)
    if pl is None:
        return None
    ok, p = pl.TryGetPolyline()
    if not ok:
        return None
    pts = []
    for q in p:
        a = xf2d(q)
        a = (round(a[0], 4), round(a[1], 4))
        if not pts or abs(pts[-1][0] - a[0]) + abs(pts[-1][1] - a[1]) > 1e-4:
            pts.append(a)
    if len(pts) < 2:
        return None
    return pts

def item(layer, pts, closed):
    return {"layer": layer, "pts": [list(p) for p in pts], "closed": bool(closed)}

def plane_cut(objs, plane, xf2d, layer_filter=None):
    out = []
    for lname, g in objs:
        if layer_filter and not layer_filter(lname):
            continue
        bb = g.GetBoundingBox(True)
        if not plane_hits_box(plane, bb):
            continue
        ok, crvs, pts = G.Intersect.Intersection.BrepPlane(g, plane, 0.0005)
        if not ok or not crvs:
            continue
        for c in G.Curve.JoinCurves(crvs, 0.001):
            p = poly(c, xf2d)
            if p:
                out.append(item(short(lname), p, c.IsClosed))
    return out

def plane_hits_box(plane, bb):
    ds = [plane.DistanceTo(c) for c in bb.GetCorners()]
    return min(ds) <= 0 <= max(ds)

SEAM_FILTER = True
SEAM_ANGLE = math.radians(15.0)
_seam_cache = {}


def is_seam(g, ci):
    """2026-11-23 (reviewer: 'what are these lines?'): an edge between two faces that continue each other (normals
    within 15 deg along the edge) is a modelling seam, not a joint or a step: leave it out of the drawing.
    g = OUR brep (looked up by tag; never touch the HLD copy, it is duplicated on every access)."""
    try:
        if g is None or ci.ComponentIndexType != Rhino.Geometry.ComponentIndexType.BrepEdge or not isinstance(g, G.Brep):
            return False
        key = (id(g), ci.Index)
        if key in _seam_cache:
            return _seam_cache[key]
        e = g.Edges[ci.Index]
        fs = list(e.AdjacentFaces())
        res = False
        if len(fs) == 2:
            p = e.PointAt(e.Domain.Mid)
            ns = []
            for fi in fs:
                f = g.Faces[fi]
                ok, u, v = f.ClosestPoint(p)
                if ok:
                    ns.append(f.NormalAt(u, v))
            if len(ns) == 2 and G.Vector3d.VectorAngle(ns[0], ns[1]) < SEAM_ANGLE:
                res = True
        _seam_cache[key] = res
        return res
    except Exception:
        return False


def hld(objs, view_dir, up, target, xf_back, clip=None, flatten=False):
    """Make2D (HiddenLineDrawing), parallel projection, visible lines only."""
    vp = Rhino.DocObjects.ViewportInfo()
    vp.ChangeToParallelProjection(True)
    cam = target - view_dir * 200.0
    vp.SetCameraLocation(cam)
    vp.SetCameraDirection(view_dir)
    vp.SetCameraUp(up)
    vp.SetFrustum(-60, 60, -60, 60, 1, 1000)
    prm = G.HiddenLineDrawingParameters()
    prm.AbsoluteTolerance = 0.001
    prm.IncludeTangentEdges = False
    prm.IncludeHiddenCurves = False
    prm.Flatten = True
    prm.SetViewport(vp)
    if clip is not None:
        prm.AddClippingPlane(clip)
    geoms = []
    for lname, g in objs:
        prm.AddGeometry(g, G.Transform.Identity, "%s|%d" % (short(lname), len(geoms)))
        geoms.append(g)
    h = G.HiddenLineDrawing.Compute(prm, True)
    out = []
    if h is None:
        return out
    for seg in h.Segments:
        if seg.SegmentVisibility != G.HiddenLineDrawingSegment.Visibility.Visible:
            continue
        if seg.ParentCurve is None or seg.ParentCurve.SilhouetteType == G.SilhouetteType.SectionCut:
            continue
        so = seg.ParentCurve.SourceObject
        raw = str(so.Tag) if so else ""
        tag, _, gi = raw.rpartition("|")
        if not tag:
            tag, gi = raw, ""
        if SEAM_FILTER and gi.isdigit() and not str(tag).startswith("base ring") and is_seam(geoms[int(gi)], seg.ParentCurve.SourceObjectComponentIndex):   # 2026-11-23: the ring step edges are real edges, keep them
            continue
        p = poly(seg.CurveGeometry, xf_back)
        if p:
            out.append(item(str(tag), p, False))
    return out

def rib_axes(objs, xf2d):
    """rib net centrelines in plan from the straight cast cores (cylinders)"""
    out = []
    for lname, g in objs:
        if "rib cores" not in short(lname):
            continue
        for f in g.Faces:
            ok, cyl = f.TryGetFiniteCylinder(0.002)
            if not ok:
                ok, cyl = f.UnderlyingSurface().TryGetCylinder(0.002)
                if not ok:
                    continue
                # finite extent from the face bounding box along the axis
                ax = cyl.Axis; c = cyl.Center
                ts = [ (pt - c) * ax for pt in f.GetBoundingBox(True).GetCorners()]
                a, b = c + ax * min(ts), c + ax * max(ts)
            else:
                a, b = cyl.Center + cyl.Axis * cyl.Height1, cyl.Center + cyl.Axis * cyl.Height2
            out.append(item("rib net centrelines", [xf2d(a), xf2d(b)], False))
            break
    return out

def dedupe(items):
    seen, res = set(), []
    for it in items:
        k = (it["layer"], tuple(map(tuple, (it["pts"] if it["pts"][0] <= it["pts"][-1] else it["pts"][::-1]))))
        if k in seen:
            continue
        seen.add(k)
        res.append(it)
    return res
