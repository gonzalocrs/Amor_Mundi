"""Revit solids of the analysed pyramid-roof structure (Rhino.Inside.Revit), from the same geometry as the Karamba
model. Every element comes from `build_model` in scripts/karamba_model.py, so Revit can't drift from the analysis.

Paste into a Python 3 Script component (Rhino 8) in the Revit .gh (grasshopper/Pyramide Revit.gh). The script reads
the slider values straight from the Karamba .gh (input `karamba_gh`), so there are no sliders to copy: move a slider
in the Karamba file, save it, then re-run this component (right-click > Recompute). Any input below that you wire
overrides the value read from the Karamba file. Units: millimetres.
The component sets up its own inputs and outputs (the names below) the first time it runs: no need to add them by
hand. Inputs or outputs it doesn't know are removed; wires to the ones it keeps stay.

What is real here and what is idealised in Karamba:
  - Karamba works on centrelines and mid-surfaces. Here every part gets its real section around those same lines:
    the ring beam and crown ring keep their Karamba centroid; their lines sit on the TOP of the beam, because Revit
    hangs a beam below its line (z justification Top, the default).
  - Roof shell (printed casing): the full build-up square to the slope (inner bead | rib zone | middle bead | lattice |
    outer beads = `t_build`), placed so the Karamba shell surface is the centroid of the two skins, as in the script.
    It runs from the top of the ring beam to the underside of the crown ring, mitred on the hips. Solid volume =
    gross; the concrete actually printed is less (lattice at its `fill` share, rib zone open): read Karamba's
    `concrete` for quantities.
  - Ribs: one solid per rib (columns, hips, middle rings), b x h square to the slope. The outer face of every rib
    sits at `rib_top` from the Karamba surface (default: the underside of the middle bead, the top of the rib zone),
    and the depth grows into the room. Columns and hips taper continuously from `rib_d_eave` to `rib_d_top`.
    Ribs run from the top of the ring beam to the underside of the crown ring.
  - Buttresses: `but_w` thick, from the inner wall face to `but_total`, from the top of the footing (z = 0) to the
    underside of the ring beam (wall_h), or with `but_cap` (ring cast solid onto the buttresses) up to the top of
    the ring: the Karamba cap beam is then part of the buttress solid, not a separate beam.
  - Footing: Karamba puts the footing beams on z = 0; here the footing hangs BELOW z = 0 (top at 0, foot_h deep),
    so the buttresses stand on it. Strip on the wall line + one pad under each buttress, joined into one solid.

INPUTS (all optional)
    karamba_gh   str     path of the Karamba .gh; default: grasshopper/Pyramide Karamba 10_14_2026.gh next to
                         this .gh's folder
    origin       Plane   where the module sits in Revit: the Module Origin marker's plane (default World XY)
    piece_max    float   TEMPORARY piece cut of the shell: largest piece width / length along the slope, mm (2000)
    rib_top      float   outer face of the ribs from the Karamba shell surface, mm, + = outwards (default: top of
                         the rib zone = bead + rib_d - centroid of the skins)
    wire_up      bool    Button: places the Rhino.Inside components to the right of this one, wired to the outputs
                         (Add DirectShape for shell / ribs / buttresses / footing, Add Structural Beam + its type chain
                         for ring + caps and for the crown), in a group "revit_structure wire_up". Only the canvas
                         changes; Revit changes when those components run. Pressing again does nothing while the
                         group exists (delete the group and its components to redo it)
    any input of karamba_model.py (foot_w, n_cols, ...)  overrides the Karamba .gh value

OUTPUTS
    shell        list Brep   printed beads: inner, middle, outer x 4 faces (the casing; the inner bead is cut where
                             the ribs pass, the rib zone between inner and middle bead is left open for the ribs and
                             rings)                                  -> Add DirectShape, category Roofs
    insulation   list Brep   lattice zone (wavy bead + insulation)   -> Add DirectShape, category Roofs
                 shell and insulation come cut into the TEMPORARY printed pieces: joints on the rib centrelines,
                 each rib bay split into equal pieces at most piece_max wide and long (3 beads per piece in shell)
    piece_names  list str    "E-C01-P01" (face, course from the eave, piece along the face), one per piece
    ribs         list Brep   one per rib                             -> Add DirectShape, category Structural Framing
    rib_names    list str    "M-col-E-03" style name per rib (same order)
    buttresses   list Brep   one per buttress                        -> Add DirectShape, category Walls
    footing      list Brep   the whole footing, one solid            -> Add DirectShape, category Structural Foundations
    ring_lines   list Line   ring beam, 4 sides corner to corner     -> Add Structural Beam, type ring_b x ring_h
    cap_lines    list Line   buttress caps (ring section)            -> Add Structural Beam, same type as the ring
    crown_lines  list Line   crown ring, 4 sides                     -> Add Structural Beam, type crown_b x crown_h
    but_lines    list Line   buttress base lines (for native structural walls later)
    ring_b, ring_h, crown_b, crown_h, but_w, foot_h, wall_h   float  mm
    params       str     the parameter values used, and where each came from
    info         str     counts and volumes, to check against Karamba's info
"""
import math
import os
import sys

