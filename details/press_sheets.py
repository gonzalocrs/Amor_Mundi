"""Stepped roofs v3e on the midterm press layout ("10.20.26 midterm press.pdf", ref page 02): 17 x 11 in landscape,
Arial, no frame or title panel. Header "STRUCTURAL ANALYSIS" + full-width rule; numbered heading + one-line
description; two columns (thin vertical divider) with "A · ..." headings; drawings with bold caps titles + scale under
them; dash notes beside the plan; scale bar 0-1-2-5 m bottom right of each column.
Drawings come from stepped_sheets.py (same linework, faint ribs, even cut steps), placed with stepped_sheets.PLACE.
Usage: python details/press_sheets.py <outdir>  -> NN-*.svg/.html/.pdf (PDF via headless Edge, vector, live text)."""
import os, sys, json, subprocess, time
import stepped_sheets as ss
import pyramid_drawings as pd

W, H = 431.8, 279.4                  # 17 x 11 in
SCALE = 150                          # same on every sheet (1:125 does not fit the 15x10 plan + section in a column)
COLX = (16.0, W / 2 + 8.0)           # column left edges
COLW = W / 2 - 24.0
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
FONT = "Arial, Helvetica, sans-serif"


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class Page:
    def __init__(self, no, title, desc):
        self.no, self.title, self.desc = no, title, desc
        self.o = []

    def text(self, x, y, s, size, bold=False, italic=False, anchor="start", color="#000"):
        self.o.append('<text x="{:.2f}" y="{:.2f}" font-size="{}" font-weight="{}" font-style="{}" text-anchor="{}" fill="{}">{}</text>'.format(
            x, y, size, "bold" if bold else "normal", "italic" if italic else "normal", anchor, color, esc(s)))

    def line(self, x1, y1, x2, y2, w=0.25, color="#000"):
        self.o.append('<line x1="{:.2f}" y1="{:.2f}" x2="{:.2f}" y2="{:.2f}" stroke="{}" stroke-width="{}"/>'.format(x1, y1, x2, y2, color, w))

    def header(self):
        self.text(16, 19, "STRUCTURAL ANALYSIS", 8.2, bold=True)
        self.line(6, 26.5, W - 2, 26.5, 0.45)
        self.text(17, 41, self.no, 6.4, bold=True)
        self.text(29, 41, self.title.upper(), 6.4, bold=True)
        self.text(29, 48.5, self.desc, 2.9)

    def column(self, i, head, sub):
        x = COLX[i]
        self.text(x + 1, 59, head, 4.0, bold=True)
        w = len(head) * 2.45 + 4
        self.text(x + 1 + w, 59, sub, 3.0, italic=True)
        if i == 1:
            self.line(W / 2, 54, W / 2, H - 14, 0.25)

    def title_under(self, x, y, t):
        self.text(x, y, t.upper(), 3.0, bold=True)

    def notes(self, x, y, items, width=46):
        for it in items:
            lines = pd.wrap(it, width)
            self.text(x, y, "–", 2.9)
            for k, l in enumerate(lines):
                self.text(x + 4.5, y + k * 3.9, l, 2.9)
            y += 3.9 * len(lines) + 2.6
        return y

    def scalebar(self, xr, y):
        """0-1-2-5 m bar ending at xr (as on the midterm sheets)"""
        s = 1000.0 / SCALE                 # mm on paper per m
        x0 = xr - 5 * s
        for a, b, f in ((0, 1, "#000"), (1, 2, "#fff"), (2, 5, "#000")):
            self.o.append('<rect x="{:.2f}" y="{:.2f}" width="{:.2f}" height="1.4" fill="{}" stroke="#000" stroke-width="0.2"/>'.format(x0 + a * s, y, (b - a) * s, f))
        for v in (0, 1, 2, 5):
            self.text(x0 + v * s, y + 4.6, str(v), 2.3, anchor="middle")
        self.text(xr + 2.5, y + 0.9, "m", 2.3)

    def add_view(self, sh):
        self.o.append("<g>" + "".join(sh.o) + "</g>")

    def svg(self):
        defs = ('<defs>'
                '<pattern id="conc" width="1.6" height="1.6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="1.6" stroke="#000" stroke-width="0.14"/></pattern>'
                '<pattern id="earth" width="2.4" height="2.4" patternUnits="userSpaceOnUse" patternTransform="rotate(-45)"><line x1="0" y1="0" x2="0" y2="2.4" stroke="#777" stroke-width="0.12"/></pattern>'
                '<pattern id="cast" width="1.6" height="1.6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="1.6" stroke="#000" stroke-width="0.14"/><line x1="0" y1="0" x2="1.6" y2="0" stroke="#000" stroke-width="0.14"/></pattern>'
                '</defs>')
        return ('<svg xmlns="http://www.w3.org/2000/svg" width="{w}mm" height="{h}mm" viewBox="0 0 {w} {h}" font-family="{f}">'
                '{d}<rect width="{w}" height="{h}" fill="#fff"/>{b}</svg>').format(w=W, h=H, f=FONT, d=defs, b="".join(self.o))


