"""Concrete 3D-print slicer - turns any closed geometry into printed bead geometry

Slices the geometry into horizontal layers (layer_H) and fills each layer with
beads (ext_W wide), working inward from every outline - outer boundaries and
holes alike. As many beads as fit:
  - a wall exactly 1 bead wide gets 1 bead down its middle
  - a wall 2 beads wide gets 2 beads side by side, and so on
  - a solid shape fills up with concentric beads (cap it with max_beads)
Where two outlines would put a bead in the same place (e.g. the ribs and walls
of a hollow piece), only one is kept, so thin walls meet in clean T-junctions.

Output is visual: each bead is a mesh with a rounded profile (flat top and
bottom, round sides), like extruded concrete.

The geometry must sit in its PRINT orientation: layers are cut along world Z.

Paste into a GhPython component (Rhino 7) or a Python 3 Script component (Rhino 8).
Units: millimetres.

INPUTS
    geo          list  (no type hint)  closed Breps / Meshes / Extrusions to print
    ext_W        item  float           extrusion (bead) width              (default 40)
    layer_H      item  float           layer height                        (default 15)
  optional:
    max_beads    item  int             max beads inward from each outline, 0 = as many as fit (default 0)
    smooth       item  int             segments per rounded bead side      (default 4)

OUTPUTS
    beads        bead meshes, one per layer, tree {object; layer}
    paths        bead centrelines, same tree
    info         layers, bead length, concrete volume per object
"""
import math
import Rhino
import Rhino.Geometry as rg
from Rhino.Geometry.Intersect import Intersection
from Grasshopper import DataTree
from Grasshopper.Kernel.Data import GH_Path


def _d(name, default):
    """Optional input: works whether or not the input exists on the component."""
    v = globals().get(name)
    return default if v is None else v


EW = float(_d('ext_W', 40.0))
LH = float(_d('layer_H', 15.0))
MAX_B = int(_d('max_beads', 0))
SEG = max(1, int(_d('smooth', 4)))

doc = Rhino.RhinoDoc.ActiveDoc
TOL = doc.ModelAbsoluteTolerance if doc else 0.01
Z = rg.Vector3d.ZAxis
SLACK = 0.25 * EW     # lets a bead sit exactly on the middle of a wall (odd bead counts)
DEDUPE = 0.5 * EW     # closer than this to an existing bead = same bead, drop it
STEP = EW / 3.0       # sampling along a path when checking where a bead fits


def bead_profile():
    """Rounded bead section (s across, v up), centred on the path: flat top/bottom, round sides."""
    r = min(EW, LH) / 2.0
    cx = EW / 2.0 - r
    pts = []
    for i in range(SEG + 1):                      # right side, bottom -> top
        a = -math.pi / 2 + math.pi * i / SEG
        pts.append((cx + r * math.cos(a), LH / 2.0 * math.sin(a)))
    for i in range(SEG + 1):                      # left side, top -> bottom
        a = math.pi / 2 + math.pi * i / SEG
        pts.append((-cx + r * math.cos(a), LH / 2.0 * math.sin(a)))
    return pts


PROF = bead_profile()


def to_geo(g):
    if isinstance(g, rg.Mesh):
        return g
    return rg.Brep.TryConvertBrep(g)


def slice_at(g, z):
    """Closed outlines of g at height z."""
    plane = rg.Plane(rg.Point3d(0, 0, z), Z)
    if isinstance(g, rg.Mesh):
        pls = Intersection.MeshPlane(g, plane) or []
        crvs = [rg.PolylineCurve(p) for p in pls if p.IsClosed]
    else:
        rc, cs, ps = Intersection.BrepPlane(g, plane, TOL)
        crvs = list(rg.Curve.JoinCurves(cs, TOL * 10)) if rc and cs else []
    return [c for c in crvs if c.IsClosed], plane


def is_hole(i, loops, plane):
    """A loop is a hole if it sits inside an odd number of other loops."""
    p = loops[i].PointAtStart
    n = 0
    for j, other in enumerate(loops):
        if j != i and other.Contains(p, plane, TOL) == rg.PointContainment.Inside:
            n += 1
    return n % 2 == 1


def offset_into_material(loop, dist, hole, plane):
    """Offset a loop by dist towards the material (inward for outlines, outward for holes)."""
    for sign in (1, -1):
        res = loop.Offset(plane, sign * dist, TOL, rg.CurveOffsetCornerStyle.Sharp)
        if not res:
            continue
        inside = loop.Contains(res[0].PointAtStart, plane, TOL) == rg.PointContainment.Inside
        if inside != hole:
            return list(res)
    return []


def dist_to(crv, p):
    rc, t = crv.ClosestPoint(p)
    return p.DistanceTo(crv.PointAt(t)) if rc else 1e9


