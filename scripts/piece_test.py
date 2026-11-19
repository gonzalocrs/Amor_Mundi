"""One-piece print test: a column piece with a downstand rib and the ring piece printed on its side and flipped onto it

Gonzalo's sketch (plan section of one print layer) and Rhino study, built for one piece so the shape and the print
path can be checked before the whole roof is cut:
  - The shell is a printed box: inner skin (2 beads) | cavity with a wavy web (insulation goes here) | outer skin
    (2 beads). The rib is NOT inside the shell (as in scripts/rib_pieces.py) but a U-shaped DOWNSTAND on the room
    side, closed on top by the second inner bead. The 4 bars sit in that tube and it is grouted, so the room sees
    a T in section.
  - COLUMN PIECE: prints upright with the slope direction vertical (print layers square to the slope, as in
    rib_pieces.py; precedent Striatus, Block Research Group ETH 2021). The column channel is a vertical tube in the
    print, so every layer is the same.
  - RING PIECE: the ring runs along the course, which would be a horizontal tube in the print (not printable). So the
    ring piece is printed on its end, with the course direction vertical, which makes the ring a vertical tube too,
    then flipped 90 deg and set on top of the column piece. Where the column crosses, the U side walls are left out
    for `rib_w` of print height (the GAP), so column bars pass through the ring and the node is cast in one pour.
    Precedent for printing a part in the orientation that makes its channels vertical and turning it into place:
    Striatus (blocks printed on their side, rotated into the arch) and the 3dpod roof deck units (Obayashi 2023,
    printed as precast units, then set on the walls and grouted).

Local frame of the roof face (mm): u along the course (horizontal), s up the slope, n square to the face, outward;
n = 0 is the room face of the shell, the downstand is at n < 0.
Print frame: x, y in the bed, z up.  Column piece (x, y, z) = (u, n, s).  Ring piece (x, y, z) = (s, n, u), then
flipped: rotation about the y (= n) axis, (x, y, z) -> (u = z, n = y, s = Hr - x).

Paste into a Python 3 Script component (Rhino 8) or GhPython (Rhino 7). Units: millimetres. The geometry core is pure
Python: `python scripts/piece_test.py` prints the check and draws the layer plans and the assembly into
details/piece-test/ (needs matplotlib and shapely).

INPUTS (all optional)
    L            float   column piece length along the course                         1200
    H            float   column piece height along the slope (= its print height)     450
    Lr           float   ring piece length along the course (= its print height)      1200
    u_col        float   column axis from the left end of both pieces                 L / 2
    bead         float   print width                                                   30
    lattice      float   cavity depth between the skins (insulation + wavy web)       120
    wave         float   pitch of the wavy web (one full wave)                          400
    rib_w        float   clear width of the rib channel                                160
    rib_d        float   clear depth of the rib channel                                160
    bar          float   bar diameter, 4 bars per channel                               12
    cover        float   clear cover from the bar to the printed channel wall           40
    layer_H      float   print layer height                                             10
    speed        float   print speed mm/s                                              100
    min_layer_t  float   shortest safe layer time, s                                     30
    density      float   printed concrete, t/m3                                          2.3
    gap_floor    bool    print the U bottom through the gap (node closed on the room side, one stop per gap layer).
                         False: leave the gap open and close it with a board when pouring.     True

OUTPUTS
    col_paths    column piece: one polyline per contour per layer, on the print bed       -> SaladSlicer
    ring_paths   ring piece: same                                                          -> SaladSlicer
    col_place    Transform print bed -> roof face frame (identity: the frame is (u, n, s))
    ring_place   Transform print bed -> roof face frame (the flip)
    bars         the 4 bar axes of the column and the ring in the face frame
    info         the check
"""
import math

DEFAULTS = dict(
    L=1200.0, H=450.0, Lr=1200.0, u_col=None, bead=30.0, lattice=120.0, wave=400.0, rib_w=160.0, rib_d=160.0,
    bar=12.0, cover=40.0, layer_H=10.0, speed=100.0, min_layer_t=30.0, density=2.3, gap_floor=True,
)


