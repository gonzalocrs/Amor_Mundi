"""Clean ring / crown / arch drawing for the Karamba-model renders (Gonzalo 2026-11-24: 'why is the ring like this?').
Karamba's BeamView draws every straight ring segment as its own box cut square at the nodes (V-notches between
segments) and the short 'arches between columns' with their own sloped boxes (loose stepped blocks). Here those three
groups are left out of the BeamView and drawn instead from the same Karamba model and the same D2 forces:
- ring and crown: one box per segment, section upright (local z = global Z, as in Karamba), ends cut on the bisector
  plane with the neighbouring segment, so the polygon closes flush with no notch or overlap;
- columns (two Karamba bars each: 0 to +1.95 and +1.95 to the ring axis +2.40): square boxes on the plan axes (Karamba's
  local axes for vertical bars), so the top stub no longer sticks out of the ring rotated. (There are no 'arch' bars in
  the assembled model: the offset blocks under the ring were these column stubs drawn by the BeamView.)
- colour at every section corner = Karamba's axial-stress colour of sigma = N/A + My z / Iy - Mz y / Iz at that end
  (Karamba sign, compression negative), on the same fixed legend as the BeamView (+-0.4 / +-0.7 kN/cm2)."""
import os, json, math, System, Rhino
import Rhino.Geometry as G
HERE = r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\details\karamba\2026-11-23"
STOPS = [(254, 0, 73), (254, 53, 111), (254, 102, 146), (254, 156, 184), (254, 205, 219), (250, 250, 253),
         (214, 208, 244), (174, 162, 233), (138, 120, 223), (97, 74, 212), (66, 38, 204)]   # Karamba gradient, -lim .. +lim
SECT = {"15x10": {"ring": (0.40, 0.40), "crown": (0.25, 0.25), "column": (0.36, 0.36)},
        "10x10": {"ring": (0.40, 0.30), "crown": (0.25, 0.25), "column": (0.30, 0.30)}}   # (width y, height z) m, read from the Karamba cross-sections


def kcol(s, lim):
    t = max(-1.0, min(1.0, s / lim)); f = (t + 1) / 2 * (len(STOPS) - 1); i = min(int(f), len(STOPS) - 2); w = f - i
    a, b = STOPS[i], STOPS[i + 1]
    return System.Drawing.Color.FromArgb(*[int(round(a[k] + (b[k] - a[k]) * w)) for k in range(3)])


def axes(pa, pb):
    x = pb - pa; x.Unitize()
    if abs(x.Z) > 0.999:                       # vertical (columns): Karamba takes local z along global -X
        z = -G.Vector3d.XAxis
    else:
        z = G.Vector3d.ZAxis - x * x.Z; z.Unitize()
    y = G.Vector3d.CrossProduct(z, x)
    return x, y, z


def build(doc, roof, lc, lim, layer_index, sect=None):
    D = json.load(open(os.path.join(HERE, "forces-%s.json" % roof)))
    N, E, F = D["nodes"], D["els"], D["forces"][lc]
    S = sect or SECT[roof]
    groups = {g: [i for i, e in enumerate(E) if e[0] == g] for g in ("ring", "crown", "column")}
    att = Rhino.DocObjects.ObjectAttributes(); att.LayerIndex = layer_index
    count = 0
    for g, ids in groups.items():
        b, h = S[g]; A = b * h; Iy = b * h ** 3 / 12; Iz = h * b ** 3 / 12
        at = {}
        for i in ids:
            for n in E[i][1:3]: at.setdefault(n, []).append(i)
        for i in ids:
            _, na, nb = E[i]; pa, pb = G.Point3d(*N[na]), G.Point3d(*N[nb])
            x, y, z = axes(pa, pb); L = pa.DistanceTo(pb)
            ends = []
            for t, (n, p, xin) in enumerate(((na, pa, x), (nb, pb, -x))):
                corners = [(-b / 2, -h / 2), (b / 2, -h / 2), (b / 2, h / 2), (-b / 2, h / 2)]
                nbrs = [j for j in at.get(n, []) if j != i] if g in ("ring", "crown") else []
                pts = []
                for (cy, cz) in corners:
                    p0 = p + y * cy + z * cz
                    if len(nbrs) == 1:
                        j = nbrs[0]; o = E[j][1] if E[j][2] == n else E[j][2]
                        xj = G.Point3d(*N[o]) - p; xj.Unitize()
                        m = xin - xj; m.Unitize()
                        den = xin * m
                        tt = -((p0 - p) * m) / den if abs(den) > 1e-6 else 0.0
                        pts.append(p0 + xin * tt)
                    else:
                        ext = 0.0
                        pts.append(p0 - xin * ext)
                Nn = F["N"][2 * i + t]; My = F["My"][2 * i + t]; Mz = F["Mz"][2 * i + t]
                cols = [kcol((Nn / A + My * cz / Iy - Mz * cy / Iz) / 10000.0, lim) for (cy, cz) in corners]
                ends.append((pts, cols))
            m = G.Mesh()
            for pts, cols in ends:
                for q, c in zip(pts, cols): m.Vertices.Add(q); m.VertexColors.Add(c)
            for k in range(4):
                k2 = (k + 1) % 4; m.Faces.AddFace(k, k2, 4 + k2, 4 + k)
            m.Faces.AddFace(3, 2, 1, 0); m.Faces.AddFace(4, 5, 6, 7)
            m.Normals.ComputeNormals(); m.Compact()
            doc.Objects.AddMesh(m, att); count += 1
    return count
