int RR=5, MM=1; double DD=800, FE=0.5; double HX=5000; int IT=150; double COEF=10; bool PIN8=false; bool TREE=false; int NF=16; bool STAG=false; bool DIA=false; bool DIA2=true; double R0=400; int[] ZN=new int[]{64,32,16}; double[] ZR=new double[]{840,870,930}; bool SHOW=false; double QV=1;
// explicit D8-symmetric cap triangulation, octagon edge k (k=0 faces (-,-)), m angular divisions per sector (even), R rings
// returns tets (cap triangle + apex) and the 8 reaction-cell centroids
(List<Brep> tets, List<Point3d> targets, List<Polyline> tris) GenTets(int R,int m,double depth,double Fexp,double Q=1){
 double b=1000*Math.Cos(Math.PI/8), a=Q*b*(1+Math.Tan(Math.PI/8));
 var V=new[]{new Point3d(-b,-a+b,0),new Point3d(-a+b,-b,0),new Point3d(a-b,-b,0),new Point3d(b,-a+b,0),new Point3d(b,a-b,0),new Point3d(a-b,b,0),new Point3d(-a+b,b,0),new Point3d(-b,a-b,0)};
 var C=Point3d.Origin; var apex=new Point3d(0,0,-depth);
 var tris=new List<Polyline>(); var targets=new List<Point3d>();
 double F(int r)=>Math.Pow((double)r/(R+1),Fexp);
 for(int k=0;k<8;k++){ var A=V[k]; var B=V[(k+1)%8];
  Point3d P(int r,int j){ if(r==0) return C; var e=A+(B-A)*((double)j/m); return C+(e-C)*F(r); }
  // centre fan
  for(int j=0;j<m;j++) tris.Add(new Polyline(new[]{C,P(1,j),P(1,j+1),C}));
  // strips, diagonals mirrored about the sector axis
  for(int r=1;r<R;r++) for(int j=0;j<m;j++){
    if(j<m/2){ tris.Add(new Polyline(new[]{P(r,j),P(r+1,j),P(r+1,j+1),P(r,j)})); tris.Add(new Polyline(new[]{P(r,j),P(r+1,j+1),P(r,j+1),P(r,j)})); }
    else     { tris.Add(new Polyline(new[]{P(r,j),P(r+1,j),P(r,j+1),P(r,j)})); tris.Add(new Polyline(new[]{P(r,j+1),P(r+1,j),P(r+1,j+1),P(r,j+1)})); } }
  // outer band: fans to the two octagon vertices + the reaction triangle in the middle
  for(int j=0;j<m;j++){ var cv=(j<m/2)?A:B; tris.Add(new Polyline(new[]{P(R,j),cv,P(R,j+1),P(R,j)})); }
  var mid=P(R,m/2); tris.Add(new Polyline(new[]{mid,A,B,mid}));
  targets.Add((mid+A+B+apex)/4.0);
 }
 var tets=new List<Brep>();
 foreach(var t in tris){ var s=Brep.CreateFromCornerPoints(t[0],t[1],t[2],0.001); var ext=Surface.CreateExtrusionToPoint(new PolylineCurve(t),apex);
   var pts=new[]{t[0],t[1],t[2],apex}; var faces=new List<Brep>{ Brep.CreateFromCornerPoints(pts[0],pts[1],pts[2],0.001), Brep.CreateFromCornerPoints(pts[0],pts[1],pts[3],0.001), Brep.CreateFromCornerPoints(pts[1],pts[2],pts[3],0.001), Brep.CreateFromCornerPoints(pts[2],pts[0],pts[3],0.001)};
   var j=Brep.JoinBreps(faces,0.001); tets.Add(j[0]); }
 return (tets,targets,tris);
}
// tree cap: octagon V (proportion Q), crown 32-gon radius r0 (fan to centre = horizontal crown ring in the form)
(List<Brep> tets, List<Point3d> targets, List<Polyline> tris) GenTree(double r0,double depth,double Q){
 double b=1000*Math.Cos(Math.PI/8), a=Q*b*(1+Math.Tan(Math.PI/8));
 var V=new[]{new Point3d(-b,-a+b,0),new Point3d(-a+b,-b,0),new Point3d(a-b,-b,0),new Point3d(b,-a+b,0),new Point3d(b,a-b,0),new Point3d(a-b,b,0),new Point3d(-a+b,b,0),new Point3d(-b,a-b,0)};
 var C=Point3d.Origin; var apex=new Point3d(0,0,-depth);
 double th0=Math.Atan2(V[0].Y,V[0].X);
 Point3d Cr(int k,int i){ double t=th0+(k*8+i)*2*Math.PI/64.0; return new Point3d(r0*Math.Cos(t),r0*Math.Sin(t),0); } // c_i of sector k, i=0..4 (c_4^k = c_0^{k+1})
 var tris=new List<Polyline>(); var targets=new List<Point3d>();
 Polyline T(Point3d p,Point3d q,Point3d r)=>new Polyline(new[]{p,q,r,p});
 for(int k=0;k<8;k++){ int k1=(k+1)%8; var Vk=V[k]; var Vk1=V[k1];
  // octagon vertex k actually sits at angle of V[k]; crown c_0^k aligned with it
  tris.Add(T(Vk,Vk1,Cr(k,4))); targets.Add((Vk+Vk1+Cr(k,4)+apex)/4.0); // foot: sector middle crown vertex = index 4 of 8 per sector
  tris.Add(T(Vk1,Cr(k,4),Cr(k1,4)));            // X node around octagon vertex k+1
  tris.Add(T(Cr(k,4),Cr(k1,0),Cr(k1,4)));       // Y (chord 45 -> 22.5)
  tris.Add(T(Cr(k,4),Cr(k,6),Cr(k1,0)));        // Z
  tris.Add(T(Cr(k1,0),Cr(k1,2),Cr(k1,4)));      // Z
  tris.Add(T(Cr(k,4),Cr(k,5),Cr(k,6)));         // W levels (11.25 chords)
  tris.Add(T(Cr(k,6),Cr(k,7),Cr(k1,0)));
  tris.Add(T(Cr(k1,0),Cr(k1,1),Cr(k1,2)));
  tris.Add(T(Cr(k1,2),Cr(k1,3),Cr(k1,4)));
  for(int i=0;i<8;i++) tris.Add(T(C,Cr(k,i),Cr(k,i+1)));   // crown fan -> crown ring nodes
 }
 var tets=new List<Brep>();
 foreach(var t in tris){ var pts=new[]{t[0],t[1],t[2],apex}; var faces=new List<Brep>{ Brep.CreateFromCornerPoints(pts[0],pts[1],pts[2],0.001), Brep.CreateFromCornerPoints(pts[0],pts[1],pts[3],0.001), Brep.CreateFromCornerPoints(pts[1],pts[2],pts[3],0.001), Brep.CreateFromCornerPoints(pts[2],pts[0],pts[3],0.001)}; tets.Add(Brep.JoinBreps(faces,0.001)[0]); }
 return (tets,targets,tris);
}
// zipper tree: crown fan at ring 0, rings of N points at angles thV + (j+0.5)*360/N, last ring = octagon vertices (regular, Q=1)
(List<Brep> tets, List<Point3d> targets, List<Polyline> tris) GenZip(int[] Ns,double[] Rs,double depth,double Q=1){
 var C=Point3d.Origin; var apex=new Point3d(0,0,-depth);
 double thV=-157.5*Math.PI/180; // octagon vertex 0 angle
 var rings=new List<List<(double t,Point3d p)>>();
 for(int L=0;L<Ns.Length;L++){ var ring=new List<(double,Point3d)>(); for(int j=0;j<Ns[L];j++){ double t=thV+(j+0.5)*2*Math.PI/Ns[L]; ring.Add((t,new Point3d(Rs[L]*Math.Cos(t),Rs[L]*Math.Sin(t),0))); } rings.Add(ring); }
 double ob=1000*Math.Cos(Math.PI/8), oa=Q*ob*(1+Math.Tan(Math.PI/8));
 var OV=new[]{new Point3d(-ob,-oa+ob,0),new Point3d(-oa+ob,-ob,0),new Point3d(oa-ob,-ob,0),new Point3d(ob,-oa+ob,0),new Point3d(ob,oa-ob,0),new Point3d(oa-ob,ob,0),new Point3d(-oa+ob,ob,0),new Point3d(-ob,oa-ob,0)};
 var oct=new List<(double,Point3d)>(); for(int j=0;j<8;j++){ double t=Math.Atan2(OV[j].Y,OV[j].X); oct.Add((t,OV[j])); } rings.Add(oct);
 var tris=new List<Polyline>(); Polyline T(Point3d p,Point3d q,Point3d r)=>new Polyline(new[]{p,q,r,p});
 var r0=rings[0]; for(int j=0;j<r0.Count;j++) tris.Add(T(C,r0[j].Item2,r0[(j+1)%r0.Count].Item2));
 var targets=new List<Point3d>();
 for(int L=0;L+1<rings.Count;L++){ var A=rings[L]; var B=rings[L+1];
   double U(List<(double t,Point3d p)> R,int k){ int n=R.Count; double t=R[k%n].Item1+2*Math.PI*(k/n); while(t<thV-1e-9) t+=2*Math.PI; return t; }
   // unwrap relative to thV
   int nA=A.Count,nB=B.Count,i=0,j=0;
   while(i<nA||j<nB){ double ta=U(A,i+1), tb=U(B,j+1);
     if(j>=nB || (i<nA && ta<tb)){ tris.Add(T(A[i%nA].Item2,A[(i+1)%nA].Item2,B[j%nB].Item2)); i++; }
     else { var tr=T(B[j%nB].Item2,B[(j+1)%nB].Item2,A[i%nA].Item2); tris.Add(tr); if(L+1==rings.Count-1) targets.Add((tr[0]+tr[1]+tr[2]+apex)/4.0); j++; } }
 }
 var tets=new List<Brep>();
 foreach(var t in tris){ var pts=new[]{t[0],t[1],t[2],apex}; var faces=new List<Brep>{ Brep.CreateFromCornerPoints(pts[0],pts[1],pts[2],0.001), Brep.CreateFromCornerPoints(pts[0],pts[1],pts[3],0.001), Brep.CreateFromCornerPoints(pts[1],pts[2],pts[3],0.001), Brep.CreateFromCornerPoints(pts[2],pts[0],pts[3],0.001)}; tets.Add(Brep.JoinBreps(faces,0.001)[0]); }
 return (tets,targets,tris);
}

