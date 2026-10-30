using Grasshopper; using Grasshopper.Kernel; using Grasshopper.Kernel.Special;
var doc=Instances.ActiveCanvas.Document;
foreach(var g in doc.Objects.OfType<GH_Group>()) if(g.NickName.StartsWith("3")) g.NickName="3  Stage A - algebraic, 8 feet pinned (over-constrained = best fit, not exact; shown left)";
var io=new GH_DocumentIO(doc); Console.WriteLine("saved "+io.Save()+" "+doc.FilePath+" modified "+doc.IsModified);
Instances.ActiveCanvas.Refresh();
