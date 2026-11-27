"""One rib of the 15x10 2 m Karamba model, followed from the base ring to the crown ring (Gonzalo 2026-11-24:
'grab a rib and let's analyse, with a section if possible, it's branched').
Path: the bottom-band rib bar with the highest utilisation (LONG / 12 MPa or W-Y / 24 MPa, worst fibre -N/A + M/W),
extended down to its ring node and up to the crown; at every Y-joint the branch that continues straightest (smallest
angle change) is kept. Input forces-15x10.json (design model D2, k_dump_D2.py; per load case). Output rib-path-15x10.json.

Karamba local axes (beams): x along the bar from its first to its second node; z in the vertical plane through the bar,
pointing up (projection of global Z normal to x); y = z cross x, horizontal. For a rib lying in the roof surface,
local z is the OUT-OF-PLANE (room-normal side, roughly normal to the roof) direction and local y lies in the roof
surface: My (about y) is out-of-plane bending, Mz (about z) in-plane bending.
Force a bar delivers to a node: at its first node +(N x + Vy y + Vz z), at its second node -(N x + Vy y + Vz z)
(Karamba section forces act on the positive cut face); checked below by horizontal equilibrium at free rib nodes."""
import os, json, math
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "rib-path")
RIB_D = {"rib_bottom": 0.22, "rib_middle": 0.16, "rib_top": 0.12}
BAND = {"rib_bottom": "bottom", "rib_middle": "middle", "rib_top": "top"}
CASES = {"LONG": 12.0, "W-Y": 24.0}
GAMMA = 24.0


def sub(a, b): return [a[i] - b[i] for i in range(3)]
def add(a, b): return [a[i] + b[i] for i in range(3)]
def mul(a, k): return [x * k for x in a]
def dot(a, b): return sum(a[i] * b[i] for i in range(3))
def cross(a, b): return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]
def norm(a): return math.sqrt(dot(a, a))
def unit(a): n = norm(a); return [x / n for x in a]


def axes(pa, pb):
    ex = unit(sub(pb, pa))
    if abs(ex[2]) > 0.999:                                   # vertical bar (columns): Karamba takes z along global -X
        ez = [-1.0, 0.0, 0.0]
    else:
        ez = unit(sub([0, 0, 1], mul(ex, ex[2])))
    ey = cross(ez, ex)
    return ex, ey, ez