(List<Brep> tets, List<Point3d> targets, List<Polyline> tris) GenTetsN(int R,int m,double depth,double Fexp,int NV){
 double st=2*Math.PI/NV, a0=-135*Math.PI/180-st/2; var V=Enumerable.Range(0,NV).Select(k=>new Point3d(1000*Math.Cos(a0+k*st),1000*Math.Sin(a0+k*st),0)).ToArray();
 var C=Point3d.Origin; var apex=new Point3d(0,0,-depth);
 var tris=new List<Polyline>(); var targets=new List<Point3d>();
 double F(int r)=>Math.Pow((double)r/(R+1),Fexp);
 for(int k=0;k<NV;k++){ var A=V[k]; var B=V[(k+1)%NV];
  Point3d P(int r,int j){ if(r==0) return C; var e=A+(B-A)*((double)j/m); return C+(e-C)*F(r); }
  // centre fan
  for(int j=0;j<m;j++) tris.Add(new Polyline(new[]{C,P(1,j),P(1,j+1),C}));
  // strips, diagonals mirrored about the sector axis
  for(int r=1;r<R;r++) for(int j=0;j<m;j++){
    if(j<m/2){ tris.Add(new Polyline(new[]{P(r,j),P(r+1,j),P(r+1,j+1),P(r,j)})); tris.Add(new Polyline(new[]{P(r,j),P(r+1,j+1),P(r,j+1),P(r,j)})); }
    else     { tris.Add(new Polyline(new[]{P(r,j),P(r+1,j),P(r,j+1),P(r,j)})); tris.Add(new Polyline(new[]{P(r,j+1),P(r+1,j),P(r+1,j+1),P(r,j+1)})); } }
  // outer band: fans to the two octagon vertices + the reaction triangle in the middle
  for(int j=0;j<m;j++){ var cv=(j<m/2)?A:B; tris.Add(new Polyline(new[]{P(R,j),cv,P(R,j+1),P(R,j)})); }
  var mid=P(R,m/2); tris.Add(new Polyline(new[]{mid,A,B,mid}));
  targets.Add((mid+A+B+apex)/4.0);
 }
 var tets=new List<Brep>();
 foreach(var t in tris){ var s=Brep.CreateFromCornerPoints(t[0],t[1],t[2],0.001); var ext=Surface.CreateExtrusionToPoint(new PolylineCurve(t),apex);
   var pts=new[]{t[0],t[1],t[2],apex}; var faces=new List<Brep>{ Brep.CreateFromCornerPoints(pts[0],pts[1],pts[2],0.001), Brep.CreateFromCornerPoints(pts[0],pts[1],pts[3],0.001), Brep.CreateFromCornerPoints(pts[1],pts[2],pts[3],0.001), Brep.CreateFromCornerPoints(pts[2],pts[0],pts[3],0.001)};
   var j=Brep.JoinBreps(faces,0.001); tets.Add(j[0]); }
 return (tets,targets,tris);
}
// staggered rings: ring points alternate between division points and half-way points, so edges between rings are zig-zag (angled) instead of radial
(List<Brep> tets, List<Point3d> targets, List<Polyline> tris) GenStag(int R,int m,double depth,double Q,int NV){
 Point3d[] V;
 if(NV==8){ double b=1000*Math.Cos(Math.PI/8), a=Q*b*(1+Math.Tan(Math.PI/8)); V=new[]{new Point3d(-b,-a+b,0),new Point3d(-a+b,-b,0),new Point3d(a-b,-b,0),new Point3d(b,-a+b,0),new Point3d(b,a-b,0),new Point3d(a-b,b,0),new Point3d(-a+b,b,0),new Point3d(-b,a-b,0)}; }
 else { double st=2*Math.PI/NV, a0=-135*Math.PI/180-st/2; V=Enumerable.Range(0,NV).Select(k=>new Point3d(1000*Math.Cos(a0+k*st),1000*Math.Sin(a0+k*st),0)).ToArray(); }
 var C=Point3d.Origin; var apex=new Point3d(0,0,-depth);
 double th0=Math.Atan2(V[0].Y,V[0].X)-1e-6;
 double Ang(Point3d p){ double t=Math.Atan2(p.Y,p.X); while(t<th0) t+=2*Math.PI; while(t>=th0+2*Math.PI) t-=2*Math.PI; return t; }
 var rings=new List<List<(double,Point3d)>>();
 for(int r=1;r<=R;r++){ double f=(double)r/(R+1); bool half=((R-r)%2==0); var ring=new List<(double,Point3d)>();
   for(int k=0;k<NV;k++){ var A=V[k]; var B=V[(k+1)%NV]; for(int j=0;j<m;j++){ double s=(half? j+0.5 : j)/m; var p=C+((A+(B-A)*s)-C)*f; ring.Add((Ang(p),p)); } }
   rings.Add(ring.OrderBy(x=>x.Item1).ToList()); }
 rings.Add(V.Select(p=>(Ang(p),p)).OrderBy(x=>x.Item1).ToList());
 var tris=new List<Polyline>(); Polyline T(Point3d p,Point3d q,Point3d r)=>new Polyline(new[]{p,q,r,p});
 var r0=rings[0]; for(int j=0;j<r0.Count;j++) tris.Add(T(C,r0[j].Item2,r0[(j+1)%r0.Count].Item2));
 var targets=new List<Point3d>();
 for(int L=0;L+1<rings.Count;L++){ var A=rings[L]; var B=rings[L+1]; int nA=A.Count,nB=B.Count,i=0,j=0;
   double UA(int k)=>A[k%nA].Item1+2*Math.PI*(k/nA); double UB(int k)=>B[k%nB].Item1+2*Math.PI*(k/nB);
   // start: align so that both start just after th0
   while(i<nA||j<nB){ double ta=UA(i+1), tb=UB(j+1);
     if(j>=nB || (i<nA && ta<tb)){ tris.Add(T(A[i%nA].Item2,A[(i+1)%nA].Item2,B[j%nB].Item2)); i++; }
     else { var tr=T(B[j%nB].Item2,B[(j+1)%nB].Item2,A[i%nA].Item2); tris.Add(tr); if(L+1==rings.Count-1) targets.Add((tr[0]+tr[1]+tr[2]+apex)/4.0); j++; } } }
 var tets=new List<Brep>();
 foreach(var t in tris){ var pts=new[]{t[0],t[1],t[2],apex}; var faces=new List<Brep>{ Brep.CreateFromCornerPoints(pts[0],pts[1],pts[2],0.001), Brep.CreateFromCornerPoints(pts[0],pts[1],pts[3],0.001), Brep.CreateFromCornerPoints(pts[1],pts[2],pts[3],0.001), Brep.CreateFromCornerPoints(pts[2],pts[0],pts[3],0.001)}; tets.Add(Brep.JoinBreps(faces,0.001)[0]); }
 return (tets,targets,tris);
}
// diamond (diagrid) cap: quads between staggered rings -> 4-valent form nodes with only diagonal bars
(List<Brep> tets, List<Point3d> targets, List<Polyline> tris) GenDiamond(int R,int m,double depth,double Q,int NV,double F0=0){
 Point3d[] V;
 if(NV==8){ double b=1000*Math.Cos(Math.PI/8), a=Q*b*(1+Math.Tan(Math.PI/8)); V=new[]{new Point3d(-b,-a+b,0),new Point3d(-a+b,-b,0),new Point3d(a-b,-b,0),new Point3d(b,-a+b,0),new Point3d(b,a-b,0),new Point3d(a-b,b,0),new Point3d(-a+b,b,0),new Point3d(-b,a-b,0)}; }
 else { double st=2*Math.PI/NV, a0=-135*Math.PI/180-st/2; V=Enumerable.Range(0,NV).Select(k=>new Point3d(1000*Math.Cos(a0+k*st),1000*Math.Sin(a0+k*st),0)).ToArray(); }
 var C=Point3d.Origin; var apex=new Point3d(0,0,-depth); int n=NV*m;
 double O(int r)=>((R-r)%2==0)?0.5:0.0;
 Point3d P(int r,int i){ i=((i%n)+n)%n; double s=(i+O(r))/m; int k=(int)Math.Floor(s); double fr=s-k; k%=NV; var A=V[k]; var B=V[(k+1)%NV]; double f=(F0<=0? (double)r/(R+1) : F0+(1-F0)*(double)(r-1)/R); return C+((A+(B-A)*fr)-C)*f; }
 var polys=new List<Polyline>(); Polyline T(params Point3d[] p){ var l=p.ToList(); l.Add(p[0]); return new Polyline(l); }
 for(int i=0;i<n;i++) polys.Add(T(C,P(1,i),P(1,i+1)));                                  // crown fan (small crown ring)
 for(int i=0;i<n;i++) polys.Add(O(1)==0? T(P(1,i),P(2,i),P(1,i+1)) : T(P(1,i),P(2,i+1),P(1,i+1)));   // inner half-diamonds
 for(int r=1;r<=R-2;r++) for(int i=0;i<n;i++) polys.Add(O(r)==0? T(P(r,i),P(r+1,i),P(r+2,i),P(r+1,i-1)) : T(P(r,i),P(r+1,i+1),P(r+2,i),P(r+1,i)));  // diamonds
 for(int i=0;i<n;i++) polys.Add(O(R)==0? T(P(R,i),P(R,i+1),P(R-1,i)) : T(P(R,i),P(R,i+1),P(R-1,i+1)));  // outer half-diamonds
 // outer band: zipper from ring R to the polygon vertices
 double th0=Math.Atan2(V[0].Y,V[0].X)-1e-6; double Ang(Point3d p){ double t=Math.Atan2(p.Y,p.X); while(t<th0) t+=2*Math.PI; while(t>=th0+2*Math.PI) t-=2*Math.PI; return t; }
 var A_=Enumerable.Range(0,n).Select(i=>P(R,i)).Select(p=>(Ang(p),p)).OrderBy(x=>x.Item1).ToList(); var B_=V.Select(p=>(Ang(p),p)).OrderBy(x=>x.Item1).ToList();
 var targets=new List<Point3d>(); int nA=A_.Count,nB=B_.Count,ii=0,jj=0;
 double UA(int k)=>A_[k%nA].Item1+2*Math.PI*(k/nA); double UB(int k)=>B_[k%nB].Item1+2*Math.PI*(k/nB);
 while(ii<nA||jj<nB){ if(jj>=nB || (ii<nA && UA(ii+1)<UB(jj+1))){ polys.Add(T(A_[ii%nA].Item2,A_[(ii+1)%nA].Item2,B_[jj%nB].Item2)); ii++; } else { var tr=T(B_[jj%nB].Item2,B_[(jj+1)%nB].Item2,A_[ii%nA].Item2); polys.Add(tr); targets.Add((tr[0]+tr[1]+tr[2]+apex)/4.0); jj++; } }
 var tets=new List<Brep>();
 foreach(var pl in polys){ int c=pl.Count-1; var faces=new List<Brep>();
   if(c==3) faces.Add(Brep.CreateFromCornerPoints(pl[0],pl[1],pl[2],0.001)); else faces.Add(Brep.CreateFromCornerPoints(pl[0],pl[1],pl[2],pl[3],0.001));
   for(int q=0;q<c;q++) faces.Add(Brep.CreateFromCornerPoints(pl[q],pl[(q+1)%c],apex,0.001));
   tets.Add(Brep.JoinBreps(faces,0.001)[0]); }
 return (tets,targets,polys);
}

