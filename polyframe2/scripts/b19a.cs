int RR=5, MM=1; double DD=800, FE=0.5; double HX=5000; int IT=150; double COEF=10; bool PIN8=false; bool TREE=false; int NF=16; bool STAG=false; bool DIA=false; bool DIA2=true; double R0=400; int[] ZN=new int[]{64,32,16}; double[] ZR=new double[]{840,870,930}; bool SHOW=false; double QV=1;
#gen
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
#show
Console.WriteLine(sb.ToString());
