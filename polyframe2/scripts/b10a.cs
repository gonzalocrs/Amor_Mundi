int NN=2; double DD=623.5; int[] SUP={5,45,43,6}; double VS=1; double HX=5000, HY=5000; var CP=new[]{new Point3d(-HX,-HY,0),new Point3d(HX,-HY,0),new Point3d(HX,HY,0),new Point3d(-HX,HY,0)}; double MINL=100, MAXL=10000, TOL=0.1;
#include
#form
#report2
vc.NickName="VC"; Tap(vc,"PFoam","VC");
var lo=Add("Linear Optimization Solver"); lo.NickName="LO"; W(vc,"Algebraic Form",lo,"Algebraic Form"); Num(lo,"Min Edge Length",MINL); Num(lo,"Max Edge Length",MAXL); Num(lo,"Min Unsigned Edge Length",0); Num(lo,"Tolerance",TOL);
Tap(lo,"PFoam","LO");
var old=Instances.ActiveCanvas.Document; Instances.DocumentServer.AddDocument(doc); Instances.ActiveCanvas.Document=doc; if(old!=null){ old.Enabled=false; Instances.DocumentServer.RemoveDocument(old); old.Dispose(); }
Solve(); sb.AppendLine("solved ms "+sw.ElapsedMilliseconds);
Console.WriteLine(sb.ToString());
