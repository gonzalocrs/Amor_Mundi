using Grasshopper; using Grasshopper.Kernel; using Grasshopper.Kernel.Types; using Rhino.Geometry;
var d=Instances.ActiveCanvas.Document;
foreach(var pp in d.Objects.OfType<IGH_Component>().Where(c=>c.Name=="PFPipe")){
 var ax=pp.Params.Output.First(o=>o.Name=="Axes").VolatileData.AllData(true).Select(x=>((GH_Line)x).Value).ToList();
 var lean=ax.Select(l=>{ var v=l.Direction; return Math.Atan2(Math.Sqrt(v.X*v.X+v.Y*v.Y),Math.Abs(v.Z))*180/Math.PI; }).ToList();
 Console.WriteLine("bars "+ax.Count+" lean from vertical: <=35: "+lean.Count(a=>a<=35)+"  35-60: "+lean.Count(a=>a>35&&a<=60)+"  60-80: "+lean.Count(a=>a>60&&a<=80)+"  >80 (near horizontal): "+lean.Count(a=>a>80)+"  min "+lean.Min().ToString("0.0")+" max "+lean.Max().ToString("0.0"));
}
Console.WriteLine("53.1 deg pyramid: face fall line lean from vertical = "+(90-Math.Atan2(6670,5000)*180/Math.PI).ToString("0.0")+" deg; hip lean = "+(90-Math.Atan2(6670,5000*Math.Sqrt(2))*180/Math.PI).ToString("0.0")+" deg");
Console.WriteLine("rise needed for a 35 deg lean from wall mid to centre: "+(5000/Math.Tan(35*Math.PI/180)).ToString("0")+" mm; from corner along hip: "+(5000*Math.Sqrt(2)/Math.Tan(35*Math.PI/180)).ToString("0")+" mm");
