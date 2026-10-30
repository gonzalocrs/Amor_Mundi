using Grasshopper; using Grasshopper.Kernel; using Rhino.Geometry;
var io=new GH_DocumentIO(); var ok=io.Open(@"C:\Program Files (x86)\PolyFrame 2\Examples\3. Form-finding using algebraic method\(7) Case Study - manipulate form diagram - a single-layer shell.gh"); var d=io.Document;
var canvas=Instances.ActiveCanvas; var old=canvas.Document;
Instances.DocumentServer.AddDocument(d); canvas.Document=d; d.Enabled=true; var sw=System.Diagnostics.Stopwatch.StartNew(); d.NewSolution(false);
if(old!=null && old!=d){ old.Enabled=false; Instances.DocumentServer.RemoveDocument(old); old.Dispose(); }
Console.WriteLine("ms "+sw.ElapsedMilliseconds);
foreach(var o in d.Objects.OfType<IGH_ActiveObject>()) if(o.RuntimeMessageLevel!=GH_RuntimeMessageLevel.Blank) Console.WriteLine("msg "+o.Name+" "+o.RuntimeMessageLevel);
var vc=d.Objects.OfType<IGH_Component>().First(c=>c.Name=="Algebraic Vertex Constraints");
var pf=vc.Params.Output[1].VolatileData.AllData(true).First();
// bbox of everything previewed
var bb=BoundingBox.Empty; foreach(var o in d.Objects.OfType<IGH_PreviewObject>()) if(!o.Hidden) bb.Union(o.ClippingBox);
Console.WriteLine("bbox "+bb.Min+" .. "+bb.Max);
foreach(var c in d.Objects.OfType<IGH_Component>()) if(!((IGH_PreviewObject)c).Hidden) Console.WriteLine("visible "+c.Name+" clip "+((IGH_PreviewObject)c).ClippingBox.Min+" .. "+((IGH_PreviewObject)c).ClippingBox.Max);
