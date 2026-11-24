"""S112-S115 on Gonzalo's deck size (17 x 11 in) with the title-block frame + info column on the right (2026-11-21):
no STRUCTURAL ANALYSIS header / rule / numbered heading / description; column headings, drawing titles with scale,
level marks, dimensions, short notes and scale bars kept; drawings as large as fit in the drawing area at a standard
scale (1:100, else 1:125), both modules at the same scale on a sheet. Reuses the existing linework (no new Make2D).
Usage: python details/deck_sheets.py <outdir> [area x0 y0 x1 y1 in mm]   -> S11x-*.svg/.html/.pdf/.png (drawings only;
the title block is overlaid afterwards with overlay_tb())."""
import os, sys, json, subprocess
import stepped_sheets as ss
import pyramid_drawings as pd

W, H = 431.8, 279.4
AREA = [10.0, 10.0, 375.0, 269.0]          # drawing area left of the info column (to be confirmed from the title block)
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
FONT = "Arial, Helvetica, sans-serif"
HEAD, TITLE, GAP = 7.0, 7.5, 10.0          # column heading band, title band under a drawing, gap between columns (mm)


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class Page:
    def __init__(self):
        self.o = []

    def text(self, x, y, s, size, bold=False, italic=False, anchor="start"):
        self.o.append('<text x="{:.2f}" y="{:.2f}" font-size="{}" font-weight="{}" font-style="{}" text-anchor="{}">{}</text>'.format(
            x, y, size, "bold" if bold else "normal", "italic" if italic else "normal", anchor, esc(s)))

    def line(self, x1, y1, x2, y2, w=0.25):
        self.o.append('<line x1="{:.2f}" y1="{:.2f}" x2="{:.2f}" y2="{:.2f}" stroke="#000" stroke-width="{}"/>'.format(x1, y1, x2, y2, w))

    def head(self, x, y, head, sub):
        self.text(x, y, head, 3.6, bold=True)
        self.text(x + len(head) * 2.2 + 4, y, sub, 2.7, italic=True)

    def title(self, x, y, t):
        self.text(x, y, t.upper(), 2.7, bold=True)

    def scalebar(self, xr, y, scale):
        s = 1000.0 / scale
        x0 = xr - 5 * s
        for a, b, f in ((0, 1, "#000"), (1, 2, "#fff"), (2, 5, "#000")):
            self.o.append('<rect x="{:.2f}" y="{:.2f}" width="{:.2f}" height="1.3" fill="{}" stroke="#000" stroke-width="0.2"/>'.format(x0 + a * s, y, (b - a) * s, f))
        for v in (0, 1, 2, 5):
            self.text(x0 + v * s, y + 4.3, str(v), 2.2, anchor="middle")
        self.text(xr + 2.3, y + 0.9, "m", 2.2)

    def add(self, sh):
        self.o.append("<g>" + "".join(sh.o) + "</g>")

    def svg(self):
        defs = ('<defs>'
                '<pattern id="conc" width="1.6" height="1.6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="1.6" stroke="#000" stroke-width="0.14"/></pattern>'
                '<pattern id="earth" width="2.4" height="2.4" patternUnits="userSpaceOnUse" patternTransform="rotate(-45)"><line x1="0" y1="0" x2="0" y2="2.4" stroke="#777" stroke-width="0.12"/></pattern>'
                '<pattern id="cast" width="1.6" height="1.6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="1.6" stroke="#000" stroke-width="0.14"/><line x1="0" y1="0" x2="1.6" y2="0" stroke="#000" stroke-width="0.14"/></pattern>'
                '</defs>')
        return ('<svg xmlns="http://www.w3.org/2000/svg" width="{w}mm" height="{h}mm" viewBox="0 0 {w} {h}" font-family="{f}">{d}{b}</svg>'
                ).format(w=W, h=H, f=FONT, d=defs, b="".join(self.o))


def LW(r):
    return json.load(open(ss.LINEWORK.format(r)))


def view(fn, roof, scale, cx, cy):
    ss.PLACE = (scale, cx, cy)
    try:
        return fn(roof)
    finally:
        ss.PLACE = None


