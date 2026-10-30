using Grasshopper; using Grasshopper.Kernel; using Grasshopper.Kernel.Special; using Grasshopper.Kernel.Types; using Grasshopper.Kernel.Parameters; using Rhino.Geometry;
var d=Instances.ActiveCanvas.Document;
var vc=d.Objects.OfType<IGH_Component>().First(c=>c.Name=="Algebraic Vertex Constraints");
var ec=d.Objects.OfType<IGH_Component>().FirstOrDefault(c=>c.Name=="Algebraic Edge Constraints");
if(ec==null){ ec=(IGH_Component)Instances.ComponentServer.EmitObject(new Guid("e6c06aca-60ed-4611-b9e2-7a08eae8d96b")); ec.CreateAttributes(); ec.Attributes.Pivot=new System.Drawing.PointF(1100,900); d.AddObject(ec,false); ec.Params.Input[0].AddSource(vc.Params.Output[0]); }
var tx=d.Objects.OfType<IGH_Component>().First(c=>c.NickName=="TX"); tx.Params.Input[0].RemoveAllSources(); tx.Params.Input[0].AddSource(ec.Params.Output[1]);
var pi=(Param_Integer)ec.Params.Input[1]; pi.PersistentData.Clear(); foreach(var i in new[]{113,126}) pi.PersistentData.Append(new GH_Integer(i));
var pl=ec.Params.Input[2]; var pln=(GH_PersistentParam<GH_Number>)pl; pln.PersistentData.Clear(); foreach(var v in new double[]{__L__}) pln.PersistentData.Append(new GH_Number(v));
var ps=(GH_PersistentParam<GH_Number>)ec.Params.Input[3]; ps.PersistentData.Clear(); ps.PersistentData.Append(new GH_Number(1));
Console.WriteLine("ec inputs: "+string.Join(", ",ec.Params.Input.Select(i=>i.Name+":"+i.TypeName)));
ec.ExpireSolution(false);
