using Grasshopper; using Grasshopper.Kernel;
var io=new GH_DocumentIO(); io.Open("C:/Users/gonza/Documents/GitHub/pyramid-roof/polyframe2/friend-diagrid-karamba.gh"); var d=io.Document; d.Enabled=true;
var sw=System.Diagnostics.Stopwatch.StartNew(); d.NewSolution(false,GH_SolutionMode.Silent);
Console.WriteLine("objs "+d.ObjectCount+" solve ms "+sw.ElapsedMilliseconds);
foreach(var p in d.Objects.OfType<Grasshopper.Kernel.Special.GH_Panel>().Where(p=>p.SourceCount>0)) Console.WriteLine(p.NickName.Split(':')[0]+": "+string.Join(" | ",p.VolatileData.AllData(true).Select(x=>x.ToString())));
foreach(var c in d.Objects.OfType<IGH_Component>()) if(c.RuntimeMessageLevel==GH_RuntimeMessageLevel.Error) Console.WriteLine("ERR "+c.NickName+": "+string.Join("|",c.RuntimeMessages(GH_RuntimeMessageLevel.Error)));
d.Enabled=false; d.Dispose();
