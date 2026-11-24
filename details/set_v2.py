"""S112-S121 v2 (Gonzalo 2026-11-21): S112 axonometric, S113/S115 plan stacked over section A-A at 1:75 (same x),
S114/S116 elevation at 1:75 (same x as the plan/section sheet), S117 worm's-eye, S118 roof from above, S119 roof
from below (drawings reused unchanged), S120/S121 detail sheets appended as-is. Reuses the existing linework."""
import os, sys, subprocess
import pikepdf, pypdf, pypdfium2 as pdfium
from pikepdf import Rectangle
import stepped_sheets as ss
import deck_sheets as ds
import one_per_sheet as o

ds.W, ds.H = 594.0, 420.0
A = (15.0, 15.0, 503.0, 405.0)
SC = 75
TR = r"C:\Users\gonza\.claude\projects\D--My-Drive-Education-Columbia-M-Arch\675e5010-51e9-4c6f-9486-4b27d96775a9\tool-results"
TB = os.path.join(TR, "mcp-claude-artifacts-blob-1795249177684-onnbt7.pdf")
DET = [os.path.join(TR, "mcp-claude-artifacts-blob-1795249117806-f156zj.pdf"), os.path.join(TR, "mcp-claude-artifacts-blob-1795249117806-7fn0lf.pdf")]
OLD = r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\details\set\09_2026-11-21_stepped-one-per-sheet"


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
    gap_t = 15.0
    tot = hp + gap_t + hs + 9
    y = A[1] + max(0.0, (A[3] - A[1] - tot) / 2)
    lv = ds.LW(roof)["levels"]
    h, x, w = place(pg, ss.plan, roof, pb, y, xo, ux0)
    pg.text(x, y + h + 5, ("%s stepped roof · plan, cut at +1.20 1:%d" % (roof, SC)).upper(), 3.0, bold=True)
    pg.text(x, y + h + 10, "–  Rib net on the room face (faint), continuous base ring to crown ring.   –  Base ring step +2.40 to +2.80 and crown ring at +%.2f above (dashed).   –  Columns cut; strip footing below ground (thin dashed)." % lv["crown_top"], 2.5)
    pg.scalebar(x + w - 4, y + h + 2.5, SC)
    y2 = y + h + gap_t
    h2, x2, w2 = place(pg, ss.section, roof, sb, y2, xo, ux0)
    pg.text(x2, y2 + h2 + 5, ("%s stepped roof · section A-A 1:%d" % (roof, SC)).upper(), 3.0, bold=True)
    pg.text(x2, y2 + h2 + 10, "Cut 10 cm north of the centre line (clear of the piece joints). Single hatch printed concrete (one solid profile per course), crossed hatch cast concrete, ribs faint.", 2.5)
    return pg


def elevation(roof):
    pg = ds.Page(); s = 1.0 / SC
    xo, ux0 = xo_of(roof)
    eb = ds.elev_box(roof, SC)
    he = (eb[3] - eb[1]) * 1000 * s
    y = A[1] + (A[3] - A[1] - he - 9) / 2
    h, x, w = place(pg, ss.elevation, roof, eb, y, xo, ux0)
    pg.text(x, y + h + 5, ("%s stepped roof · elevation, looking north 1:%d" % (roof, SC)).upper(), 3.0, bold=True)
    pg.scalebar(x + w - 4, y + h + 2.5, SC)
    return pg



import re as _re
EXACT = {"2400": "2000", "9500": "7917", "5392": "4493"}          # ring 400 unchanged
SUBS = [("+2.40", "@A@"), ("+2.80", "@B@"), ("+12.30", "@C@"), ("+8.19", "@D@"), ("+1.20", "@E@"),
        ("@A@", "+2.00"), ("@B@", "+2.40"), ("@C@", "+10.32"), ("@D@", "+6.89"), ("@E@", "+1.00")]   # simultaneous swap
CHANGED = []


