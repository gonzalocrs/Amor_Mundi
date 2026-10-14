"""DXF (CAD) export of the pyramid drawings. Reads the geometry recorded by pyramid_drawings.Sheet, so the CAD files always match the PDFs.

Each file has
  - MODEL space: the drawing at 1:1 in millimetres (insets drawn at a larger scale on a sheet are scaled up in model space,
    and their dimensions carry the matching DIMLFAC, so they still read true sizes);
  - a paper-space layout "A3 sheet" (420 x 297 mm) with ONE viewport at the sheet scale (1:50 or 1:10) and the title block,
    legend, notes and scale bar in paper space, exactly as in the PDF. Open the layout and plot at 1:1.
All dimensions are real DIMENSION entities (linear and aligned) with the dimension style "PYR" (DIMSCALE = sheet scale),
so they are associative to their definition points and remeasure when edited. Hatches are HATCH entities, rebar is drawn
at its true diameter (polyline width), everything is on named layers. Needs:  pip install ezdxf shapely
Run the whole set with:  python details/make_set.py"""
import math, os, sys
import ezdxf
from ezdxf import const
from ezdxf.enums import TextEntityAlignment as TA
from shapely.geometry import Polygon, LineString, MultiLineString, MultiPolygon, box
from shapely.ops import unary_union

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pyramid_drawings as pd

LAYERS = {   # name: (ACI colour, linetype, lineweight 1/100 mm)
    "OUTLINE-CUT": (7, "CONTINUOUS", 50), "OUTLINE-FINE": (7, "CONTINUOUS", 25), "LINES": (7, "CONTINUOUS", 25),
    "HIDDEN-AXIS": (8, "DASHED", 18), "BACKGROUND": (9, "CONTINUOUS", 13),
    "HATCH-PRINTED": (7, "CONTINUOUS", 9), "HATCH-CAST": (7, "CONTINUOUS", 9), "HATCH-EARTH": (8, "CONTINUOUS", 9),
    "PRINT-LAYERS": (7, "CONTINUOUS", 9), "AIR-ZONE-SYMBOL": (7, "CONTINUOUS", 13), "PRINTED-BEAD": (7, "CONTINUOUS", 25),
    "BUTTRESS-SOLID": (7, "CONTINUOUS", 25), "REBAR": (1, "CONTINUOUS", 0), "REBAR-POCKET": (8, "DASHED", 13),
    "DIMS": (3, "CONTINUOUS", 18), "ANNOTATION": (4, "CONTINUOUS", 18), "TEXT": (7, "CONTINUOUS", 18), "TITLEBLOCK": (7, "CONTINUOUS", 18),
}
LW = [0, 5, 9, 13, 15, 18, 20, 25, 30, 35, 40, 50, 53, 60, 70, 80, 90, 100, 106, 120, 140, 158, 200, 211]
nearest = lambda v: min(LW, key=lambda x: abs(x - v))
PATTERN = {"conc": ("ANSI31", "HATCH-PRINTED", 1.6), "cast": ("ANSI37", "HATCH-CAST", 1.6), "earth": ("EARTH", "HATCH-EARTH", 2.4), "dots": ("DOTS", "HATCH-INSULATION", 1.5)}
SPACING = 3.175       # ANSI31 line spacing at pattern scale 1


def _coords(g):
    return [list(g.exterior.coords)] + [list(r.coords) for r in g.interiors]


def _polys(g):
    if g.is_empty:
        return []
    if isinstance(g, Polygon):
        return [g]
    return [p for p in getattr(g, "geoms", []) if isinstance(p, Polygon)]


def _lines(g):
    if g.is_empty:
        return []
    if isinstance(g, LineString):
        return [g]
    return [l for p in getattr(g, "geoms", []) for l in _lines(p)]


def dim_text(label, measured):
    """'<>' lets CAD print the measured value; words around the number are kept"""
    m = "{:g}".format(round(measured))
    if label is None:
        return "<>"
    label = str(label)
    if label == m:
        return "<>"
    if m in label:
        return label.replace(m, "<>", 1)
    return label


