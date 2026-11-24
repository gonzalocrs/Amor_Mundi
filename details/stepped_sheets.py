"""Stepped roofs v3e (0.5 m courses, printed pieces joined with their rib tube): plan, elevation and section A-A
for the 15x10 and the 10x10, drawn with the midterm Sheet class (pyramid_drawings.py) from 2D linework cut out of
the Rhino model (polyframe2/stepped-15x10-10x10-v3e-current.3dm, final layers) by
polyframe2/drawings-2026-11-20/extract_linework.py. Linework JSON in metres, roof-local; drawn here in mm.

Built by make_set.py (STEPPED_SHEETS). Conventions as the midterm set: greyscale, 1:50, cut outlines 0.6,
general 0.25, fine 0.13, below ground 0.3, dashed for overhead; hatches conc (printed), cast (cast concrete),
earth (ground); numbered callouts, level marks, real DIMENSION entities in the DXF."""
import os, json, math
import pyramid_drawings as pd

HERE = os.path.dirname(os.path.abspath(__file__))
LINEWORK = os.path.join(HERE, "..", "polyframe2", "drawings-2026-11-20", "linework-{}.json")
PAPER = {"15x10": ("A3", 420, 297), "10x10": ("A3", 420, 297)}          # midterm layout: every sheet A3 (Gonzalo 2026-11-21)
SCALE = {"15x10": 75, "10x10": 50}
PLACE = None          # press deck: (scale, centre x, centre y on the page, mm); set by press_sheets.py


def _gx():
    return 600 if (PLACE and PLACE[0] <= 100) else 1500     # ground line overhang (shorter on the A2 sheets)


def _scale(roof):
    return PLACE[0] if PLACE else SCALE[roof]                                        # 15x10 does not fit A3 at 1:50

PRINTED = ("printed pieces + rib (joined)", "printed pieces", "ribs (piece not joined)", "top course U formwork",
           "crown ring printed band", "base ring formwork", "rib ends (landings, crown domes)")
CAST = ("rib cores", "crown ring cast", "base ring cast", "columns", "footing")


class StepSheet(pd.Sheet):
    paper = "A3"
    axon = False

    def callout(self, *a, **k):
        if PLACE:
            return                     # press deck: dash notes instead of numbered callouts
        return super().callout(*a, **k)

    def panel(self):
        out = []
        for it in super().panel():
            if it[0] == "text":
                t = it[4]
                t = t.replace("Pyramid roof · 3D-printed concrete · GSAPP", "Stepped roofs v3e · 3D-printed concrete · GSAPP")
                t = t.replace(" at A3", " at " + self.paper)
                t = t.replace("2026-10-14 · hand estimates, not engineered", "2026-11-21 · drawn from the Rhino model (current.3dm)")
                if self.axon and t.startswith("Scale 1:"):
                    t = "Axonometric (parallel projection), not to scale · A3"
                it = it[:4] + (t,) + it[5:]
            if self.axon and it[0] in ("rect", "text") and abs(it[2] - (self.h - 30)) < 3.5:
                continue                       # no scale bar on the axonometric sheets
            out.append(it)
        return out


def load(roof):
    return json.load(open(LINEWORK.format(roof)))


def mm(pts):
    return [(p[0] * 1000.0, p[1] * 1000.0) for p in pts]


def _inside(pt, poly):
    x, y = pt; ins = False; n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]; x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            ins = not ins
    return ins


def _area(poly):
    return abs(sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1] for i in range(len(poly)))) / 2


def cut_regions(sh, items, sw=0.6):
    """closed cut loops, hatched by material; loops inside another loop of the same element are holes (white)"""
    loops = [(it["layer"], mm(it["pts"])) for it in items if it["closed"] and len(it["pts"]) > 2]
    loops.sort(key=lambda t: -_area(t[1]))
    depth = []
    for i, (ly, p) in enumerate(loops):
        d = sum(1 for j, (ly2, q) in enumerate(loops) if j < i and ly2 == ly and _inside(p[0], q))
        depth.append(d)
    for (ly, p), d in zip(loops, depth):
        hatch = "url(#cast)" if ly in CAST else "url(#conc)"
        if d % 2 == 0:
            sh.poly(p, "#fff", 0.0); sh.poly(p, hatch, 0.0)
        else:
            sh.poly(p, "#fff", 0.0)
    for (ly, p), d in zip(loops, depth):
        sh.poly(p, "none", sw if ly != "footing" else 0.35)


