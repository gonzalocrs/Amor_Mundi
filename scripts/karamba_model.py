"""Karamba3D model of the buttressed 10 x 10 m pyramid roof (roof shell, walls, buttresses, ring beams, supports, loads).

Builds an idealised FE model as plain geometry that you wire into Karamba components. Paste into a Python 3 Script
component (Rhino 8) or GhPython (Rhino 7). The geometry core (`build_model`) is pure Python, so it also runs outside Rhino
(`python scripts/karamba_model.py` prints a summary). Units: millimetres (Karamba converts from the Rhino document units).

Idealisation (state it in your report):
  - Everything is modelled on mid-surfaces / centrelines. The roof base ring sits at the CENTROID of the solid roof base
    (z = WALL_H + 300/2), so the roof shell, wall shell and ring beam share nodes.
  - Roof = four planar shells from the ring beam to the crown ring. Wall = four vertical shells from the ground to the ring beam.
  - Buttress = one vertical shell per side at mid-span, 1000 from the inner wall face, attached along the wall mid-plane,
    top at the centroid of the solid roof base.
  - Footing not modelled: supports are fixed (or pinned) at z = 0. Add the soil/footing as springs if you need it.
  - Printed hollow layers are replaced by uniform thickness + an equivalent density (`gamma_*` outputs) so the weight is right.

INPUTS (all optional; defaults match details/pyramid_drawings.py)
    mesh_size    item float  target element size, mm                (default 500)
    wind_dir     item float  direction the wind blows TOWARD, degrees from +X, ccw (default 0: blows toward +X)
    qp           item float  peak wind pressure, kN/m2              (default 0.9)
    clad         item float  cladding + finishes on the roof, kN/m2 (default 0.3)
    gamma        item float  concrete density, kN/m3                (default 24)
    fck          item float  characteristic strength, MPa           (default 30)
    kf           item float  printing / interface knock-down        (default 0.7)
    crown_ring   item bool   add a crown compression ring           (default True)
    fixed        item bool   True fixed supports, False pinned      (default True)

OUTPUTS - wire as in the README ("Karamba model" section)
    roof_meshes    list Mesh    4 roof faces      -> Mesh to Shell (roof section)
    wall_meshes    list Mesh    4 wall faces      -> Mesh to Shell (wall section)
    but_meshes     list Mesh    4 buttresses      -> Mesh to Shell (buttress section)
    ring_lines     list Line    ring beam         -> Line to Beam (rectangular 400 x 300, the solid roof base)
    crown_lines    list Line    crown ring        -> Line to Beam (rectangular, e.g. 200 x 200, assumed)
    supports       list Point   base nodes        -> Support
    cladding       item Vector  kN/m2 on roof_meshes (Mesh Load, Z down)
    wind_vecs      list Vector  kN/m2 per roof face   (Mesh Load, one per roof_meshes item, same order)
    wind_walls     list Vector  kN/m2 per wall face   (Mesh Load, one per wall_meshes item, same order)
    t_roof, t_wall, t_but   mm  section thicknesses
    gamma_roof, gamma_wall  kN/m3 equivalent density for the printed hollow sections
    material       str          values for a custom Karamba Material
    info           str          counts, areas and weights to cross-check Karamba's results
"""
import math


