"""Final model 2026-11-27 (stepped-roofs-final-2026-11-27.3dm: base ring and columns grown inward to the rib landings,
strip footing 30 mm inward, corner joints fixed), same sheets, layout and title blocks as the review fixes of 2026-11-23:
Review fixes 2026-11-23: the 6 drawing sheets of the submitted set, same A2 title blocks, same layout and scales,
redrawn from the updated model (2 m columns, curved corners) with the real levels (no text patch):
  axonometric (+ dimensions), worm's-eye (ribs as ribs), roof from above, roof from below (ribs as ribs),
  15x10 plan + section (crown opening dimensioned both ways), 10x10 plan + section.
Runs with Rhino's CPython (pypdf from the default site-env); Edge prints the SVG drawings to PDF.
Usage: python sheets_2026_11_23.py <outdir> [name ...]"""
import os, sys, json, subprocess
import pypdf
from pypdf import Transformation
import stepped_sheets as ss
import deck_sheets as ds
import one_per_sheet as o

ds.W, ds.H = 594.0, 420.0
A = (15.0, 15.0, 503.0, 405.0)
SC = 75
SC_TB = int(os.environ.get("SC_TB", "75"))          # roof from above / below (Gonzalo 2026-11-23: "do them 1:100")
TR = r"C:\Users\gonza\.claude\projects\D--My-Drive-Education-Columbia-M-Arch\675e5010-51e9-4c6f-9486-4b27d96775a9\tool-results"
TB = os.path.join(TR, "mcp-claude-artifacts-blob-1795249177684-onnbt7.pdf")      # title blocks S112-S122 (no drawings)
P = os.path.join(ss.HERE, "..", "polyframe2", "drawings-2026-11-20")


def xo_of(roof):
    s = 1.0 / SC
    ux0, ux1 = o.union_x(roof, SC)
    return A[0] + (A[2] - A[0] - (ux1 - ux0) * 1000 * s) / 2, ux0


def place(pg, fn, roof, box, ytop, xo, ux0):
    s = 1.0 / SC
    sh = ds.view(fn, roof, SC, 0.0, 0.0)
    dx = xo - (sh.ox + ux0 * 1000 * s)
    dy = ytop - (sh.oz - box[3] * 1000 * s)
    pg.add(ds.view(fn, roof, SC, dx, dy))
    return (box[3] - box[1]) * 1000 * s, xo + (box[0] - ux0) * 1000 * s, (box[2] - box[0]) * 1000 * s


def plan_section(roof):
    pg = ds.Page(); s = 1.0 / SC
    xo, ux0 = xo_of(roof)
    pb, sb = ds.plan_box(roof), ds.section_box(roof, SC)
    hp, hs = (pb[3] - pb[1]) * 1000 * s, (sb[3] - sb[1]) * 1000 * s
    tot = hp + 15.0 + hs + 9
    y = A[1] + max(0.0, (A[3] - A[1] - tot) / 2)
    lv = ds.LW(roof)["levels"]
    h, x, w = place(pg, ss.plan, roof, pb, y, xo, ux0)
    pg.text(x, y + h + 5, ("%s stepped roof · plan, cut at +%.2f 1:%d" % (roof, lv["plan_cut"], SC)).upper(), 3.0, bold=True)
    pg.text(x, y + h + 10, "–  Rib net on the room face (faint), continuous base ring to crown ring.   –  Base ring step +%.2f to +%.2f and crown ring at +%.2f above (dashed).   –  Columns cut; rectangular strip footing with corner blocks below ground (thin dashed)." % (lv["base_ring_bottom"], lv["base_ring_top"], lv["crown_top"]), 2.5)
    pg.scalebar(x + w - 4, y + h + 2.5, SC)
    y2 = y + h + 15.0
    h2, x2, w2 = place(pg, ss.section, roof, sb, y2, xo, ux0)
    pg.text(x2, y2 + h2 + 5, ("%s stepped roof · section A-A 1:%d" % (roof, SC)).upper(), 3.0, bold=True)
    pg.text(x2, y2 + h2 + 10, "Cut 10 cm north of the centre line (clear of the piece joints). Single hatch printed concrete (one solid profile per course), crossed hatch cast concrete, ribs faint.", 2.5)
    return pg


