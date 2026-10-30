using Grasshopper; using Grasshopper.Kernel; using Grasshopper.Kernel.Special; using Grasshopper.Kernel.Types; using Grasshopper.Kernel.Parameters; using Rhino.Geometry;
var d=Instances.ActiveCanvas.Document;
var sz=d.Objects.OfType<GH_NumberSlider>().First(s=>s.Recipients.Any(r=>r.Attributes.GetTopLevel.DocObject.Name=="Scale NU")); sz.SetSliderValue(0.66m); sz.ExpireSolution(false);
var ec=d.Objects.OfType<IGH_Component>().First(c=>c.Name=="Algebraic Edge Constraints");
var pp=(IGH_Component)Instances.ComponentServer.EmitObject(new Guid("bd68a6a9-99fb-4731-a688-e8ff10a1ce34")); pp.CreateAttributes(); pp.NickName="DEVCHK"; d.AddObject(pp,false); pp.Params.Input[0].AddSource(ec.Params.Output[1]);
((GH_PersistentParam<GH_Integer>)pp.Params.Input[1]).PersistentData.Append(new GH_Integer(1)); ((GH_PersistentParam<GH_Number>)pp.Params.Input[2]).PersistentData.Append(new GH_Number(0.01)); ((GH_PersistentParam<GH_Number>)pp.Params.Input[3]).PersistentData.Append(new GH_Number(0));
d.NewSolution(false);
Console.WriteLine("dev "+string.Join(",",pp.Params.Output[1].VolatileData.AllData(true)));
d.RemoveObject(pp,false); d.NewSolution(false);
var ie=d.Objects.OfType<IGH_Component>().First(c=>c.NickName=="TE");
var L=ie.Params.Output.First(o=>o.Name=="Line").VolatileData.AllData(true).Select(x=>((GH_Line)x).Value).ToList();
double maxY=-1e9,maxX=-1e9,minY=1e9,minX=1e9; foreach(var l in L) for(double t=0;t<=1;t+=0.01){ var p=l.PointAt(t); if(Math.Abs(p.X)<500){maxY=Math.Max(maxY,p.Y);minY=Math.Min(minY,p.Y);} if(Math.Abs(p.Y)<500){maxX=Math.Max(maxX,p.X);minX=Math.Min(minX,p.X);} }
Console.WriteLine("curve-in: +y "+(5000-maxY).ToString("0")+" -y "+(5000+minY).ToString("0")+" +x "+(5000-maxX).ToString("0")+" -x "+(5000+minX).ToString("0")+" mm");
