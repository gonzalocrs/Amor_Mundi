double NN=3.0; double DD=330; double ROT=-157.5; double Q=1.0; int LM=0; double HX=5000; bool[] PAT=new[]{true,false};
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
 for(int k=0;k<8;k++){ if(k%2==0) gp.PersistentData.Append(new GH_Point(wall[k])); else { var dir=(k==1||k==5)? Vector3d.XAxis: Vector3d.YAxis; if(LM==2) gp.PersistentData.Append(new GH_Plane(new Plane(wall[k],Vector3d.ZAxis))); else gp.PersistentData.Append(new GH_Line(new Line(wall[k]-dir*3000,wall[k]+dir*3000))); } }
 PAT=new[]{true}; }
var ex=Add("Explode PFoam"); W(vc,"PFoam",ex,"PFoam"); var sp=Add("Separate PFEdges By Type"); W(ex,"PFEdges",sp,"PFEdge"); var ie=Add("Inspect PFEdge"); W(sp,"Internal",ie,"PFEdge");
var iv=Add("Inspect PFVertex"); W(ex,"PFVertices",iv,"PFVertex");
Solve();
foreach(var c in doc.Objects.OfType<IGH_Component>()) if(c.RuntimeMessageLevel==GH_RuntimeMessageLevel.Error) sb.AppendLine("ERR "+Msg(c));
var F=D(ie,"Force").Select(x=>Convert.ToDouble(x)).ToList(); var P=D(iv,"Point").Cast<Point3d>().ToList(); var X=D(iv,"External").Select(x=>(bool)x).ToList(); var VID=D(iv,"ID").Select(x=>Convert.ToInt32(x)).ToList();
var ip=P.Where((p,i)=>!X[i]).ToList();
var ids=D(lid,"Item").Select(x=>Convert.ToInt32(x)).ToList(); var tg=D(dv,"Points").Cast<Point3d>().ToList();
sb.AppendLine("n "+NN+" d "+DD+" cells "+D(ipc,"ID").Count+": bars "+F.Count/2+" T "+F.Count(f=>f<-1e-9)/2+" apex "+(ip.Count>0?ip.Max(p=>p.Z).ToString("0"):"-")+" ms "+sw.ElapsedMilliseconds+" ids "+string.Join(",",ids));
for(int k=0;k<ids.Count;k++){ int j=VID.IndexOf(ids[k]); var p=j>=0?P[j]:Point3d.Unset; var t=tg[k]; 
  // outward offset from wall line: for corners use max(|x|,|y|)-5000 ; mid: same
  double outw=Math.Max(Math.Abs(p.X),Math.Abs(p.Y))-HX;
  sb.AppendLine("  sup "+k+(PAT[k%PAT.Length]?" PIN ":" free")+" target "+t.X.ToString("0")+","+t.Y.ToString("0")+" -> "+p.X.ToString("0")+","+p.Y.ToString("0")+","+p.Z.ToString("0")+"  out "+outw.ToString("0")+" mm"); }
{ double mo=0,mz=0,mp=0; for(int k=0;k<ids.Count;k++){ int j=VID.IndexOf(ids[k]); if(j<0) continue; var p=P[j]; mo=Math.Max(mo,Math.Abs(Math.Max(Math.Abs(p.X),Math.Abs(p.Y))-HX)); mz=Math.Max(mz,Math.Abs(p.Z)); mp=Math.Max(mp,new Point3d(p.X,p.Y,0).DistanceTo(tg[k])); } sb.AppendLine("SUMMARY max|out| "+mo.ToString("0")+" max|z| "+mz.ToString("0")+" max plan miss "+mp.ToString("0")); }
{ var L=D(ie,"Line").Cast<Line>().ToList(); var tb=new List<string>(); for(int i=0;i<F.Count;i++) if(F[i]<-1e-9) tb.Add(F[i].ToString("0")+"@"+L[i].Length.ToString("0")+"mm z"+L[i].PointAt(0.5).Z.ToString("0")); sb.AppendLine("TBARS (Fmax "+F.Max().ToString("0")+"): "+string.Join("  ",tb)); }
Console.WriteLine(sb.ToString());
