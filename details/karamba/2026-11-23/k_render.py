"""'The Karamba model, every element assembled' render (Gonzalo 2026-11-23, like midterm page 04): every Karamba bar
of the 2 m model drawn as a solid of its real cross-section, coloured by stress over allowable under LONG (red
compression, blue tension, white low), from the Karamba results dumped by k_dump.py (forces-<roof>.json).
Printed courses and fins are left out (as the midterm left out the casing) and the footing from current.3dm is shown
in grey. Runs in Rhino; temporary objects are deleted after the capture. Writes karamba-model-<roof>.png + legend json."""
import json, math, os, System, Rhino
import Rhino.Geometry as G
HERE = r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\details\karamba\2026-11-23"
OUT = r"C:\Users\gonza\AppData\Local\Temp\claude\5c622a39c96e3387\d0f96d15-672a-4d67-b7d7-f160f3f4487b\scratchpad\kmodel"
ALLOW = 12.0                                         # MPa, Fc 36 long-term (LONG case)
RIB = {"15x10": {"rib_bottom": 0.22, "rib_middle": 0.16, "rib_top": 0.12}, "10x10": {"rib_bottom": 0.18, "rib_middle": 0.14, "rib_top": 0.12}}
RECT = {"ring": (0.40, 0.40), "crown": (0.25, 0.25), "column": {"15x10": (0.36, 0.36), "10x10": (0.30, 0.30)}}
CEN = {"15x10": (85.0, 0.0), "10x10": (85.0, -20.0)}


def colour(u):
    """u > 0 compression (red), u < 0 tension (blue); white at 0, full colour at |u| = 0.6"""
    t = max(-1.0, min(1.0, u / 0.6))
    if t >= 0:
        return System.Drawing.Color.FromArgb(255, int(255 - 225 * t), int(255 - 205 * t))
    t = -t
    return System.Drawing.Color.FromArgb(int(255 - 175 * t), int(255 - 185 * t), 255)


def section(g, roof):
    if g.startswith("rib"):
        d = RIB[roof][g]; return "round", d, math.pi * d * d / 4, math.pi * d ** 3 / 32
    b, h = RECT["column"][roof] if g == "column" else RECT[g]
    return "rect", (b, h), b * h, b * h * h / 6


def ring_pts(kind, dims, frame, n=12):
    o, y, z = frame
    if kind == "round":
        r = dims / 2; return [o + y * (r * math.cos(2 * math.pi * k / n)) + z * (r * math.sin(2 * math.pi * k / n)) for k in range(n)]
    b, h = dims
    return [o + y * (sy * b / 2) + z * (sz * h / 2) for sy, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1))]


def build(roof, doc, layer, lc="LONG", allow=ALLOW):
    D = json.load(open(os.path.join(HERE, "forces-%s.json" % roof)))
    f = D["forces"][lc]; N = D["nodes"]
    umax = 0.0; umin = 0.0; ids = []
    att = Rhino.DocObjects.ObjectAttributes(); att.LayerIndex = layer
    for i, (g, a, b) in enumerate(D["els"]):
        if g not in ("rib_bottom", "rib_middle", "rib_top", "ring", "crown", "column"): continue
        kind, dims, A, W = section(g, roof)
        pa, pb = G.Point3d(*N[a]), G.Point3d(*N[b])
        ax = pb - pa; ax.Unitize()
        ref = G.Vector3d.ZAxis if abs(ax.Z) < 0.95 else G.Vector3d.XAxis
        y = G.Vector3d.CrossProduct(ref, ax); y.Unitize(); z = G.Vector3d.CrossProduct(ax, y); z.Unitize()
        m = G.Mesh(); cols = []
        for t, p in ((0, pa), (1, pb)):
            Nn = f["N"][2 * i + t]; M = math.hypot(f["My"][2 * i + t], f["Mz"][2 * i + t])
            sc = (-Nn / A + M / W) / 1000.0; st = (-Nn / A - M / W) / 1000.0     # MPa, compression +
            u = sc / allow if abs(sc) >= abs(st) else st / allow
            umax = max(umax, sc / allow); umin = min(umin, st / allow)
            for q in ring_pts(kind, dims, (p, y, z)):
                m.Vertices.Add(q); cols.append(colour(u))
        n = len(cols) // 2
        for k in range(n):
            k2 = (k + 1) % n; m.Faces.AddFace(k, k2, n + k2, n + k)
        m.Faces.AddFace(*([0, 1, 2, 3] if n == 4 else [0, 1, 2])) if n == 4 else None
        if n == 4: m.Faces.AddFace(n + 3, n + 2, n + 1, n + 0)
        for c in cols: m.VertexColors.Add(c)
        m.Normals.ComputeNormals(); m.Compact()
        ids.append(doc.Objects.AddMesh(m, att))
    # footing from the model, grey
    att2 = Rhino.DocObjects.ObjectAttributes(); att2.LayerIndex = layer
    att2.ColorSource = Rhino.DocObjects.ObjectColorSource.ColorFromObject; att2.ObjectColor = System.Drawing.Color.FromArgb(205, 205, 205)
    for l in doc.Layers:
        if not l.IsDeleted and l.FullPath.startswith(roof + " complete v3e-ring-step::") and "footing" in l.Name:
            for o in doc.Objects.FindByLayer(l) or []:
                for mm in G.Mesh.CreateFromBrep(o.Geometry, G.MeshingParameters.Default): ids.append(doc.Objects.AddMesh(mm, att2))
    return ids, umax, umin, D


