using Grasshopper; using Grasshopper.Kernel;
var io=new GH_DocumentIO(); io.Open(@"C:\Users\gonza\Documents\GitHub\pyramid-roof\grasshopper\Pyramide Karamba 10_14_2026.gh"); var d=io.Document;
Console.WriteLine("objs "+d.ObjectCount);
foreach(var o in d.Objects.OfType<IGH_Component>().Where(c=>c.Category.StartsWith("Karamba"))){
 Console.WriteLine(o.Name+" ["+o.NickName+"] msg='"+o.Message+"' IN "+string.Join(", ",o.Params.Input.Select(i=>i.Name+(i.SourceCount>0?"<-"+string.Join("/",i.Sources.Select(s=>s.Attributes.GetTopLevel.DocObject.NickName+"."+s.NickName)):""))));
}
var karG=AppDomain.CurrentDomain.GetAssemblies().FirstOrDefault(a=>a.GetName().Name=="karamba");
d.Dispose();
