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
| `0.Model` | **Assemble Model**, **Create Linear Element** (→ Line to Beam), **Create Surface Element** (→ Mesh to Shell), (Orientate Elem) |
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
   needed.
3. Open `grasshopper/Pyramide Karamba 10_14_2026.gh`, then **set Karamba's geometry unit to mm**: Grasshopper
   menu bar → **Karamba3D** → **Physical Units** → **Geometry Input Units** → millimetres. Press **F5**, then
   save the `.gh` (the setting is stored in the file).
   **Karamba does NOT follow the Rhino document units.** Its default (`UnitLength = auto` in `karamba.ini`)
   means **metres**, so without this step a 10,000 mm plan becomes 10 km. Symptom: Assemble's **Mass** about
   10⁶ times too big (2.5e11 instead of about 2.9e5 kg). If you edit `karamba.ini` instead, the valid value is
   `mm` (not `Millimeters`), and the menu setting in the `.gh` overrides it.
4. The script component needs **regular** outputs named exactly: `info, roof_meshes, wall_meshes,
   but_meshes, ring_lines, crown_lines, cap_lines, rib_lines, rib_ids, supports, cladding, wind_vecs, wind_walls,
   t_roof, t_wall, t_but, ring_b, ring_h, crown_b, crown_h, rib_w, rib_d, gamma_roof, gamma_wall,
   material, weight, t_roof_elems, concrete, rise, slope, E_roof, G_roof, fc_roof, ft_roof, E_wall, G_wall,
   fc_wall, ft_wall, t_build`. Do **not** use the built-in "standard output"
   (`out`) parameter as `info`: it only carries `print()` text and stays empty.
5. Panel on `info`, press **F5**. With the defaults it must show `grid A: plan 10000 clear ...`,
   `roof 370 thick (30 bead, rib zone 160, lattice 120, 1 outer beads)` and `total 79.7 m3 = 1912 kN`.

### The printed build-up and the "equivalent shell"

Roof, square to the slope, from the room side out (every printed layer is one `bead` wide, 30 by default):
inner bead 30 | rib zone `rib_d` 160 (cavity crossed by the cast ribs) | middle bead 30 | lattice zone
`lattice` 120 (wavy bead + insulation, `fill` 0.25 solid) | `outer_beads` 1 × 30 = **370**. Walls: inner bead
| lattice zone | 1 outer bead = `wall` 400. Nothing else: no cladding load by default (`clad` = 0), the outer
bead is the exposed face.

Only the **skins** carry load (`all_layers` = False): the inner and middle beads in the roof (with the ribs between
them), the inner and outer beads in the wall. The rest is weight. Karamba's shell is a single solid layer, so the
script turns the skins into an **equivalent shell** with the same axial and bending stiffness:

| | Real build-up | Karamba shell (defaults) |
|---|---|---|
| Roof | 370 thick, 120 of it solid | `t_roof` ≈ 330 mm, E × 0.18 (`E_roof`), `gamma_roof` ≈ 8.7 |
| Wall | 400 thick, 145 of it solid | `t_wall` ≈ 642 mm, E × 0.09 (`E_wall`), `gamma_wall` ≈ 5.4 |

So the shell heights, E, G, fc and gamma of the printed materials all come **from the script outputs**, not
typed numbers. Displacements and weight are then right; Karamba's utilisation is right for in-plane stress and on
the safe side for bending. Karamba's raw stress colours are not the real stress in the 30 mm skins.

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
| E | wire **`E_roof`** (≈ 418) | wire **`E_wall`** (≈ 215) | 3280 |
| G12 | wire **`G_roof`** | wire **`G_wall`** | 1367 |
| G13 | wire **`G_roof`** | wire **`G_wall`** | 1367 |
| gamma | wire **`gamma_roof`** | wire **`gamma_wall`** | 24 |
| alphaT | leave | leave | leave |
| ft | wire **`ft_roof`** (0) | wire **`ft_wall`** (0) | 0.29 |
| fc | wire **`fc_roof`** (≈ -0.25, already negative) | wire **`fc_wall`** | **-2.0** |
| S-Hypo | 2 (Rankine) | 2 (Rankine) | 2 (Rankine) |

