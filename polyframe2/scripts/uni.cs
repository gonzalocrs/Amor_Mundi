using Grasshopper; using Grasshopper.Kernel; using Grasshopper.Kernel.Special; using Grasshopper.Kernel.Types; using Grasshopper.Kernel.Parameters; using Rhino.Geometry;
IGH_Component Mk(GH_Document d,string name){ var p=Instances.ComponentServer.ObjectProxies.First(q=>q.Desc.Name==name && !q.Obsolete && typeof(IGH_Component).IsAssignableFrom(q.Type)); var o=(IGH_Component)p.CreateInstance(); o.CreateAttributes(); d.AddObject(o,false); return o; }
List<T> O<T>(IGH_Component c,string n)=>c.Params.Output.First(o=>o.Name==n).VolatileData.AllData(true).Select(x=>(T)x.ScriptVariable()).ToList();
(List<double> F, int ki, int si, List<Line> Ls) MA(List<Line> bars,List<Point3d> sup,List<Vector3d> loads,List<Point3d> locs){
 var d=new GH_Document(); var ma=Mk(d,"Matrix Analysis Generic Structures");
 var p0=(Param_Geometry)ma.Params.Input[0]; foreach(var l in bars) p0.PersistentData.Append(new GH_Line(l));
 var p1=(Param_Point)ma.Params.Input[1]; foreach(var s in sup) p1.PersistentData.Append(new GH_Point(s));
 var p2=(Param_Vector)ma.Params.Input[2]; foreach(var v in loads) p2.PersistentData.Append(new GH_Vector(v));
 var p3=(Param_Point)ma.Params.Input[3]; foreach(var s in locs) p3.PersistentData.Append(new GH_Point(s));
 ((Param_Number)ma.Params.Input[4]).PersistentData.Append(new GH_Number(1)); ((Param_Number)ma.Params.Input[5]).PersistentData.Append(new GH_Number(1));
 d.Enabled=true; d.NewSolution(false,GH_SolutionMode.Silent);
 var msgs=string.Join("|",ma.RuntimeMessages(GH_RuntimeMessageLevel.Error).Concat(ma.RuntimeMessages(GH_RuntimeMessageLevel.Warning))); if(msgs.Length>0) Console.WriteLine("  MA msg: "+msgs);
 var F=O<double>(ma,"Forces"); var Ls=O<Line>(ma,"Lines"); var ki=O<int>(ma,"Kinematic Indeterminacy").FirstOrDefault(); var si=O<int>(ma,"Static Indeterminacy").FirstOrDefault();
 d.Enabled=false; d.Dispose(); return (F,ki,si,Ls);
}


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

 // tension sign test once
 var supPts=new List<Point3d>(); for(int i=0;i<nodes.Count;i++) if(isSup[i]) supPts.Add(nodes[i]);
 var barL=bars.Select(b=>new Line(nodes[b.Item1],nodes[b.Item2])).ToList();
 var locs=new List<Point3d>(); var vec=new List<Vector3d>(); double q=7.0; double Wt=0;
 for(int i=0;i<nodes.Count;i++){ if(isSup[i]) continue; double kN=q*trib[i]/1e6; if(kN<=0) continue; locs.Add(nodes[i]); vec.Add(new Vector3d(0,0,-kN)); Wt+=kN; }
 double Wsup=0; for(int i=0;i<nodes.Count;i++) if(isSup[i]) Wsup+=q*trib[i]/1e6;
 var r=MA(barL,supPts,vec,locs);
 Console.WriteLine(f+" UNIFORM 7 kN/m2 on "+(trib.Sum()/1e6).ToString("0.0")+" m2 of cells: load on free nodes "+Wt.ToString("0.0")+" kN (+ "+Wsup.ToString("0.0")+" kN straight into feet) | KI "+r.ki+" SI "+r.si+" | lines "+r.Ls.Count+" forces "+r.F.Count);
 if(r.F.Count>0){ var FL=r.Ls.Zip(r.F,(l,ff)=>(l,ff)).ToList();
  var C=FL.Where(x=>x.ff>1e-6).ToList(); var T=FL.Where(x=>x.ff< -1e-6).ToList();
  Console.WriteLine("  max C "+(C.Count>0?C.Max(x=>x.ff).ToString("0.0"):"-")+" kN | tension entries "+T.Count+" max T "+(T.Count>0?(-T.Min(x=>x.ff)).ToString("0.0"):"0")+" kN | sum|F| "+FL.Sum(x=>Math.Abs(x.ff)).ToString("0"));
  foreach(var x in FL.OrderByDescending(x=>Math.Abs(x.ff)).Where((x,i)=>i%2==0).Take(4)) { var m=x.l.PointAt(0.5); Console.WriteLine("    top |F| "+x.ff.ToString("0.0")+" kN at ("+(m.X/1000).ToString("0.0")+","+(m.Y/1000).ToString("0.0")+","+(m.Z/1000).ToString("0.0")+") len "+(x.l.Length/1000).ToString("0.00")+" m"); }
  foreach(var x in T.OrderBy(x=>x.ff).Where((x,i)=>i%2==0).Take(3)) { var m=x.l.PointAt(0.5); Console.WriteLine("    tension "+(-x.ff).ToString("0.0")+" kN at ("+(m.X/1000).ToString("0.0")+","+(m.Y/1000).ToString("0.0")+","+(m.Z/1000).ToString("0.0")+")"); }
  // reactions at feet from equilibrium
  foreach(var sp in supPts.Take(3)){ var R=new Vector3d(0,0,0); foreach(var x in FL){ Point3d other; if(x.l.From.DistanceTo(sp)<1) other=x.l.To; else if(x.l.To.DistanceTo(sp)<1) other=x.l.From; else continue; var u=sp-other; u.Unitize(); R+=0.5*x.ff*u; }
    var h=new Vector3d(R.X,R.Y,0); var out_=new Vector3d(sp.X,sp.Y,0); out_.Unitize(); Console.WriteLine("    foot ("+(sp.X/1000).ToString("0.0")+","+(sp.Y/1000).ToString("0.0")+"): bars push down "+R.Z.ToString("0.0")+" kN, horizontal "+h.Length.ToString("0.0")+" kN ("+(h*out_>=0?"outward":"inward")+")"); }
 }
 double sD=design.Sum(), sT=trib.Sum();
 var ratio=new List<(double r,Point3d p)>(); for(int i=0;i<nodes.Count;i++){ if(isSup[i]||design[i]<=0) continue; ratio.Add(((trib[i]/sT)/(design[i]/sD),nodes[i])); }
 var rs=ratio.Select(x=>x.r).OrderBy(x=>x).ToList();
/* Console.WriteLine(f+": nodes "+nodes.Count+" bars "+bars.Count+" net cells "+nf+" surface "+(totA/1e6).ToString("0.0")+" m2 | real/design load per node: min "+rs.First().ToString("0.00")+" median "+rs[rs.Count/2].ToString("0.00")+" max "+rs.Last().ToString("0.00")+" | nodes off by >2x: "+rs.Count(r=>r>2||r<0.5)+" of "+rs.Count);
 foreach(var x in ratio.OrderByDescending(x=>x.r).Take(3)) Console.WriteLine("   most under-designed: x"+x.r.ToString("0.0")+" at ("+(x.p.X/1000).ToString("0.0")+","+(x.p.Y/1000).ToString("0.0")+","+(x.p.Z/1000).ToString("0.0")+")");
 foreach(var x in ratio.OrderBy(x=>x.r).Take(2)) Console.WriteLine("   most over-designed: x"+x.r.ToString("0.00")+" at ("+(x.p.X/1000).ToString("0.0")+","+(x.p.Y/1000).ToString("0.0")+","+(x.p.Z/1000).ToString("0.0")+")");
*/ d.Enabled=false; d.Dispose();
}
