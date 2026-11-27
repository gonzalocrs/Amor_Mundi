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
HERE = r"C:\Users\gonza\Documents\GitHub\Amor_Mundi\details\karamba\2026-11-27"
STOPS = [(254, 0, 73), (254, 53, 111), (254, 102, 146), (254, 156, 184), (254, 205, 219), (250, 250, 253),
         (214, 208, 244), (174, 162, 233), (138, 120, 223), (97, 74, 212), (66, 38, 204)]   # Karamba gradient, -lim .. +lim
SECT = {"15x10": {"ring": (0.528, 0.40), "crown": (0.25, 0.25), "column": (0.36, 0.42)},
        "10x10": {"ring": (0.552, 0.40), "crown": (0.25, 0.25), "column": (0.30, 0.362)}}   # final sizes 2026-11-27; column h = radial depth   # (width y, height z) m, read from the Karamba cross-sections


def kcol(s, lim):
    t = max(-1.0, min(1.0, s / lim)); f = (t + 1) / 2 * (len(STOPS) - 1); i = min(int(f), len(STOPS) - 2); w = f - i
    a, b = STOPS[i], STOPS[i + 1]
    return System.Drawing.Color.FromArgb(*[int(round(a[k] + (b[k] - a[k]) * w)) for k in range(3)])


_COLS = [c for r in json.load(open(os.path.join(HERE, "model_columns_final.json"))).values() for c in r["cols"]]


def axes(pa, pb):
    x = pb - pa; x.Unitize()
    if abs(x.Z) > 0.999:                       # vertical (columns): local z = the column's radial long side (Karamba Z-Orientation, 2026-11-27)
        c = min(_COLS, key=lambda c: (c["cx"] - pa.X) ** 2 + (c["cy"] - pa.Y) ** 2)
        z = G.Vector3d(c["long_dir"][0], c["long_dir"][1], 0); z.Unitize()
    else:
        z = G.Vector3d.ZAxis - x * x.Z; z.Unitize()
    y = G.Vector3d.CrossProduct(z, x)
    return x, y, z


def build(doc, roof, lc, lim, layer_index, sect=None):
    D = json.load(open(os.path.join(HERE, "forces-%s.json" % roof)))
    N, E, F = D["nodes"], D["els"], D["forces"][lc]
    S = sect or SECT[roof]
    groups = {g: [i for i, e in enumerate(E) if e[0] == g] for g in ("ring", "crown", "column")}
    att0 = Rhino.DocObjects.ObjectAttributes(); att0.LayerIndex = layer_index
    done = set()
    for g in ("ring", "crown"):
        for mesh in loops(N, E, F, groups[g], S[g], lim):
            doc.Objects.AddMesh(mesh, att0)
        done.add(g)
    att = Rhino.DocObjects.ObjectAttributes(); att.LayerIndex = layer_index
    count = 0
    for g, ids in groups.items():
        if g in done: continue
        b, h = S[g]; A = b * h; Iy = b * h ** 3 / 12; Iz = h * b ** 3 / 12
        at = {}
        for i in ids:
            for n in E[i][1:3]: at.setdefault(n, []).append(i)
        for i in ids:
            _, na, nb = E[i]; pa, pb = G.Point3d(*N[na]), G.Point3d(*N[nb])
            if g == "column":                          # stop the column at the ring underside (no box above the ring)
                zr = max(N[n][2] for e2 in groups["ring"] for n in E[e2][1:3]) - S["ring"][1] / 2
                if pa.Z > zr: pa = G.Point3d(pa.X, pa.Y, zr)
                if pb.Z > zr: pb = G.Point3d(pb.X, pb.Y, zr)
                if pa.DistanceTo(pb) < 1e-3: continue
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


