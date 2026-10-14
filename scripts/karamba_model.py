"""Karamba3D model of the buttressed 10 x 10 m pyramid roof: roof shell, walls, buttresses, ring beams, the cast rib
grid (option A or B from the roof-grid sheets 08 / 09), supports and loads.

Builds an idealised FE model as plain geometry that you wire into Karamba components. Paste into a Python 3 Script
component (Rhino 8) or GhPython (Rhino 7). The geometry core (`build_model`) is pure Python, so it also runs outside Rhino:
`python scripts/karamba_model.py` prints a summary of the three variants and checks that everything shares nodes.
Units: millimetres (Karamba converts from the Rhino document units).

Roof grid (`grid` input), as on the drawing set:
  A   ruled-surface columns: 10 bays along the eave, columns converge to the crown; every other column stops on a
      horizontal rib where the spacing reaches `min_pitch` (+6.13), the rest stop on the next one (+7.77), only the
      hips go on to the crown ring. Horizontal ribs at +4.31, +6.13, +7.77. Levels are computed exactly as in
      details/roof_grid.py, so they match the sheets.
  B   diamond lattice: two families of diagonals parallel to the hips, 8 diamonds along the eave, every diagonal ends
      on a hip; only the bottom ring (solid base) and the crown ring.
  -   (anything else) plain shell, no ribs: the baseline.
The roof mesh follows the ribs (grid A: rows at the rib levels, columns on the rib lines, the mesh halves where
columns stop; grid B: a diamond mesh on the two diagonal families), so every rib is a chain of beams on shell nodes.
The plain shell uses the grid B mesh without ribs (even element sizes up to the crown).

Idealisation (state it in your report):
  - Everything is modelled on mid-surfaces / centrelines. The ring beam = the 300 solid roof base, at its CENTROID
    (z = wall_h + 150) on the wall centreline; the roof shell, the walls and the ring beam meet there. Ribs start on
    the ring beam (on the drawings they rise out of the solid base) and end on a rib ring, a hip or the crown ring.
  - Roof = four planar shells from the ring beam to the crown ring. The crown ring half side is the shell mid-surface
    at the crown (700 for the drawing geometry), snapped to the grid B mesh so all three variants share one geometry.
  - The rib core (layer 2 + 160 zone, 160 x 240) is centred on the shell mid-surface at the eave, so the rib beams
    sit on the shell nodes without eccentricity. The shell keeps its full thickness under the ribs (a small overlap).
  - Walls = four vertical shells from the ground to the ring beam. Buttresses = one vertical shell per buttress on its
    axis (as on the floor plan: about every 1.5 m, corners included, 8 per side), from the wall mid-plane to
    `but_total` from the inner face, ground to the ring beam. Wall and roof nodes meet only on the ring beam
    (the ring beam is split at every node of both), so the wall mesh can follow the buttress bays.
  - Footing not modelled: supports are fixed (or pinned) at z = 0. Add the soil/footing as springs if you need it.
  - Printed hollow layers are replaced by uniform thickness + an equivalent density (`gamma_*` outputs).

INPUTS (all optional; defaults match details/pyramid_drawings.py and details/roof_grid.py)
    grid         item str    "A", "B" or "none"                     (default "A")
    mesh_size    item float  target element size, mm                (default 500)
    clear        item float  clear inside plan dimension, square, mm (default 10000)
    wall_h       item float  ground to top of wall (eave), mm        (default 2500)
    rise         item float  roof height above the eave, mm          (default 6000)
    opening      item float  clear crown opening, mm                 (default 1000)
    but_spacing  item float  target buttress spacing, mm             (default 1500)
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
    but_meshes     list Mesh    all buttresses    -> Mesh to Shell (buttress section)
    ring_lines     list Line    ring beam         -> Line to Beam (rectangular 400 x 300, the solid roof base)
    crown_lines    list Line    crown ring        -> Line to Beam (rectangular, e.g. 200 x 200, assumed)
    rib_lines      list Line    rib grid (empty for "none") -> Line to Beam, Id = rib_ids
    rib_ids        list str     "col" / "hring" / "hip" (A) or "diag" / "hip" (B), one per rib_lines item
    supports       list Point   base nodes        -> Support
    cladding       item Vector  kN/m2 on roof_meshes (Mesh Load, Z down)
    wind_vecs      list Vector  kN/m2 per roof face   (Mesh Load, one per roof_meshes item, same order)
    wind_walls     list Vector  kN/m2 per wall face   (Mesh Load, one per wall_meshes item, same order)
    t_roof, t_wall, t_but   mm  section thicknesses
    rib_w, rib_d            mm  rib cross-section (160 x 240 on the drawings)
    gamma_roof, gamma_wall  kN/m3 equivalent density for the printed hollow sections
    material       str          values for a custom Karamba Material
    info           str          counts, areas, rib lengths and weights to cross-check Karamba's results
"""
import math

