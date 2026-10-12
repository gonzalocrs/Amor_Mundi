"""Screening check of the 10 x 10 m buttressed pyramid roof: roof thrust, ring beam, walls, buttresses, footing.
Hand-calculation level (membrane model of four inclined plates), NOT a design. Geometry is read from pyramid_drawings.py;
everything else is in ASSUMPTIONS below and must be replaced with real values (mix, site loads, soil).

Run:  python details/structural_check.py"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pyramid_drawings as g

# ================= ASSUMPTIONS (change these) =================
GAMMA = 24.0            # kN/m3 printed concrete (use the mix's real density)
FCK = 30.0              # MPa characteristic cylinder strength of the printed mix
PRINT_KF = 0.7          # strength knock-down for layer interfaces / printing (assumed)
FYK = 500.0             # MPa rebar
GC, GS = 1.5, 1.15
SOLID_ROOF = (0.5 * (g.T_LEAF0 + g.T_LEAF1) + g.T_SKIN + 0.35 * g.T_LAT) / 1000   # m solid, square to slope (leaf + skin + 35 % of the zig-zag zone)
SOLID_WALL = (g.WALL_LAYERS[0] + g.WALL_LAYERS[2] + 0.35 * g.WALL_LAYERS[1]) / 1000
CLAD_KPA = 0.3          # kN/m2 cladding + finishes
SNOW_KPA = 0.6          # kN/m2 on plan, before slope shape factor (steep roof sheds snow: mu = 0.8 * (60 - slope) / 30, min 0)
QP = 0.9                # kPa peak wind pressure (site dependent)
CF = 1.1                # overall force coefficient (assumed)
MU_FRICTION = 0.4       # footing/soil friction (assumed)
SOIL_ALLOW = 150.0      # kPa allowable bearing (assumed, needs a soil report)
RING_BARS = 8           # Ø16, as in the detail
BUT_SPACING = None      # None = one buttress at mid-span of each side (as in the drawing)

# ================= geometry =================
slope = math.radians(g.SLOPE)
side = g.CLEAR + g.WALL                       # centreline side length of the ring beam
crown = g.OPEN + 0.5 * (g.T_LEAF1 + g.T_SKIN) / 1000 * 1000
L, Lc = side / 1000, crown / 1000
slant = math.hypot(g.RISE / 1000, (L - Lc) / 2)
area_roof = 4 * 0.5 * (L + Lc) * slant        # m2 of roof surface
perim = 4 * L
beam_kn = g.WALL * g.BEAM_H * 1e-6 * GAMMA * perim
wall_kn = g.WALL_H / 1000 - g.BEAM_H / 1000
wall_kn = SOLID_WALL * wall_kn * perim * GAMMA
roof_g = area_roof * (SOLID_ROOF * GAMMA + CLAD_KPA)
mu_s = max(0.0, 0.8 * (60 - g.SLOPE) / 30)
roof_q = SNOW_KPA * mu_s * L * L              # kN snow on the plan area
fcd = FCK / GC * PRINT_KF
fyd = FYK / GS

def row(name, demand, cap, unit):
    ur = demand / cap
    print("  {:<46s} demand {:>9.1f} {:<4s} capacity {:>9.1f}   UR {:>5.2f}  {}".format(name, demand, unit, cap, ur, "OK" if ur <= 1 else "FAIL"))
    return ur

print("GEOMETRY  side {:.2f} m, slope {:.1f} deg, roof area {:.0f} m2, ring beam {:g}x{:g}".format(L, g.SLOPE, area_roof, g.WALL, g.BEAM_H))
print("WEIGHTS   roof {:.0f} kN, ring beam {:.0f} kN, wall {:.0f} kN, snow (plan) {:.0f} kN".format(roof_g, beam_kn, wall_kn, roof_q))

# ---------- load combinations (ULS) ----------
roof_down = 1.35 * roof_g + 1.5 * roof_q
V = roof_down / perim                          # kN per metre of eave reaching the ring beam
H = V / math.tan(slope)                        # outward thrust at the eave, kN/m (membrane, strut action)
print("\nROOF      factored vertical reaction {:.1f} kN/m, outward thrust {:.1f} kN/m (membrane model)".format(V, H))

# ---------- 1. ring beam as tension tie (membrane action) ----------
T = H * L / 2
As = RING_BARS * math.pi * 16 ** 2 / 4
print("\n1. RING BEAM - tension tie (thrust resisted by hoop tension, buttresses unloaded)")
u1 = row("ring tension vs {} x Ø16 at fyd".format(RING_BARS), T, As * fyd / 1000, "kN")
print("   splices at corners needed: lap >= 50 d = {:g} mm, staggered".format(50 * 16))

# ---------- 2. ring beam as beam on buttresses (bending), upper bound for buttress load ----------
span = L / 2                                    # corner to mid-span buttress
M_beam = H * span ** 2 / 10                     # continuous, uniform outward load, kNm
R_but = 1.25 * H * L                            # mid reaction of a 2-span continuous beam, kN
d = g.WALL - 60.0                               # outward bending: beam width acts as depth
b = g.BEAM_H
Ast = 3 * math.pi * 16 ** 2 / 4                 # 3 Ø16 on the tension face (horizontal bending)
z = 0.9 * d
Mrd = Ast * fyd * z / 1e6
print("\n2. RING BEAM - bending between buttresses (conservative: no tie action at all)")
u2 = row("horizontal bending M = H l^2/10, 3 Ø16 per face", M_beam, Mrd, "kNm")
print("   buttress reaction (upper bound) {:.0f} kN".format(R_but))

# ---------- 3. wall: vertical compression + slenderness ----------
N_wall = V + beam_kn / perim * 1.35 + 1.35 * wall_kn / perim            # kN/m at wall base
h_eff = g.WALL_H / 1000 - g.BEAM_H / 1000
slender = h_eff / (g.WALL / 1000)
Nrd = fcd * SOLID_WALL * 1000                                           # kN/m, solid concrete only
print("\n3. WALL (printed, solid fraction {:.0f} %)".format(100 * SOLID_WALL / (g.WALL / 1000)))
u3 = row("axial load at base vs fcd * solid area", N_wall, Nrd * (1 - slender / 30), "kN/m")
print("   slenderness h/t = {:.1f} (reduction factor 1 - h/(30t) applied)".format(slender))

# ---------- 4. buttress overturning / sliding under the upper-bound reaction ----------
lever = (g.WALL_H - g.BEAM_H / 2) / 1000                               # height of the thrust above the footing top
trib = L / 2 + 0.0                                                      # m of wall/roof carried per buttress
W_trib = trib * (V / 1.35 + wall_kn / perim + beam_kn / perim)        # kN, characteristic
arm = (g.BUT_TOTAL / 1000) - 0.15                                      # from the thrust line (inner side) to the outer toe
M_ov = R_but * lever
M_res = W_trib * arm
print("\n4. BUTTRESS - overturning about the outer toe, thrust taken ENTIRELY by the buttress (upper bound)")
u4 = row("overturning moment vs stabilising", M_ov, M_res, "kNm")
u4b = row("sliding vs friction on the footing", R_but, MU_FRICTION * W_trib, "kN")
print("   buttress reinforcement/tie to the wall needed if this governs: {:.0f} kN to be carried through the printed layers".format(R_but))

# ---------- 5. wind, overall ----------
A_wall = g.WALL_H / 1000 * (L + g.WALL / 1000)
A_roof = 0.5 * (L + Lc) * g.RISE / 1000
Fw = 1.5 * QP * CF * (A_wall + A_roof)
M_w = Fw * (g.WALL_H / 1000 + g.RISE / 3000)
W_tot = roof_g + beam_kn + wall_kn
B = (g.CLEAR + 2 * g.BUT_TOTAL) / 1000
print("\n5. WIND (whole building overturning, uplift ignored)")
u5 = row("overturning vs 0.9 G * B/2", M_w, 0.9 * W_tot * B / 2, "kNm")

# ---------- 6. footing bearing ----------
q = W_tot * 1.35 / (4 * L * g.FOOT_W / 1000)
print("\n6. FOOTING")
u6 = row("bearing pressure vs allowable (assumed)", q, SOIL_ALLOW, "kPa")

print("\nBRACKET: if the ring acts as a tie (check 1) the buttresses see almost nothing; if it only bends (checks 2,4) they take {:.0f} kN each.".format(R_but))
print("The truth lies between: model the roof + ring + buttress stiffnesses in FE to find the split.")
print("NOT CHECKED: crown compression ring, hip buckling, shell buckling, interface (layer) bond in tension/shear, seismic, creep.")
worst = max(u1, u2, u3, u4, u4b, u5, u6)
print("Governing UR {:.2f}".format(worst))
