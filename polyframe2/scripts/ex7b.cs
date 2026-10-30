using Rhino.Geometry;
using Grasshopper.Kernel;
using GH_IO.Serialization;
var sb=new System.Text.StringBuilder();
var path=@"C:\Program Files (x86)\PolyFrame 2\Examples\3. Form-finding using algebraic method\(7) Case Study - manipulate form diagram - a single-layer shell.gh";
var arch=new GH_Archive(); arch.ReadFromFile(path);
var doc=new GH_Document(); arch.ExtractObject(doc,"Definition");
foreach(var o in doc.Objects){
 if(o.Name=="Brep"){ var p=(Grasshopper.Kernel.Parameters.Param_Brep)o; var all=p.PersistentData.AllData(true).Select(g=>((Grasshopper.Kernel.Types.GH_Brep)g).Value).ToList();
   var bbAll=BoundingBox.Empty; foreach(var b in all) bbAll.Union(b.GetBoundingBox(true));
   sb.AppendLine("bbox "+bbAll.Min+" "+bbAll.Max);
   foreach(var grp in all.GroupBy(b=>b.Faces.Count+"f/"+b.Vertices.Count+"v solid="+b.IsSolid+" zr="+(b.GetBoundingBox(true).Max.Z-b.GetBoundingBox(true).Min.Z).ToString("0"))) sb.AppendLine(grp.Key+" x"+grp.Count());
   foreach(var b in all.Where(b=>b.Faces.Count>1).Take(3)) sb.AppendLine(string.Join(" ",b.Vertices.Select(v=>v.Location.ToString())));
 }
 if(o.Name=="Panel") sb.AppendLine("panel src: "+string.Join(",",((IGH_Param)o).Sources.Select(s=>s.Attributes.GetTopLevel.DocObject.Name))+" -> "+string.Join(",",((IGH_Param)o).Recipients.Select(s=>s.Attributes.GetTopLevel.DocObject.Name+"."+s.Name)));
 if(o is Grasshopper.Kernel.Special.GH_NumberSlider s) sb.AppendLine("slider "+s.CurrentValue+" -> "+string.Join(",",s.Recipients.Select(r=>r.Attributes.GetTopLevel.DocObject.Name+"."+r.Name)));
 if(o is Grasshopper.Kernel.Parameters.Param_Point pt) sb.AppendLine("Pt -> "+string.Join(",",pt.Recipients.Select(r=>r.Attributes.GetTopLevel.DocObject.Name+"."+r.Name)));
}
Console.WriteLine(sb.ToString());