# section of the printed shell, square to the slope (pyramid_drawings.py): leaf 160 -> 80, lattice zone 160, skin 80
T_BASE, T_CROWN = 400.0, 320.0
RIB_W, RIB_D = 160.0, 240.0


def build_model(grid="A", mesh_size=500.0, clear=10000.0, wall=400.0, base_h=300.0, wall_h=2500.0, rise=6000.0,
                open_=1000.0, but_total=1000.0, but_spacing=1500.0, crown_ring=True,
                n_cols=10, min_pitch=500.0, n_diamonds=8):
    grid = str(grid or "").strip().upper()
    grid = grid if grid in ("A", "B") else "none"
    half = clear / 2
    d_b = half + wall / 2                              # wall centreline = ring beam, half side
    z_b = wall_h + base_h / 2                          # centroid of the 300 solid roof base = base of the roof shell
    z_c = wall_h + rise
    # drawing geometry: shell mid-surface half width at the eave / crown (roof_grid.HALFB / TOPB)
    run = half - open_ / 2
    sh = 1.0 / math.sin(math.atan2(rise, run))         # horizontal width per unit thickness square to the slope
    halfb = half + T_BASE * sh / 2
    topb = open_ / 2 + T_CROWN * sh / 2
    kx = (halfb - topb) / rise
    # grid B mesh step; the crown ring sits on it (all variants use the same crown, so they compare like for like)
    m_b = max(1, int(round(2 * d_b / n_diamonds / mesh_size)))
    s_b = 2 * d_b / n_diamonds / m_b
    t_top = max(1, int(round(2 * topb / s_b)))
    d_c = t_top * s_b / 2
    slant = math.hypot(d_b - d_c, z_c - z_b)

    def W(z):                                           # half width of the model roof face at height z
        return d_b + (d_c - d_b) * (z - z_b) / (z_c - z_b)

    def z_of(w):
        return z_b + (d_b - w) / (d_b - d_c) * (z_c - z_b)

    def rows_between(levels):
        """roof row heights: the given levels, each interval split into elements of about mesh_size along the slope"""
        zs = [levels[0]]
        for a, b in zip(levels, levels[1:]):
            n = max(1, int(math.ceil((b - a) * slant / (z_c - z_b) / mesh_size)))
            zs += [a + (b - a) * k / n for k in range(1, n + 1)]
        return zs

    # buttress axes along each side (as pyramid_drawings.but_pos): equal bays on the wall centreline, corners included
    nb = max(1, int(round(2 * d_b / but_spacing)))
    but_x = [-d_b + 2 * d_b * k / nb for k in range(nb + 1)]
    q = max(1, int(round(2 * d_b / nb / mesh_size)))
    wall_x = [-d_b + 2 * d_b * k / (nb * q) for k in range(nb * q + 1)]
    n_w = max(1, int(math.ceil(z_b / mesh_size)))
    wall_z = [z_b * j / n_w for j in range(n_w + 1)]
    fin_len = half + but_total - d_b
    n_f = max(1, int(math.ceil(fin_len / mesh_size)))

    # ---- grid A levels and roof rows (in the drawings' terms: heights above the eave, roof_grid.H1 / H2)
    levels_a = []
    if grid == "A":
        if n_cols % 2:
            raise ValueError("n_cols must be even")
        col_pitch = 2 * halfb / n_cols
        h1 = (1 - min_pitch / col_pitch) * halfb / kx
        h2 = (1 - min_pitch / (2 * col_pitch)) * halfb / kx
        levels_a = [wall_h + h for h in (h1 / 2, h1, h2)]
        if not all(z_b < z < z_c for z in levels_a):
            raise ValueError("grid A rib levels fall outside the roof - check min_pitch / n_cols")
        m_a = max(1, int(round(2 * d_b / n_cols / mesh_size)))
        n0 = n_cols * m_a
        n1 = n0 // 2
        n2 = n1 // 2 if n1 % 2 == 0 else n1
        zs = rows_between([z_b] + levels_a + [z_c])
        rows = [(z, n0 if z <= levels_a[1] + 1e-6 else n1 if z <= levels_a[2] + 1e-6 else n2) for z in zs]

    out = {"grid": grid, "roof": [], "wall": [], "but": [], "ring": [], "crown": [], "ribs": [], "supports": []}
    for k in range(4):
        th = math.radians(90 * k)
        n = (math.cos(th), math.sin(th)); t = (-math.sin(th), math.cos(th))

        def P(dist, x, z):                              # dist out from the centre along n, x along the side, z up
            return (_r(dist * n[0] + x * t[0]), _r(dist * n[1] + x * t[1]), _r(z))
        out_roof = (n[0], n[1], (d_b - d_c) / (z_c - z_b))      # outward normal direction of this roof face
        V, F, idx, ribs = [], [], {}, []

        def vid(key, p):
            if key not in idx:
                idx[key] = len(V); V.append(p)
            return idx[key]

        def chain(keys, rid):
            ribs.extend((V[idx[a]], V[idx[b]], rid) for a, b in zip(keys, keys[1:]))

        if grid == "A":
            for r, (z, nr) in enumerate(rows):
                for i in range(nr + 1):
                    vid((r, i), P(W(z), (-1 + 2.0 * i / nr) * W(z), z))
            for r in range(len(rows) - 1):
                na, nb_ = rows[r][1], rows[r + 1][1]
                if na == nb_:
                    F += [(idx[r, i], idx[r, i + 1], idx[r + 1, i + 1], idx[r + 1, i]) for i in range(na)]
                else:                                   # the mesh halves above a rib level: 3 triangles per upper element
                    for i in range(nb_):
                        b0, b1, b2 = idx[r, 2 * i], idx[r, 2 * i + 1], idx[r, 2 * i + 2]
                        t0, t1 = idx[r + 1, i], idx[r + 1, i + 1]
                        F += [(b0, b1, t0), (b1, b2, t1), (b1, t1, t0)]
            base = [V[idx[0, i]] for i in range(rows[0][1] + 1)]
            top = [V[idx[len(rows) - 1, i]] for i in range(rows[-1][1] + 1)]
            for c in range(n_cols):                     # column c (0 = left hip); the right hip is the next face's left hip
                stop = z_c if c == 0 else levels_a[1] if c % 2 else levels_a[2]
                xi = -1 + 2.0 * c / n_cols
                keys = []
                for r, (z, nr) in enumerate(rows):
                    if z > stop + 1e-6:
                        break
                    keys.append((r, int(round((xi + 1) / 2 * nr))))
                chain(keys, "hip" if c == 0 else "col")
            for zl in levels_a:                         # horizontal ribs
                r = min(range(len(rows)), key=lambda rr: abs(rows[rr][0] - zl))
                chain([(r, i) for i in range(rows[r][1] + 1)], "hring")
        else:                                           # grid B and the plain shell: diamond mesh, i / j = steps along the two diagonal families
            N = n_diamonds * m_b

            def node(i, j):
                w = (i + j) * s_b / 2
                return vid((i, j), P(w, (i - j) * s_b / 2, z_of(w)))
            for i in range(N + 1):
                for j in range(N + 1 - i):
                    if i + j >= t_top:
                        node(i, j)
            for i in range(N):
                for j in range(N - i):
                    s0 = i + j
                    if s0 >= t_top and s0 + 2 <= N:
                        F.append((idx[i, j], idx[i + 1, j], idx[i + 1, j + 1], idx[i, j + 1]))
                    elif s0 + 1 == N and s0 >= t_top:              # along the eave
                        F.append((idx[i, j], idx[i + 1, j], idx[i, j + 1]))
                    elif s0 + 1 == t_top:                         # along the crown
                        F.append((idx[i + 1, j], idx[i + 1, j + 1], idx[i, j + 1]))
            base = [V[idx[i, N - i]] for i in range(N + 1)]
            top = [V[idx[i, t_top - i]] for i in range(t_top + 1)]
            if grid == "B":
                chain([(0, j) for j in range(N, t_top - 1, -1)], "hip")
            for d in range(1, n_diamonds if grid == "B" else 0):
                a = d * m_b
                chain([(a, j) for j in range(N - a, max(0, t_top - a) - 1, -1)], "diag")
                chain([(i, a) for i in range(N - a, max(0, t_top - a) - 1, -1)], "diag")
        out["roof"].append((V, _orient(V, F, out_roof)))
        out["ribs"] += ribs

        # wall: columns on the buttress bays
        wv = [P(d_b, x, z) for z in wall_z for x in wall_x]
        nx = len(wall_x)
        wf = [(j * nx + i, j * nx + i + 1, (j + 1) * nx + i + 1, (j + 1) * nx + i) for j in range(n_w) for i in range(nx - 1)]
        out["wall"].append((wv, _orient(wv, wf, (n[0], n[1], 0.0))))
        # ring beam: split at every wall-top node and every roof-eave node
        xs = sorted(set([round(x, 3) for x in wall_x] + [round(p[0] * t[0] + p[1] * t[1], 3) for p in base]))
        xs = [x for i, x in enumerate(xs) if i == 0 or x - xs[i - 1] > 1.0]
        out["ring"] += [(P(d_b, a, z_b), P(d_b, b, z_b)) for a, b in zip(xs, xs[1:])]
        if crown_ring:
            out["crown"] += list(zip(top, top[1:]))
        # buttresses
        for xb in but_x:
            bv = [P(d_b + fin_len * i / n_f, xb, z) for z in wall_z for i in range(n_f + 1)]
            bf = [(j * (n_f + 1) + i, j * (n_f + 1) + i + 1, (j + 1) * (n_f + 1) + i + 1, (j + 1) * (n_f + 1) + i)
                  for j in range(n_w) for i in range(n_f)]
            out["but"].append((bv, bf))
            out["supports"] += bv[1:n_f + 1]
        out["supports"] += wv[:nx]
    out["supports"] = sorted(set(out["supports"]))
    rib_len = sum(_dist(a, b) for a, b, _ in out["ribs"])
    out["geom"] = dict(d_b=d_b, d_c=d_c, z_b=z_b, z_c=z_c, slant=slant, fin_len=fin_len, n_but=4 * len(but_x),
                       but_bay=2 * d_b / nb, roof_area=sum(_area(V, F) for V, F in out["roof"]),
                       wall_area=4 * 2 * d_b * z_b, but_area=4 * len(but_x) * fin_len * z_b, rib_len=rib_len,
                       levels_a=levels_a, topb=topb)
    return out


