#gen
var g=GenDiamond(5,3,380,0.85,8);
int bad=0; foreach(var t in g.tets) if(t==null||!t.IsSolid) bad++;
sb.AppendLine("cells "+g.tets.Count+" not solid "+bad+" targets "+g.targets.Count);
var sw2=System.Diagnostics.Stopwatch.StartNew();
var bp=new Param_Brep(); bp.CreateAttributes(); doc.AddObject(bp,false); foreach(var t in g.tets) if(t!=null) bp.PersistentData.Append(new GH_Brep(t));
var bld=Add("PFBuild"); bld.Params.Input[0].AddSource(bp); Num(bld,"Absolute Tolerance",0.1); Num(bld,"Planarity Tolerance",0.1);
Solve(); sb.AppendLine("PFBuild ms "+sw2.ElapsedMilliseconds+" "+Msg(bld));
Console.WriteLine(sb.ToString());
