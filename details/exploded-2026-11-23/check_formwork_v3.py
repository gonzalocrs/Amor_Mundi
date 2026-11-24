import json, os, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
D = json.load(open(os.path.join(HERE, "exploded-15x10-formwork-v3.json")))
xs = [p[0] for it in D["items"] for p in it["pts"]]; ys = [p[1] for it in D["items"] for p in it["pts"]]
x0, x1, y0, y1 = min(xs) - 1, max(xs) + 14, min(ys) - 1, max(ys) + 1
s = 1600 / (x1 - x0); Wp, Hp = 1600, int((y1 - y0) * s)
out = []
LAB = {"rectangular strip footing": "RECTANGULAR STRIP FOOTING", "columns": "COLUMNS", "base ring step": "BASE RING STEP", "rib rebar": "RIB REBAR",
       "printed formwork": "PRINTED FORMWORK (pieces + rib tubes, 4 faces)", "crown ring": "CROWN RING"}
for it in D["items"]:
    lay = it["layer"]
    c, w = ("#b03a2e", 0.6) if lay == "rib rebar" else (("#222", 0.45) if lay.startswith("printed") else ("#000", 0.6))
    pts = " ".join("%.1f,%.1f" % ((p[0] - x0) * s, (y1 - p[1]) * s) for p in it["pts"])
    out.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="%s" stroke-linecap="round"/>' % (pts, c, w))
xl = (max(xs) + 1.0 - x0) * s
for g, (ax, ay) in D["anchors"].items():
    X, Y = (ax - x0) * s, (y1 - ay) * s
    out.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#555" stroke-width="0.8"/><circle cx="%.1f" cy="%.1f" r="2.5" fill="#000"/>'
               '<text x="%.1f" y="%.1f" font-family="Arial" font-size="17" font-weight="bold">%s</text>' % (X, Y, xl, Y, X, Y, xl + 6, Y + 6, LAB.get(g, g)))
h = os.path.join(HERE, "check-exploded-15x10-formwork-v3.html")
open(h, "w").write('<html><body style="margin:0;background:#fff"><svg width="%d" height="%d" style="background:#fff">%s</svg></body></html>' % (Wp, Hp, "".join(out)))
subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--screenshot=" + h[:-5] + ".png", "--window-size=%d,%d" % (Wp, Hp), "file:///" + h.replace("\\", "/")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
print(Wp, Hp)
