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

const string MUL="ce46b74e-00c9-43c4-805a-193b69ea4a11", SUB="9c007a04-d0d9-48e4-9da3-9ba142bc4d46";
// ================= Cluster 1: force diagram presets (GUESS, internalized like PF example 3(7)) =================
var d1=new GH_Document(); cur=d1;
var hP=HIn("Preset",0); var hZ=HIn("Force depth",100);
var presets=new[]{(4,3),(5,3),(6,3)};
var pb=new Param_Brep(); pb.CreateAttributes(); pb.NickName="Cells (presets)"; pb.Attributes.Pivot=new PointF(200,0); d1.AddObject(pb,false);
var pt=new Param_Point(); pt.CreateAttributes(); pt.NickName="Reaction cell centroids"; pt.Attributes.Pivot=new PointF(200,100); d1.AddObject(pt,false);
for(int i=0;i<presets.Length;i++){ var gg=GenDiamond2(presets[i].Item1,presets[i].Item2,1000,1,8,0.5); var path=new Grasshopper.Kernel.Data.GH_Path(i); foreach(var t in gg.tets) pb.PersistentData.Append(new GH_Brep(t),path); foreach(var q in gg.targets) pt.PersistentData.Append(new GH_Point(q),path); }
var tb1=Add("Tree Branch",400,0); In(tb1,"Tree").AddSource(pb); In(tb1,"Path").AddSource(hP);
var tb2=Add("Tree Branch",400,100); In(tb2,"Tree").AddSource(pt); In(tb2,"Path").AddSource(hP);
var sn1=Add("Scale NU",600,0); W(tb1,"Branch",sn1,"Geometry"); Pl(sn1,"Plane",Plane.WorldXY); Num(sn1,"Scale X",1); Num(sn1,"Scale Y",1); In(sn1,"Scale Z").AddSource(hZ);
var sn2=Add("Scale NU",600,100); W(tb2,"Branch",sn2,"Geometry"); Pl(sn2,"Plane",Plane.WorldXY); Num(sn2,"Scale X",1); Num(sn2,"Scale Y",1); In(sn2,"Scale Z").AddSource(hZ);
HOut("Force cells",Out(sn1,"Geometry"),0); HOut("Support targets",Out(sn2,"Geometry"),100);

// ================= Cluster 1b: plan, wall, reference =================
var d1b=new GH_Document(); cur=d1b;
var hS=HIn("Plan side",0); var hR=HIn("Ref apex",100);
var hs=Add("Division",200,0); In(hs,"A").AddSource(hS); Num(hs,"B",-2);
var org=Add("Construct Point",350,0); W(hs,"Result",org,"X coordinate"); W(hs,"Result",org,"Y coordinate"); Num(org,"Z coordinate",0);
var wall=Add("Rectangle",500,0); W(org,"Point",wall,"Plane"); In(wall,"X Size").AddSource(hS); In(wall,"Y Size").AddSource(hS);
var dv=Add("Divide Curve",650,0); W(wall,"Rectangle",dv,"Curve"); Int(dv,"Count",8);
var cpc=Add("Cull Pattern",800,60); W(dv,"Points",cpc,"List"); var pq=(Param_Boolean)In(cpc,"Cull Pattern"); pq.PersistentData.Clear(); pq.PersistentData.Append(new GH_Boolean(true)); pq.PersistentData.Append(new GH_Boolean(false));
var dup=Add("Duplicate Data",800,140); W(wall,"Rectangle",dup,"Data"); Int(dup,"Number",8); Bool(dup,"Order",true);
var mo=AddG(MUL,350,220); In(mo,"A").AddSource(hS); Num(mo,"B",-1.4); var ux=Add("Unit X",500,220); W(mo,"Result",ux,"Factor");
var pl=Add("PolyLine",650,300); W(cpc,"List",pl,"Vertices"); Bool(pl,"Closed",true);
var rbs=Add("Boundary Surfaces",800,300); W(pl,"Polyline",rbs,"Edges");
var rpt=Add("Construct Point",800,400); Num(rpt,"X coordinate",0); Num(rpt,"Y coordinate",0); In(rpt,"Z coordinate").AddSource(hR);
var rep=Add("Extrude Point",950,300); W(rbs,"Surfaces",rep,"Base"); W(rpt,"Point",rep,"Point");
HOut("Corner points",Out(cpc,"List"),0); HOut("Wall line x8",Out(dup,"Data"),100); HOut("Wall line",Out(wall,"Rectangle"),200); HOut("Stage A offset",Out(ux,"Unit vector"),300); HOut("Reference pyramid",Out(rep,"Extrusion"),400);
// ================= Cluster 2: support vertex IDs =================
var d2=new GH_Document(); cur=d2;
var hF=HIn("Force PFoam",0); var hT=HIn("Support targets",100);
var exf=Add("Explode PFoam",200,0); In(exf,"PFoam").AddSource(hF);
var ipc=Add("Inspect PFCell",400,0); W(exf,"PFCells",ipc,"PFCell");
var cps=Add("Closest Points",600,100); In(cps,"Point").AddSource(hT); W(ipc,"Centroid",cps,"Cloud"); Int(cps,"Count",1);
var lid=Add("List Item",800,0); W(ipc,"ID",lid,"List"); W(cps,"CP Index",lid,"Index"); In(lid,"Index").DataMapping=GH_DataMapping.Flatten;
HOut("Support IDs",Out(lid,"Item"),0);

