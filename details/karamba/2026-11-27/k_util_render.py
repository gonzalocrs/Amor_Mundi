"""Formwork-study utilisation images. Karamba's own 'Stress/Strength Ratio' divides axial stress by the plain-concrete
strengths in the material (ft 2.9 MPa for the cast cores, 0.5 MPa for the printed parts), so every reinforced rib in
tension reads 500-2000 % and the picture says nothing about the design. Instead each cast member (ribs, rings, arches,
crown, columns) is drawn as a solid of its real section and coloured by MY check from the Karamba end forces of that
variant: worst fibre compression / 24 MPa (Fc36 short-term) in the worst short-term case. White 0 %, yellow 50 %,
red 100 %, dark red above 100 %. Printed courses and fins are drawn as a light grey ghost (thin lines) so the ribs
stay visible. Baked to layer 'formwork util <roof> <v>', captured like the Karamba-model renders."""
import os, sys, json, math, System, Rhino
import Rhino.Geometry as G
HERE = r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\details\karamba\2026-11-27"
sys.path.insert(0, HERE)
import k_render as R
import k_beamview_render as K
PNG = r"C:\Users\gonza\AppData\Local\Temp\claude\5c622a39c96e3387\d0f96d15-672a-4d67-b7d7-f160f3f4487b\scratchpad\formwork27"
CAST = ("rib_bottom", "rib_middle", "rib_top", "ring", "crown", "column")


def ucol(u):
    if u >= 1.0:
        return System.Drawing.Color.FromArgb(150, 0, 20)
    if u < 0.5:
        t = u / 0.5; return System.Drawing.Color.FromArgb(255, 255, int(255 - 200 * t))       # white -> yellow
    t = (u - 0.5) / 0.5; return System.Drawing.Color.FromArgb(255, int(255 - 225 * t), int(55 - 25 * t))   # yellow -> red


def build(doc, roof, v, lc, li):
    D = json.load(open(os.path.join(HERE, "formwork", "forces-%s-%s.json" % (roof, v))))
    f = D["forces"][lc]; N = D["nodes"]; bb = G.BoundingBox.Empty; umax = 0
    att = Rhino.DocObjects.ObjectAttributes(); att.LayerIndex = li
    ghost = Rhino.DocObjects.ObjectAttributes(); ghost.LayerIndex = li
    ghost.ColorSource = Rhino.DocObjects.ObjectColorSource.ColorFromObject; ghost.ObjectColor = System.Drawing.Color.FromArgb(200, 200, 200)
    for i, (g, a, b) in enumerate(D["els"]):
        pa, pb = G.Point3d(*N[a]), G.Point3d(*N[b])
        if g == "column":                                 # down to the top of the footing, same colour (2026-11-27)
            if abs(pa.Z) < 1e-6: pa = G.Point3d(pa.X, pa.Y, -0.30)
            if abs(pb.Z) < 1e-6: pb = G.Point3d(pb.X, pb.Y, -0.30)
        if g in ("course", "fin"):
            doc.Objects.AddLine(pa, pb, ghost); continue
        if g == "arch": g2 = "ring"
        else: g2 = g
        if g2 not in CAST: continue
        kind, dims, A, W = R.section(g2, roof)
        u = 0
        for t in (0, 1):
            sc = (-f["N"][2 * i + t] / A + math.hypot(f["My"][2 * i + t], f["Mz"][2 * i + t]) / W) / 1000.0
            u = max(u, sc / 24.0)
        umax = max(umax, u)
        ax = pb - pa; ax.Unitize()
        ref = G.Vector3d.ZAxis if abs(ax.Z) < 0.95 else G.Vector3d.XAxis
        y = G.Vector3d.CrossProduct(ref, ax); y.Unitize(); z = G.Vector3d.CrossProduct(ax, y); z.Unitize()
        m = G.Mesh()
        for p in (pa, pb):
            for q in R.ring_pts(kind, dims, (p, y, z), 16): m.Vertices.Add(q)
        n = m.Vertices.Count // 2
        for k in range(n): m.Faces.AddFace(k, (k + 1) % n, n + (k + 1) % n, n + k)
        if n == 4: m.Faces.AddFace(3, 2, 1, 0); m.Faces.AddFace(4, 5, 6, 7)
        m.Normals.ComputeNormals(); m.Compact()
        c = ucol(u)
        for _k in range(m.Vertices.Count): m.VertexColors.Add(c)   # vertex colours: shown by any shaded display mode
        a2 = att.Duplicate(); a2.ColorSource = Rhino.DocObjects.ObjectColorSource.ColorFromObject; a2.ObjectColor = c
        doc.Objects.AddMesh(m, a2); bb.Union(m.GetBoundingBox(True))
    fat = att.Duplicate(); fat.ColorSource = Rhino.DocObjects.ObjectColorSource.ColorFromObject; fat.ObjectColor = System.Drawing.Color.FromArgb(222, 222, 222)
    for l in doc.Layers:
        if not l.IsDeleted and l.FullPath.startswith(roof + " complete v3e-ring-step::") and "footing" in l.Name:
            for o in doc.Objects.FindByLayer(l) or []:
                doc.Objects.Add(o.Geometry.Duplicate(), fat); bb.Union(o.Geometry.GetBoundingBox(True))
    return bb, umax


def run(doc, cases):
    out = {}
    for (roof, v), lc in cases.items():
        li = K.layer(doc, "formwork util %s %s" % (roof, v), System.Drawing.Color.FromArgb(120, 120, 120))
        bb, umax = build(doc, roof, v, lc, li)
        for l in doc.Layers:
            if not l.IsDeleted: l.IsVisible = (l.Index == li)
        for _ in (0, 1): K.capture(doc, bb, os.path.join(PNG, "formwork-%s-%s.png" % (roof, v)), wires=False)   # twice: a display-mode change shows from the next capture on
        out["%s %s" % (roof, v)] = {"case": lc, "max_util_short": round(umax, 3)}
    return out