def fitting_parts(crv, d, loops, accepted):
    """The parts of an offset path where a bead fits: not past the middle of the wall
    (closer than d to another outline) and not on top of a bead already placed."""
    ts = crv.DivideByLength(STEP, True)
    if not ts:
        return []
    ts = list(ts)
    ok = []
    for t in ts:
        p = crv.PointAt(t)
        good = all(dist_to(lp, p) >= d - SLACK for lp in loops)
        if good:
            good = all(dist_to(a, p) >= DEDUPE for a in accepted)
        ok.append(good)
    if all(ok):
        return [crv]
    if not any(ok):
        return []

    n = len(ts)
    order = [(ok.index(False) + i) % n for i in range(n)] if crv.IsClosed else list(range(n))
    parts, run = [], []
    for idx in order + [None]:
        if idx is not None and ok[idx]:
            run.append(ts[idx])
            continue
        if len(run) >= 2:
            sub = crv.Trim(run[0], run[-1])
            if sub and sub.GetLength() > 0.5 * EW:
                parts.append(sub)
        run = []
    return parts


def path_points(crv):
    rc, pl = crv.TryGetPolyline()
    if not rc:
        plc = crv.ToPolyline(0, 0, math.radians(5), 0, 0, 0.5, 0.5, EW, True)
        if plc is None:
            return None, False
        rc, pl = plc.TryGetPolyline()
        if not rc:
            return None, False
    pts = [pl[i] for i in range(pl.Count)]
    closed = crv.IsClosed
    if closed and pts[0].DistanceTo(pts[-1]) < 1e-6:
        pts = pts[:-1]
    clean = [pts[0]]
    for p in pts[1:]:
        if p.DistanceTo(clean[-1]) > 1e-3:
            clean.append(p)
    return clean, closed


def bead_mesh(crv, z):
    """Sweep the bead profile along a horizontal path; corners are mitred so the bead keeps its width."""
    pts, closed = path_points(crv)
    if not pts or len(pts) < 2:
        return None
    n, P = len(pts), len(PROF)

    def unit(a, b):
        dx, dy = b.X - a.X, b.Y - a.Y
        L = math.hypot(dx, dy) or 1.0
        return dx / L, dy / L

    m = rg.Mesh()
    for i in range(n):
        has_prev = closed or i > 0
        has_next = closed or i < n - 1
        if has_prev and has_next:
            t1 = unit(pts[i - 1], pts[i])
            t2 = unit(pts[i], pts[(i + 1) % n])
            n1 = (t1[1], -t1[0])
            sx, sy = n1[0] + t2[1], n1[1] - t2[0]
            L = math.hypot(sx, sy)
            if L < 1e-6:
                sx, sy, L = n1[0], n1[1], 1.0
            sx, sy = sx / L, sy / L
            scale = 1.0 / max(0.35, sx * n1[0] + sy * n1[1])
        else:
            t = unit(pts[i - 1], pts[i]) if has_prev else unit(pts[i], pts[i + 1])
            sx, sy, scale = t[1], -t[0], 1.0
        for s, v in PROF:
            m.Vertices.Add(pts[i].X + sx * s * scale, pts[i].Y + sy * s * scale, z + v)

    for i in range(n if closed else n - 1):
        j = (i + 1) % n
        for k in range(P):
            k2 = (k + 1) % P
            m.Faces.AddFace(i * P + k, j * P + k, j * P + k2, i * P + k2)
    if not closed:                                # cap the free ends
        for ring, flip in ((0, True), (n - 1, False)):
            ci = m.Vertices.Count
            m.Vertices.Add(pts[ring].X, pts[ring].Y, z)
            for k in range(P):
                a, b = ring * P + k, ring * P + (k + 1) % P
                if flip:
                    m.Faces.AddFace(b, a, ci)
                else:
                    m.Faces.AddFace(a, b, ci)
    return m


beads = DataTree[object]()
paths = DataTree[object]()
info = []

for o_i, g in enumerate(geo or []):
    g = to_geo(g)
    if g is None:
        info.append("object {}: not a closed Brep / Mesh, skipped".format(o_i))
        continue
    bb = g.GetBoundingBox(True)
    n_layers = int((bb.Max.Z - bb.Min.Z) / LH + 1e-6)
    total = 0.0

    for li in range(n_layers):
        z = bb.Min.Z + (li + 0.5) * LH + 1e-3   # cut mid-layer, off any flat faces
        loops, plane = slice_at(g, z)
        if not loops:
            continue
        holes = [is_hole(i, loops, plane) for i in range(len(loops))]
        accepted = []
        # outer outlines first, so outer walls get one continuous bead
        for i in sorted(range(len(loops)), key=lambda i: holes[i]):
            k = 0
            while (MAX_B <= 0 or k < MAX_B) and k < 200:
                d = (k + 0.5) * EW
                kept = []
                for oc in offset_into_material(loops[i], d, holes[i], plane):
                    kept += fitting_parts(oc, d, loops, accepted)
                if not kept:
                    break
                accepted += kept
                k += 1

        path = GH_Path(o_i, li)
        layer_mesh = rg.Mesh()
        for c in accepted:
            paths.Add(c, path)
            total += c.GetLength()
            bm = bead_mesh(c, z)
            if bm:
                layer_mesh.Append(bm)
        layer_mesh.Normals.ComputeNormals()
        layer_mesh.Compact()
        beads.Add(layer_mesh, path)

    info.append("object {}: {} layers, {:.1f} m of bead, ~{:.3f} m3 concrete".format(
        o_i, n_layers, total / 1000.0, total * EW * LH / 1e9))

info.append("bead {:.0f} x {:.0f} mm (width x layer height)".format(EW, LH))
