using Grasshopper; using Grasshopper.Kernel; using Grasshopper.Kernel.Types; using Rhino.Geometry;
var d=Instances.ActiveCanvas.Document; var pp=d.Objects.OfType<IGH_Component>().Where(c=>c.Name=="PFPipe").Last();
var ax=pp.Params.Output.First(o=>o.Name=="Axes").VolatileData.AllData(true).Select(x=>((GH_Line)x).Value).ToList();
var nodes=new List<Point3d>(); foreach(var l in ax) foreach(var p in new[]{l.From,l.To}) if(!nodes.Any(q=>q.DistanceTo(p)<1)) nodes.Add(p);
// group nodes by plan radius on the x-axis sector (|y| small) to see ring layers
foreach(var g in nodes.Where(p=>Math.Abs(p.Y)<400 && p.X>0).OrderBy(p=>p.X)) Console.WriteLine("node x "+(g.X/1000).ToString("0.00")+" z "+(g.Z/1000).ToString("0.00"));