# the analysed model of 18-19 Oct 2026 (values read from the Karamba .gh at commit 0fad7fa); used only when the
# Karamba .gh can't be read
FINAL = dict(
    rib_d_eave=350.0, rib_d_top=150.0, rib_w=150.0, rib_d=250.0, n_cols=6, min_pitch=500.0, walls=False, ring=True,
    ring_w=300.0, base_h=300.0, hring_z=[4800.0, 6578.0], hring_w=250.0, skin_check=False, ring_test=False,
    but_on_ribs=True, but_total=1000.0, but_w=400.0, wall_h=2500.0, no_corner="1,2,3,4", but_cap=True,
    footing=True, foot_w=600.0, foot_ext=1000.0, foot_h=300.0, foot_in=400.0, foot_strip=True,
)
FACE = "ENWS"                                           # face k: E +x, N +y, W -x, S -y (as rib_pieces.py)


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _add(a, b, s=1.0):
    return (a[0] + s * b[0], a[1] + s * b[1], a[2] + s * b[2])


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _unit(a):
    n = math.sqrt(_dot(a, a))
    return (a[0] / n, a[1] / n, a[2] / n)


HEX = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]


def _volume(V, F=HEX):
    vol = 0.0
    for f in F:
        for k in range(1, len(f) - 1):
            vol += _dot(V[f[0]], _cross(V[f[k]], V[f[k + 1]])) / 6.0
    return vol


def _hexa(V):
    """8 corners (bottom quad 0-3, top quad 4-7, same order) -> closed hexahedron faced outwards"""
    F = HEX if _volume(V) > 0 else [tuple(reversed(f)) for f in HEX]
    return (list(V), F)


def _box(a, b, w, d_up, d_down, side):
    """prism along a -> b: `w` wide (across, unit vector `side`), from d_up above to d_down below the line (z)"""
    up = (0.0, 0.0, 1.0)
    pts = []
    for z in (d_down, d_up):
        for p, s in ((a, -1), (b, -1), (b, 1), (a, 1)):
            pts.append(_add(_add(p, side, s * w / 2), up, z))
    return _hexa(pts)


