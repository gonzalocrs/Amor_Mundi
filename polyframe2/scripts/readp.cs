using Grasshopper; using Grasshopper.Kernel; using Rhino.Geometry;
var TAGS=new[]{"PERP"};
var sb=new System.Text.StringBuilder();
var doc=Instances.ActiveCanvas.Document;
IGH_Component C(string nn)=>doc.Objects.OfType<IGH_Component>().FirstOrDefault(c=>c.NickName==nn);
List<object> D(IGH_Component c,string n)=> c.Params.Output.First(o=>o.Name==n).VolatileData.AllData(true).Select(g=>g.ScriptVariable()).ToList();
foreach(var c in doc.Objects.OfType<IGH_Component>()) if(c.RuntimeMessageLevel!=GH_RuntimeMessageLevel.Blank) sb.AppendLine("msg "+c.NickName+": "+c.RuntimeMessageLevel+" "+string.Join(" | ",c.RuntimeMessages(GH_RuntimeMessageLevel.Error).Concat(c.RuntimeMessages(GH_RuntimeMessageLevel.Warning)).Concat(c.RuntimeMessages(GH_RuntimeMessageLevel.Remark))));
foreach(var tag in TAGS){
 var ie=C("E_"+tag); var iv2=C("V_"+tag); if(ie==null){sb.AppendLine(tag+" missing"); continue;}
 var F=D(ie,"Force").Select(x=>Convert.ToDouble(x)).ToList(); var X=D(ie,"External").Select(x=>Convert.ToInt32(x)).ToList(); var L=D(ie,"Line").Cast<Line>().ToList();
 var internalF=new List<double>(); var lens=new List<double>();
 for(int i=0;i<F.Count;i++) if(X[i]==0){ internalF.Add(F[i]); lens.Add(L[i].Length);} 
 var P=D(iv2,"Point").Cast<Point3d>().ToList(); var VX=D(iv2,"External").Select(x=>(bool)x).ToList();
 var ip=P.Where((p,i)=>!VX[i]).ToList(); var bb=ip.Count>0?new BoundingBox(ip):BoundingBox.Empty;
 sb.AppendLine(tag+": halfedges "+F.Count+" internal "+internalF.Count+" C "+internalF.Count(f=>f>1e-9)+" T "+internalF.Count(f=>f< -1e-9)+" Fmin "+internalF.DefaultIfEmpty(0).Min().ToString("0.###")+" Fmax "+internalF.DefaultIfEmpty(0).Max().ToString("0.###")+" Lmin "+lens.DefaultIfEmpty(0).Min().ToString("0.#")+" Lmax "+lens.DefaultIfEmpty(0).Max().ToString("0.#")+" | verts "+ip.Count+" bbox "+bb.Min+" .. "+bb.Max);
}
{var lo=C("LO"); if(lo!=null){ var f=lo.GetType().GetField("solved",System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.NonPublic|System.Reflection.BindingFlags.Public); sb.AppendLine("solvedflag "+f?.GetValue(lo));}}
foreach(var tag in TAGS){
 var ie=C("E_"+tag); if(ie==null) continue;
 var F=D(ie,"Force").Select(x=>Convert.ToDouble(x)).ToList(); var X=D(ie,"External").Select(x=>Convert.ToInt32(x)).ToList(); var L=D(ie,"Line").Cast<Line>().ToList();
 var nodes=new List<Point3d>(); var sum=new List<Vector3d>(); var ext=new List<Vector3d>(); var deg=new List<int>();
 int Idx(Point3d p){ for(int i=0;i<nodes.Count;i++) if(nodes[i].DistanceTo(p)<1e-3) return i; nodes.Add(p); sum.Add(Vector3d.Zero); ext.Add(Vector3d.Zero); deg.Add(0); return nodes.Count-1; }
 for(int i=0;i<F.Count;i++){ if(X[i]!=0) continue; var a=Idx(L[i].From); var b=Idx(L[i].To); var u=L[i].To-L[i].From; if(u.Length<1e-9) continue; u.Unitize();
   // half edge counted twice -> half weight
   sum[a]+= -0.5*F[i]*u; sum[b]+= 0.5*F[i]*u; deg[a]++; deg[b]++; }
 // external lines: direction from node
 for(int i=0;i<F.Count;i++){ if(X[i]==0) continue; int a=-1; for(int k=0;k<nodes.Count;k++){ if(nodes[k].DistanceTo(L[i].From)<1e-3){a=k;break;} } if(a<0) for(int k=0;k<nodes.Count;k++){ if(nodes[k].DistanceTo(L[i].To)<1e-3){a=k;break;} } if(a<0) continue; var v=nodes[a].DistanceTo(L[i].From)<1e-3? L[i].To-L[i].From : L[i].From-L[i].To; ext[a]+=v; }
 sb.AppendLine(tag+" nodes "+nodes.Count);
 var order=Enumerable.Range(0,nodes.Count).OrderByDescending(i=>nodes[i].Z).ToList();
 foreach(var i in order.Take(3).Concat(order.Skip(nodes.Count-6)))
   sb.AppendLine("  node "+nodes[i].ToString()+" deg(he) "+deg[i]+" P=-sum(bar on node) "+(-sum[i]).ToString()+" extLineDir "+ext[i].ToString());
}

Console.WriteLine(sb.ToString());