(List<Brep> tets, List<Point3d> targets, List<Polyline> tris) GenDiamond2(int R,int m,double depth,double Q,int NV,double F0){
 Point3d[] V;
 if(NV==8){ double b=1000*Math.Cos(Math.PI/8), a=Q*b*(1+Math.Tan(Math.PI/8)); V=new[]{new Point3d(-b,-a+b,0),new Point3d(-a+b,-b,0),new Point3d(a-b,-b,0),new Point3d(b,-a+b,0),new Point3d(b,a-b,0),new Point3d(a-b,b,0),new Point3d(-a+b,b,0),new Point3d(-b,a-b,0)}; }
 else { double st=2*Math.PI/NV, a0=-135*Math.PI/180-st/2; V=Enumerable.Range(0,NV).Select(k=>new Point3d(1000*Math.Cos(a0+k*st),1000*Math.Sin(a0+k*st),0)).ToArray(); }
 var C=Point3d.Origin; var apex=new Point3d(0,0,-depth); int n=NV*m;
 double O(int r)=>((R-r)%2==0)?0.5:0.0;
 Point3d P(int r,int i){ i=((i%n)+n)%n; double s=(i+O(r))/m; int k=(int)Math.Floor(s); double fr=s-k; k%=NV; var A=V[k]; var B=V[(k+1)%NV]; double f=(F0<=0? (double)r/(R+1) : F0+(1-F0)*(double)(r-1)/R); var pp=C+((A+(B-A)*fr)-C)*f; if(r<R){ var dir=pp-C; dir.Unitize(); pp=C+dir*(1000*Math.Cos(Math.PI/NV)*f); } return pp; }
 var polys=new List<Polyline>(); Polyline T(params Point3d[] p){ var l=p.ToList(); l.Add(p[0]); return new Polyline(l); }
 polys.Add(T(Enumerable.Range(0,n).Select(i=>P(1,i)).ToArray()));                     // crown = one polygon cell
 for(int i=0;i<n;i++) polys.Add(O(1)==0? T(P(1,i),P(2,i),P(1,i+1)) : T(P(1,i),P(2,i+1),P(1,i+1)));   // inner half-diamonds
 for(int r=1;r<=R-2;r++) for(int i=0;i<n;i++) polys.Add(O(r)==0? T(P(r,i),P(r+1,i),P(r+2,i),P(r+1,i-1)) : T(P(r,i),P(r+1,i+1),P(r+2,i),P(r+1,i)));  // diamonds
 for(int i=0;i<n;i++) polys.Add(O(R)==0? T(P(R,i),P(R,i+1),P(R-1,i)) : T(P(R,i),P(R,i+1),P(R-1,i+1)));  // outer half-diamonds
 // outer band, built by hand: mirrored about each foot and each octagon corner (ring R must be the half-offset ring, m odd)
 var targets=new List<Point3d>(); int mid=(m-1)/2;
 for(int k=0;k<NV;k++){ var A=V[k]; var B=V[(k+1)%NV];
   Point3d q(int j)=>P(R,k*m+j);
   for(int j=0;j<mid;j++) polys.Add(T(A,q(j),q(j+1)));
   for(int j=mid;j<m-1;j++) polys.Add(T(B,q(j),q(j+1)));
   var rt=T(A,B,q(mid)); polys.Add(rt); targets.Add((A+B+q(mid)+apex)/4.0);
   polys.Add(T(A,P(R,k*m-1),q(0)));   // corner triangle, symmetric about the octagon vertex
 }
 var tets=new List<Brep>();
 foreach(var pl in polys){ int c=pl.Count-1; var faces=new List<Brep>();
   if(c==3) faces.Add(Brep.CreateFromCornerPoints(pl[0],pl[1],pl[2],0.001)); else if(c==4) faces.Add(Brep.CreateFromCornerPoints(pl[0],pl[1],pl[2],pl[3],0.001)); else faces.Add(Brep.CreatePlanarBreps(new PolylineCurve(pl),0.001)[0]);
   for(int q=0;q<c;q++) faces.Add(Brep.CreateFromCornerPoints(pl[q],pl[(q+1)%c],apex,0.001));
   tets.Add(Brep.JoinBreps(faces,0.001)[0]); }
 return (tets,targets,polys);
}

