"""Builds the complete drawing set: one A3 PDF per sheet, the whole set as one PDF, and an editable DXF per sheet
(model space 1:1 in mm, paper-space layout "A3 sheet" at the sheet scale, real DIMENSION entities).

Run:  python details/make_set.py      ->  details/set/NN-name.pdf, details/set/pyramid-roof-drawing-set.pdf, details/set/cad/NN-name.dxf,
                                          details/set/cad/pyramid-roof-drawing-set.dxf (all sheets in one file, one layout each)
Needs:  pip install cairosvg ezdxf shapely   (and pdfunite from poppler-utils, or pypdf, to merge the set)
        cairosvg needs the Cairo library; without it (Windows without the GTK runtime) the PDFs are printed with headless Microsoft Edge (or Chrome)."""
import os, sys, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pyramid_drawings as pd
import roof_grid as rg
import roof_slice as rs

SHEETS = [   # (number, file name, builder, scale note)
    ("01", "floor-plan", lambda: pd.plan(), ""),
    ("02", "floor-plan-grid-A", lambda: pd.plan("A"), ""),
    ("03", "floor-plan-grid-B", lambda: pd.plan("B"), ""),
    ("04", "section-AA-grid-A", lambda: pd.section("A"), ""),
    ("05", "section-AA-grid-B", lambda: pd.section("B"), ""),
    ("06", "roof-plan-cut-grid-A", lambda: rs.sheet("A"), ""),
    ("07", "roof-plan-cut-grid-B", lambda: rs.sheet("B"), ""),
    ("08", "roof-grid-A-elevation", lambda: rg.sheet("A"), "rib plan cut 1:10, rib section 1:20"),
    ("09", "roof-grid-B-elevation", lambda: rg.sheet("B"), "rib plan cut 1:10, rib section 1:20"),
    ("10", "detail-D1-eave", lambda: pd.detail(), "rib plan cut 1:5"),
]

BROWSERS = [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            "msedge", "microsoft-edge", r"C:\Program Files\Google\Chrome\Application\chrome.exe", "google-chrome", "chromium"]   # Edge first: on every Windows PC

def svg_to_pdf(sh, path):
    """cairosvg; if its Cairo library is missing (Windows without the GTK runtime), print the SVG with headless Microsoft Edge (or Chrome) instead"""
    svg = sh.svg()
    try:
        import cairosvg
        cairosvg.svg2pdf(bytestring=svg.encode(), write_to=path)
        return
    except (ImportError, OSError) as e:
        err = e
    import shutil, tempfile
    browser = next((b for b in BROWSERS if os.path.isfile(b) or shutil.which(b)), None)
    if browser is None:
        raise RuntimeError("cairosvg cannot run ({}) and no Chrome / Edge was found: install Cairo (GTK runtime on Windows)".format(err))
    with tempfile.TemporaryDirectory() as d:
        html = os.path.join(d, "sheet.html")
        with open(html, "w", encoding="utf-8") as f:
            f.write('<!doctype html><html><head><meta charset="utf-8"><style>@page {{ size: {0}mm {1}mm; margin: 0 }} '
                    'html, body {{ margin: 0; width: {0}mm; height: {1}mm; overflow: hidden }} svg {{ display: block }}</style></head>'
                    '<body>{2}</body></html>'.format(sh.w, sh.h, svg))
        subprocess.run([browser, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--print-to-pdf=" + os.path.abspath(path),
                        "file:///" + html.replace("\\", "/")], check=True, capture_output=True, timeout=120)

def main(dxf_only=False):
    import cad_export
    here = os.path.dirname(os.path.abspath(__file__))
    out = os.path.join(here, "set"); cad = os.path.join(out, "cad")
    os.makedirs(cad, exist_ok=True)
    pdfs, sheets = [], []
    for no, name, build, note in SHEETS:
        sh = build()
        sh.sheet_no, sh.scale_note = no, note
        base = os.path.join(out, "{}-{}".format(no, name))
        if not dxf_only:
            svg_to_pdf(sh, base + ".pdf")
            pdfs.append(base + ".pdf")
            print("wrote", base + ".pdf")
        cad_export.export_dxf(sh, os.path.join(cad, "{}-{}".format(no, name)))
        sheets.append(("{} {}".format(no, name), sh))
    cad_export.export_set(sheets, os.path.join(cad, "pyramid-roof-drawing-set.dxf"))
    if pdfs:
        merged = os.path.join(out, "pyramid-roof-drawing-set.pdf")
        try:
            subprocess.run(["pdfunite"] + pdfs + [merged], check=True)
        except Exception:
            from pypdf import PdfWriter
            w = PdfWriter()
            for p in pdfs: w.append(p)
            w.write(merged)
        print("wrote", merged)

if __name__ == "__main__":
    main()
