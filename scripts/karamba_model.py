"""Karamba3D model of the buttressed pyramid roof: roof shell, walls, buttresses, ring beams, the cast rib grid
(option A or B from the roof-grid sheets 08 / 09), supports and loads. Fully parametric: every dimension below is an
optional input, so sliders (and Galapagos / Octopus) can drive the shape, the thicknesses and the heights of all
three options.

Paste into a Python 3 Script component (Rhino 8) or GhPython (Rhino 7). Add an input for each parameter you want to
change, named exactly as in PARAMETERS; inputs you leave out (or unconnected) use the default. The geometry core
(`build_model`) is pure Python: `python scripts/karamba_model.py` prints the three variants and checks that
everything shares nodes. Units: millimetres (Karamba converts from the Rhino document units).

Roof grid (`grid` input), as on the drawing set:
  A   ruled-surface columns: `n_cols` bays along the eave, columns converge to the crown; every other column stops on
      a horizontal rib where the spacing reaches `min_pitch`, the rest stop on the next one, only the hips go on to the
      crown ring. Horizontal ribs at half the first stop level and at the two stop levels (+4.31, +6.13, +7.77 with
      the defaults, computed exactly as in details/roof_grid.py).
  B   diamond lattice: two families of diagonals parallel to the hips, `n_diamonds` diamonds along the eave, every
      diagonal ends on a hip; only the bottom ring (solid base) and the crown ring.
  none  plain shell, no ribs: the baseline.
The roof mesh follows the ribs (grid A: rows at the rib levels, columns on the rib lines, the mesh halves where
columns stop; grid B: a diamond mesh on the two diagonal families), so every rib is a chain of beams on shell nodes.
The plain shell uses the grid B mesh without ribs (even element sizes up to the crown).

Idealisation (state it in your report):
  - Everything is modelled on mid-surfaces / centrelines. The ring beam = the solid roof base (wall x base_h), at its
    CENTROID on the wall centreline; the roof shell, the walls and the ring beam meet there. Ribs start on the ring
    beam (on the drawings they rise out of the solid base) and end on a rib ring, a hip or the crown ring.
  - Roof = four planar shells from the ring beam to the crown ring; the crown ring sits on the shell mid-surface at
    the crown (the opening plus half the crown thickness).
  - Roof thickness varies with height as on the drawings: leaf (leaf_base -> leaf_crown) + lattice zone + skin,
    square to the slope. `t_roof_elems` gives one thickness per roof element; the printed hollow layers are replaced
    by an equivalent density (`gamma_roof`) so the weight is right.
  - The rib core is centred on the shell mid-surface, so the rib beams sit on the shell nodes without eccentricity.
    The shell keeps its full thickness under the ribs (a small overlap).
  - Walls = four vertical shells from the ground to the ring beam. Buttresses = one vertical shell per buttress on its
    axis (equal bays of about `but_spacing`, corners included), from the wall mid-plane to `but_total` from the inner
    face, ground to the ring beam. Wall and roof nodes meet only on the ring beam (it is split at every node of both).
  - Footing not modelled: supports are fixed (or pinned) at z = 0. Add the soil/footing as springs if you need it.

PARAMETERS (inputs, all optional; defaults = the drawing set). Lengths in mm.
  variant      grid         "A", "B" or "none"                                         "A"
  mesh         mesh_size    target element size                                        500
  plan         clear        clear inside dimension of the square plan                  10000
               wall         wall thickness (= ring beam width)                         400
  heights      wall_h       ground to top of wall (eave)                               2500
               base_h       solid roof base height (= ring beam depth)                 300
               rise         roof height above the eave                                 6000
               slope        roof angle in degrees; if given it replaces rise           (none)
               opening      clear crown opening                                        1000
  roof layers  leaf_base    structural leaf (layers 1 + 2) at the eave                 160
  (square to   leaf_crown   structural leaf at the crown                               80
   the slope)  lattice      zig-zag lattice / air zone                                 160
               skin         outer skin                                                 80
               fill         solid share of the lattice zone (zig-zag), 0..1            0.35
  ribs         rib_w        rib width                                                  160
               rib_d        rib depth                                                  240
               n_cols       grid A: column bays along the eave (even)                  10
               min_pitch    grid A: column spacing where every other column stops      500
               n_diamonds   grid B: diamonds along the eave                            8
  crown        crown_ring   add a crown compression ring                               True
               crown_b      crown ring width                                           200
               crown_h      crown ring depth                                           200
  buttresses   but_spacing  target buttress spacing along the wall                     1500
               but_total    buttress depth from the inner wall face                    1000
               but_w        buttress width (shell thickness)                           400
  loads        wind_dir     direction the wind blows TOWARD, degrees from +X, ccw      0
               qp           peak wind pressure, kN/m2                                  0.9
               clad         cladding + finishes on the roof, kN/m2                     0.3
               gamma        concrete density, kN/m3                                    24
               fck          characteristic strength, MPa                               30
               kf           printing / interface knock-down                            0.7
               fixed        True fixed supports, False pinned                          True

OUTPUTS - wire as in the README ("Karamba model" section)
    roof_meshes    list Mesh    4 roof faces      -> Mesh to Shell (roof section)
    wall_meshes    list Mesh    4 wall faces      -> Mesh to Shell (wall section)
    but_meshes     list Mesh    all buttresses    -> Mesh to Shell (buttress section)
    ring_lines     list Line    ring beam         -> Line to Beam (ring_b x ring_h, the solid roof base)
    crown_lines    list Line    crown ring        -> Line to Beam (crown_b x crown_h)
    rib_lines      list Line    rib grid (empty for "none") -> Line to Beam, Id = rib_ids
    rib_ids        list str     "col" / "hring" / "hip" (A) or "diag" / "hip" (B), one per rib_lines item
    supports       list Point   base nodes        -> Support
    cladding       item Vector  kN/m2 on roof_meshes (Mesh Load, Z down)
    wind_vecs      list Vector  kN/m2 per roof face   (Mesh Load, one per roof_meshes item, same order)
    wind_walls     list Vector  kN/m2 per wall face   (Mesh Load, one per wall_meshes item, same order)
    t_roof         item float   average roof thickness, mm (one shell section for the whole roof)
    t_roof_elems   tree float   roof thickness per element, one branch per roof mesh (varying thickness)
    t_wall, t_but  item float   wall / buttress thickness, mm
    ring_b, ring_h, crown_b, crown_h, rib_w, rib_d   beam sections, mm
    gamma_roof, gamma_wall  kN/m3 equivalent density for the printed hollow sections
    rise, slope    item float   the roof height (mm) and angle (deg) actually built
    concrete       item float   total concrete volume, m3 (an objective for optimising)
    weight         item float   total self weight, kN, without cladding (cross-check Karamba's reactions)
    material       str          values for a custom Karamba Material
    info           str          counts, areas, rib lengths, weights and warnings
"""
import math

