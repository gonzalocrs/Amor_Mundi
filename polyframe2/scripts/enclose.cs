using Grasshopper; using Grasshopper.Kernel; using Rhino.Geometry;
IGH_Component Mk(GH_Document d,string name){ var p=Instances.ComponentServer.ObjectProxies.First(q=>q.Desc.Name==name && !q.Obsolete && typeof(IGH_Component).IsAssignableFrom(q.Type)); var o=(IGH_Component)p.CreateInstance(); o.CreateAttributes(); d.AddObject(o,false); return o; }
foreach(var f in new[]{"friend-12-feet-2m-corners-opentop"}){
 var io=new GH_DocumentIO(); io.Open(@"C:\Users\gonza\Documents\GitHub\pyramid-roof\polyframe2\"+f+".gh"); var d=io.Document; d.Enabled=true;
 var perp=d.Objects.OfType<IGH_Component>().First(c=>c.Name=="PFPerp");
 var ex=Mk(d,"Explode PFoam"); ex.Params.Input[0].AddSource(perp.Params.Output[0]); var ie=Mk(d,"Inspect PFEdge"); ie.Params.Input[0].AddSource(ex.Params.Output[1]);
 d.NewSolution(false,GH_SolutionMode.Silent);
 var L=ie.Params.Output.First(o=>o.Name=="Line").VolatileData.AllData(true).Select(x=>(Line)x.ScriptVariable()).ToList(); var X=ie.Params.Output.First(o=>o.Name=="External").VolatileData.AllData(true).Select(x=>Convert.ToInt32(x.ScriptVariable())).ToList();
 var nodes=new List<Point3d>(); int Id(Point3d p){ for(int i=0;i<nodes.Count;i++) if(nodes[i].DistanceTo(p)<1) return i; nodes.Add(p); return nodes.Count-1; }
 var bars=new List<(int a,int b)>(); var seen=new HashSet<(int,int)>(); for(int i=0;i<L.Count;i++) if(X[i]==0){ int a=Id(L[i].From), b=Id(L[i].To); if(a==b) continue; var k=(Math.Min(a,b),Math.Max(a,b)); if(seen.Add(k)) bars.Add(k); }
 var free=nodes.Where(p=>p.Z>100).ToList(); double hmin=0, amin=0, gapMax=0, outMax=0; foreach(var p in free){ double m=Math.Max(Math.Abs(p.X),Math.Abs(p.Y)); double h=p.Z/(1-m/5000.0); if(h>hmin) hmin=h; double t=Math.Tan(Math.Atan2(6670,5000)); double a2=m+p.Z/t; if(a2>amin) amin=a2; double zp=6670*(1-m/5000.0); if(p.Z-zp>outMax) outMax=p.Z-zp; if(zp-p.Z>gapMax) gapMax=zp-p.Z; }
 int outside=free.Count(p=>p.Z>6670*(1-Math.Max(Math.Abs(p.X),Math.Abs(p.Y))/5000.0));
 Console.WriteLine(f+": free nodes "+free.Count+" outside 10x10/6.67 pyramid "+outside+" (max "+outMax.ToString("0")+" mm above), max below "+gapMax.ToString("0")+" | enclosing pyramid on same 10x10 base needs apex "+hmin.ToString("0")+" mm | or same 53.1 deg slope needs base "+(2*amin/1000).ToString("0.00")+" m");
 d.Enabled=false; d.Dispose(); }
