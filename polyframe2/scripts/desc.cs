using Grasshopper; using Grasshopper.Kernel;
var sb=new System.Text.StringBuilder();
foreach(var n in new[]{"PFBuild","Algebraic Dual","Algebraic Vertex Constraints","Linear Optimization Solver","Inspect PFCell","Inspect PFVertex","Explode PFoam","Filter PFVertex","PFPipe","Inspect PFEdge","Separate PFEdges By Type","Extrude Point","Delaunay Mesh","Face Boundaries","Point In Curve","Mesh Surface","Face Normals","Polygon"}){
 var p=Instances.ComponentServer.ObjectProxies.Where(x=>x.Desc.Name==n && !x.Obsolete).ToList();
 foreach(var q in p){ var o=q.CreateInstance() as IGH_Component; if(o==null) continue;
  sb.AppendLine("## "+n+" ("+q.Desc.Category+") "+q.Guid+" : "+q.Desc.Description.Replace("\n"," "));
  foreach(var i in o.Params.Input) sb.AppendLine("  in  "+i.Name+" ["+i.NickName+"] "+i.TypeName+" "+i.Access+" opt="+i.Optional+" : "+i.Description.Replace("\n"," "));
  foreach(var i in o.Params.Output) sb.AppendLine("  out "+i.Name+" ["+i.NickName+"] "+i.TypeName+" "+i.Access+" : "+i.Description.Replace("\n"," "));
 }}
Console.WriteLine(sb.ToString());
