"""white out a rectangle (mm, A2 page, from top-left) on a sheet PDF: python whiteout.py <sheet.pdf> x y w h"""
import os, sys, subprocess, tempfile
import pikepdf, pypdfium2 as pdfium
from pikepdf import Rectangle
import deck_sheets as ds

src = sys.argv[1]; x, y, w, h = map(float, sys.argv[2:6])
svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="594mm" height="420mm" viewBox="0 0 594 420">'
       '<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" fill="#fff"/></svg>' % (x, y, w, h))
d = tempfile.mkdtemp(); hp = os.path.join(d, "t.html"); pp = os.path.join(d, "t.pdf")
open(hp, "w", encoding="utf-8").write('<!doctype html><html><head><meta charset="utf-8"><style>@page{size:594mm 420mm;margin:0}html,body{margin:0}svg{display:block;width:594mm;height:420mm}</style></head><body>%s</body></html>' % svg)
subprocess.run([ds.EDGE, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--print-to-pdf=" + pp, "file:///" + hp.replace("\\", "/")],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
MM = 72 / 25.4
pdf = pikepdf.open(src, allow_overwriting_input=True); ov = pikepdf.open(pp)
mb = pdf.pages[0].mediabox
pdf.pages[0].add_overlay(ov.pages[0], Rectangle(float(mb[0]), float(mb[1]), float(mb[0]) + 594 * MM, float(mb[1]) + 420 * MM)); pdf.save(src)
pdfium.PdfDocument(src)[0].render(scale=100 / 72).to_pil().save(src[:-4] + ".png")
print("ok")
