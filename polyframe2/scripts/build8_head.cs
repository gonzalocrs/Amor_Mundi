using Grasshopper; using Grasshopper.Kernel; using Grasshopper.Kernel.Types; using Grasshopper.Kernel.Parameters; using Grasshopper.Kernel.Special; using Rhino.Geometry; using System.Drawing;
var sb=new System.Text.StringBuilder();
GH_Document cur=null; var hookNames=new Dictionary<Guid,string>();
IGH_Component Add(string name,float x,float y){ var p=Instances.ComponentServer.ObjectProxies.First(q=>q.Desc.Name==name && !q.Obsolete && q.Kind==GH_ObjectType.CompiledObject && typeof(IGH_Component).IsAssignableFrom(q.Type)); var o=(IGH_Component)p.CreateInstance(); o.CreateAttributes(); o.Attributes.Pivot=new PointF(x,y); cur.AddObject(o,false); return o;}
IGH_Component AddG(string g,float x,float y){ var o=(IGH_Component)Instances.ComponentServer.EmitObject(new Guid(g)); o.CreateAttributes(); o.Attributes.Pivot=new PointF(x,y); cur.AddObject(o,false); return o;}
IGH_Param In(IGH_Component c, string n)=> c.Params.Input.First(i=>i.Name==n||i.NickName==n);
IGH_Param Out(IGH_Component c, string n)=> c.Params.Output.First(i=>i.Name==n||i.NickName==n);
void W(IGH_Component a,string o,IGH_Component b,string i){ In(b,i).AddSource(Out(a,o)); }
void Num(IGH_Component c,string n,double v){ var q=In(c,n); if(q is Param_GenericObject pg){ pg.PersistentData.Clear(); pg.PersistentData.Append(new GH_Number(v)); return;} var p=(Param_Number)q; p.PersistentData.Clear(); p.PersistentData.Append(new GH_Number(v)); }
void Nums(IGH_Component c,string n,IEnumerable<double> v){ var p=(Param_Number)In(c,n); p.PersistentData.Clear(); foreach(var q in v) p.PersistentData.Append(new GH_Number(q)); }
void Int(IGH_Component c,string n,int v){ var p=(Param_Integer)In(c,n); p.PersistentData.Clear(); p.PersistentData.Append(new GH_Integer(v)); }
void Bool(IGH_Component c,string n,bool v){ var p=(Param_Boolean)In(c,n); p.PersistentData.Clear(); p.PersistentData.Append(new GH_Boolean(v)); }
void Pl(IGH_Component c,string n,Plane v){ var p=(Param_Plane)In(c,n); p.PersistentData.Clear(); p.PersistentData.Append(new GH_Plane(v)); }
void Hide(IGH_DocumentObject c){ ((IGH_PreviewObject)c).Hidden=true; }
GH_ClusterInputHook HIn(string name,float y){ var h=new GH_ClusterInputHook(); h.CreateAttributes(); h.Name=name; h.NickName=name; h.Attributes.Pivot=new PointF(0,y); cur.AddObject(h,false); hookNames[h.InstanceGuid]=name; return h; }
GH_ClusterOutputHook HOut(string name,IGH_Param src,float y){ var h=new GH_ClusterOutputHook(); h.CreateAttributes(); h.Name=name; h.NickName=name; h.Attributes.Pivot=new PointF(2400,y); h.AddSource(src); cur.AddObject(h,false); hookNames[h.InstanceGuid]=name; return h; }
GH_Cluster MakeCluster(GH_Document inner,GH_Document outer,string name,string desc,float x,float y){ 
 var ins=inner.Objects.OfType<GH_ClusterInputHook>().OrderBy(h=>h.Attributes.Pivot.Y).Select(h=>hookNames[h.InstanceGuid]).ToList(); var outs=inner.Objects.OfType<GH_ClusterOutputHook>().OrderBy(h=>h.Attributes.Pivot.Y).Select(h=>hookNames[h.InstanceGuid]).ToList();
 foreach(var h in inner.Objects.OfType<GH_ClusterInputHook>()){ h.Name=hookNames[h.InstanceGuid]; h.NickName=hookNames[h.InstanceGuid]; } foreach(var h in inner.Objects.OfType<GH_ClusterOutputHook>()){ h.Name=hookNames[h.InstanceGuid]; h.NickName=hookNames[h.InstanceGuid]; }
 var cl=new GH_Cluster(); cl.CreateAttributes(); cl.CreateFromDocument(inner);
 for(int i=0;i<cl.Params.Input.Count&&i<ins.Count;i++){ cl.Params.Input[i].Name=ins[i]; cl.Params.Input[i].NickName=ins[i]; }
 for(int i=0;i<cl.Params.Output.Count&&i<outs.Count;i++){ cl.Params.Output[i].Name=outs[i]; cl.Params.Output[i].NickName=outs[i]; } cl.Name=name; cl.NickName=name; cl.Description=desc; cl.Attributes.Pivot=new PointF(x,y); outer.AddObject(cl,false); return cl; }
IGH_Param CIn(GH_Cluster c,string n){ var r=c.Params.Input.FirstOrDefault(p=>p.NickName==n||p.Name==n); if(r==null) throw new Exception("cluster "+c.NickName+" inputs: "+string.Join(",",c.Params.Input.Select(p=>p.Name+"/"+p.NickName))+" outputs: "+string.Join(",",c.Params.Output.Select(p=>p.Name+"/"+p.NickName))); return r; }
IGH_Param COut(GH_Cluster c,string n){ var r=c.Params.Output.FirstOrDefault(p=>p.NickName==n||p.Name==n); if(r==null) throw new Exception("cluster "+c.NickName+" outputs: "+string.Join(",",c.Params.Output.Select(p=>p.Name+"/"+p.NickName))); return r; }

