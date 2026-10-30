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
 var bins=new int[7]; double[] edges={30,35,45,55,65,80,91}; var horiz=new List<double>();
 foreach(var bb in bars){ var v=nodes[bb.b]-nodes[bb.a]; double ang=Math.Atan2(Math.Sqrt(v.X*v.X+v.Y*v.Y),Math.Abs(v.Z))*180/Math.PI; int k=0; while(ang>edges[k]) k++; bins[k]++; if(ang>65) horiz.Add(v.Length); }
 double zmin=nodes.Min(p=>p.Z); int islandsUp=0, islandsDown=0; double zmax=nodes.Max(p=>p.Z);
 for(int i=0;i<nodes.Count;i++){ var nb=bars.Where(b=>b.a==i||b.b==i).Select(b=>b.a==i?b.b:b.a).ToList(); if(nodes[i].Z>zmin+50 && !nb.Any(j=>nodes[j].Z<nodes[i].Z-1)) islandsUp++; if(nodes[i].Z<zmax-50 && !nb.Any(j=>nodes[j].Z>nodes[i].Z+1)) islandsDown++; }
 Console.WriteLine(f+": bars "+bars.Count+" | angle from vertical <=30:"+bins[0]+" 30-35:"+bins[1]+" 35-45:"+bins[2]+" 45-55:"+bins[3]+" 55-65:"+bins[4]+" 65-80:"+bins[5]+" >80:"+bins[6]+" | bars >65 deg lengths "+(horiz.Count>0? horiz.Min().ToString("0")+"-"+horiz.Max().ToString("0"):"-")+" mm | nodes with no lower neighbour (upright): "+islandsUp+" | no higher neighbour (upside-down): "+islandsDown);
 d.Enabled=false; d.Dispose(); }
