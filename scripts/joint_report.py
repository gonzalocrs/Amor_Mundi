"""Drawing set comparing the three ways to print the oval one-piece joint (Gonzalo, 2026-10-18):

  1   pump stops: the ring's room-side wall is its own contour (scripts/joint_toolpath.py)
  2   no stops, the path crosses the tunnel mouth at both ends; the two plugs are cut out green (scripts/joint_nostop.py)
  2b  no stops, the crossings are printed one bead past each end and trimmed off flush, a straight cut
  3   no ring tunnel: the ring course is printed with 4 ducts and post-tensioned (scripts/joint_tendon.py)

`python scripts/joint_report.py` writes details/piece-test/joint-options.pdf (A3 sheets) and a PNG of each sheet.
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Polygon as MP, Rectangle, Circle
from shapely.affinity import scale as _scale, translate as _translate
from shapely.geometry import LineString, box
from shapely.ops import unary_union

import joint_shapes as J
import joint_toolpath as T
import joint_tendon as TT
import joint_nostop as N
import joint_flare as F
import piece_test

SHAPE = "oval"
L, H, lh, B = J.P["L"], J.P["H"], J.P["lh"], J.B
h = B / 2
W, HH = 420.0, 297.0                                    # A3 landscape, mm
INK, GREY, PATH = "#1a1a1a", "#8a8a8a", "#c0392b"
plt.rcParams.update({"font.family": "Liberation Sans", "font.size": 6.5, "hatch.linewidth": 0.3,
                     "hatch.color": "#555555", "lines.solid_capstyle": "butt",
                     "pdf.fonttype": 42, "svg.fonttype": "none"})   # live, editable text in Illustrator


# ---------------------------------------------------------------- data
def options():
    p = dict(L=L, layer_H=lh, bead=B, speed=J.P["speed"])
    st = J.study(SHAPE)
    tp = T.layer_paths(SHAPE)
    _, t1, s1 = piece_test.gcode(dict(p=p, col=tp), "col")
    sec1 = unary_union([box(x["void"][0], x["s"] - lh / 2, x["void"][1], x["s"] + lh / 2)
                        for x in st["layers"] if x["void"]])
    o1 = dict(key="1", style="stop", name="Pump stops", layers=st["layers"], paths=[l["cons"] for l in tp], sec=sec1,
              time=t1 / 60, stops=s1, mass=st["mass"], crown=st["tunnel"][1], over=st["max_over"])
    out = [o1]
    for ext, key, name in ((True, "2", "No stops, ends trimmed"),):
        r = N.study_oval(ext)
        _, t, s = piece_test.gcode(dict(p=p, col=r["layers"]), "col")
        out.append(dict(key=key, style="trim" if ext else "plug", name=name, layers=r["layers"], paths=[x["cons"] for x in r["layers"]], sec=r["sec"],
                        time=t / 60, stops=s, mass=r["mass"], crown=r["crown"], over=r["max_over"], ext=ext))
    r = TT.study()
    _, t3, s3 = piece_test.gcode(dict(p=p, col=r["layers"]), "col")
    out.append(dict(key="3", style="tendon", name="Tendons through the print", layers=r["layers"],
                    paths=[x["cons"] for x in r["layers"]], sec=box(0, 0, 0, 0).buffer(0), time=t3 / 60, stops=s3,
                    mass=r["mass"], crown=None, over=r["max_over"]))
    for o in out:
        o["ring_l"] = o["sec"].area * L / 1e6           # litres of ring concrete per piece
    return out, st["cages"]


# option 3: the ring course itself is the ring, post-tensioned through four printed ducts (scripts/joint_tendon.py)
DR = TT.DUCT / 2
TENDON = "#1a1a1a"


def draw_ducts(a, pts=None, strand=True):
    for n, s in pts or TT.ducts():
        a.add_patch(Circle((n, s), DR, fc="white", ec=INK, lw=0.5, zorder=5))
        if strand:
            a.add_patch(Circle((n, s), 6.5, fc=TENDON, ec="none", zorder=6))


def draw_tendon_section(a, o, u, dims=True, upto=None, tubes=True):
    lays = o["layers"] if upto is None else o["layers"][:upto]
    g = section(dict(layers=lays), u)
    cut(a, g)
    cvs = J.col_void(SHAPE).intersection(LineString([(u, -1e3), (u, 1e3)]))
    if not cvs.is_empty and upto is None:
        lo_, hi_ = sorted(q[1] for q in cvs.coords)
        cast(a, box(lo_, 0, hi_, H))
    if tubes:
        draw_ducts(a, [(n, s) for n, s in TT.ducts() if upto is None or s < upto * lh], strand=upto is None)
    if upto is None:
        a.plot([-170, 290], [0, 0], color=INK, lw=1.0)
        a.text(285, -8, "PRINT BED", fontsize=4.8, ha="right", va="top")
    if dims:
        dim(a, (0, H), (240, H), 22, "240 shell")
        s0, s1 = TT.DUCT_S
        dim(a, (240, 0), (240, s0), 30, "{:.0f}".format(s0))
        dim(a, (240, s0), (240, s1), 30, "{:.0f}".format(s1 - s0))
        dim(a, (240, s1), (240, H), 30, "{:.0f}".format(H - s1))
        a.text(-165, 8, "ROOM SIDE", fontsize=5, rotation=90, va="bottom")


def draw_tendon_iso(a, o):
    a.add_patch(MP([iso(-60, -230, 0), iso(L + 60, -230, 0), iso(L + 60, 280, 0), iso(-60, 280, 0)], closed=True,
                   fc="none", ec=GREY, lw=0.3, ls=(0, (4, 3))))
    for n, s in sorted(TT.ducts(), key=lambda p: -p[0]):          # strands out of the far end, behind the piece
        xs, ys = zip(iso(-260, n, s), iso(0, n, s))
        a.plot(xs, ys, color=TENDON, lw=0.8, zorder=zn())
    draw_stack(a, [(x["s"] + lh / 2, [(x["geom"].intersection(box(0, -1e3, L, 1e3)), "p")]) for x in o["layers"]])
    for n, s in sorted(TT.ducts(), key=lambda p: -p[0]):          # and out of the near end, in front of it
        iso_block(a, L, L + 60, n - DR, n + DR, s - DR, s + DR, fc="#f4f3ef", top="#ffffff", side="#dcdad3")
        xs, ys = zip(iso(L + 60, n, s), iso(L + 330, n, s))
        a.plot(xs, ys, color=TENDON, lw=0.8, zorder=zn())


def tendon_sheet(o, cg, num):
    fig, fr = sheet(num, "Option 3: tendons through the print", "No ring tunnel: the ring course is printed with 4 "
                    "ducts and post-tensioned. Dimensions in mm.")
    a = view(fig, 22, 166, (-170, 300), (-30, 500), 5)
    draw_tendon_section(a, o, 300.0)
    caption(fig, 22, 282, "1", "Section between columns", 5)
    note(a, (-160, 150), "duct Ø25, 0.5\" monostrand\n(greased and sheathed)", to=(TT.DUCT_N[0] - 8, TT.DUCT_S[0] - 8))
    note(a, (-160, 300), "bead B steps out 7 mm\na layer to open the groove", to=(68, TT.DUCT_S[1] - 30))
    note(a, (-160, 420), "next layer: B comes\nback, resting on the tube", to=(45, TT.DUCT_S[1] + 18))
    a = view(fig, 122, 166, (-170, 300), (-30, 500), 5)
    draw_tendon_section(a, o, 600.0, dims=False)
    caption(fig, 122, 282, "2", "Section at a column", 5)
    note(a, (-160, 470), "column, cast in\nthe channel", to=(-60, 400))
    c = TT.tendon_check()
    y = 276
    fr.text(232, y + 3, "HOW IT WORKS", fontsize=7, fontweight="bold")
    lines = ["Like Masoud's printed bridges: printed concrete in compression,",
             "steel tendons in tension. No ring tunnel and no ring pour. The",
             "ring course is printed like a regular piece, as one continuous",
             "path, with 4 ducts along it. Bead B (and O2 on the weather side)",
             "steps 7 mm a layer away from the face bead, opening a 25 mm",
             "groove; a duct tube is laid in by hand (about a minute a layer);",
             "the next layer comes back over it. Each duct is closed by the",
             "30 mm end bead at both ends: drill through (8 short holes).",
             "",
             "On site: lay the courses, cast the columns, thread one",
             "monostrand per line of ducts, corner to corner, anchor on the",
             "hip ribs and stress. Joints between pieces: mortar, kept closed",
             "by the prestress.",
             "",
             "HAND CHECK (middle ring, Karamba final run)",
             "N = 26 kN, My = 9.0 kNm, Mz = 14.7 kNm. Section: beads A, B,",
             "O2, O1 only, 450 tall: A = {:.0f} cm², W = {:.0f} / {:.0f} cm³".format(c["A"] / 100, c["Wn"] / 1e3,
                                                                                c["Ws"] / 1e3),
             "Bending ±{:.1f} MPa, axial −{:.1f}: needs ≥ {:.0f} kN per tendon".format(c["sb"], c["sN"], c["need"] / 1e3),
             "4 × 0.5\" at {:.0f} kN jacked, {:.0f} kN after losses: {:.1f} MPa".format(c["P0"] / 1e3, c["Pe"] / 1e3, c["sp"]),
             "Edges stay in compression: {:.1f} to {:.1f} MPa".format(c["smin"], c["smax"]),
             "Needs: printed mix ≥ 35 MPa, stressed at ≥ 28 MPa;",
             "this course of the shell becomes structural."]
    for line in lines:
        fr.text(232, y - 4, line, fontsize=6.0, va="top", fontweight="bold" if line.startswith("HAND") else "normal")
        y -= 3.8
    y -= 9
    rows = [("Pump stops per piece", "{:d}".format(o["stops"])), ("Print time", "{:.0f} min".format(o["time"])),
            ("Printed mass", "{:.0f} kg".format(o["mass"])), ("Worst overhang step", "{:.1f} mm".format(o["over"])),
            ("Ring concrete per piece", "none")]
    for k, v in rows:
        fr.plot([232, 330], [y - 1.6, y - 1.6], lw=0.2, color="#999999")
        fr.text(232, y, k, fontsize=6.2)
        fr.text(330, y, v, fontsize=6.2, ha="right", fontweight="bold")
        y -= 4.6
    # the groove, step by step (bottom duct)
    j0 = TT.LOW
    steps = [(j0 + len(TT.OPEN), False, "a  groove opens, 7 mm a layer"), (j0 + len(TT.OPEN), True, "b  lay the duct tube"),
             (j0 + len(TT.OPEN) + 3, True, "c  print on over it")]
    for k, (upto, tube, t) in enumerate(steps):
        b = view(fig, 340, 228 - k * 36, (-10, 250), (30, 140), 4)
        draw_tendon_section(b, o, 300.0, dims=False, upto=upto, tubes=tube)
        fig.text(340 / W, (228 - k * 36 + 30) / HH, t, fontsize=5.5)
    caption(fig, 340, 282, "5", "Printing a duct", 4)
    # elevation
    a = view(fig, 22, 80, (-300, 1400), (-60, 520), 10)
    a.add_patch(Rectangle((0, 0), L, H, fc="white", ec=INK, lw=0.7))
    for s in range(10, int(H), 10):
        a.plot([0, L], [s, s], color="#c9c9c4", lw=0.15)
    cv = J.col_void(SHAPE).bounds
    for uu in (cv[0], cv[2]):
        a.plot([uu, uu], [0, H], color=INK, lw=0.35, ls=(0, (3, 2)))
    for s in TT.DUCT_S:
        for ss in (s - DR, s + DR):
            a.plot([30, L - 30], [ss, ss], color=INK, lw=0.35, ls=(0, (3, 2)))
        for uu in (0, L - 30):
            a.add_patch(Rectangle((uu, s - DR), 30, TT.DUCT, fc="#fbe9e5", ec=PATH, lw=0.4, hatch="xxxx"))
        for x0, x1 in ((-280, 0), (L, L + 280)):
            a.plot([x0, x1], [s, s], color=TENDON, lw=0.9)
    a.plot([-300, 1400], [0, 0], color=INK, lw=1.0)
    dim(a, (0, H), (L, H), 35, "1200")
    dim(a, (L, 0), (L, H), 60, "450")
    caption(fig, 22, 150, "3", "Elevation from the room", 10)
    a.text(600, H + 12, "column channel (hidden)", ha="center", fontsize=5)
    note(a, (100, 230), "ducts (hidden)", to=(300, TT.DUCT_S[1] - DR))
    note(a, (-290, 200), "end bead across\nthe duct: drill", to=(15, TT.DUCT_S[0] + DR))
    note(a, (-290, 440), "tendon runs on\nto the next piece", to=(-150, TT.DUCT_S[1]))
    # bed plan, a groove layer
    i = TT.LOW + 3
    a = view(fig, 190, 100, (-60, 1260), (-200, 260), 12)
    draw_plan(a, o, i)
    caption(fig, 190, 150, "4", "On the bed, layer {} (groove open)".format(i + 1), 12)
    a.text(1260, -195, "1 path, pump never stops  ·  o start  ▪ end", ha="right", va="bottom", fontsize=5)
    note(a, (900, -120), "grooves for the ducts", to=(800, TT.DUCT_N[0]))
    a.plot([800, 800], [TT.DUCT_N[0], TT.DUCT_N[1]], color=INK, lw=0)
    # ring plan, diagram
    a = view(fig, 196, 30, (-1800, 9000), (-1800, 7200), 220)
    side = 7200.0
    a.add_patch(Rectangle((0, 0), side, side, fill=False, ec=GREY, lw=0.4))
    for k in range(7):
        for p in [(k * 1200, 0), (k * 1200, side), (0, k * 1200), (side, k * 1200)]:
            a.add_patch(Circle(p, 90, fc=GREY, ec="none"))
    ext = 500
    for x0, y0, x1, y1 in [(-ext, 0, side + ext, 0), (-ext, side, side + ext, side),
                           (0, -ext, 0, side + ext), (side, -ext, side, side + ext)]:
        a.plot([x0, x1], [y0, y1], color=TENDON, lw=0.9)
        for x, y in ((x0, y0), (x1, y1)):
            a.add_patch(Rectangle((x - 120, y - 120), 240, 240, fc=STEEL, ec=INK, lw=0.3))
    note(a, (-1700, 7900), "tendons, straight corner to corner,\nanchored past each hip, stressed from outside",
         to=(-ext, side), fs=5)
    fig.text(196 / W, 84 / HH, "RING PLAN, DIAGRAM (columns grey)", fontsize=5.5, color="#555555")
    a = view(fig, 318, 36, ISO_X, ISO_Y, 20)
    draw_tendon_iso(a, o)
    caption(fig, 318, 108, "6", "The ring course piece", 20)
    return fig


STEEL = "#6d7178"


def iso_block(a, u0, u1, n0, n1, s0, s1, fc="#9a9ea5", top="#c4c7cc", side="#7d8188"):
    faces = [([(u0, n0, s0), (u1, n0, s0), (u1, n0, s1), (u0, n0, s1)], fc),
             ([(u0, n0, s1), (u1, n0, s1), (u1, n1, s1), (u0, n1, s1)], top),
             ([(u1, n0, s0), (u1, n1, s0), (u1, n1, s1), (u1, n0, s1)], side)]
    for pts, c in faces:
        a.add_patch(MP([iso(*q) for q in pts], closed=True, fc=c, ec=INK, lw=0.3, zorder=zn()))


def section(o, u):
    """the cut through the piece at u, as one polygon in (n, s)"""
    bs = []
    for x in o["layers"]:
        c = x["geom"].intersection(LineString([(u, -1e3), (u, 1e3)]))
        for g in getattr(c, "geoms", [c]):
            if not g.is_empty and g.length > 1:
                a, b = sorted(q[1] for q in g.coords)
                bs.append(box(a, x["s"] - lh / 2, b, x["s"] + lh / 2))
    return unary_union(bs).buffer(0.01).buffer(-0.01)


def end_view(o, u0, u1):
    """what is printed between u0 and u1, seen along u, in (n, s)"""
    bs = []
    for x in o["layers"]:
        g = x["geom"].intersection(box(u0, -1e3, u1, 1e3))
        for q in getattr(g, "geoms", [g]):
            if not q.is_empty and q.area > 1:
                bs.append(box(q.bounds[1], x["s"] - lh / 2, q.bounds[3], x["s"] + lh / 2))
    return unary_union(bs).buffer(0.01).buffer(-0.01)


# ---------------------------------------------------------------- drawing kit
def view(fig, x, y, xl, yl, scale):
    """axes whose data are mm at the given scale, lower-left corner at (x, y) mm on the sheet"""
    w = (xl[1] - xl[0]) / scale
    hgt = (yl[1] - yl[0]) / scale
    a = fig.add_axes([x / W, y / HH, w / W, hgt / HH])
    a.set_xlim(*xl)
    a.set_ylim(*yl)
    a.set_aspect("equal")
    a.axis("off")
    return a


def poly(a, g, **kw):
    for q in getattr(g, "geoms", [g]):
        if q.is_empty or q.geom_type != "Polygon":
            continue
        a.add_patch(MP(list(q.exterior.coords), closed=True, **kw))
        for r in q.interiors:
            a.add_patch(MP(list(r.coords), closed=True, fc="white", ec=kw.get("ec", INK), lw=kw.get("lw", 0.5)))


def cut(a, g, lw=0.7):
    poly(a, g, fc="white", ec=INK, lw=lw, hatch="////")


def cast(a, g):
    poly(a, g, fc="#f1f1ee", ec=INK, lw=0.35, hatch="....")


def bars(a, pts, r=6):
    for p in pts:
        a.add_patch(Circle(p, r, fc=INK, ec=INK, lw=0))


def dim(a, p, q, off, text, side=1, fs=5.5):
    """architect's dimension: extension lines, a line with 45-degree ticks, text above"""
    (x0, y0), (x1, y1) = p, q
    horiz = abs(y1 - y0) < abs(x1 - x0)
    if horiz:
        yy = y0 + off
        a.plot([x0, x0], [y0 + 0.15 * off, yy + 0.2 * off], color=INK, lw=0.25)
        a.plot([x1, x1], [y1 + 0.15 * off, yy + 0.2 * off], color=INK, lw=0.25)
        a.plot([x0, x1], [yy, yy], color=INK, lw=0.35)
        k = abs(off) * 0.25 + 4
        for xx in (x0, x1):
            a.plot([xx - k / 2, xx + k / 2], [yy - k / 2, yy + k / 2], color=INK, lw=0.8)
        a.text((x0 + x1) / 2, yy + (4 if off > 0 else -4), text, ha="center", va="bottom" if off > 0 else "top", fontsize=fs)
    else:
        xx = x0 + off
        a.plot([x0 + 0.15 * off, xx + 0.2 * off], [y0, y0], color=INK, lw=0.25)
        a.plot([x1 + 0.15 * off, xx + 0.2 * off], [y1, y1], color=INK, lw=0.25)
        a.plot([xx, xx], [y0, y1], color=INK, lw=0.35)
        k = abs(off) * 0.25 + 4
        for yy in (y0, y1):
            a.plot([xx - k / 2, xx + k / 2], [yy - k / 2, yy + k / 2], color=INK, lw=0.8)
        a.text(xx + (-4 if off < 0 else 4), (y0 + y1) / 2, text, ha="right" if off < 0 else "left", va="center",
               rotation=90, fontsize=fs)


