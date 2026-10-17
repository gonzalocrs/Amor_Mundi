"""Karamba3D model of the buttressed pyramid roof: roof shell, walls, buttresses, ring beams, the cast rib grid
(option A or B from the roof-grid sheets 08 / 09), supports and loads. Fully parametric: every dimension below is an
optional input, so sliders (and Galapagos / Octopus) can drive the shape, the thicknesses and the heights of all
three options.

Paste into a Python 3 Script component (Rhino 8) or GhPython (Rhino 7). Add an input for each parameter you want to
change, named exactly as in PARAMETERS; inputs you leave out (or unconnected) use the default. The geometry core
(`build_model`) is pure Python: `python scripts/karamba_model.py` prints the three variants and checks that
everything shares nodes. Units: millimetres. Karamba does NOT follow the Rhino document units (its default is
metres): set Karamba3D menu > Physical Units > Geometry Input Units to mm in the .gh.

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
  - Roof = four planar shells from the ring beam to the crown ring; the crown ring sits on the shell surface at
    the crown.
  - Roof build-up, square to the slope, from the room side out (all printed layers are `bead` wide):
        inner bead | rib zone (rib_d, a cavity crossed by the cast ribs) | middle bead | lattice zone (`lattice`,
        wavy bead + insulation, `fill` = solid share) | `outer_beads` outer beads
    = 30 + 160 + 30 + 120 + 30 = 370 with the defaults, constant from eave to crown. No cladding load by default:
    the outer bead is the exposed face and the insulation sits in the lattice zone (add it with `clad`).
  - Structural layers (`all_layers` = False, the default): only the inner and middle beads carry load, as a sandwich
    whose webs are the ribs; the lattice zone and the outer beads are weight only. With `all_layers` = True every
    printed layer counts (the lattice bead at its `fill` share).
  - Karamba's shell is one isotropic layer, so the structural layers are replaced by an EQUIVALENT shell placed on
    their centroid: thickness `t_roof` = sqrt(12 I / A), modulus E x A / t_roof (`E_roof`), density so the whole
    build-up weighs right (`gamma_roof`), and strengths fc, ft x A / t_roof (`fc_roof`, `ft_roof`). Displacements
    are then exact; Karamba's utilisation is exact for in-plane (membrane) stress and on the safe side for bending.
    Karamba's raw stresses are NOT the real skin stresses (multiply by t_roof / A for the membrane part).
  - The ribs sit in the rib zone, centred on the shell surface (the centroid of the two skins), so the rib beams sit
    on the shell nodes without eccentricity. With `all_layers` = True the centroid moves outwards and that rib
    eccentricity is ignored.
  - Walls, from the room side out: inner bead | lattice zone (wall - (1 + outer_beads) x bead, `fill` share) |
    `outer_beads` outer beads. The inner and outer beads carry load as a sandwich tied by the lattice bead (all
    printed layers with `all_layers` = True), as an equivalent shell like the roof (`t_wall`, `E_wall`, ...),
    on the wall centreline (the offset of its centroid is ignored).
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
               ring_w       ring beam width (also the buttress caps)                   = wall
  foundation   footing      True: strip footing on the wall line at z = 0 joining all    False
                            buttress feet + a footing beam under every buttress; the
                            supports move under the footing (cast, Id "footing")
               foot_w       footing width                                              800
               foot_h       footing depth                                              500
               foot_ext     how far the buttress footing reaches beyond the buttress   300
               foot_in      how far the buttress footing reaches inward, from the      0
                            wall line (under the room)
               foot_strip   True: strip on the wall line joining the pads; False:      True
                            separate pads under the buttresses only
  checks       skin_check   True: the roof shell becomes ONE bead-thick skin with the real    False
                            printed E and the whole roof weight, for Buckling Modes:
                            BLFacs = local skin buckling between the ribs (safe side)
               rise         roof height above the eave                                 6000
               slope        roof angle in degrees; if given it replaces rise           (none)
               opening      clear crown opening                                        1000
  printed      bead         print width of every printed layer (roof and walls)        30
  layers       outer_beads  number of outer beads (roof and walls)                     1
               lattice      roof lattice + insulation zone depth                       120
               fill         solid share of the lattice zones (wavy bead), 0..1         0.25
               all_layers   False: only the skins carry load; True: every layer        False
  ribs         rib_w        rib width                                                  160
               rib_d        rib depth = depth of the rib zone in the roof              160
               n_cols       grid A: column bays along the eave (even)                  10
               min_pitch    grid A: column spacing where every other column stops      500
               n_diamonds   grid B: diamonds along the eave                            8
  crown        crown_ring   add a crown compression ring                               True
               crown_b      crown ring width                                           200
               crown_h      crown ring depth                                           200
  buttresses   but_spacing  target buttress spacing along the wall                     1500
               but_total    buttress depth from the inner wall face                    1000
               but_w        buttress width (shell thickness)                           400
  walls        walls        False: no structural walls; the ring beam sits on the      True
                            buttresses only, supports under the buttresses
               ring         False: no ring beam (no solid roof base); the roof lands   True
                            on the walls / buttresses directly
               roof_only    True: only the roof, ribs and crown ring, supported on     False
                            every eave node; Reaction Forces = what the roof puts on
                            the ring (vertical + outward push)
               but_on_ribs  one buttress under every rib foot (grid A: n_cols bays,     False
                            grid B: n_diamonds bays) instead of but_spacing
               but_cap      cast cap along each buttress top, tying it to the ring     True
                            beam over its full depth (detail D1: the solid roof base
                            cast over the buttress, hooked bars into it)
  loads        wind_dir     direction the wind blows TOWARD, degrees from +X, ccw      0
               qp           peak wind pressure, kN/m2                                  0.9
               clad         anything on the roof besides the structure, kN/m2          0
                            (insulation, coating; 0 = bare structure)
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
    cap_lines      list Line    buttress caps     -> Line to Beam, Id "cap", same section as the ring beam
    foot_lines     list Line    footing (footing = True) -> Line to Beam, Id "footing", foot_b x foot_h, cast
    foot_b, foot_h item float   footing section, mm
    rib_lines      list Line    rib grid (empty for "none") -> Line to Beam, Id = rib_ids
    rib_ids        list str     "col" / "hring" / "hip" (A) or "diag" / "hip" (B), one per rib_lines item
    supports       list Point   base nodes        -> Support
    cladding       item Vector  kN/m2 on roof_meshes (Mesh Load, Z down)
    wind_vecs      list Vector  kN/m2 per roof face   (Mesh Load, one per roof_meshes item, same order)
    wind_walls     list Vector  kN/m2 per wall face   (Mesh Load, one per wall_meshes item, same order)
    t_roof         item float   EQUIVALENT roof shell thickness, mm (Shell Const height; not the 400 build-up)
    t_roof_elems   tree float   the same per element, one branch per roof mesh (for Shell Var)
    t_wall, t_but  item float   EQUIVALENT wall thickness / buttress thickness, mm
    ring_b, ring_h, crown_b, crown_h, rib_w, rib_d   beam sections, mm
    E_roof, G_roof, E_wall, G_wall  kN/cm2  equivalent moduli -> Material Properties E, G12, G13 (printed parts)
    fc_roof, ft_roof, fc_wall, ft_wall  kN/cm2  equivalent strengths -> Material Properties fc (negative), ft
    gamma_roof, gamma_wall  kN/m3 equivalent density for the printed hollow sections
    t_build        item float   real roof build-up thickness, mm
    rise, slope    item float   the roof height (mm) and angle (deg) actually built
    concrete       item float   total concrete volume, m3 (an objective for optimising)
    weight         item float   total self weight, kN, without cladding (cross-check Karamba's reactions)
    material       str          values for a custom Karamba Material
    info           str          counts, areas, rib lengths, weights and warnings
"""
import math

