using Grasshopper; using Grasshopper.Kernel;
var io=new GH_DocumentIO(); io.Open(@"C:\Users\gonza\Documents\GitHub\pyramid-roof\polyframe2\friend-15-pyramid-skin.gh"); var doc=io.Document;
var old=Instances.ActiveCanvas.Document; Instances.DocumentServer.AddDocument(doc); Instances.ActiveCanvas.Document=doc; if(old!=null){ old.Enabled=false; Instances.DocumentServer.RemoveDocument(old); old.Dispose(); }
doc.Enabled=true; doc.NewSolution(false); Console.WriteLine("ok "+doc.ObjectCount);
