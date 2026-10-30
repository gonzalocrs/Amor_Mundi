using Grasshopper.Kernel;
using GH_IO.Serialization;
var sb=new System.Text.StringBuilder();
var path=@"C:\Program Files (x86)\PolyFrame 2\Examples\3. Form-finding using algebraic method\(7) Case Study - manipulate form diagram - a single-layer shell.gh";
var arch=new GH_Archive(); arch.ReadFromFile(path);
var doc=new GH_Document(); arch.ExtractObject(doc,"Definition");
foreach(var o in doc.Objects){
 if(o.Name=="Brep"){ var p=(Grasshopper.Kernel.Parameters.Param_Brep)o; var all=p.PersistentData.AllData(true).ToList(); sb.AppendLine("breps "+all.Count);
   foreach(var g in all.Take(60)){ var b=((Grasshopper.Kernel.Types.GH_Brep)g).Value; var bb=b.GetBoundingBox(true); sb.AppendLine(" faces="+b.Faces.Count+" v="+b.Vertices.Count+" "+string.Join(" ",b.Vertices.Select(v=>"("+v.Location.X.ToString("0.#")+","+v.Location.Y.ToString("0.#")+","+v.Location.Z.ToString("0.#")+")")));}
 }
 if(o is Grasshopper.Kernel.Parameters.Param_Point pt){ sb.AppendLine("Pt: "+string.Join(";",pt.PersistentData.AllData(true).Select(x=>x.ToString())));}
 if(o.Name=="C# Script"){ var c=o as IGH_Component; var prop=o.GetType().GetProperty("ScriptSource"); sb.AppendLine("C# type "+o.GetType().FullName); 
   var w=new GH_LooseChunk("x"); o.Write(w); sb.AppendLine(w.Serialize_Xml().Substring(0,Math.Min(6000,w.Serialize_Xml().Length)));}
}
Console.WriteLine(sb.ToString());