MERGE_PRINTED = ("printed pieces + rib (joined)", "printed pieces", "top course U formwork",
                 "crown ring printed band")
DROP_CUT = ("rib ends (landings, crown domes)",)          # landings / domes: inside the rings, they only add stray circles


def element_polygons(items):
    """shapely polygons per element, holes from nesting (even-odd within the same element)"""
    from shapely.geometry import Polygon
    loops = [(it["layer"], mm(it["pts"])) for it in items if it["closed"] and len(it["pts"]) > 2]
    loops.sort(key=lambda t: -_area(t[1]))
    polys = []
    for i, (ly, p) in enumerate(loops):
        d = sum(1 for j, (ly2, q) in enumerate(loops) if j < i and ly2 == ly and _inside(p[0], q))
        if d % 2 == 0:
            holes = [q for j, (ly2, q) in enumerate(loops) if j > i and ly2 == ly and _inside(q[0], p)
                     and sum(1 for k, (ly3, r) in enumerate(loops) if k < j and ly3 == ly and _inside(q[0], r)) == d + 1]
            g = Polygon(p, holes)
            if not g.is_valid:
                from shapely.validation import make_valid
                from shapely.ops import unary_union as _uu
                fixed = make_valid(g)
                parts = [x for x in getattr(fixed, "geoms", [fixed]) if x.geom_type in ("Polygon", "MultiPolygon")]
                g = _uu(parts) if parts else Polygon(p).buffer(0)
                if g.is_empty or g.area < 0.5 * Polygon(p).buffer(0).area * 0.1:   # make_valid collapsed it: keep the outline
                    g = Polygon(p).buffer(0)
            polys.append((ly, g))
    return polys


RIB_CUT = ("rib cores", "ribs", "ribs (piece not joined)", "rib ends (landings, crown domes)")
RIB_GREY = "#8c8c8c"


def _bounds(g):
    from shapely.geometry import LineString
    out = []
    for p in getattr(g, "geoms", [g]):
        if p.is_empty or p.geom_type != "Polygon":
            continue
        out.append(("ext", p.exterior)); out += [("int", r) for r in p.interiors]
    return out


def _lines(geom):
    return [list(x.coords) for x in getattr(geom, "geoms", [geom]) if x.geom_type in ("LineString", "LinearRing") and x.length > 3.0]


