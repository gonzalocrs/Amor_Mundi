"""Corner-leg removal study: summary per roof and case from corners/forces-<roof>-<case>.json."""
import json, os, math
import stress_pdf as s
HERE = os.path.dirname(os.path.abspath(__file__))
CASES = [("0", "all 20 / 16 columns"), ("1", "1 corner out (SW)"), ("2adj", "2 corners, same long side (SW, SE)"),
         ("2diag", "2 corners, diagonal (SW, NE)"), ("3", "3 corners (SW, SE, NE)"), ("4", "all 4 corners")]
GROUPS = ["rib_bottom", "rib_middle", "rib_top", "ring", "crown", "column"]
FS_L, FS_S = 0.215, 0.345          # SD345 allowable (kN/mm2): long / short term
AS_FACE = 3 * 201.0                # 8D16 ring: 3 bars per face


def load(roof, case):
    D = json.load(open(os.path.join(HERE, "corners", "forces-%s-%s.json" % (roof, case))))
    D["idx"] = {}
    for i, (g, a, b) in enumerate(D["els"]):
        D["idx"].setdefault(g, []).append(i)
    return D


def ring_bars(D):
    f = D["forces"]; worst = (0, "", 0, 0)
    for lc in s.LCS:
        fs = FS_L if lc in s.LONGS else FS_S
        for i in D["idx"]["ring"]:
            for t in (0, 1):
                N = f[lc]["N"][2 * i + t]; M = max(abs(f[lc]["My"][2 * i + t]), abs(f[lc]["Mz"][2 * i + t]))
                need = max(N, 0) / 2 / fs + M / (0.875 * 0.34) / fs          # mm2 per face
                if need > worst[0]: worst = (need, lc, N, M)
    return worst


def summary(roof, case):
    D = load(roof, case); r = {}
    for g in GROUPS:
        a = s.group_stats(D, roof, g, s.LONGS); b = s.group_stats(D, roof, g, s.SHORTS)
        r[g] = max(a["sc"][0] / s.ALL_L, b["sc"][0] / s.ALL_S)
    rb = ring_bars(D)
    fz = [f[2] for lc in s.LCS for f in D["reactions"][lc]["RF"]]
    ringM = max(abs(v) for lc in s.LCS for i in D["idx"]["ring"] for k in ("My", "Mz") for v in (D["forces"][lc][k][2 * i], D["forces"][lc][k][2 * i + 1]))
    return dict(util=r, ring_bars=rb, ring_M=ringM, disp_mm=max(D["maxdisp_cm"].values()) * 10, disp_lc=max(D["maxdisp_cm"], key=D["maxdisp_cm"].get),
                buckling=D["buckling"][0], fz_max=max(fz), fz_min=min(fz), n_sup=len(D["reactions"]["LONG"]["RF"]))


if __name__ == "__main__":
    out = {}
    for roof in ("15x10", "10x10"):
        for case, lab in CASES:
            S = summary(roof, case); out["%s|%s" % (roof, case)] = S
            u = S["util"]
            ok = max(u.values()) < 1 and S["ring_bars"][0] <= AS_FACE and S["fz_min"] > 0
            print("%s %-6s ribs %3.0f/%3.0f/%3.0f%%  ring %3.0f%% M %5.1f bars %4.0f mm2/face  crown %3.0f%%  cols %3.0f%%  disp %5.1f mm (%s)  buck %5.1f  Fz %5.0f..%5.0f  %s" % (
                roof, case, 100 * u["rib_bottom"], 100 * u["rib_middle"], 100 * u["rib_top"], 100 * u["ring"], S["ring_M"], S["ring_bars"][0], 100 * u["crown"], 100 * u["column"],
                S["disp_mm"], S["disp_lc"], S["buckling"], S["fz_min"], S["fz_max"], "PASS" if ok else "CHECK"))
    json.dump(out, open(os.path.join(HERE, "corners_summary.json"), "w"), indent=1)