def place(scale, cx, cy):
    ss.PLACE = (scale, cx, cy)


def view(fn, roof, cx, cy):
    place(SCALE, cx, cy)
    sh = fn(roof)
    ss.PLACE = None
    return sh


def roof_cols(D):
    return {r: json.load(open(ss.LINEWORK.format(r))) for r in ("15x10", "10x10")}


def sheet_plans_sections(no):
    pg = Page(no, "Plans and sections", "Both stepped modules on the same drawings. Plans cut at +1.20 looking down; sections on the long axis, 10 cm north of the centre line (clear of the piece joints), looking north. Rebuilt model: approved printed pieces, each with its growth band; ribs as pipes on the room face.")
    pg.header()
    lv = {r: json.load(open(ss.LINEWORK.format(r)))["levels"] for r in ("15x10", "10x10")}
    for i, (roof, head, sub) in enumerate((("15x10", "15 x 10 · STEPPED", "18 printed courses + crown ring course, 19 columns"),
                                           ("10x10", "10 x 10 · STEPPED", "10 printed courses + crown ring course, 15 columns"))):
        x = COLX[i]
        pg.column(i, head, sub)
        cxp = x + 62
        pg.add_view(view(ss.plan, roof, cxp, 103))
        pg.title_under(x + 1, 150, "Roof plan, cut at +1.20 1:%d" % SCALE)
        notes = ["Rib net on the room face (faint): printed tubes with the cast cores inside, continuous from the base ring to the crown ring.",
                 "Base ring step +2.40 to +2.80 (dashed above), crown opening and crown ring at +%.2f." % lv[roof]["crown_top"],
                 "Columns cut (crossed hatch); strip footing frame below ground (thin dashed)."]
        pg.notes(x + 132, 78, notes, 40)
        pg.add_view(view(ss.section, roof, cxp, 210))
        pg.title_under(x + 1, 263, "Section A-A 1:%d" % SCALE)
        pg.scalebar(x + COLW - 6, 258)
    return pg


def sheet_elevations(no):
    pg = Page(no, "Elevations", "Long sides, looking north. Visible lines only (Make2D from the rebuilt model). Courses drawn as bands (step edges only; the 2 mm joints between pieces are not shown). Every step covers the groove below and the ribs by 1 cm.")
    pg.header()
    for i, (roof, head, sub) in enumerate((("15x10", "15 x 10 · STEPPED", "long side"), ("10x10", "10 x 10 · STEPPED", "long side"))):
        x = COLX[i]
        pg.column(i, head, sub)
        pg.add_view(view(ss.elevation, roof, x + 70, 150))
        pg.title_under(x + 1, 263, "Elevation, looking north 1:%d" % SCALE)
        pg.scalebar(x + COLW - 6, 258)
    return pg


def sheet_axon(no):
    pg = Page(no, "Axonometric and worm's-eye", "Both modules together, parallel projections from the rebuilt model (Make2D, hidden lines removed). Ribs faint in the axonometric; in the worm's-eye view the rib net is the subject.")
    pg.header()
    for i, (name, head, sub, t) in enumerate((("iso", "A · AXONOMETRIC", "from the south-east, above", "Axonometric from the south-east"),
                                              ("worm", "B · WORM'S-EYE", "from below, looking up into the roofs", "Worm's-eye view from below"))):
        x = COLX[i]
        pg.column(i, head, sub)
        sh = ss.axon(name)                # drawn at 1:125 for the A3 sheet; re-place it in the column at the same scale
        d = json.load(open(ss.AXON.format(name)))["visible"]
        x0, y0, x1, y1 = ss.ext(d)
        need = max((x1 - x0) / (COLW - 6), (y1 - y0) / 185.0)          # ext() is in mm
        scl = next(v for v in (150, 175, 200, 250, 300, 400) if v >= need)
        s = 1.0 / scl
        sh2 = ss.StepSheet(scl, x + COLW / 2 - (x0 + x1) / 2 * s, 160 + (y0 + y1) / 2 * s, "", "", [], [], W, H)
        pieces = [it for it in d if it["layer"] in ("printed pieces", "top course U formwork")]
        rib = [it for it in d if it["layer"] == "ribs"]
        other = [it for it in d if it["layer"] not in ("printed pieces", "top course U formwork", "ribs")]
        if name == "iso":
            ss.lines(sh2, pieces, 0.12, "#000"); ss.lines(sh2, other, 0.2, "#000"); ss.lines(sh2, rib, 0.12, "#7a7a7a")
        else:
            ss.lines(sh2, pieces, 0.07, "#a0a0a0"); ss.lines(sh2, other, 0.2, "#000"); ss.lines(sh2, rib, 0.16, "#222")
        pg.add_view(sh2)
        pg.title_under(x + 1, 263, t + " (parallel projection, not to scale)")
    return pg


