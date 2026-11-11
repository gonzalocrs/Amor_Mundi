# Making the printed casing structural (thin shell study)

Gonzalo, 2026-11-11. First pass: precedents and simple hand checks, compared with net 19 (Karamba, 10x10 m, 6 m rise, 3 m crown, midterm load basis).

**Short answer:** yes, the casing can carry the roof. In compression it is far below its strength, and buckling has a large margin *if the surface is curved* like net 19 (not flat pyramid faces). Typhoon uplift decides the thickness. A plain 60 mm shell is lighter than the wind suction, so the pieces must either be heavier (about 105 mm solid), or be tied together and down by small cast seams with one bar each. Against net 19 plus its casing, roughly 40 to 75% less concrete and about a third of the earthquake force.

---

## 1. Precedents (what each one proves for us)

Figures marked * are from memory and still need checking against the sources.

| Precedent | What it is | What it proves for us |
|---|---|---|
| **Armadillo Vault**, Block Research Group (ETH) + Ochsendorf DeJong & Block + Escobedo Group, Venice 2016 | 399* cut limestone pieces, no mortar, no steel, 5–12 cm* thick, ~16 m* span | A thin shell made of separate pieces stands in pure compression if the shape is funicular and the joints are cut perpendicular to the force flow. Paper: Rippmann et al., *The Armadillo Vault*, AAG 2016, pp. 344–363 ([ETH](https://www.research-collection.ethz.ch/entities/publication/99827dbc-a7f2-46e8-be5f-8bcdd3c0ae45)) |
| **Striatus**, BRG + Zaha Hadid CODE + incremental3d, Venice 2021 | 3D-printed concrete arched footbridge, 53* printed blocks, dry-assembled, unreinforced, ties at the supports | The same idea with **printed concrete**: print layers are set perpendicular to the compression, so the weak layer interfaces are only squeezed, never pulled. Our closest precedent. |
| **Nervi, Palazzetto dello Sport**, Rome 1957 | ~1,620* precast ferrocement pieces, ~25 mm* thick, used as formwork with ribs cast between them | Our current scheme (casing + cast ribs). In Nervi the pieces end up working together with the ribs, which is the step this study takes. |
| **Heinz Isler, Deitingen service station**, 1968 | Form-found concrete shells, ~31 m* span, ~9 cm* thick | Shells of this size need only 6–10 cm when the form follows the load. |
| **Félix Candela, Los Manantiales**, Xochimilco 1958 | Hypar shell, 4 cm* thick | Double curvature gives stiffness, not thickness. |
| **HiLo roof, NEST (ETH)**, 2021 | Thin concrete sandwich shell (two concrete layers with insulation between*) | A structural thin shell can also carry the insulation, which matters for our R-value. |

None of these faced a typhoon: Armadillo was indoors and Striatus was small and outdoors for a summer. That is why uplift (section 3) is the deciding check.

## 2. What changes in the construction

- **Now:** printed casing = non-structural formwork + insulation; ribs (net 19, 150x250) carry everything.
- **Structural casing:** the printed pieces carry the compression themselves. The joints between pieces become small cast seams (with one bar) that tie the pieces together, instead of the big ribs. Base ring as tension tie, crown ring in compression (like the Pantheon oculus).
- **Print orientation (35° rule):** each piece is printed lying with its thickness horizontal, so the shell wall stands nearly vertical on the printer bed (a 1.5 m piece of a curved shell leans well under 35°). Turn the piece so the layers run along the rings, so the main downhill compression crosses the layers (squeezes them), as in Striatus.
- **Pieces:** ~167 m² of roof / (1.5 x 1.5 m) ≈ 75 pieces (crane limit ~1.5 m). Weight 0.32 t at 60 mm, 0.57 t at 105 mm.
- **Beads:** 60 mm = 2 beads of 30 mm; 90 mm = 3 beads; 105 mm = 3 beads of 35 mm.

## 3. Hand checks (one 1 m wide strip, 2D)

**Loads.** Roof area ≈ 167 m² on a 100 m² plan (= the midterm 500 kN at 3.0 kN/m²), so sloped load x 1.67 = plan load.
Shell 60 mm = 0.06 x 24 = 1.44 kN/m² + insulation and skin ~0.5 = **G ≈ 1.94 kN/m²** of roof.
Design check uses 3.0 kN/m² (same as the midterm and Karamba basis, includes some live load) → 5.0 kN/m² on plan.

**a) Compression.** Strip as a funicular arch, span L = 10 m, rise f = 6 m, plan load w = 5.0 kN/m:
- Thrust H = wL²/(8f) = 5.0 x 100 / 48 = **10.4 kN/m**
- Vertical at support V = wL/2 = **25 kN/m**
- Force at the support = √(10.4² + 25²) = **27 kN per m** (net 19's highest bar force was 27 kN in one rib: same order, now spread over every metre)
- Stress at 60 mm: 27 / (1000 x 60) = **0.45 MPa**. Concrete ~30 MPa. Even if the printed layer joints are 5 times weaker, it uses under 10%.

**b) Buckling** (the usual limit for thin shells). Curvature radius of a 10 m span, 6 m rise arch: R = (5² + 6²) / (2 x 6) = 5.1 m.
Classic shell buckling pressure p = 1.21 E (t/R)², reduced to 20% for imperfections and creep, E = 10 GPa long-term:
p = 0.2 x 1.21 x 10,000,000 kPa x (0.06 / 5.1)² = **≈ 330 kPa**, against 3 kPa applied → factor **~110**.
This is true only where the surface is curved. A flat pyramid face has R → infinity and would buckle or bend, so the casing must follow net 19's curved, form-found surface.

**c) Typhoon uplift** (deciding check). Suction on the roof: 0.7 x qp 2.6 = **1.82 kN/m²** upward (open crown can add internal pressure on top of this, not counted).
- Service (1.0 G vs 1.0 W): 1.94 down vs 1.82 up → only just holds, no margin.
- Design (0.9 G vs 1.5 W): 0.9 x 1.94 = 1.75 down vs 1.5 x 1.82 = 2.73 up → **1.0 kN/m² net uplift**, about 167 kN over the roof, ~7 kN per support for 24 supports.
- To hold it by weight alone: shell weight needed = 2.73 / 0.9 − 0.5 = 2.53 kN/m² → **t ≈ 105 mm solid**.
- Or keep 60–75 mm and give each seam one bar, anchored into the base ring (7 kN per support is small).
- One-sided wind (pushing one face, sucking the other) bends the shell. A dry-joined shell has no precedent for that in a typhoon, so this needs a Karamba shell check.