def clean_cut(sh, items, sw=0.5, sw_in=0.18):
    """section cut drawn as clean merged regions (Gonzalo's markups 2026-11-21).
    - every printed element unioned into one region, single hatch; its outer profile at the cut weight sw, the hollows
      inside the pieces (open-bottom voids, the hollow of the grown step) at a fine weight, so a step cut through its
      hollow reads the same weight as one cut through its pier (v06 drew both sides of each 3 cm wall at the cut weight,
      which made those steps look heavy)
    - the ribs (cast core + the 3 cm printed tube around it, rib slices, landings) drawn faint like the ribs beyond:
      white, thin grey outline, no hatch
    - rings, columns, footing: crossed hatch, cut weight."""
    from shapely.ops import unary_union
    polys = element_polygons(items)
    cores = unary_union([g for ly, g in polys if ly == "rib cores"])
    slices = unary_union([g for ly, g in polys if ly in RIB_CUT and ly != "rib cores"])
    pp = [g for ly, g in polys if (ly in MERGE_PRINTED and ly not in RIB_CUT) or ly == "base ring formwork"]
    cast = unary_union([g for ly, g in polys if ly in CAST and ly != "rib cores"])
    rib = unary_union([cores, slices]).difference(cast)          # rib pipes cut exactly (tube + core)
    # one profile per course (Gonzalo 2026-11-21): group the printed cuts by course (z ranges that overlap by > 5 cm),
    # each course drawn as one solid profile, hollows not drawn (the plane hits the hollow of the band on some courses and
    # the solid parts on others), so every step reads the same and the room face breaks at every bed joint
    from shapely.geometry import Polygon as _P
    groups = []
    for g in sorted(pp, key=lambda g: g.bounds[1]):
        b = g.bounds
        for grp in groups:
            if min(b[3], grp[1]) - max(b[1], grp[0]) > 50.0:
                grp[2].append(g); grp[0] = min(grp[0], b[1]); grp[1] = max(grp[1], b[3]); break
        else:
            groups.append([b[1], b[3], [g]])
    prof = []
    for z0_, z1_, gs in groups:
        for side in (-1, 1):                 # each course on each side: the solid outline of piece + band (hull)
            sg = [g for g in gs if (g.centroid.x > 0) == (side > 0)]
            if not sg:
                continue
            q = unary_union(sg).convex_hull.difference(cast).difference(rib)
            prof += [x for x in getattr(q, "geoms", [q]) if not x.is_empty and x.geom_type == "Polygon" and x.area > 50]
    from shapely.geometry import MultiPolygon as _MP
    printed = _MP(prof) if prof else _P()
    for geom, hatch in ((printed, "url(#conc)"), (cast, "url(#cast)")):
        for p in getattr(geom, "geoms", [geom]):
            if p.is_empty or p.area < 50:          # < 0.5 cm2: slivers
                continue
            ext_ = list(p.exterior.coords)[:-1]
            rings = [list(r.coords)[:-1] for r in p.interiors]
            sh._rec("hatch", [ext_] + rings, hatch[5:-1], None)
            sh.mute += 1
            sh.poly(ext_, "#fff", 0.0); sh.poly(ext_, hatch, 0.0)
            for r in rings:
                sh.poly(r, "#fff", 0.0)
            sh.mute -= 1
    # ribs: white, faint grey outline (core outline too)
    for p in getattr(rib, "geoms", [rib]):
        if p.is_empty or p.geom_type != "Polygon" or p.area < 20:
            continue
        sh.mute += 1; sh.poly(list(p.exterior.coords)[:-1], "#fff", 0.0)
        for r in p.interiors: sh.poly(list(r.coords)[:-1], "#fff", 0.0)
        sh.mute -= 1
    rl = []
    for kind, r in _bounds(rib) + _bounds(cores):
        rl += _lines(r)
    sh.paths(rl, 0.11, RIB_GREY)
    # outlines: printed profile at the cut weight except where it borders a rib (that edge is the rib's, grey);
    # hollows fine; cast at the cut weight
    keep = rib.buffer(1.5)
    ext_l, int_l = [], []
    for kind, r in _bounds(printed):
        (ext_l if kind == "ext" else int_l).extend(_lines(r.difference(keep)))     # edges along a rib are the rib's (faint)
    sh.paths(ext_l, sw, "#000"); sh.paths(int_l, sw_in, "#000")
    for p in getattr(cast, "geoms", [cast]):
        if p.is_empty or p.area < 50:
            continue
        for r in [p.exterior] + list(p.interiors):
            sh.poly(list(r.coords)[:-1], "none", sw)
    return unary_union([printed, cast, rib])


def clean_lines(items, mask=None, min_len=50.0, skip=()):
    """polylines in mm, minus everything within 5 mm of the cut regions, minus fragments shorter than min_len (5 cm)"""
    from shapely.geometry import LineString, MultiLineString
    from shapely.ops import linemerge
    segs = []
    for it in items:
        if it["layer"] in skip:
            continue
        p = mm(it["pts"] + ([it["pts"][0]] if it["closed"] else []))
        if len(p) >= 2:
            segs.append(LineString(p))
    if not segs:
        return []
    merged = linemerge(MultiLineString(segs))
    if mask is not None and not mask.is_empty:
        merged = merged.difference(mask.buffer(5.0))
    out = []
    for g in getattr(merged, "geoms", [merged]):
        if g.geom_type == "LineString" and g.length >= min_len:
            out.append(list(g.coords))
    return out


def lines(sh, items, sw, color="#000", dash=None, layer=None, skip=()):
    old, sh.layer = sh.layer, layer
    polys = [mm(it["pts"] + ([it["pts"][0]] if it["closed"] else [])) for it in items if it["layer"] not in skip]
    if dash:
        for p in polys:
            sh.line(p, sw, color, dash=dash)
    else:
        sh.paths(polys, sw, color, layer)
    sh.layer = old


def ext(items):
    xs = [p[0] * 1000 for it in items for p in it["pts"]]; ys = [p[1] * 1000 for it in items for p in it["pts"]]
    return min(xs), min(ys), max(xs), max(ys)


