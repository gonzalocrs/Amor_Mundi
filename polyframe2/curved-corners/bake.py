"""Bake the curved-corner rebuild next to the originals (Gonzalo, 2026-11-23).
For each faceted piece / growth band / top-course piece: rebuild with facet_merge.Rebuilder, add it to a NEW layer
'<module>::curved corners (test)::<source layer>', copy name + user text, and HIDE the original object (not delete).
Objects without facets (straight pieces) or that fail stay as they are and visible.
Call bake(doc, module, sublayer, start, stop) in batches; returns counts."""
import os
import Rhino
import Rhino.Geometry as G
import System

HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\polyframe2\curved-corners"
SUBS = ["printed pieces (closed solids, 3 cm walls, lid 3, groove 6x4)",
        "growth bands (outer face, per piece)",
        "top course = printed U formwork for the crown ring"]
TAG = "curved_corners_src"


def env():
    g = {}
    exec(open(os.path.join(HERE, "curved_corners.py")).read(), g)
    exec(open(os.path.join(HERE, "facet_merge.py")).read(), g)
    return g


def target_layer(doc, module, sub):
    parent = "%s complete v3e-ring-step" % module
    pidx = doc.Layers.FindByFullPath(parent, -1)
    tpath = parent + "::curved corners (test)"
    tidx = doc.Layers.FindByFullPath(tpath, -1)
    if tidx < 0:
        L = Rhino.DocObjects.Layer(); L.Name = "curved corners (test)"; L.ParentLayerId = doc.Layers[pidx].Id
        tidx = doc.Layers.Add(L)
    lpath = tpath + "::" + sub
    li = doc.Layers.FindByFullPath(lpath, -1)
    if li < 0:
        src = doc.Layers[doc.Layers.FindByFullPath(parent + "::" + sub, -1)]
        L = Rhino.DocObjects.Layer(); L.Name = sub; L.ParentLayerId = doc.Layers[tidx].Id; L.Color = src.Color
        L.RenderMaterialIndex = src.RenderMaterialIndex
        li = doc.Layers.Add(L)
    return li


def all_objs(doc):
    s = Rhino.DocObjects.ObjectEnumeratorSettings(); s.HiddenObjects = True; s.LockedObjects = True
    return list(doc.Objects.GetObjectList(s))


def bake(doc, module, sub, start, stop, g=None):
    g = g or env()
    centre = g["CENTRES"][module]
    src_li = doc.Layers.FindByFullPath("%s complete v3e-ring-step::%s" % (module, sub), -1)
    objs = sorted([o for o in all_objs(doc) if o.Attributes.LayerIndex == src_li], key=lambda o: str(o.Id))
    tli = target_layer(doc, module, sub)
    done = set(o.Attributes.GetUserString(TAG) for o in all_objs(doc) if o.Attributes.LayerIndex == tli)
    n_ok = n_skip = n_fail = 0
    fails = []
    for o in objs[start:stop]:
        if str(o.Id) in done:
            n_ok += 1; continue
        br = o.Geometry
        if not isinstance(br, G.Brep):
            n_skip += 1; continue
        try:
            s, msg = g["Rebuilder"](br, centre, g["outer_chain"]).run()
        except Exception as ex:
            s, msg = None, "error %s" % ex
        if s is None:
            if msg in ("no facets", "straight"):
                n_skip += 1
            else:
                n_fail += 1; fails.append((str(o.Id), msg))
            continue
        v0 = G.VolumeMassProperties.Compute(br).Volume
        v1 = G.VolumeMassProperties.Compute(s).Volume
        if abs(v1 - v0) > 0.03 * v0:
            n_fail += 1; fails.append((str(o.Id), "volume %.4f -> %.4f" % (v0, v1))); continue
        a = o.Attributes.Duplicate()
        a.LayerIndex = tli
        a.SetUserString(TAG, str(o.Id))
        a.RemoveFromAllGroups()
        nid = doc.Objects.AddBrep(s, a)
        if nid != System.Guid.Empty:
            doc.Objects.Hide(o.Id, True)
            n_ok += 1
        else:
            n_fail += 1; fails.append((str(o.Id), "add failed"))
    return n_ok, n_skip, n_fail, fails, len(objs)