def export_dxf(sh, path):
    doc = ezdxf.new("R2010", setup=True)
    doc.units = ezdxf.units.MM
    doc.header["$INSUNITS"] = 4
    doc.header["$MEASUREMENT"] = 1
    doc.header["$LTSCALE"] = float(sh.scale)
    doc.header["$PSLTSCALE"] = 0
    doc.header["$LWDISPLAY"] = 1
    msp = doc.modelspace()
    for name, (aci, lt, lw) in LAYERS.items():
        doc.layers.add(name, color=aci, linetype=lt, lineweight=lw)
    for name in ("HATCH-INSULATION", "CLADDING"):
        doc.layers.add(name, color=7, lineweight=9)
    S = float(sh.scale)
    ds = doc.dimstyles.new("PYR")
    ds.dxf.dimscale = S                 # overall scale: dimension text / ticks are sized in paper mm
    ds.dxf.dimtxt = 1.8
    ds.dxf.dimasz = 1.2
    ds.dxf.dimexo = 0.8
    ds.dxf.dimexe = 1.2
    ds.dxf.dimgap = 0.6
    ds.dxf.dimtad = 1
    ds.dxf.dimtih = 0
    ds.dxf.dimtoh = 0
    ds.dxf.dimdec = 0
    ds.dxf.dimzin = 8
    ds.dxf.dimlunit = 2
    ds.dxf.dimclrd = 3; ds.dxf.dimclre = 3; ds.dxf.dimclrt = 7
    ds.set_arrows(blk="ARCHTICK")
    dims = []
    fills, outlines, items = [], {}, []        # fills: [shapely geom, kind, layer]; outlines keyed for de-duplication
    clip = None

    def add_outline(pts, layer, lw, closed=False, tw=None, dash=None):
        for seg in _clip_line(pts, closed):
            key = (layer, tuple((round(x, 1), round(y, 1)) for x, y in seg), tw)
            keyr = (layer, tuple(reversed(key[1])), tw)
            if keyr in outlines:
                key = keyr
            old = outlines.get(key)
            if old is None or lw > old[0]:
                outlines[key] = (lw, closed and clip is None, tw, dash)

    def _clip_line(pts, closed):
        pts = list(pts)
        if closed and pts[0] != pts[-1]:
            pts.append(pts[0])
        if clip is None:
            return [pts]
        return [list(l.coords) for l in _lines(LineString(pts).intersection(clip)) if l.length > 1e-6]

    def sub(g):
        for f in fills:
            f[0] = f[0].difference(g)

    def layer_for_line(color, dash, layer):
        if layer:
            return layer
        if color in ("#a8a8a8", "#888", "#666", "#555", "#444") and not dash:
            return "BACKGROUND"
        return "HIDDEN-AXIS" if dash else "LINES"

    for r in sh.rec:
        k = r[0]
        if k == "clip":
            clip = box(r[1][0], r[1][1], r[1][2], r[1][3])
        elif k == "clipend":
            clip = None
        elif k == "poly":
            _, ps, fill, sw, stroke, layer, tw = r
            g = Polygon(ps)
            if not g.is_valid:
                g = g.buffer(0)
            gc = g if clip is None else g.intersection(clip)
            if fill == "#fff":
                sub(gc)
            elif fill == "#000":
                fills.append([gc, "solid", layer or "BUTTRESS-SOLID"])
            elif fill == "#555":
                fills.append([gc, "solid", layer or "CLADDING"])
            elif fill.startswith("url(#"):
                fills.append([gc, fill[5:-1], None])
            if sw > 0 and stroke != "#fff":
                ly = layer or ("OUTLINE-CUT" if sw >= 0.4 else "OUTLINE-FINE")
                if fill in ("#000",) and sw == 0:
                    pass
                add_outline(ps, ly, nearest(sw * 100), True, tw)
        elif k == "line":
            _, ps, sw, color, dash, layer, tw = r
            if color == "#fff" or color.startswith("url("):
                continue
            ly = layer_for_line(color, dash, layer)
            add_outline(ps, ly, nearest(sw * 100), False, tw, dash)
        elif k == "paths":
            _, polys, sw, layer = r
            for pl in polys:
                add_outline(pl, layer or "LINES", nearest(sw * 100))
        elif k == "circle":
            _, x, z, rad, filled, layer = r
            if clip is None or clip.contains(__import__("shapely.geometry", fromlist=["Point"]).Point(x, z)):
                items.append(("circle", x, z, rad, filled, layer or "LINES"))
        elif k == "text":
            items.append(r)
        elif k == "hatch":
            g = Polygon(r[1][0], r[1][1:])
            # even-odd rings: build by xor so nested rings alternate printed / open
            g = Polygon(r[1][0])
            for ring in r[1][1:]:
                g = g.symmetric_difference(Polygon(ring))
            fills.append([g, r[2], r[3]])
        elif k == "bead":
            _, pts, w, hatch, layer = r
            g = LineString(pts).buffer(w / 2, cap_style=2, join_style=2)
            gc = g if clip is None else g.intersection(clip)
            sub(gc)
            if hatch:
                fills.append([gc, "conc", None])
            for p in _polys(gc):
                for ring in _coords(p):
                    add_outline(ring, layer, 25, True)
        elif k == "solid":
            fills.append([Polygon(r[1]), "solid", r[2]])
        elif k == "ring":
            _, outer, inner, fill, hatch = r
            g = Polygon(outer).difference(Polygon(inner))
            if fill == "#fff":
                sub(g)
            elif fill == "#555":
                fills.append([g, "solid", "CLADDING"])
            if hatch and hatch.startswith("url(#"):
                fills.append([g, hatch[5:-1], None])
        elif k in ("dimh", "dimv", "dima"):
            dims.append(r)

    # ---- write fills
    for g, kind, layer in fills:
        for p in _polys(g):
            if p.area < 1.0:
                continue
            if kind == "solid":
                h = msp.add_hatch(color=7, dxfattribs={"layer": layer})
                h.set_solid_fill()
            else:
                pat, ly, spc = PATTERN[kind]
                h = msp.add_hatch(color=7, dxfattribs={"layer": layer or ly})
                h.set_pattern_fill(pat, scale=spc * S / SPACING, angle=0)
            for ring in _coords(p):
                h.paths.add_polyline_path([(x, y) for x, y in ring[:-1]], is_closed=True)
    # ---- write outlines
    for (layer, pts, tw), (lw, closed, _tw, dash) in outlines.items():
        pts = list(pts)
        if closed and len(pts) > 1 and pts[0] == pts[-1]:
            pts = pts[:-1]
        if len(pts) < 2:
            continue
        att = {"layer": layer, "lineweight": lw}
        if dash:
            att["linetype"] = "DASHDOT" if len(str(dash).split()) >= 4 else "DASHED"
        e = msp.add_lwpolyline(pts, close=closed, dxfattribs=att)
        if tw:
            e.dxf.const_width = float(tw)
            e.dxf.lineweight = 0
    # ---- circles, text
    for it in items:
        if it[0] == "circle":
            _, x, z, rad, filled, layer = it
            if filled:
                h = msp.add_hatch(color=7, dxfattribs={"layer": layer})
                h.set_solid_fill()
                h.paths.add_edge_path().add_arc((x, z), rad, 0, 360)
            else:
                msp.add_circle((x, z), rad, dxfattribs={"layer": layer, "lineweight": 18})
        else:
            _, x, z, s, size, anchor, rot, layer = it
            if not str(s).strip():
                continue
            t = msp.add_text(str(s), height=size * S * 0.72, rotation=-rot, dxfattribs={"layer": layer or "TEXT"})
            t.set_placement((x, z), align={"start": TA.BOTTOM_LEFT, "end": TA.BOTTOM_RIGHT}.get(anchor, TA.BOTTOM_CENTER))
    # ---- dimensions: real DIMENSION entities
    nd = 0
    for d in dims:
        if d[0] == "dimh":
            _, xs, z, ext, labels, size, lf = d
            for i, (a_, b_) in enumerate(zip(xs, xs[1:])):
                ov = {"dimlfac": lf} if abs(lf - 1) > 1e-9 else {}
                dm = msp.add_linear_dim(base=(a_, z), p1=(a_, ext), p2=(b_, ext), angle=0, dimstyle="PYR",
                                        text=dim_text(labels[i] if labels else None, (b_ - a_) * lf), override=ov, dxfattribs={"layer": "DIMS"})
                dm.render(); nd += 1
        elif d[0] == "dimv":
            _, zs, x, ext, labels, size, lf = d
            for i, (a_, b_) in enumerate(zip(zs, zs[1:])):
                ov = {"dimlfac": lf} if abs(lf - 1) > 1e-9 else {}
                dm = msp.add_linear_dim(base=(x, a_), p1=(ext, a_), p2=(ext, b_), angle=90, dimstyle="PYR",
                                        text=dim_text(labels[i] if labels else None, (b_ - a_) * lf), override=ov, dxfattribs={"layer": "DIMS"})
                dm.render(); nd += 1
        else:
            _, pts, t_, off, size, lf = d
            for a_, b_ in zip(pts, pts[1:]):
                u = (b_[0] - a_[0], b_[1] - a_[1]); L = math.hypot(*u)
                n = (-u[1] / L, u[0] / L)
                dist = off * (t_[0] * n[0] + t_[1] * n[1])
                ov = {"dimlfac": lf} if abs(lf - 1) > 1e-9 else {}
                dm = msp.add_aligned_dim(p1=a_, p2=b_, distance=dist, dimstyle="PYR", override=ov, dxfattribs={"layer": "DIMS"})
                dm.render(); nd += 1
    # ---- paper space: A3 sheet, one viewport at the sheet scale, title block / legend / notes / scale bar as in the PDF
    lay = doc.layouts.new("A3 sheet")
    lay.page_setup(size=(sh.w, sh.h), margins=(0, 0, 0, 0), units="mm")
    tb = sh.w - 112
    px0, px1, py0, py1 = 8.0, float(tb), 8.0, sh.h - 8.0        # drawing area, paper mm, y down
    pcx, pcy = (px0 + px1) / 2, (py0 + py1) / 2
    vp = lay.add_viewport(center=(pcx, sh.h - pcy), size=(px1 - px0, py1 - py0),
                          view_center_point=((pcx - sh.ox) * S, (sh.oz - pcy) * S), view_height=(py1 - py0) * S)
    vp.dxf.layer = "TITLEBLOCK"
    Y = lambda y: sh.h - y
    for i in sh.panel():
        if i[0] == "line":
            lay.add_line((i[1], Y(i[2])), (i[3], Y(i[4])), dxfattribs={"layer": "TITLEBLOCK", "lineweight": nearest(i[5] * 100)})
        elif i[0] == "rect":
            _, x, y, w_, h_, fill, sw = i
            pts = [(x, Y(y)), (x + w_, Y(y)), (x + w_, Y(y + h_)), (x, Y(y + h_))]
            if fill == "#000":
                hh = lay.add_hatch(color=7, dxfattribs={"layer": "TITLEBLOCK"}); hh.set_solid_fill(); hh.paths.add_polyline_path(pts, is_closed=True)
            lay.add_lwpolyline(pts, close=True, dxfattribs={"layer": "TITLEBLOCK", "lineweight": nearest(sw * 100)})
        elif i[0] == "circle":
            lay.add_circle((i[1], Y(i[2])), i[3], dxfattribs={"layer": "TITLEBLOCK", "lineweight": 18})
        else:
            _, x, y, size, txt, bold, anchor = i
            t = lay.add_text(str(txt), height=size * 0.72, dxfattribs={"layer": "TITLEBLOCK"})
            t.set_placement((x, Y(y)), align={"start": TA.BOTTOM_LEFT, "end": TA.BOTTOM_RIGHT}.get(anchor, TA.BOTTOM_CENTER))
    doc.layouts.set_active_layout("A3 sheet")
    doc.saveas(path + ".dxf")
    print("wrote", path + ".dxf", "({} polylines, {} hatches, {} dimensions; layout 'A3 sheet' at 1:{})".format(len(outlines), sum(1 for e in msp if e.dxftype() == "HATCH"), nd, sh.scale))


if __name__ == "__main__":
    import make_set
    make_set.main(dxf_only=True)
