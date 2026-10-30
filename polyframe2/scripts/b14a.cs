double NN=1.2; double DD=375; double VS=1; double ADS=1; double HX=5000; double[] SUPT=new[]{0.125,0.375,0.625,0.875};
#include
#form
var ex=Add("Explode PFoam"); W(vc,"PFoam",ex,"PFoam"); var sp=Add("Separate PFEdges By Type"); W(ex,"PFEdges",sp,"PFEdge"); var ie=Add("Inspect PFEdge"); W(sp,"Internal",ie,"PFEdge");
var iv=Add("Inspect PFVertex"); W(ex,"PFVertices",iv,"PFVertex");
var pf=Add("PFPerp"); W(vc,"PFoam",pf,"PFoam"); Int(pf,"Max Iteration",1); Num(pf,"Deviation",0.01); Num(pf,"Minimum Edge Length",0);
Solve(); sb.Append("PFPerp-1-step deviation "+string.Join(",",D(pf,"Deviation"))+" msg "+string.Join("|",pf.RuntimeMessages(GH_RuntimeMessageLevel.Warning).Concat(pf.RuntimeMessages(GH_RuntimeMessageLevel.Remark)))+" | ");
var F=D(ie,"Force").Select(x=>Convert.ToDouble(x)).ToList(); var P=D(iv,"Point").Cast<Point3d>().ToList(); var X=D(iv,"External").Select(x=>(bool)x).ToList();
var ip=P.Where((p,i)=>!X[i]).ToList();
sb.Append("n "+NN+" d "+DD+": bars "+F.Count/2+" T "+F.Count(f=>f<-1e-9)/2+" apex "+ip.Max(p=>p.Z).ToString("0")+" ms "+sw.ElapsedMilliseconds);
Console.WriteLine(sb.ToString());