def build_model(mesh_size=500.0, clear=10000.0, wall=400.0, beam_h=300.0, wall_h=2500.0, rise=6000.0, open_=1000.0,
                but_total=1000.0, t_roof_base=400.0, t_roof_crown=320.0, crown_ring=True):
    half = clear / 2
    d_b = half + wall / 2                              # centreline half side of the wall / ring beam
    z_b = wall_h + beam_h / 2                          # centroid of the 300 solid roof base (no separate ring beam) = base of the roof shell
    d_c = open_ / 2 + 0.25 * (t_roof_crown)            # crown ring centreline half side (assumed)
    z_c = wall_h + rise
    slant = math.hypot(d_b - d_c, z_c - z_b)
    n_u = 2 * max(1, math.ceil(2 * d_b / mesh_size / 2))      # even, so there is a node at mid-span for the buttress
    n_v = max(1, math.ceil(slant / mesh_size))
    n_w = max(1, math.ceil(z_b / mesh_size))
    but_len = half + but_total - d_b                    # from the wall mid-plane to the buttress outer end
    n_b = max(1, math.ceil(but_len / mesh_size))
    out = {"roof": [], "wall": [], "but": [], "ring": [], "crown": [], "supports": [], "n": (n_u, n_v, n_w, n_b)}
    for k in range(4):
        th = math.radians(90 * k)
        n = (math.cos(th), math.sin(th)); t = (-math.sin(th), math.cos(th))
        pt = lambda dist, u, z: (round(dist * (n[0] + u * t[0]), 3), round(dist * (n[1] + u * t[1]), 3), round(z, 3))
        # roof face: grid of (n_u+1) x (n_v+1) vertices, u across (-1..1 = corner to corner), v up the slope
        def roof_pt(i, j):
            v = j / n_v; w = d_b + (d_c - d_b) * v
            return pt(w, -1 + 2 * i / n_u, z_b + (z_c - z_b) * v)
        out["roof"].append(_grid(roof_pt, n_u, n_v))
        out["wall"].append(_grid(lambda i, j: pt(d_b, -1 + 2 * i / n_u, z_b * j / n_w), n_u, n_w))
        # buttress: vertical plane through the mid-span of the side, from the wall mid-plane outward
        def but_pt(i, j):
            dist = d_b + but_len * i / n_b
            return (round(dist * n[0], 3), round(dist * n[1], 3), round(z_b * j / n_w, 3))
        out["but"].append(_grid(but_pt, n_b, n_w))
        for i in range(n_u):
            out["ring"].append((pt(d_b, -1 + 2 * i / n_u, z_b), pt(d_b, -1 + 2 * (i + 1) / n_u, z_b)))
            if crown_ring:
                out["crown"].append((pt(d_c, -1 + 2 * i / n_u, z_c), pt(d_c, -1 + 2 * (i + 1) / n_u, z_c)))
        for i in range(n_u + 1):
            out["supports"].append(pt(d_b, -1 + 2 * i / n_u, 0.0))
        for i in range(1, n_b + 1):
            out["supports"].append(but_pt(i, 0))
    out["supports"] = sorted(set(out["supports"]))
    out["geom"] = dict(d_b=d_b, d_c=d_c, z_b=z_b, z_c=z_c, slant=slant, but_len=but_len,
                       roof_area=4 * (d_b + d_c) * slant, wall_area=4 * 2 * d_b * z_b / 1.0, but_area=4 * but_len * z_b)
    return out


def _grid(f, nu, nv):
    """quad grid: returns (vertices, faces) with faces as index 4-tuples, counter-clockwise seen from outside"""
    V = [f(i, j) for j in range(nv + 1) for i in range(nu + 1)]
    F = [(j * (nu + 1) + i, j * (nu + 1) + i + 1, (j + 1) * (nu + 1) + i + 1, (j + 1) * (nu + 1) + i)
         for j in range(nv) for i in range(nu)]
    return V, F


def loads(wind_dir_deg, qp, cpe_roof=(0.7, -0.6, -0.7, -0.7), cpe_wall=(0.8, -0.5, -0.7, -0.7)):
    """pressure coefficient per face (windward, leeward, two sides) as the faces face the wind; EN 1991-1-4 order of magnitude only"""
    res_roof, res_wall = [], []
    for k in range(4):
        th = math.radians(90 * k)
        n = (math.cos(th), math.sin(th))
        a = math.radians(wind_dir_deg)
        c = n[0] * math.cos(a) + n[1] * math.sin(a)      # wind blows TOWARD wind_dir: c = -1 windward face, +1 leeward, 0 side face
        idx = 0 if c < -0.7 else 1 if c > 0.7 else 2
        res_roof.append(cpe_roof[idx]); res_wall.append(cpe_wall[idx])
    return res_roof, res_wall


def summary(m, gamma=24.0, clad=0.3, solid_roof=0.256, solid_wall=0.296):
    g = m["geom"]
    A_roof = g["roof_area"] / 1e6
    return ("{} x {} x {} x {} elements/side (across, slope, wall, buttress)\n"
            "roof shell area {:.0f} m2, wall area {:.0f} m2, buttresses {:.1f} m2\n"
            "expected self weight: roof {:.0f} kN + cladding {:.0f} kN, wall {:.0f} kN"
            .format(*m["n"], A_roof, g["wall_area"] / 1e6, g["but_area"] / 1e6, A_roof * solid_roof * gamma,
                    A_roof * clad, g["wall_area"] / 1e6 * solid_wall * gamma))


