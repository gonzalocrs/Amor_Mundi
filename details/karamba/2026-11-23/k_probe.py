# Probe: in a Rhino started with /netcore-8, check Karamba loads, open the fc36 canvas, dump its structure. Writes k_probe.log.
import os, sys, traceback, time
LOG = r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\details\karamba\2026-11-23\k_probe.log"
def log(*a):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(time.strftime("%H:%M:%S ") + " ".join(str(x) for x in a) + "\n")
try:
    import System, Rhino
    log("runtime", System.Environment.Version)
    Rhino.RhinoApp.RunScript("_-Karamba3DGetLicense _Enter", False)
    log("license cmd done")
    gh = Rhino.RhinoApp.GetPlugInObject("Grasshopper")
    gh.LoadEditor()
    import Grasshopper
    srv = Grasshopper.Instances.ComponentServer
    cats = sorted(set(p.Desc.Category for p in srv.ObjectProxies))
    log("proxies", srv.ObjectProxies.Count, "loading", srv.IsLoading, cats)
    for name in ("stepped-15x10-v3e-karamba-fc36.gh", "stepped-10x10-v3e-karamba-fc36.gh"):
        io = Grasshopper.Kernel.GH_DocumentIO()
        ok = io.Open(os.path.join(r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\polyframe2", name))
        d = io.Document
        log("open", name, ok, d.ObjectCount if d else None)
        for o in d.Objects:
            tn = o.GetType().Name
            nick = getattr(o, "NickName", "")
            extra = ""
            if hasattr(o, "Params"):
                extra = "in=" + ",".join("%s[%d]" % (p.NickName, p.SourceCount) for p in o.Params.Input)
            if tn == "GH_Panel":
                extra = (o.UserText or "")[:80].replace("\n", " ")
            if tn == "GH_NumberSlider":
                extra = str(o.CurrentValue)
            cat = getattr(o, "Category", "")
            log("  ", tn, "|", cat, "|", getattr(o, "Name", ""), "|", nick, "|", extra)
except Exception:
    log("ERROR", traceback.format_exc())
log("end")