def build_revit(m, rib_top=None, piece_max=2000.0):
    """solids and beam lines from a build_model result `m`"""
    p, g = m["p"], m["geom"]
    rs = g["roof_sec"]
    d_b, d_c, z_b, z_c = g["d_b"], g["d_c"], g["z_b"], g["z_c"]
    half = p["clear"] / 2
    z_ring_top = p["wall_h"] + p["base_h"]              # top of the ring beam (the solid roof base)
    z_crown_bot = z_c - (p["crown_h"] / 2 if p["crown_ring"] else 0.0)
    ks = (d_b - d_c) / (z_c - z_b)                     # Karamba roof surface: half width W(z) = d_b - ks (z - z_b)
    q = math.sqrt(1 + ks * ks)                          # half-width change per mm of offset square to the slope
    W = lambda z, s=0.0: d_b - ks * (z - z_b) + s * q   # half width of the surface offset s (+ out) at height z
    s_in, s_out = -rs["zc"], rs["total"] - rs["zc"]      # room face and outer face of the build-up
    if rib_top is None:
        rib_top = p["bead"] + p["rib_d"] - rs["zc"]     # top of the rib zone = underside of the middle bead
    out = dict(shell=[], ribs=[], rib_names=[], rib_ids=[], buttresses=[], footing=[], ring=[], cap=[], crown=[],
               but_lines=[], warn=[])

    def frame(k):
        th = math.radians(90 * k)
        return (math.cos(th), math.sin(th), 0.0), (-math.sin(th), math.cos(th), 0.0)

    def P(k, dist, x, z):
        n, t = frame(k)
        return (dist * n[0] + x * t[0], dist * n[1] + x * t[1], z)

    # ---- ribs: merge Karamba's split segments back into one straight rib each
    chains = []
    for a, b, rid in m["ribs"]:
        if chains:
            c = chains[-1]
            if c[2] == rid and max(abs(u - v) for u, v in zip(c[1], a)) < 1.0 and \
                    abs(_dot(_unit(_sub(c[1], c[0])), _unit(_sub(b, a))) - 1) < 1e-6:
                c[1] = b
                continue
        chains.append([a, b, rid])

    # ---- roof shell as its layers, room side out: inner bead | rib zone (open: the cast ribs and rings sit here) |
    # middle bead | lattice zone (insulation) | outer beads. The printed beads go to `shell`, the lattice zone to
    # `insulation`. TEMPORARY piece cut (until the construction study): joints on the rib centrelines (columns and
    # middle rings, so each cast rib covers a joint and the piece edges form its channel), mitred on the hips; every
    # rib bay split into equal pieces at most `piece_max` wide and long along the slope
    bead, n_out = p["bead"], int(p["outer_beads"])
    cuts = [s_in]
    for t in (bead, p["rib_d"], bead, p["lattice"], n_out * bead):
        cuts.append(cuts[-1] + t)
    layers = [("inner", 0), ("middle", 2), ("outer", 4), ("insulation", 3)]
    out.update(shell_names=[], inner_idx=[], insulation=[], piece_names=[], piece_sizes=[])
    pmax = float(piece_max)

    def corner(k, u, z, s):                             # face k, u = -1..1 across the face, height z, offset s
        x = u * W(z, s) if abs(abs(u) - 1) < 1e-9 else u * W(z)   # hips mitred, other joints square to the face
        return P(k, W(z, s), x, z)

    def block(k, u0, u1, z0, z1, s0, s1):
        return _hexa([corner(k, u, z, sv) for z in (z0, z1) for u, sv in ((u0, s0), (u1, s0), (u1, s1), (u0, s1))])

    zs = [z_ring_top] + [z for z in m["geom"]["levels_a"] if z_ring_top < z < z_crown_bot] + [z_crown_bot]
    courses = []                                        # (z0, z1, z of the band top: which columns reach it)
    for za, zb in zip(zs, zs[1:]):
        n = max(1, int(math.ceil((zb - za) * q / pmax - 1e-9)))
        courses += [(za + (zb - za) * i / n, za + (zb - za) * (i + 1) / n, zb) for i in range(n)]
    for k in range(4):
        n, t = frame(k)
        cols = []                                       # (u, top z) of the columns on face k
        for a, b, rid in chains:
            if rid != "col":
                continue
            mid = _add(a, _sub(b, a), 0.5)
            if max(range(4), key=lambda kk: _dot(frame(kk)[0], mid)) != k:
                continue
            cols.append((_dot(mid, t) / W(mid[2]), max(a[2], b[2])))
        for ci, (z0, z1, zband) in enumerate(courses):
            us = sorted(set([-1.0, 1.0] + [round(u, 6) for u, top in cols if top >= zband - 1.0]))
            pi = 0
            for ua, ub in zip(us, us[1:]):
                bay = max(abs(_dot(_sub(corner(k, ub, z0, sv), corner(k, ua, z0, sv)), t)) for sv in (cuts[0], cuts[-1]))
                m_ = max(1, int(math.ceil(bay / pmax - 1e-9)))
                for j in range(m_):
                    u0, u1 = ua + (ub - ua) * j / m_, ua + (ub - ua) * (j + 1) / m_
                    pi += 1
                    name = "{}-C{:02d}-P{:02d}".format(FACE[k], ci + 1, pi)
                    out["piece_names"].append(name)
                    wid = max(abs(_dot(_sub(corner(k, u1, z0, sv), corner(k, u0, z0, sv)), t))
                              for sv in (cuts[0], cuts[-1]))     # widest face of the piece (outer, at a hip)
                    out["piece_sizes"].append((wid, (z1 - z0) * q))
                    for lname, i in layers:
                        piece = block(k, u0, u1, z0, z1, cuts[i], cuts[i + 1])
                        if lname == "insulation":
                            out["insulation"].append(piece)
                            continue
                        if lname == "inner":
                            out["inner_idx"].append(len(out["shell"]))
                        out["shell"].append(piece)
                        out["shell_names"].append("{} {}".format(name, lname))
    d_eave = float(p["rib_d_eave"] or p["rib_d"])
    d_top = float(p["rib_d_top"] or p["rib_d"])

    def depth(z, rid):
        if rid == "hring":
            return float(p["rib_d"])
        t = min(1.0, max(0.0, (z - z_b) / (z_c - z_b)))
        return d_eave + (d_top - d_eave) * t

    def clip(a, b, z0, z1):                             # the part of a -> b between heights z0 and z1
        def at(z):
            t = (z - a[2]) / (b[2] - a[2])
            return _add(a, _sub(b, a), t)
        if abs(b[2] - a[2]) < 1e-6:
            return a, b
        lo, hi = (a, b) if a[2] < b[2] else (b, a)
        if lo[2] < z0:
            lo = at(z0)
        if hi[2] > z1:
            hi = at(z1)
        return lo, hi

    count = {}
    for a, b, rid in chains:
        a, b = clip(a, b, z_ring_top, z_crown_bot)
        if _dot(_sub(b, a), _sub(b, a)) < 1.0:
            continue
        mid = _add(a, _sub(b, a), 0.5)
        k = max(range(4), key=lambda kk: _dot(frame(kk)[0], mid))   # the face the rib is on
        n, t = frame(k)
        nf = _unit((n[0], n[1], ks))                     # outward normal of face k
        if rid == "hip":                                 # bisector of the two faces meeting on the hip
            n2 = frame((k + 1) % 4)[0] if _dot(frame((k + 1) % 4)[0], mid) > _dot(frame((k - 1) % 4)[0], mid) \
                else frame((k - 1) % 4)[0]
            nf2 = _unit((n2[0], n2[1], ks))
            no = _unit(_add(nf, nf2))
            top = rib_top / _dot(no, nf)                 # the rib top on the intersection of the two offset planes
        else:
            no, top = nf, rib_top
        side = _unit(_cross(_sub(b, a), no))
        bw = float(p["hring_w"] or p["rib_w"]) if rid == "hring" else float(p["rib_w"])
        pts = []
        for lay in ("bot", "top"):
            for e, s in ((a, -1), (b, -1), (b, 1), (a, 1)):
                h = depth(e[2], rid)
                off = top - h if lay == "bot" else top
                pts.append(_add(_add(e, no, off), side, s * bw / 2))
        out["ribs"].append(_hexa(pts))
        key = (rid, FACE[k])
        count[key] = count.get(key, 0) + 1
        out["rib_names"].append("M-{}-{}-{:02d}".format(rid, FACE[k], count[key]))
        out["rib_ids"].append(rid)

    # ---- ring beam, crown ring (4 straight sides each), buttress caps (merged per buttress)
    for k in range(4):                                  # lines on the beam top (Revit hangs beams below the line)
        out["ring"].append((P(k, d_b, -d_b, z_ring_top), P(k, d_b, d_b, z_ring_top)))
        if p["crown_ring"]:
            zt = z_c + p["crown_h"] / 2
            out["crown"].append((P(k, d_c, -d_c, zt), P(k, d_c, d_c, zt)))
    caps = []
    for a, b in m["cap"]:
        if caps and max(abs(u - v) for u, v in zip(caps[-1][1], a)) < 1.0:
            caps[-1][1] = b
        else:
            caps.append([a, b])
    out["cap"] = [] if p["but_cap"] else [tuple(c) for c in caps]   # but_cap: the cap is in the buttress solid

    # ---- buttresses: one per Karamba buttress, real size
    for V, _ in m["but"]:
        foot = V[0]                                      # on the wall centreline, z = 0
        k = max(range(4), key=lambda kk: _dot(frame(kk)[0], foot))
        n, t = frame(k)
        xb = _dot(foot, t)
        a, b = P(k, half, xb, 0.0), P(k, half + p["but_total"], xb, 0.0)
        out["buttresses"].append(_box(a, b, p["but_w"], z_ring_top if p["but_cap"] else p["wall_h"], 0.0, t))
        out["but_lines"].append((a, b))

    # ---- footing below z = 0: strip on the wall line + pads (unioned in Grasshopper)
    if p["footing"]:
        fw, fh = float(p["foot_w"]), float(p["foot_h"])
        if p["foot_strip"]:
            for k in range(4):                           # full length each side; the corners overlap (union)
                out["footing"].append(_box(P(k, d_b, -d_b - fw / 2, 0.0), P(k, d_b, d_b + fw / 2, 0.0), fw, 0.0, -fh,
                                           frame(k)[0]))
        for a, b in out["but_lines"]:
            k = max(range(4), key=lambda kk: _dot(frame(kk)[0], a))
            n, t = frame(k)
            xb = _dot(a, t)
            out["footing"].append(_box(P(k, d_b - p["foot_in"], xb, 0.0),
                                       P(k, d_b + g["fin_len"] + p["foot_ext"], xb, 0.0), fw, 0.0, -fh, t))

    # ---- volumes (m3), gross solids; footing as the union
    vol = lambda items: sum(_volume(V, F) for V, F in items) / 1e9
    fw, fh = float(p["foot_w"]), float(p["foot_h"])
    strip = ((2 * d_b + fw) ** 2 - (2 * d_b - fw) ** 2) * fh if p["footing"] and p["foot_strip"] else 0.0
    pad_len = p["foot_in"] + g["fin_len"] + p["foot_ext"]
    lap = max(0.0, min(d_b + g["fin_len"] + p["foot_ext"], d_b + fw / 2) - max(d_b - p["foot_in"], d_b - fw / 2)) \
        if p["foot_strip"] else 0.0                     # pad length inside the strip
    pads = len(out["but_lines"]) * (pad_len - lap) * fw * fh if p["footing"] else 0.0
    out["vol"] = dict(skins=vol(out["shell"]), insulation=vol(out["insulation"]), ribs=vol(out["ribs"]), buttresses=vol(out["buttresses"]),
                      footing=(strip + pads) / 1e9,
                      ring=8 * d_b * p["ring_w"] * p["base_h"] / 1e9,
                      caps=sum(math.dist(a, b) for a, b in out["cap"]) * p["ring_w"] * p["base_h"] / 1e9,
                      crown=8 * d_c * p["crown_b"] * p["crown_h"] / 1e9 if p["crown_ring"] else 0.0)
    out["levels"] = dict(ring_top=z_ring_top, crown_bot=z_crown_bot, rib_top=rib_top, t_build=rs["total"],
                         s_in=s_in, s_out=s_out)
    if any(_volume(V, F) <= 0 for V, F in out["ribs"]):
        out["warn"].append("a rib has no volume: check rib_top and the rib depths")
    return out


