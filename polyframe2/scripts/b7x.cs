int NN=2; double DD=1000; int[] SUP={5,45,43,6}; double VS=1;
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
var vc=Add("Algebraic Vertex Constraints"); W(ad,"Algebraic Form",vc,"Algebraic Form"); Ints(vc,"PFVertex IDs",SUP); Geo(vc,"Constraints",new[]{new Point3d(-5000,-5000,0),new Point3d(5000,-5000,0),new Point3d(5000,5000,0),new Point3d(-5000,5000,0)}); Num(vc,"Scale",VS);

IGH_Component Rep(IGH_Component src,string outName,string tag){
 var e=Add("Explode PFoam"); W(src,outName,e,"PFoam");
 var ie=Add("Inspect PFEdge"); W(e,"PFEdges",ie,"PFEdge");
 var iv2=Add("Inspect PFVertex"); W(e,"PFVertices",iv2,"PFVertex");
 var t0=sw.ElapsedMilliseconds; Solve(); sb.AppendLine(tag+" solve ms "+(sw.ElapsedMilliseconds-t0));
 foreach(var c in doc.Objects.OfType<IGH_Component>()) if(c.RuntimeMessageLevel!=GH_RuntimeMessageLevel.Blank) sb.AppendLine("  msg "+Msg(c));
 var F=D(ie,"Force").Select(x=>Convert.ToDouble(x)).ToList(); var X=D(ie,"External").Select(x=>Convert.ToInt32(x)).ToList(); var L=D(ie,"Line").Cast<Line>().ToList(); var EID=D(ie,"ID").Select(x=>Convert.ToInt32(x)).ToList();
 var internalF=new List<double>(); var seen=new HashSet<int>(); var lens=new List<double>();
 for(int i=0;i<F.Count;i++) if(X[i]==0){ internalF.Add(F[i]); lens.Add(L[i].Length);} 
 var P=D(iv2,"Point").Cast<Point3d>().ToList(); var VX=D(iv2,"External").Select(x=>(bool)x).ToList();
 var ip=P.Where((p,i)=>!VX[i]).ToList();
 var bb=new BoundingBox(ip);
 sb.AppendLine("  halfedges "+F.Count+" internal "+internalF.Count+" C(+) "+internalF.Count(f=>f>1e-9)+" T(-) "+internalF.Count(f=>f< -1e-9)+" Fmin "+internalF.DefaultIfEmpty(0).Min().ToString("0.###")+" Fmax "+internalF.DefaultIfEmpty(0).Max().ToString("0.###")+" Lmin "+lens.DefaultIfEmpty(0).Min().ToString("0.#")+" Lmax "+lens.DefaultIfEmpty(0).Max().ToString("0.#"));
 sb.AppendLine("  internal verts "+ip.Count+" bbox "+bb.Min+" .. "+bb.Max);
 return ie;
}

Rep(vc,"PFoam","VC");
Console.WriteLine(sb.ToString());
