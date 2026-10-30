using Grasshopper; using Grasshopper.Kernel; using Grasshopper.Kernel.Types; using Rhino.Geometry;
var d=Instances.ActiveCanvas.Document;
var bp=(Grasshopper.Kernel.Parameters.Param_Brep)d.Objects.First(o=>o.Name=="Brep");
var bs=bp.PersistentData.AllData(true).Select(g=>((GH_Brep)g).Value).ToList();
var low=new List<Point3d>(); var top=new List<Point3d>();
void AddU(List<Point3d> l,Point3d p){ if(!l.Any(q=>q.DistanceTo(p)<1)) l.Add(p); }
foreach(var b in bs) foreach(var v in b.Vertices){ if(v.Location.Z<-1) AddU(low,v.Location); else AddU(top,v.Location); }
Console.WriteLine("breps "+bs.Count+" low pts "+low.Count+": "+string.Join(" ",low.Select(p=>"("+p.X.ToString("0")+","+p.Y.ToString("0")+","+p.Z.ToString("0")+")")));
var bb=new BoundingBox(top); Console.WriteLine("top pts "+top.Count+" bbox "+bb.Min+" .. "+bb.Max);
// hull of top points (2D)
var hull=new List<Point3d>(); var pts=top.OrderBy(p=>p.X).ThenBy(p=>p.Y).ToList();
double cr(Point3d o,Point3d a,Point3d b)=>(a.X-o.X)*(b.Y-o.Y)-(a.Y-o.Y)*(b.X-o.X);
var H=new List<Point3d>(); foreach(var p in pts){ while(H.Count>=2&&cr(H[H.Count-2],H[H.Count-1],p)<=1e-6) H.RemoveAt(H.Count-1); H.Add(p);} int t=H.Count+1; for(int i=pts.Count-2;i>=0;i--){ var p=pts[i]; while(H.Count>=t&&cr(H[H.Count-2],H[H.Count-1],p)<=1e-6) H.RemoveAt(H.Count-1); H.Add(p);} 
Console.WriteLine("top hull: "+string.Join(" ",H.Select(p=>"("+p.X.ToString("0")+","+p.Y.ToString("0")+")")));
// face types by z range and plane normal for faces with low pts
var groups=bs.GroupBy(b=>b.Faces.Count+"f "+(b.IsSolid?"solid":"open")+" lowpts "+b.Vertices.Count(v=>v.Location.Z<-1)).Select(g=>g.Key+" x"+g.Count());
Console.WriteLine(string.Join("\n",groups));
