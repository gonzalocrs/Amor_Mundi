int NN=2; double DD=1000; int[] SUP={5,45,43,6}; double VS=1; double MINL=100, MAXL=10000;
#include
#form
#report2
vc.NickName="VC"; Tap(vc,"PFoam","VC");
var lo=Add("Linear Optimization Solver"); lo.NickName="LO"; W(vc,"Algebraic Form",lo,"Algebraic Form"); Num(lo,"Min Edge Length",MINL); Num(lo,"Max Edge Length",MAXL); Num(lo,"Min Unsigned Edge Length",0); Num(lo,"Tolerance",0.1);
Tap(lo,"PFoam","LO");
Instances.DocumentServer.AddDocument(doc); Instances.ActiveCanvas.Document=doc;
Solve(); sb.AppendLine("solved ms "+sw.ElapsedMilliseconds);
Console.WriteLine(sb.ToString());
