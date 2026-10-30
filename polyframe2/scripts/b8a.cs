int NN=2; double DD=1000; int[] SUP={5,45,43,6}; double VS=1; double MINL=0.01, MAXL=1000000;
#include
#form
#report
var lo=Add("Linear Optimization Solver"); W(vc,"Algebraic Form",lo,"Algebraic Form"); Num(lo,"Min Edge Length",MINL); Num(lo,"Max Edge Length",MAXL); Num(lo,"Min Unsigned Edge Length",0); Num(lo,"Tolerance",0.1);
Rep(lo,"PFoam","LO");
Console.WriteLine(sb.ToString());
