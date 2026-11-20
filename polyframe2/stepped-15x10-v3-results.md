# Stepped courses 15x10: rib net v3, Karamba results (2026-11-19/20)

Files: `stepped-15x10-v3-karamba.gh` (the Karamba canvas, course variant B, graded ribs, bonded courses + fins, no arches) and `stepped-15x10-v3-karamba.3dm` (all study layers). Previews: `previews/2026-11-20/`.

## Geometry
- Shape kept from `stepped-courses-15x10-printed-pieces v2.3dm`: superellipse plan 15 x 10 (n = 4), 20 columns, ring beam at 2.8 m, opening at 12.3 m, inner face from the model.
- Rib net v3 ("light top, corners filled"): 20 columns, rings 40-40-36-32-28-24-20, then 16 ribs on the opening ring. Ring spacing grows about 5 % per band, and node offsets alternate ring by ring, so the leaf/Y pattern continues through the corners. 256 nodes, 384 bars, 508 m of rib. Flattest rib 36.3 deg from horizontal.
- Course division, variant B (chosen): 19 courses with an equal 30.6 cm horizontal step. Heights go from 57.6 cm (bottom) to 46.0 cm (top), about 442 pieces of 1.2 m. The inner face runs 62 deg at the bottom to 56 deg at the top.

## Ribs (graded solid round, C30/37), case: bonded courses with soft joints (E x 0.02) + end-wall fins, typhoon
| band | height | cast core | printed tube | N (kN) | M max (kNm) | max compression | rebar |
|---|---|---|---|---|---|---|---|
| bottom | 2.8 to 5.5 m | 22 cm | 30 cm | -55 to +12 | 9.5 | 10.5 MPa (52 %) | 2D12 |
| middle | 5.5 to 8.5 m | 18 cm | 26 cm | -33 to +10 | 3.3 | 6.5 MPa (32 %) | 2D10 |
| top | 8.5 m to opening | 14 cm | 22 cm | -23 to +11 | 2.0 | 7.3 MPa (36 %) | 2D8 |

Solid round sections are Karamba "Circular Hollow" with wall thickness = radius. I checked inside the model: area 0.0380 m2 for D22.

## Global (variant B, no arches)
- Deflection: 8.5 mm LONG / 12.1 mm typhoon. Buckling load factor 67.
- Loads: LONG = self-weight of ribs, printed courses (881 kN real printed weight from the pieces) and ring beam, plus insulation and finishes at 0.5 kN/m2 on the slope. Total about 1,584 kN. SHORT = LONG + typhoon qp 2.6 kN/m2 (cpe +0.7 windward, -0.5 elsewhere), 195 kN sideways.
- Columns: V 55 to 107 kN (LONG), 11 to 115 kN (typhoon). H up to 35 kN.

## Arches between columns
Not needed structurally: ribs, deflection and buckling barely change. They cut ring-beam bending about 60 % (25 to 9 kNm), but double the column thrust (35 to 79 kN) and give slight uplift at a corner column in typhoon. They are architectural, and allow a lighter ring.

## Tension ring at the base (governing: no arches, typhoon)
- Karamba: N up to +70 kN, My 25 kNm, Mz 6 kNm, torsion 16 kNm, V 42 kN.
- Hand check (half-ring free body): q = 20 x 19.4 kN / 42.5 m = 9.1 kN/m, so 2T = q x 2a and T = 9.1 x 7.3 = 67 kN. That matches the 70 kN.
- Size: 40 x 40 C30/37, 6D16, closed stirrups D8 @ 150 mm. With arches, 30 x 40 with 4D16 + D8 @ 150 is enough.

## Construction (agreed)
- Each piece's centre of gravity falls about 3 cm inside the bearing edge (it tips inward). Pieces are placed with a temporary clip, and the rib is cast every 3 courses.
- Bonding: 10 mm polymer-modified mortar bed; a printed groove on top of each piece with a ring bar D8-D10 + grout (a bond beam in every course); grouted head-joint ducts between pieces.

## Caveats (to confirm)
- All results assume bonded bed joints. With dry joints the ribs alone fail (about 340 % utilisation). The real joint stiffness and the mortar bond must be confirmed by a pull-off / shear test on two printed sample pieces.
- Insulation and finishes load (0.5 kN/m2) is assumed.
- Typhoon pressure coefficients are simplified.
- Earlier Karamba numbers sent before 2026-11-19 22:40 are wrong: cross-sections and material were not reaching the elements. Only the numbers in this note are valid.

## Structure v4: all load cases (2026-11-20). These numbers replace the ones above.
Correction: Karamba "MeshLoad" lost about half of every area load. For example, the half-roof live load should have been 87.5 kN, and Karamba applied 39 kN vertical plus a spurious 35 kN horizontal. All area loads (formwork top-up, insulation, typhoon, live) are now nodal point loads, each face's load split over its 3 nearest nodes, and the resultants have been checked. Total weight W = 1,959 kN (it was 1,720 kN with the lossy mesh load).

