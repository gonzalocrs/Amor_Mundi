import Rhino, scriptcontext, time
import Rhino.Geometry as G
def smallface(f):
    a=G.AreaMassProperties.Compute(f.DuplicateFace(False))
    return (a.Area<0.12) if a else (f.GetBoundingBox(True).Diagonal.Length<0.6)
def cyl(p0,p1,r): return G.Cylinder(G.Circle(G.Plane(p0,p1-p0),r),(p1-p0).Length).ToBrep(True,True)
def cone(p0,p1,r0,r1):
    if abs(r0-r1)<1e-4: return cyl(p0,p1,r0)
    pl=G.Plane(p0,p1-p0); h=(p1-p0).Length
    rv=G.RevSurface.Create(G.LineCurve(G.Point3d(r0,0,0),G.Point3d(r1,0,h)),G.Line(G.Point3d(0,0,0),G.Point3d(0,0,1)))
    b=G.Brep.CreateFromRevSurface(rv,True,True); b.Transform(G.Transform.PlaneToPlane(G.Plane.WorldXY,pl)); return b
def union(br):
    for tol in (0.001,0.0001,0.0005,0.002):
        u=G.Brep.CreateBooleanUnion(br,tol)
        if u and len(u)==1: return u[0],tol
    return None,None
def istube(f):
    s=f.UnderlyingSurface()
    return isinstance(s,G.RevSurface) or f.TryGetCylinder(1e-3)[0] or f.TryGetCone(1e-3)[0]
def cands(b, skip):
    res=[]
    for e in b.Edges:
        fs=e.AdjacentFaces()
        if len(fs)!=2: continue
        F=[b.Faces[i] for i in fs]
        if not any(istube(f) for f in F): continue
        if any(f.IsPlanar(1e-3) and smallface(f) for f in F): continue
        if F[0].IsPlanar(1e-3) and F[1].IsPlanar(1e-3): continue
        mp=e.PointAt(e.Domain.Mid)
        if any(mp.DistanceTo(s)<0.01 for s in skip): continue
        ns=[]
        for f in F:
            ok,u_,v_=f.ClosestPoint(mp); ns.append(f.NormalAt(u_,v_))
        if ns[0]*ns[1]<0.995: res.append((e.EdgeIndex,mp))
    return res
REF=[0.0]
RADMAP={}
def area(b):
    a=G.AreaMassProperties.Compute(b); return a.Area if a else 0.0
def good(x):
    if x is None or len(x)!=1 or not x[0].IsValid or x[0].Faces.Count==0 or not x[0].IsSolid: return False
    return area(x[0])>=0.97*REF[0]
def fillet(b,rad,tol):
    REF[0]=area(b); b0=b
    c=cands(b,[])
    if not c: return b,0,0
    ids=[i for i,m in c]
    for k in (1.0,0.75,0.5):
        f=G.Brep.CreateFilletEdges(b,ids,[rad*k]*len(ids),[rad*k]*len(ids),G.BlendType.Fillet,G.RailType.RollingBall,tol)
        if good(f): return f[0],len(ids),len(ids)
    skip=[]; ok=0; total=len(ids)
    for it in range(30):
        c=cands(b,skip)
        if not c: break
        i,m=c[0]; skip.append(m)
        for k in (1.0,0.6,0.35):
            f=G.Brep.CreateFilletEdges(b,[i],[rad*k],[rad*k],G.BlendType.Fillet,G.RailType.RollingBall,tol)
            if f is not None and len(f)==1 and f[0].IsValid and f[0].IsSolid and f[0].Faces.Count>0 and f[0].Faces.Count>=b.Faces.Count:
                b=f[0]; ok+=1; break
    if ok and area(b)<0.97*REF[0]: return b0,total,0
    return b,total,ok
def rr(rec,end,stub_r0):
    p0,p1,r,b=rec
    return (stub_r0 if end==0 else r) if p0.Z<2.81 else r
