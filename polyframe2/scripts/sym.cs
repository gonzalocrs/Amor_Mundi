using Grasshopper; using Grasshopper.Kernel; using Grasshopper.Kernel.Types; using Rhino.Geometry;
var d=Instances.ActiveCanvas.Document; int idx=0;
foreach(var pp in d.Objects.OfType<IGH_Component>().Where(c=>c.Name=="PFPipe")){
 var ax=pp.Params.Output.First(o=>o.Name=="Axes").VolatileData.AllData(true).Select(x=>((GH_Line)x).Value).ToList();
 var nodes=new List<Point3d>(); foreach(var l in ax) foreach(var p in new[]{l.From,l.To}) if(!nodes.Any(q=>q.DistanceTo(p)<1)) nodes.Add(p);
 var c=new Point3d(nodes.Average(p=>p.X),nodes.Average(p=>p.Y),0);
 double Err(Func<Point3d,Point3d> m){ return nodes.Max(p=>{ var q=m(p); return nodes.Min(n=>n.DistanceTo(q)); }); }
 Func<Point3d,Point3d> mx=p=>new Point3d(2*c.X-p.X,p.Y,p.Z), my=p=>new Point3d(p.X,2*c.Y-p.Y,p.Z), md=p=>new Point3d(c.X+(p.Y-c.Y),c.Y+(p.X-c.X),p.Z), r90=p=>new Point3d(c.X-(p.Y-c.Y),c.Y+(p.X-c.X),p.Z);
 Console.WriteLine((idx++==0?"stage A":"stage B")+" nodes "+nodes.Count+" centre ("+c.X.ToString("0")+","+c.Y.ToString("0")+")  worst mismatch mm: mirror-x "+Err(mx).ToString("0")+"  mirror-y "+Err(my).ToString("0")+"  mirror-diagonal "+Err(md).ToString("0")+"  rotate-90 "+Err(r90).ToString("0"));
}
