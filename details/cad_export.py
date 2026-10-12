"""DXF (CAD) export of the pyramid drawings. Reads the geometry recorded by pyramid_drawings.Sheet, so the CAD files always match the PDFs.

Model space, millimetres, 1:1 (the PDFs are 1:50 / 1:50 / 1:10; text and symbols are sized for those scales, and
dashed linetypes use LTSCALE = scale). Everything is on named layers; hatches are real HATCH entities, rebar is drawn
at its TRUE diameter (polyline width), printed layers are every 10 mm. Needs:  pip install ezdxf shapely

Run:  python details/cad_export.py [out_dir]   ->  pyramid-plan.dxf, pyramid-section.dxf, pyramid-detail.dxf"""
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
PATTERN = {"conc": ("ANSI31", "HATCH-PRINTED", 1.6), "cast": ("ANSI37", "HATCH-CAST", 1.6), "earth": ("EARTH", "HATCH-EARTH", 2.4)}
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


def export_dxf(sh, path):
    doc = ezdxf.new("R2010", setup=True)
    doc.units = ezdxf.units.MM
    doc.header["$LTSCALE"] = float(sh.scale)
    doc.header["$LWDISPLAY"] = 1
    msp = doc.modelspace()
    for name, (aci, lt, lw) in LAYERS.items():
        doc.layers.add(name, color=aci, linetype=lt, lineweight=lw)
    S = float(sh.scale)
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
    # ---- title / legend / notes block, to the right of the drawing
    xs = [c[0] for e in msp if e.dxftype() == "LWPOLYLINE" for c in e.get_points()]
    if not xs:
        xs = [0.0]
    ys = [c[1] for e in msp if e.dxftype() == "LWPOLYLINE" for c in e.get_points()]
    x0, y = max(xs) + 12 * S, max(ys)
    h = 2.8 * S * 0.72
    def put(txt, size=2.8, bold=False):
        nonlocal y
        t = msp.add_text(txt, height=size * S * 0.72, dxfattribs={"layer": "TITLEBLOCK"})
        t.set_placement((x0, y), align=TA.BOTTOM_LEFT)
        y -= (size * 1.45) * S
    put(sh.title, 5.4); put(sh.sub, 3.1); y -= 4 * S
    for n, assumed, txt in sh.legend:
        for i, l in enumerate(pd.wrap(txt, 70)):
            put(("({}{}) ".format(n, "*" if assumed else "") if i == 0 else "      ") + l)
        y -= 1 * S
    if sh.legend:
        put("* = assumed, to confirm"); y -= 3 * S
    put("Notes", 3.1)
    for n_ in sh.notes:
        for i, l in enumerate(pd.wrap(n_, 78)):
            put(("- " if i == 0 else "  ") + l)
    y -= 3 * S
    put("Model space, mm, 1:1. Drawn for 1:{} at A3 (text, symbols, linetypes). Rebar at true diameter; printed layers 10 mm.".format(sh.scale), 2.6)
    doc.saveas(path + ".dxf")
    print("wrote", path + ".dxf", "({} polylines, {} hatches)".format(len(outlines), sum(1 for e in msp if e.dxftype() == "HATCH")))


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "cad")
    os.makedirs(out, exist_ok=True)
    export_dxf(pd.plan(), os.path.join(out, "pyramid-plan"))
    export_dxf(pd.section(), os.path.join(out, "pyramid-section"))
    export_dxf(pd.detail(), os.path.join(out, "pyramid-detail"))