def centroid_of(items, layer, pick):
    cands = [mm(it["pts"]) for it in items if it["layer"] == layer and it["closed"]]
    if not cands:
        return None
    p = pick(cands)
    return (sum(q[0] for q in p) / len(p), sum(q[1] for q in p) / len(p))


def _sheet(roof, kind, scale=50):
    paper, W, H = PAPER[roof]
    return paper, W, H


def plan(roof):
    D = load(roof); d = D["drawings"]["plan"]; lv = D["levels"]
    paper, W, H = PAPER[roof]
    x0, y0, x1, y1 = ext(d["below"] + d["above"] + d["cut"])
    s = 1.0 / SCALE[roof]
    area_w = W - 112 - 16
    ox = 8 + area_w / 2 - (x0 + x1) / 2 * s
    oz = H / 2 + (y0 + y1) / 2 * s + 6
    if PLACE:
        s = 1.0 / PLACE[0]; ox = PLACE[1] - (x0 + x1) / 2 * s; oz = PLACE[2] + (y0 + y1) / 2 * s
    ncol = len([it for it in d["cut"] if it["layer"] == "columns"])
    sh = StepSheet(_scale(roof), ox, oz, "Plan · {} stepped roof".format(roof), "cut at +1.20, rib net and rings above (dashed)",
                   [(1, False, "Column, cast concrete in printed formwork, {} in all (cut).".format(ncol)),
                    (2, False, "Base ring step +{:.2f} to +{:.2f}, above (dashed): printed U formwork with the cast ring inside.".format(lv["base_ring_bottom"], lv["base_ring_top"])),
                    (3, False, "Rib net on the room face, above: printed rib tubes (pipes) with the cast cores inside, faint. Outlines dashed, centrelines dash-dot."),
                    (4, False, "Crown opening and crown ring at +{:.2f}, above (dashed).".format(lv["crown_top"])),
                    (5, True, "Strip footing frame with corner blocks, top {:.2f}, below ground (thin dashed).".format(lv["footing_top"]))],
                   ["Drawn from the Rhino model (stepped-15x10-10x10-v3e-current.3dm, rebuilt 2026-11-21): approved printed pieces, each with its growth band; ribs as pipes on the room face.",
                    "Levels: ±0.00 ground floor, +{:.2f} underside of the base ring, +{:.2f} first printed course.".format(lv["base_ring_bottom"], lv["base_ring_top"])],
                   W, H)
    sh.paper = paper
    lines(sh, d["below"], 0.18, "#000", dash="2 1")
    lines(sh, [it for it in d["above"] if it["layer"] != "rib net centrelines"], 0.25, "#000", dash="3 1.2")
    lines(sh, d.get("ribs_outline", []), 0.1, "#8c8c8c", dash="1.6 0.7")      # ribs faint (Gonzalo 2026-11-21)
    lines(sh, d.get("ribs_axis", []), 0.09, "#a8a8a8", dash="4 0.8 0.6 0.8")
    cut_regions(sh, d["cut"])
    # dimensions: base ring outer extents
    bx = [it for it in d["above"] if it["layer"] == "base ring (above)"]
    ex0, ey0, ex1, ey1 = ext(bx)
    sh.dim_h([ex0, ex1], ey0 - 900, ext=ey0, labels=["{:g} base ring, outside".format(round(ex1 - ex0))])
    sh.dim_v([ey0, ey1], ex1 + 900, ext=ex1, labels=["{:g}".format(round(ey1 - ey0))])
    co = [it for it in d["above"] if it["layer"] == "crown opening (above)"]
    if co:
        cx0, cy0, cx1, cy1 = ext(co)
        sh.dim_h([cx0, cx1], cy1 + 500, ext=cy1, labels=["{:g} crown opening".format(round(cx1 - cx0))])
        sh.dim_v([cy0, cy1], cx1 + 500, ext=cx1, labels=["{:g}".format(round(cy1 - cy0))])      # both directions (review 2026-11-23)
    # callouts
    col = centroid_of(d["cut"], "columns", lambda c: max(c, key=lambda p: sum(q[0] for q in p)))
    if col:
        sh.callout(1, col[0] + 1600, col[1] + 1200, col[0], col[1])
    sh.callout(2, ex1 - 600, ey1 + 1100, ex1 - 1500, ey1 - 150)
    rb = d.get("ribs_axis", [])
    if rb:
        p = mm(rb[len(rb) // 3]["pts"]); m = ((p[0][0] + p[-1][0]) / 2, (p[0][1] + p[-1][1]) / 2)
        sh.callout(3, m[0] - 1800, m[1] + 1500, m[0], m[1])
    if co:
        sh.callout(4, cx1 + _gx(), (cy0 + cy1) / 2 + 900, cx1, (cy0 + cy1) / 2)
    sh.callout(5, ex0 - 400, ey0 - 1700, ex0 + 300, ey0 + 200)
    if not PLACE:
        sh.text((x0 + x1) / 2, y0 - 2300, "section A-A on the long axis (y = 0), looking north", 2.4, italic=True)
    sh.line([(x0 - 600, 0), (x0 - 1300, 0)], 0.5); sh.circle_label(x0 - 1700, 0, "A", 2.6)
    sh.line([(x1 + 600, 0), (x1 + 1300, 0)], 0.5); sh.circle_label(x1 + 1700, 0, "A", 2.6)
    return sh


def elevation(roof):
    D = load(roof); d = D["drawings"]["elevation"]; lv = D["levels"]
    paper, W, H = PAPER[roof]
    x0, z0, x1, z1 = ext([it for it in d["visible"] if it["layer"] != "ground line"])
    s = 1.0 / SCALE[roof]
    area_w = W - 112 - 16
    ox = 8 + area_w / 2 - (x0 + x1) / 2 * s
    oz = 8 + (H - 16) / 2 + (z0 + z1) / 2 * s
    if PLACE:
        s = 1.0 / PLACE[0]; ox = PLACE[1] - (x0 + x1) / 2 * s; oz = PLACE[2] + (z0 + z1) / 2 * s
    nco = 18 if roof == "15x10" else 10
    sh = StepSheet(_scale(roof), ox, oz, "Elevation · {} stepped roof".format(roof), "long side, looking north",
                   [(1, False, "Printed courses, 0.5 m stepped ({} courses + the top course that is the formwork of the crown ring), exposed printed concrete; each piece carries its growth band on the outer face (covers the groove below and the ribs by 1 cm).".format(nco)),
                    (2, False, "Top course: printed U formwork with the cast crown ring, top +{:.2f}.".format(lv["crown_top"])),
                    (3, False, "Base ring step +{:.2f} to +{:.2f}, printed U formwork (cast ring inside).".format(lv["base_ring_bottom"], lv["base_ring_top"])),
                    (4, False, "Columns, cast in printed formwork, flush with the ring faces.")],
                   ["Visible lines only, from the model (Make2D, parallel view). The ribs are on the room face, behind the shell, so they do not show in elevation (see the section)."],
                   W, H)
    sh.paper = paper
    ground = [(x0 - _gx(), 0), (x1 + _gx(), 0)]
    sh.poly(pd.rect(x0 - _gx(), -900, x1 + _gx(), 0), "url(#earth)", 0.0)
    # courses as clean horizontal bands (Gonzalo 2026-11-21: no "barcode" of joints / seams on the curved ends):
    # printed layers keep only near-horizontal runs + one vertical edge at each end of every course; rest as drawn
    pr = [it for it in d["visible"] if it["layer"] in MERGE_PRINTED]
    hz = []
    for it in pr:
        pts = it["pts"]; cur = []
        for a, b in zip(pts, pts[1:]):
            if abs(b[1] - a[1]) <= 0.05 * max(abs(b[0] - a[0]), 1e-9):
                cur = cur or [a]; cur.append(b)
            else:
                if len(cur) > 1: hz.append(cur)
                cur = []
        if len(cur) > 1: hz.append(cur)
    lv_z = sorted(set(round(p[1], 2) for h in hz for p in h))
    ends = []
    zs_ = sorted(set(round((h[0][1] + h[-1][1]) / 2, 2) for h in hz))
    bands = []
    for z in zs_:
        if not bands or z - bands[-1][-1] > 0.06: bands.append([z])
        else: bands[-1].append(z)
    levels_ = [sum(b) / len(b) for b in bands]
    for za, zb in zip(levels_, levels_[1:]):
        seg = [h for h in hz if za - 0.03 <= (h[0][1] + h[-1][1]) / 2 <= zb + 0.03]
        if not seg: continue
        xa = min(min(p[0] for p in h) for h in seg if abs((h[0][1] + h[-1][1]) / 2 - za) < 0.03) if any(abs((h[0][1] + h[-1][1]) / 2 - za) < 0.03 for h in seg) else None
        if xa is None: continue
        # the course between za (bottom) and zb (top): its width is that of its top edge
        top = [h for h in seg if abs((h[0][1] + h[-1][1]) / 2 - zb) < 0.03]
        if not top: continue
        xl = min(min(p[0] for p in h) for h in top); xr_ = max(max(p[0] for p in h) for h in top)
        ends += [[(xl, za), (xl, zb)], [(xr_, za), (xr_, zb)]]
    sh.paths([mm(h) for h in hz], 0.2, "#000")
    sh.paths([mm(e) for e in ends], 0.2, "#000")
    lines(sh, [it for it in d["visible"] if it["layer"] not in MERGE_PRINTED], 0.2, skip=("ground line",))
    sh.line(ground, 0.5)
    xr = x1 + 600
    sh.dim_v([0, lv["base_ring_bottom"] * 1000, lv["base_ring_top"] * 1000, lv["crown_top"] * 1000], xr + 400, ext=xr,
             labels=["{:g}".format(lv["base_ring_bottom"] * 1000), "{:g}".format((lv["base_ring_top"] - lv["base_ring_bottom"]) * 1000),
                     "{:g}".format((lv["crown_top"] - lv["base_ring_top"]) * 1000)])
    for z, lab in ((0, "±0.00"), (lv["base_ring_bottom"], "+{:.2f} ring".format(lv["base_ring_bottom"])),
                   (lv["base_ring_top"], "+{:.2f} first course".format(lv["base_ring_top"])), (lv["crown_top"], "+{:.2f} crown".format(lv["crown_top"]))):
        sh.level(*((xr + (1500 if PLACE[0] <= 100 else 2600), z * 1000, lab, 1) if PLACE else (x0 - 700, z * 1000, lab, -1)))
    sh.dim_h([x0, x1], -1300, ext=0, labels=["{:g} overall".format(round(x1 - x0))])
    sh.callout(1, x1 - 1200, (lv["base_ring_top"] + lv["crown_top"]) * 500 + 1500, (x0 + x1) / 2 + (x1 - x0) * 0.2, (lv["base_ring_top"] + lv["crown_top"]) * 500)
    sh.callout(2, (x0 + x1) / 2 + 2600, lv["crown_top"] * 1000 + 900, (x0 + x1) / 2 + 900, lv["crown_top"] * 1000 - 200)
    sh.callout(3, x1 + 300, lv["base_ring_bottom"] * 1000 + 1300, x1 - 400, lv["base_ring_bottom"] * 1000 + 200)
    sh.callout(4, x1 + 300, 1000, x1 - 150, 1000)
    return sh


def section(roof):
    D = load(roof); d = D["drawings"]["section"]; lv = D["levels"]
    paper, W, H = PAPER[roof]
    x0, z0, x1, z1 = ext(d["cut"] + [it for it in d["beyond_clean"] if it["layer"] != "ground line"])
    s = 1.0 / SCALE[roof]
    area_w = W - 112 - 16
    ox = 8 + area_w / 2 - (x0 + x1) / 2 * s
    oz = 8 + (H - 16) / 2 + (z0 + z1) / 2 * s
    if PLACE:
        s = 1.0 / PLACE[0]; ox = PLACE[1] - (x0 + x1) / 2 * s; oz = PLACE[2] + (z0 + z1) / 2 * s
    sh = StepSheet(_scale(roof), ox, oz, "Section A-A · {} stepped roof".format(roof), "through the centre on the long axis, looking north",
                   [(1, False, "Printed piece (3 cm walls and lid, 6 x 4 groove on top, open at the bottom) with its growth band on the outer face (printed the same way, hollow), so every step covers the groove below and the ribs by 1 cm."),
                    (2, False, "Rib: printed tube (pipe) on the room face with the cast core inside. Drawn faint (thin grey) where cut, like the ribs beyond; at y = 0 one rib runs along the cut, so it shows lengthwise."),
                    (3, False, "Crown ring cast in the top course (printed U formwork), top +{:.2f}.".format(lv["crown_top"])),
                    (4, False, "Base ring step +{:.2f} to +{:.2f}: printed U formwork, cast ring inside.".format(lv["base_ring_bottom"], lv["base_ring_top"])),
                    (5, False, "Column, cast concrete, flush with the ring faces."),
                    (6, True, "Strip footing, underside {:.2f}.".format(lv["footing_bottom"]))],
                   ["Cut from the Rhino model at y = 0. Single hatch = printed concrete, drawn as the solid profile of each course (the hollows inside the pieces and bands are not drawn), crossed hatch = cast concrete (rings, columns, footing), grey = ground.",
                    "Beyond the cut: the ribs on the room face of the far half (light grey), course and step lines (fine)."],
                   W, H)
    sh.paper = paper
    sh.poly(pd.rect(x0 - _gx(), lv["footing_bottom"] * 1000 - 300, x1 + _gx(), 0), "url(#earth)", 0.0)
    # beyond (Gonzalo's markup 2026-11-21): only course/step lines, silhouettes of rings and columns, and the ribs faint;
    # no head joints, facets, seams or fragments < 5 cm, nothing over or along the cut
    from shapely.ops import unary_union
    mask = unary_union([g for ly, g in element_polygons(d["cut"]) if ly not in DROP_CUT])
    nonprinted = [it for it in d["beyond"] if it["layer"] not in MERGE_PRINTED + DROP_CUT + ("ground line", "ribs", "rib cores")]
    courses = []
    for it in d["beyond"]:                      # course / step lines only: near-horizontal runs of the printed pieces
        if it["layer"] not in MERGE_PRINTED:
            continue
        pts = it["pts"]; cur = []
        for a, b in zip(pts, pts[1:]):
            if abs(b[1] - a[1]) <= 0.05 * max(abs(b[0] - a[0]), 1e-9):
                cur = cur or [a]; cur.append(b)
            else:
                if len(cur) > 1: courses.append({"layer": it["layer"], "pts": cur, "closed": False})
                cur = []
        if len(cur) > 1: courses.append({"layer": it["layer"], "pts": cur, "closed": False})
    sh.paths(clean_lines(courses, mask, 100.0), 0.13, "#000")
    sh.paths(clean_lines(nonprinted, mask, 50.0), 0.18, "#000")
    sh.paths(clean_lines(d.get("ribs_outline", []), mask, 50.0), 0.11, "#8c8c8c")   # ribs faint
    clean_cut(sh, d["cut"])
    sh.line([(x0 - _gx(), 0), (x1 + _gx(), 0)], 0.5)
    xr = x1 + 600
    zs = [lv["footing_bottom"] * 1000, 0, lv["base_ring_bottom"] * 1000, lv["base_ring_top"] * 1000, lv["crown_top"] * 1000]
    sh.dim_v(zs, xr + 400, ext=xr, labels=["{:g}".format(round(b - a)) for a, b in zip(zs, zs[1:])])
    for z, lab in ((lv["footing_bottom"], "{:.2f}".format(lv["footing_bottom"])), (0, "±0.00"),
                   (lv["base_ring_top"], "+{:.2f}".format(lv["base_ring_top"])), (lv["crown_top"], "+{:.2f} crown".format(lv["crown_top"]))):
        sh.level(*((xr + (1500 if PLACE[0] <= 100 else 2600), z * 1000, lab, 1) if PLACE else (x0 - 700, z * 1000, lab, -1)))
    cols = [mm(it["pts"]) for it in d["cut"] if it["layer"] == "columns"]
    if len(cols) >= 2:
        cxs = sorted(min(q[0] for q in p) for p in cols) + sorted(max(q[0] for q in p) for p in cols)
        a, b = min(cxs), max(cxs)
        sh.dim_h([a, b], lv["footing_bottom"] * 1000 - 900, ext=lv["footing_bottom"] * 1000, labels=["{:g} columns, outside".format(round(b - a))])
    # callouts on the right half
    right = lambda c: max(c, key=lambda p: (sum(q[0] for q in p) / len(p)))
    def mid_piece(c):
        zt = (lv["base_ring_top"] + lv["crown_top"]) * 500
        rr = [p for p in c if sum(q[0] for q in p) / len(p) > 0]
        return min(rr or c, key=lambda p: abs(sum(q[1] for q in p) / len(p) - zt))
    pc = centroid_of(d["cut"], "printed pieces", mid_piece)
    if pc: sh.callout(1, pc[0] + 2600, pc[1] + 600, pc[0], pc[1])
    cc = centroid_of(d["cut"], "rib cores", mid_piece)
    if cc: sh.callout(2, cc[0] + 2400, cc[1] - 900, cc[0], cc[1])
    cr = centroid_of(d["cut"], "crown ring cast", right)
    if cr: sh.callout(3, cr[0] + 1800, cr[1] + 1200, cr[0], cr[1])
    br = centroid_of(d["cut"], "base ring cast", right)
    if br: sh.callout(4, br[0] + 1900, br[1] + 900, br[0], br[1])
    co = centroid_of(d["cut"], "columns", right)
    if co: sh.callout(5, co[0] + 1700, co[1] - 300, co[0], co[1])
    ft = centroid_of(d["cut"], "footing", right)
    if ft: sh.callout(6, ft[0] + 1700, ft[1] - 200, ft[0], ft[1])
    return sh



AXON = os.path.join(HERE, "..", "polyframe2", "drawings-2026-11-20", "_tmp_axon_{}.json")


def axon(name):
    d = json.load(open(AXON.format(name)))["visible"]
    x0, y0, x1, y1 = ext(d)
    scale = 125
    s = 1.0 / scale
    area_w = 420 - 112 - 16
    ox = 8 + area_w / 2 - (x0 + x1) / 2 * s
    oz = 8 + (297 - 16) / 2 + (y0 + y1) / 2 * s
    if name == "iso":
        title, sub = "Axonometric · both modules", "15x10 and 10x10 stepped roofs, from the south-east, above"
        legend = [(1, False, "15x10 module: 18 printed courses + the top course (crown ring formwork), each piece with its growth band; base ring step on 19 columns, strip footing."),
                  (2, False, "10x10 module: 10 printed courses + the top course; base ring step on 15 columns, strip footing."),
                  (3, False, "Crown opening and crown ring; the ribs end inside the ring, nothing above the crown.")]
        notes = ["Visible lines only, from the rebuilt Rhino model (Make2D, parallel projection). Fine lines = course and piece joints (2 mm head joints)."]
    else:
        title, sub = "Worm's-eye view · both modules", "from below, looking up into the roofs (south-east)"
        legend = [(1, False, "Rib net on the room face of the 15x10: printed rib tubes (pipes) with cast cores, continuous from the base ring to the crown ring (grey)."),
                  (2, False, "Rib net of the 10x10, same system."),
                  (3, False, "Base ring step and columns (footing omitted).")]
        notes = ["Visible lines only, from the rebuilt Rhino model (Make2D, parallel projection, looking up). Ribs in grey like the rest of the set."]
    sh = StepSheet(scale, ox, oz, title, sub, legend, notes, 420, 297)
    sh.axon = True
    rib = [it for it in d if it["layer"] == "ribs"]
    rest = [it for it in d if it["layer"] != "ribs"]
    pieces = [it for it in rest if it["layer"] in ("printed pieces", "top course U formwork")]
    other = [it for it in rest if it["layer"] not in ("printed pieces", "top course U formwork")]
    if name == "iso":
        lines(sh, pieces, 0.12, "#000"); lines(sh, other, 0.2, "#000"); lines(sh, rib, 0.12, "#7a7a7a")
    else:                                   # worm's-eye: the rib net is the subject, piece joints recede
        lines(sh, pieces, 0.07, "#a0a0a0"); lines(sh, other, 0.2, "#000"); lines(sh, rib, 0.16, "#222")
    return sh


def sheets():
    out = []
    n = 11
    for roof in ("15x10", "10x10"):
        for kind, fn in (("plan", plan), ("elevation", elevation), ("section-AA", section)):
            out.append(("{:02d}".format(n), "stepped-{}-{}".format(roof, kind), (lambda fn=fn, roof=roof: fn(roof)), ""))
            n += 1
    out.append(("{:02d}".format(n), "stepped-both-axonometric", (lambda: axon("iso")), "")); n += 1
    out.append(("{:02d}".format(n), "stepped-both-wormseye", (lambda: axon("worm")), ""))
    return out