Where the numbers come from (fck 30 MPa, knock-down kf 0.7): the printed concrete itself has
E = 0.7 × Ecm 32.8 GPa = 23 GPa = 2300 kN/cm², G = E/2.4, fc = 30/1.5 × 0.7 = 14 MPa. The script multiplies E, G and
fc by A / t of the equivalent shell (0.18 roof, 0.09 wall with the defaults), so wire them; they change with
every slider. Cast = C30/37: Ecm 32.8 GPa, fcd 20 MPa, fctm 2.9 MPa. Rankine (maximum principal stress) is the
usual strength criterion for concrete.

`ft = 0` on the printed parts is on purpose: printed layers take no tension, so any tension there shows up
as over-utilised. That is the thing to find. If the utilisation colours come out blank or infinite, type
`0.01` instead of wiring `ft_roof` / `ft_wall`.

`gamma = 24` for cast concrete (not Karamba's library C30/37 at 25) so the reactions match the script's
`weight`; that is the check in step 9.

---

## 3. Cross sections: `3.Cross Section` → **Cross Sections** (place 6)

One multi-component per section; pick the type with the drop-down at the bottom.
Each cross section's **Material** input gets the Material Properties output from step 2.
Leave `Elem|Id` empty: we plug each cross section straight into its element in step 4.

| Name | Drop-down | Size inputs (all in **cm**, from the Division components) | Material |
|---|---|---|---|
| `roof` | **Shell Const** | Height ← `t_roof` ÷ 10 (≈ 33, the equivalent shell) | printed-roof |
| `wall` | **Shell Const** | Height ← `t_wall` ÷ 10 (≈ 58, the equivalent shell) | printed-wall |
| `but` | **Shell Const** | Height ← `t_but` ÷ 10 (40) | cast |
| `ring` | **Trapezoid** | see below | cast |
| `crown` | **Trapezoid** | see below | cast |
| `rib` | **Trapezoid** | see below | cast |

The three Trapezoids, input by input (`←` = wire into; each "÷ 10" is its own Division component, B = 10):

| Cross section | Height ← | Top width ← and bottom width ← (the same Division output into both) |
|---|---|---|
| `ring` | `ring_h` ÷ 10 = 30 | `ring_b` ÷ 10 = 40 |
| `crown` | `crown_h` ÷ 10 = 20 | `crown_b` ÷ 10 = 20 |
| `rib` | `rib_d` ÷ 10 = 16 | `rib_w` ÷ 10 = 16 |

Rule of thumb: Height always takes the `_h` / `_d` output (depth), the widths always take the `_b` / `_w`
output. That makes 6 Division components for these three. Trapezoid with equal top and bottom widths = solid
rectangle. Height is the depth of the section along the beam's local Z axis.

The roof build-up is now constant from eave to crown, so **Shell Const** is all you need. `t_roof_elems` (one
value per element) is still there if a later version varies the thickness again: then use **Shell Var** with
`t_roof_elems` ÷ 10 into **Heights**.

---

## 4. Elements: `0.Model`

In Karamba 3.1 these are multi-components, not separate entries in the `0.Model` list:
- **Mesh to Shell** = place **Create Surface Element (Karamba3D)** (blue surface icon), drop-down at the
  bottom → **Mesh to Shell** (not Mesh to Membrane).
- **Line to Beam** = place **Create Linear Element (Karamba3D)** (blue line icon), drop-down at the bottom →
  **Line to Beam** (not Line to Truss).

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
| Line to Beam 4 | `cap_lines` | `cap` | the **same** `ring` cross section (one cross section can feed two Line to Beams) |

**Buttress caps (`cap_lines`)** are the eave detail D1 in the model: the solid roof base is cast over each buttress
top and hooked bars run down into it, so each buttress is joined to the ring beam along its whole top, not at one
point. They're short beams (2 per buttress, 64 in all) at ring-beam height with the ring beam's section and the
cast material. Turn them off with a `but_cap` input = False to compare. They add about 7,400 kg of concrete
(partly a modelling device: on the real detail the solid base only overlaps the buttress near the wall).

For `grid = none`, `rib_lines` is empty and Line to Beam 3 just outputs nothing; that's fine.
Leave the Options (LDist etc.) at their defaults. The script already puts shells, ribs and the ring beam on
the same nodes, and the default merge distance (5 mm) joins them.

---

## 5. Supports: `1.Support` → **Support** (place 1)

- **Pos|Ind** ← `supports` (148 points at z = 0, under every wall and buttress node).
- Under **Conditions**, six circles `Tx Ty Tz Rx Ry Rz`: the first three are translations, the last three
  rotations. A dot in the circle = fixed. **Fixed: all six dotted** (default for this model). Pinned: only
  Tx Ty Tz.
- Leave Plane, Ct, Cr, Dofs empty. Output **Supp** goes to Assemble Model (step 7).

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
| **Elem** | Mesh to Shell 1, 2, 3 + Line to Beam 1, 2, 3, 4 (their element output) |
| **Support** | Support |
| **Load** | Loads 1, 2, 3, 4 + the Load-Case-Combinator's **Load** output |
| CroSec, Material, Joint, Pts | leave empty (sections are already on the elements) |
| LDist | leave default |

**Flatten the Load input** (right-click Load → *Flatten*; a ↓ icon appears). Otherwise the loads arrive in
two data branches and Assemble builds two models, one without wind. The symptom is an orange Assemble with
*"The following load case is empty and will be ignored: W"*. Check with a panel on **LCNames**: one branch
listing `G, W, ULS1, ULS2, SLS`. If it still shows two branches, flatten Elem and Support too.

Put a panel on its **Info** output. Check the element counts look right (grid A with the defaults: 1300 roof
shell elements plus the wall and buttress elements, and 772 rib beams; the script's `info` gives the numbers for
your sliders) and that there are no warnings.
**Mass** (kg) / 100 ≈ the script's `weight` in kN. Expected Mass with the default sliders (30 bead, lattice 120,
ribs 160 × 160), part by part (kg):

