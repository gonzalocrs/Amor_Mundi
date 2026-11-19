"""Joint piece, oval, printed with NO pump stops (Gonzalo, 2026-10-18: "make another version without stopping")

The stop version (joint_toolpath.py) prints the ring's room-side wall as a separate contour, so every ring layer has
a stop. Here every layer is the regular piece's single path with one change: the inner skin bead A is moved out to
become the beam's room-side wall. The path runs down the piece's left end, along the wall (round the bottom of the
oval column), and back up the right end, so the left and right ends cross the tunnel mouth with one bead each. Those
two end beads are cut out with a wire while the concrete is still green (a few hours after printing), which opens the
tunnel at both ends for the ring bars and the pour.
  - floor (3 layers): bead A becomes a zig-zag that fills the beam's floor, passing the column round its bottom;
  - tunnel: bead A becomes the wall, at most 7 mm further in or out than the layer below (35 deg), never inside
    the oval channel;
  - above the crown: the regular path.
The tunnel is flat on the shell side (bead B) and the wall corbels in from the room side, so the crown is higher
than in the stop version. Odd layers run backwards, so each layer starts where the last ended: 0 stops.

`python scripts/joint_nostop.py` writes details/piece-test/joint-oval-nostop.gcode and joint-oval-nostop-paths.png (the oval
version, layers_oval; the first D-shaped version is layers()).
"""
import math
import os

import numpy as np
from shapely.geometry import LineString, Point, box
from shapely.ops import unary_union

import joint_shapes as J
import piece_test

SHAPE = "oval"
B, h = J.B, J.B / 2
L, lh, STEP = J.P["L"], J.P["lh"], J.P["step"]
nA, nB = J.nA, J.nB
nO1 = J.nO1
BOT = J.BOT


def wall_line(cv):
    """the room-side wall's centreline n per layer: outside the oval ring channel by a bead, moving <= STEP a layer,
    and back at bead A at the top; returns (n_w per layer, first tunnel layer)"""
    tgt = J.ring_target(SHAPE)
    n = int(round(J.P["H"] / lh))
    req = []
    for i in range(n):
        s = (i + 0.5) * lh
        c = tgt.intersection(LineString([(-1e3, s), (1e3, s)]))
        req.append(c.bounds[0] - h if not c.is_empty else 1e9)
    first = int(round(J.P["floor"] / lh))
    w = [min(nA, min(req[j] + STEP * abs(i - j) for j in range(first, n))) for i in range(n)]
    for i in range(first):
        w[i] = None                                     # floor layers
    return w, first


def _arc(ring, n_line, u0, u1):
    """the lower part of the bead ring round the column between its two crossings with n = n_line"""
    pts = list(ring.coords)[:-1]
    top = max(range(len(pts)), key=lambda k: pts[k][1])
    pts = pts[top:] + pts[:top]                         # start at the top, so the lower part is one run
    lo = [q for q in pts if q[1] <= n_line]
    if lo and lo[0][0] > lo[-1][0]:
        lo.reverse()
    return [(u0, n_line)] + lo + [(u1, n_line)]


def _cross(ring, n_line):
    c = ring.intersection(LineString([(-1e3, n_line), (L + 1e3, n_line)]))
    xs = sorted(q.x for q in getattr(c, "geoms", [c]))
    return xs[0], xs[-1]


def _strokes(u0, u1, nf, cvb, up_first):
    """zig-zag strokes across the floor (along n) from u0 to u1, odd count, <= one bead apart"""
    k = int(math.ceil((u1 - u0) / B))
    k += 1 if k % 2 == 0 else 0                         # odd number of gaps... -> even strokes; fix below
    m = k + 1 if (k + 1) % 2 == 1 else k + 2            # odd number of strokes
    us = np.linspace(u0, u1, m)
    out, up = [], up_first
    for u in us:
        seg = LineString([(u, nf), (u, nA)]).difference(cvb)
        seg = max(getattr(seg, "geoms", [seg]), key=lambda g: g.length) if not seg.is_empty else None
        if seg is None:
            continue
        a, b = sorted(seg.coords, key=lambda q: q[1])
        out += [a, b] if up else [b, a]
        up = not up
    return out


