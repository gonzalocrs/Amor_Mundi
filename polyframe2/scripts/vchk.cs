using Grasshopper; using Grasshopper.Kernel; using Grasshopper.Kernel.Types; using Rhino.Geometry;
var d=Instances.ActiveCanvas.Document;
IGH_Component Add(string name){ var p=Instances.ComponentServer.ObjectProxies.First(q=>q.Desc.Name==name && !q.Obsolete && typeof(IGH_Component).IsAssignableFrom(q.Type)); var o=(IGH_Component)p.CreateInstance(); o.CreateAttributes(); d.AddObject(o,false); return o; }
foreach(var nm in new[]{"Algebraic Vertex Constraints","PFPerp"}){
 var src=d.Objects.OfType<IGH_Component>().First(c=>c.Name==nm);
 var ex=Add("Explode PFoam"); ex.Params.Input[0].AddSource(src.Params.Output.Last(o=>o.TypeName.Contains("PFoam")||o.Name=="PFoam"));
 var sp=Add("Separate PFEdges By Type"); sp.Params.Input[0].AddSource(ex.Params.Output[1]);
 var ie=Add("Inspect PFEdge"); ie.Params.Input[0].AddSource(sp.Params.Output[0]);
 d.NewSolution(false);
 var F=ie.Params.Output.First(o=>o.Name=="Force").VolatileData.AllData(true).Select(x=>((GH_Number)x).Value).ToList();
 var L=ie.Params.Output.First(o=>o.Name=="Line").VolatileData.AllData(true).Select(x=>((GH_Line)x).Value).ToList();
 Console.WriteLine(nm+" src out "+src.Params.Output.Last(o=>o.Name=="PFoam").Name+" halfedges "+F.Count+" T "+F.Count(f=>f<-1e-9)+" min "+F.Min().ToString("0")+" lens of T: "+string.Join(",",F.Select((f,i)=>f<-1e-9?L[i].Length.ToString("0"):null).Where(s=>s!=null)));
 d.RemoveObject(ex,false); d.RemoveObject(sp,false); d.RemoveObject(ie,false);
}
d.NewSolution(false);
