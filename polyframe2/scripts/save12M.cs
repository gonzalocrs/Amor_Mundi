using Grasshopper; using Grasshopper.Kernel; using GH_IO.Serialization;
var doc=Instances.ActiveCanvas.Document;
var path=@"C:\Users\gonza\Documents\GitHub\pyramid-roof\polyframe2\friend-12-feet-2m-corners-opentop.gh";
var arch=new GH_Archive(); arch.CreateNewRoot(false); arch.AppendObject(doc,"Definition"); 
Console.WriteLine("write "+arch.WriteToFile(path,true,false));
// reload test into a separate doc and solve
var a2=new GH_Archive(); a2.ReadFromFile(path); var d2=new GH_Document(); a2.ExtractObject(d2,"Definition");
d2.Enabled=true; var sw=System.Diagnostics.Stopwatch.StartNew(); d2.NewSolution(false, GH_SolutionMode.Silent);
Console.WriteLine("reload objs "+d2.ObjectCount+" solve ms "+sw.ElapsedMilliseconds);
foreach(var o in d2.Objects.OfType<IGH_ActiveObject>()) if(o.RuntimeMessageLevel!=GH_RuntimeMessageLevel.Blank) Console.WriteLine("msg "+o.NickName+": "+o.RuntimeMessageLevel);
foreach(var pan in d2.Objects.OfType<Grasshopper.Kernel.Special.GH_Panel>()) Console.WriteLine("panel: "+string.Join(" ; ",pan.VolatileData.AllData(true)));
foreach(var c in d2.Objects.OfType<Grasshopper.Kernel.Special.GH_Cluster>()) Console.WriteLine("cluster "+c.NickName+" in "+string.Join(",",c.Params.Input.Select(p=>p.NickName))+" out "+string.Join(",",c.Params.Output.Select(p=>p.NickName+"="+p.VolatileData.DataCount)));
d2.Dispose();
