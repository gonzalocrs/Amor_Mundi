double NN=1.2; double DD=480; double ROT=-157.5; double HX=5000; bool[] PAT=new[]{true}; double Q=1; int RINGS=3; int SP16=0; int LM=0; int IT=1000; double COEF=10;
// ---- AP8 force diagram: octagon cap ----
double R=1000;
var hex=Add("Hexagonal"); Pl(hex,"Plane",Plane.WorldXY); Num(hex,"Size",R/(3*NN)); Int(hex,"Extent X",41); Int(hex,"Extent Y",41);
var li=Add("List Item"); W(hex,"Points",li,"List"); In(li,"List").DataMapping=GH_DataMapping.Flatten; Int(li,"Index",840);
var poly0=Add("Polygon"); W(li,"Item",poly0,"Plane"); Num(poly0,"Radius",R); Int(poly0,"Segments",8); Num(poly0,"Fillet Radius",0);
var rot=AddG("b7798b74-037e-4f0c-8ac7-dc1043d093e0"); W(poly0,"Polygon",rot,"Geometry"); Num(rot,"Angle",ROT*Math.PI/180); W(li,"Item",rot,"Plane");
List<Point3d> VS8=null; IGH_Component poly=rot; string PO="Geometry";
if(Q>0){ double Sz=R/(3*NN); var c0=new Point3d(30*Sz, 20*Math.Sqrt(3)*Sz,0); double b=R*Math.Cos(Math.PI/8), a=Q*b*(1+Math.Tan(Math.PI/8));
 var vs=new[]{new Point3d(-b,-a+b,0),new Point3d(-a+b,-b,0),new Point3d(a-b,-b,0),new Point3d(b,-a+b,0),new Point3d(b,a-b,0),new Point3d(a-b,b,0),new Point3d(-a+b,b,0),new Point3d(-b,a-b,0),new Point3d(-b,-a+b,0)}.Select(p=>p+(Vector3d)c0).ToList(); VS8=vs;
 var pl8=Add("PolyLine"); var pv=(Param_Point)In(pl8,"Vertices"); pv.PersistentData.Clear(); foreach(var q in vs) pv.PersistentData.Append(new GH_Point(q)); Bool(pl8,"Closed",false); poly=pl8; PO="Polyline"; }
var pic=Add("Point In Curve"); W(hex,"Points",pic,"Point"); In(pic,"Point").DataMapping=GH_DataMapping.Flatten; W(poly,PO,pic,"Curve");
var gt=Add("Larger Than"); W(pic,"Relationship",gt,"First Number"); Num(gt,"Second Number",1);
var cull=Add("Cull Pattern"); W(pic,"Point",cull,"List"); W(gt,"Larger than",cull,"Cull Pattern");
var disc=Add("Discontinuity"); W(poly,PO,disc,"Curve"); Int(disc,"Level",1);
var mrg=AddG("3cadddef-1e2b-4c09-9390-0e8f78f7609f"); In(mrg,"Data 1").AddSource(Out(disc,"Points")); In(mrg,"Data 2").AddSource(Out(cull,"List"));
if(RINGS>0 && VS8!=null){ var cc=new Point3d(0,0,0); for(int k=0;k<8;k++) cc+=VS8[k]; cc/=8; var rp=new List<Point3d>{cc};
  // spokes toward the 8 edge midpoints (feet) and the 8 vertices
  for(int r=1;r<=RINGS;r++){ double f=(double)r/(RINGS+1); for(int k=0;k<8;k++){ var m=0.5*(VS8[k]+VS8[k+1]); rp.Add(cc+(m-cc)*f); if(SP16>0) rp.Add(cc+(VS8[k]-cc)*f); } }
  In(mrg,"Data 2").RemoveAllSources(); var d2p=(Param_GenericObject)In(mrg,"Data 2"); d2p.PersistentData.Clear(); foreach(var q in rp) d2p.PersistentData.Append(new GH_Point(q)); }
