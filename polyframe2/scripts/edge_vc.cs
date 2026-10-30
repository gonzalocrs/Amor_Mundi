using Grasshopper; using Grasshopper.Kernel; using Rhino.Geometry;
var sb=new System.Text.StringBuilder();
var doc=Instances.ActiveCanvas.Document;
IGH_Component C(string nn)=>doc.Objects.OfType<IGH_Component>().FirstOrDefault(c=>c.NickName==nn);
List<object> D(IGH_Component c,string n)=> c.Params.Output.First(o=>o.Name==n).VolatileData.AllData(true).Select(g=>g.ScriptVariable()).ToList();
var ie=C("E_VC"); var X=D(ie,"External").Select(x=>Convert.ToInt32(x)).ToList(); var L=D(ie,"Line").Cast<Line>().ToList(); var F=D(ie,"Force").Select(x=>Convert.ToDouble(x)).ToList();
var bars=new List<Line>(); var fs=new List<double>(); for(int i=0;i<L.Count;i++) if(X[i]==0 && !bars.Any(b=>(b.From.DistanceTo(L[i].To)<1e-3&&b.To.DistanceTo(L[i].From)<1e-3)||(b.From.DistanceTo(L[i].From)<1e-3&&b.To.DistanceTo(L[i].To)<1e-3))){ bars.Add(L[i]); fs.Add(F[i]); }
sb.AppendLine("bars "+bars.Count);
// node valence
var nodes=new List<Point3d>(); var val=new List<int>(); void Addn(Point3d p){ for(int i=0;i<nodes.Count;i++) if(nodes[i].DistanceTo(p)<1e-3){val[i]++;return;} nodes.Add(p); val.Add(1);} foreach(var b in bars){Addn(b.From);Addn(b.To);}
sb.AppendLine("valence hist "+string.Join(",",val.GroupBy(v=>v).OrderBy(g=>g.Key).Select(g=>g.Key+":"+g.Count())));
// free-edge inset: in plan, for side y=+5000 (between supports (-5000,5000),(5000,5000)), the max y of any bar point sampled; inset = 5000 - max y among non-support region near middle |x|<1000
double maxY=double.MinValue; foreach(var b in bars) for(double t=0;t<=1;t+=0.01){ var p=b.PointAt(t); if(Math.Abs(p.X)<500) maxY=Math.Max(maxY,p.Y);} 
sb.AppendLine("at mid-side (|x|<0.5 m) outermost bar y = "+maxY.ToString("0")+" -> curves in "+(5000-maxY).ToString("0")+" mm");
double maxX=double.MinValue; foreach(var b in bars) for(double t=0;t<=1;t+=0.01){ var p=b.PointAt(t); if(Math.Abs(p.Y)<500) maxX=Math.Max(maxX,p.X);} 
sb.AppendLine("other side: outermost x = "+maxX.ToString("0")+" -> curves in "+(5000-maxX).ToString("0")+" mm");
var zs=nodes.Select(p=>p.Z).ToList(); sb.AppendLine("node z max "+zs.Max().ToString("0")+" ; forces range "+fs.Min().ToString("0")+".."+fs.Max().ToString("0"));
// angle of bars from horizontal
sb.AppendLine("bar slope deg: max "+bars.Max(b=>Math.Atan2(Math.Abs(b.To.Z-b.From.Z),new Vector2d(b.To.X-b.From.X,b.To.Y-b.From.Y).Length)*180/Math.PI).ToString("0.0")+" min "+bars.Min(b=>Math.Atan2(Math.Abs(b.To.Z-b.From.Z),new Vector2d(b.To.X-b.From.X,b.To.Y-b.From.Y).Length)*180/Math.PI).ToString("0.0"));
Console.WriteLine(sb.ToString());