var g=(DIA2? GenDiamond2(RR,MM,DD,QV,NF,FE) : DIA? GenDiamond(RR,MM,DD,QV,NF,FE) : STAG? GenStag(RR,MM,DD,QV,NF) : NF==12? GenTetsN(RR,MM,DD,FE,12) : TREE? GenZip(ZN,ZR,DD,QV) : GenTets(RR,MM,DD,FE,QV));
var bp=new Param_Brep(); bp.CreateAttributes(); doc.AddObject(bp,false); foreach(var t in g.tets) bp.PersistentData.Append(new GH_Brep(t));
var bld=Add("PFBuild"); bld.Params.Input[0].AddSource(bp); Num(bld,"Absolute Tolerance",0.1); Num(bld,"Planarity Tolerance",0.1);
var exf=Add("Explode PFoam"); W(bld,"Force PFoam",exf,"PFoam"); var ipc=Add("Inspect PFCell"); W(exf,"PFCells",ipc,"PFCell");
var cps=Add("Closest Points"); Pts(cps,"Point",g.targets); W(ipc,"Centroid",cps,"Cloud"); Int(cps,"Count",1);
var lid=Add("List Item"); W(ipc,"ID",lid,"List"); W(cps,"CP Index",lid,"Index"); In(lid,"Index").DataMapping=GH_DataMapping.Flatten;
var ad=Add("Algebraic Dual"); W(bld,"Force PFoam",ad,"Force PFoam"); Num(ad,"Scale",1); Bool(ad,"Flip",false);
var wallC=new PolylineCurve(new[]{new Point3d(-HX,-HX,0),new Point3d(HX,-HX,0),new Point3d(HX,HX,0),new Point3d(-HX,HX,0),new Point3d(-HX,-HX,0)}); var wallPts=wallC.DivideByCount(NF,true).Select(tt=>wallC.PointAt(tt)).ToArray();
var vc=Add("Algebraic Vertex Constraints"); W(ad,"Algebraic Form",vc,"Algebraic Form"); Num(vc,"Scale",1);
if(PIN8){ W(lid,"Item",vc,"PFVertex IDs"); In(vc,"PFVertex IDs").DataMapping=GH_DataMapping.Flatten; Geo(vc,"Constraints",wallPts); }
else { var cpi=Add("Cull Pattern"); W(lid,"Item",cpi,"List"); In(cpi,"List").DataMapping=GH_DataMapping.Flatten; var pq=(Param_Boolean)In(cpi,"Cull Pattern"); pq.PersistentData.Clear(); int stp=NF/4; for(int q=0;q<stp;q++) pq.PersistentData.Append(new GH_Boolean(q==0)); W(cpi,"List",vc,"PFVertex IDs"); Geo(vc,"Constraints",new[]{wallPts[0],wallPts[stp],wallPts[2*stp],wallPts[3*stp]}); }
var wc=new PolylineCurve(new[]{new Point3d(-HX,-HX,0),new Point3d(HX,-HX,0),new Point3d(HX,HX,0),new Point3d(-HX,HX,0),new Point3d(-HX,-HX,0)});
var pvc=Add("PFVertex Constraints"); W(vc,"PFoam",pvc,"PFoam"); W(lid,"Item",pvc,"PFVertex ID"); In(pvc,"PFVertex ID").DataMapping=GH_DataMapping.Flatten;
var cg=(Param_Geometry)In(pvc,"Constraint"); cg.PersistentData.Clear(); for(int k=0;k<NF;k++) cg.PersistentData.Append(new GH_Curve(wc)); Num(pvc,"Coefficient",COEF); Bool(pvc,"On",true);
var perp=Add("PFPerp"); W(pvc,"PFoam",perp,"PFoam"); Int(perp,"Max Iteration",IT); Num(perp,"Deviation",0.1); Num(perp,"Minimum Edge Length",10);
string Stats(IGH_Component src,string outn,string tag){
 var ex=Add("Explode PFoam"); W(src,outn,ex,"PFoam"); var sp=Add("Separate PFEdges By Type"); W(ex,"PFEdges",sp,"PFEdge"); var ie=Add("Inspect PFEdge"); W(sp,"Internal",ie,"PFEdge");
 var iff=Add("Inspect PFFace"); W(ie,"Dual",iff,"PFFace"); var iv=Add("Inspect PFVertex"); W(ex,"PFVertices",iv,"PFVertex");
 var t0=sw.ElapsedMilliseconds; Solve(); var tms=sw.ElapsedMilliseconds-t0;
 var F=D(ie,"Force").Select(x=>Convert.ToDouble(x)).ToList(); var L=D(ie,"Line").Cast<Line>().ToList(); var PL=D(iff,"Plane").Cast<Plane>().ToList();
 var dev=new List<double>(); for(int i=0;i<L.Count&&i<PL.Count;i++){ var a=Vector3d.VectorAngle(L[i].Direction,PL[i].Normal)*180/Math.PI; dev.Add(Math.Min(a,180-a)); }
 var lean=L.Select(l=>{var v=l.Direction; return Math.Atan2(Math.Sqrt(v.X*v.X+v.Y*v.Y),Math.Abs(v.Z))*180/Math.PI;}).ToList(); var ring=lean.Count(a=>a>89.5)/2; var inpl=L.Select(l=>{ var m=l.PointAt(0.5); var rad=new Vector3d(m.X,m.Y,0); var v=new Vector3d(l.Direction.X,l.Direction.Y,0); if(rad.Length<1||v.Length<1e-6) return 0.0; var a=Vector3d.VectorAngle(rad,v)*180/Math.PI; return Math.Min(a,180-a); }).ToList(); var inplB=inpl.Where((a,ii)=>lean[ii]<=89.5).ToList(); var br=lean.Where(a=>a<=89.5).ToList();
 var P=D(iv,"Point").Cast<Point3d>().ToList(); var VID=D(iv,"ID").Select(x=>Convert.ToInt32(x)).ToList(); var X=D(iv,"External").Select(x=>(bool)x).ToList();
 var ids=D(lid,"Item").Select(x=>Convert.ToInt32(x)).ToList();
 var feet=ids.Select(id=>{int j=VID.IndexOf(id); return j>=0?P[j]:Point3d.Unset;}).ToList();
 var off=feet.Select(p=>{ double t; wc.ClosestPoint(p,out t); return p.DistanceTo(wc.PointAt(t)); }).ToList();
 var ip=P.Where((p,i)=>!X[i]).ToList();
 return tag+" ms "+tms+" bars "+F.Count/2+" T "+F.Count(f=>f<-1e-9)/2+" apex "+ip.Max(p=>p.Z).ToString("0")+" | branches "+br.Count/2+" over35 "+br.Count(a=>a>35)/2+" maxlean "+br.DefaultIfEmpty(0).Max().ToString("0.0")+" ring "+ring+" gt80 "+lean.Count(a=>a>80)/2+" 60to80 "+lean.Count(a=>a>60&&a<=80)/2+" 35to60 "+lean.Count(a=>a>35&&a<=60)/2+" le35 "+lean.Count(a=>a<=35)/2+" | in-plan off fall line: over35 "+inplB.Count(a=>a>35)/2+" max "+inplB.DefaultIfEmpty(0).Max().ToString("0.0")+" | dev max "+dev.DefaultIfEmpty(0).Max().ToString("0.00")+" mean "+dev.DefaultIfEmpty(0).Average().ToString("0.00")+" | foot-to-wall max "+off.Max().ToString("0")+" mean "+off.Average().ToString("0")+" mm | feet "+string.Join(" ",feet.Select(p=>"("+(p.X/1000).ToString("0.00")+","+(p.Y/1000).ToString("0.00")+","+(p.Z/1000).ToString("0.00")+")"));
}
sb.AppendLine("tets "+g.tets.Count); foreach(var c in doc.Objects.OfType<IGH_Component>()) if(c.RuntimeMessageLevel==GH_RuntimeMessageLevel.Error) sb.AppendLine("ERR "+Msg(c));
Solve(); foreach(var c in doc.Objects.OfType<IGH_Component>()) if(c.RuntimeMessageLevel!=GH_RuntimeMessageLevel.Blank) sb.AppendLine("MSG "+Msg(c)); try{ sb.AppendLine(Stats(vc,"PFoam","A")); }catch(Exception e){ sb.AppendLine("statsA fail "+e.Message); Console.WriteLine(sb.ToString()); return; }
sb.AppendLine(Stats(perp,"PFoam","B"));
if(SHOW){ foreach(var o in doc.Objects.OfType<IGH_ActiveObject>()) if(o is IGH_PreviewObject po) po.Hidden=true;
var pA=Add("PFPipe"); W(vc,"PFoam",pA,"PFoam"); Num(pA,"MinR",30); Num(pA,"MaxR",90); ((IGH_PreviewObject)pA).Hidden=true;
var mA=Add("Move"); W(pA,"Pipe",mA,"Geometry"); var vx=(Param_Vector)In(mA,"Motion"); vx.PersistentData.Clear(); vx.PersistentData.Append(new GH_Vector(new Vector3d(-14000,0,0)));
var cA=Add("Custom Preview"); W(mA,"Geometry",cA,"Geometry"); W(pA,"Color",cA,"Material");
var pB=Add("PFPipe"); W(perp,"PFoam",pB,"PFoam"); Num(pB,"MinR",30); Num(pB,"MaxR",90); ((IGH_PreviewObject)pB).Hidden=true;
var cB=Add("Custom Preview"); W(pB,"Pipe",cB,"Geometry"); W(pB,"Color",cB,"Material");
var old=Instances.ActiveCanvas.Document; Instances.DocumentServer.AddDocument(doc); Instances.ActiveCanvas.Document=doc; if(old!=null){ old.Enabled=false; Instances.DocumentServer.RemoveDocument(old); old.Dispose(); }
doc.NewSolution(false); }

Console.WriteLine(sb.ToString());
