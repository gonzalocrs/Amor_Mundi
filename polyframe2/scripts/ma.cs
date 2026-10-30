using Grasshopper; using Grasshopper.Kernel; using Grasshopper.Kernel.Special; using Grasshopper.Kernel.Types; using Grasshopper.Kernel.Parameters; using Rhino.Geometry;
IGH_Component Mk(GH_Document d,string name){ var p=Instances.ComponentServer.ObjectProxies.First(q=>q.Desc.Name==name && !q.Obsolete && typeof(IGH_Component).IsAssignableFrom(q.Type)); var o=(IGH_Component)p.CreateInstance(); o.CreateAttributes(); d.AddObject(o,false); return o; }
List<T> O<T>(IGH_Component c,string n)=>c.Params.Output.First(o=>o.Name==n).VolatileData.AllData(true).Select(x=>(T)x.ScriptVariable()).ToList();
(List<double> F, int ki, int si, List<Line> Ls) MA(List<Line> bars,List<Point3d> sup,List<Vector3d> loads,List<Point3d> locs){
 var d=new GH_Document(); var ma=Mk(d,"Matrix Analysis Generic Structures");
 var p0=(Param_Geometry)ma.Params.Input[0]; foreach(var l in bars) p0.PersistentData.Append(new GH_Line(l));
 var p1=(Param_Point)ma.Params.Input[1]; foreach(var s in sup) p1.PersistentData.Append(new GH_Point(s));
 var p2=(Param_Vector)ma.Params.Input[2]; foreach(var v in loads) p2.PersistentData.Append(new GH_Vector(v));
 var p3=(Param_Point)ma.Params.Input[3]; foreach(var s in locs) p3.PersistentData.Append(new GH_Point(s));
 ((Param_Number)ma.Params.Input[4]).PersistentData.Append(new GH_Number(1)); ((Param_Number)ma.Params.Input[5]).PersistentData.Append(new GH_Number(1));
 d.Enabled=true; d.NewSolution(false,GH_SolutionMode.Silent);
 var msgs=string.Join("|",ma.RuntimeMessages(GH_RuntimeMessageLevel.Error).Concat(ma.RuntimeMessages(GH_RuntimeMessageLevel.Warning))); if(msgs.Length>0) Console.WriteLine("  MA msg: "+msgs);
 var F=O<double>(ma,"Forces"); var Ls=O<Line>(ma,"Lines"); var ki=O<int>(ma,"Kinematic Indeterminacy").FirstOrDefault(); var si=O<int>(ma,"Static Indeterminacy").FirstOrDefault();
 d.Enabled=false; d.Dispose(); return (F,ki,si,Ls);
}
// sign test: 3-bar truss: two legs to apex, apex loaded down
var t=MA(new List<Line>{new Line(new Point3d(0,0,0),new Point3d(1000,0,1000)),new Line(new Point3d(2000,0,0),new Point3d(1000,0,1000)),new Line(new Point3d(1000,-1000,0),new Point3d(1000,0,1000))}, new List<Point3d>{new Point3d(0,0,0),new Point3d(2000,0,0),new Point3d(1000,-1000,0)}, new List<Vector3d>{new Vector3d(0,0,-10)}, new List<Point3d>{new Point3d(1000,0,1000)});
Console.WriteLine("sign test (legs under downward load should be compression): forces "+string.Join(", ",t.F.Select(x=>x.ToString("0.00")))+" KI "+t.ki+" SI "+t.si);