def loops(N, E, F, ids, sect, lim):
    """ring / crown as closed loops, welded: walk each loop in order; at every node the four section corners are
    computed once on the bisector (mitre) plane and shared by the two segments; each of the four faces of the box is
    one strip mesh along the whole loop with shared vertices, so the normals average across the joints (smooth along
    the ring, crisp at the box edges). Colour at a node corner = mean of the two segment ends' Karamba stress there."""
    b, h = sect; A = b * h; Iy = b * h ** 3 / 12; Iz = h * b ** 3 / 12
    corners = [(-b / 2, -h / 2), (b / 2, -h / 2), (b / 2, h / 2), (-b / 2, h / 2)]
    at = {}
    for i in ids:
        for n in E[i][1:3]: at.setdefault(n, []).append(i)
    left = set(ids); out = []
    while left:
        i0 = left.pop(); seq = [i0]
        a0, b0 = E[i0][1], E[i0][2]; nodes = [a0, b0]; cur = b0; prev = i0
        while True:
            nxt = [j for j in at[cur] if j != prev and j in left]
            if len(at[cur]) != 2 or not nxt: break
            j = nxt[0]; left.discard(j); seq.append(j)
            cur = E[j][2] if E[j][1] == cur else E[j][1]; nodes.append(cur); prev = j
        closed = nodes[0] == nodes[-1] and len(at[nodes[0]]) == 2
        pts = [G.Point3d(*N[n]) for n in nodes]
        nseg = len(seq)
        def seg_dir(k):
            v = pts[k + 1] - pts[k]; v.Unitize(); return v
        def frame(x):
            z = G.Vector3d.ZAxis - x * x.Z; z.Unitize(); return G.Vector3d.CrossProduct(z, x), z
        P = []; C = []
        for k in range(len(nodes)):
            if closed and k == len(nodes) - 1:
                P.append(P[0]); C.append(C[0]); continue
            xin = seg_dir(k - 1) if k > 0 else (seg_dir(nseg - 1) if closed else None)
            xout = seg_dir(k) if k < nseg else None
            if xin is None: xin = xout
            if xout is None: xout = xin
            t = xin + xout; t.Unitize()                     # tangent at the node; mitre plane normal
            y, z = frame(t)
            ym, zm = [], []
            # section corners on the mitre plane: offset in the bisector frame, scaled so the faces stay parallel
            cosh = max(0.2, xin * t)
            P.append([pts[k] + y * (cy / cosh) + z * cz for (cy, cz) in corners])
            # stresses from the two segment ends meeting here (Karamba local y flips if the bar runs against the walk)
            ss = []
            for kk, end_is_b in ((k - 1, True), (k, False)):
                kk = kk % nseg if closed else kk
                if kk < 0 or kk >= nseg: continue
                i = seq[kk]; na = E[i][1]
                walk_a = nodes[kk]; same = (na == walk_a)
                t_end = (1 if end_is_b else 0) if same else (0 if end_is_b else 1)
                sgn = 1 if same else -1
                Nn = F["N"][2 * i + t_end]; My = F["My"][2 * i + t_end]; Mz = F["Mz"][2 * i + t_end]
                ss.append([(Nn / A + My * cz / Iy - Mz * (sgn * cy) / Iz) / 10000.0 for (cy, cz) in corners])
            C.append([kcol(sum(v[c] for v in ss) / len(ss), lim) for c in range(4)])
        m = G.Mesh()
        K = len(nodes) - 1 if closed else len(nodes)       # closed: the last node is the first, so wrap round
        for side in range(4):
            s2 = (side + 1) % 4; base = m.Vertices.Count
            for k in range(K):
                m.Vertices.Add(P[k][side]); m.VertexColors.Add(C[k][side])
                m.Vertices.Add(P[k][s2]); m.VertexColors.Add(C[k][s2])
            for k in range(K if closed else K - 1):
                q = base + 2 * k; q2 = base + 2 * ((k + 1) % K)
                m.Faces.AddFace(q, q2, q2 + 1, q + 1)
        if not closed:
            for k in (0, len(nodes) - 1):
                base = m.Vertices.Count
                for c in range(4): m.Vertices.Add(P[k][c]); m.VertexColors.Add(C[k][c])
                m.Faces.AddFace(base, base + 1, base + 2, base + 3) if k else m.Faces.AddFace(base + 3, base + 2, base + 1, base)
        m.UnifyNormals(); m.Normals.ComputeNormals()
        if m.IsClosed and m.Volume() < 0: m.Flip(True, True, True)   # outward normals: lit like the ribs, not seen from inside
        m.Normals.ComputeNormals()
        out.append(m)
    return out
