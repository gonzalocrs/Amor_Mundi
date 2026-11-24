"""S112-S121: one drawing per A2 sheet (Gonzalo 2026-11-21), on the title blocks ref/title-blocks-S112-S121.pdf.
Drawing area x 15..503, y 15..405 mm. Reuses the existing linework (no Make2D)."""
import os, sys, json, subprocess
import stepped_sheets as ss
import deck_sheets as ds

ds.W, ds.H = 594.0, 420.0
A = (15.0, 15.0, 503.0, 405.0)
TB = r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\details\set\07_2026-11-21_stepped-press-layout\ref\title-blocks-S112-S121.pdf"


def union_x(roof, sc):
    bs = [ds.plan_box(roof), ds.elev_box(roof, sc), ds.section_box(roof, sc)]
    return min(b[0] for b in bs), max(b[2] for b in bs)


def single(fn, roof, sc, box, title, notes=None):
    pg = ds.Page()
    s = 1.0 / sc
    b = box
    bw, bh = (b[2] - b[0]) * 1000 * s, (b[3] - b[1]) * 1000 * s
    extra = 9 + (6 if notes else 0)
    ux0, ux1 = union_x(roof, sc)                     # same x origin on the plan, elevation and section sheets of a module
    xo = A[0] + (A[2] - A[0] - (ux1 - ux0) * 1000 * s) / 2
    x0 = xo + (b[0] - ux0) * 1000 * s
    y0 = A[1] + (A[3] - A[1] - bh - extra) / 2
    sh = ds.view(fn, roof, sc, 0.0, 0.0)
    dx = x0 - (sh.ox + b[0] * 1000 * s)
    dy = y0 - (sh.oz - b[3] * 1000 * s)
    pg.add(ds.view(fn, roof, sc, dx, dy))
    pg.text(x0, y0 + bh + 6, title.upper(), 3.2, bold=True)
    if notes:
        pg.text(x0, y0 + bh + 12, notes, 2.8)
    pg.scalebar(x0 + bw - 4, y0 + bh + 3, sc)
    return pg


def lines_view(items_list, sc, titles, light, extra=None):
    """several Make2D views side by side (both modules), centred"""
    pg = ds.Page()
    exts = [ss.ext(it) for it in items_list]
    if sc is None:
        for c in (50, 75, 100, 125, 150, 175, 200, 250):
            if sum(e[2] - e[0] for e in exts) / c + 20 * (len(exts) - 1) <= A[2] - A[0] - 10 and max(e[3] - e[1] for e in exts) / c <= A[3] - A[1] - 25:
                sc = c; break
    s = 1.0 / sc
    ws = [(e[2] - e[0]) * s for e in exts]; hs = [(e[3] - e[1]) * s for e in exts]
    tot = sum(ws) + 20 * (len(exts) - 1)
    x = A[0] + (A[2] - A[0] - tot) / 2
    hmax = max(hs)
    ytop = A[1] + (A[3] - A[1] - hmax - 10) / 2
    for items, e, w, h, t in zip(items_list, exts, ws, hs, titles):
        y = ytop + (hmax - h) / 2
        sh = ss.StepSheet(sc, x - e[0] * s, y + e[3] * s, "", "", [], [], ds.W, ds.H)
        pieces = [it for it in items if it["layer"] in ("printed pieces", "top course U formwork")]
        rib = [it for it in items if it["layer"] == "ribs"]
        other = [it for it in items if it["layer"] not in ("printed pieces", "top course U formwork", "ribs", "ground")]
        ground = [it for it in items if it["layer"] == "ground"]          # ±0.00 where the ground touches (Gonzalo 2026-11-23), dashed
        if ground:
            ss.lines(sh, ground, 0.18, "#000", dash="2 1")
        if not light:
            ss.lines(sh, pieces, 0.18, "#000"); ss.lines(sh, other, 0.3, "#000"); ss.lines(sh, rib, 0.15, "#7a7a7a")
        else:
            ss.lines(sh, pieces, 0.1, "#a0a0a0"); ss.lines(sh, other, 0.3, "#000"); ss.lines(sh, rib, 0.2, "#444")      # rib tubes: their two true outlines (2026-11-23 v3), grey like the plan
        if extra:
            extra[items_list.index(items)](sh)    # per-view extras (dimensions), drawn in model mm
        pg.add(sh)
        pg.text(x, ytop + hmax + 8, t.replace("{sc}", str(sc)).upper(), 3.2, bold=True)
        x += w + 20
    return pg, sc


