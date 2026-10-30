using Grasshopper; using Grasshopper.Kernel; using Grasshopper.Kernel.Types; using Rhino.Geometry;
var d=Instances.ActiveCanvas.Document;
var ec=d.Objects.OfType<IGH_Component>().First(c=>c.Name=="Algebraic Edge Constraints");
IGH_Component Add(string name){ var p=Instances.ComponentServer.ObjectProxies.First(q=>q.Desc.Name==name && !q.Obsolete && typeof(IGH_Component).IsAssignableFrom(q.Type)); var o=(IGH_Component)p.CreateInstance(); o.CreateAttributes(); d.AddObject(o,false); return o; }
var ex=Add("Explode PFoam"); ex.Params.Input[0].AddSource(ec.Params.Output[1]);
var ie=Add("Inspect PFEdge"); ie.Params.Input[0].AddSource(ex.Params.Output[1]);
d.NewSolution(false);
List<T> O<T>(IGH_Component c,string n)=>c.Params.Output.First(o=>o.Name==n).VolatileData.AllData(true).Select(x=>(T)x.ScriptVariable()).ToList();
var X=O<int>(ie,"External"); var L=O<Line>(ie,"Line"); var F=O<double>(ie,"Force");
int nv=0,nr=0; var rs=new List<string>();
for(int i=0;i<X.Count;i++) if(X[i]==2){ var v=L[i].Direction; v.Unitize(); bool vert=Math.Abs(v.Z)>0.999; if(vert) nv++; else { nr++; rs.Add("("+(L[i].From.X/1000).ToString("0.0")+","+(L[i].From.Y/1000).ToString("0.0")+","+(L[i].From.Z/1000).ToString("0.0")+") dir("+v.X.ToString("0.00")+","+v.Y.ToString("0.00")+","+v.Z.ToString("0.00")+")"); } }
Console.WriteLine("force edges: vertical "+nv+" non-vertical "+nr); Console.WriteLine(string.Join("\n",rs));
d.RemoveObject(ex,false); d.RemoveObject(ie,false); d.NewSolution(false);
