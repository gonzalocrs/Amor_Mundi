int NN=2; double DD=1000;
#include
Solve();
foreach(var c in new[]{li,poly,pic,cull,disc,mrg,del,fb}) foreach(var o in c.Params.Output) sb.AppendLine(c.Name+"."+o.Name+" n="+o.VolatileData.DataCount+" paths="+string.Join(",",o.VolatileData.Paths.Take(5)));
Console.WriteLine(sb.ToString());
