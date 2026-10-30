using Grasshopper; using Grasshopper.Kernel;
var d=Instances.ActiveCanvas?.Document; Console.WriteLine("active: "+(d==null?"none":d.DisplayName+" enabled "+d.Enabled+" objs "+d.ObjectCount+" preview "+d.PreviewMode));
foreach(GH_Document x in Instances.DocumentServer) Console.WriteLine(" open: "+x.DisplayName+(x.IsModified?" (modified)":""));
if(d!=null){ int e=0,w=0; foreach(var o in d.Objects.OfType<IGH_ActiveObject>()){ if(o.RuntimeMessageLevel==GH_RuntimeMessageLevel.Error){e++; Console.WriteLine(" ERR "+o.NickName+": "+string.Join("|",o.RuntimeMessages(GH_RuntimeMessageLevel.Error)));} if(o.RuntimeMessageLevel==GH_RuntimeMessageLevel.Warning){w++; Console.WriteLine(" WARN "+o.NickName+": "+string.Join("|",o.RuntimeMessages(GH_RuntimeMessageLevel.Warning)));} } Console.WriteLine("errors "+e+" warnings "+w);
 foreach(var p in d.Objects.OfType<Grasshopper.Kernel.Special.GH_Panel>().Where(p=>p.SourceCount>0)) Console.WriteLine(" panel "+p.NickName+": "+string.Join(" ; ",p.VolatileData.AllData(true)));
 foreach(var s in d.Objects.OfType<Grasshopper.Kernel.Special.GH_NumberSlider>()) Console.WriteLine(" slider "+s.NickName+" = "+s.CurrentValue); }