def joints(recs,nodes,stub_r0,base_fil,i0,i1):
    out=[]; st=[0,0,0,0]
    for n in nodes[i0:i1]:
        p=n[0]; br=[]; rmax=0
        for rec in recs:
            p0,p1,r,b=rec
            if p0.DistanceTo(p)<0.05: a,c,ra,rc=p0,p1,rr(rec,0,stub_r0),rr(rec,1,stub_r0)
            elif p1.DistanceTo(p)<0.05: a,c,ra,rc=p1,p0,rr(rec,1,stub_r0),rr(rec,0,stub_r0)
            else: continue
            br.append(cone(a,a+(c-a)*0.5,ra,(ra+rc)/2)); rmax=max(rmax,ra)
        if len(br)<2: out.extend(br); continue
        br.append(G.Sphere(p,rmax).ToBrep())
        u,tol=union(br)
        if u is None: st[3]+=1; out.extend(br); continue
        rad=base_fil if (p.Z<3.5 and stub_r0>0.141) else (0.04 if rmax>0.13 else (0.03 if rmax>0.10 else 0.025))
        f,tot,ok=fillet(u,rad,tol); out.append(f); st[0]+=1; st[1]+=tot; st[2]+=ok
    return out,st
def bases(recs,ring,stub_r0,base_fil):
    out=[]; st=[0,0,0,0]
    bs=[rec for rec in recs if rec[0].Z<2.81]; groups=[]
    for rec in bs:
        for g in groups:
            if g[0][0].DistanceTo(rec[0])<0.7: g.append(rec); break
        else: groups.append([rec])
    for g in groups:
        c=G.Point3d(g[0][0].X,g[0][0].Y,2.6)
        box=G.Box(G.Plane(c,G.Vector3d.ZAxis),G.Interval(-0.9,0.9),G.Interval(-0.9,0.9),G.Interval(-0.3,0.25)).ToBrep()
        br=list(G.Brep.CreateBooleanIntersection(ring,box,0.001) or [])
        for p0,p1,r,b in g:
            d=(p1-p0)/(p1-p0).Length
            st_=cone(p0-d*0.15,p0+(p1-p0)*0.5,stub_r0,(stub_r0+r)/2)
            cut=G.Box(G.Plane.WorldXY,G.Interval(p0.X-3,p0.X+3),G.Interval(p0.Y-3,p0.Y+3),G.Interval(2.78,4.0)).ToBrep()
            tr=G.Brep.CreateBooleanIntersection(st_,cut,0.001)
            br.append(tr[0] if tr else st_)
        u,tol=union(br)
        if u is None: st[3]+=1; out.extend(br); continue
        f,tot,ok=fillet(u,base_fil,tol); out.append(f); st[0]+=1; st[1]+=tot; st[2]+=ok
    return out,st

def cyl_rot(p0,p1,r,ang):
    pl=G.Plane(p0,p1-p0); pl.Rotate(ang,pl.ZAxis)
    return G.Cylinder(G.Circle(pl,r),(p1-p0).Length).ToBrep(True,True)
def node_parts(recs,p,stub_r0,ang=0.0,sk=1.0):
    br=[];rmax=0
    for rec in recs:
        p0,p1,r,b=rec
        if p0.DistanceTo(p)<0.05: a,c,ra,rc=p0,p1,rr(rec,0,stub_r0),rr(rec,1,stub_r0)
        elif p1.DistanceTo(p)<0.05: a,c,ra,rc=p1,p0,rr(rec,1,stub_r0),rr(rec,0,stub_r0)
        else: continue
        m=a+(c-a)*0.5
        br.append(cyl_rot(a,m,ra,ang) if abs(ra-rc)<1e-4 else cone(a,m,ra,(ra+rc)/2)); rmax=max(rmax,ra)
    br.append(G.Sphere(p,rmax*sk).ToBrep()); return br,rmax
def robust_joint(recs,p,stub_r0,base_fil):
    for ang in (0.0,0.3,0.7,1.1):
        for sk in (1.0,1.003,0.997):
            br,rmax=node_parts(recs,p,stub_r0,ang,sk)
            u,tol=union(br)
            if u is not None and u.IsValid and u.IsSolid:
                rad=RADMAP.get(round(rmax,3)) if RADMAP else (base_fil if (p.Z<3.5 and stub_r0>0.141) else (0.04 if rmax>0.13 else (0.03 if rmax>0.10 else 0.025)))
                f,tot,ok=fillet(u,rad,tol)
                if f.IsValid and f.IsSolid: return f,tot,ok
    return None,0,0
