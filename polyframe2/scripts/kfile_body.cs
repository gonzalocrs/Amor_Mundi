using Grasshopper; using Grasshopper.Kernel; using Grasshopper.Kernel.Types; using Grasshopper.Kernel.Parameters; using GH_IO.Serialization; using Rhino.Geometry;
double HCMV=25.0, WCMV=15.0;
var sb=new System.Text.StringBuilder();
// ---- copy configured Karamba components from Gonzalo's model (read only) ----
var io=new GH_DocumentIO(); io.Open(@"C:\Users\gonza\Documents\GitHub\pyramid-roof\grasshopper\Pyramide Karamba 10_14_2026.gh"); var src=io.Document;
var kc=src.Objects.OfType<IGH_Component>().Where(c=>c.Category.StartsWith("Karamba")).ToList();
IGH_Component Find(Func<IGH_Component,bool> f)=>kc.First(f);
var oMat=Find(c=>c.Name.StartsWith("Material Properties") && c.Params.Input.First(i=>i.Name.StartsWith("Young")).Sources.All(s=>s.Attributes.GetTopLevel.DocObject.NickName!="Py3"));
var oCs=Find(c=>c.NickName=="Trapezoid");
var oL2B=Find(c=>c.NickName=="LineToBeam" && c.Params.Input[0].Sources.Any(s=>s.NickName=="rib_lines"));
var oSup=Find(c=>c.NickName=="Supp" && c.Params.Input[0].Sources.Any(s=>s.NickName=="supports"));
var oGrav=Find(c=>c.NickName=="Gravity");
var oML=Find(c=>c.NickName=="MeshLoad Const" && c.Params.Input[0].Sources.Any(s=>s.NickName=="cladding"));
var oAsm=Find(c=>c.NickName=="Assemble"); var oAn=Find(c=>c.NickName=="Analyse");
var oBF=Find(c=>c.NickName=="B-Forces"); var oRF=Find(c=>c.NickName=="React"); var oBuck=Find(c=>c.NickName=="Buckling Modes"); var oTh2=Find(c=>c.NickName=="AnalyseThII");
// record the original inputs' source values (sliders/panels) for reporting
string SrcVals(IGH_Component c)=>string.Join("; ",c.Params.Input.Where(i=>i.SourceCount>0).Select(i=>i.Name+"="+string.Join(",",i.Sources.Select(s=>{ var o=s.Attributes.GetTopLevel.DocObject; if(o is Grasshopper.Kernel.Special.GH_NumberSlider sl) return sl.CurrentValue.ToString(); if(o is Grasshopper.Kernel.Special.GH_Panel p) return "'"+p.UserText+"'"; if(o is Grasshopper.Kernel.Special.GH_ValueList vl) return vl.FirstSelectedItem?.Name; return o.NickName; }))));
var srcInfo="cast material inputs: "+SrcVals(oMat)+"\n  gravity: "+SrcVals(oGrav)+"\n  meshload LCase: "+SrcVals(oML)+"\n  buckling: "+SrcVals(oBuck)+"\n  thII: "+SrcVals(oTh2)+"\n  BF: "+SrcVals(oBF);
GH_Document doc=new GH_Document();
IGH_Component Clone(IGH_Component o){ var w=new GH_LooseChunk("c"); o.Write(w); var c=(IGH_Component)Instances.ComponentServer.EmitObject(o.ComponentGuid); c.CreateAttributes(); var r=new GH_LooseChunk("c"); r.Deserialize_Binary(w.Serialize_Binary()); c.Read(r); c.NewInstanceGuid(); foreach(var p in c.Params.Input) { p.RemoveAllSources(); p.NewInstanceGuid(); } foreach(var p in c.Params.Output) p.NewInstanceGuid(); doc.AddObject(c,false); return c; }
var keep=new List<(string name,IGH_Component asm,IGH_Component an,IGH_Component bf,IGH_Component rf,IGH_Component buck,List<IGH_Component> all)>();
IGH_Component Mk(GH_Document d,string name){ var p=Instances.ComponentServer.ObjectProxies.First(q=>q.Desc.Name==name && !q.Obsolete && typeof(IGH_Component).IsAssignableFrom(q.Type)); var o=(IGH_Component)p.CreateInstance(); o.CreateAttributes(); d.AddObject(o,false); return o; }
List<T> O2<T>(IGH_Component c,string n)=>c.Params.Output.First(o=>o.Name.StartsWith(n)||o.NickName.StartsWith(n)).VolatileData.AllData(true).Select(x=>(T)x.ScriptVariable()).ToList();
Mesh Pyr(double dx){ var m=new Mesh(); var A=new Point3d(dx,0,6670); var C=new[]{new Point3d(dx-5000,-5000,0),new Point3d(dx+5000,-5000,0),new Point3d(dx+5000,5000,0),new Point3d(dx-5000,5000,0)}; int n=24;
 for(int f=0;f<4;f++){ var p=C[f]; var q=C[(f+1)%4]; var idx=new int[n+1,n+1];
  for(int i=0;i<=n;i++) for(int j=0;j<=n-i;j++){ double u=(double)i/n, v=(double)j/n; idx[i,j]=m.Vertices.Count; m.Vertices.Add(p+(q-p)*u+(A-p)*v); }
  for(int i=0;i<n;i++) for(int j=0;j<n-i;j++){ m.Faces.AddFace(idx[i,j],idx[i+1,j],idx[i,j+1]); if(j<n-i-1) m.Faces.AddFace(idx[i+1,j],idx[i+1,j+1],idx[i,j+1]); } }
 m.Normals.ComputeNormals(); m.Compact(); return m; }
