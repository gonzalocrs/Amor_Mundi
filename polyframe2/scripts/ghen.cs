dynamic gh=Rhino.RhinoApp.GetPlugInObject("Grasshopper"); if(!gh.IsEditorLoaded()) gh.LoadEditor(); Grasshopper.Kernel.GH_Document.EnableSolutions=true; Console.WriteLine("ok");