def summary(r, m):
    v, lv, p, kv = r["vol"], r["levels"], m["p"], m["geom"]["vol"]
    n = {}
    for rid in r["rib_ids"]:
        n[rid] = n.get(rid, 0) + 1
    lines = [
        "shell: {:.0f} build-up (room face {:.0f}, outer face +{:.0f} from the Karamba surface), +{:.2f} (ring top) to "
        "+{:.2f} (crown ring underside), as layers: inner, middle and outer beads ({:.0f}) in `shell` (inner bead cut "
        "where the ribs pass), rib zone {:.0f} left open for the ribs and rings, lattice zone {:.0f} in `insulation`".format(
            lv["t_build"], lv["s_in"], lv["s_out"], lv["ring_top"] / 1000, lv["crown_bot"] / 1000, p["bead"],
            p["rib_d"], p["lattice"]),
        "printed pieces (TEMPORARY cut, joints on the rib centrelines): {} ({} per face), largest {:.0f} wide x {:.0f} "
        "along the slope".format(len(r["piece_names"]), len(r["piece_names"]) // 4,
                                 max(w for w, _ in r["piece_sizes"]), max(h for _, h in r["piece_sizes"])),
        "ribs: {} ({}), outer face {:+.0f} from the Karamba surface; columns and hips {:.0f} -> {:.0f} deep, {:.0f} wide; "
        "middle rings {:.0f} x {:.0f}".format(len(r["ribs"]), ", ".join("{} {}".format(c, k) for k, c in sorted(n.items())),
                                              lv["rib_top"], float(p["rib_d_eave"] or p["rib_d"]),
                                              float(p["rib_d_top"] or p["rib_d"]), p["rib_w"],
                                              p["hring_w"] or p["rib_w"], p["rib_d"]),
        "buttresses: {}, {:.0f} x {:.0f} x {:.0f} tall{}; caps {} beams; ring 4 beams {:.0f} x {:.0f}; crown 4 beams "
        "{:.0f} x {:.0f}".format(len(r["buttresses"]), p["but_total"], p["but_w"], r["buttresses"][0][0][4][2] if r["buttresses"] else p["wall_h"],
                                 " (cap cast in, up to the ring top)" if p["but_cap"] else "", len(r["cap"]),
                                 p["ring_w"], p["base_h"], p["crown_b"], p["crown_h"]),
        "footing: {:.0f} wide x {:.0f} deep below z = 0, {} pieces joined into one".format(
            p["foot_w"], p["foot_h"], len(r["footing"])) if r["footing"] else "footing: none (footing = False)",
        "volumes m3 (Revit solids | Karamba): ribs {:.1f} | {:.1f}, buttresses {:.1f} | {:.1f}, ring {:.1f} | {:.1f}, "
        "caps {:.1f} | {:.1f}, crown {:.1f} | {:.1f}, footing {:.1f} | {:.1f}; printed beads {:.1f} + lattice zone {:.1f} "
        "(Karamba: printed concrete {:.1f}, the lattice bead at its fill share)".format(
            v["ribs"], kv["ribs"], v["buttresses"], kv["buttresses"], v["ring"], kv["ring"], v["caps"], kv["caps"],
            v["crown"], kv["crown"], v["footing"], kv["footing"], v["skins"], v["insulation"], kv["shell"]),
        "Revit and Karamba differ on purpose: Karamba overlaps parts at the nodes and runs the buttresses to the ring "
        "centroid; here each part stops where the next begins."]
    return "\n".join(lines + ["WARNING: " + w for w in r["warn"] + m["warn"]])


