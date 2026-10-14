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
| `scripts/karamba_model.py` | Karamba3D model: roof/wall/buttress shells, solid roof-base ring, supports, wind and cladding loads |
| `details/set/pyramid-roof-drawing-set.pdf` | **The drawing set**, 10 A3 sheets: 01 floor plan, 02/03 floor plan with roof grid A/B, 04/05 section A-A grid A/B, 06/07 roof plan cut at +6.00 grid A/B, 08/09 roof-grid elevations A/B, 10 eave detail D1. One PDF per sheet next to it. |
| `details/set/cad/*.dxf` | The same 10 sheets as editable CAD: model space 1:1 in mm, a paper-space layout **A3 sheet** with a viewport at the sheet scale (plot at 1:1), title block and legend in paper space, real DIMENSION entities (style `PYR`), hatches, named layers. |
| `details/make_set.py` | Builds the whole set (PDFs + DXFs): `pip install cairosvg ezdxf shapely`, then `python details/make_set.py` |
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
All three have the same shell, walls and 32 buttresses (8 per side, as on the floor plan), so the results compare
like for like. The roof mesh follows the ribs, so each rib is a chain of beams on shell nodes.
Run `python scripts/karamba_model.py` to print the three variants and check that everything connects.

Wire its outputs like this:

| Output | Karamba component |
|---|---|
| `roof_meshes`, `wall_meshes`, `but_meshes` | one **Mesh to Shell** each, with a Shell cross-section of thickness `t_roof` / `t_wall` / `t_but` and a material from `material` (use `gamma_roof` / `gamma_wall` as the density so the hollow printed layers weigh the right amount) |
| `ring_lines` | **Line to Beam**, rectangular 400 x 300 (the solid roof base) |
| `crown_lines` | **Line to Beam**, e.g. 200 x 200 (assumed crown compression ring; set `crown_ring` False to drop it) |
| `rib_lines` | **Line to Beam** with `rib_ids` into its Id input; rectangular `rib_w` x `rib_d` (160 x 240), full concrete density. The ids (`col`, `hring`, `hip` for A; `diag`, `hip` for B) let you give the hips or the horizontal ribs their own section. Empty for `none`. |
| `supports` | **Support** (fixed, or pinned with `fixed` = False) |
| gravity | Karamba **Gravity** load |
| `cladding` | **Mesh Load** on `roof_meshes` |
| `wind_vecs`, `wind_walls` | **Mesh Load**, one per mesh, same order (4 load cases: rotate `wind_dir` 0 / 90 / 180 / 270) |

Then **Assemble** all, **Analyze**, and read utilisation, reactions at `supports` and the displacement. Run it once
per `grid` value to compare the options. The self weight should match `info`. The buttress base reactions settle how
much of the roof thrust the buttresses take and how much the solid roof base carries as a tension ring.
Idealisations (ring beam at the centroid of the solid base, ribs start on the ring beam, crown ring snapped to the
mesh, no footing) are listed at the top of the script.
