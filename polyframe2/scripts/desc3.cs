using Grasshopper; using Grasshopper.Kernel;
var sb=new System.Text.StringBuilder();
foreach(var n in new[]{"Inspect PFFace","Visualize Deviation"}){
 foreach(var q in Instances.ComponentServer.ObjectProxies.Where(x=>x.Desc.Name==n && !x.Obsolete)){ var o=q.CreateInstance() as IGH_Component; if(o==null) continue;
  sb.AppendLine("## "+n+" "+q.Guid+" : "+q.Desc.Description.Replace("\n"," "));
  foreach(var i in o.Params.Input) sb.AppendLine("  in  "+i.Name+" "+i.TypeName+" "+i.Access+" : "+i.Description.Replace("\n"," "));
  foreach(var i in o.Params.Output) sb.AppendLine("  out "+i.Name+" "+i.TypeName+" "+i.Access+" : "+i.Description.Replace("\n"," "));
 }}
Console.WriteLine(sb.ToString());
