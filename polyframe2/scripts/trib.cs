using Grasshopper; using Grasshopper.Kernel; using Grasshopper.Kernel.Special; using Grasshopper.Kernel.Types; using Rhino.Geometry;
IGH_Component Mk(GH_Document d,string name){ var p=Instances.ComponentServer.ObjectProxies.First(q=>q.Desc.Name==name && !q.Obsolete && typeof(IGH_Component).IsAssignableFrom(q.Type)); var o=(IGH_Component)p.CreateInstance(); o.CreateAttributes(); d.AddObject(o,false); return o; }
List<T> O<T>(IGH_Component c,string n)=>c.Params.Output.First(o=>o.Name==n).VolatileData.AllData(true).Select(x=>(T)x.ScriptVariable()).ToList();
foreach(var f in new[]{"friend-AP8-diagrid","friend-16-diagrid"}){
 var io=new GH_DocumentIO(); io.Open(@"C:\Users\gonza\Documents\GitHub\pyramid-roof\polyframe2\"+f+".gh"); var d=io.Document; d.Enabled=true;
 var perp=d.Objects.OfType<IGH_Component>().First(c=>c.Name=="PFPerp");
 var ex=Mk(d,"Explode PFoam"); ex.Params.Input[0].AddSource(perp.Params.Output[0]);
 var ie=Mk(d,"Inspect PFEdge"); ie.Params.Input[0].AddSource(ex.Params.Output[1]);
 var iff=Mk(d,"Inspect PFFace"); iff.Params.Input[0].AddSource(ex.Params.Output[2]);
 d.NewSolution(false,GH_SolutionMode.Silent);
 var L=O<Line>(ie,"Line"); var X=O<int>(ie,"External"); var F=O<double>(ie,"Force");
 // nodes
 var nodes=new List<Point3d>(); int Id(Point3d p){ for(int i=0;i<nodes.Count;i++) if(nodes[i].DistanceTo(p)<1) return i; nodes.Add(p); return nodes.Count-1; }
 var bars=new List<(int,int)>(); for(int i=0;i<L.Count;i++) if(X[i]==0){ int a=Id(L[i].From), b=Id(L[i].To); if(a!=b && !bars.Contains((a,b)) && !bars.Contains((b,a))) bars.Add((a,b)); }
 // PF design load per node = vertical external force edges (load arrows) magnitude
 var design=new double[nodes.Count]; var isSup=new bool[nodes.Count];
 for(int i=0;i<L.Count;i++) if(X[i]==2){ int a=-1; for(int k=0;k<nodes.Count;k++) if(nodes[k].DistanceTo(L[i].From)<1||nodes[k].DistanceTo(L[i].To)<1){a=k;break;} if(a<0) continue; var v=L[i].Direction; v.Unitize(); if(Math.Abs(v.Z)>0.999) design[a]+=Math.Abs(F[i]); else isSup[a]=true; }
 // tributary area of the net cells: form faces = polygons of the net (internal faces only, each counted once)
 var fm=O<Mesh>(iff,"Mesh"); var fx=O<bool>(iff,"External");
 var trib=new double[nodes.Count]; var seen=new HashSet<string>(); double totA=0; int nf=0;
 for(int i=0;i<fm.Count;i++){ if(fx[i]) continue; var m=fm[i]; var vs=m.Vertices.Select(v=>(Point3d)v).ToList(); var key=string.Join(",",vs.Select(p=>Id(p)).OrderBy(x=>x)); if(seen.Contains(key)) continue; seen.Add(key); double A=AreaMassProperties.Compute(m).Area; var ids=vs.Select(p=>Id(p)).Distinct().ToList(); foreach(var id in ids) trib[id]+=A/ids.Count; totA+=A; nf++; }
 double sD=design.Sum(), sT=trib.Sum();
 var ratio=new List<(double r,Point3d p)>(); for(int i=0;i<nodes.Count;i++){ if(isSup[i]||design[i]<=0) continue; ratio.Add(((trib[i]/sT)/(design[i]/sD),nodes[i])); }
 var rs=ratio.Select(x=>x.r).OrderBy(x=>x).ToList();
 Console.WriteLine(f+": nodes "+nodes.Count+" bars "+bars.Count+" net cells "+nf+" surface "+(totA/1e6).ToString("0.0")+" m2 | real/design load per node: min "+rs.First().ToString("0.00")+" median "+rs[rs.Count/2].ToString("0.00")+" max "+rs.Last().ToString("0.00")+" | nodes off by >2x: "+rs.Count(r=>r>2||r<0.5)+" of "+rs.Count);
 foreach(var x in ratio.OrderByDescending(x=>x.r).Take(3)) Console.WriteLine("   most under-designed: x"+x.r.ToString("0.0")+" at ("+(x.p.X/1000).ToString("0.0")+","+(x.p.Y/1000).ToString("0.0")+","+(x.p.Z/1000).ToString("0.0")+")");
 foreach(var x in ratio.OrderBy(x=>x.r).Take(2)) Console.WriteLine("   most over-designed: x"+x.r.ToString("0.00")+" at ("+(x.p.X/1000).ToString("0.0")+","+(x.p.Y/1000).ToString("0.0")+","+(x.p.Z/1000).ToString("0.0")+")");
 d.Enabled=false; d.Dispose();
}
