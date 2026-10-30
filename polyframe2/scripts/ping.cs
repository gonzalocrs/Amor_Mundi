Console.WriteLine("pid "+System.Diagnostics.Process.GetCurrentProcess().Id+" doc "+(Rhino.RhinoDoc.ActiveDoc.Path??"unsaved"));