| grid | roof shell | ribs | ring | crown | walls | buttresses | caps | **total** |
|---|---|---|---|---|---|---|---|---|
| A | 49,890 | 18,026 | 11,981 | 490 | 38,364 | 65,126 | 7,373 | **191,249** |
| B | 49,890 | 19,223 | 11,981 | 490 | 38,364 | 65,126 | 7,373 | **192,446** |
| none | 49,890 | 0 | 11,981 | 490 | 38,364 | 65,126 | 7,373 | **173,223** |

With other slider values, compare with `weight` × 100 instead.

If the total is off, the difference usually equals one of these parts: that part is missing or has the wrong
section or density.

---

## 8. Analyse: `6.Algorithms` → **Analyze** (place 1)

- **Model** ← Assemble Model's Model output.
- **LCase**: leave empty, so every load case (`G`, `W`) and combination (`ULS1`, `ULS2`, `SLS`) is computed.
- Outputs: **Model** (analysed), **MaxDisp** (maximum displacement, **cm**, one value per load case in the
  LCNames order G, W, ULS1, ULS2, SLS), **Force** (kN) and **Energy**. Panel on **MaxDisp**; the SLS value
  must stay under 4 cm.

---

## 9. Results: `7.Results`

### a) Weight cross-check first: **Reaction Forces**

- **Model** ← Analyze's Model. **LCase** ← panel `G`.
- Panel on **SumRF**: the Z component should be about the script's `weight` (+ `clad` × roof area if you set
  one): with the default sliders **1912 kN** for grid A (none: 1732, B: 1924). If it isn't, a material gamma or cross section is wrong; fix that
  before reading anything else.
- Then with LCase `ULS1` / `ULS2`: **RF** gives each support's reaction. The horizontal reactions at the
  buttress base points against the wall base points show how much thrust the buttresses take.

### Seeing the results in the viewport (the coloured model)

Chain **ModelView → ShellView → BeamView**, each one's **Model** input from the previous one's **Model**
output. Turn **preview off** (select, **Ctrl+Q**) on the Python script and on every Karamba component before
Analyse, or their meshes cover the colours. Leave preview on only for the view components.