# extents of each drawing in model metres, including its annotations (dims, A markers, level marks)
def plan_box(roof):
    d = LW(roof)["drawings"]["plan"]; x0, y0, x1, y1 = [v / 1000 for v in ss.ext(d["below"] + d["above"] + d["cut"])]
    return x0 - 2.0, y0 - 1.4, x1 + 2.0, y1 + 0.5          # A markers left/right, overall dim below, crown dim above


def section_box(roof, scale):
    D = LW(roof); d = D["drawings"]["section"]; lv = D["levels"]
    x0, z0, x1, z1 = [v / 1000 for v in ss.ext(d["cut"] + [it for it in d["beyond_clean"] if it["layer"] != "ground line"])]
    lab = 20.0 * scale / 1000                                 # level label ~20 mm on paper
    return x0 - 0.7, lv["footing_bottom"] - 1.3, x1 + 0.6 + 1.5 + lab, z1 + 0.3


def elev_box(roof, scale):
    D = LW(roof); d = D["drawings"]["elevation"]; lv = D["levels"]
    x0, z0, x1, z1 = [v / 1000 for v in ss.ext([it for it in d["visible"] if it["layer"] != "ground line"])]
    lab = 26.0 * scale / 1000
    return x0 - 0.7, -1.5, x1 + 0.6 + 1.5 + lab, z1 + 0.3


def fit_scale(widths_m, heights_m, avail_w, avail_h):
    for sc in (75, 100, 125, 150):
        if sum(widths_m) * 1000 / sc + GAP * (len(widths_m) - 1) <= avail_w and max(heights_m) * 1000 / sc <= avail_h:
            return sc
    return 150


def two_rows(rows, title_fn, heads, notes=None):
    """rows: list of (fn, boxfn) for each row; columns: 15x10, 10x10. returns Page and scale"""
    ax0, ay0, ax1, ay1 = AREA
    roofs = ("15x10", "10x10")
    for sc in (75, 100, 125, 150):
        boxes = [[(bf(r) if bf.__code__.co_argcount == 1 else bf(r, sc)) for r in roofs] for fn, bf in rows]
        xmin = [min(b[i][0] for b in boxes) for i in range(2)]; xmax = [max(b[i][2] for b in boxes) for i in range(2)]
        colw = [(xmax[i] - xmin[i]) * 1000 / sc for i in range(2)]          # common x origin per column: plan over section aligned
        rowh = [max((b[i][3] - b[i][1]) for i in range(2)) * 1000 / sc for b in boxes]
        need_w = sum(colw) + GAP + 4
        need_h = sum(rowh) + len(rows) * TITLE + HEAD + 2
        if need_w <= ax1 - ax0 and need_h <= ay1 - ay0:
            break
    pg = Page()
    s = 1.0 / sc
    sparew = (ax1 - ax0) - need_w
    xcol = [ax0 + 2 + sparew / 3, None]
    xcol[1] = xcol[0] + colw[0] + GAP + sparew / 3
    spareh = (ay1 - ay0) - need_h
    y = ay0 + HEAD + spareh / (len(rows) + 1)
    for i in range(2):
        pg.head(xcol[i], ay0 + 5.5, *heads[i])
    pg.line(xcol[1] - GAP / 2, ay0 + 1, xcol[1] - GAP / 2, ay1 - 1, 0.25)
    for k, (fn, bf) in enumerate(rows):
        for i, r in enumerate(roofs):
            b = boxes[k][i]
            bw, bh = (b[2] - b[0]) * 1000 * s, (b[3] - b[1]) * 1000 * s
            # place the box top-left at (xcol, y): model point (b[0], b[3]) -> paper (xcol, y)
            cxm, cym = 0.0, 0.0
            sh = view(fn, r, sc, 0.0, 0.0)          # dry run to get the drawing's own centre mapping
            ox0, oz0 = sh.ox, sh.oz
            # the drawing maps model mm (x, z) -> (ox + x*s, oz - z*s); shift so model b[0] lands at xcol, b[3] at y
            dx = xcol[i] - (ox0 + xmin[i] * 1000 * s)
            dy = y + (rowh[k] - bh) / 2 - (oz0 - b[3] * 1000 * s)
            sh = view(fn, r, sc, dx, dy)
            pg.add(sh)
            pg.title(xcol[i], y + rowh[k] + 5.0, title_fn(k, r, sc))
        y += rowh[k] + TITLE + spareh / (len(rows) + 1)
    for i in range(2):
        pg.scalebar(xcol[i] + colw[i] - 4, ay1 - 6.0, sc)
    return pg, sc

