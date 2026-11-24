"""Formwork study summary from formwork/forces-<roof>-<A|B|C>.json (written by k_formwork.py in Karamba).
Stresses are my section checks from Karamba's end forces (same method as stress_pdf.py): ribs solid round cores,
rings/columns rectangles, courses/fins with the A and W of the Karamba cross-sections. Writes formwork-study.json."""
import os, sys, json, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import stress_pdf as s

V = {"A": "ribs only: courses and fins E x 0.0001 (pure weight)", "B": "current: courses E x 0.02, fins E x 0.3",
     "C": "formwork structural: courses and fins E = 25 GPa, bonded to the ribs"}
BOND, FT_LAYERS = 0.6, 2.0          # MPa: mortar bond between printed parts / printed concrete tension across layers
RIBS = ["rib_bottom", "rib_middle", "rib_top"]


def load(roof, v):
    D = json.load(open(os.path.join(HERE, "formwork", "forces-%s-%s.json" % (roof, v))))
    D["idx"] = {}
    for i, (g, a, b) in enumerate(D["els"]):
        D["idx"].setdefault(g, []).append(i)
    return D


def worst(D, roof, groups, lcs, allow):
    best = (0, None, None)
    for g in groups:
        st = s.group_stats(D, roof, g, lcs)
        u = st["sc"][0] / allow
        if u > best[0]: best = (u, g, st["sc"][1], round(st["sc"][0], 2))
    return {"util": round(best[0], 3), "group": best[1], "case": best[2], "stress_MPa": best[3]}


def rng(D, g, k, lcs):
    vals = [D["forces"][lc][k][2 * i + t] for lc in lcs for i in D["idx"][g] for t in (0, 1)]
    return [round(min(vals), 1), round(max(vals), 1)]


def mmax(D, g, lcs):
    return round(max(math.hypot(D["forces"][lc]["My"][2 * i + t], D["forces"][lc]["Mz"][2 * i + t]) for lc in lcs for i in D["idx"][g] for t in (0, 1)), 1)


def printed(D, g):
    """max compression / tension fibre stress (MPa) in courses or fins, with case and location"""
    c = D["crosec"][g]; A, Wy, Wz = c["A"], c["Wy"], c["Wz"]
    bc, bt = (0, None), (0, None)
    for lc in s.LCS:
        f = D["forces"][lc]
        for i in D["idx"][g]:
            for t in (0, 1):
                N = f["N"][2 * i + t]; m = abs(f["My"][2 * i + t]) / Wy + abs(f["Mz"][2 * i + t]) / Wz
                sc_ = (-N / A + m) / 1000.0; st_ = (N / A + m) / 1000.0
                p = D["nodes"][D["els"][i][1 + t]]
                if sc_ > bc[0]: bc = (sc_, (lc, i, p))
                if st_ > bt[0]: bt = (st_, (lc, i, p))
    lab = lambda x: {"case": x[0], "element": x[1], "node_xyz": x[2]}
    return {"max_compression_MPa": round(bc[0], 2), "at": lab(bc[1]), "max_tension_MPa": round(bt[0], 2), "at_t": lab(bt[1]), "A_m2": round(A, 4)}


def base_share(D, lc="LONG"):
    """vertical load entering the base ring nodes from above: rib feet vs printed courses/fins (kN, LONG)"""
    ring_nodes = set()
    for i in D["idx"]["ring"]:
        ring_nodes.update(D["els"][i][1:3])
    sh = {"ribs": 0.0, "courses_fins": 0.0}
    for i, (g, a, b) in enumerate(D["els"]):
        if g not in RIBS + ["course", "fin"]: continue
        for t, n in ((0, a), (1, b)):
            if n not in ring_nodes: continue
            o = D["nodes"][b if t == 0 else a]; p = D["nodes"][n]
            L = math.dist(o, p); dz = (o[2] - p[2]) / L if L else 0
            N = D["forces"][lc]["N"][2 * i + t]                 # + tension; compression pushes down on the ring
            fz = -N * dz                                       # downward force on the ring node (kN), + = down
            sh["ribs" if g in RIBS else "courses_fins"] += fz
    tot = sh["ribs"] + sh["courses_fins"]
    return {k: round(v, 1) for k, v in sh.items()} | {"courses_fins_share": round(sh["courses_fins"] / tot, 3) if tot else None}