DEFAULTS = dict(
    grid="A", mesh_size=500.0, clear=10000.0, wall=400.0, wall_h=2500.0, base_h=300.0, rise=6000.0, slope=None,
    opening=1000.0, bead=30.0, outer_beads=1, lattice=120.0, fill=0.25, all_layers=False,
    rib_w=160.0, rib_d=160.0, n_cols=10, min_pitch=500.0, n_diamonds=8,
    crown_ring=True, crown_b=200.0, crown_h=200.0, but_spacing=1500.0, but_total=1000.0, but_w=400.0, walls=True,
    but_cap=True, ring=True, but_on_ribs=False, roof_only=False, ring_w=None, skin_check=False,
    footing=False, foot_w=800.0, foot_h=500.0, foot_ext=300.0, foot_in=0.0, foot_strip=True,
)


def _equiv(layers):
    """layers: (thickness, solid share, structural?) from the room side out. Returns the equivalent single-layer shell
    of the structural layers (same A and I per unit width): thickness, A / thickness (factor on E and the strengths),
    the centroid from the room-side face, and the solid thickness of ALL layers (for the weight)."""
    parts, z = [], 0.0
    for t, share, struct in layers:
        if struct and t > 0 and share > 0:
            parts.append((t * share, t, z + t / 2))
        z += t
    a = sum(pa for pa, _, _ in parts)
    zc = sum(pa * zm for pa, _, zm in parts) / a
    i = sum(pa * t * t / 12 + pa * (zm - zc) ** 2 for pa, t, zm in parts)
    t_eq = math.sqrt(12 * i / a)
    return dict(t=t_eq, ratio=a / t_eq, zc=zc, solid=sum(t * share for t, share, _ in layers), total=z)


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
    bead, n_out, fill, every = p["bead"], int(p["outer_beads"]), p["fill"], bool(p["all_layers"])
    if not p["ring_w"]:
        p["ring_w"] = p["wall"]                         # ring beam as wide as the wall unless set
    if p["ring_w"] <= 0 or p["base_h"] <= 0:
        raise ValueError("ring_w and base_h must be positive")
    roof_only = bool(p["roof_only"])                    # the roof alone, pinned along the eave: its reactions are
    walls, ring = bool(p["walls"]) and not roof_only, bool(p["ring"]) and not roof_only   # what it puts on the ring
    if bead <= 0 or n_out < 1 or min(p["lattice"], p["rib_d"]) < 0 or not 0 <= fill <= 1:
        raise ValueError("bead and outer_beads must be positive, lattice and rib_d not negative, fill between 0 and 1")
    wall_lat = p["wall"] - (1 + n_out) * bead
    if wall_lat < 0:
        raise ValueError("wall ({:.0f}) is thinner than its {} beads of {:.0f}".format(p["wall"], 1 + n_out, bead))
    roof_sec = _equiv([(bead, 1.0, True), (p["rib_d"], 0.0, False), (bead, 1.0, True),
                       (p["lattice"], fill, every), (n_out * bead, 1.0, every)])
    wall_sec = _equiv([(bead, 1.0, True), (wall_lat, fill, every), (n_out * bead, 1.0, True)])
    # shell surface = centroid of the structural layers; half width at the eave and at the crown (the room-side face
    # meets the inner wall face at the eave, as on the drawings)
    sh = 1.0 / math.sin(math.radians(slope))           # horizontal width per unit thickness square to the slope
    halfb = half + roof_sec["zc"] * sh
    d_c = p["opening"] / 2 + roof_sec["zc"] * sh
    if d_c >= d_b - ms / 2:
        raise ValueError("crown too wide for the plan - reduce opening or the roof thickness")
    kx = (halfb - d_c) / rise
    slant = math.hypot(d_b - d_c, z_c - z_b)

    def W(z):                                           # half width of the model roof face at height z
        return d_b + (d_c - d_b) * (z - z_b) / (z_c - z_b)

    def z_of(w):
        return z_b + (d_b - w) / (d_b - d_c) * (z_c - z_b)

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

    # buttress axes along each side (as pyramid_drawings.but_pos): equal bays on the wall centreline, corners included.
    # but_on_ribs: one buttress under every rib foot instead (grid A: every column, grid B: every diagonal pair)
    nb = max(1, int(round(2 * d_b / p["but_spacing"])))
    if p["but_on_ribs"]:
        if grid == "A":
            nb = n_cols
        elif grid == "B":
            nb = n_d
        else:
            warn.append("but_on_ribs: the plain shell has no ribs, buttresses keep but_spacing")
    but_x = [-d_b + 2 * d_b * k / nb for k in range(nb + 1)]
    q = max(1, int(round(2 * d_b / nb / ms)))
    wall_x = [-d_b + 2 * d_b * k / (nb * q) for k in range(nb * q + 1)]
    n_w = max(1, int(math.ceil(z_b / ms)))
    wall_z = [z_b * j / n_w for j in range(n_w + 1)]
    fin_len = half + p["but_total"] - d_b
    if fin_len <= 0:
        raise ValueError("but_total must be larger than half the wall thickness")
    n_f = max(1, int(math.ceil(fin_len / ms)))

    out = {"grid": grid, "roof": [], "t_elems": [], "wall": [], "but": [], "ring": [], "crown": [], "ribs": [], "cap": [], "foot": [],
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
        out["t_elems"].append([roof_sec["t"]] * len(F))
        out["ribs"] += ribs

        # every wall-top node and every roof-eave node along this side
        eave_x = [round(pt[0] * t[0] + pt[1] * t[1], 3) for pt in base]
        xs = sorted(set([round(x, 3) for x in wall_x] + eave_x))
        xs = [x for i, x in enumerate(xs) if i == 0 or x - xs[i - 1] > 1.0]
        if not roof_only and not ring and not walls and any(min(abs(x - xb) for x in eave_x) > 1.0 for xb in but_x):
            raise ValueError("without ring and walls each buttress must sit under a rib foot: set but_on_ribs = True "
                             "(grid A or B)")
        # wall: columns on the buttress bays; without a ring beam also on every roof-eave node, so the roof sits on it
        wxs = wall_x if ring else xs
        wv = [P(d_b, x, z) for z in wall_z for x in wxs]
        nx = len(wxs)
        wf = [(j * nx + i, j * nx + i + 1, (j + 1) * nx + i + 1, (j + 1) * nx + i) for j in range(n_w) for i in range(nx - 1)]
        if walls:
            out["wall"].append((wv, _orient(wv, wf, (n[0], n[1], 0.0))))
            out["supports"] += wv[:nx]
        # ring beam: split at every wall-top node and every roof-eave node
        if ring:
            out["ring"] += [(P(d_b, a, z_b), P(d_b, b, z_b)) for a, b in zip(xs, xs[1:])]
        if p["crown_ring"]:
            out["crown"] += list(zip(top, top[1:]))
        if roof_only:                                   # supports on every eave node instead of walls / buttresses
            out["supports"] += base
            continue
        # buttresses
        for xb in but_x:
            bv = [P(d_b + fin_len * i / n_f, xb, z) for z in wall_z for i in range(n_f + 1)]
            bf = [(j * (n_f + 1) + i, j * (n_f + 1) + i + 1, (j + 1) * (n_f + 1) + i + 1, (j + 1) * (n_f + 1) + i)
                  for j in range(n_w) for i in range(n_f)]
            out["but"].append((bv, bf))
            out["supports"] += bv[0 if not walls else 1:n_f + 1]
            if p["but_cap"]:                            # the solid roof base cast over the buttress top (detail D1)
                top_row = bv[n_w * (n_f + 1):]
                out["cap"] += list(zip(top_row, top_row[1:]))
        if p["footing"]:                                # strip footing on the wall line + a footing beam under every
            if p["foot_strip"]:                         # buttress, reaching foot_in inward from the wall line and
                fx = [P(d_b, x, 0.0) for x in wxs]      # foot_ext beyond the buttress; supported at every node.
                out["foot"] += list(zip(fx, fx[1:]))    # foot_strip = False: pads under the buttresses only
                out["supports"] += fx
            ext, fin_in = max(0.0, float(p["foot_ext"])), max(0.0, float(p["foot_in"]))
            n_ext, n_in = int(math.ceil(ext / ms)), int(math.ceil(fin_in / ms))
            for xb in but_x:
                fp = [P(d_b - fin_in * (1 - i / n_in), xb, 0.0) for i in range(n_in)] if fin_in > 1.0 else []
                fp += [P(d_b + fin_len * i / n_f, xb, 0.0) for i in range(n_f + 1)]
                if ext > 1.0:
                    fp += [P(d_b + fin_len + ext * i / n_ext, xb, 0.0) for i in range(1, n_ext + 1)]
                out["foot"] += list(zip(fp, fp[1:]))
                out["supports"] += fp
    out["supports"] = sorted(set(out["supports"]))

    # ---- quantities (m3): printed parts at their solid share, cast parts full
    areas = [[_area(V, [f]) for f in F] for V, F in out["roof"]]
    roof_area = sum(sum(a) for a in areas)
    rib_len = sum(_dist(a, b) for a, b, _ in out["ribs"])
    wall_area = 4 * 2 * d_b * z_b if walls else 0.0
    vol = dict(shell=roof_area * roof_sec["solid"] / 1e9, ribs=rib_len * p["rib_w"] * p["rib_d"] / 1e9,
               ring=8 * d_b * p["ring_w"] * p["base_h"] / 1e9 if ring else 0.0,
               crown=sum(_dist(a, b) for a, b in out["crown"]) * p["crown_b"] * p["crown_h"] / 1e9,
               walls=wall_area * wall_sec["solid"] / 1e9,
               buttresses=0.0 if roof_only else 4 * len(but_x) * fin_len * z_b * p["but_w"] / 1e9,
               caps=sum(_dist(a, b) for a, b in out["cap"]) * p["ring_w"] * p["base_h"] / 1e9,
               footing=sum(_dist(a, b) for a, b in out["foot"]) * p["foot_w"] * p["foot_h"] / 1e9)
    out["p"] = p
    out["geom"] = dict(d_b=d_b, d_c=d_c, z_b=z_b, z_c=z_c, rise=rise, slope=slope, slant=slant, fin_len=fin_len,
                       n_but=4 * len(but_x), but_bay=2 * d_b / nb, roof_area=roof_area,
                       wall_area=wall_area, rib_len=rib_len, levels_a=levels_a, roof_sec=roof_sec, wall_sec=wall_sec,
                       vol=vol, gamma_ratio_roof=roof_sec["solid"] / roof_sec["t"],
                       gamma_ratio_wall=wall_sec["solid"] / wall_sec["t"])
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


def summary(m, gamma=24.0, clad=0.0):
    g, p = m["geom"], m["p"]
    vol, rs, ws = g["vol"], g["roof_sec"], g["wall_sec"]
    n_roof = sum(len(F) for _, F in m["roof"])
    lines = ["grid {}: plan {:.0f} clear, eave +{:.2f}, rise {:.0f}, slope {:.1f} deg, crown opening {:.0f}".format(
                 m["grid"], p["clear"], p["wall_h"] / 1000, g["rise"], g["slope"], p["opening"]),
             "roof {:.0f} thick ({:.0f} bead, rib zone {:.0f}, lattice {:.0f}, {} outer beads), {} elements, {:.0f} m2; "
             "{} buttresses ({} per side, bays {:.0f})".format(
                 rs["total"], p["bead"], p["rib_d"], p["lattice"], int(p["outer_beads"]), n_roof, g["roof_area"] / 1e6,
                 g["n_but"], g["n_but"] // 4, g["but_bay"]),
             "Karamba equivalent shells ({}): roof t {:.0f}, E x {:.3f}; wall t {:.0f}, E x {:.3f}".format(
                 "all printed layers" if p["all_layers"] else "skins only", rs["t"], rs["ratio"], ws["t"], ws["ratio"])]
    if p["skin_check"]:
        lines.append("SKIN CHECK: roof shell = one {:.0f} mm skin, real printed E, full roof weight. Use only with "
                     "Buckling Modes (BLFacs = local skin buckling between ribs, on the safe side)".format(p["bead"]))
    if p["roof_only"]:
        lines.append("ROOF ONLY: supported on every eave node (set Support to pinned: Tx Ty Tz only). The reactions are "
                     "what the roof puts on the ring: Z = down, horizontal = outward push")
    elif not m["ring"]:
        lines.append("NO ring beam: the roof lands on the {} directly".format("wall top" if m["wall"] else "buttresses at the rib feet"))
    if p["but_on_ribs"] and m["grid"] != "none":
        lines.append("buttresses under the rib feet: {} bays per side ({} buttresses with both corners), {:.0f} apart".format(
            g["n_but"] // 4 - 1, g["n_but"] // 4, g["but_bay"]))
    if not m["wall"] and not p["roof_only"]:
        lines.append("NO structural walls: the ring beam sits on the {} buttresses only (wall_meshes and wind_walls are "
                     "empty, supports under the buttresses)".format(g["n_but"]))
    if m["foot"]:
        lines.append("footing {:.0f} x {:.0f}: {}under each buttress from {:.0f} inside the wall "
                     "line to {:.0f} beyond the buttress (footing length {:.0f}), {} beams, supports under the footing "
                     "(foot_lines)".format(p["foot_w"], p["foot_h"],
                                           "strip on the wall line + " if p["foot_strip"] else "PADS ONLY, ",
                                           p["foot_in"], p["foot_ext"],
                                           p["foot_in"] + g["fin_len"] + p["foot_ext"], len(m["foot"])))
    if m["cap"]:
        lines.append("buttress caps: {} beams, ring section {:.0f} x {:.0f} (cap_lines)".format(
            len(m["cap"]), p["ring_w"], p["base_h"]))
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
    but_nodes = set(key(p) for V, _ in m["but"] for p in V)
    errs += ["buttress cap end off the buttress {}".format(p) for a, b in m["cap"] for p in (a, b) if key(p) not in but_nodes]
    z_b = m["geom"]["z_b"]
    # what the roof eave and the buttress tops land on: the ring beam, else the wall top, else (no ring, no walls) the
    # roof itself at the rib feet
    land = ring if m["ring"] else wall if m["wall"] else roof
    what = "ring beam" if m["ring"] else "wall top" if m["wall"] else "roof (rib foot)"
    if m["ring"] or m["wall"]:
        errs += ["roof eave node not on the {} {}".format(what, p) for V, _ in m["roof"] for p in V
                 if abs(p[2] - z_b) < tol and key(p) not in land]
    if m["ring"]:
        errs += ["wall top node not on the ring beam {}".format(p) for V, _ in m["wall"] for p in V
                 if abs(p[2] - z_b) < tol and key(p) not in ring]
    if m["foot"]:
        foot = set(key(p) for a, b in m["foot"] for p in (a, b))
        errs += ["buttress foot not on the footing {}".format(V[0]) for V, _ in m["but"] if key(V[0]) not in foot]
    if m["wall"]:
        errs += ["buttress not attached to the wall {}".format(V[0]) for V, _ in m["but"] if key(V[0]) not in wall]
    else:                                               # no walls: each buttress top must reach the ring / the roof
        errs += ["buttress not attached to the {} {}".format(what, V[0]) for V, _ in m["but"]
                 if not any(abs(pt[2] - z_b) < tol and key(pt) in land for pt in V)]
    caps_on = sum(1 for a, b in m["cap"] if key(a) in land)
    if m["cap"] and caps_on < len(m["but"]):
        errs.append("only {} of {} buttress caps start on the {}".format(caps_on, len(m["but"]), what))
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
    wd, qp, clad = get("wind_dir", 0.0), get("qp", 0.9), get("clad", 0.0)
    gam, fck, kf, fixed = get("gamma", 24.0), get("fck", 30.0), get("kf", 0.7), get("fixed", True)
    out = dict(roof_meshes=[], wall_meshes=[], but_meshes=[], ring_lines=[], crown_lines=[], cap_lines=[], foot_lines=[], rib_lines=[], rib_ids=[],
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
    out["cap_lines"] = [line(a, b) for a, b in m["cap"]]
    out["foot_lines"] = [line(a, b) for a, b in m["foot"]]
    out["foot_b"], out["foot_h"] = p["foot_w"], p["foot_h"]
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
    rs, ws = g["roof_sec"], g["wall_sec"]
    out["t_roof"], out["t_wall"], out["t_but"], out["t_build"] = rs["t"], ws["t"], p["but_w"], rs["total"]
    out["ring_b"], out["ring_h"] = p["ring_w"], p["base_h"]
    out["crown_b"], out["crown_h"] = p["crown_b"], p["crown_h"]
    out["rib_w"], out["rib_d"] = p["rib_w"], p["rib_d"]
    out["gamma_roof"] = gam * g["gamma_ratio_roof"]
    out["gamma_wall"] = gam * g["gamma_ratio_wall"]
    out["rise"], out["slope"] = g["rise"], g["slope"]
    out["concrete"] = sum(g["vol"].values())
    out["weight"] = out["concrete"] * gam
    E = 22 * ((fck + 8) / 10) ** 0.3 * kf * 100                   # kN/cm2, EC2 Ecm, knocked down
    fc = fck / 1.5 * kf / 10                                      # kN/cm2, printed
    for key, sec in (("roof", rs), ("wall", ws)):                 # equivalent shells: E and strengths x A / t
        out["E_" + key] = E * sec["ratio"]
        out["G_" + key] = E * sec["ratio"] / 2.4
        out["fc_" + key] = -fc * sec["ratio"]                     # Karamba wants fc negative
        out["ft_" + key] = 0.0                                    # printed layers: take no tension
    if p["skin_check"]:                                           # buckling check: the roof shell = ONE real skin
        out["t_roof"] = p["bead"]                                 # (full printed E), carrying the whole roof weight
        out["E_roof"], out["G_roof"], out["fc_roof"] = E, E / 2.4, -fc
        out["gamma_roof"] = gam * rs["solid"] / p["bead"]
        out["t_roof_elems"] = DataTree[object]()
        for i, ts in enumerate(m["t_elems"]):
            out["t_roof_elems"].AddRange([p["bead"]] * len(ts), GH_Path(i))
    out["material"] = ("printed (Ecm x kf = {:.0f} kN/cm2, fc {:.2f} kN/cm2) as equivalent shells: roof E {:.0f}, G {:.0f}, "
                       "fc {:.3f}, gamma {:.2f}; wall E {:.0f}, G {:.0f}, fc {:.3f}, gamma {:.2f} (kN/cm2, kN/m3), ft 0. "
                       "Ribs, ring beam, crown ring and buttresses are cast: full gamma {:g} kN/m3".format(
                           E, fc, out["E_roof"], out["G_roof"], out["fc_roof"], out["gamma_roof"],
                           out["E_wall"], out["G_wall"], out["fc_wall"], out["gamma_wall"], gam))
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
