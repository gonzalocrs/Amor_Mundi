GH_Document cur2=null;
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

var g=GenTree(500,200,1);
// test PFBuild on subsets: by triangle type index within sector (9 types + 8 fan) 
int per=9+8;
foreach(var keep in new[]{"fan","fan+W","fan+W+Z","fan+W+Z+Y","all-but-X","all"}){
 var docT=new GH_Document(); cur2=docT;
 var sel=new List<Brep>();
 for(int i=0;i<g.tets.Count;i++){ int t=i%per; string ty= t==0?"foot": t==1?"X": t==2?"Y": (t==3||t==4)?"Z": (t>=5&&t<=8)?"W":"fan";
   bool k= keep=="all" || (keep=="all-but-X" && ty!="X") || (keep.Contains(ty) && !(keep=="fan" && ty!="fan"));
   if(keep=="fan+W") k= ty=="fan"||ty=="W"; if(keep=="fan+W+Z") k= ty=="fan"||ty=="W"||ty=="Z"; if(keep=="fan+W+Z+Y") k= ty=="fan"||ty=="W"||ty=="Z"||ty=="Y"; if(keep=="fan") k= ty=="fan";
   if(k) sel.Add(g.tets[i]); }
 var bp=new Param_Brep(); bp.CreateAttributes(); docT.AddObject(bp,false); foreach(var t in sel) bp.PersistentData.Append(new GH_Brep(t));
 var bld=(IGH_Component)Instances.ComponentServer.EmitObject(new Guid("e99d404e-47c7-4572-ad31-9463a4abe4af")); bld.CreateAttributes(); docT.AddObject(bld,false); bld.Params.Input[0].AddSource(bp); ((Param_Number)bld.Params.Input[1]).PersistentData.Append(new GH_Number(0.1)); ((Param_Number)bld.Params.Input[2]).PersistentData.Append(new GH_Number(0.1));
 docT.Enabled=true; docT.NewSolution(false,GH_SolutionMode.Silent);
 sb.AppendLine(keep+" n="+sel.Count+" : "+bld.RuntimeMessageLevel+" "+string.Join("|",bld.RuntimeMessages(GH_RuntimeMessageLevel.Error)).Replace("\n"," ").Substring(0,Math.Min(120,string.Join("|",bld.RuntimeMessages(GH_RuntimeMessageLevel.Error)).Length)));
}
Console.WriteLine(sb.ToString());
