using Grasshopper; using Grasshopper.Kernel;
Console.WriteLine("EnableSolutions="+GH_Document.EnableSolutions+" canvasDoc="+(Instances.ActiveCanvas?.Document!=null)+" enabled="+Instances.ActiveCanvas?.Document?.Enabled);