DEFAULTS = dict(
    grid="A", mesh_size=500.0, clear=10000.0, wall=400.0, wall_h=2500.0, base_h=300.0, rise=6000.0, slope=None,
    opening=1000.0, leaf_base=160.0, leaf_crown=80.0, lattice=160.0, skin=80.0, fill=0.35,
    rib_w=160.0, rib_d=240.0, n_cols=10, min_pitch=500.0, n_diamonds=8,
    crown_ring=True, crown_b=200.0, crown_h=200.0, but_spacing=1500.0, but_total=1000.0, but_w=400.0,
)
WALL_LEAVES = 0.6          # wall: inner leaf 160 + outer layer 80 of 400 are printed solid, the 160 zone between is lattice


def build_model(**kw):
    p = dict(DEFAULTS)
    p.update({k: v for k, v in kw.items() if v is not None})
    warn = []
    grid = str(p["grid"] or "").strip().upper()
    grid = grid if grid in ("A", "B") else "none"
    ms = float(p["mesh_size"])
    half = p["clear"] / 2
    d_b = half + p["wall"] / 2                         # wall centreline = ring beam, half side
    z_b = p["wall_h"] + p["base_h"] / 2                # centroid of the solid roof base = base of the roof shell
    run = half - p["opening"] / 2
    if run <= 0:
        raise ValueError("opening must be smaller than the clear plan")
    if p["slope"]:
        if not 5 <= p["slope"] < 85:
            raise ValueError("slope must be between 5 and 85 degrees")
        rise = run * math.tan(math.radians(p["slope"]))
    else:
        rise = float(p["rise"])
    slope = math.degrees(math.atan2(rise, run))
    if rise <= p["base_h"]:
        raise ValueError("rise must be larger than base_h")
    z_c = p["wall_h"] + rise
    lat, skin = p["lattice"], p["skin"]
    t_base, t_crown = p["leaf_base"] + lat + skin, p["leaf_crown"] + lat + skin
    if min(p["leaf_base"], p["leaf_crown"], lat, skin) < 0 or t_crown <= 0:
        raise ValueError("layer thicknesses must be positive")
    # shell mid-surface half width at the eave and at the crown, as on the drawings (roof_grid.HALFB / TOPB)
    sh = 1.0 / math.sin(math.radians(slope))           # horizontal width per unit thickness square to the slope
    halfb = half + t_base * sh / 2
    d_c = p["opening"] / 2 + t_crown * sh / 2
    if d_c >= d_b - ms / 2:
        raise ValueError("crown too wide for the plan - reduce opening or the roof thickness")
    kx = (halfb - d_c) / rise
    slant = math.hypot(d_b - d_c, z_c - z_b)

    def W(z):                                           # half width of the model roof face at height z
        return d_b + (d_c - d_b) * (z - z_b) / (z_c - z_b)

    def z_of(w):
        return z_b + (d_b - w) / (d_b - d_c) * (z_c - z_b)

    def leaf(z):
        return p["leaf_base"] + (p["leaf_crown"] - p["leaf_base"]) * (z - p["wall_h"]) / rise

    def band_rows(a, b, n_band, n_first):
        """row heights from a to b: each row about as tall (along the slope) as the elements are wide, at most mesh_size,
        so the elements stay near square as the face narrows towards the crown. The first row takes the width of the
        row below it (n_first), so the triangles where the mesh halves come out near 45/45/90."""
        h = lambda z, nn: min(ms, 2 * W(z) / nn) * (z_c - z_b) / slant
        z, c, nn = a, 0.0, n_first
        while z + h(z, nn) < b - 1e-9:
            z += h(z, nn); c += 1; nn = n_band
        c += (b - z) / h(z, nn)
        k = max(1, int(round(c)))
        zs, z, nn = [], a, n_first
        for _ in range(k - 1):
            z += h(z, nn) * c / k; nn = n_band
            if z >= b - 1e-6:
                break
            zs.append(z)
        return zs + [b]

    # buttress axes along each side (as pyramid_drawings.but_pos): equal bays on the wall centreline, corners included
    nb = max(1, int(round(2 * d_b / p["but_spacing"])))
    but_x = [-d_b + 2 * d_b * k / nb for k in range(nb + 1)]
    q = max(1, int(round(2 * d_b / nb / ms)))
    wall_x = [-d_b + 2 * d_b * k / (nb * q) for k in range(nb * q + 1)]
    n_w = max(1, int(math.ceil(z_b / ms)))
    wall_z = [z_b * j / n_w for j in range(n_w + 1)]
    fin_len = half + p["but_total"] - d_b
    if fin_len <= 0:
        raise ValueError("but_total must be larger than half the wall thickness")
    n_f = max(1, int(math.ceil(fin_len / ms)))

    # ---- grid A: stop levels (drawings' terms: heights above the eave, roof_grid.H1 / H2) and roof rows
    levels_a, stops = [], (z_c, z_c)
    if grid == "A":
        n_cols = int(p["n_cols"])
        if n_cols % 2 or n_cols < 2:
            n_cols = max(2, n_cols + n_cols % 2)
            warn.append("n_cols must be even: using {}".format(n_cols))
        col_pitch = 2 * halfb / n_cols
        if p["min_pitch"] >= col_pitch:
            raise ValueError("min_pitch ({:.0f}) must be smaller than the column spacing at the eave ({:.0f})".format(p["min_pitch"], col_pitch))
        h1 = (1 - p["min_pitch"] / col_pitch) * halfb / kx
        h2 = (1 - p["min_pitch"] / (2 * col_pitch)) * halfb / kx
        cand = [p["wall_h"] + h for h in (h1 / 2, h1, h2)]
        levels_a = [z for z in cand if z_b + ms / 4 < z < z_c - ms / 4]
        if len(levels_a) < 3:
            warn.append("grid A: {} of the 3 rib levels fall outside the roof; those columns run to the crown".format(3 - len(levels_a)))
        L1 = cand[1] if cand[1] in levels_a else None
        L2 = cand[2] if cand[2] in levels_a else None
        stops = (L1 or z_c, L2 or z_c)                  # odd columns stop at L1, even ones at L2
        m_a = max(1, int(round(2 * d_b / n_cols / ms)))
        n0 = n_cols * m_a
        n1 = n0 // 2 if L1 else n0
        n2 = n1 // 2 if (L2 and n1 % 2 == 0) else n1
        n_at = lambda z: n0 if (L1 is None or z <= L1 + 1e-6) else n1 if (L2 is None or z <= L2 + 1e-6) else n2
        breaks = [z_b] + levels_a + [z_c]
        rows = [(z_b, n0)]
        for a, b in zip(breaks, breaks[1:]):
            rows += [(z, n_at(z)) for z in band_rows(a, b, n_at((a + b) / 2), n_at(a))]
    else:
        n_d = max(2, int(p["n_diamonds"]))
        m_b = max(1, int(round(2 * d_b / n_d / ms)))
        s_b = 2 * d_b / n_d / m_b
        N = n_d * m_b
        t_top = min(N - 1, max(1, int(round(2 * d_c / s_b))))     # mesh row nearest the crown; moved onto it below

    out = {"grid": grid, "roof": [], "t_elems": [], "wall": [], "but": [], "ring": [], "crown": [], "ribs": [],
           "supports": [], "warn": warn}
    for k in range(4):
        th = math.radians(90 * k)
        n = (math.cos(th), math.sin(th)); t = (-math.sin(th), math.cos(th))

        def P(dist, x, z):                              # dist out from the centre along n, x along the side, z up
            return (_r(dist * n[0] + x * t[0]), _r(dist * n[1] + x * t[1]), _r(z))
        out_roof = (n[0], n[1], (d_b - d_c) / (z_c - z_b))      # outward normal direction of this roof face
        V, F, idx, ribs = [], [], {}, []

        def vid(key, pt):
            if key not in idx:
                idx[key] = len(V); V.append(pt)
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
                stop = z_c if c == 0 else stops[0] if c % 2 else stops[1]
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
            def node(i, j):
                if i + j == t_top:                      # the top row is moved onto the crown
                    w, x = d_c, (i - j) / float(t_top) * d_c
                else:
                    w, x = (i + j) * s_b / 2, (i - j) * s_b / 2
                return vid((i, j), P(w, x, z_of(w)))
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
                for d in range(1, n_d):
                    a = d * m_b
                    chain([(a, j) for j in range(N - a, max(0, t_top - a) - 1, -1)], "diag")
                    chain([(i, a) for i in range(N - a, max(0, t_top - a) - 1, -1)], "diag")
        F = _orient(V, F, out_roof)
        out["roof"].append((V, F))
        out["t_elems"].append([leaf(sum(V[i][2] for i in f) / len(f)) + lat + skin for f in F])
        out["ribs"] += ribs

        # wall: columns on the buttress bays
        wv = [P(d_b, x, z) for z in wall_z for x in wall_x]
        nx = len(wall_x)
        wf = [(j * nx + i, j * nx + i + 1, (j + 1) * nx + i + 1, (j + 1) * nx + i) for j in range(n_w) for i in range(nx - 1)]
        out["wall"].append((wv, _orient(wv, wf, (n[0], n[1], 0.0))))
        # ring beam: split at every wall-top node and every roof-eave node
        xs = sorted(set([round(x, 3) for x in wall_x] + [round(pt[0] * t[0] + pt[1] * t[1], 3) for pt in base]))
        xs = [x for i, x in enumerate(xs) if i == 0 or x - xs[i - 1] > 1.0]
        out["ring"] += [(P(d_b, a, z_b), P(d_b, b, z_b)) for a, b in zip(xs, xs[1:])]
        if p["crown_ring"]:
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

    # ---- quantities (m3): printed parts at their solid share, cast parts full
    areas = [[_area(V, [f]) for f in F] for V, F in out["roof"]]
    v_shell = sum(a * (tt - lat * (1 - p["fill"])) for ar, ts in zip(areas, out["t_elems"]) for a, tt in zip(ar, ts)) / 1e9
    v_shell_gross = sum(a * tt for ar, ts in zip(areas, out["t_elems"]) for a, tt in zip(ar, ts)) / 1e9
    rib_len = sum(_dist(a, b) for a, b, _ in out["ribs"])
    wall_area = 4 * 2 * d_b * z_b
    vol = dict(shell=v_shell, ribs=rib_len * p["rib_w"] * p["rib_d"] / 1e9,
               ring=8 * d_b * p["wall"] * p["base_h"] / 1e9,
               crown=sum(_dist(a, b) for a, b in out["crown"]) * p["crown_b"] * p["crown_h"] / 1e9,
               walls=wall_area * p["wall"] * (WALL_LEAVES + (1 - WALL_LEAVES) * p["fill"]) / 1e9,
               buttresses=4 * len(but_x) * fin_len * z_b * p["but_w"] / 1e9)
    out["p"] = p
    out["geom"] = dict(d_b=d_b, d_c=d_c, z_b=z_b, z_c=z_c, rise=rise, slope=slope, slant=slant, fin_len=fin_len,
                       n_but=4 * len(but_x), but_bay=2 * d_b / nb, roof_area=sum(sum(a) for a in areas),
                       wall_area=wall_area, rib_len=rib_len, levels_a=levels_a, t_base=t_base, t_crown=t_crown,
                       vol=vol, gamma_ratio_roof=v_shell / v_shell_gross,
                       gamma_ratio_wall=WALL_LEAVES + (1 - WALL_LEAVES) * p["fill"])
    lean = 90 - slope
    if lean > 30:
        warn.append("roof faces lean {:.0f} deg from vertical: check printability (beads shift {:.1f} mm per 10 mm layer)".format(
            lean, 10 / math.tan(math.radians(slope))))
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


