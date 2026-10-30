using Grasshopper; using Grasshopper.Kernel;
foreach(var n in new[]{"Matrix Analysis Generic Structures"}){
 foreach(var q in Instances.ComponentServer.ObjectProxies.Where(x=>x.Desc.Name==n && !x.Obsolete)){ var o=q.CreateInstance() as IGH_Component;
  Console.WriteLine("## "+n+" : "+q.Desc.Description.Replace("\n"," "));
  foreach(var i in o.Params.Input) Console.WriteLine("  in  "+i.Name+" "+i.TypeName+" "+i.Access+" : "+i.Description.Replace("\n"," "));
  foreach(var i in o.Params.Output) Console.WriteLine("  out "+i.Name+" "+i.TypeName+" "+i.Access+" : "+i.Description.Replace("\n"," "));
 }}
