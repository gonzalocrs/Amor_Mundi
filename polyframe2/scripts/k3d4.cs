using Grasshopper;
foreach(var q in Instances.ComponentServer.ObjectProxies.Where(x=>x.Desc.Category.StartsWith("Karamba") && !x.Obsolete && (x.Desc.SubCategory.Contains("Result")||x.Desc.SubCategory.Contains("Algorithm")||x.Desc.SubCategory.Contains("Model"))).OrderBy(x=>x.Desc.SubCategory)){
 var o=q.CreateInstance() as Grasshopper.Kernel.IGH_Component; if(o==null) continue;
 Console.WriteLine(q.Desc.SubCategory+" | "+q.Desc.Name+" | "+q.Guid+" IN "+string.Join(", ",o.Params.Input.Select(i=>i.Name))+" OUT "+string.Join(", ",o.Params.Output.Select(i=>i.Name))); }