def note(a, xy, txt, to=None, ha="left", fs=5.5):
    if to is None:
        a.text(*xy, txt, ha=ha, va="center", fontsize=fs)
    else:
        a.annotate(txt, to, xy, ha=ha, va="center", fontsize=fs,
                   arrowprops=dict(arrowstyle="-", lw=0.3, color=INK, shrinkA=1, shrinkB=0))


def caption(fig, x, y, num, title, scale):
    fig.text(x / W, y / HH, num, fontsize=8, fontweight="bold", va="top")
    fig.text((x + 7) / W, y / HH, title.upper(), fontsize=7, va="top")
    fig.text((x + 7) / W, (y - 3.6) / HH, "SCALE 1:{:d}".format(scale), fontsize=5, va="top", color="#555555")
    fig.add_artist(plt.Line2D([x / W, (x + 7 + 2.1 * len(title)) / W], [(y - 2.8) / HH] * 2, lw=0.4, color=INK))


def sheet(num, title, sub):
    fig = plt.figure(figsize=(W / 25.4, HH / 25.4))
    fr = fig.add_axes([0, 0, 1, 1])
    fr.set_xlim(0, W)
    fr.set_ylim(0, HH)
    fr.axis("off")
    fr.add_patch(Rectangle((10, 10), W - 20, HH - 20, fill=False, lw=0.8, ec=INK))
    # title block, along the bottom right
    x0 = W - 10 - 150
    fr.add_patch(Rectangle((x0, 10), 150, 22, fill=False, lw=0.5, ec=INK))
    for xx in (x0 + 95, x0 + 125):
        fr.plot([xx, xx], [10, 32], lw=0.3, color=INK)
    fr.plot([x0, x0 + 95], [21, 21], lw=0.3, color=INK)
    fr.text(x0 + 2.5, 28.5, "AMOR MUNDI 2  ·  ISHIGAKI PYRAMID ROOF", fontsize=6, fontweight="bold", va="center")
    fr.text(x0 + 2.5, 24.5, "Printed roof: where the ring meets the column", fontsize=5.5, va="center")
    fr.text(x0 + 2.5, 17.5, title.upper(), fontsize=6.5, fontweight="bold", va="center")
    fr.text(x0 + 2.5, 13.5, sub, fontsize=5.2, va="center", color="#444444")
    fr.text(x0 + 97, 28.5, "DATE", fontsize=4.5, color="#555555", va="center")
    fr.text(x0 + 97, 24, "19.10.2026", fontsize=5.5, va="center")
    fr.text(x0 + 97, 17.5, "STATUS", fontsize=4.5, color="#555555", va="center")
    fr.text(x0 + 97, 13.5, "STUDY", fontsize=5.5, va="center")
    fr.text(x0 + 127, 28.5, "SHEET", fontsize=4.5, color="#555555", va="center")
    fr.text(x0 + 137.5, 18, num, fontsize=15, fontweight="bold", ha="center", va="center")
    return fig, fr


