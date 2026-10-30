using Grasshopper; using Grasshopper.Kernel; using Grasshopper.Kernel.Special; using Grasshopper.Kernel.Types; using Rhino.Geometry;
var d=Instances.ActiveCanvas.Document; var sz=d.Objects.OfType<GH_NumberSlider>().First(s=>s.NickName.StartsWith("Force depth"));
foreach(var z in new[]{0.41,0.37,0.33}){ sz.SetSliderValue((decimal)z); sz.ExpireSolution(false); d.NewSolution(false);
 var pp=d.Objects.OfType<IGH_Component>().Where(c=>c.Name=="PFPipe").Last();
 var ax=pp.Params.Output.First(o=>o.Name=="Axes").VolatileData.AllData(true).Select(x=>((GH_Line)x).Value).ToList();
 var apex=ax.Max(l=>Math.Max(l.From.Z,l.To.Z));
 // corner legs = bars whose lower end is within 300 mm of a plan corner
 bool corner(Line l){ var lo=l.From.Z<l.To.Z?l.From:l.To; return Math.Abs(Math.Abs(lo.X)-5000)<600 && Math.Abs(Math.Abs(lo.Y)-5000)<600; }
 var lean=ax.Select(l=>{var v=l.Direction; return (Math.Atan2(Math.Sqrt(v.X*v.X+v.Y*v.Y),Math.Abs(v.Z))*180/Math.PI, corner(l));}).ToList();
 var face=lean.Where(t=>!t.Item2).Select(t=>t.Item1).ToList();
 Console.WriteLine("ScaleZ "+z+" stageB apex "+apex.ToString("0")+" bars "+ax.Count+" corner-leg bars "+lean.Count(t=>t.Item2)+" | non-corner: <=35 "+face.Count(a=>a<=35)+"  >35 "+face.Count(a=>a>35)+"  >60 "+face.Count(a=>a>60)+"  >80 "+face.Count(a=>a>80));
}
sz.SetSliderValue(0.41m); sz.ExpireSolution(false); d.NewSolution(false);