Load cases:
- LONG
- Typhoon qp 2.6 kN/m2: +Y, -Y, +X, -X, 45 deg
- 0.6 kN/m2 on half the roof (x > 0 and y > 0)
- Earthquake EQ X / EQ Y: Ci = Z Rt Ai Co = 0.7 x 1 x 1 x 0.2 = 0.14, giving Q = 0.14 x 1,959 = 274 kN (Karamba 279). Z = 0.7 for Okinawa (BSL, MLIT Notification 1793) is from secondary sources and is not yet read in the official table.

Allowable stresses (AIJ, Fc 30): long-term Fc/3 = 10 MPa, short-term 2Fc/3 = 20 MPa. Live load is checked as long-term (conservative).

| element | governing case | forces | size |
|---|---|---|---|
| ribs bottom (core 24 / tube 32, was 22) | LIVE half (long-term) / W45 | 8.6 MPa = 86 % long-term; 12.0 MPa = 60 % short-term | D24, 2D13 |
| ribs middle D18 | W45 | 6.9 MPa (35 %) | 2D10 |
| ribs top D14 | W+X | 6.5 MPa (33 %), tension up to +24 kN | 2D10 |
| base ring 40x40 | W+Y / W45 | N +129 kN, My 27, Mz 17, T 13.7 kNm, V 66 kN | 8D16 (2 extra mid-side bars for torsion), D10 @ 150 |
| crown ring at 12.3 m | W+X | N -18..+7 kN, M 6.3, T 3.5 kNm | 25x25, 4D12, D8 @ 150 |
| columns 36x36 (20) | W45 / EQ Y | N 53..160 kN, M base 36.7 kNm, V 23 kN | 8D16 (pg >= 0.8 % rules out 4D16), hoops D10 @ 100 |
| pad footings | W-Y (overturning), W45 (bearing) | q max 115 kPa < 200; contact 71 %; FS overturning 1.89; FS sliding 2.41 (mu 0.5) | 1.8 x 1.8 x 0.5 at -0.8 m, D13 @ 200 both ways |

Hand checks:
- Crown: rib thrust into the crown, horizontal sum = 34.1 kN (LONG), so q = 34.1 / 8.7 m = 3.9 kN/m. Half-ring free body: C = q a = 3.9 x 1.49 = 5.8 kN compression. Karamba gives 5.1.
- Earthquake: 274 / 20 = 14 kN mean per column (max 24). Drift 7.6 mm at roof level = 1/368 < 1/200.
- Column: sigma = 160/0.1296 + 36.7/0.00778 = 1.2 + 4.7 = 5.9 MPa < 20. Tension face (N 53 kN, M 36.5 kNm): As = (43.2/0.28 - 53)/345 = 300 mm2 per face, and 3D16 = 603 mm2. Buckling factor about 70, so P-delta is about 1 %.
- Footing (W-Y, worst column): N = 61.6 + 56.4 = 118 kN, M = 32.6 + 24.4 x 0.8 = 56 kNm, e = 0.47 m > B/6. q = 2N / (3 (B/2 - e) B) = 115 kPa.

Typhoon governs, not earthquake: the bonded courses + ribs + ring frame take Q = 274 kN with drift 1/368. No perpendicular shear walls are needed for strength. The two corner footings overlap, so cast each corner pair as one combined footing.

## Mortar joints (10 mm polymer-modified mortar), all load cases
- Bed joints at the fins (Karamba fin = 2 end walls, 8 x 30 cm):
  - Worst case W45: N -24..+3.5 kN, strong-axis M up to 4.3 kNm at a few points at the base; 95 % of points are under 0.9 kNm.
  - On the end-wall area alone that gives 4.5 MPa compression and 3.6 MPa bending tension, which is too much for a mortar bond.
  - The real bed joint is the whole piece section over 1.2 m: 2 skins of 4 cm, about 0.40 m apart, plus the end walls. A = 0.12 m2, W = 8.3e-3 m3.
  - Peak compression 0.2 + 0.5 = 0.7 MPa (mortar 30 MPa or more). Peak bending tension 0.5 MPa; typical about 0.1 MPa.
  - Shear 0.17 MPa on the end walls alone, 0.34 of the EN 1996 resistance 0.3 + 0.4 sigma; on the full joint area about 0.03 MPa.
- Head joints (hoop direction): compression 0.23 MPa, tension 0.13 MPa, so about 9 kN per course section. The D10 ring bar in the groove takes 23 kN short-term.
- Required: tensile bond strength of the mortar at least 0.6 MPa (EN 1015-12 pull-off test on printed samples). Where the peaks are (first two courses above the ring beam), add D10 starter bars from the ring beam, grouted into the head-joint ducts.

## Bottom detail piece, updated for the D24 core / D32 tube
- h 57.6 cm, 232 kg (was 230), bearing 15.4 cm.
- The centre of gravity is 3.8 cm inside the bearing edge (was 3.6), so the piece still tips inward.
- Overturning moment 85 Nm, so the clip takes 554 N (56 kgf). The same clip as before is fine.
- Top piece unchanged: 188 kg, clip 40 kgf.
- Previews 16, 17.