(List<Line> bars,List<Point3d> feet) Geom(string f,double dx){
 var io2=new GH_DocumentIO(); io2.Open("C:/Users/gonza/Documents/GitHub/pyramid-roof/polyframe2/"+f+".gh"); var d=io2.Document; d.Enabled=true;
 var perp=d.Objects.OfType<IGH_Component>().First(c=>c.Name=="PFPerp");
 var ex=Mk(d,"Explode PFoam"); ex.Params.Input[0].AddSource(perp.Params.Output[0]); var ie=Mk(d,"Inspect PFEdge"); ie.Params.Input[0].AddSource(ex.Params.Output[1]);
 d.NewSolution(false,GH_SolutionMode.Silent);
 var L=O2<Line>(ie,"Line"); var X=O2<int>(ie,"External");
 var nodes=new List<Point3d>(); int Id(Point3d p){ for(int i=0;i<nodes.Count;i++) if(nodes[i].DistanceTo(p)<1) return i; nodes.Add(p); return nodes.Count-1; }
 var bars=new List<Line>(); var seen=new HashSet<(int,int)>(); for(int i=0;i<L.Count;i++) if(X[i]==0){ int a=Id(L[i].From), b=Id(L[i].To); if(a==b) continue; var k=(Math.Min(a,b),Math.Max(a,b)); if(seen.Add(k)) bars.Add(new Line(nodes[a],nodes[b])); }
 var feet=new List<Point3d>(); for(int i=0;i<L.Count;i++) if(X[i]==2){ var v=L[i].Direction; v.Unitize(); if(Math.Abs(v.Z)<0.999){ foreach(var p in new[]{L[i].From,L[i].To}) if(nodes.Any(n=>n.DistanceTo(p)<1) && p.Z<500 && !feet.Any(q=>q.DistanceTo(p)<1)) feet.Add(p); } }
 d.Enabled=false; d.Dispose(); var t=Transform.Translation(dx,0,0); for(int i=0;i<bars.Count;i++){ var l=bars[i]; l.Transform(t); bars[i]=l; } for(int i=0;i<feet.Count;i++){ var p=feet[i]; p.Transform(t); feet[i]=p; } return (bars,feet); }
