double R=1000; int n=3; double d=1000;
var poly=Add("Polygon"); Pl(poly,"Plane",Plane.WorldXY); Num(poly,"Radius",R); Int(poly,"Segments",4); Num(poly,"Fillet Radius",0);
var tri=Add("Triangular"); Pl(tri,"Plane",new Plane(new Point3d(-R,-R,0),Vector3d.XAxis,Vector3d.YAxis)); Num(tri,"Size",R/n); Int(tri,"Extent X",3*n); Int(tri,"Extent Y",3*n);
Solve();
var pts=D(tri,"Points").Cast<Point3d>().ToList();
sb.AppendLine("tri pts "+pts.Count+" first "+string.Join(" ",pts.Take(12).Select(p=>"("+p.X.ToString("0")+","+p.Y.ToString("0")+")")));
sb.AppendLine(Msg(tri)+" "+Msg(poly));
var pc=D(poly,"Polygon")[0] as Curve; sb.AppendLine("poly ok "+(pc!=null)+" pts "+string.Join(" ",new[]{0,0.25,0.5,0.75}.Select(t=>pc.PointAtNormalizedLength(t).ToString())));
Console.WriteLine(sb.ToString());
