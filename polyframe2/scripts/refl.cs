using Grasshopper; using Grasshopper.Kernel; using System.Reflection;
var sb=new System.Text.StringBuilder();
var doc=Instances.ActiveCanvas.Document;
var lo=doc.Objects.OfType<IGH_Component>().First(c=>c.NickName=="LO");
var t=lo.GetType(); sb.AppendLine(t.FullName);
foreach(var f in t.GetFields(BindingFlags.Instance|BindingFlags.NonPublic|BindingFlags.Public|BindingFlags.Static)) { object v=null; try{v=f.IsStatic?f.GetValue(null):f.GetValue(lo);}catch{} var s=v is System.Collections.IEnumerable e && !(v is string)? string.Join(",",e.Cast<object>().Take(10)) : v?.ToString(); sb.AppendLine(" field "+f.Name+" : "+f.FieldType.Name+" = "+s); }
foreach(var m in t.GetMethods(BindingFlags.Instance|BindingFlags.NonPublic|BindingFlags.Public|BindingFlags.DeclaredOnly)) sb.AppendLine(" method "+m.Name);
var menu=new System.Windows.Forms.ToolStripDropDown(); 
try{ ((GH_DocumentObject)lo).AppendMenuItems(menu); foreach(System.Windows.Forms.ToolStripItem it in menu.Items) sb.AppendLine(" menu: "+it.Text+(it is System.Windows.Forms.ToolStripMenuItem mi? " checked="+mi.Checked+" sub="+string.Join("/",mi.DropDownItems.Cast<System.Windows.Forms.ToolStripItem>().Select(x=>x.Text+((x as System.Windows.Forms.ToolStripMenuItem)?.Checked==true?"*":""))):"")); }catch(Exception ex){sb.AppendLine("menu err "+ex.Message);}
Console.WriteLine(sb.ToString());