def axes_key(fig, x, y, a="n", b="s", la="through the roof", lb="up the slope"):
    fr = fig.axes[0]
    fr.annotate("", (x + 9, y), (x, y), arrowprops=dict(arrowstyle="-|>", lw=0.4, color=INK, mutation_scale=5))
    fr.annotate("", (x, y + 9), (x, y), arrowprops=dict(arrowstyle="-|>", lw=0.4, color=INK, mutation_scale=5))
    fr.text(x + 10, y, a + "  " + la, fontsize=4.8, va="center")
    fr.text(x, y + 10, b + "  " + lb, fontsize=4.8, ha="center", va="bottom")


# ---------------------------------------------------------------- views
def draw_section(a, o, cg, dims=True, u=300.0):
    g = section(o, u)
    cut(a, g)
    cast(a, o["sec"])
    bars(a, cg["ring"])
    a.plot([-290, 270], [0, 0], color=INK, lw=1.0)                  # bed
    a.text(265, -8, "PRINT BED", fontsize=4.8, ha="right", va="top")
    if dims:
        dim(a, (0, H), (240, H), 22, "240 shell")
        lo = o["sec"].bounds
        dim(a, (lo[0], 0), (lo[0], o["crown"]), -26, "{:.0f}  crown".format(o["crown"]))
        dim(a, (lo[0], lo[1]), (30, lo[1]), -38, "{:.0f}".format(30 - lo[0]))
        a.text(-295, H - 10, "ROOM SIDE", fontsize=5, rotation=90, va="top")
        a.text(262, H - 10, "WEATHER SIDE", fontsize=5, rotation=90, va="top")


