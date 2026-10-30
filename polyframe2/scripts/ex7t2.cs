using Grasshopper; using Grasshopper.Kernel; using Grasshopper.Kernel.Special; using Grasshopper.Kernel.Types; using Grasshopper.Kernel.Parameters; using Rhino.Geometry;
var d=Instances.ActiveCanvas.Document;
var vc=d.Objects.OfType<IGH_Component>().First(c=>c.Name=="Algebraic Vertex Constraints");
var pin=(Param_Geometry)vc.Params.Input[2]; 
if(pin.SourceCount>0){ pin.RemoveAllSources(); pin.PersistentData.Clear(); foreach(var p in new[]{new Point3d(-5000,5000,0),new Point3d(-5000,-5000,0),new Point3d(5000,-5000,0),new Point3d(5000,5000,0)}) pin.PersistentData.Append(new GH_Point(p)); }
IGH_Component Add(string name){ var p=Instances.ComponentServer.ObjectProxies.First(q=>q.Desc.Name==name && !q.Obsolete && typeof(IGH_Component).IsAssignableFrom(q.Type)); var o=(IGH_Component)p.CreateInstance(); o.CreateAttributes(); o.Attributes.Pivot=new System.Drawing.PointF(900,900); d.AddObject(o,false); return o; }
var ex=d.Objects.OfType<IGH_Component>().FirstOrDefault(c=>c.NickName=="TX"); IGH_Component ie,iv;
if(ex==null){ ex=Add("Explode PFoam"); ex.NickName="TX"; ex.Params.Input[0].AddSource(vc.Params.Output[1]); var sp=Add("Separate PFEdges By Type"); sp.Params.Input[0].AddSource(ex.Params.Output[1]); ie=Add("Inspect PFEdge"); ie.NickName="TE"; ie.Params.Input[0].AddSource(sp.Params.Output[0]); iv=Add("Inspect PFVertex"); iv.NickName="TV"; iv.Params.Input[0].AddSource(ex.Params.Output[0]); }
ie=d.Objects.OfType<IGH_Component>().First(c=>c.NickName=="TE"); iv=d.Objects.OfType<IGH_Component>().First(c=>c.NickName=="TV");
var sz=d.Objects.OfType<GH_NumberSlider>().First(s=>s.Recipients.Any(r=>r.Attributes.GetTopLevel.DocObject.Name=="Scale NU"));
sz.Slider.Maximum=10;
foreach(var z in new[]{__Z__}){ sz.SetSliderValue((decimal)z); sz.ExpireSolution(false); var sw=System.Diagnostics.Stopwatch.StartNew(); d.NewSolution(false);
 var F=ie.Params.Output.First(o=>o.Name=="Force").VolatileData.AllData(true).Select(x=>((GH_Number)x).Value).ToList();
 var P=iv.Params.Output.First(o=>o.Name=="Point").VolatileData.AllData(true).Select(x=>((GH_Point)x).Value).ToList(); var X=iv.Params.Output.First(o=>o.Name=="External").VolatileData.AllData(true).Select(x=>((GH_Boolean)x).Value).ToList();
 var ip=P.Where((p,i)=>!X[i]).ToList(); var bb=new BoundingBox(ip);
 var L=ie.Params.Output.First(o=>o.Name=="Line").VolatileData.AllData(true).Select(x=>((GH_Line)x).Value).ToList(); var tb=new List<string>(); for(int i=0;i<F.Count;i++) if(F[i]<-1e-9) tb.Add(F[i].ToString("0")+"@"+L[i].Length.ToString("0")+"mm mid("+(L[i].PointAt(0.5).X/1000).ToString("0.0")+","+(L[i].PointAt(0.5).Y/1000).ToString("0.0")+","+(L[i].PointAt(0.5).Z/1000).ToString("0.0")+")");
 Console.WriteLine("  Fmax "+F.Max().ToString("0")+" T: "+string.Join(" ",tb));
 Console.WriteLine("ScaleZ "+z+" ms "+sw.ElapsedMilliseconds+" bars "+F.Count/2+" T "+F.Count(f=>f<-1e-9)/2+" nodes "+ip.Count+" bbox "+bb.Min+" .. "+bb.Max);
}