# ---- A2 sheets as published (title block page kept), drawings enlarged -------------------------------------------
W, H = 594.0, 420.0
AREA = [14.0, 14.0, 503.0, 405.0]
TB = r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\details\set\07_2026-11-21_stepped-press-layout\ref\title-blocks-S112-S115-1to75.pdf"
PLAN_NOTES = {
    "15x10": "–  Rib net on the room face (faint), continuous from the base ring to the crown ring.   –  Base ring step +2.40 to +2.80 (dashed above), crown ring at +12.30.   –  Columns cut (crossed hatch); strip footing below ground (thin dashed).",
    "10x10": "–  Rib net faint, base ring step +2.40 to +2.80 (dashed), crown ring at +8.19.   –  Columns cut; strip footing below ground (dashed)."}


def s112():
    def t(k, r, sc):
        return ("Roof plan, cut at +1.20 1:%d" % sc) if k == 0 else ("Section A-A 1:%d" % sc)
    pg, sc = two_rows([(ss.plan, plan_box), (ss.section, section_box)], t,
                      [("15 x 10 · STEPPED", "18 printed courses + crown ring course, 19 columns"),
                       ("10 x 10 · STEPPED", "10 printed courses + crown ring course, 15 columns")])
    return pg, sc


def s113():
    def t(k, r, sc):
        return "Elevation, looking north 1:%d" % sc
    return two_rows([(ss.elevation, elev_box)], t, [("15 x 10 · STEPPED", "long side"), ("10 x 10 · STEPPED", "long side")])


def _axon_or_tb(items_by_col, heads, titles, fixed_scale=None, stacked=False):
    ax0, ay0, ax1, ay1 = AREA
    pg = Page()
    exts = [[ss.ext(it) for it in col] for col in items_by_col]          # mm, per view
    avail_h = ay1 - ay0 - HEAD - len(items_by_col[0]) * TITLE - 6
    if fixed_scale:
        sc = fixed_scale
    else:
        sc = None
    widths = [max(e[2] - e[0] for e in col) for col in exts]
    heights = [sum(e[3] - e[1] for e in col) for col in exts]
    if not sc:
        for cand in (75, 100, 125, 150, 175, 200, 250, 300):
            if sum(widths) / cand + GAP + 4 <= ax1 - ax0 and max(heights) / cand <= avail_h:
                sc = cand; break
    s = 1.0 / sc
    colw = [w * s for w in widths]
    sparew = (ax1 - ax0) - (sum(colw) + GAP + 4)
    xcol = [ax0 + 2 + sparew / 3, None]; xcol[1] = xcol[0] + colw[0] + GAP + sparew / 3
    pg.line(xcol[1] - GAP / 2, ay0 + 1, xcol[1] - GAP / 2, ay1 - 1, 0.25)
    for i, col in enumerate(items_by_col):
        pg.head(xcol[i], ay0 + 5.5, *heads[i])
        n = len(col)
        tot = sum((e[3] - e[1]) * s for e in exts[i]) + n * TITLE
        spare = (ay1 - ay0 - HEAD - 6) - tot
        y = ay0 + HEAD + spare / (n + 1)
        for k, items in enumerate(col):
            x0, y0, x1, y1 = exts[i][k]
            bw, bh = (x1 - x0) * s, (y1 - y0) * s
            sh = ss.StepSheet(sc, xcol[i] + (colw[i] - bw) / 2 - x0 * s, y + y1 * s, "", "", [], [], W, H)
            pieces = [it for it in items if it["layer"] in ("printed pieces", "top course U formwork")]
            rib = [it for it in items if it["layer"] == "ribs"]
            other = [it for it in items if it["layer"] not in ("printed pieces", "top course U formwork", "ribs")]
            light = titles[i][k][1]
            if not light:
                ss.lines(sh, pieces, 0.15, "#000"); ss.lines(sh, other, 0.25, "#000"); ss.lines(sh, rib, 0.13, "#7a7a7a")
            else:
                ss.lines(sh, pieces, 0.09, "#a0a0a0"); ss.lines(sh, other, 0.25, "#000"); ss.lines(sh, rib, 0.2, "#222")
            pg.add(sh)
            pg.title(xcol[i], y + bh + 5.0, titles[i][k][0].replace("{sc}", str(sc)))
            y += bh + TITLE + spare / (n + 1)
    return pg, sc


