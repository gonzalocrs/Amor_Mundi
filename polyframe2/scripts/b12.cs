double NN=__N__; double DD=__D__; double VS=1; double HX=5000; double[] SUPT=new[]{0.125,0.375,0.625,0.875}; 
#include
#form
#report2
// dual vertex IDs in PFBuild form for the picked cells
var ivd=Add("Inspect PFVertex"); W(ipc,"Dual",ivd,"PFVertex");
Solve();
var cellIdx=D(cps,"CP Index").Select(x=>Convert.ToInt32(x)).ToList();
var dualTree=Out(ivd,"ID").VolatileData; var paths=dualTree.Paths.ToList();
var fids=new List<int>(); foreach(var ci in cellIdx){ var br=dualTree.get_Branch(paths[ci]); fids.Add(Convert.ToInt32(((GH_Integer)br[0]).Value)); }
sb.AppendLine("cell idx "+string.Join(",",cellIdx)+" -> form IDs "+string.Join(",",fids)+" (branch sizes "+string.Join(",",cellIdx.Select(ci=>dualTree.get_Branch(paths[ci]).Count))+")");
var pvc=Add("PFVertex Constraints"); W(bld,"Form PFoam",pvc,"PFoam"); Ints(pvc,"PFVertex ID",fids); W(sel,"Point",pvc,"Constraint"); In(pvc,"Constraint").DataMapping=GH_DataMapping.Flatten; Num(pvc,"Coefficient",__COEF__); Bool(pvc,"On",true);
var perp=Add("PFPerp"); W(pvc,"PFoam",perp,"PFoam"); Int(perp,"Max Iteration",__IT__); Num(perp,"Deviation",0.1); Num(perp,"Minimum Edge Length",__ML__);
perp.NickName="PERP"; Tap(perp,"PFoam","PERP");
var old=Instances.ActiveCanvas.Document; Instances.DocumentServer.AddDocument(doc); Instances.ActiveCanvas.Document=doc; if(old!=null){ old.Enabled=false; Instances.DocumentServer.RemoveDocument(old); old.Dispose(); }
var t0=sw.ElapsedMilliseconds; Solve(); sb.AppendLine("perp solve ms "+(sw.ElapsedMilliseconds-t0)+" dev "+string.Join(",",D(perp,"Deviation")));
foreach(var c in doc.Objects.OfType<IGH_Component>()) if(c.RuntimeMessageLevel!=GH_RuntimeMessageLevel.Blank && !c.NickName.EndsWith("_LO")) sb.AppendLine("  msg "+Msg(c));
Console.WriteLine(sb.ToString());
