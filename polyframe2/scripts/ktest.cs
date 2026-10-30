var lines=new List<Line3>{ new Line3(new Point3(0,0,0),new Point3(2.5,0,0)), new Line3(new Point3(2.5,0,0),new Point3(5,0,0)) };
var sup=new List<Point3>{new Point3(0,0,0),new Point3(5,0,0)};
var m=Build(lines,sup,new List<(Point3,double)>{(new Point3(2.5,0,0),10.0)},25,15,false,out var info,out var mass);
m=k3d.Algorithms.AnalyzeThI(m,out var maxD,out var gF,out var en,out var warn);
Console.WriteLine("mass "+mass.ToString("0.0")+" kg (expect 0.15*0.25*5*2400/... ~ "+(0.15*0.25*5*24/9.81*1000).ToString("0")+" kg via gamma 24) | maxDisp "+string.Join(",",maxD.Select(x=>x.ToString("0.00000")))+" (hand 0.00407 m) warn "+warn);
// beam forces via GH component
var d=new GH_Document(); var pm=new Karamba.GHopper.Models.Param_Model(); pm.CreateAttributes(); d.AddObject(pm,false); pm.PersistentData.Append(new Karamba.GHopper.Models.GH_Model(m));
var bf=KC(d,"4f255ff1-ffed-4f54-99ab-f8f82c48a624"); bf.Params.Input[0].AddSource(pm);
d.Enabled=true; d.NewSolution(false,GH_SolutionMode.Silent);
foreach(var o in bf.Params.Output.Skip(1)) Console.WriteLine(o.Name+": "+string.Join(" ",o.VolatileData.AllData(true).Take(12).Select(x=>x.ToString())));
Console.WriteLine("bf msgs: "+string.Join("|",bf.RuntimeMessages(GH_RuntimeMessageLevel.Warning).Concat(bf.RuntimeMessages(GH_RuntimeMessageLevel.Error))));
foreach(var i in bf.Params.Input) Console.WriteLine(" in "+i.Name+" data "+string.Join(",",i.VolatileData.AllData(true).Take(6)));
