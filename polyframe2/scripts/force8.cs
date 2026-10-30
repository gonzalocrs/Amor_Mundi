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
  if(SP16<2){ for(int r=1;r<=RINGS;r++){ double f=(double)r/(RINGS+1); for(int k=0;k<8;k++){ var m=0.5*(VS8[k]+VS8[k+1]); rp.Add(cc+(m-cc)*f); if(SP16>0) rp.Add(cc+(VS8[k]-cc)*f); } } }
  else { var oc=new PolylineCurve(VS8); 
    for(int r=1;r<=RINGS;r++){ double f=(double)r/(RINGS+1); var ring=oc.DuplicateCurve(); ring.Transform(Transform.Scale(cc,f)); foreach(var tt in ring.DivideByCount(16,true)) rp.Add(ring.PointAt(tt)); }
    for(int r=(SP16==3?1:0);r<=RINGS;r++){ double f=(r+0.5)/(RINGS+1); var ring=oc.DuplicateCurve(); ring.Transform(Transform.Scale(cc,f)); var ts=ring.DivideByCount(32,true); for(int i=1;i<32;i+=2) rp.Add(ring.PointAt(ts[i])); } }
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