def cands_ring(b, skip, ringonly):
    res=[]
    for e in b.Edges:
        fs=e.AdjacentFaces()
        if len(fs)!=2: continue
        F=[b.Faces[i] for i in fs]; t=[istube(f) for f in F]
        if not any(t): continue
        if any(f.IsPlanar(1e-3) and smallface(f) for f in F): continue
        if ringonly and all(t): continue
        if (not ringonly) and not all(t): continue
        mp=e.PointAt(e.Domain.Mid)
        if any(mp.DistanceTo(s)<0.01 for s in skip): continue
        ns=[]
        for f in F:
            ok,u_,v_=f.ClosestPoint(mp); ns.append(f.NormalAt(u_,v_))
        if ns[0]*ns[1]<0.995: res.append((e.EdgeIndex,mp))
    return res
def fillet_pass(b,rad,tol,ringonly):
    REF[0]=area(b); b0=b
    c=cands_ring(b,[],ringonly)
    if not c: return b,0,0
    ids=[i for i,m in c]
    for k in (1.0,0.75,0.5):
        f=G.Brep.CreateFilletEdges(b,ids,[rad*k]*len(ids),[rad*k]*len(ids),G.BlendType.Fillet,G.RailType.RollingBall,tol)
        if good(f): return f[0],len(ids),len(ids)
    skip=[]; ok=0
    for it in range(30):
        c=cands_ring(b,skip,ringonly)
        if not c: break
        i,m=c[0]; skip.append(m)
        for k in (1.0,0.6,0.35):
            f=G.Brep.CreateFilletEdges(b,[i],[rad*k],[rad*k],G.BlendType.Fillet,G.RailType.RollingBall,tol)
            if f is not None and len(f)==1 and f[0].IsValid and f[0].IsSolid and f[0].Faces.Count>=b.Faces.Count:
                b=f[0]; ok+=1; break
    if ok and area(b)<0.97*REF[0]: return b0,len(ids),0
    return b,len(ids),ok
def bases2(recs,ring,stub_r0,base_fil):
    out=[]; st=[0,0,0,0,0]
    bs=[rec for rec in recs if rec[0].Z<2.81]; groups=[]
    for rec in bs:
        for g in groups:
            if g[0][0].DistanceTo(rec[0])<0.7: g.append(rec); break
        else: groups.append([rec])
    for g in groups:
        c=G.Point3d(g[0][0].X,g[0][0].Y,2.6)
        box=G.Box(G.Plane(c,G.Vector3d.ZAxis),G.Interval(-0.9,0.9),G.Interval(-0.9,0.9),G.Interval(-0.3,0.25)).ToBrep()
        rc=list(G.Brep.CreateBooleanIntersection(ring,box,0.001) or [])
        res=None
        for ang in (0.0,0.4,0.9):
            br=list(rc)
            for p0,p1,r,b in g:
                d=(p1-p0)/(p1-p0).Length; m=p0+(p1-p0)*0.5
                st_=cyl_rot(p0-d*0.15,m,r,ang) if abs(stub_r0-r)<1e-4 else cone(p0-d*0.15,m,stub_r0,(stub_r0+r)/2)
                cut=G.Box(G.Plane.WorldXY,G.Interval(p0.X-3,p0.X+3),G.Interval(p0.Y-3,p0.Y+3),G.Interval(2.78,4.0)).ToBrep()
                tr=G.Brep.CreateBooleanIntersection(st_,cut,0.001)
                br.append(tr[0] if tr else st_)
            u,tol=union(br)
            if u is None: continue
            f1,t1,o1=fillet_pass(u,base_fil,tol,True)
            f2,t2,o2=fillet_pass(f1,base_fil*0.8,tol,False)
            if res is None or o1+o2>res[1]: res=(f2,o1+o2,t1+t2,o1,o2)
            if o1==t1 and o2==t2: break
        if res is None: st[4]+=1; continue
        out.append(res[0]); st[0]+=1; st[1]+=res[2]; st[2]+=res[1]; st[3]+=res[3]
    return out,st

def run_joints(recs,nodes,stub,bf,i0,i1,zmax=99):
    out={}; st=[0,0,0]
    for i,n in enumerate(nodes):
        if i<i0 or i>=i1 or n[0].Z>=zmax: continue
        p=n[0]
        if sum(1 for r in recs if r[0].DistanceTo(p)<0.05 or r[1].DistanceTo(p)<0.05)<2: continue
        f,tot,ok=robust_joint(recs,p,stub,bf); out[i]=f; st[0]+=1; st[1]+=tot; st[2]+=ok
    return out,st

