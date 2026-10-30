using Grasshopper; using Grasshopper.Kernel;
var d=Instances.ActiveCanvas.Document; foreach(var c in d.Objects.OfType<IGH_Component>().Where(c=>c.Name=="Discontinuity")) Console.WriteLine("disc: "+string.Join(" ; ",c.Params.Output[0].VolatileData.AllData(true).Select(x=>x.ToString())));
var pc=d.Objects.OfType<IGH_Component>().First(c=>c.Name=="Project Curve"); double zmax=-1; foreach(var g in pc.Params.Output[0].VolatileData.AllData(true)){ var cv=(Rhino.Geometry.Curve)g.ScriptVariable(); zmax=Math.Max(zmax,cv.GetBoundingBox(true).Max.Z);} Console.WriteLine("projected curves max z "+zmax);
