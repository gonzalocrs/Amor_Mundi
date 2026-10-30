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