# =============== Grasshopper glue (runs only inside Rhino) ===============
def _read_karamba_gh(path, names):
    """slider / toggle / panel values wired into the Karamba script component of another .gh, without opening it"""
    import Grasshopper
    io = Grasshopper.Kernel.GH_DocumentIO()
    if not io.Open(path):
        raise IOError("can't open " + path)
    doc = io.Document
    best = None
    for obj in doc.Objects:
        params = getattr(obj, "Params", None)
        if params is None or not hasattr(params, "Input"):
            continue
        ins = set(prm.NickName for prm in params.Input)
        if {"rib_d_eave", "n_cols", "but_total"} <= ins or ({"n_cols", "rib_w"} <= ins and best is None):
            best = obj
    if best is None:
        raise ValueError("no Karamba script component in " + path)
    vals = {}
    for prm in best.Params.Input:
        if prm.NickName not in names or prm.SourceCount == 0:
            continue
        got = []
        for src in prm.Sources:
            kind = src.GetType().Name                   # the .NET class (Python sees only the IGH_Param interface)
            if kind == "GH_NumberSlider":
                got.append(float(str(src.CurrentValue)))
            elif kind == "GH_Panel":
                got.append(str(src.UserText).strip())
            elif kind == "GH_BooleanToggle":
                got.append(bool(src.Value))
        if got:
            vals[prm.NickName] = got if len(got) > 1 or prm.Access == Grasshopper.Kernel.GH_ParamAccess.list else got[0]
    doc.Dispose()
    return vals


INPUTS = ["karamba_gh", "origin", "rib_top", "piece_max", "foot_w", "wire_up"]
OUTPUTS = ["info", "params", "shell", "insulation", "piece_names", "ribs", "rib_names", "buttresses", "footing", "ring_lines", "cap_lines",
           "crown_lines", "but_lines", "ring_b", "ring_h", "crown_b", "crown_h", "but_w", "foot_h", "wall_h"]


def _setup_params(comp):
    """give the component exactly the INPUTS and OUTPUTS above. Grasshopper can't change parameters while it solves,
    so this is scheduled for right after the current solution; the component then runs again. True = done already."""
    import Grasshopper

    def var(prm):                                       # the name the script sees (a renamed output can keep its
        return getattr(prm, "VariableName", None) or prm.Name   # old variable name, e.g. "a")

    def ok(params, want):
        return [prm.NickName for prm in params] == want and all(var(prm) == prm.NickName for prm in params)
    if ok(comp.Params.Input, INPUTS) and ok(comp.Params.Output, OUTPUTS):
        return True

    def make(name):
        try:                                            # Rhino 8 script components
            from RhinoCodePluginGH.Parameters import ScriptVariableParam
            prm = ScriptVariableParam(name)
        except Exception:                               # Rhino 7 GhPython
            prm = Grasshopper.Kernel.Parameters.Param_GenericObject()
        prm.Name = prm.NickName = name
        for attr in ("VariableName", "PrettyName"):
            if hasattr(prm, attr):
                try:
                    setattr(prm, attr, name)
                except Exception:
                    pass
        prm.Access = Grasshopper.Kernel.GH_ParamAccess.item
        prm.Optional = True
        return prm

    def fix(doc):
        for params, want, side in ((comp.Params.Input, INPUTS, "Input"), (comp.Params.Output, OUTPUTS, "Output")):
            keep = {}
            for prm in list(params):
                if prm.NickName in want and var(prm) == prm.NickName and prm.NickName not in keep:
                    keep[prm.NickName] = prm
                else:
                    getattr(comp.Params, "Unregister{}Parameter".format(side))(prm)
            for prm in list(params):
                getattr(comp.Params, "Unregister{}Parameter".format(side))(prm, False)
            for i, name in enumerate(want):
                getattr(comp.Params, "Register{}Param".format(side))(keep.get(name) or make(name), i)
        comp.Params.OnParametersChanged()
        comp.ExpireSolution(False)
    comp.OnPingDocument().ScheduleSolution(1, fix)
    return False


