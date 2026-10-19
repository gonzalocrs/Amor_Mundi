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
    the ring beam, crown ring and buttress caps stay CENTRED on the Karamba lines (Revit beam justification Origin).
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
    underside of the ring beam (wall_h). The cap on top is the Karamba cap beam (ring section).
  - Footing: Karamba puts the footing beams on z = 0; here the footing hangs BELOW z = 0 (top at 0, foot_h deep),
    so the buttresses stand on it. Strip on the wall line + one pad under each buttress, joined into one solid.

INPUTS (all optional)
    karamba_gh   str     path of the Karamba .gh; default: grasshopper/Pyramide Karamba 10_14_2026.gh next to
                         this .gh's folder
    origin       Plane   where the module sits in Revit: the Module Origin marker's plane (default World XY)
    rib_top      float   outer face of the ribs from the Karamba shell surface, mm, + = outwards (default: top of
                         the rib zone = bead + rib_d - centroid of the skins)
    any input of karamba_model.py (foot_w, n_cols, ...)  overrides the Karamba .gh value

OUTPUTS
    shell        list Brep   4 roof faces (printed casing)           -> Add DirectShape, category Roofs
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


def build_revit(m, rib_top=None):
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

    # ---- roof shell: 4 faces, mitred on the hips (vertical diagonal planes)
    for k in range(4):
        pts = []
        for z in (z_ring_top, z_crown_bot):
            a_in, a_out = W(z, s_in), W(z, s_out)
            pts += [P(k, a_in, -a_in, z), P(k, a_in, a_in, z), P(k, a_out, a_out, z), P(k, a_out, -a_out, z)]
        out["shell"].append(_hexa(pts))

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
    for k in range(4):
        out["ring"].append((P(k, d_b, -d_b, z_b), P(k, d_b, d_b, z_b)))
        if p["crown_ring"]:
            out["crown"].append((P(k, d_c, -d_c, z_c), P(k, d_c, d_c, z_c)))
    caps = []
    for a, b in m["cap"]:
        if caps and max(abs(u - v) for u, v in zip(caps[-1][1], a)) < 1.0:
            caps[-1][1] = b
        else:
            caps.append([a, b])
    out["cap"] = [tuple(c) for c in caps]

    # ---- buttresses: one per Karamba buttress, real size
    for V, _ in m["but"]:
        foot = V[0]                                      # on the wall centreline, z = 0
        k = max(range(4), key=lambda kk: _dot(frame(kk)[0], foot))
        n, t = frame(k)
        xb = _dot(foot, t)
        a, b = P(k, half, xb, 0.0), P(k, half + p["but_total"], xb, 0.0)
        out["buttresses"].append(_box(a, b, p["but_w"], p["wall_h"], 0.0, t))
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
    out["vol"] = dict(shell_gross=vol(out["shell"]), ribs=vol(out["ribs"]), buttresses=vol(out["buttresses"]),
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
        "shell: 4 faces, {:.0f} thick (room face {:.0f}, outer face +{:.0f} from the Karamba surface), +{:.2f} (ring top) "
        "to +{:.2f} (crown ring underside)".format(lv["t_build"], lv["s_in"], lv["s_out"], lv["ring_top"] / 1000,
                                                    lv["crown_bot"] / 1000),
        "ribs: {} ({}), outer face {:+.0f} from the Karamba surface; columns and hips {:.0f} -> {:.0f} deep, {:.0f} wide; "
        "middle rings {:.0f} x {:.0f}".format(len(r["ribs"]), ", ".join("{} {}".format(c, k) for k, c in sorted(n.items())),
                                              lv["rib_top"], float(p["rib_d_eave"] or p["rib_d"]),
                                              float(p["rib_d_top"] or p["rib_d"]), p["rib_w"],
                                              p["hring_w"] or p["rib_w"], p["rib_d"]),
        "buttresses: {}, {:.0f} x {:.0f} x {:.0f} tall; caps {} beams; ring 4 beams {:.0f} x {:.0f}; crown 4 beams "
        "{:.0f} x {:.0f}".format(len(r["buttresses"]), p["but_total"], p["but_w"], p["wall_h"], len(r["cap"]),
                                 p["ring_w"], p["base_h"], p["crown_b"], p["crown_h"]),
        "footing: {:.0f} wide x {:.0f} deep below z = 0, {} pieces joined into one".format(
            p["foot_w"], p["foot_h"], len(r["footing"])) if r["footing"] else "footing: none (footing = False)",
        "volumes m3 (Revit solids | Karamba): ribs {:.1f} | {:.1f}, buttresses {:.1f} | {:.1f}, ring {:.1f} | {:.1f}, "
        "caps {:.1f} | {:.1f}, crown {:.1f} | {:.1f}, footing {:.1f} | {:.1f}; shell gross {:.1f} (Karamba counts the "
        "printed concrete only: {:.1f})".format(v["ribs"], kv["ribs"], v["buttresses"], kv["buttresses"], v["ring"],
                                                kv["ring"], v["caps"], kv["caps"], v["crown"], kv["crown"],
                                                v["footing"], kv["footing"], v["shell_gross"], kv["shell"]),
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


INPUTS = ["karamba_gh", "origin", "rib_top", "foot_w"]
OUTPUTS = ["info", "params", "shell", "ribs", "rib_names", "buttresses", "footing", "ring_lines", "cap_lines",
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
    out = dict(shell=[], ribs=[], rib_names=[], buttresses=[], footing=[], ring_lines=[], cap_lines=[],
               crown_lines=[], but_lines=[], params="", info="")
    try:
        if not _setup_params(ghenv.Component):          # noqa: F821
            out["info"] = "setting up the inputs and outputs; the component runs again by itself"
            G.update(out)
            return
    except Exception as e:
        out["setup_note"] = "WARNING: could not set up the inputs and outputs ({}); add them by hand".format(e)
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
    kgh = G.get("karamba_gh") or os.path.join(here, "Pyramide Karamba 10_14_2026.gh")
    try:
        vals = _read_karamba_gh(kgh, names)
        for k, v in vals.items():
            p[k] = v
            src[k] = "Karamba .gh"
        note = "read {} values from {}".format(len(vals), os.path.basename(kgh))
    except Exception as e:
        note = "WARNING: could not read the Karamba .gh ({}); using the values analysed on 18-19 Oct".format(e)
    for k in names:                                     # wired inputs win
        if G.get(k) is not None:
            p[k] = G[k]
            src[k] = "input here"
    if isinstance(p.get("hring_z"), (list, tuple)) and len(p["hring_z"]) == 1:
        p["hring_z"] = p["hring_z"][0]
    out["params"] = note + "\n" + "\n".join("{} = {} ({})".format(k, p[k], src[k]) for k in sorted(p))
    try:
        m = karamba_model.build_model(**{k: p.get(k) for k in names})
        r = build_revit(m, G.get("rib_top"))
    except ValueError as e:
        out["info"] = "ERROR: {}".format(e)
        G.update(out)
        return

    doc = Rhino.RhinoDoc.ActiveDoc
    tol = doc.ModelAbsoluteTolerance if doc else 0.01
    pl = G.get("origin")
    xf = rg.Transform.PlaneToPlane(rg.Plane.WorldXY, pl) if pl is not None else rg.Transform.Identity

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
    out["shell"] = [brep(x) for x in r["shell"]]
    out["ribs"] = [brep(x) for x in r["ribs"]]
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
    if parts and len(out["footing"]) != 1:
        info += "\nWARNING: the footing pieces did not join into one solid ({} pieces)".format(len(out["footing"]))
    out["info"] = (out.pop("setup_note", "") + "\n" + info).strip()
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
