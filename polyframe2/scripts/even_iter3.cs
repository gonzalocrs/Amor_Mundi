#gen
double[] FR=__FR__; double DEP=__DEP__; int RR=FR.Length, MM=3;
var g=GenDiamond5(RR,MM,DEP,1,8,FR);
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
var wall=new[]{new Point3d(-5000,-5000,0),new Point3d(0,-5000,0),new Point3d(5000,-5000,0),new Point3d(5000,0,0),new Point3d(5000,5000,0),new Point3d(0,5000,0),new Point3d(-5000,5000,0),new Point3d(-5000,0,0)};
var vc=Add("Algebraic Vertex Constraints"); W(ad,"Algebraic Form",vc,"Algebraic Form"); Ints(vc,"PFVertex IDs",new[]{supIds[0],supIds[2],supIds[4],supIds[6]}); Geo(vc,"Constraints",new[]{wall[0],wall[2],wall[4],wall[6]}); Num(vc,"Scale",1);
var wc=new PolylineCurve(new[]{wall[0],wall[2],wall[4],wall[6],wall[0]});
var pvc=Add("PFVertex Constraints"); W(vc,"PFoam",pvc,"PFoam"); Ints(pvc,"PFVertex ID",supIds); var cg=(Param_Geometry)In(pvc,"Constraint"); cg.PersistentData.Clear(); for(int k=0;k<8;k++) cg.PersistentData.Append(new GH_Curve(wc)); Num(pvc,"Coefficient",10); Bool(pvc,"On",true);
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
for(int k=1;k<RR;k++) newFR[k]=Math.Max(newFR[k],newFR[k-1]+0.03); newFR[RR-1]=Math.Min(newFR[RR-1],0.97);
double newDep=DEP*apexZ/6670.0;
var dev=D(perp,"Deviation").FirstOrDefault();
Console.WriteLine("FR "+string.Join(",",FR.Select(v=>v.ToString("0.000")))+" dep "+DEP.ToString("0")+" | apex "+apexZ.ToString("0")+" | tension "+T/2+" | stageB dev "+dev+" | node ratio min "+ratios.First().ToString("0.00")+" median "+ratios[ratios.Count/2].ToString("0.00")+" max "+ratios.Last().ToString("0.00")+" off>2x "+ratios.Count(r=>r>2||r<0.5)+"/"+ratios.Count);
Console.WriteLine("  annulus design share: "+string.Join(" ",Ak.Select(a=>(a/sA).ToString("0.00")))+" | trib share: "+string.Join(" ",Tk.Select(a=>(a/sT).ToString("0.00"))));
var LL=D(ie,"Line").Cast<Line>().ToList(); var lean=new List<double>(); var ringR=new List<double>(); for(int i=0;i<LL.Count;i++) if(X[i]==0){ var v=LL[i].Direction; lean.Add(Math.Atan2(Math.Sqrt(v.X*v.X+v.Y*v.Y),Math.Abs(v.Z))*180/Math.PI); }
// crown ring nodes = form nodes of the fan cells (first n polys)
int nfan=8*MM; for(int i=0;i<nfan;i++) if(pos.ContainsKey(cellIds[i])){ var p=pos[cellIds[i]]; ringR.Add(Math.Sqrt(p.X*p.X+p.Y*p.Y)); }
double outMax=pos.Values.Max(p=>p.Z-6670*(1-Math.Max(Math.Abs(p.X),Math.Abs(p.Y))/5000));
Console.WriteLine("  bars >80: "+lean.Count(a=>a>80)/2+" (crown ring bars expected ~"+nfan+") <=35: "+lean.Count(a=>a<=35)/2+" | crown ring radius "+(ringR.Count>0?ringR.Min().ToString("0")+"-"+ringR.Max().ToString("0"):"-")+" mm, ring z "+(ringR.Count>0? string.Join("",new[]{pos[cellIds[0]].Z.ToString("0")}):"-")+" | max outside pyramid "+outMax.ToString("0")+" mm");
Console.WriteLine("NEXT new double[]{"+string.Join(",",newFR.Select(v=>v.ToString("0.0000")))+"} "+newDep.ToString("0"));
