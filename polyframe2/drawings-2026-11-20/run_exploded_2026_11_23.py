"""Exploded axonometric of the stepped roofs, bottom to top (Gonzalo 2026-11-23: the midterm 'every element, exploded'
layout for our roofs). Runs in Rhino on current.3dm without touching it: duplicates of the final objects are lifted
group by group in memory and one hidden-line drawing is made (parallel, from the south-west and above). A short
marker line per group gives the 2D label anchor. Also measures the element data per group (count, overall size, m3).
Output: exploded-<roof>.json (linework in metres, same item format as the linework JSONs) and elements-model.json."""
import importlib.util, json, os
import Rhino, Rhino.Geometry as G

P = r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\polyframe2\drawings-2026-11-20"
OUT = r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\details\exploded-2026-11-23"
spec = importlib.util.spec_from_file_location("rx", os.path.join(P, "run_extract.py"))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
X = m.X

# group: (short layer tags, lift in m). Model levels: footing -0.80/-0.30, columns -0.30/+2.00, ring +2.00/+2.40,
# ribs and courses +2.40 to the crown, crown ring + top course at the top. Gaps of about 1.5-2.5 m between groups.
GROUPS = [("rectangular strip footing", ("footing",), 0.0),
          ("columns", ("columns",), 1.8),
          ("base ring step", ("base ring formwork", "base ring cast"), 3.8),
          ("rib net", ("ribs",), 5.8),
          ("printed courses", ("printed pieces",), None),          # lift set per roof: above the rib net
          ("crown ring", ("crown ring cast", "crown ring printed band", "top course U formwork"), None)]
CEN = {"15x10": (85.0, 0.0), "10x10": (85.0, -20.0)}


def lifts(roof, objs):
    zmax = max(g.GetBoundingBox(True).Max.Z for ln, g in objs if X.short(ln) == "ribs")
    zmin = 2.4
    h = zmax - zmin
    L = {n: dz for n, k, dz in GROUPS if dz is not None}
    L["printed courses"] = 5.8 + h + 2.0
    L["crown ring"] = L["printed courses"] + 2.0
    return L


def run(doc):
    os.makedirs(OUT, exist_ok=True)
    elements = {}
    for roof in ("15x10", "10x10"):
        cx, cy = CEN[roof]
        objs = X.final_objects(doc, roof)
        L = lifts(roof, objs)
        lifted = []; info = {}
        for name, keys, _ in GROUPS:
            T = G.Transform.Translation(0, 0, L[name])
            bb = G.BoundingBox.Empty; n = 0; vol = 0.0
            for lname, g in objs:
                if X.short(lname) not in keys:
                    continue
                h = g.DuplicateBrep(); h.Transform(T); lifted.append((name, h)); n += 1
                bb.Union(g.GetBoundingBox(True))
                if g.IsSolid: vol += g.GetVolume()
            info[name] = dict(count=n, lift_m=round(L[name], 2), size_m=[round(bb.Max.X - bb.Min.X, 3), round(bb.Max.Y - bb.Min.Y, 3), round(bb.Max.Z - bb.Min.Z, 3)],
                              z_m=[round(bb.Min.Z, 3), round(bb.Max.Z, 3)], volume_m3=round(vol, 2))
            # label anchor: a 1 cm marker on the group's south-east outer edge, at mid height of the lifted group
            a = G.Point3d(bb.Max.X, bb.Min.Y + 0.0, (bb.Min.Z + bb.Max.Z) / 2 + L[name])
            lifted.append(("anchor|" + name, G.LineCurve(a, a + G.Vector3d(0.01, 0, 0))))
        elements[roof] = info
        d = G.Vector3d(1, 1, -1); d.Unitize()                   # looking from the south-west, from above
        vis = X.hld(lifted, d, G.Vector3d(0, 0, 1), G.Point3d(cx, cy, 10), lambda q: (q.X, q.Y))
        anchors = {}; lines = []
        for it in vis:
            if it["layer"].startswith("anchor|"):
                anchors[it["layer"][7:]] = it["pts"][0]
            else:
                lines.append(it)
        json.dump({"roof": roof, "units": "m", "view": "parallel, from the south-west and above (direction 1,1,-1), z up; 2D screen coordinates",
                   "groups": [(n, round(L[n], 2)) for n, k, _ in GROUPS], "anchors": anchors, "items": X.dedupe(lines)},
                  open(os.path.join(OUT, "exploded-%s.json" % roof), "w"), separators=(",", ":"))
        m.log("exploded %s: %d lines, anchors %s" % (roof, len(lines), sorted(anchors)))
    json.dump(elements, open(os.path.join(OUT, "elements-model.json"), "w"), indent=1)
