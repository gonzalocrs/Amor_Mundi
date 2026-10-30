using Grasshopper; using Grasshopper.Kernel; using Grasshopper.Kernel.Types; using Grasshopper.Kernel.Parameters; using Rhino.Geometry;
var sb=new System.Text.StringBuilder();
var doc=new GH_Document();
IGH_Component Add(string name){ var p=Instances.ComponentServer.ObjectProxies.First(x=>x.Desc.Name==name && !x.Obsolete && x.Kind==GH_ObjectType.CompiledObject && typeof(IGH_Component).IsAssignableFrom(x.Type)); var o=(IGH_Component)p.CreateInstance(); o.CreateAttributes(); doc.AddObject(o,false); return o;}
IGH_Param In(IGH_Component c, string n)=> c.Params.Input.First(i=>i.Name==n||i.NickName==n);
IGH_Param Out(IGH_Component c, string n)=> c.Params.Output.First(i=>i.Name==n||i.NickName==n);
void W(IGH_Component a,string o,IGH_Component b,string i){ In(b,i).AddSource(Out(a,o)); }
void Num(IGH_Component c,string n,double v){ var p=(Param_Number)In(c,n); p.PersistentData.Clear(); p.PersistentData.Append(new GH_Number(v)); }
void Int(IGH_Component c,string n,int v){ var p=(Param_Integer)In(c,n); p.PersistentData.Clear(); p.PersistentData.Append(new GH_Integer(v)); }
void Bool(IGH_Component c,string n,bool v){ var p=(Param_Boolean)In(c,n); p.PersistentData.Clear(); p.PersistentData.Append(new GH_Boolean(v)); }
void Pts(IGH_Component c,string n,IEnumerable<Point3d> v){ var p=(Param_Point)In(c,n); p.PersistentData.Clear(); foreach(var q in v) p.PersistentData.Append(new GH_Point(q)); }
void Ints(IGH_Component c,string n,IEnumerable<int> v){ var p=(Param_Integer)In(c,n); p.PersistentData.Clear(); foreach(var q in v) p.PersistentData.Append(new GH_Integer(q)); }
List<object> D(IGH_Component c,string n)=> Out(c,n).VolatileData.AllData(true).Select(g=>g.ScriptVariable()).ToList();
string Msg(IGH_Component c)=> c.Name+": "+c.RuntimeMessageLevel+" "+string.Join(" | ",c.RuntimeMessages(GH_RuntimeMessageLevel.Error).Concat(c.RuntimeMessages(GH_RuntimeMessageLevel.Warning)));
var sw=System.Diagnostics.Stopwatch.StartNew();
IGH_Component AddG(string g){ var o=(IGH_Component)Instances.ComponentServer.EmitObject(new Guid(g)); o.CreateAttributes(); doc.AddObject(o,false); return o;}
void Pl(IGH_Component c,string n,Plane v){ var p=(Param_Plane)In(c,n); p.PersistentData.Clear(); p.PersistentData.Append(new GH_Plane(v)); }
void Solve(){ doc.Enabled=true; doc.NewSolution(false, GH_SolutionMode.Silent); }
void Geo(IGH_Component c,string n,IEnumerable<Point3d> v){ var p=(Param_Geometry)In(c,n); p.PersistentData.Clear(); foreach(var q in v) p.PersistentData.Append(new GH_Point(q)); }
void Nums(IGH_Component c,string n,IEnumerable<double> v){ var p=(Param_Number)In(c,n); p.PersistentData.Clear(); foreach(var q in v) p.PersistentData.Append(new GH_Number(q)); }