class Section(object):
    """depths (n) of the build-up, shared by both pieces"""

    def __init__(self, p):
        b = p["bead"]
        self.b, self.h = b, b / 2.0
        self.nA = self.h                         # inner skin, room-side bead (it dips round the channel)
        self.nB = b + self.h                     # inner skin, second bead (closes the channel on top)
        self.c0 = 2 * b                          # cavity, room side
        self.c1 = 2 * b + p["lattice"]           # cavity, outer side
        self.T = 4 * b + p["lattice"]            # shell thickness
        self.nO1 = self.T - self.h               # outer skin, outer bead
        self.nO2 = self.T - b - self.h           # outer skin, inner bead
        self.top = b                             # channel clear: n from b - rib_d up to b (under bead B)
        self.bot = b - p["rib_d"]                # channel bottom (clear)
        self.nU = self.bot - self.h              # U bottom bead
        self.down = -(self.bot - b)              # downstand below the room face


def _wave(u0, u1, n0, n1, pitch, step=10.0):
    """wavy web from (u0, n0) to (u1, n1), touching the cavity faces n0 and n1, an odd number of half waves"""
    span = abs(u1 - u0)
    k = max(1, int(round(span / (pitch / 2.0))))
    if k % 2 == 0:
        k += 1 if span / (pitch / 2.0) > k else -1
        k = max(1, k)
    m = max(2, int(math.ceil(span / step)))
    pts = []
    for i in range(m + 1):
        t = i / float(m)
        a = 0.5 - 0.5 * math.cos(math.pi * k * t)          # 0 at n0, 1 at n1, k half waves
        pts.append((u0 + (u1 - u0) * t, n0 + (n1 - n0) * a))
    return pts


def _seq(*parts):
    """join point runs into one polyline, dropping repeated points"""
    out = []
    for part in parts:
        for q in part:
            if not out or math.hypot(q[0] - out[-1][0], q[1] - out[-1][1]) > 1e-6:
                out.append((float(q[0]), float(q[1])))
    return out


def column_layer(p, S):
    """one layer of the column piece, in (u, n): a single continuous path (Gonzalo's sketch)
    1 left end wall down to the room face        2 inner bead A, dipping round the channel (the U downstand)
    3 right end wall up                          4 outer bead O1 back
    5 left end wall down                         6 inner bead B (closes the channel)
    7 wavy web back across the cavity            8 outer bead O2"""
    L, h, b = p["L"], S.h, S.b
    uc, w = p["u_col"], p["rib_w"]
    uL, uR = uc - w / 2.0 - h, uc + w / 2.0 + h          # U walls (bead centres)
    path = _seq(
        [(h, S.nB), (h, S.nA)],
        [(uL, S.nA), (uL, S.nU), (uR, S.nU), (uR, S.nA), (L - h, S.nA)],
        [(L - h, S.nO1)],
        [(h, S.nO1)],
        [(h, S.nB)],
        [(L - b, S.nB)],
        _wave(L - b - h, b + h, S.c0, S.c1, p["wave"]),
        [(b, S.nO2), (L - b, S.nO2)],
    )
    return [path]


def ring_layer(p, S, gap):
    """one layer of the ring piece, in (s, n). The ring channel spans the whole piece width Hr, so the U walls are
    the end walls. In the GAP (where the column crosses) the U walls are left out so the column runs through."""
    Hr, h, b = p["rib_w"] + 2 * S.b, S.h, S.b
    if not gap:
        path = _seq(
            [(h, S.nB), (h, S.nU), (Hr - h, S.nU)],
            [(Hr - h, S.nO1), (h, S.nO1), (h, S.nB)],
            [(Hr - b, S.nB)],
            _wave(Hr - b - h, b + h, S.c0, S.c1, p["wave"]),
            [(b, S.nO2), (Hr - b, S.nO2)],
        )
        return [path]
    shell = _seq(
        [(h, S.nB), (Hr - h, S.nB), (Hr - h, S.nO1), (h, S.nO1), (h, S.c0)],
        _wave(b + h, Hr - b - h, S.c0, S.c1, p["wave"]),
        [(Hr - b, S.nO2), (b, S.nO2)],
    )
    cons = [shell]
    if p["gap_floor"]:
        cons.append([(Hr - h, S.nU), (h, S.nU)])
    return cons


def _plen(P):
    return sum(math.hypot(q[0] - a[0], q[1] - a[1]) for a, q in zip(P, P[1:]))


