"""Variant D summary from formwork/forces-<roof>-<D1|D2>.json (k_variant_D.py): one reduced model per load case
(fins as compression-only trusses via Karamba TenComElim). Same section checks as formwork_report.py. Also the shear at
the tube-core interface: at each rib node, the force the printed pieces (courses + fins) put into the rib, its component
along the rib axis, spread over the rib length that node serves, over the core perimeter (= inner tube surface)."""
import os, sys, json, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rib_path as R
LONGS = ["LONG", "LIVEX", "LIVEY"]; SHORTS = ["W+Y", "W-Y", "W+X", "W-X", "W45", "EQX", "EQY"]; LCS = LONGS + SHORTS
RIB_D = {"15x10": {"rib_bottom": 0.22, "rib_middle": 0.16, "rib_top": 0.12}, "10x10": {"rib_bottom": 0.18, "rib_middle": 0.14, "rib_top": 0.12}}
RIBS = list(RIB_D["15x10"])


def load(roof, v):
    """BeamForces of a reduced model list only the active elements, in model order: spread them back onto all elements
    (removed elements get zero forces)"""
    J = json.load(open(os.path.join(HERE, "formwork", "forces-%s-%s.json" % (roof, v))))
    n = len(J["els"])
    for lc, c in J["cases"].items():
        act = c["active"]; ids = [i for i in range(n) if act[i]]
        assert len(c["forces"]["N"]) == 2 * len(ids), (lc, len(c["forces"]["N"]), len(ids))
        for k, arr in list(c["forces"].items()):
            full = [0.0] * (2 * n)
            for j, i in enumerate(ids):
                full[2 * i] = arr[2 * j]; full[2 * i + 1] = arr[2 * j + 1]
            c["forces"][k] = full
    return J


def end_force(J, F, i, n):
    g, a, b = J["els"][i]; ex, ey, ez = R.axes(J["nodes"][a], J["nodes"][b]); t = 0 if n == a else 1
    f = R.add(R.add(R.mul(ex, F["N"][2 * i + t]), R.mul(ey, F["Vy"][2 * i + t])), R.mul(ez, F["Vz"][2 * i + t]))
    return R.mul(f, 1 if t == 0 else -1)


def summary(roof, v):
    J = load(roof, v); E = J["els"]; N = J["nodes"]; C = J["cases"]
    idx = {}
    for i, (g, a, b) in enumerate(E): idx.setdefault(g, []).append(i)
    at = {}
    for i, (g, a, b) in enumerate(E): at.setdefault(a, []).append(i); at.setdefault(b, []).append(i)
    rib_long = (0, None, None); rib_short = (0, None, None)
    for lc in LCS:
        F = C[lc]["forces"]; al = 12.0 if lc in LONGS else 24.0
        for g in RIBS:
            dm = RIB_D[roof][g]; A = math.pi * dm * dm / 4; W = math.pi * dm ** 3 / 32
            for i in idx[g]:
                for t in (0, 1):
                    u = (-F["N"][2 * i + t] / A + math.hypot(F["My"][2 * i + t], F["Mz"][2 * i + t]) / W) / 1000.0 / al
                    if lc in LONGS and u > rib_long[0]: rib_long = (u, g, lc)
                    if lc in SHORTS and u > rib_short[0]: rib_short = (u, g, lc)
    fins_out = {lc: sum(1 for i in idx["fin"] if not C[lc]["active"][i]) for lc in LCS}
    fin_tension_left = {lc: round(max([max(C[lc]["forces"]["N"][2 * i], C[lc]["forces"]["N"][2 * i + 1]) for i in idx["fin"] if C[lc]["active"][i]] or [0]), 3) for lc in LCS}
    cs = J["crosec"]
    def maxcomp(g):
        best = (0, None); A, Wy, Wz = cs[g]["A"], cs[g]["Wy"], cs[g]["Wz"]
        for lc in LCS:
            F = C[lc]["forces"]
            for i in idx[g]:
                if not C[lc]["active"][i]: continue
                for t in (0, 1):
                    m = 0 if g == "fin" else abs(F["My"][2 * i + t]) / Wy + abs(F["Mz"][2 * i + t]) / Wz
                    sc = (-F["N"][2 * i + t] / A + m) / 1000.0
                    if sc > best[0]: best = (sc, lc)
        return {"MPa": round(best[0], 2), "case": best[1]}
    def maxten_course():
        best = (0, None); A, Wy, Wz = cs["course"]["A"], cs["course"]["Wy"], cs["course"]["Wz"]
        for lc in LCS:
            F = C[lc]["forces"]
            for i in idx["course"]:
                for t in (0, 1):
                    st = (F["N"][2 * i + t] / A + abs(F["My"][2 * i + t]) / Wy + abs(F["Mz"][2 * i + t]) / Wz) / 1000.0
                    if st > best[0]: best = (st, lc)
        return {"MPa": round(best[0], 2), "case": best[1]}
    # vertical load into the base ring from ribs vs printed parts, LONG
    ring = {n for i in idx["ring"] for n in E[i][1:3]}
    share = {"ribs": 0.0, "courses_fins": 0.0}
    F = C["LONG"]["forces"]
    for i, (g, a, b) in enumerate(E):
        if g not in RIBS + ["course", "fin"] or not C["LONG"]["active"][i]: continue
        for n in (a, b):
            if n in ring:
                fz = -end_force(J, F, i, n)[2]            # force the member puts DOWN on the ring node
                share["ribs" if g in RIBS else "courses_fins"] += fz
    tot = share["ribs"] + share["courses_fins"]
    # tube-core interface shear
    iface = {}
    for lc in LCS:
        F = C[lc]["forces"]
        for n, bars in at.items():
            ribs = [i for i in bars if E[i][0] in RIBS]
            if len(ribs) < 2: continue
            pieces = [i for i in bars if E[i][0] in ("course", "fin") and C[lc]["active"][i]]
            if not pieces: continue
            tsum = [0, 0, 0]; Ls = []
            for i in ribs:
                g, a, b = E[i]; o = b if a == n else a; d = R.sub(N[o], N[n]); L = R.norm(d); Ls.append(L)
                u = R.unit(d);  u = u if u[2] >= 0 else R.mul(u, -1); tsum = R.add(tsum, u)
            tax = R.unit(tsum)
            f = [0, 0, 0]
            for i in pieces: f = R.add(f, end_force(J, F, i, n))
            fpar = abs(R.dot(f, tax)); ftot = R.norm(f)
            trib = sum(Ls) / len(ribs)                      # 2 bars: half of each; Y-joint: mean bar length
            g = max((E[i][0] for i in ribs), key=lambda gg: RIB_D[roof][gg]); D = RIB_D[roof][g]
            tau = fpar / (trib * math.pi * D) / 1000.0; taut = ftot / (trib * math.pi * D) / 1000.0
            k = iface.get(g)
            if k is None or tau > k["tau_long_MPa"]:
                iface[g] = {"tau_long_MPa": round(tau, 3), "tau_total_MPa": round(taut, 3), "kN_per_m_along": round(fpar / trib, 2), "case": lc, "node": n,
                            "util_smooth_0.5MPa": round(tau / 0.5, 2), "util_keyed_1.0MPa": round(tau / 1.0, 2)}
    disp = max(C[lc]["maxdisp_cm"] for lc in LCS) * 10
    r = {"rib_long": {"util": round(rib_long[0], 3), "band": rib_long[1], "case": rib_long[2]},
         "rib_short": {"util": round(rib_short[0], 3), "band": rib_short[1], "case": rib_short[2]},
         "max_deflection_mm": round(disp, 1), "deflection_case": max(LCS, key=lambda lc: C[lc]["maxdisp_cm"]),
         "buckling_factor_1_LONG_model": round(C["LONG"]["buckling"][0], 2) if C["LONG"]["buckling"] else None,
         "vertical_reaction_LONG_kN": round(sum(f[2] for f in C["LONG"]["RF"]), 1),
         "base_share_LONG": {k: round(v, 1) for k, v in share.items()} | {"courses_fins_share": round(share["courses_fins"] / tot, 3) if tot else None},
         "fins_total": len(idx["fin"]), "fins_dropped_in_tension": fins_out,
         "max_axial_N_in_remaining_fins_kN": fin_tension_left,
         "fins_max_compression": maxcomp("fin"), "courses_max_compression": maxcomp("course"),
         "courses_max_tension_along_hoop": maxten_course(),
         "tube_core_interface": iface}
    return r


