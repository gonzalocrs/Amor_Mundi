import json, os, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
D = json.load(open(os.path.join(HERE, "exploded-15x10-bricks.json")))
xs = [p[0] for it in D["items"] for p in it["pts"]]; ys = [p[1] for it in D["items"] for p in it["pts"]]
x0, x1, y0, y1 = min(xs) - 1, max(xs) + 7, min(ys) - 1, max(ys) + 1
s = 1400 / (x1 - x0); Wp, Hp = 1400, int((y1 - y0) * s)
out = []
for it in D["items"]:
    c = "#b03a2e" if it["layer"].startswith("rib") else ("#666" if it["layer"].startswith("printed") else "#000")
    pts = " ".join("%.1f,%.1f" % ((p[0] - x0) * s, (y1 - p[1]) * s) for p in it["pts"])
    out.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="0.5"/>' % (pts, c))
for g, (ax, ay) in D["anchors"].items():
    X, Y = (ax - x0) * s, (y1 - ay) * s
    out.append('<circle cx="%.1f" cy="%.1f" r="4" fill="#1f6feb"/><text x="%.1f" y="%.1f" font-family="Arial" font-size="22" fill="#1f6feb">%s</text>' % (X, Y, X + 8, Y + 7, g))
h = os.path.join(HERE, "check-exploded-15x10-bricks.html")
open(h, "w").write('<html><body style="margin:0;background:#fff"><svg width="%d" height="%d" style="background:#fff">%s</svg></body></html>' % (Wp, Hp, "".join(out)))
subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--screenshot=" + h[:-5] + ".png", "--window-size=%d,%d" % (Wp, Hp), "file:///" + h.replace("\\", "/")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
print(Wp, Hp, D["exploded_height_m"], D["groups"])
