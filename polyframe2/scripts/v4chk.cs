using Grasshopper; using Grasshopper.Kernel; using Grasshopper.Kernel.Types; using Rhino.Geometry;
foreach(var f in new[]{"friend-AP8-diagrid-evenload-4ring"}){
 var io=new GH_DocumentIO(); io.Open("C:/Users/gonza/Documents/GitHub/pyramid-roof/polyframe2/"+f+".gh"); var d=io.Document; d.Enabled=true; d.NewSolution(false,GH_SolutionMode.Silent);
 foreach(var pp in d.Objects.OfType<IGH_Component>().Where(c=>c.Name=="PFPipe")){
  bool B=pp.Params.Input[0].Sources.Any(s=>s.Attributes.GetTopLevel.DocObject.Name=="PFPerp");
  var ax=pp.Params.Output.First(o=>o.Name=="Axes").VolatileData.AllData(true).Select(x=>((GH_Line)x).Value).ToList();
  var nodes=new List<Point3d>(); foreach(var l in ax) foreach(var p in new[]{l.From,l.To}) if(!nodes.Any(q=>q.DistanceTo(p)<1)) nodes.Add(p);
  var row=nodes.Where(p=>Math.Abs(p.Y)<300 && p.X>0).OrderBy(p=>p.X).Select(p=>"("+(p.X/1000).ToString("0.00")+", z "+(p.Z/1000).ToString("0.00")+")");
  // closest distinct node pair
  double mn=1e9; for(int i=0;i<nodes.Count;i++) for(int j=i+1;j<nodes.Count;j++){ var dd=nodes[i].DistanceTo(nodes[j]); if(dd<mn) mn=dd; }
  int close=0; for(int i=0;i<nodes.Count;i++) for(int j=i+1;j<nodes.Count;j++) if(nodes[i].DistanceTo(nodes[j])<200) close++;
  Console.WriteLine(f+(B?" stage B":" stage A")+": nodes "+nodes.Count+" closest node pair "+mn.ToString("0")+" mm, pairs <200 mm: "+close+" | nodes along +x: "+string.Join(" ",row));
 }
 d.Enabled=false; d.Dispose();
}
