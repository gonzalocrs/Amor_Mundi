"""replace the sheet-name field of a title-block sheet: python retitle.py <sheet.pdf> "LINE 1" ["LINE 2"]"""
import os, sys, subprocess, tempfile
import pikepdf, pypdf, pypdfium2 as pdfium
from pikepdf import Rectangle
import deck_sheets as ds

src, lines = sys.argv[1], sys.argv[2:]
cy = 306.5 - (len(lines) - 1) * 4.0
txt = "".join('<text x="545.5" y="%.1f" font-size="6.3" text-anchor="middle">%s</text>' % (cy + 8.0 * i + 2.2, l) for i, l in enumerate(lines))
svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="594mm" height="420mm" viewBox="0 0 594 420" font-family="Arial, Helvetica, sans-serif">'
       '<rect x="512.5" y="292.5" width="66" height="27.5" fill="#fff"/>%s</svg>' % txt)
d = tempfile.mkdtemp()
h = os.path.join(d, "t.html"); p = os.path.join(d, "t.pdf")
open(h, "w", encoding="utf-8").write('<!doctype html><html><head><meta charset="utf-8"><style>@page{size:594mm 420mm;margin:0}html,body{margin:0}svg{display:block;width:594mm;height:420mm}</style></head><body>%s</body></html>' % svg)
subprocess.run([ds.EDGE, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--print-to-pdf=" + p, "file:///" + h.replace("\\", "/")],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
MM = 72 / 25.4
pdf = pikepdf.open(src, allow_overwriting_input=True); ov = pikepdf.open(p)
pdf.pages[0].add_overlay(ov.pages[0], Rectangle(0, 0, 594 * MM, 420 * MM)); pdf.save(src)
pdfium.PdfDocument(src)[0].render(scale=100 / 72).to_pil().save(src[:-4] + ".png")
print("ok")