def layers(ext=False):
    """ext=True (option 2b): the floor and the tunnel's end crossings are printed one bead past each end of the piece,
    so the tunnel mouth opens with one straight cut on the end plane (u = 0 and u = L) instead of cutting round it"""
    path, _ = J.shell_layer(SHAPE, fillet=0)
    k = path.index((L - h, J.nO1))
    head, tail = [(h, J.nB), (h, nA)], path[k:]
    cv = J.col_void(SHAPE)
    ring = cv.buffer(h, 64).exterior
    cvb = cv.buffer(h - 0.5, 64)
    w, first = wall_line(cv)
    nf = w[first]                                        # floor edge: under the first wall
    out = []
    for i in range(len(w)):
        if w[i] is None:                                 # floor: zig-zag, round the column's bottom
            ua, ub = _cross(ring, nf)
            e = -h if ext else h
            left = _strokes(e, ua - h, nf, cvb, up_first=False)
            right = _strokes(ub + h, L - e, nf, cvb, up_first=True)
            mid = _arc(ring, nf, ua, ub)
            if ext:
                p = [(h, nB), (-h, nB)] + left + mid + right + [(L + h, nB), (L - h, nB)] + tail
            else:
                p = head + left + mid + right + tail
        elif w[i] < nA - 0.5:                            # tunnel: bead A moved out to the wall
            n_w = w[i]
            if n_w > -J.P["depth"] + h:                  # the wall would cut the column: go round its bottom
                ua, ub = _cross(ring, n_w)
                mid = _arc(ring, n_w, ua, ub)
            else:
                mid = []
            if ext:                                      # the crossing sits outside the piece, cut off flush
                p = [(h, nB), (-h, nB), (-h, n_w)] + mid + [(L + h, n_w), (L + h, nB), (L - h, nB)] + tail
            else:
                p = head + [(h, n_w)] + mid + [(L - h, n_w), (L - h, nA)] + tail
        else:
            p = path
        p = J._seq_pts(p) if hasattr(J, "_seq_pts") else _dedupe(p)
        geom = LineString(p).buffer(h, cap_style=2, join_style=2).difference(cv).buffer(0)
        out.append(dict(i=i, s=(i + 0.5) * lh, wall=w[i], cons=[p if i % 2 == 0 else list(reversed(p))], geom=geom,
                        z=(i + 1) * lh))
    return out, nf


def _dedupe(p):
    o = []
    for q in p:
        q = (float(q[0]), float(q[1]))
        if not o or math.hypot(q[0] - o[-1][0], q[1] - o[-1][1]) > 1e-6:
            o.append(q)
    return o


def study(ext=False):
    ls, nf = layers(ext)
    over = [0.0] + [J._overhang(a["geom"], b["geom"]) for a, b in zip(ls, ls[1:])]
    tun = [x for x in ls if x["wall"] is not None and x["wall"] < nA - 0.5]
    crown = max(x["s"] for x in tun) + lh / 2
    # the tunnel section (between the wall and bead B) and what the stop version needs
    sec = unary_union([box(x["wall"] + h, x["s"] - lh / 2, B, x["s"] + lh / 2) for x in tun])
    length = sum(LineString(x["cons"][0]).length for x in ls)
    t = [LineString(x["cons"][0]).length / J.P["speed"] for x in ls]
    mass = sum(x["geom"].intersection(box(0, -1e3, L, 1e3)).area for x in ls) * lh * J.P["density"] / 1e6
    tgt_in = J.ring_target(SHAPE).difference(sec).area             # mm2 of the oval channel outside the tunnel
    return dict(layers=ls, over=over, max_over=max(over), crown=crown, tunnel=(J.P["floor"], crown), sec=sec,
                length=length, t=t, mass=mass, fits=tgt_in, floor_edge=nf)


def main(oval=True):
    """writes the no-stop G-code: by default the oval tunnel with its end crossings printed outside and trimmed
    (option 2 of the report); oval=False gives the first, taller D-shaped version"""
    r = study_oval(True) if oval else study()
    r.setdefault("tunnel", (J.P["floor"], r["crown"]))
    ls = r["layers"]
    p = dict(L=L, layer_H=lh, bead=B, speed=J.P["speed"])
    txt, t, stops = piece_test.gcode(dict(p=p, col=ls), "col", title="JOINT piece, oval, NO pump stops: trim the two "
                                     "end tabs off flush while green (x = u, y = n, z = s up the slope)")
    here = os.path.dirname(os.path.abspath(__file__))
    folder = os.path.normpath(os.path.join(here, "..", "details", "piece-test"))
    with open(os.path.join(folder, "joint-oval-nostop.gcode"), "w") as f:
        f.write(txt)
    print("no-stop joint: {:.0f} min, {} stops, layers {:.0f}-{:.0f} s, {:.0f} kg, worst step {:.1f} mm, crown {:.0f} mm,"
          " tunnel {:.0f} cm2".format(t / 60, stops, min(r["t"]), max(r["t"]), r["mass"], r["max_over"], r["crown"],
                                      r["sec"].area / 100))
    draw(r, os.path.join(folder, "joint-oval-nostop-paths.png"))
    return r, t, stops