def draw_end(a, o):
    """the end face of the piece (u = 0) as you see it when the print is done"""
    if o["style"] == "trim":
        tab = end_view(o, -30, -7)
        poly(a, tab, fc="#fbe9e5", ec=PATH, lw=0.5, hatch="xxxx")
        cut(a, end_view(o, 0, 30), lw=0.4)
        poly(a, tab, fc="#fbe9e5", ec=PATH, lw=0.5, hatch="xxxx")
    else:
        face = end_view(o, 0, 30)
        cut(a, face, lw=0.4)
        if o["style"] == "plug":
            plug = face.intersection(o["sec"].buffer(0.5))
            poly(a, plug, fc="#fbe9e5", ec=PATH, lw=0.5, hatch="xxxx")
    a.plot([-290, 270], [0, 0], color=INK, lw=1.0)


def draw_plan(a, o, i, stops=True):
    x = o["layers"][i]
    poly(a, x["geom"], fc="#ecebe6", ec="none")
    poly(a, J.col_void(SHAPE), fc="white", ec=INK, lw=0.3, ls=(0, (3, 2)))
    cons = o["paths"][i]
    for k, c in enumerate(cons):
        xs, ys = zip(*c)
        a.plot(xs, ys, color=PATH, lw=0.5)
        a.plot(xs[0], ys[0], "o", ms=2.0, mfc="white", mec=PATH, mew=0.5)
        a.plot(xs[-1], ys[-1], "s", ms=1.8, color=PATH)
    if stops and len(cons) > 1:
        for c0, c1 in zip(cons, cons[1:]):
            a.plot([c0[-1][0], c1[0][0]], [c0[-1][1], c1[0][1]], color=PATH, lw=0.35, ls=(0, (1.5, 1.5)))
    if o.get("ext"):
        for uu in (0, L):
            a.plot([uu, uu], [-190, 70], color=INK, lw=0.5, ls=(0, (6, 2, 1, 2)))
    a.plot([-40, L + 40], [0, 0], color=GREY, lw=0.25, ls=(0, (4, 3)))


def draw_elev(a, o, cg):
    """the piece seen from the room, hidden ring tunnel and column channel dashed"""
    x0 = -30 if o.get("ext") else 0
    a.add_patch(Rectangle((0, 0), L, H, fc="white", ec=INK, lw=0.7))
    for s in range(10, int(H), 10):
        a.plot([0, L], [s, s], color="#c9c9c4", lw=0.15)
    lo, hi = J.P["floor"], o["crown"]
    cv = J.col_void(SHAPE).bounds
    hid = dict(color=INK, lw=0.35, ls=(0, (3, 2)))
    a.plot([0, L], [lo, lo], **hid)
    a.plot([0, L], [hi, hi], **hid)
    for uu in (cv[0], cv[2]):
        a.plot([uu, uu], [0, H], **hid)
    for _, s in cg["ring"][:2]:
        pass
    if o["style"] == "plug":
        for uu in (0, L - 30):
            a.add_patch(Rectangle((uu, lo), 30, hi - lo, fc="#fbe9e5", ec=PATH, lw=0.4, hatch="xxxx"))
    if o.get("ext"):
        for uu in (-30, L):
            a.add_patch(Rectangle((uu, 0), 30, hi, fc="#fbe9e5", ec=PATH, lw=0.4, hatch="xxxx"))
        for uu in (0, L):
            a.plot([uu, uu], [-25, hi + 25], color=INK, lw=0.5, ls=(0, (6, 2, 1, 2)))
    a.plot([x0 - 40, L + 40], [0, 0], color=INK, lw=1.0)
    dim(a, (0, H), (L, H), 35, "1200")
    dim(a, (L, 0), (L, H), 60, "450")
    dim(a, (0, 0), (0, hi), -45, "{:.0f}".format(hi))


# ---------------------------------------------------------------- axonometric (layer by layer, as it prints)
from matplotlib.path import Path
from matplotlib.patches import PathPatch
import math as _m

UV, NV = (0.85, -0.35), (0.6, 0.5)         # where one mm along u and along n lands on the paper (s stays vertical)
PLUG = "#e9b8ad"


def iso(u, n, s):
    return u * UV[0] + n * NV[0], s + u * UV[1] + n * NV[1]


def iso_box(u0, u1, n0, n1, s0, s1, pad=20):
    pts = [iso(u, n, s) for u in (u0, u1) for n in (n0, n1) for s in (s0, s1)]
    xs, ys = zip(*pts)
    return (min(xs) - pad, max(xs) + pad), (min(ys) - pad, max(ys) + pad)


ISO_X, ISO_Y = iso_box(-60, L + 60, -230, 280, 0, H)


def _ring_path(coords, s, du=0.0, ds=0.0):
    pts = [iso(u + du, n, s + ds) for u, n in coords]
    return pts


_Z = [10.0]


def zn():
    """painter's order: every call draws over everything drawn before it"""
    _Z[0] += 0.001
    return _Z[0]


def iso_poly(a, g, s, fc, ec="#777770", lw=0.12, du=0.0, ds=0.0, z=None):
    for q in getattr(g, "geoms", [g]):
        if q.is_empty or q.geom_type != "Polygon" or q.area < 2:
            continue
        verts, codes = [], []
        for ring in [q.exterior] + list(q.interiors):
            pts = _ring_path(list(ring.coords), s, du, ds)
            verts += pts
            codes += [Path.MOVETO] + [Path.LINETO] * (len(pts) - 2) + [Path.CLOSEPOLY]
        a.add_patch(PathPatch(Path(verts, codes), fc=fc, ec=ec, lw=lw, zorder=z or zn()))


def piece_layers(o):
    """[(s_top, geom, kind)] for one option's joint piece; kind marks what gets cut away"""
    out = []
    for x in o["layers"]:
        g = x["geom"]
        top = x["s"] + lh / 2
        if o["style"] == "plug":
            m = o["sec"].intersects(box(-1e3, x["s"] - 1, 1e3, x["s"] + 1))
            plug = unary_union([box(-1, -1e3, 30, 30), box(L - 30, -1e3, L + 1, 30)]).intersection(g) if m else None
            if plug is not None and not plug.is_empty:
                plug = plug.intersection(box(-1e3, -1e3, 1e3 + L, 30)).difference(J.col_void(SHAPE))
                rest = g.difference(plug)
                out.append((top, [(rest, "p"), (plug, "x")]))
                continue
        if o["style"] == "trim":
            tab = g.intersection(unary_union([box(-40, -1e3, -7, 1e3), box(L + 7, -1e3, L + 40, 1e3)]))
            if tab.area > 10:
                out.append((top, [(g.difference(tab), "p"), (tab, "x")]))
                continue
        out.append((top, [(g, "p")]))
    return out


def regular_layers():
    _, pg = J.shell_layer(SHAPE)
    pg = pg.intersection(box(0, -1e3, L, 1e3))
    return [((i + 1) * lh, [(pg, "p")]) for i in range(int(round(H / lh)))]


def draw_stack(a, lays, du=0.0, ds=0.0, fc="#ebe8e1", top_ec=INK):
    n = len(lays)
    for k, (s, parts) in enumerate(lays):
        for g, kind in parts:
            iso_poly(a, g, s, PLUG if kind == "x" else fc, ec=top_ec if k == n - 1 else "#8d8a82",
                     lw=0.45 if k == n - 1 else 0.12, du=du, ds=ds)


