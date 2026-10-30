using Grasshopper; using Grasshopper.Kernel;
var sb=new System.Text.StringBuilder();
foreach(var n in new[]{"Dispatch","Smaller Than","Length","Mass Addition","Unit Z","Line"}){
 foreach(var q in Instances.ComponentServer.ObjectProxies.Where(x=>x.Desc.Name==n && !x.Obsolete && x.Desc.Category!="Kangaroo2")){ var o=q.CreateInstance() as IGH_Component; if(o==null) continue;
  sb.AppendLine("## "+n+" ("+q.Desc.Category+"/"+q.Desc.SubCategory+") "+q.Guid+" IN "+string.Join(", ",o.Params.Input.Select(i=>i.Name+":"+i.TypeName))+" OUT "+string.Join(", ",o.Params.Output.Select(i=>i.Name)));
 }}
Console.WriteLine(sb.ToString());
