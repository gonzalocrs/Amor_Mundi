"""Per-slot audit of the joined layer against the original pieces. Writes _audit.json (one record per slot)."""
import collections, json, time
import Rhino.Geometry as G

OUT = r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\polyframe2\joined-pieces\_audit.json"

def run(doc):
    rep = {}
    for rt in ("15x10", "10x10"):
        R = rt + " complete v3e-ring-step::"
        lay = lambda n: doc.Layers[doc.Layers.FindByFullPath(R + n, -1)]
        srcs = list(doc.Objects.FindByLayer(lay("printed pieces (closed solids, 3 cm walls, lid 3, groove 6x4)"))) + \
               list(doc.Objects.FindByLayer(lay("top course = printed U formwork for the crown ring")))
        J = list(doc.Objects.FindByLayer(lay("printed pieces + rib (joined)")))
        by = collections.defaultdict(list)
        for o in J:
            by[o.Attributes.GetUserString("source_piece")].append(o)
        recs = []
        for s in srcs:
            a = s.Geometry.GetBoundingBox(True)
            va = abs(G.VolumeMassProperties.Compute(s.Geometry, True, False, False, False).Volume)
            for o in by.get(str(s.Id), []) or [None]:
                r = {"src": str(s.Id), "z": round(a.Min.Z, 3)}
                if o is None:
                    r["issue"] = "missing"; recs.append(r); continue
                b = o.Geometry.GetBoundingBox(True)
                vm = G.VolumeMassProperties.Compute(o.Geometry, True, False, False, False)
                vb = abs(vm.Volume) if vm else 0.0
                grow = max(a.Min.X - b.Min.X, b.Max.X - a.Max.X, a.Min.Y - b.Min.Y, b.Max.Y - a.Max.Y, a.Min.Z - b.Min.Z, b.Max.Z - a.Max.Z)
                shrink = max(b.Min.X - a.Min.X, a.Max.X - b.Max.X, b.Min.Y - a.Min.Y, a.Max.Y - b.Max.Y, b.Min.Z - a.Min.Z, a.Max.Z - b.Max.Z)
                r.update({"id": str(o.Id), "join": o.Attributes.GetUserString("join_status"), "fill": o.Attributes.GetUserString("fill"),
                          "vr": round(vb / va, 3) if va else 0, "grow": round(grow, 3), "shrink": round(shrink, 3),
                          "solid": bool(o.Geometry.IsSolid and o.Geometry.IsValid), "n": len(by[str(s.Id)])})
                issues = []
                if r["n"] > 1: issues.append("duplicate")
                if not r["solid"]: issues.append("not-solid")
                if r["vr"] < 0.8 or r["vr"] > 1.7: issues.append("volume")
                if r["grow"] > 0.3: issues.append("outlier")
                if r["shrink"] > 0.01: issues.append("smaller-than-slot")
                r["issue"] = ",".join(issues)
                recs.append(r)
        rep[rt] = {"sources": len(srcs), "visible": len(J), "records": recs}
    json.dump(rep, open(OUT, "w"))
    return {k: (v["sources"], v["visible"], collections.Counter(r["issue"] for r in v["records"] if r["issue"])) for k, v in rep.items()}
