using Grasshopper; using Grasshopper.Kernel;
var sb=new System.Text.StringBuilder();
foreach(var n in new[]{"Triangular","Boundary Surfaces","Cull Pattern","Larger Than","Discontinuity","Merge","Construct Point","Equality","Closest Points","List Item","Square","Populate Geometry"}){
 var p=Instances.ComponentServer.ObjectProxies.Where(x=>x.Desc.Name==n && !x.Obsolete).ToList();
 foreach(var q in p){ var o=q.CreateInstance() as IGH_Component; if(o==null) continue;
  sb.AppendLine("## "+n+" ("+q.Desc.Category+"/"+q.Desc.SubCategory+") "+q.Guid);
  foreach(var i in o.Params.Input) sb.AppendLine("  in  "+i.Name+" ["+i.NickName+"] "+i.TypeName+" "+i.Access);
  foreach(var i in o.Params.Output) sb.AppendLine("  out "+i.Name+" ["+i.NickName+"] "+i.TypeName+" "+i.Access);
 }}
Console.WriteLine(sb.ToString());