float yy=0;
foreach(var (f,dx) in new[]{("friend-AP8-diagrid",0.0),("friend-16-diagrid",14000.0)}){
 var g=Geom(f,dx);
 var mat=Clone(oMat); var cs=Clone(oCs); var l2b=Clone(oL2B); var sup=Clone(oSup); var grav=Clone(oGrav); var ml=Clone(oML); var asm=Clone(oAsm); var an=Clone(oAn); var bf=Clone(oBF); var rf=Clone(oRF); var buck=Clone(oBuck); var th2=Clone(oTh2);
 
 IGH_Param In(IGH_Component c,string n){ var r=c.Params.Input.FirstOrDefault(i=>i.Name.StartsWith(n)||i.NickName.StartsWith(n)); if(r==null) throw new Exception(c.Name+" no input "+n+": "+string.Join(",",c.Params.Input.Select(i=>i.Name+"/"+i.NickName))); return r; }
 IGH_Param Out(IGH_Component c,string n){ var r=c.Params.Output.FirstOrDefault(i=>i.Name.StartsWith(n)||i.NickName.StartsWith(n)); if(r==null) throw new Exception(c.Name+" no output "+n+": "+string.Join(",",c.Params.Output.Select(i=>i.Name+"/"+i.NickName))); return r; }
 void SetV(IGH_Param p,params object[] vals){ var pd=p.GetType().GetProperty("PersistentData"); var st=pd.GetValue(p); st.GetType().GetMethod("Clear").Invoke(st,null); foreach(var v in vals){ IGH_Goo g= v is double dd? new GH_Number(dd) : v is int ii? new GH_Integer(ii) : v is string ss? new GH_String(ss) : v is bool bb? new GH_Boolean(bb) : v is Point3d pp? new GH_Point(pp) : v is Vector3d vv? new GH_Vector(vv) : v is Line ll? new GH_Line(ll) : v is Mesh mm? new GH_Mesh(mm) : (IGH_Goo)v; var t=p.Type; object gg=g; if(!t.IsAssignableFrom(g.GetType())){ var inst=(IGH_Goo)Activator.CreateInstance(t); inst.CastFrom(g is GH_String gs? (object)gs.Value : g.ScriptVariable()); gg=inst; } st.GetType().GetMethods().First(m=>m.Name=="Append"&&m.GetParameters().Length==1).Invoke(st,new[]{gg}); } }
 // material: C30/37 cast as in the 19 Oct model
 SetV(In(mat,"Family"),"Concrete"); SetV(In(mat,"Name"),"C30/37 cast"); SetV(In(mat,"Young"),3280.0); SetV(In(mat,"In-plane"),3280.0/2.4); SetV(In(mat,"Transverse"),3280.0/2.4); SetV(In(mat,"Specific"),24.0); SetV(In(mat,"Tensile"),0.29); SetV(In(mat,"Compressive"),-2.0);
 In(cs,"Material").AddSource(Out(mat,"Mat")); SetV(In(cs,"Name"),"rib 150x250"); SetV(In(cs,"Height"),HCMV); SetV(In(cs,"Upper"),WCMV); SetV(In(cs,"Lower"),WCMV);
 In(l2b,"Line").RemoveAllSources(); SetV(In(l2b,"Identifier"),"rib"); In(l2b,"Cross-section").AddSource(Out(cs,"CroSec"));
 SetV(In(grav,"LCase"),"G"); SetV(In(ml,"LCase"),"G");
 In(asm,"Elem").AddSource(Out(l2b,"Elem")); In(asm,"Support").AddSource(Out(sup,"Supp")); In(asm,"Load").AddSource(Out(grav,"Load")); In(asm,"Load").AddSource(Out(ml,"Load"));
 In(an,"Model").AddSource(Out(asm,"Model")); In(bf,"Analysed").AddSource(Out(an,"Analysed")); In(rf,"Analysed").AddSource(Out(an,"Analysed"));
 In(th2,"Model").AddSource(Out(asm,"Model")); In(buck,"Model").AddSource(Out(th2,"Analysed")); SetV(In(buck,"Number of Modes"),3);
 
 SetV(In(th2,"Load Cases"),"G"); SetV(In(bf,"Load Case"),"G"); SetV(In(rf,"Load Case"),"G"); SetV(In(bf,"ts"),0.0,0.5,1.0); SetV(In(buck,"Number of Modes"),1);
 SetV(In(l2b,"Line"),g.bars.Cast<object>().ToArray()); SetV(In(sup,"Pos"),g.feet.Cast<object>().ToArray());
 SetV(In(ml,"Vec"),new Vector3d(0,0,-7)); SetV(In(ml,"Mesh"),Pyr(dx));
 var all=new List<IGH_Component>{mat,cs,l2b,sup,grav,ml,asm,an,bf,rf,buck,th2};
 float x=0; foreach(var c in all){ c.Attributes.Pivot=new System.Drawing.PointF(80+x,80+yy); x+=170; }
 keep.Add((f,asm,an,bf,rf,buck,all)); yy+=260;
}
src.Dispose();
