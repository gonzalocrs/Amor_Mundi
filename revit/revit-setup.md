# Revit setup: structural drawings

Where the structural work in the team Revit model stands, and what's next. Updated 2026-10-16.

## The model

| | |
|---|---|
| File | **CONCRETE_2026.rvt**, a workshared cloud model (121 MB) |
| Where | Autodesk Docs: *Untitled Hub → Concrete 2026 → Project Files* |
| How to open | In Revit (not the website): Home screen → Autodesk Docs → Concrete 2026 → Project Files → CONCRETE_2026, or *File → Open → Cloud Models* |
| Who's in it | Every discipline (architecture, interior, landscape, MEP, civil, structure) works in this one file. There's no separate structural file. |
| My part | **All of the structure**: foundations, slabs, structural walls, pyramid roofs. |

The website's *Publish* button only refreshes the web viewer. Changes reach the team through **Synchronize with Central** in Revit.

## Worksets

| Workset | What's in it |
|---|---|
| CAD links | Imported CAD files (hidden by default) |
| Shared Levels and Grids | Levels and grids: everyone uses them, nobody moves them without telling the team |
| Workset1 | Everything the rest of the team has drawn |
| **Structure** | **Mine.** Created and synced 2026-10-16. Everything structural goes here. |

**Check every session that the active workset (status bar, bottom of the window) says Structure** before drawing anything.

## What's set up

**Sheets** (numbered to match the team's A101 / C101 style):

| Sheet | Title | View on it |
|---|---|---|
| S100 | Cover Sheet | `S - 3D COVER` |
| S101 | Foundation Plan | `L1 - Structural` |
| S102 | Structural Plans (title to decide) | `L2 - Structural` |
| — | Roof framing plan | not created yet |

**Views:**

- `S - 3D COVER` (*Structural → 3D Views*): the cover picture. Workset1 and Levels are hidden, so it stays blank until structure is modelled. The visual style gets chosen at the end.
- `{3D - gc3139}` (*Coordination → 3D Views*): my working 3D view, with architecture visible. Optional extras: *Gray Inactive Workset Graphics*, and ~60 % transparency on Walls, Roofs and Floors (VV → Model Categories).
- `L1 - Structural`, `L2 - Structural`: no view template yet.

**View templates:** the team wants every sheet view to use one. Duplicate *Structural Foundation Plan* and *Structural Framing Plan* as `S - Foundation Plan` and `S - Framing Plan`, set them up (scale to match A101, Medium detail, halftone non-structural categories, Discipline = Structural), and assign them. Never edit a template another discipline uses.

## Rules for the shared model

**Sync** every 30–60 minutes and before closing:
1. *Collaborate → Synchronize with Central ▾ → Synchronize and Modify Settings*.
2. Write a comment.
3. Tick **every** relinquish box (Borrowed Elements, User-created Worksets, …).

Relinquish even though only I edit Structure. Holding ownership blocks teammates whenever their edits have to touch my elements: wall joins, moved grids or levels, attached floors and roofs.

**Never:**
- *Purge Unused*.
- Move the Project Base Point or Survey Point.
- Change level heights without telling the team.
- *Save As* or *Detach from Central* and keep working in the copy.
- Click *Editable* on Workset1 or Shared Levels and Grids.
- Edit `{3D - rc3943}` or any other personal view.
- Delete elements or views that aren't mine.

**Each session:** open the model, check the active workset is Structure, then click *Collaborate → Reload Latest*.

## Done 2026-10-16 (night session)

- [x] Opened the cloud model and understood worksharing
- [x] Created the **Structure** workset, made it active, synced and relinquished
- [x] Found the team's placeholder structural views and sheets and renumbered the sheets S100–S102
- [x] Made `S - 3D COVER` (Workset1 and Levels hidden) and placed it on S100
- [x] Set up `{3D - gc3139}` as the working view

## Today's tasks

1. **Families**
   - Go through the family package from BIG: what's in it, and what's useful for structure.
   - Load only the families actually needed into the shared model. Every family loaded grows the file for the whole team, and families saved in a newer Revit than ours won't load.
   - It's BIG's own office library: fine for coursework, but don't post it or pass it on outside the team.
2. **Shortcuts**: a short list of the ones that matter for structural work.
3. **Karamba → Revit**
   - Bring the Grasshopper/Karamba structure in as a full 3D model through **Rhino.Inside.Revit**, as DirectShapes on the Structure workset.
   - The Karamba model is centre-line surfaces and lines with no thickness. Revit needs solids, so build those from the same parameters in `scripts/karamba_model.py` to keep the Revit model consistent with the analysis.

## Open questions

- [ ] **Which Revit version (year)** is the team on? Check Revit → ? → About. Rhino.Inside.Revit and the families both depend on it.
- [ ] **Levels:** the heights of L1 / LEVEL 1a / LEVEL 1b / L2 / ROOFa / ROOFb, and which pavilion sits on which level. Take a screenshot of the level heads in *South – Architectural*. The pavilions step down the slope, so "first / second floor" titles don't fit. Plan titles and View Ranges (or Plan Regions) depend on this.
- [ ] **S102:** is there a real upper floor anywhere? If not, give the sheet another use (ring beam / wall plan, or sections).
- [ ] **Roof framing plan:** which level (ROOFa or ROOFb) is the roof base the structure sits on.
- [ ] **Foundations:** civil already has *C101 Foundation Plan*. Agree with civil who owns the foundations.
- [ ] **Duplicate walls and roofs:** architecture's old model already has the walls and pyramid roofs. Once mine are in, they delete theirs or untick *Structural* on them.