def _bars(p, S, centre):
    """4 bar centres in a channel section, (across, n)"""
    o = p["cover"] + p["bar"] / 2.0
    w = p["rib_w"] / 2.0
    return [(centre + sx * (w - o), n) for sx in (-1, 1) for n in (S.top - o, S.bot + o)]


def build(p):
    p = dict(p)
    if p["u_col"] is None:
        p["u_col"] = p["L"] / 2.0
    S = Section(p)
    lh = p["layer_H"]
    out = dict(p=p, S=S)
    # column piece: every layer the same, alternate direction so a layer starts where the last ended
    n_c = int(round(p["H"] / lh))
    base = column_layer(p, S)
    out["col"] = [dict(z=(i + 1) * lh, cons=base if i % 2 == 0 else [list(reversed(base[0]))]) for i in range(n_c)]
    # ring piece: print height is the course direction u, the gap is where the column crosses
    n_r = int(round(p["Lr"] / lh))
    g0, g1 = p["u_col"] - p["rib_w"] / 2.0, p["u_col"] + p["rib_w"] / 2.0
    ring = []
    for i in range(n_r):
        zm = (i + 0.5) * lh
        gap = g0 <= zm <= g1
        cons = ring_layer(p, S, gap)
        if i % 2:
            cons = [list(reversed(c)) for c in reversed(cons)]
        ring.append(dict(z=(i + 1) * lh, cons=cons, gap=gap))
    out["ring"] = ring
    out["Hr"] = p["rib_w"] + 2 * S.b
    out["check"] = check(p, S, out)
    return out


def _piece_stats(p, layers):
    b, lh = p["bead"], p["layer_H"]
    t = [sum(_plen(c) for c in ly["cons"]) / p["speed"] for ly in layers]
    length = sum(_plen(c) for ly in layers for c in ly["cons"])
    stops = sum(len(ly["cons"]) - 1 for ly in layers)
    # a travel move between layers when a layer does not start where the last one ended
    for a, c in zip(layers, layers[1:]):
        e, s = a["cons"][-1][-1], c["cons"][0][0]
        if math.hypot(e[0] - s[0], e[1] - s[1]) > 1.0:
            stops += 1
    vol = length * b * lh
    return dict(t_min=min(t), t_max=max(t), path=length, mass=vol * p["density"] / 1e6, stops=stops,
                print_s=length / p["speed"])


def _overlap(p, cons):
    """share of printed area deposited twice in one layer (corners and T-joints), and the worst spot"""
    try:
        from shapely.geometry import LineString
        from shapely.ops import unary_union
    except ImportError:
        return None
    b = p["bead"]
    segs = []
    for c in cons:
        for a, q in zip(c, c[1:]):
            segs.append(LineString([a, q]).buffer(b / 2.0, cap_style=2))
    total = sum(s.area for s in segs)
    return (total - unary_union(segs).area) / total


