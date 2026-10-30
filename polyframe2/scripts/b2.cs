double R=1000; int n=3;
var hex=Add("Hexagonal"); Pl(hex,"Plane",Plane.WorldXY); Num(hex,"Size",100); Int(hex,"Extent X",4); Int(hex,"Extent Y",4);
Solve();
foreach(var o in hex.Params.Output) sb.AppendLine(o.Name+" "+o.VolatileData.DataCount+" paths "+o.VolatileData.PathCount);
var pts=D(hex,"Points").Cast<Point3d>().ToList();
sb.AppendLine(string.Join(" ",pts.Select(p=>"("+p.X.ToString("0.#")+","+p.Y.ToString("0.#")+")")));
sb.AppendLine(Msg(hex)); sb.AppendLine(string.Join(",",hex.Params.Input.Select(i=>i.Name)));
Console.WriteLine(sb.ToString());
