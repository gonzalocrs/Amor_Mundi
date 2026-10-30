using Grasshopper; using Grasshopper.Kernel; using Grasshopper.Kernel.Special; using System.Drawing;
var d=Instances.ActiveCanvas.Document;
foreach(var p in d.Objects.OfType<GH_Panel>()){ if(p.NickName=="Bar force range") p.Attributes.Bounds=new RectangleF(p.Attributes.Bounds.X,p.Attributes.Bounds.Y,240,70); if(p.NickName=="Arch edge IDs") p.Attributes.Bounds=new RectangleF(p.Attributes.Bounds.X,p.Attributes.Bounds.Y,120,70); p.Attributes.ExpireLayout(); }
foreach(var g in d.Objects.OfType<GH_Group>()) g.Attributes.ExpireLayout();
Instances.ActiveCanvas.Refresh();
var io=new GH_DocumentIO(d); Console.WriteLine("saved "+io.Save()+" "+d.FilePath);
