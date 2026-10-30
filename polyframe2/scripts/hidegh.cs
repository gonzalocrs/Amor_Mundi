using Grasshopper; using Grasshopper.Kernel;
var d=Instances.ActiveCanvas?.Document; if(d!=null){ foreach(var o in d.Objects.OfType<IGH_PreviewObject>()) o.Hidden=true; } Rhino.RhinoDoc.ActiveDoc?.Views.Redraw(); __rhino_doc__.Views.Redraw(); Console.WriteLine("hidden");
