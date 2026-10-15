# Pyramid roof: 3D-printed concrete

GSAPP, Semester 5. A corbelled pyramid roof after the **Cork House** (Eton, 2019), rebuilt as
hollow, lapped pieces for **3D concrete printing**, sliced to printer programs with
[SaladSlicer](https://github.com/3DCP-TUe/SaladSlicer).

## What's in here

| Path | What it is |
|---|---|
| `scripts/cork_house_roof.py` | Main script: roof pieces, print paths, bead preview, printability check |
| `scripts/concrete_slicer.py` | General slicer: turns any closed geometry into printed-bead geometry (visual only) |
| `grasshopper/Pyramide 10_1_2026.gh` | The Grasshopper definition (scripts pasted into Py3 components + SaladSlicer chain) |
| `rhino/10_1_2026.3dm` | The Rhino model (stored with Git LFS) |
| `scripts/karamba_model.py` | Parametric Karamba3D model, roof grid A, B or none: roof/wall/buttress shells, rib beams, solid roof-base ring, crown ring, supports, wind and cladding loads (see "Karamba model" below) |
| `preview/karamba-preview.html` | Interactive 3D view of the Karamba model (plain shell, grid A, grid B), open in a browser. Rebuild it with `python preview/build_preview.py` after changing the script |
| `details/set/VV_date_label/` | **The drawing sets, one folder per version** (`01_…_80mm-layers`, `02_…_30mm-beads`, `03_…_no-outside-insulation`, …; the highest number is the latest). Older sets are kept, never overwritten, so changes can be compared. |
| `details/set/VV_…/pyramid-roof-drawing-set.pdf` | **The drawing set**, 10 A3 sheets: 01 floor plan, 02/03 floor plan with roof grid A/B, 04/05 section A-A grid A/B, 06/07 roof plan cut grid A/B, 08/09 roof-grid elevations A/B, 10 eave detail D1. One PDF per sheet next to it. |
| `details/set/VV_…/cad/pyramid-roof-drawing-set.dxf` | **The whole set in one CAD file**: the 10 sheets side by side in model space (1:1 in mm, labelled), and one A3 layout per sheet (`01 floor-plan` … `10 detail-D1-eave`), each with its viewport at the sheet scale. |
| `details/set/VV_…/cad/NN-*.dxf` | The same 10 sheets as one CAD file each: model space 1:1 in mm, a paper-space layout **A3 sheet** with a viewport at the sheet scale (plot at 1:1), title block and legend in paper space, real DIMENSION entities (style `PYR-1-50` / `PYR-1-10`), hatches, named layers. All text is Arial (`Standard` style = `arial.ttf`), so CAD doesn't substitute a font. |
| `details/make_set.py` | Builds the whole set (PDFs + DXFs): `pip install cairosvg ezdxf shapely`, then `python details/make_set.py "what changed"`: writes a new version folder in `details/set/`. Without Cairo (Windows) the PDFs are printed with headless Microsoft Edge |
| `details/pyramid_drawings.py`, `roof_grid.py`, `roof_slice.py`, `cad_export.py` | The drawing definitions (geometry, plan, section, D1, roof grids, roof cut) and the DXF writer used by `make_set.py` |

The input/output list for each script is at the top of each `.py` file.

## Setup

1. **Rhino 8** (the scripts run in the Python 3 Script component; GhPython in Rhino 7 should also work).
2. **SaladSlicer**: in Rhino type `PackageManager`, search *SaladSlicer*, install, restart Rhino.
3. Open `rhino/10_1_2026.3dm`, then `grasshopper/Pyramide 10_1_2026.gh`.

## How the definition is wired

```
Rec (rectangles) ──► roof Py3 (cork_house_roof.py)
                       piece_paths ──► Join Open Contours ──► Curve Slicer ──► Program Generator ──► Panel (program)
                                       (T = Linear)            (SO)              ▲
                                                               Printer Settings ─┘ (first in O)
```

- Type a piece ID (e.g. `R0-C3-W-02`) into the panel wired to the `piece` input; `ids` lists all IDs.
- `print_paths` must be **True** for toolpaths, beads and the check.
- `check` lists every piece rated **AMBER** or **RED** (layer time, lap stubs, sharp corners, tiny segments).
- Units: millimetres.

## Working together

- **The `.py` files are the source of truth.** When you change a script, edit the `.py` here,
  paste it into the Py3 component, and commit both the `.py` and the `.gh`.
- **`.gh` and `.3dm` can't be merged.** If you both edit the same one, one person's changes get
  lost. Say in chat who's working on which file before you start.
- **Always pull before you start working** (GitHub Desktop: *Fetch origin*, then *Pull origin*),
  and push when you stop.
- Printer programs (`.mpf`, `.gcode`) aren't committed. Regenerate them from Grasshopper.
- The Rhino model uses **Git LFS**. GitHub's free LFS storage is limited, and every committed
  version of the 135 MB model counts against it. Commit the `.3dm` only when the model has
  really changed.

## Credits

SaladSlicer © 3D Concrete Printing Research Group, TU Eindhoven, GPL-3.0. Cite:
Deetman, Bos, Ferguson, Versteege, *Salad Slicer: An open-source slicer toolkit for 3D concrete printing*, Zenodo, doi:10.5281/zenodo.7818240.

## Karamba model

`scripts/karamba_model.py` (Py3 Script component, millimetres). The `grid` input picks the roof:
**A** (ruled-surface columns, sheet 08), **B** (diamond lattice, sheet 09) or **none** (plain shell, the baseline).
All three share the same shell, walls and buttresses, so the results compare like for like. The roof mesh follows
the ribs, so each rib is a chain of beams on shell nodes.
Run `python scripts/karamba_model.py` to print the three variants and check that everything connects.

### Parameters

Every dimension is an optional input: add an input to the component named exactly like the parameter and wire a
slider to it. Inputs you leave out keep the drawing value. They work the same for A, B and none.

| Group | Inputs (default) |
|---|---|
| Plan and heights | `clear` (10000), `wall` (400), `wall_h` (2500), `base_h` (300, solid roof base = ring beam depth), `rise` (6000), `slope` (deg; if connected it replaces `rise`), `opening` (1000) |
| Roof thickness, square to the slope | `leaf_base` (160) → `leaf_crown` (80), `lattice` (160), `skin` (80), `fill` (0.35, solid share of the lattice zone) |
| Ribs | `rib_w` (160), `rib_d` (240); grid A: `n_cols` (10, even), `min_pitch` (500); grid B: `n_diamonds` (8) |
| Crown ring | `crown_ring` (True), `crown_b` (200), `crown_h` (200) |
| Buttresses | `but_spacing` (1500), `but_total` (1000 from the inner face), `but_w` (400) |
| Mesh and loads | `mesh_size` (500), `wind_dir`, `qp`, `clad`, `gamma`, `fck`, `kf`, `fixed` |

A slider combination that can't be built (for example an opening wider than the plan) gives empty outputs and the
reason in `info`, so an optimiser run doesn't stop on an error.

### Wiring

| Output | Karamba component |
|---|---|
| `roof_meshes`, `wall_meshes`, `but_meshes` | one **Mesh to Shell** each. Shell cross-section height: `t_roof_elems` for the roof (one thickness per element, tapering like the drawings) if your Karamba version takes a list of heights per element, otherwise `t_roof` (the area-weighted average); `t_wall`, `t_but` for the others. Material from `material`, density `gamma_roof` / `gamma_wall` so the hollow printed layers weigh the right amount |
| `ring_lines` | **Line to Beam**, rectangular `ring_b` x `ring_h` (the solid roof base) |
| `crown_lines` | **Line to Beam**, rectangular `crown_b` x `crown_h` |
| `rib_lines` | **Line to Beam** with `rib_ids` into its Id input; rectangular `rib_w` x `rib_d`, full concrete density. The ids (`col`, `hring`, `hip` for A; `diag`, `hip` for B) let you give the hips or the horizontal ribs their own section. Empty for `none`. |
| `supports` | **Support** (fixed, or pinned with `fixed` = False) |
| gravity | Karamba **Gravity** load |
| `cladding` | **Mesh Load** on `roof_meshes` |
| `wind_vecs`, `wind_walls` | **Mesh Load**, one per mesh, same order (4 load cases: rotate `wind_dir` 0 / 90 / 180 / 270) |

Then **Assemble** all, **Analyze**, and read utilisation, reactions at `supports` and the displacement.
The buttress base reactions settle how much of the roof thrust the buttresses take and how much the solid roof base
carries as a tension ring.

### Optimising

`concrete` (m3) and `weight` (kN, without cladding) are outputs, and `rise` / `slope` give the roof actually built.
For Galapagos (or Octopus for several objectives), use the sliders above as genes. A typical fitness is
minimise `concrete` subject to Karamba's maximum displacement and utilisation staying under a limit, run once per
`grid`. `weight` should match the sum of Karamba's vertical reactions under gravity alone. Idealisations (ring beam at
the centroid of the solid base, ribs start on the ring beam, no footing) are listed at the top of the script.
