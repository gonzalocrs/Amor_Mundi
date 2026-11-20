# Stepped courses 10x10: rib net v3, Karamba structure v4 (2026-11-20)

Files: `stepped-10x10-v3-karamba.gh` (the Karamba canvas, same build as the 15x10 v4). Rhino layers in the open model: `10x10 stepped v3 (16 columns)` (net, course rings, columns) and `10x10 structure v4 - all load cases (Karamba)` (results). These sit at x 85, y -20, next to the 15x10. Previews: `previews/2026-11-20/18` to `22`.

## Geometry
- Superellipse plan 10 x 10 (n = 4). Ring beam at 2.80 m, opening 3.0 m at 8.19 m.
- Profile: the 15x10 long-side inner-face profile, scaled to the 10x10 span (x 0.568 both ways), so the face angles are the same.
- Courses, variant B: 11 courses at an equal 30 cm step (30.6 cm would miss the 3.0 m opening by 13 cm). Heights run 55.0 / 51.5 / 50.3 / 49.4 / 48.8 / 48.4 / 48.0 / 47.6 / 47.2 / 47.1 / 46.0 cm. The face is 61 deg at the bottom and 57 deg at the top.
- Rib net v3, same generator and rules as the 15x10 v3 (leaf/Y split-and-merge, alternating ring offsets, 5 % growth per band):
  - 16 columns, then rings 32-32-28-24 at 3.29 / 4.29 / 5.34 / 6.44 m, then 16 ribs on the opening ring.
  - 148 nodes, 228 bars, 298 m. Flattest rib 36.7 deg.
  - With an extra 20 ring the flattest rib is 32.5 deg, so I rejected it.
- The net is script-generated (the v3 generator with only the plan, column count and ring counts changed). It is not a PolyFrame form-find.

## Model (as the 15x10 structure v4)
- Graded solid round ribs (Karamba "Circular Hollow" with wall = radius). Sections were checked inside the model: A = 0.0314 m2 for D20.
- Bonded courses (E x 0.02) with 24 end-wall fins.
- Columns full height, fixed at the foundation. Base ring and crown ring.
- All area loads are nodal point loads (each face split over its 3 nearest nodes). Resultants checked:
  - formwork top-up + insulation: 224 kN
  - half-roof live: 45.8 kN = 0.6 x 76 m2
  - typhoon: 111 kN sideways
  - EQ: 0.14 x 993 = 139 kN
- Load cases: LONG; typhoon W+Y, W-Y, W+X, W-X, W45; LIVE 0.6 kN/m2 on half the roof (x, y); EQ X, EQ Y (Ci 0.14).
- Total weight W = 993 kN.

## Sizes (AIJ Fc 30: long-term 10 MPa, short-term 20 MPa; live load checked as long-term)
| element | governing case | forces | size |
|---|---|---|---|
| ribs bottom (2.8 to 4.33 m), core 20 / tube 28 | LIVE half (long-term) / W45 | 6.2 MPa = 62 % long-term; 8.5 MPa = 43 % short-term | D20, 2D12 |
| ribs middle (4.33 to 6.04 m) D16 / tube 24 | W45 | 4.5 MPa (23 %) | 2D10 |
| ribs top (6.04 m to opening) D14 / tube 22 | W+Y | 4.8 MPa (24 %), tension up to +12 kN | 2D10 |
| base ring 30 deep x 40 wide | W+Y / W45 / EQ | N +62 kN, My 13.8, Mz 8.1, T 6.3 kNm, V 38 kN | 6D13 (2 mid-side bars for torsion), D10 @ 150 |
| crown ring at 8.19 m | W+Y | N -17.6..+2.4 kN, M 4.7, T 2.1 kNm | 25x25, 4D12, D8 @ 150 |
| columns 30x30 (16) | W45 / EQ | N 32..94 kN, M base 18.2 kNm, V 12.5 kN | 4D16 (pg 0.89 % >= 0.8 %), hoops D10 @ 100 |
| pad footings | W45 | q max 114 kPa < 200; contact 76 %; FS overturning 2.03; FS sliding 3.33 (mu 0.5) | 1.4 x 1.4 x 0.5 at -0.8 m |

The first run used the 15x10 sizes (ribs D24/D18/D14, ring 40x40, columns 36x36). Maximum rib stress was 5.1 MPa long-term and 6.8 MPa short-term, so I reduced the sizes to the ones above and ran all 10 cases again. All numbers in the table are from the second run. The top rib stays D14, the practical minimum for 2D10 with cover.

## Global
- Deflection: 1.6 mm LONG, 4.5 mm typhoon.
- Buckling load factor 125.
- Drift: 2.9 mm under EQ at roof level (about 1/2,800), 4.0 mm under typhoon.
- Earthquake: 139 / 16 = 8.7 kN mean per column (max 12.5).
- Typhoon governs the columns and the ring; half-roof live governs the bottom ribs. No shear walls are needed for strength.

## Hand checks
- Column: sigma = 94/0.09 + 18.2/0.0045 = 1.0 + 4.0 = 5.1 MPa < 20. Tension face (N 32 kN, M 16 kNm, z 0.20 m): As = (80 - 16) kN / 345 MPa = 187 mm2 per face, so 2D16 (402 mm2) per face.
- Ring tension: 62 kN / 345 MPa = 180 mm2.
  - Bending My 13.8 kNm on d = 0.24 m: 185 mm2 per face.
  - Torsion 6.3 kNm (A0 about 0.065 m2): Al = 146 mm2, At/s = 140 mm2/m per leg.
  - Total about 700 mm2, so 6D13 (760 mm2). D10 @ 150 (523 mm2/m) covers the torsion.
- Crown: the 32 top ribs give a horizontal thrust of 25 kN (LONG). For a round ring that is q = 25 / 11 m = 2.3 kN/m and C = q a = 3.4 kN. Karamba gives 6 to 8 kN: the squarish crown and its corners add bending, so the Karamba value governs.
- Footing (W45, worst column): N = 43.5 + 34 kN self-weight, M = 26.7 kNm, e > B/6, q = 114 kPa.

## Caveats
Same as the 15x10:
- Bonded bed joints are assumed (pull-off test required).
- Insulation and finishes load (0.5 kN/m2) is assumed.
- Typhoon cpe are simplified.
- Z = 0.7 is from secondary sources.
