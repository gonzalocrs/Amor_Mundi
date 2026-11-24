"""Joined printed pieces: printed piece UNION (rib tube INTERSECT piece slot) MINUS cast cores.
Inputs: root (roof layer group), cx, cy (roof centre), start / count (batch of pieces, in a stable order).
Reads the live layers of the active Rhino document; generator in joined_gen.py (same folder)."""
import importlib.util
import Grasshopper
import Rhino
import Rhino.Geometry as G
P = r'C:\Users\gonza\Documents\GitHub\Amor_Mundi\polyframe2\joined-pieces'

PIECE_LAYERS = ("printed pieces", "top course = printed U formwork")


class MyComponent(Grasshopper.Kernel.GH_ScriptInstance):
    def RunScript(self, root: str, cx: float, cy: float, start: int, count: int):
        spec = importlib.util.spec_from_file_location('joined_gen', P + r'\joined_gen.py')
        J = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(J)
        doc = Rhino.RhinoDoc.ActiveDoc
        rl = doc.Layers[doc.Layers.FindByFullPath(str(root).strip(), -1)]
        pieces, ribs, cores = [], [], []
        for ch in rl.GetChildren():
            nm = ch.Name
            objs = list(doc.Objects.FindByLayer(ch) or [])
            if nm.startswith(PIECE_LAYERS) and "(joined)" not in nm:
                pieces += [(str(o.Id), o.Geometry) for o in objs]
            elif nm == "ribs (final, joint fillets)":
                ribs += [(o.Geometry, o.Geometry.GetBoundingBox(True)) for o in objs]
            elif nm.startswith("cast rib cores - pushed in"):
                cores += [(o.Geometry, o.Geometry.GetBoundingBox(True)) for o in objs]
        pieces.sort(key=lambda t: (round(t[1].GetBoundingBox(True).Min.Z, 2), t[0]))
        c = G.Point3d(cx, cy, 0)
        out, ids, status, lines = [], [], [], []
        batch = pieces[int(start): int(start) + int(count)]
        for pid, g in batch:
            j, s, info = J.join_piece(g, c, ribs, cores)
            out.append(j); ids.append(pid); status.append(s)
            if s.startswith("fail"):
                bb = g.GetBoundingBox(True)
                lines.append("%s z %.2f %s (%s)" % (pid[:8], bb.Min.Z, s, info))
        summary = "pieces %d-%d of %d: %s" % (int(start), int(start) + len(batch), len(pieces),
                                              ", ".join("%s %d" % (k, status.count(k)) for k in sorted(set(status))))
        return out, ids, status, summary + ("\n" + "\n".join(lines) if lines else "")