GH_Document ColourDoc(){ var d3=new GH_Document(); cur=d3;
 var hV=HIn("Forces",0);
 var bnd=Add("Bounds",200,0); In(bnd,"Numbers").AddSource(hV);
 var rmp=Add("Remap Numbers",400,0); In(rmp,"Value").AddSource(hV); W(bnd,"Domain",rmp,"Source");
 var gproxy=Instances.ComponentServer.ObjectProxies.First(q=>q.Desc.Name=="Gradient" && !q.Obsolete && typeof(GH_GradientControl).IsAssignableFrom(q.Type));
 var grad=(GH_GradientControl)gproxy.CreateInstance(); grad.CreateAttributes(); grad.Attributes.Pivot=new PointF(600,0); d3.AddObject(grad,false);
 var g=new Grasshopper.GUI.Gradient.GH_Gradient(); g.AddGrip(0.0,Color.FromArgb(40,90,220)); g.AddGrip(0.5,Color.FromArgb(150,90,200)); g.AddGrip(1.0,Color.FromArgb(220,40,40)); grad.Gradient=g;
 grad.Params.Input[2].AddSource(Out(rmp,"Mapped"));
 ((Param_Number)grad.Params.Input[0]).PersistentData.Clear(); ((Param_Number)grad.Params.Input[0]).PersistentData.Append(new GH_Number(0)); ((Param_Number)grad.Params.Input[1]).PersistentData.Clear(); ((Param_Number)grad.Params.Input[1]).PersistentData.Append(new GH_Number(1));
 HOut("Colours",grad.Params.Output[0],0); return d3; }

