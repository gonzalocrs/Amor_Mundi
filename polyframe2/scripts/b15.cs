double NN=__N__; double DD=__D__; double ROT=__ROT__; double Q=QQ; int LM=LMV; double HX=5000; bool[] PAT=__PAT__;
#force8
#form8
if(LM>0){ In(vc,"PFVertex IDs").RemoveAllSources(); In(vc,"Constraints").RemoveAllSources(); W(lid,"Item",vc,"PFVertex IDs"); In(vc,"PFVertex IDs").DataMapping=GH_DataMapping.Flatten;
 var gp=(Param_Geometry)In(vc,"Constraints"); gp.PersistentData.Clear();
 var wall=new[]{new Point3d(-HX,-HX,0),new Point3d(0,-HX,0),new Point3d(HX,-HX,0),new Point3d(HX,0,0),new Point3d(HX,HX,0),new Point3d(0,HX,0),new Point3d(-HX,HX,0),new Point3d(-HX,0,0)};
 for(int k=0;k<8;k++){ if(k%2==0) gp.PersistentData.Append(new GH_Point(wall[k])); else { var dir=(k==1||k==5)? Vector3d.XAxis: Vector3d.YAxis; if(LM==2) gp.PersistentData.Append(new GH_Plane(new Plane(wall[k],Vector3d.ZAxis))); else gp.PersistentData.Append(new GH_Line(new Line(wall[k]-dir*3000,wall[k]+dir*3000))); } }
 PAT=new[]{true}; }
var ex=Add("Explode PFoam"); W(vc,"PFoam",ex,"PFoam"); var sp=Add("Separate PFEdges By Type"); W(ex,"PFEdges",sp,"PFEdge"); var ie=Add("Inspect PFEdge"); W(sp,"Internal",ie,"PFEdge");
var iv=Add("Inspect PFVertex"); W(ex,"PFVertices",iv,"PFVertex");
Solve();
foreach(var c in doc.Objects.OfType<IGH_Component>()) if(c.RuntimeMessageLevel==GH_RuntimeMessageLevel.Error) sb.AppendLine("ERR "+Msg(c));
var F=D(ie,"Force").Select(x=>Convert.ToDouble(x)).ToList(); var P=D(iv,"Point").Cast<Point3d>().ToList(); var X=D(iv,"External").Select(x=>(bool)x).ToList(); var VID=D(iv,"ID").Select(x=>Convert.ToInt32(x)).ToList();
var ip=P.Where((p,i)=>!X[i]).ToList();
var ids=D(lid,"Item").Select(x=>Convert.ToInt32(x)).ToList(); var tg=D(dv,"Points").Cast<Point3d>().ToList();
sb.AppendLine("n "+NN+" d "+DD+" cells "+D(ipc,"ID").Count+": bars "+F.Count/2+" T "+F.Count(f=>f<-1e-9)/2+" apex "+(ip.Count>0?ip.Max(p=>p.Z).ToString("0"):"-")+" ms "+sw.ElapsedMilliseconds+" ids "+string.Join(",",ids));
for(int k=0;k<ids.Count;k++){ int j=VID.IndexOf(ids[k]); var p=j>=0?P[j]:Point3d.Unset; var t=tg[k]; 
  // outward offset from wall line: for corners use max(|x|,|y|)-5000 ; mid: same
  double outw=Math.Max(Math.Abs(p.X),Math.Abs(p.Y))-HX;
  sb.AppendLine("  sup "+k+(PAT[k%PAT.Length]?" PIN ":" free")+" target "+t.X.ToString("0")+","+t.Y.ToString("0")+" -> "+p.X.ToString("0")+","+p.Y.ToString("0")+","+p.Z.ToString("0")+"  out "+outw.ToString("0")+" mm"); }
{ double mo=0,mz=0,mp=0; for(int k=0;k<ids.Count;k++){ int j=VID.IndexOf(ids[k]); if(j<0) continue; var p=P[j]; mo=Math.Max(mo,Math.Abs(Math.Max(Math.Abs(p.X),Math.Abs(p.Y))-HX)); mz=Math.Max(mz,Math.Abs(p.Z)); mp=Math.Max(mp,new Point3d(p.X,p.Y,0).DistanceTo(tg[k])); } sb.AppendLine("SUMMARY max|out| "+mo.ToString("0")+" max|z| "+mz.ToString("0")+" max plan miss "+mp.ToString("0")); }
{ var L=D(ie,"Line").Cast<Line>().ToList(); var tb=new List<string>(); for(int i=0;i<F.Count;i++) if(F[i]<-1e-9) tb.Add(F[i].ToString("0")+"@"+L[i].Length.ToString("0")+"mm z"+L[i].PointAt(0.5).Z.ToString("0")); sb.AppendLine("TBARS (Fmax "+F.Max().ToString("0")+"): "+string.Join("  ",tb)); }
Console.WriteLine(sb.ToString());
