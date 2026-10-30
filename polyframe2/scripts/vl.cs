using Grasshopper; using Grasshopper.Kernel; using Grasshopper.Kernel.Special;
var d=Instances.ActiveCanvas.Document; var vl=d.Objects.OfType<GH_ValueList>().First();
foreach(var i in new[]{0,1,3,4,2}){ vl.SelectItem(i); vl.ExpireSolution(false); var sw=System.Diagnostics.Stopwatch.StartNew(); d.NewSolution(false);
 Console.WriteLine(vl.FirstSelectedItem.Name+" ms "+sw.ElapsedMilliseconds+" | "+string.Join(" || ",d.Objects.OfType<GH_Cluster>().Where(c=>c.NickName=="Check").Select(k=>string.Join(" | ",k.Params.Output.Select(o=>string.Join(" ",o.VolatileData.AllData(true).Select(x=>x.ToString())))))));
 foreach(var pp in d.Objects.OfType<IGH_Component>().Where(c=>c.Name=="PFPipe")){ var ax=pp.Params.Output.First(o=>o.Name=="Axes").VolatileData.AllData(true).Select(x=>((Grasshopper.Kernel.Types.GH_Line)x).Value).ToList(); Console.WriteLine("   apex "+ax.Max(l=>Math.Max(l.From.Z,l.To.Z)).ToString("0")+" bars "+ax.Count); }
}
var io=new GH_DocumentIO(d); Console.WriteLine("modified "+d.IsModified);