def draw_iso(a, o):
    a.add_patch(MP([iso(-60, -230, 0), iso(L + 60, -230, 0), iso(L + 60, 280, 0), iso(-60, 280, 0)], closed=True,
                   fc="none", ec=GREY, lw=0.3, ls=(0, (4, 3))))
    draw_stack(a, piece_layers(o))
    txt = {"stop": "tunnel open\nat both ends", "plug": "plug: cut out\nwhile green",
           "trim": "tab: trim off\nflush"}[o["style"]]
    a.annotate(txt, iso(L + 10, -60, 170), iso(L + 330, -60, -260), fontsize=5.2, ha="left", va="center",
               arrowprops=dict(arrowstyle="-", lw=0.3, color=INK), zorder=60)


# ---------------------------------------------------------------- sheets
TEXT = {
    "stop": ["The ring's room-side wall is printed as its own contour.",
          "Each layer the pump stops, the nozzle lifts and travels across",
          "the tunnel, and the pump restarts. The tunnel stays open at both",
          "ends straight off the bed: nothing to cut.",
          "",
          "Needs: a printer that stops and restarts cleanly",
          "(nozzle shut-off valve, or a pump that answers within a second).",
          "Risk: a blob or a gap at every restart; the crown corbels",
          "in at 7 mm a layer."],
    "plug": ["One continuous path, every layer. Bead A swings out to become",
          "the ring's room-side wall, so the path has to cross the tunnel",
          "mouth at both ends of the piece.",
          "",
          "After printing, while the concrete is green (a few hours),",
          "cut the two plugs out with a wire, following the tunnel's",
          "outline. Each plug is 30 mm thick, about 3 kg.",
          "Risk: an uneven cut edge; the crown is higher (wall leans",
          "at most 7 mm a layer)."],
    "trim": ["One continuous path, every layer: the same oval tunnel as",
             "option 1. The room-side wall is one bead that goes round the",
             "column's foot; the strip between the tunnel and the shell is",
             "a zig-zag that rides over the column's top. The path crosses",
             "the tunnel mouth once at each end, on a tab printed 30 mm",
             "outside the piece. While green, cut both tabs off flush",
             "with one straight cut down the end plane (or print the",
             "crossing inside the end and cut out a plug instead).",
             "Worst overhang 8.5 mm a layer at the crown, as in option 1."],
}