def sheets():
    out = []
    for i, roof in enumerate(("15x10", "10x10")):
        lv = ds.LW(roof)["levels"]
        out.append((3 * i + 0, "S%d-%s-plan" % (112 + 3 * i, roof), lambda roof=roof, lv=lv: single(ss.plan, roof, 50, ds.plan_box(roof), "%s stepped roof · plan, cut at +1.20 1:50" % roof,
                    "–  Rib net on the room face (faint), continuous base ring to crown ring.   –  Base ring step +2.40 to +2.80 and crown ring at +%.2f above (dashed).   –  Columns cut; strip footing below ground (thin dashed)." % lv["crown_top"])))
        out.append((3 * i + 1, "S%d-%s-elevation" % (113 + 3 * i, roof), lambda roof=roof: single(ss.elevation, roof, 50, ds.elev_box(roof, 50), "%s stepped roof · elevation, looking north 1:50" % roof)))
        out.append((3 * i + 2, "S%d-%s-section-AA" % (114 + 3 * i, roof), lambda roof=roof: single(ss.section, roof, 50, ds.section_box(roof, 50), "%s stepped roof · section A-A 1:50" % roof,
                    "Cut 10 cm north of the centre line (clear of the piece joints). Single hatch printed concrete (one solid profile per course), crossed hatch cast concrete, ribs faint.")))
    iso = json.load(open(ss.AXON.format("iso")))["visible"]; worm = json.load(open(ss.AXON.format("worm")))["visible"]
    out.append((6, "S118-axonometric", lambda: lines_view([iso], None, ["Axonometric from the south-east, both modules (parallel projection, not to scale)"], False)[0]))
    out.append((7, "S119-wormseye", lambda: lines_view([worm], None, ["Worm's-eye view from below, both modules (parallel projection, not to scale)"], True)[0]))
    TBJ = os.path.join(ss.HERE, "..", "polyframe2", "drawings-2026-11-20", "_tmp_{}_topbottom.json")
    d15, d10 = json.load(open(TBJ.format("15x10"))), json.load(open(TBJ.format("10x10")))
    out.append((8, "S120-roof-from-above", lambda: lines_view([d15["top"], d10["top"]], 75, ["15x10 roof from above 1:75", "10x10 roof from above 1:75"], False)[0]))
    out.append((9, "S121-roof-from-below", lambda: lines_view([d15["bottom"], d10["bottom"]], 75, ["15x10 roof from below (mirrored) 1:75", "10x10 roof from below (mirrored) 1:75"], True)[0]))
    return out


def overlay(idx, src, out):
    import pikepdf
    from pikepdf import Rectangle
    MM = 72 / 25.4
    tb = pikepdf.open(TB); o = pikepdf.new(); o.pages.append(tb.pages[idx]); p = o.pages[0]
    sp = pikepdf.open(src); p.add_overlay(sp.pages[0], Rectangle(0, 0, ds.W * MM, ds.H * MM)); o.save(out)


if __name__ == "__main__":
    od = sys.argv[1]; os.makedirs(od, exist_ok=True)
    import pypdfium2 as pdfium
    for idx, name, fn in sheets():
        pg = fn(); base = os.path.join(od, name)
        html = ('<!doctype html><html><head><meta charset="utf-8"><style>@page{size:594mm 420mm;margin:0}html,body{margin:0}'
                'svg{display:block;width:594mm;height:420mm}</style></head><body>%s</body></html>' % pg.svg())
        open(base + "-drawing.html", "w", encoding="utf-8").write(html)
        subprocess.run([ds.EDGE, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--print-to-pdf=" + base + "-drawing.pdf",
                        "file:///" + (base + "-drawing.html").replace("\\", "/")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=240)
        overlay(idx, base + "-drawing.pdf", base + ".pdf")
        pdfium.PdfDocument(base + ".pdf")[0].render(scale=100 / 72).to_pil().save(base + ".png")
        print(name, flush=True)