def axon_sheet():
    iso = json.load(open(os.path.join(P, "_tmp_axon_iso.json")))["visible"]
    pg, sc = o.lines_view([iso], None, ["Axonometric from the south-east, both modules (parallel projection, not to scale)"], False)
    l15, l10 = ds.LW("15x10")["levels"], ds.LW("10x10")["levels"]
    p15, p10 = ds.plan_box("15x10"), ds.plan_box("10x10")
    notes = ["DIMENSIONS (mm, levels from ±0.00 ground floor)",
             "15 x 10 module:  20 columns 420 (radial) x 360, strip footing 1.20 m wide with corner blocks, outside 16,316 x 11,210;  base ring outside 15,752 x 10,540, cast ring 528 wide (typical) x 400;  crown opening (clear) 3,019 x 1,998",
             "   columns ±0.00 to +%.2f;  base ring +%.2f to +%.2f;  crown top +%.2f;  roof %d high above the ring top" % (l15["base_ring_bottom"], l15["base_ring_bottom"], l15["base_ring_top"], l15["crown_top"], round((l15["crown_top"] - l15["base_ring_top"]) * 1000)),
             "10 x 10 module:  16 columns 362 (radial) x 300, strip footing 0.85 m wide with corner blocks, outside 10,930 x 10,930;  base ring outside 10,680 x 10,680, cast ring 552 wide (typical) x 400;  crown opening (clear) 3,045 x 3,045",
             "   columns ±0.00 to +%.2f;  base ring +%.2f to +%.2f;  crown top +%.2f;  roof %d high above the ring top" % (l10["base_ring_bottom"], l10["base_ring_bottom"], l10["base_ring_top"], l10["crown_top"], round((l10["crown_top"] - l10["base_ring_top"]) * 1000)),
             "Rectangular strip footing under the column centres with square corner blocks, -0.80 to -0.30: 1.20 m wide (15 x 10), 0.85 m wide (10 x 10).  Printed pieces 3 cm walls; ribs cast in printed tubes on the room face."]
    y = A[1] + 14
    for i, t in enumerate(notes):
        pg.text(A[0] + 10, y + i * 4.6, t, 3.0 if i == 0 else 2.7, bold=(i == 0))
    return pg


def worm_sheet():
    worm = json.load(open(os.path.join(P, "_tmp_axon_worm.json")))["visible"]
    return o.lines_view([worm], None, ["Worm's-eye view from below, both modules (parallel projection, not to scale)"], True)[0]


def tb_view(key, light, title):
    d15 = json.load(open(os.path.join(P, "_tmp_15x10_topbottom.json")))
    d10 = json.load(open(os.path.join(P, "_tmp_10x10_topbottom.json")))
    return o.lines_view([d15[key], d10[key]], SC_TB, ["15x10 " + title + " 1:{sc}", "10x10 " + title + " 1:{sc}"], light)[0]


def plan_dims(roof):
    """general dimensions on the roof from above (review: 'dim.'): base ring outside and crown opening clear, both ways,
    measured in the model (_tmp_plan_dims.json, written in Rhino from the base ring and crown ring breps)"""
    d = json.load(open(os.path.join(P, "_tmp_plan_dims.json")))[roof]
    ox, oy = {"15x10": (85000.0, 0.0), "10x10": (85000.0, -20000.0)}[roof]     # Make2D linework is centred on the roof
    x0, y0, x1, y1 = [v - (ox if i % 2 == 0 else oy) for i, v in enumerate(d["ring"])]
    cx0, cy0, cx1, cy1 = [v - (ox if i % 2 == 0 else oy) for i, v in enumerate(d["crown"])]

    def f(sh):
        m = lambda v: "%.2f m" % (int(v / 10.0 + 0.5) / 100.0)        # Gonzalo 2026-11-23: metres, 2 decimals (half up), no words
        sh.dim_h([x0, x1], y1 + 900, ext=y1, labels=[m(x1 - x0)])     # above (the view title is below)
        sh.dim_v([y0, y1], x1 + 900, ext=x1, labels=[m(y1 - y0)])
        w, h = cx1 - cx0, cy1 - cy0                 # crown opening, drawn inside the (empty) opening
        sh.dim_h([cx0, cx1], cy0 + 0.72 * h, ext=cy0 + 0.72 * h, labels=[m(w)])
        sh.dim_v([cy0, cy1], cx0 + 0.30 * w, ext=cx0 + 0.30 * w, labels=[m(h)])
    return f


def top_view():
    d15 = json.load(open(os.path.join(P, "_tmp_15x10_topbottom.json")))
    d10 = json.load(open(os.path.join(P, "_tmp_10x10_topbottom.json")))
    return o.lines_view([d15["top"], d10["top"]], SC_TB, ["15x10 roof from above 1:{sc}", "10x10 roof from above 1:{sc}"], False,
                        extra=[plan_dims("15x10"), plan_dims("10x10")])[0]