WIRE_GROUP = "revit_structure wire_up"
BEAM_FAMILY = "Concrete-Rectangular Beam"           # as Load Autodesk Family names it (no M_)
# (output, element name, Revit category) for each Add DirectShape
DIRECT_SHAPES = [("shell", "GH - Roof shell", "Roofs"), ("insulation", "GH - Roof insulation", "Roofs"), ("ribs", "GH - Ribs", "Structural Framing"),
                 ("buttresses", "GH - Buttresses", "Walls"), ("footing", "GH - Footing", "Structural Foundations")]
# (line outputs, new type name, width output, depth output) for each Add Structural Beam
BEAMS = [(["ring_lines", "cap_lines"], "Ring beam - GH", "ring_b", "ring_h"),
         (["crown_lines"], "Crown ring - GH", "crown_b", "crown_h")]


def _wire_up(comp):
    """place and wire the Rhino.Inside components for this script's outputs (canvas only). Returns a report."""
    import System
    import Grasshopper
    from Grasshopper.Kernel.Special import GH_Panel, GH_Group
    doc = comp.OnPingDocument()
    for obj in doc.Objects:
        if isinstance(obj, GH_Group) and obj.NickName == WIRE_GROUP:
            return "wire_up: already done (group '{}' exists). Delete the group and its components to redo".format(WIRE_GROUP)
    made, miss = [], []

    def proxy(name):                                    # name, or several names separated by "|" (first found)
        for nm in name.split("|"):
            best = None
            for pr in Grasshopper.Instances.ComponentServer.ObjectProxies:
                if pr.Desc.Name == nm and not pr.Obsolete:
                    if pr.Desc.Category == "Revit":
                        return pr
                    best = best or pr
            if best:
                return best
        return None

    def place(name, x, y):
        pr = proxy(name)
        if pr is None:
            miss.append("component '{}' not found".format(name))
            return None
        obj = pr.CreateInstance()
        obj.CreateAttributes()
        obj.Attributes.Pivot = System.Drawing.PointF(x, y)
        doc.AddObject(obj, False)
        made.append(obj)
        return obj

    def panel(text, x, y):
        pn = GH_Panel()
        pn.CreateAttributes()
        pn.UserText = str(text)
        pn.NickName = str(text)
        pn.Attributes.Pivot = System.Drawing.PointF(x, y)
        pn.Attributes.Bounds = System.Drawing.RectangleF(x, y, 160, 20)
        doc.AddObject(pn, False)
        made.append(pn)
        return pn

    def prm(obj, side, *names):                         # a component's input / output by nick name or name
        if obj is None:
            return None
        if not hasattr(obj, "Params"):                  # a panel or a parameter is its own input and output
            return obj
        params = list(obj.Params.Input if side == "in" else obj.Params.Output)
        low = [n.lower() for n in names]
        for test in (lambda q, n: q.NickName.lower() == n, lambda q, n: q.Name.lower() == n,
                     lambda q, n: q.Name.lower().startswith(n)):
            for n in low:
                for q in params:
                    if test(q, n):
                        return q
        miss.append("{} '{}' has no {} named {}".format("input of" if side == "in" else "output of",
                                                         obj.Name, side, "/".join(names)))
        return None

    def wire(src, src_names, dst, dst_names):
        a, b = prm(src, "out", *src_names), prm(dst, "in", *dst_names)
        if a is not None and b is not None:
            b.AddSource(a)

    x0 = comp.Attributes.Bounds.Right + 400
    y = comp.Attributes.Bounds.Top
    skipped = []
    for key, name, cat in DIRECT_SHAPES:
        o = prm(comp, "out", key)
        if o is not None and o.Recipients.Count > 0:    # already wired by hand: don't make a second element
            skipped.append(key)
            continue
        ds = place("Add DirectShape|Add DirectShape (Geometry)", x0 + 250, y)
        wire(comp, [key], ds, ["Geometry", "G", "Brep", "B"])
        wire(panel(name, x0, y), [], ds, ["Name", "N"])
        qc = place("Query Categories", x0 - 30, y + 40)
        wire(panel(cat, x0 - 230, y + 50), [], qc, ["Name", "N"])
        wire(qc, ["Categories", "Category", "C"], ds, ["Category", "C"])
        y += 140
    for keys, tname, kb, kh in BEAMS:
        qt = place("Query Types", x0 - 30, y)
        wire(panel(BEAM_FAMILY, x0 - 230, y), [], qt, ["Family Name", "FN"])
        li = place("List Item", x0 + 120, y)
        wire(qt, ["Types", "T"], li, ["List", "L"])
        wire(panel("0", x0, y + 50), [], li, ["Index", "i"])
        dt = place("Duplicate Type", x0 + 250, y)
        wire(li, ["Item", "i"], dt, ["Type", "T"])
        wire(panel(tname, x0 + 60, y + 90), [], dt, ["Name", "N"])
        last = dt
        for k, (pname, out_key) in enumerate((("b", kb), ("h", kh))):
            ep = place("Element Parameter", x0 + 420 + 170 * k, y)
            wire(last, ["Type", "T", "Element", "E"], ep, ["Element", "E"])
            wire(panel(pname, x0 + 300 + 170 * k, y + 70), [], ep, ["Parameter", "P"])
            wire(comp, [out_key], ep, ["Value", "V"])
            last = ep
        bm = place("Add Structural Beam", x0 + 800, y)
        for key in keys:
            wire(comp, [key], bm, ["Curve", "C"])
        wire(last, ["Element", "E"], bm, ["Type", "T"])
        y += 180
    grp = GH_Group()
    grp.CreateAttributes()
    grp.NickName = WIRE_GROUP
    for obj in made:
        grp.AddObject(obj.InstanceGuid)
    doc.AddObject(grp, False)
    doc.NewSolution(False)
    return "wire_up: placed {} components and panels{}{}".format(
        len(made), "; skipped (already wired): " + ", ".join(skipped) if skipped else "", "" if not miss else "; NOT done (wire these by hand): " + "; ".join(miss))


