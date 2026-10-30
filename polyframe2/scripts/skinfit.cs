using Grasshopper; using Grasshopper.Kernel; using Rhino.Geometry;
IGH_Component Mk(GH_Document d,string name){ var p=Instances.ComponentServer.ObjectProxies.First(q=>q.Desc.Name==name && !q.Obsolete && typeof(IGH_Component).IsAssignableFrom(q.Type)); var o=(IGH_Component)p.CreateInstance(); o.CreateAttributes(); d.AddObject(o,false); return o; }
foreach(var f in new[]{"friend-12-feet-2m-corners-opentop","friend-20-feet-2m-corners-opentop"}){
 var io=new GH_DocumentIO(); io.Open(@"C:\Users\gonza\Documents\GitHub\pyramid-roof\polyframe2\"+f+".gh"); var d=io.Document; d.Enabled=true;
 var perp=d.Objects.OfType<IGH_Component>().First(c=>c.Name=="PFPerp");
 var ex=Mk(d,"Explode PFoam"); ex.Params.Input[0].AddSource(perp.Params.Output[0]); var ie=Mk(d,"Inspect PFEdge"); ie.Params.Input[0].AddSource(ex.Params.Output[1]);
 d.NewSolution(false,GH_SolutionMode.Silent);
 var L=ie.Params.Output.First(o=>o.Name=="Line").VolatileData.AllData(true).Select(x=>(Line)x.ScriptVariable()).ToList(); var X=ie.Params.Output.First(o=>o.Name=="External").VolatileData.AllData(true).Select(x=>Convert.ToInt32(x.ScriptVariable())).ToList();
 var nodes=new List<Point3d>(); int Id(Point3d p){ for(int i=0;i<nodes.Count;i++) if(nodes[i].DistanceTo(p)<1) return i; nodes.Add(p); return nodes.Count-1; }
 var bars=new List<(int a,int b)>(); var seen=new HashSet<(int,int)>(); for(int i=0;i<L.Count;i++) if(X[i]==0){ int a=Id(L[i].From), b=Id(L[i].To); if(a==b) continue; var k=(Math.Min(a,b),Math.Max(a,b)); if(seen.Add(k)) bars.Add(k); }
 var pts=nodes.ToList(); double zc=nodes.Max(p=>p.Z), rc=nodes.Where(p=>p.Z>zc-50).Max(p=>Math.Max(Math.Abs(p.X),Math.Abs(p.Y)));
 Console.WriteLine(f+": crown z "+zc.ToString("0")+" crown half-width (square) "+rc.ToString("0")+" | outer foot half-width "+nodes.Where(p=>p.Z<100).Max(p=>Math.Max(Math.Abs(p.X),Math.Abs(p.Y))).ToString("0"));
 const double C=200; // perpendicular clearance between bar centreline and skin, mm
 double BaseFor(double H){ double lo=5000, hi=40000; for(int it=0;it<60;it++){ double a=(lo+hi)/2; double th=Math.Atan2(H,a); bool ok=pts.All(p=>{ double m=Math.Max(Math.Abs(p.X),Math.Abs(p.Y)); double zp=H*(1-m/a); return (zp-p.Z)*Math.Cos(th)>=C-1e-6; }); if(ok) hi=a; else lo=a; } return hi; }
 foreach(var H in new[]{7500.0,8000,8500,8930,9500,10000,11000,12000}){ double a=BaseFor(H); double th=Math.Atan2(H,a)*180/Math.PI; double gapMax=pts.Max(p=>{ double m=Math.Max(Math.Abs(p.X),Math.Abs(p.Y)); return (H*(1-m/a)-p.Z)*Math.Cos(th*Math.PI/180); }); 
   // binding node
   var bind=pts.OrderBy(p=>{ double m=Math.Max(Math.Abs(p.X),Math.Abs(p.Y)); return (H*(1-m/a)-p.Z)*Math.Cos(th*Math.PI/180);}).First();
   Console.WriteLine("  apex "+(H/1000).ToString("0.00")+" m -> base "+(2*a/1000).ToString("0.00")+" m square, slope "+th.ToString("0.0")+" deg, eave overhang past wall "+((a-5000)/1000).ToString("0.00")+" m, max gap "+(gapMax/1000).ToString("0.00")+" m, tight at z "+(bind.Z/1000).ToString("0.0")+" r "+(Math.Max(Math.Abs(bind.X),Math.Abs(bind.Y))/1000).ToString("0.0")); }
 d.Enabled=false; d.Dispose(); }
