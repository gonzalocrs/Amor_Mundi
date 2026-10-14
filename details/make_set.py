"""Builds the complete drawing set: one A3 PDF per sheet, the whole set as one PDF, and an editable DXF per sheet
(model space 1:1 in mm, paper-space layout "A3 sheet" at the sheet scale, real DIMENSION entities).

Run:  python details/make_set.py      ->  details/set/NN-name.pdf, details/set/pyramid-roof-drawing-set.pdf, details/set/cad/NN-name.dxf,
                                          details/set/cad/pyramid-roof-drawing-set.dxf (all sheets in one file, one layout each)
Needs:  pip install cairosvg ezdxf shapely   (and pdfunite from poppler-utils, or pypdf, to merge the set)"""
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
            import cairosvg
            cairosvg.svg2pdf(bytestring=sh.svg().encode(), write_to=base + ".pdf")
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