def main():
    os.makedirs(OUT, exist_ok=True)
    D = json.load(open(os.path.join(HERE, "forces-15x10.json")))
    N, E, F = D["nodes"], D["els"], D["forces"]
    at = {}
    for i, (g, a, b) in enumerate(E):
        at.setdefault(a, []).append(i); at.setdefault(b, []).append(i)
    ring_nodes = {n for i, (g, a, b) in enumerate(E) if g == "ring" for n in (a, b)}
    crown_nodes = {n for i, (g, a, b) in enumerate(E) if g == "crown" for n in (a, b)}
    rib = lambda i: E[i][0] in RIB_D

    def bar_stress(i, lc):
        g = E[i][0]; dm = RIB_D[g]; A = math.pi * dm * dm / 4; W = math.pi * dm ** 3 / 32; out = []
        for t in (0, 1):
            n = F[lc]["N"][2 * i + t]; m = math.hypot(F[lc]["My"][2 * i + t], F[lc]["Mz"][2 * i + t])
            out.append(((-n / A + m / W) / 1000.0, (-n / A - m / W) / 1000.0))
        return out

    def util(i):
        return max(max(s[0] for s in bar_stress(i, lc)) / al for lc, al in CASES.items())

    start = max((i for i, e in enumerate(E) if e[0] == "rib_bottom"), key=util)
    a, b = E[start][1], E[start][2]
    lo, hi = (a, b) if N[a][2] < N[b][2] else (b, a)

    def walk(node, came, direction, stop):
        """follow ribs from node, away from bar 'came', up (direction=+1) or down (-1), straightest branch"""
        bars, nodes = [], [node]
        d0 = unit(sub(N[node], N[E[came][1] if E[came][2] == node else E[came][2]]))
        while node not in stop:
            cand = [j for j in at[node] if rib(j) and j != came]
            cand = [j for j in cand if (N[E[j][1] if E[j][2] == node else E[j][2]][2] - N[node][2]) * direction > 0]
            if not cand: break
            def turn(j):
                o = E[j][1] if E[j][2] == node else E[j][2]
                return -dot(unit(sub(N[o], N[node])), d0)
            j = min(cand, key=turn)
            o = E[j][1] if E[j][2] == node else E[j][2]
            d0 = unit(sub(N[o], N[node])); bars.append(j); nodes.append(o); came = j; node = o
        return bars, nodes

    down_bars, down_nodes = walk(lo, start, -1, ring_nodes)
    up_bars, up_nodes = walk(hi, start, +1, crown_nodes)
    path_nodes = list(reversed(down_nodes)) + up_nodes            # ring ... lo, hi ... crown
    path_bars = list(reversed(down_bars)) + [start] + up_bars
    pset = set(path_bars)

    def end_force(i, node, lc):
        g, a, b = E[i]; ex, ey, ez = axes(N[a], N[b]); t = 0 if node == a else 1
        f = add(add(mul(ex, F[lc]["N"][2 * i + t]), mul(ey, F[lc]["Vy"][2 * i + t])), mul(ez, F[lc]["Vz"][2 * i + t]))
        m = add(add(mul(ex, F[lc]["Mt"][2 * i + t]), mul(ey, F[lc]["My"][2 * i + t])), mul(ez, F[lc]["Mz"][2 * i + t]))
        s = 1 if t == 0 else -1
        return mul(f, s), mul(m, s)

    # sign check: horizontal resultant of all bar forces at free rib nodes should be ~0 under LONG (gravity loads only)
    res = []
    for n in path_nodes[1:-1]:
        tot = [0, 0, 0]
        for i in at[n]: tot = add(tot, end_force(i, n, "LONG")[0])
        res.append(math.hypot(tot[0], tot[1]))
    check = {"max_horizontal_residual_kN_LONG": round(max(res), 3) if res else None,
             "note": "sum of all bar end forces at each free path node under LONG; gravity point loads are vertical, so the horizontal part should be ~0"}

    s = 0.0; nodes_out = []
    for k, n in enumerate(path_nodes):
        if k: s += math.dist(N[path_nodes[k - 1]], N[n])
        ribs_here = [i for i in at[n] if rib(i)]
        below = path_bars[k - 1] if k else None; above = path_bars[k] if k < len(path_bars) else None
        g = E[above][0] if above is not None else E[below][0]
        rec = {"index": k, "node": n, "xyz": N[n], "s_m": round(s, 3), "band": BAND[g], "core_D_mm": int(RIB_D[g] * 1000),
               "y_joint": len(ribs_here) >= 3, "ribs_meeting": len(ribs_here),
               "on_base_ring": n in ring_nodes, "on_crown_ring": n in crown_nodes, "delivered": {}}
        for lc in CASES:
            others = {}
            for i in at[n]:
                if i in pset: continue
                f, m = end_force(i, n, lc)
                key = {"rib_bottom": "branch_rib", "rib_middle": "branch_rib", "rib_top": "branch_rib"}.get(E[i][0], E[i][0])
                o = others.setdefault(key, {"F_kN": [0, 0, 0], "M_kNm": [0, 0, 0], "bars": []})
                o["F_kN"] = add(o["F_kN"], f); o["M_kNm"] = add(o["M_kNm"], m); o["bars"].append(i)
            for o in others.values():
                o["F_kN"] = [round(x, 2) for x in o["F_kN"]]; o["M_kNm"] = [round(x, 2) for x in o["M_kNm"]]
            rec["delivered"][lc] = others
        nodes_out.append(rec)

    bars_out = []
    for k, i in enumerate(path_bars):
        g, a, b = E[i]; dm = RIB_D[g]; A = math.pi * dm * dm / 4; L = math.dist(N[a], N[b])
        ex, ey, ez = axes(N[a], N[b])
        r = {"index": k, "element": i, "band": BAND[g], "core_D_mm": int(dm * 1000), "length_m": round(L, 3),
             "from_node": path_nodes[k], "to_node": path_nodes[k + 1], "karamba_first_node": a,
             "self_weight_kN": round(GAMMA * A * L, 3), "local_axes": {"x": [round(v, 3) for v in ex], "y": [round(v, 3) for v in ey], "z": [round(v, 3) for v in ez]},
             "cases": {}}
        for lc, al in CASES.items():
            ends = []
            st = bar_stress(i, lc)
            for t in (0, 1):
                ends.append({"node": (a, b)[t], **{kk: round(F[lc][kk][2 * i + t], 2) for kk in ("N", "Vy", "Vz", "Mt", "My", "Mz")},
                             "sigma_c_MPa": round(st[t][0], 2), "sigma_t_MPa": round(st[t][1], 2)})
            r["cases"][lc] = {"ends": ends, "worst_compression_MPa": round(max(x[0] for x in st), 2),
                              "worst_tension_MPa": round(min(x[1] for x in st), 2), "utilisation": round(max(x[0] for x in st) / al, 3), "allowable_MPa": al}
        bars_out.append(r)

    def sum_from(n, groups, lc):
        tot = [0, 0, 0]
        for i in at[n]:
            if E[i][0] in groups: tot = add(tot, end_force(i, n, lc)[0])
        return [round(x, 2) for x in tot]
    ring_n, crown_n = path_nodes[0], path_nodes[-1]
    out = {"roof": "15x10", "model": "Karamba 2 m canvas, design model D2 (pieces tied to the ribs, bed joints compression-only, head joints open), forces-15x10.json",
           "path_rule": "start = most utilised bottom-band rib bar (LONG/12 or W-Y/24); down to the base ring and up to the crown ring, at each Y-joint keeping the straightest branch",
           "start_bar": start, "start_bar_utilisation": round(util(start), 3),
           "local_axes": "x along the bar (first -> second Karamba node); z in the vertical plane through the bar, up = OUT-OF-PLANE / room-normal side of the roof; y = z x x, horizontal, in the roof surface. My = out-of-plane bending, Mz = in-plane bending.",
           "sign": "N + tension; forces delivered to a node = +S at a bar's first node, -S at its second node (S = N x + Vy y + Vz z)",
           "equilibrium_check": check,
           "ring_node": {"node": ring_n, "xyz": N[ring_n],
                         "support_from_ring_columns_arches_kN": {lc: sum_from(ring_n, ("ring", "arch", "column"), lc) for lc in CASES}},
           "crown_node": {"node": crown_n, "xyz": N[crown_n], "force_from_crown_ring_kN": {lc: sum_from(crown_n, ("crown",), lc) for lc in CASES}},
           "nodes": nodes_out, "bars": bars_out,
           "rib_self_weight_total_kN": round(sum(b["self_weight_kN"] for b in bars_out), 2),
           "path_length_m": nodes_out[-1]["s_m"]}
    json.dump(out, open(os.path.join(OUT, "rib-path-15x10.json"), "w"), indent=1)
    return out


if __name__ == "__main__":
    o = main()
    print("start bar", o["start_bar"], o["start_bar_utilisation"], "nodes", len(o["nodes"]), "bars", len(o["bars"]), "L", o["path_length_m"], o["equilibrium_check"])
    for b in o["bars"]:
        print(b["index"], b["band"], b["length_m"], {lc: (c["utilisation"], c["ends"][0]["My"], c["ends"][1]["My"]) for lc, c in b["cases"].items()})
    print(o["ring_node"], o["crown_node"])
    print([(n["index"], n["y_joint"], list(n["delivered"]["LONG"].keys())) for n in o["nodes"]])