var del=Add("Delaunay Mesh"); W(mrg,"Result",del,"Points"); In(del,"Points").DataMapping=GH_DataMapping.Flatten; Pl(del,"Plane",Plane.WorldXY);
var fb=Add("Face Boundaries"); W(del,"Mesh",fb,"Mesh");
var bs=Add("Boundary Surfaces"); W(fb,"Boundaries",bs,"Edges"); In(bs,"Edges").DataMapping=GH_DataMapping.Graft;
var mv=Add("Move"); W(li,"Item",mv,"Geometry");
var uz=Add("Unit Z"); Num(uz,"Factor",-DD); W(uz,"Unit vector",mv,"Motion");
var ep=Add("Extrude Point"); W(bs,"Surfaces",ep,"Base"); W(mv,"Geometry",ep,"Point");
var el=Add("Evaluate Length"); W(poly,PO,el,"Curve"); Nums(el,"Length",Enumerable.Range(0,8).Select(k=>(k+0.5)/8.0)); Bool(el,"Normalized",true);
var mcp=Add("Mesh Closest Point"); if(Q>0){ var mids=new List<Point3d>(); for(int k=0;k<8;k++) mids.Add(0.5*(VS8[k]+VS8[k+1])); Pts(mcp,"Point",mids);} else W(el,"Point",mcp,"Point"); W(del,"Mesh",mcp,"Mesh");
var lib=Add("List Item"); W(ep,"Extrusion",lib,"List"); In(lib,"List").DataMapping=GH_DataMapping.Flatten; W(mcp,"Index",lib,"Index");
var vol=AddG("7c0523e8-79c9-45a2-8777-cf0d46bc5432"); W(lib,"Item",vol,"Geometry");

var bld=Add("PFBuild"); W(ep,"Extrusion",bld,"Brep"); In(bld,"Brep").DataMapping=GH_DataMapping.Flatten; Num(bld,"Absolute Tolerance",0.1); Num(bld,"Planarity Tolerance",0.1);
var exf=Add("Explode PFoam"); W(bld,"Force PFoam",exf,"PFoam");
var ipc=Add("Inspect PFCell"); W(exf,"PFCells",ipc,"PFCell");
var cps=Add("Closest Points"); W(vol,"Centroid",cps,"Point"); W(ipc,"Centroid",cps,"Cloud"); Int(cps,"Count",1);
var lid=Add("List Item"); W(ipc,"ID",lid,"List"); W(cps,"CP Index",lid,"Index"); In(lid,"Index").DataMapping=GH_DataMapping.Flatten;
var ad=Add("Algebraic Dual"); W(bld,"Force PFoam",ad,"Force PFoam"); Num(ad,"Scale",1); Bool(ad,"Flip",false);
// wall square: Divide Curve 8 -> corner, mid, corner ... starting (-,-)
var rect=Add("Rectangle"); Pl(rect,"Plane",Plane.WorldXY);
var dom=new Grasshopper.Kernel.Types.GH_Interval(new Interval(-HX,HX)); ((Param_Interval)In(rect,"X Size")).PersistentData.Clear(); ((Param_Interval)In(rect,"X Size")).PersistentData.Append(dom); ((Param_Interval)In(rect,"Y Size")).PersistentData.Clear(); ((Param_Interval)In(rect,"Y Size")).PersistentData.Append(dom);
var dv=Add("Divide Curve"); W(rect,"Rectangle",dv,"Curve"); Int(dv,"Count",8);
// pinned subset (pattern)
var cpat=Add("Cull Pattern"); W(dv,"Points",cpat,"List"); var pp_=(Param_Boolean)In(cpat,"Cull Pattern"); pp_.PersistentData.Clear(); foreach(var b in PAT) pp_.PersistentData.Append(new GH_Boolean(b));
var cid=Add("Cull Pattern"); W(lid,"Item",cid,"List"); In(cid,"List").DataMapping=GH_DataMapping.Flatten; var pq_=(Param_Boolean)In(cid,"Cull Pattern"); pq_.PersistentData.Clear(); foreach(var b in PAT) pq_.PersistentData.Append(new GH_Boolean(b));
var vc=Add("Algebraic Vertex Constraints"); W(ad,"Algebraic Form",vc,"Algebraic Form"); W(cid,"List",vc,"PFVertex IDs"); W(cpat,"List",vc,"Constraints"); In(vc,"Constraints").DataMapping=GH_DataMapping.Flatten; Num(vc,"Scale",1);

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
