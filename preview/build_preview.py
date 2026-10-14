"""Builds preview/karamba-preview.html: an interactive 3D view (three.js) of what scripts/karamba_model.py sends to
Karamba, with the plain shell, grid A and grid B, the layers, the wind load cases and a comparison table.
Uses the drawing defaults of build_model(). Open the HTML in a browser (it loads three.js from a CDN).

Run:  python preview/build_preview.py"""
import json, os, sys
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(here, "..", "scripts"))
import karamba_model as km

r = lambda p: [round(c, 1) for c in p]
mesh = lambda lst: [{"v": [r(p) for p in V], "f": [list(f) for f in F]} for V, F in lst]
out = {"variants": {}}
for g in ("none", "A", "B"):
    m = km.build_model(grid=g)
    G = m["geom"]
    errs = km.check(m)
    if errs:
        sys.exit("grid {}: {}".format(g, errs[:3]))
    out["variants"][g] = {"roof": mesh(m["roof"]), "ring": [[r(a), r(b)] for a, b in m["ring"]],
        "crown": [[r(a), r(b)] for a, b in m["crown"]], "ribs": [[r(a), r(b), i] for a, b, i in m["ribs"]],
        "stats": {"elements": sum(len(F) for _, F in m["roof"]), "rib_m": round(G["rib_len"] / 1000),
                  "rib_beams": len(m["ribs"]), "rib_m3": round(G["vol"]["ribs"], 1),
                  "total_m3": round(sum(G["vol"].values()), 1),
                  "levels": [round(z / 1000, 2) for z in G["levels_a"]], "ring_segs": len(m["ring"])}}
    if g == "A":                                       # walls, buttresses and supports are the same in all three
        out["wall"] = mesh(m["wall"]); out["but"] = mesh(m["but"]); out["supports"] = [r(p) for p in m["supports"]]
        out["summary"] = km.summary(m)

page = open(os.path.join(here, "karamba_preview_template.html")).read().replace("__MODEL__", json.dumps(out, separators=(",", ":")))
head = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        '<style>body{margin:0}[hidden]{display:none!important}</style>\n</head>\n<body>\n')
path = os.path.join(here, "karamba-preview.html")
open(path, "w").write(head + page + "\n</body>\n</html>\n")
print("wrote", path)
