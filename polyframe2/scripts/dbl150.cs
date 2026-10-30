using Grasshopper; using Grasshopper.Kernel; using Grasshopper.Kernel.Types; using Rhino.Geometry;
var d=Instances.ActiveCanvas.Document;
foreach(var pp in d.Objects.OfType<IGH_Component>().Where(c=>c.Name=="PFPipe")){
 var ax=pp.Params.Output.First(o=>o.Name=="Axes").VolatileData.AllData(true).Select(x=>((GH_Line)x).Value).ToList();
 int pairs=0; var ex=new List<string>(); int shortb=ax.Count(l=>l.Length<150);
 for(int i=0;i<ax.Count;i++) for(int j=i+1;j<ax.Count;j++){ var a=ax[i]; var b=ax[j]; if(a.Length<300||b.Length<300) continue; var da=a.Direction; da.Unitize(); var db=b.Direction; db.Unitize(); if(Math.Abs(da*db)<0.995) continue; double dist=b.PointAt(0.5).DistanceTo(a.ClosestPoint(b.PointAt(0.5),false)); if(dist<150){ pairs++; if(ex.Count<4) ex.Add("("+(a.PointAt(0.5).X/1000).ToString("0.0")+","+(a.PointAt(0.5).Y/1000).ToString("0.0")+","+(a.PointAt(0.5).Z/1000).ToString("0.0")+") gap "+dist.ToString("0")+"mm len "+a.Length.ToString("0")+"/"+b.Length.ToString("0")); } }
 Console.WriteLine("bars "+ax.Count+" short(<150mm) "+shortb+" near-parallel pairs closer than 250 mm: "+pairs+"  e.g. "+string.Join(" ; ",ex));
}
