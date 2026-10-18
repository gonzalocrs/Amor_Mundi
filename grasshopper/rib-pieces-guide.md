# Rib pieces: printed formwork for the Karamba rib grid, and into Revit

`scripts/rib_pieces.py` cuts the printed roof into pieces that leave an open channel wherever the Karamba model has a
rib. You stack the pieces, drop the bars into the channels and pour, so the channels become the cast columns, hips,
horizontal rings and crown ring. Everything comes from the same rib lines that go into Karamba, so the pieces, the
analysis and the Revit model can't drift apart.

## What the pieces are

- **Course joints are square to the slope.** Every piece prints upright (zero lean) and is rotated into place.
  - With horizontal courses on the 53° roof, the printed walls would lean 37° from vertical, and
    `cork_house_roof.py` already rates anything over 30° RED.
  - The force running down the face would also hit each horizontal bed joint 37° off square. That puts shear of
    tan 37° = 0.75 × the compression on the joint, against about 0.4 friction for a mortar joint (EN 1996-1-1 §3.6.2).
    On a joint square to the slope the membrane force is pure compression.
  - The precedent is Striatus (Block Research Group ETH, ZHCODE, incremental3D, Venice 2021): printed concrete blocks
    whose print layers run square to the force.
- **Column channels run up the slope,** so in the printer they are near-vertical tubes inside the piece.
- **Horizontal rings and the crown ring** are open troughs along the top of a course: the course joint is put at the
  top of every ring.
- **Hips:** each corner is two half pieces mitred on the hip. The hip channel straddles the mitre, so the cast hip rib
  covers that joint.
- **Joints between pieces** stay at least 210 mm (7 beads) clear of every channel and are staggered from the course
  below.

Build-up square to the slope, room side out (the same as the Karamba model and the drawing set): inner bead (30) |
rib zone (160: zig-zag webs + channels) | middle bead (30) | lattice zone (120: zig-zag web) | outer bead (30) = 370.

## Grasshopper

1. Place a **Python 3 Script** component next to the Karamba script component and paste `scripts/rib_pieces.py`.
2. Add inputs (right-click the component → zoom in → **+**), named exactly:
   - `rib_lines` and `rib_ids`: wire them from the Karamba script's outputs with the same names. Set both to
     **List Access** (right-click the input → List Access).
   - The plan, height and build-up sliders you already use for Karamba, with the same names: `clear`, `wall`,
     `wall_h`, `base_h`, `rise`, `opening`, `bead`, `lattice`, `rib_w`, `rib_d`, `crown_b`. Wire the same sliders
     into both components so they always agree.
   - Optional: `course_H` (450, along the slope), `piece_min` (900), `piece_max` (1500), `hip_L` (500), `web_sp`
     (600), `wave` (300), `layer_H` (10), `speed` (100), `min_layer_t` (30), `seed`, `print_paths` (Boolean Toggle),
     `solids` (Boolean Toggle), `piece` (Panel with a piece id).
3. Add outputs: `blocks`, `ids`, `tags`, `cutlist`, `ribs`, `rib_names`, `rib_axes`, `toolpaths`, `beads`,
   `to_print`, `check`, `piece_paths`, `piece_beads`, `piece_check`, `info`.
4. Read `info` first. It lists the courses, the pieces, the printed weight and the warnings.

`print_paths` = True builds every print layer of every piece (slow: leave it off while you move sliders). Then:

- `beads` shows the printed result in place.
- `check` lists every piece rated AMBER or RED. RED "layer only N s" means a piece too small to print alone: print it
  in the same layer cycle as other pieces so each layer has time to stiffen.
- `piece`: type an id from `ids` into a Panel. `piece_paths` gives that piece's layers on the print bed. Wire them into
  SaladSlicer as before: **Join Open Contours → Curve Slicer → Program Generator**.

Piece ids read `M1-S-C05-03`: module, face (E +x, N +y, W −x, S −y), course from the eave, piece along the face
(H1 and H2 = the two hip pieces).

## Revit (Rhino.Inside.Revit)

Use the same route as the ring beams: the **Module Origin marker** gives the plane the module sits on in Revit.

1. In Revit, check the status bar shows the active workset **Structure** before you start. Rhino.Inside puts new
   elements on the active workset.
2. In Grasshopper, find the plane coming out of **Element Location** of the Module Origin marker (the one the ring
   beams use).
3. Place an **Orient** component (double-click the canvas, type `Orient`):
   - Geometry ← `blocks`
   - A (reference plane) ← a **XY Plane** component (the module centre at 0,0,0)
   - B (target plane) ← the marker's plane
4. Place a second **Orient** the same way for `ribs`.
5. Place **Add DirectShape** (double-click the canvas, type `Add DirectShape`). Right-click it and untick **Enable**
   so it doesn't write to Revit while you wire it.
   - Geometry ← the oriented `blocks`
   - Name ← `ids`
   - Category ← a **Model Categories** picker set to **Roofs** (if Revit refuses that category for a
     DirectShape, use **Generic Models**)
6. Place a second **Add DirectShape** for the cast concrete:
   - Geometry ← the oriented `ribs`
   - Name ← `rib_names`
   - Category ← **Structural Framing**
7. Tick **Enable** on both components. Check the result in `{3D - gc3139}`, then **Synchronize with Central**.

DirectShapes keep the exact printed and cast geometry for plans and sections. They are not analytical members: the
analysis stays in Karamba.

## Self-test

`python scripts/rib_pieces.py` builds grid A (n_cols 4 and 10) and grid B from `karamba_model.py`, prints the summary
and checks every print layer for beads printed twice.
