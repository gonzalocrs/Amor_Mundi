# Archive: hand-calculation structural check (2026-10-14)

Kept for reference only, no longer maintained. The structural work continues in the Karamba model
(`scripts/karamba_model.py`).

- `structural_check.py`: screening check (roof thrust, ring beam, wall, buttress, wind, footing).
  It still assumes ONE buttress per side at mid-span (the drawings now have 8 per side, about 1486 apart),
  so its buttress FAIL is out of date. It imports `pyramid_drawings.py` from its own folder, so it no longer
  runs from here; copy it back to `details/` to run it.
