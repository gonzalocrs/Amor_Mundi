"""Strip footings moved 30 mm inward (Gonzalo 2026-11-27, "yea" to the shift). After the columns grew inward with the
base ring (outer face fixed), their centres sat ~30 mm off the strip axis and tipping fell to 1.49 / 1.44. Each footing
(strips + square corner blocks, one solid per roof) is rebuilt from its own plan outline offset 30 mm toward the centre
(both the outer loop and the inner loop, so the widths 1.20 / 0.85 m stay), extruded over the same levels -0.80 to
-0.30. Applied with File3dm (object replaced on the same layer with the same attributes) to
stepped-15x10-10x10-v3e-current.3dm (backup current-before-footing-shift-2026-11-27.3dm) and
stepped-roofs-final-2026-11-27.3dm (backup stepped-roofs-final-2026-11-27-before-footing-shift.3dm).
Check: every column corner on the strip, min edge distance 234 mm (15x10) / 192 mm (10x10), was 204 / 162;
tipping 1.60 / 1.60 (details/karamba/2026-11-27/rect_check.py with rect_result.json xl, yl - 0.03)."""
import Rhino
import Rhino.Geometry as G
TOL = 0.0001


def inset(c, dist):
    best = None
    for s in (dist, -dist):
        r = c.Offset(G.Plane.WorldXY, s, TOL, G.CurveOffsetCornerStyle.Sharp)
        if not r or len(r) != 1 or not r[0].IsClosed: continue
        a = G.AreaMassProperties.Compute(r[0]).Area
        if best is None or a < best[0]: best = (a, r[0])
    return best[1]


def shifted(b, d=0.03):
    bb = b.GetBoundingBox(True)
    ok, cs, ps = G.Intersect.Intersection.BrepPlane(b, G.Plane(G.Point3d(0, 0, (bb.Min.Z + bb.Max.Z) / 2), G.Vector3d.ZAxis), 0.00005)
    loops = [inset(c, d) for c in G.Curve.JoinCurves(cs, 0.0005)]
    for c in loops: c.Translate(G.Vector3d(0, 0, bb.Min.Z - c.PointAtStart.Z))
    T = G.Brep.CreatePlanarBreps(loops, TOL)[0].Faces[0].CreateExtrusion(G.LineCurve(G.Point3d(0, 0, bb.Min.Z), G.Point3d(0, 0, bb.Max.Z)), True)
    if T.SolidOrientation == G.BrepSolidOrientation.Inward: T.Flip()
    return T


def apply(path_in, path_out):
    f = Rhino.FileIO.File3dm.Read(path_in)
    for o in list(f.Objects):
        if "strip footing" in f.AllLayers.FindIndex(o.Attributes.LayerIndex).Name:
            T = shifted(o.Geometry); att = o.Attributes.Duplicate(); f.Objects.Delete(o.Id); f.Objects.AddBrep(T, att)
    return f.Write(path_out, 8)