// ================= Cluster 4 (built twice): checks =================
GH_Document CheckDoc(){ var d4=new GH_Document(); cur=d4;
 var hP=HIn("Form PFoam",0); var hI=HIn("Support IDs",100); var hW=HIn("Wall line",200);
 var ex4=Add("Explode PFoam",200,0); In(ex4,"PFoam").AddSource(hP);
 var sep=Add("Separate PFEdges By Type",400,0); W(ex4,"PFEdges",sep,"PFEdge");
 var ie4=Add("Inspect PFEdge",600,0); W(sep,"Internal",ie4,"PFEdge");
 var bnF=Add("Bounds",800,-100); W(ie4,"Force",bnF,"Numbers");
 // deviation = angle between each bar and the normal of its dual force face, folded to 0..90
 var enp=Add("End Points",800,0); W(ie4,"Line",enp,"Curve");
 var v2=Add("Vector 2Pt",950,0); W(enp,"Start",v2,"Point A"); W(enp,"End",v2,"Point B");
 var iff=Add("Inspect PFFace",800,100); W(ie4,"Dual",iff,"PFFace");
 var dpl=Add("Deconstruct Plane",950,100); W(iff,"Plane",dpl,"Plane");
 var ang=Add("Angle",1100,50); W(v2,"Vector",ang,"Vector A"); W(dpl,"Z-Axis",ang,"Vector B");
 var deg=Add("Degrees",1250,50); W(ang,"Angle",deg,"Radians");
 var s1=AddG(SUB,1400,50); W(deg,"Degrees",s1,"A"); Num(s1,"B",90);
 var ab=Add("Absolute",1550,50); W(s1,"Result",ab,"Value");
 var s2=AddG(SUB,1700,50); Num(s2,"A",90); W(ab,"Result",s2,"B");
 var bnD=Add("Bounds",1850,0); W(s2,"Result",bnD,"Numbers");
 var avD=Add("Average",1850,100); W(s2,"Result",avD,"Input");
 // feet: distance of the 8 support vertices to the wall line
 var iv4=Add("Inspect PFVertex",400,250); W(ex4,"PFVertices",iv4,"PFVertex");
 var mi=Add("Member Index",600,250); W(iv4,"ID",mi,"Set"); In(mi,"Member").AddSource(hI);
 var lpt=Add("List Item",800,250); W(iv4,"Point",lpt,"List"); W(mi,"Index",lpt,"Index"); In(lpt,"Index").DataMapping=GH_DataMapping.Flatten;
 var ccp=Add("Curve Closest Point",950,250); W(lpt,"Item",ccp,"Point"); In(ccp,"Curve").AddSource(hW);
 var bnW=Add("Bounds",1100,250); W(ccp,"Distance",bnW,"Numbers");
 var avW=Add("Average",1100,350); W(ccp,"Distance",avW,"Input");
 HOut("Bar force range",Out(bnF,"Domain"),0); HOut("Deviation range (deg)",Out(bnD,"Domain"),100); HOut("Mean deviation (deg)",Out(avD,"Arithmetic mean"),200); HOut("Foot-to-wall range (mm)",Out(bnW,"Domain"),300); HOut("Mean foot-to-wall (mm)",Out(avW,"Arithmetic mean"),400);
 return d4; }