def bed_joints(D):
    """worst bed-joint stress, taken in the fins (the vertical end walls that cross every bed joint between courses):
    normal tension N/A + bending, and shear V/A, over all cases; per unit length = stress x wall thickness"""
    c = D["crosec"]["fin"]; A, Wy, Wz = c["A"], c["Wy"], c["Wz"]
    bt, bs = (0, None), (0, None)
    for lc in s.LCS:
        f = D["forces"][lc]
        for i in D["idx"]["fin"]:
            for t in (0, 1):
                N = f["N"][2 * i + t]; m = abs(f["My"][2 * i + t]) / Wy + abs(f["Mz"][2 * i + t]) / Wz
                ten = (N / A + m) / 1000.0; sh = math.hypot(f["Vy"][2 * i + t], f["Vz"][2 * i + t]) / A / 1000.0
                if ten > bt[0]: bt = (ten, lc)
                if sh > bs[0]: bs = (sh, lc)
    return {"tension_MPa": round(bt[0], 2), "tension_case": bt[1], "shear_MPa": round(bs[0], 2), "shear_case": bs[1],
            "vs_mortar_bond_0.6MPa": round(max(bt[0], bs[0]) / BOND, 2), "vs_layer_tension_2MPa": round(bt[0] / FT_LAYERS, 2)}


def summary(roof, v):
    D = load(roof, v)
    r = {"variant": V[v], "E_kN_cm2": D.get("E_kN_cm2"),
         "rib_long": worst(D, roof, RIBS, s.LONGS, s.ALL_L), "rib_short": worst(D, roof, RIBS, s.SHORTS, s.ALL_S),
         "ring_N_kN": rng(D, "ring", "N", s.LCS), "ring_M_kNm": mmax(D, "ring", s.LCS),
         "crown_N_kN": rng(D, "crown", "N", s.LCS), "crown_M_kNm": mmax(D, "crown", s.LCS),
         "column_N_kN": rng(D, "column", "N", s.LCS), "column_M_kNm": mmax(D, "column", s.LCS),
         "ring_util": worst(D, roof, ["ring"], s.LCS, s.ALL_S), "column_util_long": worst(D, roof, ["column"], s.LONGS, s.ALL_L),
         "column_util_short": worst(D, roof, ["column"], s.SHORTS, s.ALL_S),
         "max_deflection_mm": round(max(D["maxdisp_cm"].values()) * 10, 1), "deflection_case": max(D["maxdisp_cm"], key=D["maxdisp_cm"].get),
         "max_deflection_ThII_mm": round(max(D["maxdisp_ThII_cm"].values()) * 10, 1),
         "buckling_factor_1": round(D["buckling"][0], 2),
         "vertical_reaction_LONG_kN": round(sum(f[2] for f in D["reactions"]["LONG"]["RF"]), 1)}
    if v in ("B", "C"):
        r["courses"] = printed(D, "course"); r["fins"] = printed(D, "fin")
        r["base_share_LONG"] = base_share(D); r["bed_joints"] = bed_joints(D)
    fails = []
    for k in ("rib_long", "rib_short", "column_util_long", "column_util_short", "ring_util"):
        if r[k]["util"] > 1: fails.append("%s %.0f%%" % (k, 100 * r[k]["util"]))
    if v == "A" and r["buckling_factor_1"] < 5: fails.append("buckling factor %.1f < 5" % r["buckling_factor_1"])
    if v == "C":
        if r["bed_joints"]["vs_mortar_bond_0.6MPa"] > 1: fails.append("bed joints %.1f MPa > 0.6 MPa bond" % max(r["bed_joints"]["tension_MPa"], r["bed_joints"]["shear_MPa"]))
        if r["courses"]["max_tension_MPa"] > FT_LAYERS: fails.append("course tension %.1f MPa > 2 MPa" % r["courses"]["max_tension_MPa"])
    r["fails"] = fails
    return r


if __name__ == "__main__":
    out = {"method": "Karamba 3.1, 2 m canvases, all 10 cases; only course/fin E and G changed. Allowables Fc36: 12 MPa long, 24 MPa short. "
                     "Rib/ring/column stress = -N/A + M/W from Karamba end forces (my section check, not Karamba utilisation).",
           "results": {}}
    for roof in ("15x10", "10x10"):
        for v in ("A", "B", "C"):
            out["results"]["%s %s" % (roof, v)] = summary(roof, v)
    p = os.path.join(HERE, "formwork", "formwork-study.json")
    json.dump(out, open(p, "w"), indent=1)
    for k, r in out["results"].items():
        print(k, "ribs L %.0f%% %s/%s  S %.0f%% %s/%s  col %.0f/%.0f%%  defl %.1f mm  buck %.2f  Rz %.0f  %s" % (
            100 * r["rib_long"]["util"], r["rib_long"]["group"], r["rib_long"]["case"], 100 * r["rib_short"]["util"], r["rib_short"]["group"], r["rib_short"]["case"],
            100 * r["column_util_long"]["util"], 100 * r["column_util_short"]["util"], r["max_deflection_mm"], r["buckling_factor_1"], r["vertical_reaction_LONG_kN"], r["fails"]))
        if "courses" in r:
            print("   courses", r["courses"]["max_compression_MPa"], r["courses"]["max_tension_MPa"], "fins", r["fins"]["max_compression_MPa"], r["fins"]["max_tension_MPa"], r["base_share_LONG"], r["bed_joints"])
