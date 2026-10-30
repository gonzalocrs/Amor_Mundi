using Grasshopper; using Grasshopper.Kernel; using Rhino.Geometry;
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
Console.WriteLine(sb.ToString());