### b) Picture of the deformation: **ModelView**

- **Model** ← Analyse's Model. **LCase** ← `SLS` (or `ULS1` for the stress pictures below).
- In its **Display** submenu turn up the displacement scale slider to exaggerate the deformation.
- **DefMax** = maximum displacement in **cm**. Limit: span/250 = 10000/250 = 40 mm = **4 cm**.

### c) Stresses in the roof and walls: **ShellView** (after ModelView)

- **Model** ← ModelView's Model output; set ModelView's LCase to `ULS1`, then `ULS2`.
- **Render Settings** submenu, one at a time:
  - **Princ. Stress 2**: compression. Must stay below 14 MPa in the printed parts.
  - **Princ. Stress 1**: tension. Should be about zero in the printed parts. Note **where** it isn't
    (crown, eave, around the buttresses): that is where the shell needs the ribs, a ring or reinforcement.
  - **Stress/Strength Ratio**: utilisation per face. Negative values mean compression governs.
  - **Position of Results** slider: 0 = middle of the thickness, 1 = top face, -1 = bottom face. Check
    1 and -1 too: bending shows at the faces.
- **Colour bar:** `9.Utilities` → **Legend (Karamba3D)**: wire ShellView's **Legend C** (colours) and
  **Legend T** (values) into it. It draws the bar in the viewport corner and follows the Render Setting.
- For numbers instead of colours: **Utilization of Elements** (drop-down **Shell**), Model ← Analyse,
  Elems|Ids ← `roof`, LCase ← `ULS1`.

### d) Forces in ring beam, crown ring and ribs: **BeamView** + **Beam Forces**

