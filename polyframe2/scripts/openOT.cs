using Grasshopper; using Grasshopper.Kernel;
var io=new GH_DocumentIO(); var ok=io.Open(@"C:\Users\gonza\Documents\GitHub\pyramid-roof\polyframe2\friend-AP8-diagrid-evenload-opentop.gh"); var d=io.Document;
var canvas=Instances.ActiveCanvas; var old=canvas.Document;
Instances.DocumentServer.AddDocument(d); canvas.Document=d; d.Enabled=true; d.NewSolution(false);
if(old!=null && old!=d){ old.Enabled=false; Instances.DocumentServer.RemoveDocument(old); old.Dispose(); }
canvas.Refresh();
Console.WriteLine("opened "+ok+" path "+d.FilePath+" objs "+d.ObjectCount+" modified "+d.IsModified);
