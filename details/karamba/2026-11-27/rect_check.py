"""Hand check of the rectangular strip footing from the Karamba support reactions: each column on its share of strip
(perimeter / columns), moment across the strip resisted over (B/2 - offset of the column from the strip axis);
corner columns stand in the square corner block (block side as width, no offset). Bearing on the effective width."""
import json, math, os
import stress_pdf as s
HERE = os.path.dirname(os.path.abspath(__file__))
RR = json.load(open(os.path.join(HERE, "rect_result.json")))
# column centres of the FINAL model (2026-11-27: columns grown inward with the ring, outer face fixed)
LAY = json.load(open(os.path.join(HERE, "model_columns_final.json")))
CEN = {"15x10": (85.0, 0.0), "10x10": (85.0, -20.0)}


def check(roof, B, Df=0.8, tf=0.5, D=None):
    D = D or s.load(roof); R = RR[roof]; cx, cy = CEN[roof]
    per = 2 * (2 * R["xl"] + 2 * R["yl"]); n = len(D["reactions"]["LONG"]["RF"]); L = per / n
    sp = [p for p in D["nodes"] if abs(p[2]) < 1e-6]
    res = {}
    for lc in s.LCS:
        tip = 99; slide = 99; q = 0
        for (f, mm), p in zip(zip(D["reactions"][lc]["RF"], D["reactions"][lc]["RM"]), sp):
            x, y = p[0] - cx, p[1] - cy
            corner = abs(x) > 0.5 and abs(y) > 0.5 and abs(abs(x) - R["xl"]) > 0.3 and abs(abs(y) - R["yl"]) > 0.3
            if corner:
                b = min(R["block_m"]); off = 0.0; nx, ny = x / math.hypot(x, y), y / math.hypot(x, y); Ls = b
            elif abs(abs(x) - R["xl"]) < abs(abs(y) - R["yl"]):
                b = B; nx, ny = (1.0 if x > 0 else -1.0), 0.0; Ls = L
                col = min(LAY[roof]["cols"], key=lambda c: math.hypot(c["cx"] - p[0], c["cy"] - p[1])); off = abs(abs(col["cx"] - cx) - R["xl"])
            else:
                b = B; nx, ny = 0.0, (1.0 if y > 0 else -1.0); Ls = L
                col = min(LAY[roof]["cols"], key=lambda c: math.hypot(c["cx"] - p[0], c["cy"] - p[1])); off = abs(abs(col["cy"] - cy) - R["yl"])
            tx, ty = -ny, nx
            Ha = abs(f[0] * nx + f[1] * ny); Hl = abs(f[0] * tx + f[1] * ty)
            Ma = abs(mm[0] * tx + mm[1] * ty) + Ha * Df
            Ml = abs(mm[0] * nx + mm[1] * ny) + Hl * Df
            N = f[2] + 24 * b * tf * Ls + 18 * b * (Df - tf) * Ls
            Mo = Ma + N * off                                   # off-axis column: extra moment about the strip axis
            tip = min(tip, N * (b / 2) / Mo if Mo else 99, N * Ls / 2 / Ml if Ml else 99)
            slide = min(slide, 0.5 * N / math.hypot(f[0], f[1]))
            Bp, Lp = b - 2 * Mo / N, Ls - 2 * Ml / N
            q = max(q, N / (Bp * Lp) if Bp > 0 and Lp > 0 else 1e9)
        res[lc] = (q, tip, slide)
    return res, L


if __name__ == "__main__":
    for roof, B in (("15x10", 1.20), ("10x10", 0.85)):
        for b in (B, B + 0.1, B + 0.2):
            r, L = check(roof, b)
            print(roof, "B %.2f L %.2f" % (b, L), "tip %.2f" % min(v[1] for v in r.values()), "slide %.2f" % min(v[2] for v in r.values()),
                  "qL %.0f qS %.0f" % (max(r[l][0] for l in s.LONGS), max(r[l][0] for l in s.SHORTS)))
