using Grasshopper; using Grasshopper.Kernel; using Rhino.Geometry;
var doc=Instances.ActiveCanvas.Document;
foreach(var o in doc.Objects.OfType<IGH_ActiveObject>()) if(o is IGH_PreviewObject p) p.Hidden=true;
var lo=doc.Objects.OfType<IGH_Component>().First(c=>c.NickName=="LO"); ((IGH_PreviewObject)lo).Hidden=false;
var v=__rhino_doc__.Views.ActiveView; v.Redraw();
Console.WriteLine("ok");
