int NN=2; double DD=1000;
#include
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
