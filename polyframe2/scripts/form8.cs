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