// ================= main document =================
var doc=new GH_Document(); cur=doc;
GH_NumberSlider Sl(string name,double min,double max,double val,int dec,float x,float y){ var s=new GH_NumberSlider(); s.CreateAttributes(); s.NickName=name; s.Slider.Minimum=(decimal)min; s.Slider.Maximum=(decimal)max; s.Slider.DecimalPlaces=dec; s.Slider.Type= dec==0? Grasshopper.GUI.Base.GH_SliderAccuracy.Integer : Grasshopper.GUI.Base.GH_SliderAccuracy.Float; s.SetSliderValue((decimal)val); s.Attributes.Pivot=new PointF(x,y); doc.AddObject(s,false); return s; }
var vl=new GH_ValueList(); vl.CreateAttributes(); vl.NickName="Branching preset (GUESS)"; vl.ListItems.Clear(); foreach(var kv in new[]{("4 rings","0"),("5 rings","1"),("6 rings","2")}) vl.ListItems.Add(new GH_ValueListItem(kv.Item1,kv.Item2)); vl.SelectItem(1); vl.Attributes.Pivot=new PointF(60,100); doc.AddObject(vl,false);
var sD=Sl("Force depth (Scale Z)",0.3,1.5,0.68,3,60,200); var sS=Sl("Plan side (mm)",4000,16000,10000,0,60,250); var sR=Sl("Ref apex (mm)",1000,12000,6670,0,60,300);
var sIt=Sl("PFPerp iterations",0,3000,300,0,1060,420); var sCo=Sl("Pull strength",0,100,10,1,1060,470);
var c1=MakeCluster(d1,doc,"Force diagram presets (GUESS)","GUESSED force diagrams (not the friend's): regular octagon cap, diamond (diagrid) cells between half-offset circular rings, crown = one polygon cell (hub node), outer band built by hand mirrored about each foot, joined to one point below; internalized like PF example 3(7). Scale Z = cone depth.",380,140);
CIn(c1,"Preset").AddSource(vl); CIn(c1,"Force depth").AddSource(sD);
var c1b=MakeCluster(d1b,doc,"Plan + wall + reference","Wall points/line of the square plan, 4 corner points, grey 53.1 deg reference pyramid",380,300);
CIn(c1b,"Plan side").AddSource(sS); CIn(c1b,"Ref apex").AddSource(sR);
var bld=Add("PFBuild",640,110); In(bld,"Brep").AddSource(COut(c1,"Force cells")); Num(bld,"Absolute Tolerance",0.1); Num(bld,"Planarity Tolerance",0.1); Hide(bld);
var c2=MakeCluster(d2,doc,"Support IDs","Form vertices (= force cells) carrying the 8 reactions, in wall order: corner, mid, corner, ...",840,210);
CIn(c2,"Force PFoam").AddSource(Out(bld,"Force PFoam")); CIn(c2,"Support targets").AddSource(COut(c1,"Support targets"));
var ad=Add("Algebraic Dual",840,90); W(bld,"Force PFoam",ad,"Force PFoam"); Num(ad,"Scale",1); Bool(ad,"Flip",false); Hide(ad);
var vc=Add("Algebraic Vertex Constraints",1080,150); W(ad,"Algebraic Form",vc,"Algebraic Form"); var cid=Add("Cull Pattern",960,240); In(cid,"List").AddSource(COut(c2,"Support IDs")); In(cid,"List").DataMapping=GH_DataMapping.Flatten; var pq2=(Param_Boolean)In(cid,"Cull Pattern"); pq2.PersistentData.Clear(); pq2.PersistentData.Append(new GH_Boolean(true)); pq2.PersistentData.Append(new GH_Boolean(false));
W(cid,"List",vc,"PFVertex IDs"); In(vc,"Constraints").AddSource(COut(c1b,"Corner points")); Num(vc,"Scale",1); Hide(vc);
// stage A display (moved left)
var ppA=Add("PFPipe",1340,40); W(vc,"PFoam",ppA,"PFoam"); Num(ppA,"MinR",40); Num(ppA,"MaxR",120); Hide(ppA);
var cA=MakeCluster(ColourDoc(),doc,"Colour by force","Blue = low compression, red = high (PFPipe force magnitude)",1540,90); cur=doc; CIn(cA,"Forces").AddSource(Out(ppA,"Force"));
var mvA=Add("Move",1540,10); W(ppA,"Pipe",mvA,"Geometry"); In(mvA,"Motion").AddSource(COut(c1b,"Stage A offset")); Hide(mvA);
var cpA=Add("Custom Preview",1740,40); W(mvA,"Geometry",cpA,"Geometry"); In(cpA,"Material").AddSource(COut(cA,"Colours"));
var kA=MakeCluster(CheckDoc(),doc,"Check","Bar force range (+ = compression), deviation of bars from their force faces, distance of the 8 feet to the wall line",1340,200); cur=doc;
CIn(kA,"Form PFoam").AddSource(Out(vc,"PFoam")); CIn(kA,"Support IDs").AddSource(COut(c2,"Support IDs")); CIn(kA,"Wall line").AddSource(COut(c1b,"Wall line"));
// stage B
var pvc=Add("PFVertex Constraints",1300,440); W(vc,"PFoam",pvc,"PFoam"); In(pvc,"PFVertex ID").AddSource(COut(c2,"Support IDs")); In(pvc,"Constraint").AddSource(COut(c1b,"Wall line x8")); In(pvc,"Coefficient").AddSource(sCo); Bool(pvc,"On",true); Hide(pvc);
var perp=Add("PFPerp",1500,440); W(pvc,"PFoam",perp,"PFoam"); In(perp,"Max Iteration").AddSource(sIt); Num(perp,"Deviation",0.1); Num(perp,"Minimum Edge Length",10); Hide(perp);
var ppB=Add("PFPipe",1700,420); W(perp,"PFoam",ppB,"PFoam"); Num(ppB,"MinR",40); Num(ppB,"MaxR",120); Hide(ppB);
var cB=MakeCluster(ColourDoc(),doc,"Colour by force","Blue = low compression, red = high (PFPipe force magnitude)",1900,470); cur=doc; CIn(cB,"Forces").AddSource(Out(ppB,"Force"));
var cpB=Add("Custom Preview",2100,420); W(ppB,"Pipe",cpB,"Geometry"); In(cpB,"Material").AddSource(COut(cB,"Colours"));
var kB=MakeCluster(CheckDoc(),doc,"Check","Bar force range (+ = compression), deviation of bars from their force faces, distance of the 8 feet to the wall line",1700,580); cur=doc;
CIn(kB,"Form PFoam").AddSource(Out(perp,"PFoam")); CIn(kB,"Support IDs").AddSource(COut(c2,"Support IDs")); CIn(kB,"Wall line").AddSource(COut(c1b,"Wall line"));
GH_Panel Pan(string name,GH_Cluster k,float x,float y){ var pan=new GH_Panel(); pan.CreateAttributes(); pan.NickName=name; pan.Attributes.Pivot=new PointF(x,y); pan.Attributes.Bounds=new RectangleF(x,y,300,150); foreach(var o in k.Params.Output) pan.AddSource(o); doc.AddObject(pan,false); return pan; }
var pA=Pan("Stage A: forces | dev range | mean dev | feet-to-wall range | mean",kA,1560,170);
var pB=Pan("Stage B: forces | dev range | mean dev | feet-to-wall range | mean",kB,1920,560);
var swp=Instances.ComponentServer.ObjectProxies.First(q=>q.Desc.Name=="Colour Swatch" && !q.Obsolete);
var swo=(IGH_Param)swp.CreateInstance(); swo.CreateAttributes(); swo.Attributes.Pivot=new PointF(1940,760); doc.AddObject(swo,false);
var swProp=swo.GetType().GetProperty("SwatchColour"); if(swProp!=null) swProp.SetValue(swo,Color.FromArgb(70,150,150,150));
var cpr=Add("Custom Preview",2100,760); In(cpr,"Geometry").AddSource(COut(c1b,"Reference pyramid")); In(cpr,"Material").AddSource(swo);
Hide(c1); Hide(c1b); Hide(c2); Hide(kA); Hide(kB);
GH_Group Grp(string name,Color col,params IGH_DocumentObject[] objs){ var gr=new GH_Group(); gr.CreateAttributes(); gr.NickName=name; gr.Colour=col; foreach(var o in objs) gr.AddObject(o.InstanceGuid); doc.AddObject(gr,false); return gr; }
Grp("1  Play here",Color.FromArgb(120,255,230,150),vl,sD,sS,sR);
Grp("2  Force diagram - GUESS diagrid, mirror-symmetric (PolyFrame build)",Color.FromArgb(80,170,200,255),c1,c1b,bld,c2);
Grp("3  Stage A - exact algebraic, 4 corners pinned (shown left)",Color.FromArgb(80,170,255,180),ad,cid,vc,ppA,cA,mvA,cpA,kA,pA);
Grp("4  Stage B - pull 8 feet onto wall line, PFPerp",Color.FromArgb(80,255,200,170),sIt,sCo,pvc,perp,ppB,cB,cpB,kB,pB,swo,cpr);
var old=Instances.ActiveCanvas.Document; Instances.DocumentServer.AddDocument(doc); Instances.ActiveCanvas.Document=doc; if(old!=null){ old.Enabled=false; Instances.DocumentServer.RemoveDocument(old); old.Dispose(); }
var swt=System.Diagnostics.Stopwatch.StartNew(); doc.Enabled=true; doc.NewSolution(false); sb.AppendLine("solve ms "+swt.ElapsedMilliseconds);
foreach(var o in doc.Objects.OfType<IGH_ActiveObject>()) if(o.RuntimeMessageLevel!=GH_RuntimeMessageLevel.Blank) sb.AppendLine("msg "+o.NickName+": "+o.RuntimeMessageLevel+" "+string.Join(" | ",o.RuntimeMessages(GH_RuntimeMessageLevel.Error).Concat(o.RuntimeMessages(GH_RuntimeMessageLevel.Warning))));
sb.AppendLine("IDs "+string.Join(" ",COut(c2,"Support IDs").VolatileData.AllData(true)));
foreach(var k in new[]{kA,kB}) sb.AppendLine("check: "+string.Join(" | ",k.Params.Output.Select(o=>string.Join(" ",o.VolatileData.AllData(true)))));
sb.AppendLine("pipes A "+Out(ppA,"Pipe").VolatileData.DataCount+" B "+Out(ppB,"Pipe").VolatileData.DataCount+" objs "+doc.ObjectCount);
Console.WriteLine(sb.ToString());
