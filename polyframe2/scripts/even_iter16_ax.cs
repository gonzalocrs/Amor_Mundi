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

(List<Brep> tets, List<Point3d> targets, List<Polyline> tris) GenDiamond3(int R,int m,double depth,double Q,int NV,double[] FR){
 Point3d[] V;
 if(NV==8){ double b=1000*Math.Cos(Math.PI/8), a=Q*b*(1+Math.Tan(Math.PI/8)); V=new[]{new Point3d(-b,-a+b,0),new Point3d(-a+b,-b,0),new Point3d(a-b,-b,0),new Point3d(b,-a+b,0),new Point3d(b,a-b,0),new Point3d(a-b,b,0),new Point3d(-a+b,b,0),new Point3d(-b,a-b,0)}; }
 else { double st=2*Math.PI/NV, a0=-135*Math.PI/180-st/2; V=Enumerable.Range(0,NV).Select(k=>new Point3d(1000*Math.Cos(a0+k*st),1000*Math.Sin(a0+k*st),0)).ToArray(); }
 var C=Point3d.Origin; var apex=new Point3d(0,0,-depth); int n=NV*m;
 double O(int r)=>((R-r)%2==0)?0.5:0.0;
 Point3d P(int r,int i){ i=((i%n)+n)%n; double s=(i+O(r))/m; int k=(int)Math.Floor(s); double fr=s-k; k%=NV; var A=V[k]; var B=V[(k+1)%NV]; double f=FR[r-1]; var pp=C+((A+(B-A)*fr)-C)*f; if(r<R){ var dir=pp-C; dir.Unitize(); pp=C+dir*(1000*Math.Cos(Math.PI/NV)*f); } return pp; }
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

(List<Brep> tets, List<Point3d> targets, List<Polyline> tris) GenDiamond4(int R,int m,double depth,double Q,int NV,double[] FR,double[] PS){
 Point3d[] V;
 if(NV==8){ double b=1000*Math.Cos(Math.PI/8), a=Q*b*(1+Math.Tan(Math.PI/8)); V=new[]{new Point3d(-b,-a+b,0),new Point3d(-a+b,-b,0),new Point3d(a-b,-b,0),new Point3d(b,-a+b,0),new Point3d(b,a-b,0),new Point3d(a-b,b,0),new Point3d(-a+b,b,0),new Point3d(-b,a-b,0)}; }
 else { double st=2*Math.PI/NV, a0=-135*Math.PI/180-st/2; V=Enumerable.Range(0,NV).Select(k=>new Point3d(1000*Math.Cos(a0+k*st),1000*Math.Sin(a0+k*st),0)).ToArray(); }
 var C=Point3d.Origin; var apex=new Point3d(0,0,-depth); int n=NV*m;
 double O(int r)=>((R-r)%2==0)?0.5:0.0;
 Point3d P(int r,int i){ i=((i%n)+n)%n; double s=(i+O(r))/m; int k=(int)Math.Floor(s); double fr=s-k; k%=NV; var A=V[k]; var B=V[(k+1)%NV]; double f=FR[r-1]; var pp=C+((A+(B-A)*fr)-C)*f; if(r<R){ var dir=pp-C; dir.Unitize(); double th=Math.Atan2(dir.Y,dir.X); double p=PS[r-1]; double se=1.0/Math.Pow(Math.Pow(Math.Abs(Math.Cos(th)),p)+Math.Pow(Math.Abs(Math.Sin(th)),p),1.0/p); pp=C+dir*(1000*Math.Cos(Math.PI/NV)*f*se); } return pp; }
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

(List<Brep> tets, List<Point3d> targets, List<Polyline> tris) GenDiamond5(int R,int m,double depth,double Q,int NV,double[] FR){
 Point3d[] V;
 if(NV==8){ double b=1000*Math.Cos(Math.PI/8), a=Q*b*(1+Math.Tan(Math.PI/8)); V=new[]{new Point3d(-b,-a+b,0),new Point3d(-a+b,-b,0),new Point3d(a-b,-b,0),new Point3d(b,-a+b,0),new Point3d(b,a-b,0),new Point3d(a-b,b,0),new Point3d(-a+b,b,0),new Point3d(-b,a-b,0)}; }
 else { double st=2*Math.PI/NV, a0=-135*Math.PI/180-st/2; V=Enumerable.Range(0,NV).Select(k=>new Point3d(1000*Math.Cos(a0+k*st),1000*Math.Sin(a0+k*st),0)).ToArray(); }
 var C=Point3d.Origin; var apex=new Point3d(0,0,-depth); int n=NV*m;
 double O(int r)=>((R-r)%2==0)?0.5:0.0;
 Point3d P(int r,int i){ i=((i%n)+n)%n; double s=(i+O(r))/m; int k=(int)Math.Floor(s); double fr=s-k; k%=NV; var A=V[k]; var B=V[(k+1)%NV]; double f=FR[r-1]; var pp=C+((A+(B-A)*fr)-C)*f; if(r<R){ var dir=pp-C; dir.Unitize(); pp=C+dir*(1000*Math.Cos(Math.PI/NV)*f); } return pp; }
 var polys=new List<Polyline>(); Polyline T(params Point3d[] p){ var l=p.ToList(); l.Add(p[0]); return new Polyline(l); }
 for(int i=0;i<n;i++) polys.Add(T(C,P(1,i),P(1,i+1)));   // open crown: fan -> one horizontal crown ring in the form
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


double[] FR=new double[]{0.3725,0.4525,0.5438,0.7723}; double DEP=376; int RR=FR.Length, MM=1; int NVV=16;
var g=GenDiamond5(RR,MM,DEP,1,NVV,FR);
var bp=new Param_Brep(); bp.CreateAttributes(); doc.AddObject(bp,false); foreach(var t in g.tets) bp.PersistentData.Append(new GH_Brep(t));
var bld=Add("PFBuild"); bld.Params.Input[0].AddSource(bp); Num(bld,"Absolute Tolerance",0.1); Num(bld,"Planarity Tolerance",0.1);
var exf=Add("Explode PFoam"); W(bld,"Force PFoam",exf,"PFoam"); var ipc=Add("Inspect PFCell"); W(exf,"PFCells",ipc,"PFCell");
var ad=Add("Algebraic Dual"); W(bld,"Force PFoam",ad,"Force PFoam"); Num(ad,"Scale",1); Bool(ad,"Flip",false);
Solve();
var cid=D(ipc,"ID").Select(x=>Convert.ToInt32(x)).ToList(); var ccen=D(ipc,"Centroid").Cast<Point3d>().ToList();
int CellOf(Point3d c){ int best=-1; double bd=1e18; for(int i=0;i<ccen.Count;i++){ double dd=ccen[i].DistanceTo(c); if(dd<bd){bd=dd;best=i;} } return cid[best]; }
var apex=new Point3d(0,0,-DEP);
Point3d PyrCentroid(Polyline pl){ var pts=pl.Take(pl.Count-1).ToList(); if(pts.Count==3) return new Point3d((pts[0].X+pts[1].X+pts[2].X+apex.X)/4,(pts[0].Y+pts[1].Y+pts[2].Y+apex.Y)/4,(pts[0].Z+pts[1].Z+pts[2].Z+apex.Z)/4); var c=AreaMassProperties.Compute(new PolylineCurve(pl)).Centroid; return c+(apex-c)*0.25; }
var polys=g.tris; var cellIds=polys.Select(p=>CellOf(PyrCentroid(p))).ToList();
var capA=polys.Select(p=>AreaMassProperties.Compute(new PolylineCurve(p)).Area).ToList();
var supIds=g.targets.Select(t=>CellOf(t)).ToList();
var wcl=new PolylineCurve(new[]{new Point3d(-5000,-5000,0),new Point3d(5000,-5000,0),new Point3d(5000,5000,0),new Point3d(-5000,5000,0),new Point3d(-5000,-5000,0)}); var wall=wcl.DivideByCount(NVV,true).Select(tt=>wcl.PointAt(tt)).ToArray();
var vc=Add("Algebraic Vertex Constraints"); W(ad,"Algebraic Form",vc,"Algebraic Form"); Ints(vc,"PFVertex IDs",new[]{supIds[0],supIds[4],supIds[8],supIds[12]}); Geo(vc,"Constraints",new[]{wall[0],wall[4],wall[8],wall[12]}); Num(vc,"Scale",1);
var wc=wcl;
var pvc=Add("PFVertex Constraints"); W(vc,"PFoam",pvc,"PFoam"); Ints(pvc,"PFVertex ID",supIds); var cg=(Param_Geometry)In(pvc,"Constraint"); cg.PersistentData.Clear(); for(int k=0;k<NVV;k++) cg.PersistentData.Append(new GH_Curve(wc)); Num(pvc,"Coefficient",10); Bool(pvc,"On",true);
var perp=Add("PFPerp"); W(pvc,"PFoam",perp,"PFoam"); Int(perp,"Max Iteration",300); Num(perp,"Deviation",0.1); Num(perp,"Minimum Edge Length",10);
var ex=Add("Explode PFoam"); W(perp,"PFoam",ex,"PFoam"); var iv=Add("Inspect PFVertex"); W(ex,"PFVertices",iv,"PFVertex"); var ie=Add("Inspect PFEdge"); W(ex,"PFEdges",ie,"PFEdge");
Solve();
var vid=D(iv,"ID").Select(x=>Convert.ToInt32(x)).ToList(); var vpt=D(iv,"Point").Cast<Point3d>().ToList(); var vext=D(iv,"External").Select(x=>(bool)x).ToList();
var pos=new Dictionary<int,Point3d>(); for(int i=0;i<vid.Count;i++) if(!vext[i]) pos[vid[i]]=vpt[i];
var F=D(ie,"Force").Select(x=>Convert.ToDouble(x)).ToList(); var X=D(ie,"External").Select(x=>Convert.ToInt32(x)).ToList(); int T=0; for(int i=0;i<F.Count;i++) if(X[i]==0&&F[i]<-1e-9) T++;
double apexZ=pos.Values.Max(p=>p.Z);
// plan Voronoi tributary area (10x10 plan, 50 mm grid) for every form node that is a cell dual
var nodeIds=cellIds.Distinct().Where(id=>pos.ContainsKey(id)).ToList(); var np=nodeIds.Select(id=>pos[id]).ToList(); var trib=new double[np.Count];
for(double x=-4975;x<5000;x+=50) for(double y=-4975;y<5000;y+=50){ int best=0; double bd=1e18; for(int k=0;k<np.Count;k++){ double dx=np[k].X-x, dy=np[k].Y-y, dd=dx*dx+dy*dy; if(dd<bd){bd=dd;best=k;} } trib[best]+=2500; }
var tribOf=new Dictionary<int,double>(); for(int k=0;k<np.Count;k++) tribOf[nodeIds[k]]=trib[k];
// annulus of each cap polygon: compare its centroid radius with the ring radii (rings are circles r=1000cos(pi/8)f; last ring on the octagon)
double Rad(int r)=> 1000*Math.Cos(Math.PI/8)*FR[r-1];
var ann=new int[polys.Count]; for(int i=0;i<polys.Count;i++){ var c=AreaMassProperties.Compute(new PolylineCurve(polys[i])).Centroid; double rc=Math.Sqrt(c.X*c.X+c.Y*c.Y); int k=0; while(k<RR && rc>Rad(k+1)) k++; ann[i]=k; }
var Tk=new double[RR+1]; var Ak=new double[RR+1]; for(int i=0;i<polys.Count;i++){ Ak[ann[i]]+=capA[i]; if(tribOf.ContainsKey(cellIds[i])) Tk[ann[i]]+=tribOf[cellIds[i]]; }
double sT=Tk.Sum(), sA=Ak.Sum();
// mismatch per node: (trib share) / (design share)
var ratios=new List<double>(); for(int i=0;i<polys.Count;i++){ if(!tribOf.ContainsKey(cellIds[i])) continue; if(supIds.Contains(cellIds[i])) continue; ratios.Add((tribOf[cellIds[i]]/sT)/(capA[i]/sA)); }
ratios.Sort();
// update: cumulative target fraction inside ring k -> new radius (area within a scaled octagon ~ f^2)
var cum=0.0; var newFR=new double[RR]; for(int k=0;k<RR;k++){ cum+=Tk[k]/sT; newFR[k]=Math.Sqrt(Math.Max(cum,1e-4)); }
for(int k=0;k<RR;k++) newFR[k]=0.5*FR[k]+0.5*newFR[k];   // damped
for(int k=1;k<RR;k++) newFR[k]=Math.Max(newFR[k],newFR[k-1]+0.08); newFR[RR-1]=Math.Min(newFR[RR-1],0.97);
double newDep=DEP*apexZ/6670.0;
var dev=D(perp,"Deviation").FirstOrDefault();
Console.WriteLine("FR "+string.Join(",",FR.Select(v=>v.ToString("0.000")))+" dep "+DEP.ToString("0")+" | apex "+apexZ.ToString("0")+" | tension "+T/2+" | stageB dev "+dev+" | node ratio min "+ratios.First().ToString("0.00")+" median "+ratios[ratios.Count/2].ToString("0.00")+" max "+ratios.Last().ToString("0.00")+" off>2x "+ratios.Count(r=>r>2||r<0.5)+"/"+ratios.Count);
Console.WriteLine("  annulus design share: "+string.Join(" ",Ak.Select(a=>(a/sA).ToString("0.00")))+" | trib share: "+string.Join(" ",Tk.Select(a=>(a/sT).ToString("0.00"))));
var LL=D(ie,"Line").Cast<Line>().ToList(); var lean=new List<double>(); var ringR=new List<double>(); for(int i=0;i<LL.Count;i++) if(X[i]==0){ var v=LL[i].Direction; lean.Add(Math.Atan2(Math.Sqrt(v.X*v.X+v.Y*v.Y),Math.Abs(v.Z))*180/Math.PI); }
// crown ring nodes = form nodes of the fan cells (first n polys)
int nfan=NVV*MM; for(int i=0;i<nfan;i++) if(pos.ContainsKey(cellIds[i])){ var p=pos[cellIds[i]]; ringR.Add(Math.Sqrt(p.X*p.X+p.Y*p.Y)); }
double outMax=pos.Values.Max(p=>p.Z-6670*(1-Math.Max(Math.Abs(p.X),Math.Abs(p.Y))/5000));
Console.WriteLine("  bars >80: "+lean.Count(a=>a>80)/2+" (crown ring bars expected ~"+nfan+") <=35: "+lean.Count(a=>a<=35)/2+" | crown ring radius "+(ringR.Count>0?ringR.Min().ToString("0")+"-"+ringR.Max().ToString("0"):"-")+" mm, ring z "+(ringR.Count>0? string.Join("",new[]{pos[cellIds[0]].Z.ToString("0")}):"-")+" | max outside pyramid "+outMax.ToString("0")+" mm");

var allN=pos.Values.ToList(); double mnd=1e9; int c200=0; for(int i=0;i<allN.Count;i++) for(int j=i+1;j<allN.Count;j++){ var dd=allN[i].DistanceTo(allN[j]); if(dd<mnd) mnd=dd; if(dd<200) c200++; }
Console.WriteLine("  closest node pair "+mnd.ToString("0")+" mm, pairs <200 mm: "+c200);
Console.WriteLine("NEXT new double[]{"+string.Join(",",newFR.Select(v=>v.ToString("0.0000")))+"} "+newDep.ToString("0"));
