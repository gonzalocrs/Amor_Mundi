"""rebuild single sheets of the one-per-sheet set: python one_sheet.py <outdir> <name> [<name> ...]"""
import os, sys, subprocess
import pypdfium2 as pdfium
import one_per_sheet as o
import deck_sheets as ds

od, names = sys.argv[1], sys.argv[2:]
for idx, name, fn in o.sheets():
    if name not in names:
        continue
    pg = fn(); base = os.path.join(od, name)
    html = ('<!doctype html><html><head><meta charset="utf-8"><style>@page{size:594mm 420mm;margin:0}html,body{margin:0}'
            'svg{display:block;width:594mm;height:420mm}</style></head><body>%s</body></html>' % pg.svg())
    open(base + "-drawing.html", "w", encoding="utf-8").write(html)
    subprocess.run([ds.EDGE, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--print-to-pdf=" + base + "-drawing.pdf",
                    "file:///" + (base + "-drawing.html").replace("\\", "/")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=240)
    o.overlay(idx, base + "-drawing.pdf", base + ".pdf")
    pdfium.PdfDocument(base + ".pdf")[0].render(scale=100 / 72).to_pil().save(base + ".png")
    print(name)