def _r(v):
    v = round(v, 3)
    return 0.0 if v == 0 else v


def _dist(a, b):
    return math.sqrt(sum((p - q) ** 2 for p, q in zip(a, b)))


def _normal(V, f):
    a, b, c = V[f[0]], V[f[1]], V[f[2]]
    u = [b[i] - a[i] for i in range(3)]; v = [c[i] - a[i] for i in range(3)]
    return (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])


def _orient(V, F, ref):
    """turn every face counter-clockwise seen from the `ref` side (outside)"""
    return [f if sum(a * b for a, b in zip(_normal(V, f), ref)) >= 0 else tuple(reversed(f)) for f in F]


def _area(V, F):
    tot = 0.0
    for f in F:
        for k in range(1, len(f) - 1):
            nrm = _normal(V, (f[0], f[k], f[k + 1]))
            tot += 0.5 * math.sqrt(sum(c * c for c in nrm))
    return tot


def loads(wind_dir_deg, qp, cpe_roof=(0.7, -0.6, -0.7), cpe_wall=(0.8, -0.5, -0.7)):
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


SOLID_ROOF = (0.5 * (160 + 80) + 80 + 0.35 * 160) / 1000      # m of solid concrete per m2 of roof (leaf + skin + 35 % of the lattice zone)
SOLID_WALL = (160 + 80 + 0.35 * 160) / 1000