def draw(r, fn):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon as MP

    ls = r["layers"]
    tun = [x["i"] for x in ls if (x.get("void") if "void" in x else x["wall"] is not None and x["wall"] < nA - 0.5)]
    picks = [(1, "floor"), (tun[len(tun) // 3], "ring tunnel"), (tun[-2], "crown closing")]
    fig = plt.figure(figsize=(15, 16))
    gs = fig.add_gridspec(4, 3)
    for k, (i, name) in enumerate(picks):
        a = fig.add_subplot(gs[k, :])
        x = ls[i]
        for q in getattr(x["geom"], "geoms", [x["geom"]]):
            a.add_patch(MP(list(q.exterior.coords), closed=True, fc="#e4dfd6", ec="none"))
            for hh in q.interiors:
                a.add_patch(MP(list(hh.coords), closed=True, fc="white", ec="none"))
        c = x["cons"][0]
        xs, ys = zip(*c)
        a.plot(xs, ys, color="#d62828", lw=1.2)
        a.plot(xs[0], ys[0], "o", color="#d62828")
        a.plot(xs[-1], ys[-1], "s", color="#d62828")
        for u in (h, L - h):
            if x.get("void") or ("void" not in x and x["wall"] is not None and x["wall"] < nA - 0.5):
                a.annotate("trim off green" if "void" in x else "cut out green", (u, (x["wall"] + nA) / 2), (u + (60 if u < 600 else -260), -175),
                           arrowprops=dict(arrowstyle="->", lw=0.7), fontsize=8)
        a.set_title("Layer {} (s = {:.0f}-{:.0f} mm), {}: 1 continuous path, {:.0f} s".format(
            i + 1, i * lh, i * lh + lh, name, LineString(c).length / J.P["speed"]), fontsize=10)
        a.set_xlim(-20, L + 20)
        a.set_ylim(-200, 260)
        a.set_aspect("equal")
        a.set_ylabel("n (mm)")
    a = fig.add_subplot(gs[3, 0])
    for x in ls:
        sec = x["geom"].intersection(box(299.5, -1e3, 300.5, 1e3))
        for g in getattr(sec, "geoms", [sec]):
            if g.is_empty:
                continue
            a.add_patch(plt.Rectangle((g.bounds[1], x["s"] - lh / 2), g.bounds[3] - g.bounds[1], lh,
                                      fc="#c9c3b8" if x["i"] % 2 else "#b5aea2", ec="white", lw=0.3))
    rt = J.ring_target(SHAPE)
    a.add_patch(MP(list(rt.exterior.coords), closed=True, fill=False, ec="#2f6db3", ls="--"))
    a.set_xlim(-200, 260)
    a.set_ylim(0, J.P["H"])
    a.set_aspect("equal")
    a.set_title("Section at u = 300: tunnel {:.0f} cm2,\ncrown {:.0f} mm, worst step {:.1f} mm".format(
        r["sec"].area / 100, r["crown"], r["max_over"]), fontsize=10)
    a.set_xlabel("n (mm), room side left")
    a = fig.add_subplot(gs[3, 1:])
    a.axis("off")
    a.text(0, 0.95, "Each layer is the regular piece's path with bead A moved out to\nbecome the beam's room-side wall. "
                    "The path crosses the tunnel mouth\nat both ends of the piece: cut those two beads out with a wire\n"
                    "a few hours after printing, while the concrete is green.\nOdd layers run backwards: no pump stops "
                    "in the whole piece.", va="top", fontsize=11)
    fig.suptitle("Joint piece, oval, printed without stopping", fontsize=13)
    fig.tight_layout()
    fig.savefig(fn, dpi=100)
    plt.close(fig)




# ---------------------------------------------------------------- the oval tunnel, still without stops
def _zig(u0, u1, lo, hi, cvb, n_even=True):
    """strokes across n between lo and hi (bead centres), stepping along u from u0 to u1, first stroke going down,
    an even count so the last stroke ends at the top; each stroke is cut back where it meets the column"""
    m = max(2, int(math.ceil((u1 - u0) / B)) + 1)
    if m % 2:
        m += 1
    out, down = [], True
    for u in np.linspace(u0, u1, m):
        seg = LineString([(u, lo), (u, hi)]).difference(cvb)
        if seg.is_empty:
            continue
        seg = max(getattr(seg, "geoms", [seg]), key=lambda g: g.coords[-1][1])     # the part that reaches the top
        a, b = sorted(seg.coords, key=lambda q: q[1])
        out += [b, a] if down else [a, b]
        down = not down
    if not down:                                         # a stroke was dropped at the column: finish at the top
        out.append((out[-1][0], hi))
    return out


def _route(p, q, cv, ring):
    """join p to q without crossing the column: straight if clear, else along the bead ring round its bottom"""
    if not LineString([p, q]).intersects(cv):
        return [q]
    a, b = ring.project(Point(p)), ring.project(Point(q))
    pts = list(ring.coords)
    run = [ring.interpolate(d) for d in np.linspace(a, b, 24)]
    alt = [ring.interpolate((a + (b - a + ring.length) * k / 23) % ring.length) for k in range(24)] if b < a else \
        [ring.interpolate((a - (a + ring.length - b) * k / 23) % ring.length) for k in range(24)]
    low = min((run, alt), key=lambda r: max(x.y for x in r))          # the way round below the column
    return [(x.x, x.y) for x in low] + [q]


def _floor_zig(u0, u1, lo, hi, cv, cvb, ring):
    """floor of a deep ring: strokes across n from the room face lo to bead A hi, odd count, first going down; where a
    stroke meets the column it keeps the part below it, and the joins go round the column's bottom"""
    m = int(math.ceil((u1 - u0) / B)) + 1
    m += 0 if m % 2 else 1
    out, down = [], True
    for u in np.linspace(u0, u1, m):
        seg = LineString([(u, lo), (u, hi)]).difference(cvb)
        seg = min(getattr(seg, "geoms", [seg]), key=lambda g: min(c[1] for c in g.coords))
        a, b = sorted(seg.coords, key=lambda c: c[1])
        st = [b, a] if down else [a, b]
        out += (_route(out[-1], st[0], cv, ring) if out else [st[0]]) + [st[1]]
        down = not down
    return out


def layers_oval(ext=False):
    """every layer one continuous path, tunnel shaped like the stop version (scripts/joint_shapes.py ring_void, both
    faces corbelling in at <= 7 mm a layer):
      - the room-side wall is one bead on the stop version's room face, going round the column's bottom;
      - the strip between the tunnel and bead B (the shell-side face of the tunnel) is filled with a zig-zag that
        rides over the top of the column;
      - the path crosses the tunnel mouth at both ends, as in option 2 (cut out green, or printed outside and trimmed).
    Path order: B-side zig-zag left to right, down the right end, wall right to left, up the left end, O1, web, O2."""
    st = J.study(SHAPE)
    path, _ = J.shell_layer(SHAPE, fillet=0)
    cv = J.col_void(SHAPE)
    ring = cv.buffer(h, 64).exterior
    cvb = cv.buffer(h - 0.5, 64)
    wave = path[path.index((L - B, nB)) + 1:]            # web and O2, as in the regular path
    e = h if ext else 0.0                                # how far the end crossings sit outside the piece
    out = []
    first = min(x["i"] for x in st["layers"] if x["void"])
    for x in st["layers"]:
        i, v, m = x["i"], x["void"], x["outer"]
        # the strokes reach closer to the column 7 mm a layer, from the floor's clearance to touching it
        cvz = cv.buffer(max(1.0, h - 0.5 - J.P["step"] * (i - first)), 64)
        if m is None:
            p, strip, nw = list(path), None, None
        else:
            nw = m + h                                   # the wall's bead centre
            lo_s = v[1] + h if v else nw                 # bottom of the B-side strip (tunnel face, or the room face)
            u0, u1 = (h, L - h) if ext else (h + B, L - h - B)
            if lo_s > nB - 4:                            # strip is (about) bead B alone
                zz = [(h, nB), (L - h + 2 * e, nB)]
            else:
                ua, ub = _cross(cv.buffer(h + 0.5, 64).exterior, lo_s) if BOT - h < lo_s < 30 else (None, None)
                if ua is None:
                    zz = [(h, nB)] + _zig(u0, u1, lo_s, nB, cvz)
                else:                                     # left of the column, over its top, right of it
                    left = _zig(u0, ua - h, lo_s, nB, cvz)
                    right = _zig(ub + h, u1, lo_s, nB, cvz)
                    zz = [(h, nB)] + left + right
                zz += [(L - h + 2 * e, nB)]
            if v:                                         # tunnel layer: wall bead, crossings at both ends
                mid = _arc(ring, nw, *_cross(ring, nw)) if nw > -J.P["depth"] + h else []
                p = zz + [(L - h + 2 * e, nw)] + list(reversed(mid)) + [(h - 2 * e, nw), (h - 2 * e, nB)]
                p += ([(h, nB)] if ext else []) + [(h, nO1), (L - h, nO1), (L - h, nB), (L - B, nB)] + wave
            else:                                         # floor: zig-zag from the room face to bead A, round the column
                k = path.index((L - h, nO1))
                e0 = -h if ext else h
                head = [(h, nB), (-h, nB)] if ext else [(h, nB), (h, nA)]
                tail = [(L + h, nB), (L - h, nB)] if ext else []
                if nw > -J.P["depth"] + h:                # shallow ring: the column cuts the floor's room face
                    ua, ub = _cross(ring, nw)
                    left = _strokes(e0, ua - h, nw, cvb, up_first=False)
                    right = _strokes(ub + h, L - e0, nw, cvb, up_first=True)
                    zz = left + _arc(ring, nw, ua, ub) + right
                else:                                     # deep ring: the column is an island in the floor
                    zz = _floor_zig(e0, L - e0, nw, nA, cv, cvb, ring)
                p = head + zz + tail + path[k:]
                if nw <= -J.P["depth"] + h:               # bead B dips round the column's sides, above it
                    j = p.index((L - B, nB), len(head) + len(zz))
                    cb = cv.bounds
                    dip = _zig(cb[0] - h, cb[2] + h, nw, nB, cvb)
                    p = p[:j] + dip + p[j:]
            strip = (lo_s - h, v) if v else None
        p = _dedupe(p)
        g = LineString(p).buffer(h, cap_style=2, join_style=2, mitre_limit=1.5)
        if strip is not None:                             # the zig-zag fills its strip solid
            u_a, u_b = (-B, L + B) if ext else (0, L)
            g = g.union(box(u_a if not v else 0, strip[0], u_b if not v else L, 60).difference(cvz))
        g = g.difference(cv).buffer(0)
        if v:
            g = g.difference(box(-1e3, v[0], 1e3 + L, v[1])).union(
                LineString(p).buffer(h, cap_style=2, join_style=2, mitre_limit=1.5).intersection(
                    unary_union([box(-B, -1e3, B, 1e3), box(L - B, -1e3, L + B, 1e3)]))).buffer(0)
        out.append(dict(i=i, s=x["s"], wall=nw, void=v, cons=[p if i % 2 == 0 else list(reversed(p))], geom=g,
                        z=(i + 1) * lh))
    return out


def study_oval(ext=False):
    ls = layers_oval(ext)
    keep = box(0, -1e3, L, 1e3)                          # the tabs are trimmed off: judge the piece itself

    def clip(g):
        g = g.intersection(keep)
        return unary_union([q for q in getattr(g, "geoms", [g]) if q.geom_type == "Polygon"])
    over = [0.0] + [J._overhang(clip(a["geom"]), clip(b["geom"])) for a, b in zip(ls, ls[1:])]
    tun = [x for x in ls if x["void"]]
    crown = max(x["s"] for x in tun) + lh / 2
    sec = unary_union([box(x["void"][0], x["s"] - lh / 2, x["void"][1], x["s"] + lh / 2) for x in tun])
    t = [LineString(x["cons"][0]).length / J.P["speed"] for x in ls]
    mass = sum(x["geom"].intersection(box(0, -1e3, L, 1e3)).area for x in ls) * lh * J.P["density"] / 1e6
    ends = [(x["cons"][0][0], x["cons"][0][-1]) for x in ls]
    return dict(layers=ls, over=over, max_over=max(over), crown=crown, sec=sec, t=t, mass=mass, ends=ends)


if __name__ == "__main__":
    main()
