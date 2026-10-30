int NN=2; double DD=623.5; double VS=1; double HX=5000; double[] SUPT=new[]{0.125,0.375,0.625,0.875}; 
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
// targets: centroids of the 4 boundary tets (one per diamond edge), order (+,+),(-,+),(-,-),(+,-)
var el=Add("Evaluate Length"); W(poly,"Polygon",el,"Curve"); Nums(el,"Length",new[]{0.125,0.375,0.625,0.875}); Bool(el,"Normalized",true);
var mcp=Add("Mesh Closest Point"); W(el,"Point",mcp,"Point"); W(del,"Mesh",mcp,"Mesh");
var lib=Add("List Item"); W(ep,"Extrusion",lib,"List"); In(lib,"List").DataMapping=GH_DataMapping.Flatten; W(mcp,"Index",lib,"Index");
var vol=AddG("7c0523e8-79c9-45a2-8777-cf0d46bc5432"); W(lib,"Item",vol,"Geometry");

var bld=Add("PFBuild"); W(ep,"Extrusion",bld,"Brep"); In(bld,"Brep").DataMapping=GH_DataMapping.Flatten; Num(bld,"Absolute Tolerance",0.1); Num(bld,"Planarity Tolerance",0.1);
// pick support cell IDs natively
var exf=Add("Explode PFoam"); W(bld,"Force PFoam",exf,"PFoam");
var ipc=Add("Inspect PFCell"); W(exf,"PFCells",ipc,"PFCell");
var cps=Add("Closest Points"); W(vol,"Centroid",cps,"Point"); W(ipc,"Centroid",cps,"Cloud"); Int(cps,"Count",1);
var lid=Add("List Item"); W(ipc,"ID",lid,"List"); W(cps,"CP Index",lid,"Index"); In(lid,"Index").DataMapping=GH_DataMapping.Flatten;
var spoly=Add("Polygon"); Pl(spoly,"Plane",Plane.WorldXY); Num(spoly,"Radius",2*HX); Int(spoly,"Segments",4); Num(spoly,"Fillet Radius",0);
var sel=Add("Evaluate Length"); W(spoly,"Polygon",sel,"Curve"); Nums(sel,"Length",SUPT); Bool(sel,"Normalized",true);
var ad=Add("Algebraic Dual"); W(bld,"Force PFoam",ad,"Force PFoam"); Num(ad,"Scale",1); Bool(ad,"Flip",false);
var vc=Add("Algebraic Vertex Constraints"); W(ad,"Algebraic Form",vc,"Algebraic Form"); W(lid,"Item",vc,"PFVertex IDs"); In(vc,"PFVertex IDs").DataMapping=GH_DataMapping.Flatten; W(sel,"Point",vc,"Constraints"); In(vc,"Constraints").DataMapping=GH_DataMapping.Flatten; Num(vc,"Scale",VS);

void Tap(IGH_Component src,string outName,string tag){
 var e=Add("Explode PFoam"); W(src,outName,e,"PFoam"); e.NickName="X_"+tag;
 var ie=Add("Inspect PFEdge"); W(e,"PFEdges",ie,"PFEdge"); ie.NickName="E_"+tag;
 var iv2=Add("Inspect PFVertex"); W(e,"PFVertices",iv2,"PFVertex"); iv2.NickName="V_"+tag;
}

// dual vertex IDs in PFBuild form for the picked cells
var ivd=Add("Inspect PFVertex"); W(ipc,"Dual",ivd,"PFVertex");
Solve();
var cellIdx=D(cps,"CP Index").Select(x=>Convert.ToInt32(x)).ToList();
var dualTree=Out(ivd,"ID").VolatileData; var paths=dualTree.Paths.ToList();
var fids=new List<int>(); foreach(var ci in cellIdx){ var br=dualTree.get_Branch(paths[ci]); fids.Add(Convert.ToInt32(((GH_Integer)br[0]).Value)); }
sb.AppendLine("cell idx "+string.Join(",",cellIdx)+" -> form IDs "+string.Join(",",fids)+" (branch sizes "+string.Join(",",cellIdx.Select(ci=>dualTree.get_Branch(paths[ci]).Count))+")");
var pvc=Add("PFVertex Constraints"); W(bld,"Form PFoam",pvc,"PFoam"); Ints(pvc,"PFVertex ID",fids); W(sel,"Point",pvc,"Constraint"); In(pvc,"Constraint").DataMapping=GH_DataMapping.Flatten; Num(pvc,"Coefficient",10); Bool(pvc,"On",true);
var perp=Add("PFPerp"); W(pvc,"PFoam",perp,"PFoam"); Int(perp,"Max Iteration",3000); Num(perp,"Deviation",0.1); Num(perp,"Minimum Edge Length",10);
perp.NickName="PERP"; Tap(perp,"PFoam","PERP");
var old=Instances.ActiveCanvas.Document; Instances.DocumentServer.AddDocument(doc); Instances.ActiveCanvas.Document=doc; if(old!=null){ old.Enabled=false; Instances.DocumentServer.RemoveDocument(old); old.Dispose(); }
var t0=sw.ElapsedMilliseconds; Solve(); sb.AppendLine("perp solve ms "+(sw.ElapsedMilliseconds-t0)+" dev "+string.Join(",",D(perp,"Deviation")));
foreach(var c in doc.Objects.OfType<IGH_Component>()) if(c.RuntimeMessageLevel!=GH_RuntimeMessageLevel.Blank && !c.NickName.EndsWith("_LO")) sb.AppendLine("  msg "+Msg(c));
Console.WriteLine(sb.ToString());
