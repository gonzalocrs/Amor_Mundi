"""Headline numbers of the design model D2 for the drawing set (design-values-D2.json), from forces-<roof>.json (D2) with
the same hand checks as the stress PDF (stress_pdf.group_stats, rect_check), and the D2 update of karamba-model-tables.json."""
import os, sys, json, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import stress_pdf as s, rect_check
KM = r"C:\Users\gonza\AppData\Local\Temp\claude\5c622a39c96e3387\d0f96d15-672a-4d67-b7d7-f160f3f4487b\scratchpad\kmodel27\karamba-model-tables.json"
V = json.load(open(os.path.join(HERE, "formwork", "variant-D.json")))["results"]


def worst(D, roof, groups, lcs, allow):
    b = (0, None, None, None)
    for g in groups:
        st = s.group_stats(D, roof, g, lcs)
        if st["sc"][0] / allow > b[0]: b = (st["sc"][0] / allow, g, st["sc"][1], st["sc"][0])
    return {"util_pct": round(100 * b[0]), "member": b[1], "case": b[2], "stress_MPa": round(b[3], 1)}


def mmax(D, g, lcs):
    return round(max(math.hypot(D["forces"][lc]["My"][2 * i + t], D["forces"][lc]["Mz"][2 * i + t]) for lc in lcs for i in D["idx"][g] for t in (0, 1)), 1)


def rng(D, g, lcs):
    v = [D["forces"][lc]["N"][2 * i + t] for lc in lcs for i in D["idx"][g] for t in (0, 1)]
    return [round(min(v), 1), round(max(v), 1)]


out = {"model": "D2 at the FINAL model sizes (2026-11-27: base ring 528 x 400 / 552 x 400, columns 420 radial x 360 / 362 x 300): printed casing tied to the ribs through the tubes; bed joints compression-only (end walls as compression-only "
                "trusses, Karamba Tension/Compression Eliminator per load case); head joints open (courses E x 0.02). Karamba 3.1, 2 m canvases "
                "polyframe2/stepped-<roof>-karamba-2m-2026-11-27.gh. Allowables Fc36 12 / 24 MPa; soil 200 / 400 kPa assumed; footing mu 0.5.",
       "sign": "N + tension (kN); stresses compression +"}
for roof in ("15x10", "10x10"):
    D = s.load(roof)
    B = 1.20 if roof == "15x10" else 0.85
    rc, Ls = rect_check.check(roof, B)
    qL = max(rc[l][0] for l in s.LONGS); qS = max(rc[l][0] for l in s.SHORTS)
    tip = min(rc.values(), key=lambda v: v[1]); sl = min(rc.values(), key=lambda v: v[2])
    tl = min(s.LCS, key=lambda l: rc[l][1]); sll = min(s.LCS, key=lambda l: rc[l][2])
    W = abs(D["sumF"]["LONG"][2]); d2 = V["%s D2" % roof]
    out[roof] = {
        "rib_worst_long_term": worst(D, roof, ["rib_bottom", "rib_middle", "rib_top"], s.LONGS, s.ALL_L),
        "rib_worst_short_term": worst(D, roof, ["rib_bottom", "rib_middle", "rib_top"], s.SHORTS, s.ALL_S),
        "rib_cores_mm": {"bottom": int(s.RIB_D[roof]["rib_bottom"] * 1000), "middle": int(s.RIB_D[roof]["rib_middle"] * 1000), "top": int(s.RIB_D[roof]["rib_top"] * 1000)},
        "base_ring": {"N_kN_long": rng(D, "ring", s.LONGS), "N_kN_short": rng(D, "ring", s.SHORTS), "M_kNm_max": mmax(D, "ring", s.LCS),
                      "steel_mm2_needed_long": round(rng(D, "ring", s.LONGS)[1] / 0.215), "steel_mm2_needed_short": round(rng(D, "ring", s.SHORTS)[1] / 0.345), "bars": "8-D16 (1,592 mm2)"},
        "crown_ring": {"N_kN_long": rng(D, "crown", s.LONGS), "N_kN_short": rng(D, "crown", s.SHORTS), "M_kNm_max": mmax(D, "crown", s.LCS),
                       "util_short": worst(D, roof, ["crown"], s.SHORTS, s.ALL_S)},
        "columns": {"N_kN_long": rng(D, "column", s.LONGS), "N_kN_short": rng(D, "column", s.SHORTS), "M_kNm_max": mmax(D, "column", s.LCS),
                    "util_long": worst(D, roof, ["column"], s.LONGS, s.ALL_L), "util_short": worst(D, roof, ["column"], s.SHORTS, s.ALL_S)},
        "deflection_mm": {"LONG": round(D["maxdisp_cm"]["LONG"] * 10, 1), "max": round(max(D["maxdisp_cm"].values()) * 10, 1), "max_case": max(D["maxdisp_cm"], key=D["maxdisp_cm"].get),
                          "second_order_max": round(max(D["maxdisp_ThII_cm"].values()) * 10, 1)},
        "buckling_factor_1": round(D["buckling"][0], 1),
        "footing": {"width_m": B, "depth_m": 0.5, "base_level_m": -0.80, "bearing_kPa_long": round(qL), "bearing_kPa_short": round(qS),
                    "tipping_FS_min": round(tip[1], 2), "tipping_case": tl, "sliding_FS_min": round(sl[2], 2), "sliding_case": sll, "all_ok": tip[1] >= 1.5 and sl[2] >= 1.5 and qL <= 200 and qS <= 400},
        "weight_LONG_kN": round(W), "weight_LONG_t": round(W / 9.81, 1),
        "casing": {"share_of_weight_through_casing": d2["base_share_LONG"]["courses_fins_share"], "end_walls_lifting_off_max": max(d2["fins_dropped_in_tension"].values()),
                   "end_walls_total": d2["fins_total"], "tube_core_shear_MPa_max": max(v["tau_long_MPa"] for v in d2["tube_core_interface"].values())},
        "supports": len(D["reactions"]["LONG"]["RF"]),
        "support_V_kN_long": [round(min(f[2] for f in D["reactions"]["LONG"]["RF"])), round(max(f[2] for f in D["reactions"]["LONG"]["RF"]))]}
