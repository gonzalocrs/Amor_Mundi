# Karamba analysis: step-by-step

How to go from `scripts/karamba_model.py` to analysis results in Grasshopper. The wiring reference
is in the README ("Karamba model"); this file is the walkthrough.

## 0. Set up a new PC

1. **Rhino 8.** The script runs in the Python 3 Script component, and nothing needs `pip install`.
   The first time you open a Py3 component, Rhino sets up its Python. Let it finish.
2. **Karamba3D 3.1.** In Rhino type `PackageManager`, search *Karamba3D*, install, and restart Rhino.
   The file was saved with 3.1.60309.
3. **Licence.** The model has about 1,200–1,400 shell elements and about 800 rib beams, far above
   the limits of the free version, so you need a trial or an educational licence from
   karamba3d.com. The `License` component in the file shows your status.
4. **Units.** Start Rhino from the *Large Objects – Millimeters* template, or set the document to mm.
   Karamba reads the document units (`UnitLength = auto`), and the script works in mm.
5. Open `grasshopper/Pyramide Karamba 10_14_2026.gh`. You don't need the `.3dm`: the script builds
   all the geometry itself.

## 1. Fix the Python component

The embedded script is current, but the component is missing some outputs. Zoom in on the
component, click **+** on the output side, and rename each new output exactly:

- `t_roof_elems`, `crown_b`, `concrete`, `rise`, `slope`

Optional inputs: click **+** on the input side, rename to a parameter name (`mesh_size`,
`rise`, `rib_d`, `wind_dir`, `fixed`, ... see the README table), and set the type hint
(right-click the input → *Type hint*): `float` for numbers, `bool` for `fixed` / `crown_ring`.
Wire a slider. Leave anything you don't need unconnected: it keeps the drawing value.

Check `info` in a panel. It should say `connectivity` is fine and list the concrete volume. If it
starts with `ERROR:`, the slider combination can't be built.

You can delete the stray `Mesh Breps` component: the script already outputs meshes.

## 2. Materials

Karamba units: **E and G in kN/cm², strengths in kN/cm², density in kN/m³.**

| Material | Use for | E | G (G12 and G3) | gamma | fc | ft |
|---|---|---|---|---|---|---|
| `printed-roof` | roof shell | 2300 | 958 | `gamma_roof` (≈17.2) | 1.4 | 0 |
| `printed-wall` | walls | 2300 | 958 | `gamma_wall` (≈17.8) | 1.4 | 0 |
| `cast` | ribs, ring beam, crown ring, buttresses | 3280 | 1367 | 24 | 2.0 | 0.29 |

- Use one **Material Properties** component per row. Wire `gamma_roof` / `gamma_wall` from the
  script rather than typing them: they change with `fill` and the layer thicknesses.
- The printed values come from the `material` output (fck 30, kf 0.7). Recompute them if you
  change `fck` or `kf`.
- `ft = 0` for printed layers is deliberate: the layers can't carry tension, so any tension in
  the printed shell shows as over-utilised. That is what you are checking for.
- `gamma = 24` for cast concrete makes the reactions match the script's `weight` output, which is
  your cross-check (step 6). Don't pick Karamba's library C30/37 (gamma 25) unless you accept
  the mismatch.

## 3. Cross sections

Use one **Cross Section** component each. **Karamba cross-section dimensions are in cm**, so
divide the script's mm outputs by 10 (an `A/B` component with B = 10).

| Elem\|Id | Type | Dimensions (mm → ÷10) | Material |
|---|---|---|---|
| `roof` | Shell Const: height `t_roof` (later Shell Var with `t_roof_elems`) | t_roof ≈ 369 | printed-roof |
| `wall` | Shell Const | `t_wall` 400 | printed-wall |
| `but` | Shell Const | `t_but` 400 | cast |
| `ring` | Trapezoid/rectangle | `ring_h` × `ring_b` (300 × 400) | cast |
| `crown` | Trapezoid/rectangle | `crown_h` × `crown_b` (200 × 200) | cast |
| `rib` | Trapezoid/rectangle | `rib_d` × `rib_w` (240 × 160) | cast |

For a rectangle, use the Trapezoid family with the top width equal to the bottom width, and put
the depth into Height. Set each cross-section's `Elem|Id` to the Id in the first column.

Start with **Shell Const + `t_roof`** for the roof. When the model runs, switch to **Shell Var**
with `t_roof_elems` (one branch per roof mesh, one value per face). That gives you the taper from
400 to 320 mm.