def option_sheet(o, cg, num):
    fig, fr = sheet(num, "Option {}: {}".format(o["key"], o["name"]),
                    "Joint piece, oval rib and ring, printed upright. Dimensions in mm.")
    # 1 section 1:5
    a = view(fig, 22, 170, (-300, 290), (-30, 500), 6)
    draw_section(a, o, J_cages)
    caption(fig, 22, 282, "1", "Section through the ring", 6)
    note(a, (-295, 470), "4 D12 ring bars\n(to confirm for 250 × 250)", to=tuple(cg["ring"][1]))
    note(a, (90, 330), "ring concrete,\ncast on site", to=(-50, 200))
    # 2 end face 1:5
    a = view(fig, 130, 170, (-300, 290), (-30, 500), 6)
    draw_end(a, o)
    caption(fig, 130, 282, "2", "End face as printed", 6)
    if o["style"] == "stop":
        note(a, (90, 330), "tunnel open\nstraight off the bed", to=(-50, 150))
    elif o["style"] == "plug":
        note(a, (90, 330), "plug, 30 mm thick:\ncut out green", to=(-50, 150))
    else:
        note(a, (90, 330), "tab outside the end:\ntrim off flush", to=(-50, 150))
    # notes
    y = 276
    fr.text(248, y + 3, "HOW IT PRINTS", fontsize=7, fontweight="bold")
    for line in TEXT[o["style"]]:
        fr.text(248, y - 4, line, fontsize=6.2, va="top")
        y -= 4.2
    rows = [("Pump stops per piece", "{:d}".format(o["stops"])),
            ("Print time", "{:.0f} min".format(o["time"])),
            ("Printed mass", "{:.0f} kg".format(o["mass"])),
            ("Ring crown above the bed", "{:.0f} mm".format(o["crown"])),
            ("Ring tunnel section", "{:.0f} cm²".format(o["sec"].area / 100)),
            ("Ring concrete per piece", "{:.0f} l".format(o["ring_l"])),
            ("Worst overhang step", "{:.1f} mm".format(o["over"]))]
    y -= 6
    for k, v in rows:
        fr.plot([248, 400], [y - 1.6, y - 1.6], lw=0.2, color="#999999")
        fr.text(248, y, k, fontsize=6.2)
        fr.text(400, y, v, fontsize=6.2, ha="right", fontweight="bold")
        y -= 5
    # 3 elevation 1:10
    a = view(fig, 22, 78, (-80, 1300), (-60, 520), 10)
    draw_elev(a, o, cg)
    caption(fig, 22, 150, "3", "Elevation from the room", 10)
    a.text(600, H + 12, "column channel (hidden)", ha="center", fontsize=5)
    a.text(250, (J.P["floor"] + o["crown"]) / 2, "ring tunnel (hidden)", ha="center", va="center", fontsize=5,
           bbox=dict(fc="white", ec="none", pad=0.6))
    # 4, 5 bed plans 1:10
    tun = [k for k, x in enumerate(o["layers"]) if o["sec"].intersects(box(-1e3, x["s"] - 1, 1e3, x["s"] + 1))]
    i1 = tun[len(tun) // 2]
    a = view(fig, 175, 88, (-60, 1260), (-270, 260), 11)
    draw_plan(a, o, i1)
    nc = len(o["paths"][i1])
    caption(fig, 175, 150, "4", "On the bed, layer {} (s = {:.0f})".format(i1 + 1, o["layers"][i1]["s"] + lh / 2), 11)
    a.text(1260, -195, "{} path{}{}  ·  o start  ▪ end".format(
        nc, "s" if nc > 1 else "", ", dotted = travel, pump off" if nc > 1 else ", pump never stops"),
        ha="right", va="bottom", fontsize=5)
    # 5 end detail, plan 1:4
    a = view(fig, 330, 40, (-60, 260), (-270, 250), 5.5)
    draw_plan(a, o, i1)
    caption(fig, 330, 140, "5", "Left end of layer {}, plan".format(i1 + 1), 5)
    if o["style"] == "stop":
        note(a, (90, -20), "pump off, lift, travel,\npump on", to=(15, -148))
    elif o["style"] == "plug":
        note(a, (90, -20), "crossing bead:\nbecomes the plug", to=(15, -60))
    else:
        note(a, (90, -20), "crossing bead outside\nthe piece; trim line", to=(-15, -60))
    note(a, (120, -185), "oval column channel", to=(150, -100))
    axes_key(fig, 290, 64, "u", "n", "along the course", "through the roof")
    a = view(fig, 246, 140, ISO_X, ISO_Y, 20)
    draw_iso(a, o)
    caption(fig, 326, 192, "6", "The piece as printed", 20)
    fig.text(333 / W, 184 / HH, "seen from the room side", fontsize=5, color="#555555")
    return fig


def cover(ops, cg):
    fig, fr = sheet("00", "The three options side by side", "1 and 2: same oval ring and bars, different print "
                    "path. 3: tendons through printed ducts.")
    fr.text(22, 274, "Ring joint: three ways to build it", fontsize=17)
    fr.text(22, 266, "Oval rib and 250 × 250 middle ring (Karamba, final run), 1200 × 450 × 240 mm piece, Polyuse printer, 30 mm bead, "
            "10 mm layers.",
            fontsize=7.5, color="#333333")
    for k, o in enumerate(ops):
        x = 22 + k * 128
        caption(fig, x, 256, o["key"], o["name"], 20)
        a = view(fig, x + 10, 188, ISO_X, ISO_Y, 20)
        if o["style"] == "tendon":
            draw_tendon_iso(a, o)
            a.annotate("4 ducts, tendons\ncorner to corner", iso(L + 30, TT.DUCT_N[0], TT.DUCT_S[0]), iso(L + 330, -60, -260),
                       fontsize=5.2, ha="left", va="center", arrowprops=dict(arrowstyle="-", lw=0.3, color=INK),
                       zorder=60)
            a = view(fig, x + 25, 122, (-170, 300), (-30, 500), 10)
            draw_tendon_section(a, o, 300.0, dims=False)
            fr.text(x, 180, "SECTION BETWEEN COLUMNS, 1:10", fontsize=5, color="#555555")
        else:
            draw_iso(a, o)
            a = view(fig, x + 13, 122, (-300, 290), (-30, 500), 10)
            draw_section(a, o, cg, dims=False)
            fr.text(x, 180, "SECTION THROUGH THE RING, 1:10", fontsize=5, color="#555555")
    # comparison table
    y0, x0 = 106, 22
    cols = [x0, x0 + 110, x0 + 190, x0 + 270]
    hdr = ["", "1  Pump stops", "2  No stops, ends trimmed", "3  Tendons through the print"]
    rows = [("Pump stops per piece", ["{:d}".format(o["stops"]) for o in ops]),
            ("Print time", ["{:.0f} min".format(o["time"]) for o in ops]),
            ("Printed mass", ["{:.0f} kg".format(o["mass"]) for o in ops]),
            ("Ring", ["concrete, cast with the columns", "concrete, cast with the columns",
                      "the printed course, post-tensioned"]),
            ("Ring concrete per piece", ["{:.0f} l".format(ops[0]["ring_l"]), "{:.0f} l".format(ops[1]["ring_l"]),
                                         "none"]),
            ("Work after printing", ["none", "trim 2 ends flush, green", "lay 4 duct tubes; drill 8 duct ends"]),
            ("Bed length per piece", ["1200 mm", "1260 mm", "1200 mm"]),
            ("Column pieces at the ring", ["flared, R 250 (sheet 04)", "flared, R 250 (sheet 04)", "plain"]),
            ("On site", ["ring bars, one pour", "ring bars, one pour", "thread 4 tendons, anchor, stress"]),
            ("Depends on", ["clean pump stops", "a straight green cut", "mix strength, hip anchors, stressing"])]
    for c, t in zip(cols, hdr):
        fr.text(c, y0, t, fontsize=7, fontweight="bold")
    fr.plot([x0, x0 + 340], [y0 - 2.5, y0 - 2.5], lw=0.6, color=INK)
    y = y0 - 7
    for name, vals in rows:
        fr.text(cols[0], y, name, fontsize=6.8)
        for c, v in zip(cols[1:], vals):
            fr.text(c, y, v, fontsize=6.8)
        fr.plot([x0, x0 + 340], [y - 2.2, y - 2.2], lw=0.2, color="#999999")
        y -= 5.6
    import textwrap
    fr.text(22, y - 4, textwrap.fill("1 and 2 give the same oval ring, cast with the columns. Choose 1 if Polyuse confirms the printer "
            "stops and restarts cleanly within a layer, otherwise 2. 3 needs no tunnel and no ring pour: "
            "the printed course becomes the ring, held in compression by tendons, so that course is no longer a casing. "
            "In 1 and 2 the ring's band is filled flat above the crown and the column pieces either side flare onto it "
            "(sheet 04).", 175),
            fontsize=6.8, va="top")
    # legend
    lx, ly = 378, 104
    fr.text(lx, ly, "KEY", fontsize=6.5, fontweight="bold")
    items = [("////", "white", INK, "printed concrete, cut"), ("....", "#f1f1ee", INK, "ring, cast on site"),
             ("xxxx", "#fbe9e5", PATH, "cut or drilled away")]
    for k, (ht, fc, ec, t) in enumerate(items):
        yy = ly - 8 - k * 7
        fr.add_patch(Rectangle((lx, yy - 2), 7, 4, fc=fc, ec=ec, lw=0.4, hatch=ht))
        fr.text(lx + 9, yy, t, fontsize=5.5, va="center")
    fr.add_patch(Circle((lx + 3.5, ly - 29), 2.0, fc="white", ec=INK, lw=0.4))
    fr.add_patch(Circle((lx + 3.5, ly - 29), 1.0, fc=TENDON))
    fr.text(lx + 9, ly - 29, "tendon in its duct", fontsize=5.5, va="center")
    ly -= 7
    fr.add_patch(Circle((lx + 3.5, ly - 29), 1.0, fc=INK))
    fr.text(lx + 9, ly - 29, "D12 bar", fontsize=5.5, va="center")
    fr.plot([lx, lx + 7], [ly - 36, ly - 36], color=PATH, lw=0.6)
    fr.text(lx + 9, ly - 36, "print path", fontsize=5.5, va="center")
    return fig


STEPS = [
    ("1", "Lay the flared course below the ring",
     "Flared column pieces, printed upright and turned over, wide end up, on a mortar bed. The column channels line "
     "up from course to course."),
    ("2", "Thread the ring bars, slide the joint pieces on",
     "4 D12 ring bars laid along the course. Each joint piece slides along u over them. Options 2 and 2b: "
     "plugs or tabs already cut off on the bed."),
    ("3", "Lay the flared course above the ring",
     "The same flared piece as printed, wide end down on the ring's filled band. The ring tunnel is now closed all "
     "round, open only at the corners."),
    ("4", "Drop the column bars", "4 D12 per column, down the channels and past the ring bars (they cross 12 mm apart)."),
    ("5", "Seal", "Mortar the joints. Stop-ends at the corners and at the column foot; a vent at the ring's crown."),
    ("6", "Cast columns and ring together",
     "Self-compacting concrete down the column channels, about two courses a lift, until it shows at the vent."),
]


GAP = 620


def tag(a, xy, n):
    a.add_patch(Circle(xy, 55, fc="white", ec=PATH, lw=0.6, zorder=50))
    a.text(*xy, n, ha="center", va="center", fontsize=6.5, color=PATH, fontweight="bold", zorder=51)


def assembly_axo(a, o, cg, fl):
    jnt = piece_layers(o)
    lay = [(x["s"] - lh / 2, x["s"] + lh / 2, x["geom"]) for x in fl["layers"]]
    below = [(H - s0, [(_scale(g, -1, 1, origin=(L / 2, 0)), "p")]) for s0, s1, g in reversed(lay)]
    above = [(s1, [(g, "p")]) for s0, s1, g in lay]
    gap = GAP
    z1, z2, z3 = 0, 450 + gap, 900 + 2 * gap
    slide = 420
    cbar = [(p * L + uu, nn) for p in range(2) for uu, nn in cg["col"]]
    for uu, nn in cbar:                                          # column bars, behind everything
        xs, ys = zip(iso(uu, nn, -40), iso(uu, nn, z3 + 450 + 380))
        a.plot(xs, ys, color=INK, lw=0.6, zorder=zn())
    for p in range(2):                                           # course 1
        draw_stack(a, [(s + z1, g) for s, g in below], du=p * L)
    for nn, ss in (cg["ring"][0], cg["ring"][1]):                 # ring bars
        xs, ys = zip(iso(-350, nn, z2 + ss), iso(2 * L + slide + 250, nn, z2 + ss))
        a.plot(xs, ys, color=INK, lw=0.6, zorder=zn())
    for p in range(2):                                           # course 2, the second piece still sliding on
        draw_stack(a, [(s + z2, g) for s, g in jnt], du=p * L + (slide if p == 1 else 0))
    xs, ys = zip(iso(2 * L + slide + 120, -200, z2 + 200), iso(2 * L + 120, -200, z2 + 200))
    a.annotate("", (xs[1], ys[1]), (xs[0], ys[0]), arrowprops=dict(arrowstyle="-|>", lw=0.7, color=PATH,
                                                                   mutation_scale=7), zorder=40)
    for p in range(2):                                           # course 3
        draw_stack(a, [(s + z3, g) for s, g in above], du=p * L)
    for uu, nn in cbar[::4]:                                     # drop arrows
        x0, y0 = iso(uu + 50, nn - 20, z3 + 450 + 420)
        x1, y1 = iso(uu + 50, nn - 20, z3 + 450 + 120)
        a.annotate("", (x1, y1), (x0, y0), arrowprops=dict(arrowstyle="-|>", lw=0.7, color=PATH, mutation_scale=7),
                   zorder=40)
    for zz in (z2, z3):                                          # 'lower onto' arrows
        x0, y0 = iso(-230, -150, zz - 30)
        x1, y1 = iso(-230, -150, zz - gap + 30)
        a.annotate("", (x1, y1), (x0, y0), arrowprops=dict(arrowstyle="-|>", lw=0.5, color=GREY, mutation_scale=6))
    tag(a, iso(-260, -200, 230), "1")
    tag(a, iso(2 * L + slide + 300, -200, z2 + 330), "2")
    tag(a, iso(-260, -200, z3 + 230), "3")
    tag(a, iso(600, -50, z3 + 450 + 560), "4")
    tag(a, iso(2 * L + 200, -200, 450 + 60), "5")
    tag(a, iso(L + 600, -50, z3 + 450 + 560), "6")


def assembly(ops, cg, fl=None):
    fig, fr = sheet("05", "Assembly on the roof", "Options 1 and 2 (shown with the option 1 piece; 2 looks the "
                    "same once trimmed). Option 3: sheet 03.")
    xl, yl = iso_box(-450, 2 * L + 750, -230, 280, -60, 900 + 2 * GAP + 450 + 650, pad=60)
    a = view(fig, 22, 60, xl, yl, 20)
    assembly_axo(a, ops[0], cg, fl)
    caption(fig, 22, 282, "1", "Exploded axonometric, from the room", 20)
    # the steps, as text
    y = 268
    fr.text(236, y + 6, "SEQUENCE", fontsize=7, fontweight="bold")
    import textwrap
    for n, tt, d in STEPS:
        fr.add_patch(Circle((239, y - 1.2), 2.6, fc="white", ec=PATH, lw=0.6))
        fr.text(239, y - 1.2, n, ha="center", va="center", fontsize=6.5, color=PATH, fontweight="bold")
        fr.text(245, y, tt.upper(), fontsize=6.5, fontweight="bold", va="center")
        for j, line in enumerate(textwrap.wrap(d, 78)):
            fr.text(245, y - 4.6 - 3.7 * j, line, fontsize=6, va="center", color="#333333")
        y -= 8.5 + 3.7 * len(textwrap.wrap(d, 78))
    # the same sequence as small elevations from the room
    cv = J.col_void(SHAPE).bounds
    lo, hi = J.P["floor"], ops[0]["crown"]
    faces = [room_face(c) for c in node_courses(fl, ops[0])]
    fr.text(236, y - 2, "THE SAME, ELEVATION FROM THE ROOM, 1:50", fontsize=5.5, color="#555555")
    for k, (n, tt, d) in enumerate(STEPS):
        col, row = k % 3, k // 3
        x, yy = 236 + col * 58, y - 48 - row * 44
        b = view(fig, x, yy, (-120, 2520), (-80, 1650), 50)
        show = {0: 1, 1: 2}.get(k, 3)
        for ci, z in enumerate((0, 450, 900)[:show]):
            for p in range(2):
                u0 = p * L
                b.add_patch(Rectangle((u0 + 5, z + 5), L - 10, 440, fc="white", ec=INK, lw=0.45))
                poly(b, _translate(faces[ci], u0, 0), fc="#e4e2dc", ec=INK, lw=0.3)
                hid = dict(color=GREY, lw=0.25, ls=(0, (3, 2)))
                for uu in (cv[0], cv[2]):
                    b.plot([u0 + uu] * 2, [z + 5, z + 445], **hid)
                if ci == 1:
                    b.plot([u0 + 5, u0 + L - 5], [z + lo] * 2, **hid)
                    b.plot([u0 + 5, u0 + L - 5], [z + hi] * 2, **hid)
                    if k == 5:
                        b.add_patch(Rectangle((u0, z + lo), L, hi - lo, fc="#f1f1ee", ec="none", hatch="...."))
                if k == 5:
                    b.add_patch(Rectangle((u0 + cv[0], z), cv[2] - cv[0], 450, fc="#f1f1ee", ec="none", hatch="...."))
        if k >= 1:
            for _, s in (cg["ring"][0], cg["ring"][1]):
                b.plot([-100, 2 * L + 100], [450 + s] * 2, color=INK, lw=0.5)
        if k >= 3:
            for p in range(2):
                for uu in (cg["col"][0][0], cg["col"][2][0]):
                    b.plot([p * L + uu] * 2, [-50, 1350 + (180 if k == 3 else 50)], color=INK, lw=0.5)
        if k >= 4:
            for zz in (450, 900):
                b.plot([0, 2 * L], [zz, zz], color=INK, lw=1.1)
            for p in range(3):
                b.plot([p * L] * 2, [0, 1350], color=INK, lw=1.1)
            b.add_patch(Rectangle((-40, 450 + lo), 40, hi - lo, fc=INK))
            b.add_patch(Rectangle((2 * L, 450 + lo), 40, hi - lo, fc=INK))
        if k == 5:
            for p in range(2):
                b.annotate("", (p * L + 600, 1370), (p * L + 600, 1600),
                           arrowprops=dict(arrowstyle="-|>", lw=0.6, color=PATH, mutation_scale=5))
        b.plot([-120, 2520], [0, 0], color=INK, lw=0.8)
        fig.text((x - 1) / W, (yy + 37) / HH, n, fontsize=7, fontweight="bold", color=PATH, va="bottom")
    fr.text(22, 52, "Rib sizes are still moving in Karamba (deeper toward the eave, tapering continuously, protruding "
            "inside). The oval channel drawn here is 220 × 160; each course's channel will follow the rib at its height.",
            fontsize=6)
    return fig


# ---------------------------------------------------------------- the node: flared column pieces either side of the ring
def flare_piece():
    r = F.study()
    p = dict(L=L, layer_H=lh, bead=B, speed=J.P["speed"])
    _, t, s = piece_test.gcode(dict(p=p, col=r["layers"]), "col")
    return dict(key="F", style="flare", name="Flared column piece", layers=r["layers"],
                paths=[x["cons"] for x in r["layers"]], time=t / 60, stops=s, mass=r["mass"], extra=r["extra"],
                over=r["max_over"], reach=r["reach"], rise=r["rise"])


def node_courses(fl, o):
    """(s_lo, s_hi, geom) for the three courses at a node: flared piece turned over, the joint (beam) piece, the
    flared piece as printed"""
    lay = [(x["s"] - lh / 2, x["s"] + lh / 2, x["geom"]) for x in fl["layers"]]
    below = [(H - s1, H - s0, _scale(g, -1, 1, origin=(L / 2, 0))) for s0, s1, g in lay]
    beam = [(x["s"] - lh / 2 + H, x["s"] + lh / 2 + H, x["geom"]) for x in o["layers"]]
    above = [(s0 + 2 * H, s1 + 2 * H, g) for s0, s1, g in lay]
    return below, beam, above


def room_face(courses):
    """what stands proud of the shell's room face (n < 0), seen from the room: (u, s) outline"""
    bs = []
    for s0, s1, g in courses:
        part = g.intersection(box(-1e3, -1e3, L + 1e3, -0.5))
        for q in getattr(part, "geoms", [part]):
            if not q.is_empty and q.area > 1:
                bs.append(box(q.bounds[0], s0, q.bounds[2], s1))
    return unary_union(bs).buffer(0.01).buffer(-0.01)


def draw_node_elev(a, fl, o):
    below, beam, above = node_courses(fl, o)
    for k in range(3):
        a.add_patch(Rectangle((0, k * H), L, H, fc="white", ec=INK, lw=0.5))
    poly(a, room_face(below + beam + above), fc="#e4e2dc", ec=INK, lw=0.6)
    for s in range(10, int(3 * H), 10):
        a.plot([0, L], [s, s], color="#c9c9c4", lw=0.12, zorder=0.5)
    for k in (1, 2):
        a.plot([0, L], [k * H, k * H], color=INK, lw=0.8)
    cv = J.col_void(SHAPE).bounds
    hid = dict(color=INK, lw=0.35, ls=(0, (3, 2)))
    for uu in (cv[0], cv[2]):
        a.plot([uu, uu], [0, 3 * H], **hid)
    for ss in (J.P["floor"], o["crown"]):
        a.plot([0, L], [H + ss, H + ss], **hid)
    a.plot([-60, L + 60], [0, 0], color=INK, lw=1.0)
    # the two quarter circles, dimensioned on the left wing
    import numpy as np
    u0 = room_face(above[-1:]).bounds[0]                   # the column's edge above the flare
    for sgn, s0 in ((1, 2 * H), (-1, H)):
        t = np.linspace(0, np.pi / 2, 30)
        xs = u0 - F.R_NODE + F.R_NODE * np.cos(t)
        ys = s0 + sgn * (F.R_NODE - F.R_NODE * np.sin(t))
        a.plot(xs, ys, color=PATH, lw=0.4, ls=(0, (4, 2)))
    a.annotate("R {:.0f}".format(F.R_NODE), (u0 - F.R_NODE * 0.3, 2 * H + F.R_NODE * 0.05), (u0 - 330, 2 * H + 200),
               fontsize=5.5, arrowprops=dict(arrowstyle="-", lw=0.3, color=INK))
    dim(a, (L, 0), (L, H), 40, "450")
    dim(a, (L, H), (L, 2 * H), 40, "450")
    dim(a, (L, 2 * H), (L, 3 * H), 40, "450")
    dim(a, (u0 - fl["reach"], 3 * H), (u0, 3 * H), 30, "{:.0f}".format(fl["reach"]))
    for k, t in enumerate(["flared piece, turned over", "joint piece (ring), band filled to the top",
                           "flared piece, as printed"]):
        a.text(L + 120, k * H + H / 2, t, fontsize=5.5, va="center")


def node_axo(a, fl, o):
    below, beam, above = node_courses(fl, o)
    gap = 160
    for k, (lays, kind) in enumerate(((below, "below"), (beam, "beam"), (above, "above"))):
        lays = sorted(lays, key=lambda x: x[0])
        draw_stack(a, [(s1 + k * gap, [(g.intersection(box(0, -1e3, L, 1e3)), "p")]) for s0, s1, g in lays])


def draw_flare_iso(a, fl):
    a.add_patch(MP([iso(-60, -230, 0), iso(L + 60, -230, 0), iso(L + 60, 280, 0), iso(-60, 280, 0)], closed=True,
                   fc="none", ec=GREY, lw=0.3, ls=(0, (4, 3))))
    draw_stack(a, [(x["s"] + lh / 2, [(x["geom"], "p")]) for x in fl["layers"]])


def node_sheet(fl, ops, cg, num):
    o = ops[0]
    fig, fr = sheet(num, "The node: flared column pieces", "Options 1 and 2. The column meets the ring on a "
                    "250 mm quarter circle above and below. Dimensions in mm.")
    a = view(fig, 22, 110, (-420, 1600), (-60, 3 * H + 80), 10)
    draw_node_elev(a, fl, o)
    caption(fig, 22, 282, "1", "Elevation from the room, three courses", 10)
    # notes
    y = 276
    x0 = 252
    fr.text(x0, y + 3, "HOW IT PRINTS AND GOES TOGETHER", fontsize=7, fontweight="bold")
    lines = ["Every piece is printed upright and then laid on the roof, so no",
             "piece may overhang as it prints. The joint piece (the ring) stays",
             "as it is, with its band filled flat from the crown to the top, so",
             "the ring reads as one 450 mm band, flush all along.",
             "",
             "The column pieces either side of it carry the curve. Printed",
             "upright, the column is widest on the bed ({:.0f} mm out each side)".format(fl["reach"]),
             "and narrows layer by layer up to s = {:.0f}: every layer sits".format(fl["rise"]),
             "inside the one below. Above the ring it goes on as printed; below",
             "the ring the same piece is turned over, wide end up.",
             "",
             "One path a layer, no pump stops: bead A runs to the column, each",
             "wing is 4 rows along the course (33 mm bead) joined along the",
             "column and down the wing's edge, the U takes the path under the",
             "column, and the rows mirrored bring it back to bead A.",
             "The wings stay flush with the band's face (n = {:.0f}).".format(F.BAND_FACE),
             "",
             "Option 3 has no ring beam to land on (the ring is the course",
             "itself), so it keeps plain column pieces."]
    for line in lines:
        fr.text(x0, y - 4, line, fontsize=6.0, va="top")
        y -= 3.8
    y -= 7
    rows = [("Flared piece: pump stops", "{:d}".format(fl["stops"])),
            ("Print time", "{:.0f} min".format(fl["time"])),
            ("Printed mass", "{:.0f} kg ({:+.0f} on a regular piece)".format(fl["mass"], fl["extra"])),
            ("Worst overhang step", "{:.1f} mm".format(fl["over"])),
            ("Joint piece, band filled: mass", "{:.0f} kg (opt. 1), {:.0f} kg (opt. 2)".format(ops[0]["mass"], ops[1]["mass"]))]
    for k, v in rows:
        fr.plot([x0, 400], [y - 1.6, y - 1.6], lw=0.2, color="#999999")
        fr.text(x0, y, k, fontsize=6.2)
        fr.text(400, y, v, fontsize=6.2, ha="right", fontweight="bold")
        y -= 4.6
    # plans of the flared piece
    for k, (i, yy) in enumerate(((0, 62), (14, 18))):
        a = view(fig, 22, yy, (-60, 1260), (-180, 260), 11)
        draw_plan(a, fl, i)
        fig.text(22 / W, (yy + 44) / HH, "{}  ON THE BED, LAYER {} (s = {:.0f})".format(2 + k, i + 1, (i + 1) * lh),
                 fontsize=6.5, va="top")
        a.text(1260, -175, "1 path, pump never stops  ·  o start  ▪ end", ha="right", va="bottom", fontsize=5)
    # axonometrics
    a = view(fig, 250, 40, ISO_X, ISO_Y, 22)
    draw_flare_iso(a, fl)
    caption(fig, 250, 40 + (ISO_Y[1] - ISO_Y[0]) / 22 + 10, "4", "The flared piece as printed", 22)
    xl, yl = iso_box(-60, L + 60, -230, 280, 0, 3 * H + 2 * 160)
    a = view(fig, 335, 40, xl, yl, 35)
    node_axo(a, fl, o)
    caption(fig, 335, 40 + (yl[1] - yl[0]) / 35 + 10, "5", "The node, exploded", 35)
    return fig


def main():
    global J_cages
    ops, cg = options()
    J_cages = cg
    here = os.path.dirname(os.path.abspath(__file__))
    folder = os.path.normpath(os.path.join(here, "..", "details", "piece-test"))
    fl = flare_piece()
    figs = [cover(ops, cg), option_sheet(ops[0], cg, "01"), option_sheet(ops[1], cg, "02"), tendon_sheet(ops[2], cg, "03"),
            node_sheet(fl, ops, cg, "04"), assembly(ops, cg, fl)]
    fn = os.path.join(folder, "joint-options.pdf")
    with PdfPages(fn) as pdf:
        for k, f in enumerate(figs):
            pdf.savefig(f)
            f.savefig(os.path.join(folder, "joint-options-{}.png".format(k)), dpi=110)
            f.savefig(os.path.join(folder, "joint-options-{}.svg".format(k)))
            plt.close(f)
    for o in ops:
        print("{:3s} {:3d} stops {:4.0f} min {:4.0f} kg crown {} ring {:4.0f} l".format(
            o["key"], o["stops"], o["time"], o["mass"], o["crown"], o["ring_l"]))
    print("F   {:3d} stops {:4.0f} min {:4.0f} kg overhang {:.1f}".format(fl["stops"], fl["time"], fl["mass"], fl["over"]))
    print("wrote", fn)


if __name__ == "__main__":
    main()