json.dump(out, open(os.path.join(HERE, "design-values-2026-11-27.json"), "w"), indent=1)

# karamba-model-tables.json -> D2
T = json.load(open(KM, encoding="utf-8"))
for roof in ("15x10", "10x10"):
    for e in T[roof]["elements"]:
        if e["id"] == "course":
            e["section_mm"] = "box 450 x 500, 2 skins; printed, E x 0.02 of C30/37 (head joints open); tied to the ribs at the tubes; not drawn in the render"
        if e["id"] == "ring":
            e["section_mm"] = "528 x 400 (typical cast width of the final model x depth)" if roof == "15x10" else "552 x 400 (typical cast width of the final model x depth)"
        if e["id"] == "column":
            e["section_mm"] = ("420 (radial) x 360, fixed at the base, 20 columns" if roof == "15x10" else "362 (radial) x 300, fixed at the base, 16 columns")
        if e["id"] == "fin":
            e["section_mm"] = "2 walls 80 x 300; pinned truss, E 25 GPa, COMPRESSION ONLY (bed joints): removed by Karamba's Tension/Compression Eliminator wherever it would pull, per load case; weight carried in the courses; not drawn"
    T[roof]["weight_LONG_kN"] = out[roof]["weight_LONG_kN"]; T[roof]["weight_LONG_t"] = out[roof]["weight_LONG_t"]
D_ = {r: s.load(r) for r in ("15x10", "10x10")}
for k, leg in T["render"]["legends"].items():
    roof, case = k.split()
    lc = leg["load_case"]; D = D_[roof]; ext = (0, 0)
    for g in ("rib_bottom", "rib_middle", "rib_top", "ring", "crown", "column"):
        st = s.group_stats(D, roof, g, [lc]); ext = (max(ext[0], st["sc"][0]), min(ext[1], st["st"][0]))
    leg["actual_extremes_MPa_my_section_check"] = {"compression": round(ext[0], 1), "tension": round(ext[1], 1)}
T["casing_note"] = ("Design model D2. Every printed piece is printed around its rib tube and the cast core runs through it, so the casing hangs on "
                    "the ribs. The bed joints between courses are mortar and only push: the piece end walls that cross them are compression-only "
                    "(Karamba removes any that would pull, case by case). The head joints along a course are taken as open (courses E x 0.02). "
                    "About a third of the weight reaches the base ring through the casing; under typhoon some end walls lift off (up to %d of %d on the "
                    "15x10, %d of %d on the 10x10) and the ribs carry their load around them." % (out["15x10"]["casing"]["end_walls_lifting_off_max"], out["15x10"]["casing"]["end_walls_total"],
                                                                                             out["10x10"]["casing"]["end_walls_lifting_off_max"], out["10x10"]["casing"]["end_walls_total"]))
T["render"]["model"] = "D2 (forces of each case from its own compression-only solve)"
T["worst_cases"] = {r: {"rib_long": out[r]["rib_worst_long_term"], "rib_short": out[r]["rib_worst_short_term"]} for r in ("15x10", "10x10")}
json.dump(T, open(KM, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(json.dumps({r: {k: out[r][k] for k in ("rib_worst_long_term", "rib_worst_short_term", "deflection_mm", "buckling_factor_1", "footing", "weight_LONG_kN")} for r in ("15x10", "10x10")}, indent=0))
print(json.dumps({r: {k: out[r][k] for k in ("base_ring", "crown_ring", "columns")} for r in ("15x10", "10x10")}))