if __name__ == "__main__":
    out = {"method": ("Variant D: variant C (printed courses and fins E = 25 GPa, tied to the ribs at the tube) with the fins - the "
                      "members that cross the bed joints - as pin-ended trusses (Karamba Create Linear Element, Bending = False) and "
                      "compression-only through Karamba 3.1 'Tension/Compression Eliminator' (6.Algorithms, Compr = True, BeamIds = fin, "
                      "MaxIter 20), run separately for each of the 10 load cases. In B/C the bed-joint tension came from fin bending, "
                      "their axial force was compression; making them trusses removes that bending. Head joints along a course "
                      "cannot be isolated in this model, so the hoops are bracketed: D1 courses full E, D2 courses E x 0.02. "
                      "Allowables Fc36 12 / 24 MPa. Interface shear = force from the printed pieces along the rib axis per metre of "
                      "rib, over the core perimeter; compared with 0.5 MPa (smooth printed tube) and 1.0 MPa (keyed / rough tube)."),
           "results": {}}
    for roof in ("15x10", "10x10"):
        for v in ("D1", "D2"):
            out["results"]["%s %s" % (roof, v)] = summary(roof, v)
    p = os.path.join(HERE, "formwork", "variant-D.json")
    json.dump(out, open(p, "w"), indent=1)
    for k, r in out["results"].items():
        print(k, "ribs L %.0f%% %s %s | S %.0f%% %s %s | defl %.1f mm %s | buck %s | Rz %.0f | share %s" % (
            100 * r["rib_long"]["util"], r["rib_long"]["band"], r["rib_long"]["case"], 100 * r["rib_short"]["util"], r["rib_short"]["band"], r["rib_short"]["case"],
            r["max_deflection_mm"], r["deflection_case"], r["buckling_factor_1_LONG_model"], r["vertical_reaction_LONG_kN"], r["base_share_LONG"]))
        print("   fins out", r["fins_dropped_in_tension"], "left max N", max(r["max_axial_N_in_remaining_fins_kN"].values()))
        print("   fin comp", r["fins_max_compression"], "course comp", r["courses_max_compression"], "course ten", r["courses_max_tension_along_hoop"])
        print("   iface", r["tube_core_interface"])