def above_and_below():
    """review 'combine with before' (Gonzalo 2026-11-23): roof from above (with general dims) over roof from below, one A2, 1:100,
    each module keeps the same left x in both rows; sheet name in the title block patched to ROOF FROM ABOVE AND BELOW"""
    import stepped_sheets as ss
    sc = SC_TB; s = 1.0 / sc
    d15 = json.load(open(os.path.join(P, "_tmp_15x10_topbottom.json")))
    d10 = json.load(open(os.path.join(P, "_tmp_10x10_topbottom.json")))
    rows = [([d15["top"], d10["top"]], False, ["15x10 roof from above 1:{sc}", "10x10 roof from above 1:{sc}"], [plan_dims("15x10"), plan_dims("10x10")]),
            ([d15["bottom"], d10["bottom"]], True, ["15x10 roof from below (mirrored) 1:{sc}", "10x10 roof from below (mirrored) 1:{sc}"], [None, None])]
    pg = ds.Page()
    cols = [[ss.ext(r[0][k]) for r in rows] for k in (0, 1)]           # per module: extents in both rows
    colx = [(min(e[0] for e in c), max(e[2] for e in c)) for c in cols]
    ws = [(b - a) * s for a, b in colx]
    gap = 28
    x0 = A[0] + (A[2] - A[0] - sum(ws) - gap) / 2
    xs = [x0, x0 + ws[0] + gap]
    hs = [max((e[3] - e[1]) * s for e in (cols[0][i], cols[1][i])) for i in (0, 1)]
    vgap = 34
    y = A[1] + (A[3] - A[1] - sum(hs) - vgap - 10) / 2 + 6
    for ri, (items, light, titles, extras) in enumerate(rows):
        for k in (0, 1):
            e = cols[k][ri]
            yk = y + (hs[ri] - (e[3] - e[1]) * s) / 2
            sh = ss.StepSheet(sc, xs[k] - colx[k][0] * s, yk + e[3] * s, "", "", [], [], ds.W, ds.H)
            it = items[k]
            pieces = [q for q in it if q["layer"] in ("printed pieces", "top course U formwork")]
            rib = [q for q in it if q["layer"] == "ribs"]
            other = [q for q in it if q["layer"] not in ("printed pieces", "top course U formwork", "ribs")]
            if not light:
                ss.lines(sh, pieces, 0.18, "#000"); ss.lines(sh, other, 0.3, "#000"); ss.lines(sh, rib, 0.15, "#7a7a7a")
            else:
                ss.lines(sh, pieces, 0.1, "#a0a0a0"); ss.lines(sh, other, 0.3, "#000"); ss.lines(sh, rib, 0.2, "#444")
            if extras[k]:
                extras[k](sh)
            pg.add(sh)
            pg.text(xs[k], y + hs[ri] + 8, titles[k].replace("{sc}", str(sc)).upper(), 3.2, bold=True)
        y += hs[ri] + vgap
    # title block sheet name: cover the printed name and write the new one
    pg.o.append('<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" fill="#fff"/>' % TB_NAME_BOX)
    cx = TB_NAME_BOX[0] + TB_NAME_BOX[2] / 2; cy = TB_NAME_BOX[1] + TB_NAME_BOX[3] / 2
    for i, t in enumerate(("ROOF FROM ABOVE", "AND BELOW")):
        pg.text(cx, cy - 1.5 + i * 7.5, t, 6.0, anchor="middle")
    return pg


TB_NAME_BOX = (511.5, 292.0, 67.0, 28.0)      # sheet-name field of the A2 title block (mm), measured on the rendered sheet


SHEETS = [(0, "A-axonometric", axon_sheet),
          (5, "B-wormseye", worm_sheet),
          (6, "C-roof-from-above", top_view),
          (6, "CD-roof-from-above-and-below", above_and_below),
          (7, "D-roof-from-below", lambda: tb_view("bottom", True, "roof from below (mirrored)")),
          (1, "E-15x10-plan-and-section", lambda: plan_section("15x10")),
          (3, "F-10x10-plan-and-section", lambda: plan_section("10x10"))]

if __name__ == "__main__":
    od = sys.argv[1]; only = sys.argv[2:]
    os.makedirs(od, exist_ok=True)
    MM = 72 / 25.4
    tbr = pypdf.PdfReader(TB)
    for idx, name, fn in SHEETS:
        if only and name not in only:
            continue
        pg = fn(); base = os.path.join(od, name)
        html = ('<!doctype html><html><head><meta charset="utf-8"><style>@page{size:594mm 420mm;margin:0}html,body{margin:0}'
                'svg{display:block;width:594mm;height:420mm}</style></head><body>%s</body></html>' % pg.svg())
        open(base + "-drawing.html", "w", encoding="utf-8").write(html)
        subprocess.run([ds.EDGE, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--print-to-pdf=" + base + "-drawing.pdf",
                        "file:///" + (base + "-drawing.html").replace("\\", "/")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=300)
        w = pypdf.PdfWriter()
        w.add_page(tbr.pages[idx])
        tp = w.pages[0]
        dr = pypdf.PdfReader(base + "-drawing.pdf").pages[0]
        # scale the drawing page onto the title block page (both A2)
        sx = float(tp.mediabox.width) / float(dr.mediabox.width); sy = float(tp.mediabox.height) / float(dr.mediabox.height)
        tp.merge_transformed_page(dr, Transformation().scale(sx, sy))
        tp.compress_content_streams()
        w.compress_identical_objects()
        w.write(base + ".pdf")
        print(name, os.path.getsize(base + ".pdf"), flush=True)
