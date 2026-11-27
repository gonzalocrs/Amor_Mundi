"""Footing width needed for tipping FS 1.5 in each corner-column-removal case (page 07), from corners/forces-<roof>-<case>.json
(D2 at the final sizes, 2026-11-27) with rect_check.check (strip on the side column lines, final column centres)."""
import os, json
import rect_check as rc, corners_report as cr
HERE = os.path.dirname(os.path.abspath(__file__))
out = {}
for roof in ("15x10", "10x10"):
    for case, lab in cr.CASES:
        D = cr.load(roof, case); B = 0.5
        while min(v[1] for v in rc.check(roof, B, D=D)[0].values()) < 1.5 and B < 4: B += 0.05
        out[roof + "|" + case] = round(B, 2); print(roof, case, round(B, 2))
json.dump(out, open(os.path.join(HERE, "corners_footing_width.json"), "w"), indent=1)
