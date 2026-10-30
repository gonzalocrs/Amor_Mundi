using Grasshopper; using Grasshopper.Kernel; using Grasshopper.Kernel.Special; using Rhino.Geometry;
var sb=new System.Text.StringBuilder();
var doc=Instances.ActiveCanvas.Document;
var c1=doc.Objects.OfType<GH_Cluster>().First(c=>c.NickName=="Octagon force diagram");
var d=c1.Document("");
foreach(var o in d.Objects.OfType<IGH_Component>()){ if(o.Name=="Evaluate Length"||o.Name=="Curve Middle"||o.Name=="Divide Curve"||o.Name=="Addition"||o.Name=="Mesh Closest Point"||o.Name=="Delaunay Mesh"){ foreach(var p in o.Params.Output.Take(1)) sb.AppendLine(o.Name+"."+p.Name+": "+string.Join(" ",p.VolatileData.AllData(true).Select(x=>x.ToString()).Take(10))); } }
Console.WriteLine(sb.ToString());
