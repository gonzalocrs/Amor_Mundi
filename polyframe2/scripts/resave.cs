using Grasshopper; using Grasshopper.Kernel;
var d=Instances.ActiveCanvas.Document; var io=new GH_DocumentIO(d); Console.WriteLine("saved "+io.Save()+" "+d.FilePath);
