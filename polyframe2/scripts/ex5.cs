using Grasshopper.Kernel;
using GH_IO.Serialization;
var sb=new System.Text.StringBuilder();
var path=@"C:\Program Files (x86)\PolyFrame 2\Examples\3. Form-finding using algebraic method\(5) Constraint minimum and maximum edge length.gh";
var arch=new GH_Archive(); arch.ReadFromFile(path);
var doc=new GH_Document(); arch.ExtractObject(doc,"Definition");
foreach(var o in doc.Objects){
 if(o is Grasshopper.Kernel.Special.GH_Panel p) sb.AppendLine("PANEL: "+p.UserText);
 if(o.Name=="Minimize Total Edge Length"||o.Name=="Linear Optimization Solver"){ var w=new GH_LooseChunk("x"); o.Write(w); var x=w.Serialize_Xml(); int i=x.IndexOf("<items"); sb.AppendLine(x.Substring(0,Math.Min(2500,x.Length))); }
 if(o is Grasshopper.Kernel.Special.GH_NumberSlider s) sb.AppendLine("slider "+s.CurrentValue+" -> "+string.Join(",",s.Recipients.Select(r=>r.Attributes.GetTopLevel.DocObject.Name+"."+r.Name)));
 if(o.Name=="Brep"){ var bp=(Grasshopper.Kernel.Parameters.Param_Brep)o; sb.AppendLine("breps "+bp.PersistentData.DataCount);}
}
Console.WriteLine(sb.ToString());
