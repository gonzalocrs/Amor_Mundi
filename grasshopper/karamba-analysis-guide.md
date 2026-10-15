# Karamba analysis: step-by-step wiring

How to go from the script component (`scripts/karamba_model.py`) in `Pyramide Karamba 10_14_2026.gh` to
analysis results. Every Karamba component is listed with **where it is on the ribbon**, **how to set it**
and **which wire goes into which input**.

Checked against Karamba3D **3.1.60921** (installed on Gonzalo's PC) and the official manual
(manual.karamba3d.com, chapter 3). If an input is named slightly differently in your version, hover over it:
Karamba shows the full name and the **units** in the tooltip.

---

## 0. Where things are

The **Karamba3D** tab in Grasshopper has these groups (left to right):

| Group | What we take from it |
|---|---|
| `0.Model` | **Assemble Model**, **Line to Beam**, **Mesh to Shell**, (Orientate Element) |
| `1.Support` | **Support** |
| `2.Load` | **Loads**, **Load-Case-Combinator** |
| `3.Cross Section` | **Cross Sections** |
| `4.Joint` | nothing (all connections stay rigid) |
| `5.Material` | **Material Properties** |
| `6.Algorithms` | **Analyze** |
| `7.Results` | **ModelView**, **ShellView**, **BeamView**, **Reaction Forces**, **Beam Forces**, **Utilization of Elements** |
| `8.Export` | nothing |
| `9.Utilities` | nothing (delete the `Mesh Breps` that is on the canvas: the script already makes the meshes) |

**Fastest way to place any component:** double-click on an empty part of the canvas, type its name
(e.g. `Mesh to Shell`), press Enter. Karamba components show a small K3D logo.

Several Karamba components are **multi-components**: one component with a **drop-down list at the bottom**
that switches what it does (Loads, Cross Sections, Utilization of Elements). Click the bar at the bottom
of the component to change it.

**Several wires into one input:** hold **Shift** while you drag the second, third... wire into the same input.

### The whole chain

```
                      ┌─► Material Properties ×3 ─┐
script outputs ───────┤                           ▼
                      ├─► Cross Sections ×6 ──► Mesh to Shell ×3 ─┐
                      │                     └─► Line to Beam ×3 ──┤
                      ├─► Support ────────────────────────────────┤
                      └─► Loads ×4 ──┐                            │
                Load-Case-Combinator ┴────────────────────────────┴─► Assemble Model ─► Analyze ─► ModelView ─► ShellView ─► BeamView
                                                                                           │
                                                                       Reaction Forces, Beam Forces, Utilization of Elements
```

---

## 1. Rhino and Python setup (once per PC)

1. **Rhino 8**, **Karamba3D 3.1** (`PackageManager` → Karamba3D → install → restart Rhino), and a licence
   (trial or educational from karamba3d.com; the model is far over the free version's limits).
2. New Rhino file in **millimetres** (template *Large Objects – Millimeters*). The `.3dm` in the repo is not
   needed. Karamba reads the document units, so it knows the script's numbers are mm.
3. Open `grasshopper/Pyramide Karamba 10_14_2026.gh`.
4. The script component needs **regular** outputs named exactly: `info, roof_meshes, wall_meshes,
   but_meshes, ring_lines, crown_lines, rib_lines, rib_ids, supports, cladding, wind_vecs, wind_walls,
   t_roof, t_wall, t_but, ring_b, ring_h, crown_b, crown_h, rib_w, rib_d, gamma_roof, gamma_wall,
   material, weight, t_roof_elems, concrete, rise, slope`. Do **not** use the built-in "standard output"
   (`out`) parameter as `info`: it only carries `print()` text and stays empty.
5. Panel on `info`, press **F5**. It must show `grid A: plan 10000 clear ...` and `total 122.5 m3 = 2940 kN`.

### Unit converters you will need (standard Grasshopper)

Karamba wants **cross-section sizes in cm**; the script gives **mm**. Make one converter per value:

- **Division** (`Maths` tab → `Operators` group → **Division**, or double-click and type `Division`).
  A = script output (e.g. `t_roof`), B = **10** (right-click B → *Set Number* → 10). Output = cm.

You need them for: `t_roof`, `t_wall`, `t_but`, `ring_b`, `ring_h`, `crown_b`, `crown_h`, `rib_w`, `rib_d`
(and `t_roof_elems` if you use the varying thickness in step 3).

---

## 2. Materials: `5.Material` → **Material Properties** (place 3)

Set the drop-down at the bottom to **Isotropic**. Type values with a **Panel** or **Number** into each input,
or right-click the input → *Set Number*.

Units (hover to confirm): `E`, `G12`, `G13`, `ft`, `fc` in **kN/cm²**; `gamma` in **kN/m³**.
**`fc` is entered as a negative number** in Karamba.

| Input | `printed-roof` | `printed-wall` | `cast` |
|---|---|---|---|
| Family | `Concrete` | `Concrete` | `Concrete` |
| Name | `printed-roof` | `printed-wall` | `cast` |
| Elem\|Id | *leave empty* | *leave empty* | *leave empty* |
| E | 2300 | 2300 | 3280 |
| G12 | 958 | 958 | 1367 |
| G13 | 958 | 958 | 1367 |
| gamma | wire **`gamma_roof`** | wire **`gamma_wall`** | 24 |
| alphaT | leave | leave | leave |
| ft | 0 | 0 | 0.29 |
| fc | **-1.4** | **-1.4** | **-2.0** |
| S-Hypo | 2 (Rankine) | 2 (Rankine) | 2 (Rankine) |

Where the numbers come from (the script's `material` output, fck 30 MPa, knock-down kf 0.7):
printed E = 0.7 × Ecm 32.8 GPa = 23 GPa = 2300 kN/cm², G = E/2.4, fc = 30/1.5 × 0.7 = 14 MPa.
Cast = C30/37: Ecm 32.8 GPa, fcd 20 MPa, fctm 2.9 MPa. Rankine (maximum principal stress) is the
usual strength criterion for concrete.

`ft = 0` on the printed parts is on purpose: printed layers take no tension, so any tension there shows up
as over-utilised. That is the thing to find. If the utilisation colours come out blank or infinite, use
`ft = 0.01` instead.

`gamma = 24` for cast concrete (not Karamba's library C30/37 at 25) so the reactions match the script's
`weight`; that is the check in step 9.

---

## 3. Cross sections: `3.Cross Section` → **Cross Sections** (place 6)

One multi-component per section; pick the type with the drop-down at the bottom.
Each cross section's **Material** input gets the Material Properties output from step 2.
Leave `Elem|Id` empty: we plug each cross section straight into its element in step 4.

| Name | Drop-down | Size inputs (all in **cm**, from the Division components) | Material |
|---|---|---|---|
| `roof` | **Shell Const** | Height ← `t_roof` ÷ 10 (≈ 36.9) | printed-roof |
| `wall` | **Shell Const** | Height ← `t_wall` ÷ 10 (40) | printed-wall |
| `but` | **Shell Const** | Height ← `t_but` ÷ 10 (40) | cast |
| `ring` | **Trapezoid** | Height ← `ring_h` ÷ 10 (30); both widths (top and bottom) ← `ring_b` ÷ 10 (40) | cast |
| `crown` | **Trapezoid** | Height ← `crown_h` ÷ 10 (20); both widths ← `crown_b` ÷ 10 (20) | cast |
| `rib` | **Trapezoid** | Height ← `rib_d` ÷ 10 (24); both widths ← `rib_w` ÷ 10 (16) | cast |

Trapezoid with equal top and bottom widths = solid rectangle. Height is the depth of the section along the
beam's local Z axis.

**Later, for the tapering roof (400 → 320 mm):** change the `roof` cross section to **Shell Var** and feed
`t_roof_elems` ÷ 10 into **Heights** (one branch per roof face, one value per mesh face). Its output should
then hold 4 cross sections, one per roof face. Start with Shell Const until everything runs.

---

## 4. Elements: `0.Model`

### Mesh to Shell (place 3)

| Component | Mesh ← | Id (type in a panel) | CroSec ← |
|---|---|---|---|
| Mesh to Shell 1 | `roof_meshes` | `roof` | `roof` cross section |
| Mesh to Shell 2 | `wall_meshes` | `wall` | `wall` cross section |
| Mesh to Shell 3 | `but_meshes` | `but` | `but` cross section |

### Line to Beam (place 3)

| Component | Line ← | Id | CroSec ← |
|---|---|---|---|
| Line to Beam 1 | `ring_lines` | `ring` | `ring` cross section |
| Line to Beam 2 | `crown_lines` | `crown` | `crown` cross section |
| Line to Beam 3 | `rib_lines` | wire **`rib_ids`** (gives `col` / `hring` / `hip` for A, `diag` / `hip` for B) | `rib` cross section |

For `grid = none`, `rib_lines` is empty and Line to Beam 3 just outputs nothing; that's fine.
Leave the Options (LDist etc.) at their defaults. The script already puts shells, ribs and the ring beam on
the same nodes, and the default merge distance (5 mm) joins them.

---

## 5. Supports: `1.Support` → **Support** (place 1)

- **Pt** ← `supports` (148 points at z = 0, under every wall and buttress node).
- Six small circles on the component: the first three are translations X, Y, Z, the last three rotations.
  Click to fill. **Fixed: all six filled** (default for this model). Pinned: only the first three.

---

## 6. Loads: `2.Load` → **Loads** (place 4)

Each one is the **Loads** multi-component with its drop-down set as below. Type the load case name into
**LCase** with a panel.

| # | Drop-down | Inputs | Orientation (right-click menu or radio buttons on the component) | LCase |
|---|---|---|---|---|
| 1 | **Gravity** | Vec: leave default (0, 0, -1) | — | `G` |
| 2 | **MeshLoad Const** | Mesh ← `roof_meshes`, Vec ← `cladding` | **global** (not *global proj.*) | `G` |
| 3 | **MeshLoad Const** | Mesh ← `roof_meshes`, Vec ← `wind_vecs` | **global** | `W` |
| 4 | **MeshLoad Const** | Mesh ← `wall_meshes`, Vec ← `wind_walls` | **global** | `W` |

- Gravity acts on everything that has a `gamma`, so it covers all the concrete from step 2.
- On the MeshLoad components, keep the **Point loads** generation ticked and **Line loads** off, so the load
  goes onto the shell nodes rather than being turned into line loads on the ribs.
- `wind_vecs` and `wind_walls` each hold 4 vectors in the same order as the 4 meshes, so Grasshopper pairs
  face 1 with vector 1 and so on. They already point normal to each face (pressure inwards, suction outwards),
  which is why the orientation is **global**: don't let Karamba re-orient or project them.
- The building is symmetric four ways, so `wind_dir = 0` stands for all four directions.

### Load-Case-Combinator (`2.Load`, place 1)

Feed a **Panel** with these three lines (one rule per line) into **Rules**:

```
ULS1 = 1.35 * G + 1.5 * W
ULS2 = 1.0 * G + 1.5 * W
SLS = 1.0 * G + 1.0 * W
```

Hover the **Rules** input to check the syntax in your version. Check the **Load** output in a panel: it should
list the three combinations. `ULS1` is for strength, `ULS2` for the tension and uplift check (the least weight
against the wind), and `SLS` for deflection.

---

## 7. Assemble: `0.Model` → **Assemble Model** (place 1)

| Input | Wires (Shift-drag to add several) |
|---|---|
| **Elem** | Mesh to Shell 1, 2, 3 + Line to Beam 1, 2, 3 (their element output) |
| **Support** | Support |
| **Load** | Loads 1, 2, 3, 4 + the Load-Case-Combinator's **Load** output |
| CroSec, Material, Joint, Pts | leave empty (sections are already on the elements) |
| LDist | leave default |

Put a panel on its **Info** output. Check the element counts look right (grid A: 1380 roof shell elements plus
the wall and buttress elements, and 812 rib beams) and that there are no warnings.
**Mass** (kg) / 100 ≈ the script's `weight` in kN.

---

## 8. Analyse: `6.Algorithms` → **Analyze** (place 1)

- **Model** ← Assemble Model's Model output.
- **LoadCases**: leave empty, so every load case (`G`, `W`) and combination (`ULS1`, `ULS2`, `SLS`) is computed.
- Outputs: the analysed **Model**, the maximum displacement (**cm**, one value per load case), the maximum
  force (kN) and the deformation energy. Panel on the displacement output.

---

## 9. Results: `7.Results`

### a) Weight cross-check first: **Reaction Forces**

- **Model** ← Analyze's Model. **LCase** ← panel `G`.
- Panel on **SumRF**: the Z component should be about **2940 + 52 = 2992 kN** for grid A
  (none: 2667 + 52, B: 2956 + 52). If it isn't, a material gamma or cross section is wrong; fix that
  before reading anything else.
- Then with LCase `ULS1` / `ULS2`: **RF** gives each support's reaction. The horizontal reactions at the
  buttress base points against the wall base points show how much thrust the buttresses take.

### b) Picture of the deformation: **ModelView**

- **Model** ← Analyze's Model. **LCase** ← `SLS`.
- In its **Display** submenu turn up the displacement scale slider to exaggerate the deformation.
- **DefMax** = maximum displacement in **cm**. Limit: span/250 = 10000/250 = 40 mm = **4 cm**.

### c) Stresses in the roof and walls: **ShellView** (after ModelView)

- **Model** ← ModelView's Model output; set ModelView's LCase to `ULS1`, then `ULS2`.
- **Render Settings** submenu, one at a time:
  - **Princ. Stress 2**: compression. Must stay below 14 MPa in the printed parts.
  - **Princ. Stress 1**: tension. Should be about zero in the printed parts. Note **where** it isn't
    (crown, eave, around the buttresses): that is where the shell needs the ribs, a ring or reinforcement.
  - **Utilization**: material strength ÷ stress, per face. Negative values mean compression governs.
  - **Position of results** slider: 1 = top face, -1 = bottom face. Check both.
- For numbers instead of colours: **Utilization of Elements** (drop-down **Shell**), Model ← Analyze,
  Elems|Ids ← `roof`, LCase ← `ULS1`.

### d) Forces in ring beam, crown ring and ribs: **BeamView** + **Beam Forces**

- **BeamView** after ShellView (Model ← ShellView's Model) to show force diagrams on the beams.
- **Beam Forces**: Model ← Analyze, **Beams|Ids** ← `ring` (then `crown`, `col`, `hring`, `hip`, `diag`),
  LCase ← `ULS1`. Outputs **N** (axial, kN; positive = tension), **V**, **M**.
  - `ring`: the tension the solid roof base carries.
  - `crown`: should be in compression.
  - ribs: do they actually pick up load compared with the shell?

---

## 10. Compare A, B and none

Switch the `grid` value list and read the same results each time. Keep this table; it is the argument for the
grid you choose:

| grid | concrete m³ | SumRF Z under G (kN) | max displ. SLS (cm) | max compression (MPa) | max tension in printed shell (MPa) | ring N (kN) |
|---|---|---|---|---|---|---|
| none | | | | | | |
| A | | | | | | |
| B | | | | | | |

**Optimising** (Galapagos, `Params` tab → `Util`; Octopus for several objectives): the genes are sliders
on script inputs (`rib_d`, `leaf_base`, `n_cols`, ...). Fitness: minimise `concrete`, plus a penalty when the
maximum displacement or utilisation goes over the limit. Run it once per grid.

---

## Known simplifications (state them in the report)

All elements on mid-surfaces and centrelines. The ring beam is at the centroid of the solid base, and the
ribs start on the ring beam. The footing isn't modelled (fixed or pinned at z = 0). The printed hollow layers
are replaced by an equivalent density. The rib beams use Karamba's default orientation, so ribs off the fall
line aren't exactly square to the roof; **Orientate Element** (`0.Model`) with the roof normals fixes that if
rib bending matters. The full list is at the top of `scripts/karamba_model.py`.

## Troubleshooting

| Symptom | Cause |
|---|---|
| `info` empty | it's the standard-output parameter; add a normal output named `info` |
| `info` says `ERROR: ...` | that slider combination can't be built; the message says why |
| Assemble warns about unconnected parts | Rhino document not in mm, or LDist changed |
| SumRF ≠ weight | gamma wrong (kN/m³), or Height given in mm instead of cm |
| Huge displacements | E in the wrong units (must be kN/cm²), or supports not all six fixed |
| Utilisation blank / infinite | `ft = 0`; use 0.01 |