def check(p, S, out):
    lines, flags = [], []
    c, r = _piece_stats(p, out["col"]), _piece_stats(p, out["ring"])
    ov_c = _overlap(p, out["col"][0]["cons"])
    ov_r = _overlap(p, [x for x in out["ring"] if not x["gap"]][0]["cons"])
    Hr = out["Hr"]
    lines.append("build-up {:.0f} = 2 x {:.0f} inner | {:.0f} cavity + wavy web | 2 x {:.0f} outer; downstand {:.0f} "
                 "below the room face, channel {:.0f} x {:.0f} clear".format(S.T, S.b, p["lattice"], S.b, S.down,
                                                                             p["rib_w"], p["rib_d"]))
    lines.append("COLUMN piece {:.0f} long x {:.0f} up the slope: {} layers, 1 contour per layer, path {:.2f} m/layer, "
                 "layer {:.0f} s, {:.0f} kg, {:.0f} min print, {} stops".format(
                     p["L"], p["H"], len(out["col"]), c["path"] / len(out["col"]) / 1000, c["t_min"], c["mass"],
                     c["print_s"] / 60, c["stops"]))
    ng = sum(1 for x in out["ring"] if x["gap"])
    lines.append("RING piece {:.0f} long (printed on end, {:.0f} tall) x {:.0f} up the slope: {} layers ({} in the gap), "
                 "layer {:.0f}-{:.0f} s, {:.0f} kg, {:.0f} min print, {} stops".format(
                     p["Lr"], p["Lr"], Hr, len(out["ring"]), ng, r["t_min"], r["t_max"], r["mass"], r["print_s"] / 60,
                     r["stops"]))
    face = p["L"] * p["H"] / 1e6
    lines.append("column piece weighs {:.0f} kg per m2 of roof face (rib_pieces.py, rib inside: about 400)".format(
        c["mass"] / face))
    if ov_c is not None:
        lines.append("printed twice at corners and T-joints: column {:.1%}, ring {:.1%} of the bead area".format(
            ov_c, ov_r))
    for name, st in (("column", c), ("ring", r)):
        if st["t_min"] < p["min_layer_t"]:
            k = int(math.ceil(p["min_layer_t"] / st["t_min"]))
            flags.append("RED {} piece: layer only {:.0f} s, print {} at once so each layer gets {:.0f} s".format(
                name, st["t_min"], k, k * st["t_min"]))
    slender = p["Lr"] / Hr
    if slender > 4:
        flags.append("AMBER ring piece prints {:.0f} tall on a {:.0f} x {:.0f} footprint ({:.1f}:1): print it with "
                     "a second ring piece or shorten Lr".format(p["Lr"], Hr, S.T + S.down, slender))
    if r["stops"] and p["gap_floor"]:
        flags.append("AMBER ring piece: {} stops, one per gap layer (the U bottom is a second contour there). "
                     "gap_floor = False removes them; then board the node on the room side when pouring".format(
                         r["stops"]))
    # bars
    o = p["cover"] + p["bar"] / 2.0
    clear = p["rib_w"] - 2 * o - p["bar"]
    if clear < max(p["bar"], 20.0, 16.0 + 5.0):
        flags.append("RED bars: {:.0f} mm clear between bars, under 21 (EC2 8.2, 16 mm aggregate)".format(clear))
    lines.append("bars 4 x D{:.0f}, {:.0f} cover to the printed wall, {:.0f} clear between bars (EC2 8.2 needs 21)".format(
        p["bar"], p["cover"], clear))
    lines.append("joints: column piece ends are {:.0f} / {:.0f} from the channel walls (rib_pieces.py keeps 210)".format(
        p["u_col"] - p["rib_w"] / 2.0 - S.b, p["L"] - p["u_col"] - p["rib_w"] / 2.0 - S.b))
    return dict(lines=lines, flags=flags, col=c, ring=r)


def gcode(res, which, copies=1, spacing=300.0, lift=20.0, title=""):
    """print file for one piece (or `copies` of it side by side on the bed, printed layer by layer together so each
    layer has time to stiffen). Generic G-code: G1 = print move at `speed`, G0 = travel with the nozzle lifted,
    M3 / M5 = pump on / off. Map M3 / M5 to the printer's own pump commands, or use the SaladSlicer chain
    (col_paths / ring_paths -> Program Generator) to write the program in the robot's own language."""
    p = res["p"]
    lays = res[which]
    width = (p["L"] if which == "col" else res["Hr"]) + spacing
    F = p["speed"] * 60.0
    out = ["; {}".format(title or which), "; units mm, absolute, origin = bed corner of the first piece, z = top of the layer",
           "; {} layers of {:.0f} mm, bead {:.0f} mm, {:.0f} mm/s, {} piece(s) side by side, {:.0f} mm apart".format(
               len(lays), p["layer_H"], p["bead"], p["speed"], copies, spacing),
           "; M3 = pump on, M5 = pump off, M221 S = flow %: map to the printer's own commands",
           "G21", "G90", "M5"]
    pos, pump, t, stops = None, False, 0.0, 0
    for i, ly in enumerate(lays):
        out.append("; layer {} z {:.1f}{}".format(i + 1, ly["z"], " GAP" if ly.get("gap") else ""))
        for k in range(copies):
            dx = k * width
            for ci, c in enumerate(ly["cons"]):
                fl = (ly.get("flow") or [None] * len(ly["cons"]))[ci]
                x0, y0 = c[0][0] + dx, c[0][1]
                if pos is None or math.hypot(x0 - pos[0], y0 - pos[1]) > 1.0 or abs(ly["z"] - pos[2]) > 15:
                    if pump:
                        out.append("M5")
                        stops += 1
                        pump = False
                    zt = ly["z"] + lift
                    out.append("G0 Z{:.1f}".format(zt))
                    out.append("G0 X{:.1f} Y{:.1f}".format(x0, y0))
                    out.append("G0 Z{:.1f}".format(ly["z"]))
                elif pos[2] != ly["z"]:
                    out.append("G1 Z{:.1f} F{:.0f}".format(ly["z"], F))
                if not pump:
                    out.append("M3")
                    pump = True
                if fl:
                    out.append("M221 S{:.0f} ; flow {:.0f} %: this bead overlaps the one beside it".format(100 * fl, 100 * fl))
                for (xa, ya), (xb, yb) in zip(c, c[1:]):
                    out.append("G1 X{:.1f} Y{:.1f} F{:.0f}".format(xb + dx, yb, F))
                    t += math.hypot(xb - xa, yb - ya) / p["speed"]
                if fl:
                    out.append("M221 S100")
                pos = (c[-1][0] + dx, c[-1][1], ly["z"])
    out += ["M5", "G0 Z{:.1f}".format(lays[-1]["z"] + 100), "; print time {:.0f} min, {} pump stops".format(
        t / 60.0, stops)]
    return "\n".join(out) + "\n", t, stops


