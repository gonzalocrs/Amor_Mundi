double NN=3.0; double DD=375; double VS=1; double ADS=1; double HX=5000; double[] SUPT=new[]{0.125,0.375,0.625,0.875}; double MINL=100, MAXL=10000, TOL=0.1;
#include
#form
#report2
lid.NickName="IDS"; vc.NickName="VC"; Tap(vc,"PFoam","VC");
var lo=Add("Linear Optimization Solver"); lo.NickName="LO"; W(vc,"Algebraic Form",lo,"Algebraic Form"); Num(lo,"Min Edge Length",MINL); Num(lo,"Max Edge Length",MAXL); Num(lo,"Min Unsigned Edge Length",0); Num(lo,"Tolerance",TOL);
Tap(lo,"PFoam","LO");
var old=Instances.ActiveCanvas.Document; Instances.DocumentServer.AddDocument(doc); Instances.ActiveCanvas.Document=doc; if(old!=null){ old.Enabled=false; Instances.DocumentServer.RemoveDocument(old); old.Dispose(); }
Solve(); sb.AppendLine("solved ms "+sw.ElapsedMilliseconds+" cells "+D(ipc,"ID").Count+" IDs "+string.Join(",",D(lid,"Item"))+" supports "+string.Join(" ",D(sel,"Point")));
foreach(var c in doc.Objects.OfType<IGH_Component>()) if(c.RuntimeMessageLevel!=GH_RuntimeMessageLevel.Blank && c.NickName!="LO" && !c.NickName.EndsWith("_LO")) sb.AppendLine("  msg "+Msg(c));
Console.WriteLine(sb.ToString());
