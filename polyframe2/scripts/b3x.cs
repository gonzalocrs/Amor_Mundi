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
Solve();
sb.AppendLine("t="+sw.ElapsedMilliseconds);
foreach(var c in new[]{hex,li,poly,pic,gt,cull,disc,mrg,del,fb,bs,mv,uz,ep,bld}) if(c.RuntimeMessageLevel!=GH_RuntimeMessageLevel.Blank) sb.AppendLine(Msg(c));
var M=D(del,"Mesh")[0] as Mesh; sb.AppendLine("mesh V="+M.Vertices.Count+" F="+M.Faces.Count);
var breps=D(ep,"Extrusion").Cast<Brep>().ToList(); sb.AppendLine("breps "+breps.Count+" solid "+breps.Count(b=>b.IsSolid)+" faces "+string.Join(",",breps.Select(b=>b.Faces.Count).Distinct()));
sb.AppendLine("corners "+string.Join(" ",D(disc,"Points").Cast<Point3d>().Select(p=>p.ToString())));
sb.AppendLine("pfbuild out: "+string.Join(" ; ",bld.Params.Output.Select(o=>o.Name+"="+o.VolatileData.DataCount)));
Console.WriteLine(sb.ToString());
