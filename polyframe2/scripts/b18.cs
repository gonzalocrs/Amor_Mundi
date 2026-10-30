double NN=__N__; double DD=__D__; double ROT=__ROT__; double HX=5000; bool[] PAT=__PAT__; double Q=QQ; int RINGS=RNG; int SP16=SPV; int LM=LMV; int IT=ITV; double COEF=COEFV;
#force8
#form8
if(LM>0){ In(vc,"PFVertex IDs").RemoveAllSources(); In(vc,"Constraints").RemoveAllSources(); W(lid,"Item",vc,"PFVertex IDs"); In(vc,"PFVertex IDs").DataMapping=GH_DataMapping.Flatten;
 var gp=(Param_Geometry)In(vc,"Constraints"); gp.PersistentData.Clear();
 var wall=new[]{new Point3d(-HX,-HX,0),new Point3d(0,-HX,0),new Point3d(HX,-HX,0),new Point3d(HX,0,0),new Point3d(HX,HX,0),new Point3d(0,HX,0),new Point3d(-HX,HX,0),new Point3d(-HX,0,0)};
 for(int k=0;k<8;k++){ if(k%2==0) gp.PersistentData.Append(new GH_Point(wall[k])); else gp.PersistentData.Append(new GH_Plane(new Plane(wall[k],Vector3d.ZAxis))); } }
var pvc=Add("PFVertex Constraints"); W(vc,"PFoam",pvc,"PFoam"); W(lid,"Item",pvc,"PFVertex ID"); In(pvc,"PFVertex ID").DataMapping=GH_DataMapping.Flatten;
var wc=new PolylineCurve(new[]{new Point3d(-HX,-HX,0),new Point3d(HX,-HX,0),new Point3d(HX,HX,0),new Point3d(-HX,HX,0),new Point3d(-HX,-HX,0)});
var cg=(Param_Geometry)In(pvc,"Constraint"); cg.PersistentData.Clear(); for(int k=0;k<8;k++) cg.PersistentData.Append(new GH_Curve(wc));
Num(pvc,"Coefficient",COEF); Bool(pvc,"On",true);
var perp=Add("PFPerp"); W(pvc,"PFoam",perp,"PFoam"); Int(perp,"Max Iteration",IT); Num(perp,"Deviation",0.1); Num(perp,"Minimum Edge Length",10);
string Stats(IGH_Component src,string outn,string tag){
 var ex=Add("Explode PFoam"); W(src,outn,ex,"PFoam"); var sp=Add("Separate PFEdges By Type"); W(ex,"PFEdges",sp,"PFEdge"); var ie=Add("Inspect PFEdge"); W(sp,"Internal",ie,"PFEdge");
 var iff=Add("Inspect PFFace"); W(ie,"Dual",iff,"PFFace"); var iv=Add("Inspect PFVertex"); W(ex,"PFVertices",iv,"PFVertex");
 var t0=sw.ElapsedMilliseconds; Solve(); var tms=sw.ElapsedMilliseconds-t0;
 var F=D(ie,"Force").Select(x=>Convert.ToDouble(x)).ToList(); var L=D(ie,"Line").Cast<Line>().ToList(); var PL=D(iff,"Plane").Cast<Plane>().ToList();
 var dev=new List<double>(); for(int i=0;i<L.Count&&i<PL.Count;i++){ var a=Vector3d.VectorAngle(L[i].Direction,PL[i].Normal)*180/Math.PI; dev.Add(Math.Min(a,180-a)); }
 var P=D(iv,"Point").Cast<Point3d>().ToList(); var VID=D(iv,"ID").Select(x=>Convert.ToInt32(x)).ToList(); var X=D(iv,"External").Select(x=>(bool)x).ToList();
 var ids=D(lid,"Item").Select(x=>Convert.ToInt32(x)).ToList();
 var feet=ids.Select(id=>{int j=VID.IndexOf(id); return j>=0?P[j]:Point3d.Unset;}).ToList();
 var off=feet.Select(p=>{ double t; wc.ClosestPoint(p,out t); return p.DistanceTo(wc.PointAt(t)); }).ToList();
 var ip=P.Where((p,i)=>!X[i]).ToList();
 return tag+" ms "+tms+" bars "+F.Count/2+" T "+F.Count(f=>f<-1e-9)/2+" apex "+ip.Max(p=>p.Z).ToString("0")+" dev max "+dev.DefaultIfEmpty(0).Max().ToString("0.00")+" mean "+dev.DefaultIfEmpty(0).Average().ToString("0.00")+" | foot-to-wall max "+off.Max().ToString("0")+" mean "+off.Average().ToString("0")+" mm | feet "+string.Join(" ",feet.Select(p=>"("+(p.X/1000).ToString("0.00")+","+(p.Y/1000).ToString("0.00")+","+(p.Z/1000).ToString("0.00")+")"));
}
sb.AppendLine(Stats(vc,"PFoam","A"));
sb.AppendLine(Stats(perp,"PFoam","B")+" | perp: "+string.Join("",perp.RuntimeMessages(GH_RuntimeMessageLevel.Warning).Concat(perp.RuntimeMessages(GH_RuntimeMessageLevel.Remark))));
foreach(var o in doc.Objects.OfType<IGH_ActiveObject>()) if(o is IGH_PreviewObject po) po.Hidden=true;
var pA=Add("PFPipe"); W(vc,"PFoam",pA,"PFoam"); Num(pA,"MinR",30); Num(pA,"MaxR",90); ((IGH_PreviewObject)pA).Hidden=true;
var mA=Add("Move"); W(pA,"Pipe",mA,"Geometry"); var vx=(Param_Vector)In(mA,"Motion"); vx.PersistentData.Clear(); vx.PersistentData.Append(new GH_Vector(new Vector3d(-14000,0,0)));
var cA=Add("Custom Preview"); W(mA,"Geometry",cA,"Geometry"); W(pA,"Color",cA,"Material");
var pB=Add("PFPipe"); W(perp,"PFoam",pB,"PFoam"); Num(pB,"MinR",30); Num(pB,"MaxR",90); ((IGH_PreviewObject)pB).Hidden=true;
var cB=Add("Custom Preview"); W(pB,"Pipe",cB,"Geometry"); W(pB,"Color",cB,"Material");
var old=Instances.ActiveCanvas.Document; Instances.DocumentServer.AddDocument(doc); Instances.ActiveCanvas.Document=doc; if(old!=null){ old.Enabled=false; Instances.DocumentServer.RemoveDocument(old); old.Dispose(); }
doc.NewSolution(false);
Console.WriteLine(sb.ToString());