def heights_text(svg):
    """TEXT ONLY (Gonzalo 2026-11-21, temporary): vertical dimensions and levels above +-0.00 column 2.4 m shown as 2 m, roof heights x 5/6, ring 400 unchanged, so the 2.4 m
    column reads 2 m; geometry unchanged; +-0.00, footing -0.80 / 800 and horizontal dimensions unchanged."""
    def f(m):
        t = m.group(1)
        n = EXACT.get(t.strip(), None)
        if n is not None:
            CHANGED.append((t, n)); return ">" + n + "<"
        u = t
        for a, b in SUBS:
            u = u.replace(a, b)
        if u != t:
            CHANGED.append((t[:60], u[:60]))
        return ">" + u + "<"
    return _re.sub(r">([^<>]+)<", f, svg)


SHEETS = [(0, "S112-axonometric", "S118-axonometric"),
          (1, "S113-15x10-plan-and-section", lambda: plan_section("15x10")),
          (2, "S114-15x10-elevation", lambda: elevation("15x10")),
          (3, "S115-10x10-plan-and-section", lambda: plan_section("10x10")),
          (4, "S116-10x10-elevation", lambda: elevation("10x10")),
          (5, "S117-wormseye", "S119-wormseye"),
          (6, "S118-roof-from-above", "S120-roof-from-above"),
          (7, "S119-roof-from-below", "S121-roof-from-below")]

if __name__ == "__main__":
    od = sys.argv[1]; os.makedirs(od, exist_ok=True)
    MM = 72 / 25.4
    fs = []
    for idx, name, src in SHEETS:
        base = os.path.join(od, name)
        if isinstance(src, str):
            drawing = os.path.join(OLD, src + "-drawing.pdf")
        else:
            pg = src()
            html = ('<!doctype html><html><head><meta charset="utf-8"><style>@page{size:594mm 420mm;margin:0}html,body{margin:0}'
                    'svg{display:block;width:594mm;height:420mm}</style></head><body>%s</body></html>' % heights_text(pg.svg()))
            open(base + "-drawing.html", "w", encoding="utf-8").write(html)
            drawing = base + "-drawing.pdf"
            subprocess.run([ds.EDGE, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--print-to-pdf=" + drawing,
                            "file:///" + (base + "-drawing.html").replace("\\", "/")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=240)
        tb = pikepdf.open(TB); oo = pikepdf.new(); oo.pages.append(tb.pages[idx]); p = oo.pages[0]
        sp = pikepdf.open(drawing); p.add_overlay(sp.pages[0], Rectangle(0, 0, 594 * MM, 420 * MM)); oo.save(base + ".pdf")
        w = pypdf.PdfWriter(); w.append(base + ".pdf")
        for pp in w.pages: pp.compress_content_streams()
        w.compress_identical_objects(); w.write(base + ".pdf")
        pdfium.PdfDocument(base + ".pdf")[0].render(scale=100 / 72).to_pil().save(base + ".png")
        fs.append(base + ".pdf"); print(name, flush=True)
    det = os.path.join(TR, "mcp-claude-artifacts-blob-1795249177685-a427gn.pdf")
    rd = pypdf.PdfReader(det)
    for k, n in enumerate(("S120-assembly-sequence", "S121-clamp-detail", "S122-rib-detail")):
        w1 = pypdf.PdfWriter(); w1.add_page(rd.pages[k]); f = os.path.join(od, n + ".pdf"); w1.write(f)
        pdfium.PdfDocument(f)[0].render(scale=100 / 72).to_pil().save(os.path.join(od, n + ".png")); fs.append(f)
    w = pypdf.PdfWriter()
    for f in fs: w.append(f)
    w.compress_identical_objects(); w.write(os.path.join(od, "S112-S122-stepped-roofs.pdf"))
    for a, b in sorted(set(CHANGED)): print("TEXT:", repr(a), "->", repr(b))
    print("merged", len(fs), os.path.getsize(os.path.join(od, "S112-S122-stepped-roofs.pdf")))
