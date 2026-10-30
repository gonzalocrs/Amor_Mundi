int NN=2; double DD=1000;
#include
var bld=Add("PFBuild"); W(ep,"Extrusion",bld,"Brep"); In(bld,"Brep").DataMapping=GH_DataMapping.Flatten; Num(bld,"Absolute Tolerance",0.1); Num(bld,"Planarity Tolerance",0.1);
var ad=Add("Algebraic Dual"); W(bld,"Force PFoam",ad,"Force PFoam"); Num(ad,"Scale",1); Bool(ad,"Flip",false);
var ex=Add("Explode PFoam"); W(ad,"Form PFoam",ex,"PFoam");
var iv=Add("Inspect PFVertex"); W(ex,"PFVertices",iv,"PFVertex");
var ic=Add("Inspect PFCell"); W(iv,"Dual",ic,"PFCell");
Solve(); sb.AppendLine("t="+sw.ElapsedMilliseconds);
foreach(var c in new[]{bld,ad,ex,iv,ic}) if(c.RuntimeMessageLevel!=GH_RuntimeMessageLevel.Blank) sb.AppendLine(Msg(c));
var ids=D(iv,"ID"); var ext=D(iv,"External"); var pts=D(iv,"Point").Cast<Point3d>().ToList(); var cen=D(ic,"Centroid").Cast<Point3d>().ToList(); var cext=D(ic,"External");
sb.AppendLine("form verts "+ids.Count+" cells "+cen.Count);
// boundary breps: tets whose cap triangle has a naked mesh edge
var M=D(del,"Mesh")[0] as Mesh; var breps=D(ep,"Extrusion").Cast<Brep>().ToList();
var nk=M.GetNakedEdges(); sb.AppendLine("naked polylines "+nk.Length+" segs "+nk.Sum(p=>p.SegmentCount));
var mids=new List<Point3d>(); foreach(var pl in nk) foreach(var sg in pl.GetSegments()) mids.Add(sg.PointAt(0.5));
var apex=D(mv,"Geometry")[0]; sb.AppendLine("apex "+apex);
for(int k=0;k<mids.Count;k++){ // find brep containing midpoint on cap
  int bj=-1; for(int j=0;j<breps.Count;j++){ if(breps[j].ClosestPoint(mids[k]).DistanceTo(mids[k])<1e-3){ bj=j; break;} }
  var bc=VolumeMassProperties.Compute(breps[bj]).Centroid;
  int vi=-1; for(int i=0;i<cen.Count;i++) if(cen[i].DistanceTo(bc)<1e-2) vi=i;
  sb.AppendLine("mid "+mids[k]+" brep "+bj+" -> formvert idx "+vi+" ID "+(vi>=0?ids[vi]:"-")+" pt "+(vi>=0?pts[vi].ToString():""));
}
sb.AppendLine("all IDs: "+string.Join(",",ids.Select((x,i)=>x+(((bool)ext[i])?"e":""))));
Console.WriteLine(sb.ToString());