def summary(m, gamma=24.0, clad=0.3):
    g, p = m["geom"], m["p"]
    vol = g["vol"]
    n_roof = sum(len(F) for _, F in m["roof"])
    lines = ["grid {}: plan {:.0f} clear, eave +{:.2f}, rise {:.0f}, slope {:.1f} deg, crown opening {:.0f}".format(
                 m["grid"], p["clear"], p["wall_h"] / 1000, g["rise"], g["slope"], p["opening"]),
             "roof {:.0f} -> {:.0f} thick, {} elements, {:.0f} m2; {} buttresses ({} per side, bays {:.0f})".format(
                 g["t_base"], g["t_crown"], n_roof, g["roof_area"] / 1e6, g["n_but"], g["n_but"] // 4, g["but_bay"])]
    if m["ribs"]:
        lines.append("ribs {:.0f} x {:.0f}: {:.0f} m ({} beams)".format(p["rib_w"], p["rib_d"], g["rib_len"] / 1000, len(m["ribs"])))
    if g["levels_a"]:
        lines.append("grid A horizontal ribs at " + ", ".join("+{:.2f}".format(z / 1000) for z in g["levels_a"]))
    lines.append("concrete m3: " + ", ".join("{} {:.1f}".format(k, v) for k, v in vol.items()) +
                 "; total {:.1f} m3 = {:.0f} kN (+ cladding {:.0f} kN)".format(sum(vol.values()), sum(vol.values()) * gamma,
                                                                             g["roof_area"] / 1e6 * clad))
    lines += ["WARNING: " + w for w in m["warn"]]
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
    from Grasshopper import DataTree
    from Grasshopper.Kernel.Data import GH_Path
    G = globals()
    get = lambda k, d: G[k] if G.get(k) is not None else d
    wd, qp, clad = get("wind_dir", 0.0), get("qp", 0.9), get("clad", 0.3)
    gam, fck, kf, fixed = get("gamma", 24.0), get("fck", 30.0), get("kf", 0.7), get("fixed", True)
    out = dict(roof_meshes=[], wall_meshes=[], but_meshes=[], ring_lines=[], crown_lines=[], rib_lines=[], rib_ids=[],
               supports=[], wind_vecs=[], wind_walls=[], t_roof_elems=DataTree[object]())
    try:
        m = build_model(**{k: G.get(k) for k in DEFAULTS})
    except ValueError as e:                             # bad slider combination: empty model + the reason, no crash
        out["info"] = "ERROR: {}".format(e)
        G.update(out)
        return
    p, g = m["p"], m["geom"]

    def to_mesh(vf):
        V, F = vf
        me = rg.Mesh()
        for pt in V:
            me.Vertices.Add(*pt)
        for f in F:
            me.Faces.AddFace(*f)
        me.Normals.ComputeNormals(); me.Compact()
        return me
    line = lambda a, b: rg.Line(rg.Point3d(*a), rg.Point3d(*b))
    out["roof_meshes"] = [to_mesh(x) for x in m["roof"]]
    out["wall_meshes"] = [to_mesh(x) for x in m["wall"]]
    out["but_meshes"] = [to_mesh(x) for x in m["but"]]
    out["ring_lines"] = [line(a, b) for a, b in m["ring"]]
    out["crown_lines"] = [line(a, b) for a, b in m["crown"]]
    out["rib_lines"] = [line(a, b) for a, b, _ in m["ribs"]]
    out["rib_ids"] = [rid for _, _, rid in m["ribs"]]
    out["supports"] = [rg.Point3d(*pt) for pt in m["supports"]]
    for i, ts in enumerate(m["t_elems"]):
        out["t_roof_elems"].AddRange(ts, GH_Path(i))
    out["cladding"] = rg.Vector3d(0, 0, -clad)
    # wind acts normal to the surface: pressure (+) pushes onto the face (against the outward normal)
    cr_, cw_ = loads(wd, qp)
    for meshes, cps, key in ((out["roof_meshes"], cr_, "wind_vecs"), (out["wall_meshes"], cw_, "wind_walls")):
        for me, cp in zip(meshes, cps):
            v = rg.Vector3d(me.FaceNormals[0]); v.Unitize(); v *= -cp * qp
            out[key].append(v)
    areas = [a for V, F in m["roof"] for a in (_area(V, [f]) for f in F)]
    ts = [tt for row in m["t_elems"] for tt in row]
    out["t_roof"] = sum(a * tt for a, tt in zip(areas, ts)) / sum(areas)
    out["t_wall"], out["t_but"] = p["wall"], p["but_w"]
    out["ring_b"], out["ring_h"] = p["wall"], p["base_h"]
    out["crown_b"], out["crown_h"] = p["crown_b"], p["crown_h"]
    out["rib_w"], out["rib_d"] = p["rib_w"], p["rib_d"]
    out["gamma_roof"] = gam * g["gamma_ratio_roof"]
    out["gamma_wall"] = gam * g["gamma_ratio_wall"]
    out["rise"], out["slope"] = g["rise"], g["slope"]
    out["concrete"] = sum(g["vol"].values())
    out["weight"] = out["concrete"] * gam
    E = 22 * ((fck + 8) / 10) ** 0.3 * kf                         # GPa, EC2 Ecm, knocked down
    out["material"] = ("E = {:.0f} kN/cm2 (Ecm {:.1f} GPa x kf), G = {:.0f} kN/cm2, gamma = see gamma_roof / gamma_wall, "
                       "fc = {:.1f} kN/cm2 (fck/1.5*kf), ft = 0.0 (printed layers: take no tension). "
                       "Ribs, ring beam, crown ring and buttresses are cast: full gamma {:g} kN/m3".format(
                           E * 100, E, E * 100 / 2.4, fck / 1.5 * kf / 10, gam))
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
            mm = build_model(grid=gname)
            print(summary(mm))
            errs = check(mm)
            print("connectivity: " + ("OK" if not errs else "{} problems, e.g. {}".format(len(errs), errs[:3])))
            print()