# =============== Grasshopper glue (runs only inside Rhino) ===============
def _gh_main():
    import Rhino.Geometry as rg
    G = globals()
    get = lambda k, d: G[k] if G.get(k) is not None else d
    ms, wd, qp, clad = get("mesh_size", 500.0), get("wind_dir", 0.0), get("qp", 0.9), get("clad", 0.3)
    gam, fck, kf = get("gamma", 24.0), get("fck", 30.0), get("kf", 0.7)
    cr, fixed = get("crown_ring", True), get("fixed", True)
    m = build_model(ms, crown_ring=cr)

    def to_mesh(vf):
        V, F = vf
        me = rg.Mesh()
        for p in V:
            me.Vertices.Add(*p)
        for f in F:
            me.Faces.AddFace(*f)
        me.Normals.ComputeNormals(); me.Compact()
        return me
    out = {}
    out["roof_meshes"] = [to_mesh(x) for x in m["roof"]]
    out["wall_meshes"] = [to_mesh(x) for x in m["wall"]]
    out["but_meshes"] = [to_mesh(x) for x in m["but"]]
    out["ring_lines"] = [rg.Line(rg.Point3d(*a), rg.Point3d(*b)) for a, b in m["ring"]]
    out["crown_lines"] = [rg.Line(rg.Point3d(*a), rg.Point3d(*b)) for a, b in m["crown"]]
    out["supports"] = [rg.Point3d(*p) for p in m["supports"]]
    out["cladding"] = rg.Vector3d(0, 0, -clad)
    # wind acts normal to the surface: pressure (+) pushes onto the face (against the outward normal)
    cr_, cw_ = loads(wd, qp)
    vecs = []
    for me, cp in zip(out["roof_meshes"], cr_):
        nrm = me.FaceNormals[0] if me.FaceNormals.Count else rg.Vector3d.ZAxis
        v = rg.Vector3d(nrm); v.Unitize(); v *= -cp * qp
        vecs.append(v)
    out["wind_vecs"] = vecs
    wv = []
    for me, cp in zip(out["wall_meshes"], cw_):
        nrm = me.FaceNormals[0]
        v = rg.Vector3d(nrm); v.Unitize(); v *= -cp * qp
        wv.append(v)
    out["wind_walls"] = wv
    solid_roof = (0.5 * (160 + 80) + 80 + 0.35 * 160) / 1000
    solid_wall = (160 + 80 + 0.35 * 160) / 1000
    t_roof = 0.5 * (400 + 320); t_wall = 400.0; t_but = 400.0
    out["t_roof"], out["t_wall"], out["t_but"] = t_roof, t_wall, t_but
    out["gamma_roof"] = gam * solid_roof * 1000 / t_roof
    out["gamma_wall"] = gam * solid_wall * 1000 / t_wall
    E = 22 * ((fck + 8) / 10) ** 0.3 * kf                         # GPa, EC2 Ecm, knocked down
    out["material"] = ("E = {:.0f} kN/cm2 (Ecm {:.1f} GPa x kf), G = {:.0f} kN/cm2, gamma = see gamma_roof / gamma_wall, "
                       "fc = {:.1f} kN/cm2 (fck/1.5*kf), ft = 0.0 (printed layers: take no tension)".format(
                           E * 100, E, E * 100 / 2.4, fck / 1.5 * kf / 10))
    out["info"] = summary(m, gam, clad, solid_roof, solid_wall) + "\nfixed supports: {}, wind {} deg, qp {} kN/m2".format(fixed, wd, qp)
    G.update(out)


try:
    import Rhino                      # inside Grasshopper (__name__ is "__main__" there too, so test for Rhino instead)
    _gh_main()
except ImportError:
    if __name__ == "__main__":
        mm = build_model()
        print(summary(mm))
        nverts = len({v for s_ in ("roof", "wall", "but") for vs, _ in mm[s_] for v in vs})
        print("unique nodes {}, ring segments {}, crown segments {}, supports {}".format(
            nverts, len(mm["ring"]), len(mm["crown"]), len(mm["supports"])))