def worst_wind(roof):
    """typhoon case with the highest member stress (short-term)"""
    D = json.load(open(os.path.join(HERE, "forces-%s.json" % roof))); best = (0, "W+Y")
    for lc in ("W+Y", "W-Y", "W+X", "W-X", "W45"):
        f = D["forces"][lc]
        for i, (g, a, b) in enumerate(D["els"]):
            if g not in ("rib_bottom", "rib_middle", "rib_top", "ring", "crown", "column"): continue
            kind, dims, A, W = section(g, roof)
            for t in (0, 1):
                sc = (-f["N"][2 * i + t] / A + math.hypot(f["My"][2 * i + t], f["Mz"][2 * i + t]) / W) / 1000.0
                if sc > best[0]: best = (sc, lc)
    return best[1]


def run(doc):
    os.makedirs(OUT, exist_ok=True)
    vis = {l.Index: l.IsVisible for l in doc.Layers if not l.IsDeleted}
    lay = Rhino.DocObjects.Layer(); lay.Name = "_tmp karamba render (delete)"; li = doc.Layers.Add(lay)
    legend = {}
    for roof in ("15x10", "10x10"):
        for case, lc, allow in (("LONG", "LONG", 12.0), ("SHORT", worst_wind(roof), 24.0)):
            ids, umax, umin, D = build(roof, doc, li, lc, allow)
            for l in doc.Layers:
                if not l.IsDeleted and l.Index != li: l.IsVisible = False
            v = doc.Views.ActiveView; vp = v.ActiveViewport
            vp.DisplayMode = Rhino.Display.DisplayModeDescription.FindByName("Shaded")
            cx, cy = CEN[roof]
            vp.ChangeToParallelProjection(True)
            tgt = G.Point3d(cx, cy, 4.0); dv = G.Vector3d(1, 1, -0.75); dv.Unitize()
            vp.SetCameraLocations(tgt, tgt - dv * 80); vp.CameraUp = G.Vector3d.ZAxis
            bb = G.BoundingBox.Empty
            for i in ids: bb.Union(doc.Objects.FindId(i).Geometry.GetBoundingBox(True))
            vp.ZoomBoundingBox(bb)
            v.Redraw()
            vc = Rhino.Display.ViewCapture(); vc.Width = 3200; vc.Height = 2400; vc.DrawAxes = False; vc.DrawGrid = False; vc.DrawGridAxes = False; vc.TransparentBackground = False
            vc.CaptureToBitmap(v).Save(os.path.join(OUT, "karamba-model-%s-%s.png" % (roof, case)), System.Drawing.Imaging.ImageFormat.Png)
            for i in ids: doc.Objects.Delete(i, True)
            legend["%s %s" % (roof, case)] = {"load_case": lc, "allowable_MPa": allow, "max_compression_utilisation": round(umax, 3), "max_tension_utilisation": round(-umin, 3),
                                              "max_compression_MPa": round(umax * allow, 2), "max_tension_MPa": round(-umin * allow, 2),
                                              "colour_scale": "white 0, full red (compression) / blue (tension) at 60 %% of %d MPa" % allow}
    doc.Layers.Delete(li, True)
    for i, s in vis.items(): doc.Layers[i].IsVisible = s
    doc.Views.Redraw(); doc.Modified = False
    json.dump(legend, open(os.path.join(OUT, "legend.json"), "w"), indent=1)
    return legend