## 4. Elements, supports, loads

| Script output | Karamba component | Settings |
|---|---|---|
| `roof_meshes` | Mesh to Shell | Id `roof` |
| `wall_meshes` | Mesh to Shell | Id `wall` |
| `but_meshes` | Mesh to Shell | Id `but` |
| `ring_lines` | Line to Beam | Id `ring` |
| `crown_lines` | Line to Beam | Id `crown` |
| `rib_lines` | Line to Beam | Id `rib`, or `rib_ids` if hips/rings get their own section (then make cross sections for `col`, `hring`, `hip`, `diag`). Empty for `none`, which is fine |
| `supports` | Support | Fixed: all six toggles (Tx Ty Tz Rx Ry Rz) on. Pinned: only Tx Ty Tz |

Loads use the Karamba **Loads** component, switched with its drop-down. Give each one a load case
name (`LCName`):

| Load | Type | Input | LCName |
|---|---|---|---|
| Self weight | Gravity | (0, 0, -1) | `G` |
| Cladding | Mesh Load (const) | Mesh = `roof_meshes`, Vec = `cladding`, global, **not projected** | `G` |
| Wind on roof | Mesh Load | Mesh = `roof_meshes`, Vec = `wind_vecs` (pairs up face by face), global, not projected | `W` |
| Wind on walls | Mesh Load | Mesh = `wall_meshes`, Vec = `wind_walls`, global, not projected | `W` |

The vectors already point the right way (normal to each face, pressure in and suction out), so
don't use local or projected orientation.

The building is symmetric four ways, so `wind_dir = 0` covers 90 / 180 / 270. Run 45° once if
you want a diagonal check.

**Combinations** (Load Case Combinator):
- `ULS1 = 1.35*G + 1.5*W` (strength)
- `ULS2 = 1.0*G + 1.5*W` (least weight against wind: the tension and uplift check)
- `SLS = 1.0*G + 1.0*W` (deflection)

## 5. Assemble and analyse

**Assemble Model**: Elem ← all shells and beams, Support ← supports, Load ← all loads,
CroSec ← all cross sections. The script makes sure shells, ribs and the ring beam share nodes, so
the default merge tolerance works.

**Analyze** (first order) → Model. Look at its `Disp` output (max displacement per load case;
check the units on the output).

## 6. Read the results (do them in this order)

1. **Weight cross-check.** Use **Reaction Forces** and sum the Z component under `G`. It should
   equal `weight` plus cladding: about **2667 / 2940 / 2956 kN** for none / A / B, plus about
   **52 kN** cladding. If it doesn't, a material, density or cross section is wrong. Fix that
   before you trust anything else.
2. **Deflection (SLS).** Use **Model View** with the deformation scale up. Use span/250 = 40 mm
   as the limit; a shell like this should be well under it.
3. **Roof and wall stresses (ULS).** In **Shell View**, render principal stresses (Sig1 / Sig2)
   or utilisation:
   - compression: below fc = **14 MPa** (1.4 kN/cm²) for printed concrete;
   - tension (Sig1 > 0) in printed parts: should be about zero. Find **where** it occurs (crown,
     around the eave, near the buttresses). That is where the printed shell needs the ribs, a ring
     or reinforcement.
4. **Ring beam.** In **Beam View**, show the axial force N on `ring`. Tension there is the roof
   thrust that the solid base carries.
5. **Buttresses.** Look at the horizontal reactions at the buttress bases against the wall bases:
   they show how much thrust the buttresses take.
6. **Ribs.** Show N and M on `rib`: do they actually pick up load compared with the shell?

## 7. Compare A, B and none

Switch the `grid` value list and read the same six results for each. Keep a small table: max
displacement, max compression, max tension in the printed shell, ring tension, and `concrete`.
That table is the argument for the grid you choose.

To optimise (Galapagos / Octopus): genes = sliders (`rib_d`, `leaf_base`, `n_cols`, ...),
fitness = minimise `concrete`, with a penalty when max displacement or utilisation goes over
the limit. Run it once per grid.

## Known simplifications to state in the report

The script header lists them: everything on mid-surfaces and centrelines, the ring beam at the
centroid of the solid base, ribs starting on the ring beam, the footing not modelled (fixed or
pinned at z = 0), and printed layers replaced by an equivalent density. Also: rib beams use
Karamba's default orientation, so ribs that aren't on the fall line aren't exactly square to the
roof. Use **Orientate Beam** with the roof normals if rib bending matters.
