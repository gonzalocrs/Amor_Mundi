int NN=__N__; double DD=__D__; int[] SUP=__SUP__; double VS=__VS__; double HX=__HX__, HY=__HY__; var CP=__CP__; double MINL=__MIN__, MAXL=__MAX__, TOL=__TOL__;
#include
#form
#report2
vc.NickName="VC"; Tap(vc,"PFoam","VC");
var lo=Add("Linear Optimization Solver"); lo.NickName="LO"; W(__SRC__,"Algebraic Form",lo,"Algebraic Form"); Num(lo,"Min Edge Length",MINL); Num(lo,"Max Edge Length",MAXL); Num(lo,"Min Unsigned Edge Length",__MU__); Num(lo,"Tolerance",TOL);
Tap(lo,"PFoam","LO");
var old=Instances.ActiveCanvas.Document; Instances.DocumentServer.AddDocument(doc); Instances.ActiveCanvas.Document=doc; if(old!=null){ old.Enabled=false; Instances.DocumentServer.RemoveDocument(old); old.Dispose(); }
Solve(); sb.AppendLine("solved ms "+sw.ElapsedMilliseconds);
Console.WriteLine(sb.ToString());
