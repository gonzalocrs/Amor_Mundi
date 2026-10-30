IGH_Component Rep(IGH_Component src,string outName,string tag){
 var e=Add("Explode PFoam"); W(src,outName,e,"PFoam");
 var ie=Add("Inspect PFEdge"); W(e,"PFEdges",ie,"PFEdge");
 var iv2=Add("Inspect PFVertex"); W(e,"PFVertices",iv2,"PFVertex");
 var t0=sw.ElapsedMilliseconds; Solve(); sb.AppendLine(tag+" solve ms "+(sw.ElapsedMilliseconds-t0));
 foreach(var c in doc.Objects.OfType<IGH_Component>()) if(c.RuntimeMessageLevel!=GH_RuntimeMessageLevel.Blank) sb.AppendLine("  msg "+Msg(c));
 var F=D(ie,"Force").Select(x=>Convert.ToDouble(x)).ToList(); var X=D(ie,"External").Select(x=>Convert.ToInt32(x)).ToList(); var L=D(ie,"Line").Cast<Line>().ToList(); var EID=D(ie,"ID").Select(x=>Convert.ToInt32(x)).ToList();
 var internalF=new List<double>(); var seen=new HashSet<int>(); var lens=new List<double>();
 for(int i=0;i<F.Count;i++) if(X[i]==0){ internalF.Add(F[i]); lens.Add(L[i].Length);} 
 var P=D(iv2,"Point").Cast<Point3d>().ToList(); var VX=D(iv2,"External").Select(x=>(bool)x).ToList();
 var ip=P.Where((p,i)=>!VX[i]).ToList();
 var bb=new BoundingBox(ip);
 sb.AppendLine("  halfedges "+F.Count+" internal "+internalF.Count+" C(+) "+internalF.Count(f=>f>1e-9)+" T(-) "+internalF.Count(f=>f< -1e-9)+" Fmin "+internalF.DefaultIfEmpty(0).Min().ToString("0.###")+" Fmax "+internalF.DefaultIfEmpty(0).Max().ToString("0.###")+" Lmin "+lens.DefaultIfEmpty(0).Min().ToString("0.#")+" Lmax "+lens.DefaultIfEmpty(0).Max().ToString("0.#"));
 sb.AppendLine("  internal verts "+ip.Count+" bbox "+bb.Min+" .. "+bb.Max);
 return ie;
}