def info(res):
    ch = res["check"]
    return "\n".join(ch["lines"] + (ch["flags"] or ["no flags"]))


# ===================================== Grasshopper =====================================
def _gh_main():
    import Rhino.Geometry as rg
    p = dict(DEFAULTS)
    g = globals()
    for k in DEFAULTS:
        if g.get(k) is not None:
            p[k] = g[k]
    res = build(p)

    def polys(layers):
        out = []
        for ly in layers:
            for c in ly["cons"]:
                out.append(rg.PolylineCurve([rg.Point3d(x, y, ly["z"]) for x, y in c]))
        return out

    Hr = res["Hr"]
    flip = rg.Transform.Identity
    flip.M00, flip.M01, flip.M02, flip.M03 = 0, 0, 1, 0          # u = z
    flip.M10, flip.M11, flip.M12, flip.M13 = 0, 1, 0, 0          # n = y
    flip.M20, flip.M21, flip.M22, flip.M23 = -1, 0, 0, Hr        # s = Hr - x
    S, pp = res["S"], res["p"]
    bars = []
    for x, n in _bars(pp, S, pp["u_col"]):                      # column bars run up the slope (s)
        bars.append(rg.Line(rg.Point3d(x, n, 0), rg.Point3d(x, n, pp["H"] + Hr)))
    for x, n in _bars(pp, S, Hr / 2.0):                         # ring bars run along the course (u)
        bars.append(rg.Line(rg.Point3d(0, n, pp["H"] + Hr - x), rg.Point3d(pp["Lr"], n, pp["H"] + Hr - x)))
    return dict(col_paths=polys(res["col"]), ring_paths=polys(res["ring"]), col_place=rg.Transform.Identity,
                ring_place=rg.Transform.Translation(0, 0, pp["H"]) * flip, bars=bars, info=info(res))


def _publish(o):
    globals().update(o)


def _selftest():
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    res = build(DEFAULTS)
    print(info(res))
    here = os.path.dirname(os.path.abspath(__file__))
    folder = os.path.normpath(os.path.join(here, "..", "details", "piece-test"))
    if not os.path.isdir(folder):
        os.makedirs(folder)
    for name, which, n, title in (("column-piece.gcode", "col", 1, "COLUMN piece, printed upright"),
                                  ("ring-pieces-x3.gcode", "ring", 3, "RING pieces x 3, printed on end, then flipped")):
        txt, t, stops = gcode(res, which, copies=n, title=title)
        with open(os.path.join(folder, name), "w") as f:
            f.write(txt)
        print("{}: {:.0f} min, {} pump stops".format(os.path.join(folder, name), t / 60.0, stops))
    if "--no-draw" not in sys.argv:
        import piece_test_draw
        print("\n".join(piece_test_draw.draw(res, folder)))


try:
    import Rhino  # noqa: F401
    _publish(_gh_main())
except ImportError:
    if __name__ == "__main__":
        _selftest()
