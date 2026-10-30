using Grasshopper.Kernel;
using GH_IO.Serialization;
var sb=new System.Text.StringBuilder();
foreach(var f in new[]{"(5) Constraint minimum and maximum edge length.gh","(7) Case Study - manipulate form diagram - a single-layer shell.gh","(2) A simple bridge with edge and vertex constraints.gh"}){
 var path=@"C:\Program Files (x86)\PolyFrame 2\Examples\3. Form-finding using algebraic method\"+f;
 var arch=new GH_Archive(); arch.ReadFromFile(path);
 var doc=new GH_Document(); arch.ExtractObject(doc,"Definition");
 sb.AppendLine("=== "+f+" objs="+doc.ObjectCount);
 foreach(var o in doc.Objects){
  string extra="";
  if(o is Grasshopper.Kernel.Special.GH_NumberSlider s) extra=" val="+s.CurrentValue+" ["+s.Slider.Minimum+","+s.Slider.Maximum+"]";
  if(o is Grasshopper.Kernel.Special.GH_Panel p) extra=" txt="+p.UserText.Replace("\n"," | ").Substring(0,Math.Min(300,p.UserText.Length));
  if(o is Grasshopper.Kernel.Special.GH_Group g) extra=" group:"+g.NickName;
  sb.Append(o.Name+" ["+o.NickName+"] "+o.ComponentGuid+extra);
  if(o is IGH_Component c){
   sb.Append(" IN:");
   foreach(var pi in c.Params.Input){ sb.Append(pi.Name+(pi.SourceCount>0?"<-"+string.Join("/",pi.Sources.Select(x=>(x.Attributes.GetTopLevel.DocObject.NickName)+"."+x.NickName)):"")); 
     if(pi.SourceCount==0){ try{ var pd=pi.GetType().GetProperty("PersistentData"); if(pd!=null){var v=pd.GetValue(pi) as Grasshopper.Kernel.Data.IGH_Structure; if(v!=null && v.DataCount>0) sb.Append("="+string.Join(",",v.AllData(true).Take(4).Select(q=>q.ToString())));}}catch{} }
     sb.Append("; ");}
   sb.Append(" OUT:"+string.Join(",",c.Params.Output.Select(x=>x.Name)));
  } else if(o is IGH_Param pp && pp.SourceCount>0){ sb.Append(" <-"+string.Join("/",pp.Sources.Select(x=>x.Attributes.GetTopLevel.DocObject.NickName+"."+x.NickName)));}
  sb.AppendLine();
 }
}
Console.WriteLine(sb.ToString());