def s114():
    iso = json.load(open(ss.AXON.format("iso")))["visible"]
    worm = json.load(open(ss.AXON.format("worm")))["visible"]
    pg, sc = _axon_or_tb([[iso], [worm]], [("A · AXONOMETRIC", "from the south-east, above"), ("B · WORM'S-EYE", "from below, looking up into the roofs")],
                         [[("Axonometric from the south-east (parallel projection, not to scale)", False)],
                          [("Worm's-eye view from below (parallel projection, not to scale)", True)]])
    return pg, sc


def s115():
    TBJ = os.path.join(ss.HERE, "..", "polyframe2", "drawings-2026-11-20", "_tmp_{}_topbottom.json")
    d15, d10 = json.load(open(TBJ.format("15x10"))), json.load(open(TBJ.format("10x10")))
    ttl = [("Roof from above 1:{sc}", False), ("Roof from below (seen from below, mirrored) 1:{sc}", True)]
    pg, sc = _axon_or_tb([[d15["top"], d15["bottom"]], [d10["top"], d10["bottom"]]],
                         [("15 x 10 · STEPPED", "roof only"), ("10 x 10 · STEPPED", "roof only")], [ttl, ttl])
    ax0, ay0, ax1, ay1 = AREA
    return pg, sc


SHEETS = [(0, "S112-plans-and-sections", s112), (1, "S113-elevations", s113), (2, "S114-axonometric-and-wormseye", s114),
          (3, "S115-roof-from-above-and-below", s115)]


def overlay_tb(idx, src, out):
    import pikepdf
    from pikepdf import Rectangle
    MM = 72 / 25.4
    tb = pikepdf.open(TB); o = pikepdf.new(); o.pages.append(tb.pages[idx]); p = o.pages[0]
    sp = pikepdf.open(src); p.add_overlay(sp.pages[0], Rectangle(0, 0, W * MM, H * MM)); o.save(out)


def build(outdir, only=None):
    os.makedirs(outdir, exist_ok=True)
    res = []
    for idx, name, fn in SHEETS:
        if only and name not in only:
            continue
        pg, sc = fn()
        if idx != 2 and sc != 75:          # title block says 1:75: write the true scale over the Scale field
            pg.o.append('<rect x="558" y="398" width="21.3" height="7.4" fill="#fff"/>')
            pg.o.append('<text x="578.6" y="404.0" font-size="4.0" text-anchor="end">1:%d</text>' % sc)
        base = os.path.join(outdir, name)
        html = ('<!doctype html><html><head><meta charset="utf-8"><style>@page{size:594mm 420mm;margin:0}html,body{margin:0}'
                'svg{display:block;width:594mm;height:420mm}</style></head><body>%s</body></html>' % pg.svg())
        open(base + "-drawing.html", "w", encoding="utf-8").write(html)
        url = "file:///" + (base + "-drawing.html").replace("\\", "/")
        subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--print-to-pdf=" + base + "-drawing.pdf", url],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=240)
        overlay_tb(idx, base + "-drawing.pdf", base + ".pdf")
        import pypdfium2 as pdfium
        pdfium.PdfDocument(base + ".pdf")[0].render(scale=150 / 72).to_pil().save(base + ".png")
        res.append((name, sc))
    return res


if __name__ == "__main__":
    for r in build(sys.argv[1], sys.argv[2:] or None):
        print(r)
