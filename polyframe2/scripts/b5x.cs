int NN=2; double DD=1000;
// ---- force diagram (native) ----
double R=1000; 
var hex=Add("Hexagonal"); Pl(hex,"Plane",Plane.WorldXY); Num(hex,"Size",R/(3*NN)); Int(hex,"Extent X",41); Int(hex,"Extent Y",41);
var li=Add("List Item"); W(hex,"Points",li,"List"); In(li,"List").DataMapping=GH_DataMapping.Flatten; Int(li,"Index",840);
var poly=Add("Polygon"); W(li,"Item",poly,"Plane"); Num(poly,"Radius",R); Int(poly,"Segments",4); Num(poly,"Fillet Radius",0);
var pic=Add("Point In Curve"); W(hex,"Points",pic,"Point"); In(pic,"Point").DataMapping=GH_DataMapping.Flatten; W(poly,"Polygon",pic,"Curve");
var gt=Add("Larger Than"); W(pic,"Relationship",gt,"First Number"); Num(gt,"Second Number",1);
var cull=Add("Cull Pattern"); W(pic,"Point",cull,"List"); W(gt,"Larger than",cull,"Cull Pattern");
var disc=Add("Discontinuity"); W(poly,"Polygon",disc,"Curve"); Int(disc,"Level",1);
var mrg=AddG("3cadddef-1e2b-4c09-9390-0e8f78f7609f"); In(mrg,"Data 1").AddSource(Out(disc,"Points")); In(mrg,"Data 2").AddSource(Out(cull,"List"));
var del=Add("Delaunay Mesh"); W(mrg,"Result",del,"Points"); In(del,"Points").DataMapping=GH_DataMapping.Flatten; Pl(del,"Plane",Plane.WorldXY);
var fb=Add("Face Boundaries"); W(del,"Mesh",fb,"Mesh");
var bs=Add("Boundary Surfaces"); W(fb,"Boundaries",bs,"Edges"); In(bs,"Edges").DataMapping=GH_DataMapping.Graft;
var mv=Add("Move"); W(li,"Item",mv,"Geometry"); 
var uz=Add("Unit Z"); Num(uz,"Factor",-DD); W(uz,"Unit vector",mv,"Motion");
var ep=Add("Extrude Point"); W(bs,"Surfaces",ep,"Base"); W(mv,"Geometry",ep,"Point");

var bld=Add("PFBuild"); W(ep,"Extrusion",bld,"Brep"); In(bld,"Brep").DataMapping=GH_DataMapping.Flatten; Num(bld,"Absolute Tolerance",0.1); Num(bld,"Planarity Tolerance",0.1);
var ad=Add("Algebraic Dual"); W(bld,"Force PFoam",ad,"Force PFoam"); Num(ad,"Scale",1); Bool(ad,"Flip",false);
var ex=Add("Explode PFoam"); W(bld,"Force PFoam",ex,"PFoam");
var ic=Add("Inspect PFCell"); W(ex,"PFCells",ic,"PFCell");
var ivd=Add("Inspect PFVertex"); W(ic,"Dual",ivd,"PFVertex");
Solve(); sb.AppendLine("t="+sw.ElapsedMilliseconds);
foreach(var c in new[]{bld,ad,ex,ic,ivd}) if(c.RuntimeMessageLevel!=GH_RuntimeMessageLevel.Blank) sb.AppendLine(Msg(c));
var ids=D(ic,"ID"); var ext=D(ic,"External"); var cen=D(ic,"Centroid").Cast<Point3d>().ToList(); var dualIds=D(ivd,"ID");
sb.AppendLine("cells "+ids.Count+" dual ids "+dualIds.Count);
var breps=D(ep,"Extrusion").Cast<Brep>().ToList();
for(int i=0;i<ids.Count;i++){ int bi=-1; for(int j=0;j<breps.Count;j++){ var bc=VolumeMassProperties.Compute(breps[j]).Centroid; if(bc.DistanceTo(cen[i])<1) bi=j;} sb.Append(ids[i]+":"+ext[i]+":b"+bi+":d"+(i<dualIds.Count?dualIds[i]:"-")+"  "); }
Console.WriteLine(sb.ToString());
