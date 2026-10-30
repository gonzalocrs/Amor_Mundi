using Grasshopper; using Grasshopper.Kernel; using Grasshopper.Kernel.Special; using Rhino.Geometry;
var sb=new System.Text.StringBuilder();
var doc=Instances.ActiveCanvas.Document;
void Set(string n,double v){ var s=doc.Objects.OfType<GH_NumberSlider>().First(x=>x.NickName==n); s.SetSliderValue((decimal)v); s.ExpireSolution(false); }
foreach(var kv in "__SET__".Split(';')){ var p=kv.Split('='); if(p.Length==2) Set(p[0],double.Parse(p[1])); }
var sw=System.Diagnostics.Stopwatch.StartNew(); doc.NewSolution(false); sb.AppendLine("ms "+sw.ElapsedMilliseconds);
foreach(var k in doc.Objects.OfType<GH_Cluster>().Where(c=>c.NickName=="Check")) sb.AppendLine("check: "+string.Join(" | ",k.Params.Output.Select(o=>string.Join(" ",o.VolatileData.AllData(true).Select(x=>x.ToString())))));
foreach(var pp in doc.Objects.OfType<IGH_Component>().Where(c=>c.Name=="PFPipe")){ var ax=pp.Params.Output.First(o=>o.Name=="Axes").VolatileData.AllData(true).Select(x=>((Grasshopper.Kernel.Types.GH_Line)x).Value).ToList(); sb.AppendLine("apex "+ax.Max(l=>Math.Max(l.From.Z,l.To.Z)).ToString("0")+" bars "+ax.Count); }
Console.WriteLine(sb.ToString());
