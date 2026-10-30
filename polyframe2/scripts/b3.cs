int NN=2; double DD=1000;
#include
var bld=Add("PFBuild"); W(ep,"Extrusion",bld,"Brep"); In(bld,"Brep").DataMapping=GH_DataMapping.Flatten; Num(bld,"Absolute Tolerance",0.1); Num(bld,"Planarity Tolerance",0.1);
Solve();
sb.AppendLine("t="+sw.ElapsedMilliseconds);
foreach(var c in new[]{hex,li,poly,pic,gt,cull,disc,mrg,del,fb,bs,mv,uz,ep,bld}) if(c.RuntimeMessageLevel!=GH_RuntimeMessageLevel.Blank) sb.AppendLine(Msg(c));
var M=D(del,"Mesh")[0] as Mesh; sb.AppendLine("mesh V="+M.Vertices.Count+" F="+M.Faces.Count);
var breps=D(ep,"Extrusion").Cast<Brep>().ToList(); sb.AppendLine("breps "+breps.Count+" solid "+breps.Count(b=>b.IsSolid)+" faces "+string.Join(",",breps.Select(b=>b.Faces.Count).Distinct()));
sb.AppendLine("corners "+string.Join(" ",D(disc,"Points").Cast<Point3d>().Select(p=>p.ToString())));
sb.AppendLine("pfbuild out: "+string.Join(" ; ",bld.Params.Output.Select(o=>o.Name+"="+o.VolatileData.DataCount)));
Console.WriteLine(sb.ToString());
