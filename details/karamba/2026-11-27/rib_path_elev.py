"""Developed elevation of the 15x10 rib path: the rib unrolled into its own vertical plane (horizontal = distance along
the rib measured in plan, vertical = height), drawn twice (LONG, W-Y). The rib line is coloured by My, the out-of-plane
bending moment (Karamba local y), and the My diagram is drawn normal to the rib at the same scale in both panels.
Writes rib-path-15x10-elevation.svg (3200 x 2000); PNG via headless Edge."""
import os, json, math
HERE = os.path.dirname(os.path.abspath(__file__))
P = json.load(open(os.path.join(HERE, "rib-path", "rib-path-15x10.json")))
W, H = 3200, 2000


def col(v, vmax):
    t = max(-1, min(1, v / vmax))
    if t >= 0: return "rgb(%d,%d,%d)" % (255, int(255 - 220 * t), int(255 - 200 * t))      # + red
    t = -t; return "rgb(%d,%d,%d)" % (int(255 - 200 * t), int(255 - 170 * t), 255)         # - blue


def main():
    nodes = P["nodes"]; bars = P["bars"]
    u = [0.0]
    for k in range(1, len(nodes)):
        a, b = nodes[k - 1]["xyz"], nodes[k]["xyz"]; u.append(u[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    z = [n["xyz"][2] for n in nodes]
    vmax = max(abs(e["My"]) for b in bars for lc in ("LONG", "W-Y") for e in b["cases"][lc]["ends"])
    s = 120.0                                                       # px per m
    out = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" font-family="Arial">' % (W, H, W, H),
           '<rect width="100%" height="100%" fill="white"/>',
           '<text x="80" y="90" font-size="44" font-weight="bold">15x10 ROOF, ONE RIB FROM BASE RING TO CROWN, DEVELOPED ELEVATION</text>',
           '<text x="80" y="145" font-size="28">Rib unrolled into its own vertical plane: horizontal = distance along the rib in plan, vertical = height. Colour and diagram = My, out-of-plane bending (Karamba local y), kNm.</text>',
           '<text x="80" y="185" font-size="28">Karamba 2 m model, design model D2. Diagram scale: %.1f kNm = 1.5 m; colour full at half of that. Red = +My, blue = -My. Path length %.2f m; start bar = most utilised bottom-band rib (%.0f %%).</text>' % (vmax, P["path_length_m"], 100 * P["start_bar_utilisation"])]
    for p, lc in enumerate(("LONG", "W-Y")):
        ox = 140 + p * 1530; oy = 1820
        X = lambda uu: ox + uu * s; Y = lambda zz: oy - (zz - 2.0) * s
        out.append('<text x="%d" y="%d" font-size="34" font-weight="bold">%s</text>' % (ox, 300, {"LONG": "LONG (self-weight + finishes), long-term", "W-Y": "Typhoon W-Y, short-term"}[lc]))
        out.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#999" stroke-width="2"/>' % (X(-0.3), Y(2.4), X(u[-1] + 0.5), Y(2.4)))
        out.append('<text x="%d" y="%d" font-size="22" fill="#666">base ring +2.40</text>' % (X(u[-1] + 0.6) - 40, Y(2.4) + 32))
        out.append('<text x="%d" y="%d" font-size="22" fill="#666">crown +%.2f</text>' % (X(u[-1]) + 20, Y(z[-1]) + 8, z[-1]))
        for k, b in enumerate(bars):
            e0, e1 = b["cases"][lc]["ends"]
            m0, m1 = (e0["My"], e1["My"]) if e0["node"] == b["from_node"] else (e1["My"], e0["My"])
            x0, y0, x1, y1 = X(u[k]), Y(z[k]), X(u[k + 1]), Y(z[k + 1])
            L = math.hypot(x1 - x0, y1 - y0) or 1; nx, ny = -(y1 - y0) / L, (x1 - x0) / L        # left normal
            if ny > 0: nx, ny = -nx, -ny                                                        # normal pointing up/left
            k0, k1 = m0 / vmax * 1.5 * s, m1 / vmax * 1.5 * s
            out.append('<polygon points="%.1f,%.1f %.1f,%.1f %.1f,%.1f %.1f,%.1f" fill="%s" fill-opacity="0.55" stroke="#555" stroke-width="1"/>' % (
                x0, y0, x1, y1, x1 + nx * k1, y1 + ny * k1, x0 + nx * k0, y0 + ny * k0, col((m0 + m1) / 2, vmax / 2)))
            w = {"bottom": 16, "middle": 12, "top": 9}[b["band"]]
            out.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="%d" stroke-linecap="round"/>' % (x0, y0, x1, y1, col((m0 + m1) / 2, vmax / 2), w))
            out.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#222" stroke-width="3"/>' % (x0, y0, x1, y1))
        big = []
        for k, b in enumerate(bars):
            for e in b["cases"][lc]["ends"]:
                big.append((abs(e["My"]), e["My"], b, e))
        big.sort(key=lambda t: -t[0])
        for _, m, b, e in big[:2]:
            k = b["index"]; kk = k if e["node"] == b["from_node"] else k + 1
            out.append('<text x="%.0f" y="%.0f" font-size="24" font-weight="bold">My %+.1f kNm</text>' % (X(u[kk]) + 18, Y(z[kk]) + 8, m))
        for k, n in enumerate(nodes):
            if n["y_joint"]:
                out.append('<circle cx="%.1f" cy="%.1f" r="9" fill="white" stroke="#000" stroke-width="3"/>' % (X(u[k]), Y(z[k])))
        prev = None
        for k, b in enumerate(bars):
            if b["band"] != prev:
                out.append('<text x="%.0f" y="%.0f" font-size="22" fill="#333">%s band, core D%d</text>' % (X(u[k]) + 30, Y(z[k]) + 40, b["band"], b["core_D_mm"]))
                prev = b["band"]
        ut = max(b["cases"][lc]["utilisation"] for b in bars)
        out.append('<text x="%d" y="%d" font-size="26">max utilisation along the rib %.0f %% of %d MPa</text>' % (ox, 345, 100 * ut, {"LONG": 12, "W-Y": 24}[lc]))
    out.append('<circle cx="100" cy="1950" r="9" fill="white" stroke="#000" stroke-width="3"/><text x="120" y="1958" font-size="24">Y-joint (a branch leaves the path)</text>')
    out.append('</svg>')
    p = os.path.join(HERE, "rib-path", "rib-path-15x10-elevation.svg")
    open(p, "w", encoding="utf-8").write("\n".join(out))
    return p


if __name__ == "__main__":
    print(main())