def extract(doc, layer_path, ring_top):
    L=doc.Layers[doc.Layers.FindByFullPath(layer_path,-1)]
    recs=[]; bad=0
    for o in doc.Objects.FindByLayer(L):
        b=o.Geometry; cyl=None; cents=[]
        for f in b.Faces:
            ok,c=f.TryGetCylinder(0.001)
            if ok: cyl=c; continue
            if f.IsPlanar(1e-3):
                a=G.AreaMassProperties.Compute(f.DuplicateFace(False))
                if a and a.Area<1.0: cents.append(a.Centroid)
        if cyl is None or not cents: bad+=1; continue
        ax=G.Line(cyl.Center, cyl.Center+cyl.Axis)
        ts=sorted(ax.ClosestParameter(p) for p in cents)
        if len(cents)==1:
            p1=ax.PointAt(ts[0]); d=cyl.Axis; t=(ring_top-cyl.Center.Z)/d.Z; p0=cyl.Center+d*t
        else:
            p0,p1=ax.PointAt(ts[0]),ax.PointAt(ts[-1])
        if p0.Z>p1.Z: p0,p1=p1,p0
        recs.append((p0,p1,cyl.Radius,p0.Z<ring_top+0.01))
    return recs,bad
def cluster(recs, ring_top):
    nodes=[]
    def add(p,r):
        for n in nodes:
            if n[0].DistanceTo(p)<0.05: n[1]=max(n[1],r); n[2]+=1; return
        nodes.append([p,r,1])
    for p0,p1,r,b in recs:
        if p0.Z>=ring_top+0.01: add(p0,r)
        add(p1,r)
    return nodes

def joints_range(recs,nodes,stub,i0,i1):
    out={}; st=[0,0,0,0]
    for i in range(i0,min(i1,len(nodes))):
        p=nodes[i][0]
        d=sum(1 for r in recs if r[0].DistanceTo(p)<0.05 or r[1].DistanceTo(p)<0.05)
        if d<2:
            br,_=node_parts(recs,p,stub); out[i]=("halves",br[:-1]); continue
        f,tot,ok=robust_joint(recs,p,stub,0.04)
        if f is None:
            br,_=node_parts(recs,p,stub); out[i]=("raw",br); st[3]+=1; continue
        out[i]=("joint",[f]); st[0]+=1; st[1]+=tot; st[2]+=ok
    return out,st
def foot_groups(recs,ring_top):
    bs=[rec for rec in recs if rec[0].Z<ring_top+0.01]; groups=[]
    for rec in bs:
        for g in groups:
            if g[0][0].DistanceTo(rec[0])<0.7: g.append(rec); break
        else: groups.append([rec])
    return groups
def foot(recs_g,ring,base_fil,ring_top):
    g=recs_g
    c=G.Point3d(g[0][0].X,g[0][0].Y,ring_top-0.2)
    box=G.Box(G.Plane(c,G.Vector3d.ZAxis),G.Interval(-0.9,0.9),G.Interval(-0.9,0.9),G.Interval(-0.3,0.25)).ToBrep()
    rc=list(G.Brep.CreateBooleanIntersection(ring,box,0.001) or [])
    best=None
    for ang in (0.0,0.4,0.9):
        br=list(rc)
        for p0,p1,r,b in g:
            d=(p1-p0)/(p1-p0).Length; m=p0+(p1-p0)*0.5
            st_=cyl_rot(p0-d*0.15,m,r,ang)
            cut=G.Box(G.Plane.WorldXY,G.Interval(p0.X-3,p0.X+3),G.Interval(p0.Y-3,p0.Y+3),G.Interval(ring_top-0.02,ring_top+1.2)).ToBrep()
            tr=G.Brep.CreateBooleanIntersection(st_,cut,0.001)
            br.append(tr[0] if tr else st_)
        u,tol=union(br)
        if u is None: continue
        f1,t1,o1=fillet_pass(u,base_fil,tol,True)
        f2,t2,o2=fillet_pass(f1,base_fil*0.8,tol,False)
        if best is None or o1+o2>best[1]: best=(f2,o1+o2,t1+t2)
        if o1==t1 and o2==t2: break
    if best is None: return None,0,0
    return best[0],best[2],best[1]
