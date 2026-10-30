using Grasshopper; using Grasshopper.Kernel.Special;
var d=Instances.ActiveCanvas.Document; Console.WriteLine(string.Join(" | ",d.Objects.OfType<GH_Panel>().Select(p=>p.NickName))+" objs "+d.ObjectCount);