def sheet_topbottom(no):
    pg = Page(no, "Roof from above and below", "Both roofs seen straight from above (stepped courses, crown opening) and straight from below (rib net on the room face, base ring, column heads). Parallel projections, hidden lines removed, from the rebuilt model.")
    pg.header()
    TB = os.path.join(ss.HERE, "..", "polyframe2", "drawings-2026-11-20", "_tmp_{}_topbottom.json")
    for i, (roof, head, sub) in enumerate((("15x10", "15 x 10 · STEPPED", "roof only"), ("10x10", "10 x 10 · STEPPED", "roof only"))):
        x = COLX[i]
        pg.column(i, head, sub)
        d = json.load(open(TB.format(roof)))
        for key, cy, t in (("top", 112, "Roof from above 1:%d" % SCALE), ("bottom", 207, "Roof from below (seen from below, mirrored) 1:%d" % SCALE)):
            items = d[key]
            x0, y0, x1, y1 = ss.ext(items)
            s = 1.0 / SCALE
            sh = ss.StepSheet(SCALE, x + COLW / 2 - (x0 + x1) / 2 * s, cy + (y0 + y1) / 2 * s, "", "", [], [], W, H)
            pieces = [it for it in items if it["layer"] in ("printed pieces", "top course U formwork")]
            rib = [it for it in items if it["layer"] == "ribs"]
            other = [it for it in items if it["layer"] not in ("printed pieces", "top course U formwork", "ribs")]
            if key == "top":
                ss.lines(sh, pieces, 0.12, "#000"); ss.lines(sh, other, 0.22, "#000")
            else:
                ss.lines(sh, pieces, 0.07, "#a0a0a0"); ss.lines(sh, other, 0.22, "#000"); ss.lines(sh, rib, 0.16, "#222")
            pg.add_view(sh)
            pg.title_under(x + 1, cy + (y1 - y0) / 2 * s + 9, t)
        pg.scalebar(x + COLW - 6, 258)
    return pg


SHEETS = [("04", "stepped-plans-and-sections", sheet_plans_sections),
          ("05", "stepped-elevations", sheet_elevations),
          ("06", "stepped-axonometric-and-wormseye", sheet_axon),
          ("07", "stepped-roof-from-above-and-below", sheet_topbottom)]


def build(outdir, only=None):
    os.makedirs(outdir, exist_ok=True)
    out = []
    for no, name, fn in SHEETS:
        if only and name not in only:
            continue
        pg = fn(no)
        base = os.path.join(outdir, "%s-%s" % (no, name))
        open(base + ".svg", "w", encoding="utf-8").write(pg.svg())
        html = ('<!doctype html><html><head><meta charset="utf-8"><style>@page{size:17in 11in;margin:0}html,body{margin:0}'
                'svg{display:block;width:17in;height:11in}</style></head><body>%s</body></html>' % pg.svg())
        open(base + ".html", "w", encoding="utf-8").write(html)
        url = "file:///" + (base + ".html").replace("\\", "/")
        subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--print-to-pdf=" + base + ".pdf", url],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=180)
        subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--window-size=2448,1584",
                        "--force-device-scale-factor=1", "--screenshot=" + base + ".png",
                        "file:///" + (base + "-png.html").replace("\\", "/")] if False else
                       [EDGE, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--window-size=1632,1056", "--screenshot=" + base + ".png", url],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=180)
        out.append(base)
    return out


if __name__ == "__main__":
    od = sys.argv[1]
    only = sys.argv[2:] or None
    for b in build(od, only):
        print(b)
