"""Option 3 for the ring course: post-tensioned printed course (Masoud's printed bridges, applied to the ring)

No ring tunnel and no ring pour. The ring course is printed like a regular piece, with four small ducts along the
course (two near the room face, two near the weather face, one pair low and one pair high). After the courses are
laid and the columns cast, a greased-and-sheathed monostrand is threaded through each line of ducts, straight from
corner to corner of the square, anchored on the hip ribs and stressed. The printed concrete of that course then
works as the ring, kept in compression by the tendons.

How a duct is printed with no pump stop:
  - bead B (room side) steps out and bead O2 (weather side) steps in, 7 mm a layer (the corbel limit), opening a
    groove between them and the face beads A and O1; the web follows them so it stays joined
  - with the groove 25 mm wide, a 25 mm duct tube is laid in it by hand (a layer takes about a minute)
  - the next layer brings B and O2 straight back, resting on the tube
  - the path still crosses the groove at both ends of the piece (the end beads), so each duct is closed by a 30 mm
    plug at each end: 8 short holes per piece, drilled (or pushed through while green) to join the ducts up.
"""

import math
import os

from shapely.geometry import box
from shapely.ops import unary_union

import joint_shapes as J
import piece_test

SHAPE = "oval"
L, H, lh, B = J.P["L"], J.P["H"], J.P["lh"], J.B
h = B / 2
DUCT = 25.0                                     # duct tube outside diameter; 20 mm bore for a 0.5" monostrand
OPEN = [7.0, 14.0, 21.0, 25.0, 25.0]            # groove width, layer by layer
WEB = OPEN + [18.0, 11.0, 4.0]                  # the web steps back at 7 mm a layer once the duct is in
LOW, HIGH = 5, 33                               # first groove layer of the low and the high duct


def _shift(i, seq):
    for j0 in (LOW, HIGH):
        if j0 <= i < j0 + len(seq):
            return seq[i - j0]
    return 0.0


def duct_rise():
    """how far above the groove's first layer the tube's centre ends up, resting in the V the steps make"""
    r = DUCT / 2
    zb = 0.0
    for k, g in enumerate(OPEN):
        if g >= DUCT:
            break
        top = (k + 1) * lh                      # at this height the tube must be no wider than the groove
        d = r - math.sqrt(r * r - (g / 2) ** 2)
        zb = max(zb, top - d)
    return zb + r


RISE = duct_rise()
DUCT_S = (LOW * lh + RISE, HIGH * lh + RISE)     # duct centres up the slope
DUCT_N = (B + DUCT / 2, J.T - B - DUCT / 2)      # room-side and weather-side duct centres
assert LOW * lh + RISE + DUCT / 2 <= (LOW + len(OPEN)) * lh


def ducts():
    return [(n, s) for s in DUCT_S for n in DUCT_N]


def layers():
    out, prev = [], None
    for i in range(int(round(H / lh))):
        g, w = _shift(i, OPEN), _shift(i, WEB)
        path, pg = J.shell_layer(SHAPE, nb=J.nB + g, no2=J.nO2 - g, w0=J.c0 + w, w1=J.c1 - w)
        if i % 2:
            path = list(reversed(path))
        if prev is not None and math.hypot(path[0][0] - prev[0], path[0][1] - prev[1]) > 0.5:
            path = [prev] + path                # step across to where the last layer ended: no lift, no stop
        prev = path[-1]
        out.append(dict(i=i, s=(i + 0.5) * lh, z=(i + 1) * lh, geom=pg, cons=[path], groove=g))
    return out


def _tubes():
    return unary_union([box(0, n - DUCT / 2, L, n + DUCT / 2) for n in DUCT_N])


def study():
    ls = layers()
    over = [0.0]
    for a, b in zip(ls, ls[1:]):
        below = a["geom"]
        if a["groove"] and not b["groove"]:
            below = below.union(_tubes())       # the closing layer rests on the tubes
        over.append(J._overhang(below, b["geom"]))
    mass = sum(x["geom"].area for x in ls) * lh * J.P["density"] / 1e6
    return dict(layers=ls, over=over, max_over=max(over), mass=mass, ducts=ducts())


# 0.5" monostrand, greased and sheathed (unbonded), one in each duct
AP, FPK, E_P = 98.7, 1860.0, 195e3
JACK = 0.75                                     # of fpk at the jack
LOSS = 0.25                                     # anchor set, shrinkage and creep of the printed mix, relaxation


def tendon_check():
    """the printed course as the ring, with the middle-ring forces from Karamba's final run (2026-10-19, SHORT).
    Only the four shell beads A, B, O2, O1 are counted (the web is left out), full piece height"""
    N, My, Mz = 26.0e3, 9.0e6, 14.7e6
    walls = [J.nA, J.nB, J.nO2, J.nO1]
    nc = sum(walls) / 4
    A = 4 * B * H
    In = sum(B * H * (n - nc) ** 2 + H * B ** 3 / 12 for n in walls)
    Is = 4 * B * H ** 3 / 12
    Wn, Ws = In / (J.T - nc), Is / (H / 2)
    sb = max(Mz / Wn + My / Ws, My / Wn + Mz / Ws)   # put the larger moment on the weaker axis
    sN = N / A
    need = (sb - sN) * A / 4                    # per tendon, so no edge goes into tension
    P0 = JACK * FPK * AP
    Pe = P0 * (1 - LOSS)
    sp = 4 * Pe / A
    return dict(A=A, Wn=Wn, Ws=Ws, sb=sb, sN=sN, need=need, P0=P0, Pe=Pe, sp=sp,
                smin=sp + sN - sb, smax=sp + sN + sb, s0=4 * P0 / A + sN + sb)


def main():
    r = study()
    p = dict(L=L, layer_H=lh, bead=B, speed=J.P["speed"])
    txt, t, s = piece_test.gcode(dict(p=p, col=r["layers"]), "col", title="ring course with 4 tendon ducts")
    here = os.path.dirname(os.path.abspath(__file__))
    fn = os.path.normpath(os.path.join(here, "..", "details", "piece-test", "joint-tendon.gcode"))
    with open(fn, "w") as f:
        f.write(txt)
    c = tendon_check()
    print("ducts at", [(round(n, 1), round(s_, 1)) for n, s_ in r["ducts"]])
    print("{} stops {:.0f} min {:.0f} kg worst overhang {:.1f} mm".format(s, t / 60, r["mass"], r["max_over"]))
    print("A {:.0f} Wn {:.2e} Ws {:.2e} bending {:.2f} axial {:.2f} need {:.0f} kN/tendon".format(
        c["A"], c["Wn"], c["Ws"], c["sb"], c["sN"], c["need"] / 1e3))
    print("P0 {:.0f} kN Pe {:.0f} kN prestress {:.1f} MPa edges {:.1f}..{:.1f} MPa, at stressing {:.1f}".format(
        c["P0"] / 1e3, c["Pe"] / 1e3, c["sp"], c["smin"], c["smax"], c["s0"]))
    print("wrote", fn)


if __name__ == "__main__":
    main()