def _gh_main():
    import importlib
    import Rhino
    import Rhino.Geometry as rg
    G = globals()
    here = None
    try:
        here = os.path.dirname(ghenv.Component.OnPingDocument().FilePath)   # noqa: F821 (Grasshopper global)
    except Exception:
        pass
    out = dict(shell=[], insulation=[], piece_names=[], ribs=[], rib_names=[], buttresses=[], footing=[], ring_lines=[],
               cap_lines=[], crown_lines=[], but_lines=[], params="", info="")
    try:
        if not _setup_params(ghenv.Component):          # noqa: F821
            out["info"] = "setting up the inputs and outputs; the component runs again by itself"
            G.update(out)
            return
    except Exception as e:
        out["setup_note"] = "WARNING: could not set up the inputs and outputs ({}); add them by hand".format(e)
    in_names = set(prm.NickName for prm in ghenv.Component.Params.Input)   # noqa: F821

    def inp(name):                                      # an input's value: the script variable, else read straight
        if name not in in_names:                        # from the input (in case its variable name didn't take).
            return None                                 # Not an input: ignore leftovers of the last run's outputs
        if G.get(name) is not None:                     # (wall_h, but_w, ... are outputs too)
            return G[name]
        for prm in ghenv.Component.Params.Input:        # noqa: F821
            if prm.NickName == name and not prm.VolatileData.IsEmpty:
                goo = list(prm.VolatileData.AllData(True))[0]
                val = goo.ScriptVariable() if hasattr(goo, "ScriptVariable") else getattr(goo, "Value", goo)
                return val
        return None
    if not here:
        out["info"] = "ERROR: save this .gh first (next to the Karamba .gh, in the repo's grasshopper folder)"
        G.update(out)
        return
    root = os.path.dirname(here)
    sp = os.path.join(root, "scripts")
    if sp not in sys.path:
        sys.path.insert(0, sp)
    import karamba_model
    importlib.reload(karamba_model)                     # pick up edits to karamba_model.py
    names = list(karamba_model.DEFAULTS)
    p, src = dict(FINAL), {k: "script FINAL" for k in FINAL}
    kgh = inp("karamba_gh") or os.path.join(here, "Pyramide Karamba 10_14_2026.gh")
    try:
        vals = _read_karamba_gh(kgh, names)
        for k, v in vals.items():
            p[k] = v
            src[k] = "Karamba .gh"
        note = "read {} values from {}".format(len(vals), os.path.basename(kgh))
    except Exception as e:
        note = "WARNING: could not read the Karamba .gh ({}); using the values analysed on 18-19 Oct".format(e)
    for k in names:                                     # wired inputs win
        if inp(k) is not None:
            p[k] = inp(k)
            src[k] = "input here"
    if isinstance(p.get("hring_z"), (list, tuple)) and len(p["hring_z"]) == 1:
        p["hring_z"] = p["hring_z"][0]
    out["params"] = note + "\n" + "\n".join("{} = {} ({})".format(k, p[k], src[k]) for k in sorted(p))
    try:
        m = karamba_model.build_model(**{k: p.get(k) for k in names})
        r = build_revit(m, inp("rib_top"), float(inp("piece_max") or 2000.0))
    except ValueError as e:
        out["info"] = "ERROR: {}".format(e)
        G.update(out)
        return

    doc = Rhino.RhinoDoc.ActiveDoc
    tol = doc.ModelAbsoluteTolerance if doc else 0.01
    pl = inp("origin")
    if isinstance(pl, (list, tuple)):
        pl = pl[0] if pl else None
    if pl is not None and not isinstance(pl, rg.Plane):
        pl = getattr(pl, "Value", pl)                   # a Grasshopper GH_Plane
    if isinstance(pl, rg.Plane):
        xf = rg.Transform.PlaneToPlane(rg.Plane.WorldXY, pl)
        placed = "placed on the origin plane at ({:.0f}, {:.0f}, {:.0f}), x axis ({:.3f}, {:.3f})".format(
            pl.OriginX, pl.OriginY, pl.OriginZ, pl.XAxis.X, pl.XAxis.Y)
    else:
        xf = rg.Transform.Identity
        placed = "NOT placed: origin is {} (wire the marker's Location plane into origin)".format(
            "empty" if pl is None else type(pl).__name__)

    def brep(vf):
        V, F = vf
        me = rg.Mesh()
        for pt in V:
            me.Vertices.Add(*pt)
        for f in F:
            me.Faces.AddFace(*f)
        me.Normals.ComputeNormals()
        b = rg.Brep.CreateFromMesh(me, True)
        b.MergeCoplanarFaces(tol)
        b.Transform(xf)
        return b

    def line(ab):
        ln = rg.Line(rg.Point3d(*ab[0]), rg.Point3d(*ab[1]))
        ln.Transform(xf)
        return ln
    out["ribs"] = [brep(x) for x in r["ribs"]]
    out["shell"] = [brep(x) for x in r["shell"]]
    cut_fail = 0
    rib_box = [rb.GetBoundingBox(True) for rb in out["ribs"]]
    for i in r["inner_idx"]:                            # the ribs pass through the inner bead: cut them out
        bb = out["shell"][i].GetBoundingBox(True)
        near = [rb for rb, rbb in zip(out["ribs"], rib_box) if rg.BoundingBox.Intersection(bb, rbb).IsValid]
        if not near:
            continue
        res = rg.Brep.CreateBooleanDifference([out["shell"][i]], near, tol)
        if res:
            out["shell"][i] = res[0] if len(res) == 1 else rg.Brep.MergeBreps(list(res), tol)
        else:
            cut_fail += 1
    out["insulation"] = [brep(x) for x in r["insulation"]]
    out["piece_names"] = r["piece_names"]
    out["rib_names"] = r["rib_names"]
    out["buttresses"] = [brep(x) for x in r["buttresses"]]
    parts = [brep(x) for x in r["footing"]]
    if parts:
        joined = rg.Brep.CreateBooleanUnion(parts, tol)
        out["footing"] = list(joined) if joined else parts
    out["ring_lines"] = [line(x) for x in r["ring"]]
    out["cap_lines"] = [line(x) for x in r["cap"]]
    out["crown_lines"] = [line(x) for x in r["crown"]]
    out["but_lines"] = [line(x) for x in r["but_lines"]]
    mp = m["p"]
    out.update(ring_b=mp["ring_w"], ring_h=mp["base_h"], crown_b=mp["crown_b"], crown_h=mp["crown_h"],
               but_w=mp["but_w"], foot_h=mp["foot_h"], wall_h=mp["wall_h"])
    info = summary(r, m)
    if cut_fail:
        info += "\nWARNING: {} inner bead faces could not be cut for the ribs (left whole)".format(cut_fail)
    if parts and len(out["footing"]) != 1:
        info += "\nWARNING: the footing pieces did not join into one solid ({} pieces)".format(len(out["footing"]))
    import scriptcontext
    sticky = scriptcontext.sticky
    if inp("wire_up"):                                  # canvas changes must wait for the end of this solution
        comp = ghenv.Component                          # noqa: F821

        def go(gh_doc):
            rep = _wire_up(comp)
            if not (rep.startswith("wire_up: already done") and sticky.get("revit_structure_wire")):
                sticky["revit_structure_wire"] = rep    # keep the report of the run that placed them
            comp.ExpireSolution(False)
        comp.OnPingDocument().ScheduleSolution(1, go)
    comp = ghenv.Component                              # noqa: F821
    filled = dict((k, out[k]) for k in OUTPUTS if k in out and out[k] not in ("", [], None))

    def refill(gh_doc):                                 # outputs the script filled but Grasshopper left null (its
        import Grasshopper                              # variable binding didn't take): put the data in directly
        fixed = []                                      # and recompute what they feed
        for prm in comp.Params.Output:
            val = filled.get(prm.NickName)
            if val is None or any(x is not None for x in prm.VolatileData.AllData(False)):
                continue
            prm.ClearData()
            prm.AddVolatileDataList(Grasshopper.Kernel.Data.GH_Path(0), val if isinstance(val, list) else [val])
            for rec in prm.Recipients:
                rec.Attributes.GetTopLevel.DocObject.ExpireSolution(False)
            fixed.append(prm.NickName)
        if fixed:
            sticky["revit_structure_refilled"] = fixed
    comp.OnPingDocument().ScheduleSolution(1, refill)
    if sticky.get("revit_structure_refilled"):
        info += "\n(outputs passed on directly because Grasshopper didn't bind them: {})".format(
            ", ".join(sticky["revit_structure_refilled"]))
    out["info"] = (out.pop("setup_note", "") + "\n" + sticky.get("revit_structure_wire", "") + "\n" + placed + "\n" + info).strip()
    G.update(out)


try:
    import Rhino                      # inside Grasshopper
    _gh_main()
except ImportError:
    if __name__ == "__main__":
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import karamba_model
        mm = karamba_model.build_model(**FINAL)
        rr = build_revit(mm)
        print(summary(rr, mm))