- **BeamView** after ShellView (Model ← ShellView's Model).
  - **Display** submenu → **Axial Stress** (or **Stress/Strength Ratio**) colours the beams. This is the
    readable option with hundreds of short rib segments. A second **Legend (Karamba3D)** on BeamView's Legend C / T
    gives its colour bar.
  - **Section Forces** submenu → **Nx** draws axial-force diagrams. Lower *Scale [kN] to [m]* to about
    0.01 first: at the default 0.5 the diagrams float metres away from the beams as loose dashes.
- **Beam Forces**: Model ← Analyze, **Beams|Ids** ← `ring` (then `crown`, `col`, `hring`, `hip`, `diag`),
  LCase ← `ULS1`. Outputs **N** (axial, kN; positive = tension), **V**, **M**.
  - `ring`: the tension the solid roof base carries.
  - `crown`: should be in compression.
  - ribs: do they actually pick up load compared with the shell?

---

## 10a. Without structural walls (roof + ring beam + buttresses)

Add an input **`walls`** to the script component (type hint **bool**) and wire a **Boolean Toggle**
(`Params` → `Input`). Set it to **False**:

- `wall_meshes` and `wind_walls` come out **empty**. The wall Mesh to Shell and the wall-wind Loads component turn
  orange ("failed to collect data"). That's expected and harmless: they just add nothing to the model.
- `supports` moves under the buttresses (92 points instead of 148). The ring beam now sits only on the
  buttresses, each one joined to it at its top inner corner.
- `info` says `NO structural walls ...`, and `weight` drops by the walls (grid A with ribs 100 × 200:
  Mass ≈ 149,112 kg instead of 187,476).
- Nothing to rewire. Toggle back to **True** for the full model.

Compare MaxDisp, the ring beam's N and the buttress reactions with and without walls. If Analyse reports the
model as unstable (singular / kinematic), tell Claude: the buttress-to-ring connection is a single node.

## 10b. Without a ring beam, buttresses under the ribs

Two more toggles (add inputs `ring` and `but_on_ribs`, type hint **bool**, each with a **Boolean Toggle**):

- **`ring` = False**: no ring beam, so no solid roof base. `ring_lines` comes out empty, and its Line to Beam turns
  orange, which is harmless. With walls the roof sits straight on the wall top; without walls it lands only where
  ribs meet buttresses. The buttress caps stay, so each rib foot is still cast into its buttress.
- **`but_on_ribs` = True**: one buttress under every rib foot instead of every ~1.5 m. Grid A: `n_cols` bays per
  side (set `n_cols` = **6** for ribs about every 1.7 m). Grid B: `n_diamonds` bays. The plain shell has no ribs
  and keeps `but_spacing`. Every corner gets two buttresses, one per face, like an L. So 6 bays gives 4 × 7 = 28
  buttresses: 20 under the ribs and 8 at the corners.
- **`ring` = False with `walls` = False** only works with `but_on_ribs` = True. Otherwise the buttresses wouldn't
  touch the roof, and `info` says so.

A useful set of runs (grid A, `n_cols` = 6, `walls` = False):

| Run | `ring` | `but_on_ribs` | What it shows |
|---|---|---|---|
| 1 | True | False | today's system: ring beam on buttresses every ~1.5 m |
| 2 | True | True | same ring, buttresses moved under the ribs |
| 3 | False | True | no ring: each rib lands on its own buttress |

Compare MaxDisp (SLS), the shell colours at the eave between the rib feet, and the horizontal buttress reactions.

## 10c. Foundation (footing) and tipping

Add an input **`footing`** (bool, Boolean Toggle = True) and sliders **`foot_w`** (width, 800), **`foot_h`** (depth,
500) and **`foot_ext`** (how far the buttress footing reaches beyond the buttress, 300). Add the outputs
**`foot_lines`**, **`foot_b`**, **`foot_h`**.

- The script adds a **strip footing on the wall line** at z = 0 joining every buttress foot, and a **footing beam
  under each buttress**, `foot_ext` longer than it. The supports move under the footing (every footing node).
- Karamba: one more **Cross Sections** (Trapezoid: Height ← `foot_h` ÷ 10, both widths ← `foot_b` ÷ 10, Mat ← `cast`)
  and one more **Line to Beam** (Line ← `foot_lines`, Id `footing`, CroSec ← that section) into Assemble's Elem.
- Support: **Tx Ty Tz only** (pinned) for the tipping check.

**Reading tipping:** Reaction Forces (LCase `ULS1`) → RF → Deconstruct Vector → **Z** → **Bounds** (flatten N).
The lowest value is the worst support: **negative = the ground would have to pull it down = that point lifts
(tipping)**; the number is the missing hold-down in kN (10 kN ≈ 1 t). Aim for **≥ 0**. The highest value is the
most a single point presses on the soil. With walls off, every support is under the buttresses / footing.
ULS1 governs here: the roof's own weight makes the push that tips the buttresses.

## 10. Compare A, B and none

Switch the `grid` value list and read the same results each time. Keep this table; it is the argument for the
grid you choose:

| grid | concrete m³ | SumRF Z under G (kN) | max displ. SLS (cm) | max compression (MPa) | max tension in printed shell (MPa) | ring N (kN) |
|---|---|---|---|---|---|---|
| none | | | | | | |
| A | | | | | | |
| B | | | | | | |

**Optimising** (Galapagos, `Params` tab → `Util`; Octopus for several objectives): the genes are sliders
on script inputs (`rib_d`, `bead`, `lattice`, `n_cols`, ...). Fitness: minimise `concrete`, plus a penalty when the
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
| Mass about 10⁶ too big (2.5e11 kg) | Karamba geometry unit is metres: Karamba3D menu → Physical Units → Geometry Input Units → mm, F5 |
| Assemble warns about unconnected parts | Karamba geometry unit not mm, or LDist changed |
| Orange Assemble: "load case W is empty" | Load input not flattened (two models); flatten it |
| Mass about 10% short of `weight` × 100 | Trapezoids with no UpperWidth / LowerWidth wired: Karamba falls back to a small default width (about 5 cm), so ring, crown and ribs are far too thin and too weak. Wire both widths on all three |
| Walls about 2,300 kg light | printed-wall material got `gamma_roof` instead of `gamma_wall` |
| SumRF ≠ weight | gamma wrong (kN/m³), or Height given in mm instead of cm |
| Huge displacements | E in the wrong units (must be kN/cm²), or supports not all six fixed |
| Utilisation blank / infinite | `ft = 0`; use 0.01 |
