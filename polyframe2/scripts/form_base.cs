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