def summary(m, gamma=24.0, clad=0.3):
    g = m["geom"]
    A_roof = g["roof_area"] / 1e6
    rib_m3 = g["rib_len"] / 1000 * RIB_W * RIB_D / 1e6
    n_roof = sum(len(F) for _, F in m["roof"])
    lines = ["grid {}: {} roof elements, {} buttresses ({} per side, bays {:.0f}), crown ring half side {:.0f} (drawings {:.0f})".format(
                 m["grid"], n_roof, g["n_but"], g["n_but"] // 4, g["but_bay"], g["d_c"], g["topb"]),
             "roof shell area {:.0f} m2, wall area {:.0f} m2, buttresses {:.1f} m2".format(A_roof, g["wall_area"] / 1e6, g["but_area"] / 1e6),
             "expected self weight: roof {:.0f} kN + cladding {:.0f} kN, wall {:.0f} kN".format(
                 A_roof * SOLID_ROOF * gamma, A_roof * clad, g["wall_area"] / 1e6 * SOLID_WALL * gamma)]
    if m["ribs"]:
        lines.append("ribs {:.0f} m ({} beams), {:.1f} m3 cast concrete = {:.0f} kN".format(
            g["rib_len"] / 1000, len(m["ribs"]), rib_m3, rib_m3 * gamma))
    if g["levels_a"]:
        lines.append("grid A horizontal ribs at " + ", ".join("+{:.2f}".format(z / 1000) for z in g["levels_a"]))
    return "\n".join(lines)


def check(m, tol=1.0):
    """every beam end is a shell node, the faces meet on the hips, the walls and roof meet on the ring beam"""
    key = lambda p: tuple(int(round(c / tol)) for c in p)
    roof = set(key(p) for V, _ in m["roof"] for p in V)
    wall = set(key(p) for V, _ in m["wall"] for p in V)
    ring = set(key(p) for a, b in m["ring"] for p in (a, b))
    errs = []
    errs += ["rib end off the roof mesh {}".format(p) for a, b, _ in m["ribs"] for p in (a, b) if key(p) not in roof]
    errs += ["crown ring end off the roof mesh {}".format(p) for a, b in m["crown"] for p in (a, b) if key(p) not in roof]
    z_b = m["geom"]["z_b"]
    errs += ["roof eave node not on the ring beam {}".format(p) for V, _ in m["roof"] for p in V if abs(p[2] - z_b) < tol and key(p) not in ring]
    errs += ["wall top node not on the ring beam {}".format(p) for V, _ in m["wall"] for p in V if abs(p[2] - z_b) < tol and key(p) not in ring]
    errs += ["buttress not attached to the wall {}".format(V[0]) for V, _ in m["but"] if key(V[0]) not in wall]
    for k in range(4):                                  # right hip of face k = left hip of face k+1
        on_hip = lambda V: set(key(p) for p in V if abs(abs(p[0]) - abs(p[1])) < tol and p[2] > z_b + tol)
        shared = on_hip(m["roof"][k][0]) & on_hip(m["roof"][(k + 1) % 4][0])
        if len(shared) < 3:
            errs.append("faces {} and {} share only {} hip nodes".format(k, (k + 1) % 4, len(shared)))
    return errs


# =============== Grasshopper glue (runs only inside Rhino) ===============
def _gh_main():
    import Rhino.Geometry as rg
    G = globals()
    get = lambda k, d: G[k] if G.get(k) is not None else d
    ms, wd, qp, clad = get("mesh_size", 500.0), get("wind_dir", 0.0), get("qp", 0.9), get("clad", 0.3)
    gam, fck, kf = get("gamma", 24.0), get("fck", 30.0), get("kf", 0.7)
    cr, fixed = get("crown_ring", True), get("fixed", True)
    m = build_model(get("grid", "A"), ms, clear=get("clear", 10000.0), wall_h=get("wall_h", 2500.0), rise=get("rise", 6000.0),
                    open_=get("opening", 1000.0), but_spacing=get("but_spacing", 1500.0), crown_ring=cr)

    def to_mesh(vf):
        V, F = vf
        me = rg.Mesh()
        for p in V:
            me.Vertices.Add(*p)
        for f in F:
            me.Faces.AddFace(*f)
        me.Normals.ComputeNormals(); me.Compact()
        return me
    line = lambda a, b: rg.Line(rg.Point3d(*a), rg.Point3d(*b))
    out = {}
    out["roof_meshes"] = [to_mesh(x) for x in m["roof"]]
    out["wall_meshes"] = [to_mesh(x) for x in m["wall"]]
    out["but_meshes"] = [to_mesh(x) for x in m["but"]]
    out["ring_lines"] = [line(a, b) for a, b in m["ring"]]
    out["crown_lines"] = [line(a, b) for a, b in m["crown"]]
    out["rib_lines"] = [line(a, b) for a, b, _ in m["ribs"]]
    out["rib_ids"] = [rid for _, _, rid in m["ribs"]]
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
    t_roof = 0.5 * (T_BASE + T_CROWN); t_wall = 400.0; t_but = 400.0
    out["t_roof"], out["t_wall"], out["t_but"] = t_roof, t_wall, t_but
    out["rib_w"], out["rib_d"] = RIB_W, RIB_D
    out["gamma_roof"] = gam * SOLID_ROOF * 1000 / t_roof
    out["gamma_wall"] = gam * SOLID_WALL * 1000 / t_wall
    E = 22 * ((fck + 8) / 10) ** 0.3 * kf                         # GPa, EC2 Ecm, knocked down
    out["material"] = ("E = {:.0f} kN/cm2 (Ecm {:.1f} GPa x kf), G = {:.0f} kN/cm2, gamma = see gamma_roof / gamma_wall, "
                       "fc = {:.1f} kN/cm2 (fck/1.5*kf), ft = 0.0 (printed layers: take no tension). "
                       "Ribs and ring beam are cast: full gamma {:g} kN/m3".format(E * 100, E, E * 100 / 2.4, fck / 1.5 * kf / 10, gam))
    errs = check(m)
    out["info"] = summary(m, gam, clad) + "\nfixed supports: {}, wind {} deg, qp {} kN/m2".format(fixed, wd, qp) + (
        "\nWARNING: " + "; ".join(errs[:5]) if errs else "")
    G.update(out)


try:
    import Rhino                      # inside Grasshopper (__name__ is "__main__" there too, so test for Rhino instead)
    _gh_main()
except ImportError:
    if __name__ == "__main__":
        for gname in ("none", "A", "B"):
            mm = build_model(gname)
            print(summary(mm))
            errs = check(mm)
            print("connectivity: " + ("OK" if not errs else "{} problems, e.g. {}".format(len(errs), errs[:3])))
            print()