**d) Earthquake** (Japan base shear coefficient C0 = 0.2, my simple reading):
- Structural casing 60 mm: (167 x 1.44) + (167 x 0.5) ≈ 325 kN → **~65 kN** sideways.
- Net 19 + casing: ribs 21.9 m³ x 24 = 526 kN + casing 500 kN ≈ 1,030 kN → **~205 kN** sideways.
- A lighter roof means about a third of the sideways force on the walls and base ring.

## 4. Comparison with net 19

| | Net 19 + non-structural casing (now) | A. 60–75 mm shell + seams with bars | B. 105 mm shell, no steel (Armadillo / Striatus) | C. Printed sandwich: two 30 mm skins + webs, insulation inside, seams with bars |
|---|---|---|---|---|
| Concrete | ribs 21.9 m³ + casing ~21 m³ ≈ **43 m³** | **~10–13 m³** + seams | **~17.5 m³** | **~12–13 m³** (≈75 mm equivalent) + seams |
| Compression | OK (ribs) | 0.45 MPa | ~0.35 MPa (heavier) | ~0.4 MPa |
| Buckling | ribs, factor 177 | ~110 (curved only) | higher | highest (deep section) |
| Typhoon uplift | weight holds | **bars needed** | **weight holds** | **bars needed** |
| One-sided wind | ribs bend | needs check | needs check, riskiest | best (deep section) |
| Insulation | inside the casing | outside, extra layer | outside, extra layer | inside (concrete webs are thermal bridges, R-value check) |
| Earthquake | ~205 kN | ~65 kN | ~100 kN | ~75 kN |

## 5. Recommendation

**Option C**, the printed sandwich: it is the current casing, made to carry load. It keeps your "eggshell holds the insulation" idea, its depth handles one-sided typhoon wind best, and the big ribs shrink to small cast seams with one bar, which tie the pieces together against uplift. Precedents: Striatus (printed, layers across the force), Nervi (pieces + cast seams working together), HiLo (structural shell with insulation inside).

Still to confirm:
1. The casing follows net 19's curved surface. The PolyFrame form stays the same, only the build-up of the members changes.
2. A Karamba **shell** check of 19's surface (shell elements instead of bars), with one-sided typhoon and half load. It needs your PC with your Rhino saved and closed.
3. R-value with concrete webs crossing the insulation.
4. Wind qp 2.6 and the open-crown internal pressure.
