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
IGH_Component Clone(IGH_Component o){ var w=new GH_LooseChunk("c"); o.Write(w); var c=(IGH_Component)Instances.ComponentServer.EmitObject(o.ComponentGuid); c.CreateAttributes(); var r=new GH_LooseChunk("c"); r.Deserialize_Binary(w.Serialize_Binary()); c.Read(r); c.NewInstanceGuid(); foreach(var p in c.Params.Input) p.RemoveAllSources(); doc.AddObject(c,false); return c; }
var mat=Clone(oMat); var cs=Clone(oCs); var l2b=Clone(oL2B); var sup=Clone(oSup); var grav=Clone(oGrav); var ml=Clone(oML); var asm=Clone(oAsm); var an=Clone(oAn); var bf=Clone(oBF); var rf=Clone(oRF); var buck=Clone(oBuck); var th2=Clone(oTh2);
src.Dispose();
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
In(th2,"Model").AddSource(Out(asm,"Model")); In(buck,"Model").AddSource(Out(th2,"Analysed")); SetV(In(buck,"Number of Modes"),1);
// ---- roof runs ----
SetV(In(th2,"Load Cases"),"G"); SetV(In(bf,"Load Case"),"G"); SetV(In(rf,"Load Case"),"G"); SetV(In(bf,"ts"),0.0,0.5,1.0);
// full pyramid surface mesh (10x10 plan, apex 6670), 24x24 subdivision per face
Mesh Pyr(){ var m=new Mesh(); var A=new Point3d(0,0,6670); var C=new[]{new Point3d(-5000,-5000,0),new Point3d(5000,-5000,0),new Point3d(5000,5000,0),new Point3d(-5000,5000,0)}; int n=24;
 for(int f=0;f<4;f++){ var p=C[f]; var q=C[(f+1)%4]; int b=m.Vertices.Count; var idx=new int[n+1,n+1];
  for(int i=0;i<=n;i++) for(int j=0;j<=n-i;j++){ double u=(double)i/n, v=(double)j/n; var pt=p+(q-p)*u+(A-p)*v; idx[i,j]=m.Vertices.Count; m.Vertices.Add(pt); }
  for(int i=0;i<n;i++) for(int j=0;j<n-i;j++){ m.Faces.AddFace(idx[i,j],idx[i+1,j],idx[i,j+1]); if(j<n-i-1) m.Faces.AddFace(idx[i+1,j],idx[i+1,j+1],idx[i,j+1]); } }
 m.Normals.ComputeNormals(); m.Compact(); return m; }
var pyr=Pyr(); double pyrA=AreaMassProperties.Compute(pyr).Area/1e6;
IGH_Component Mk(GH_Document d,string name){ var p=Instances.ComponentServer.ObjectProxies.First(q=>q.Desc.Name==name && !q.Obsolete && typeof(IGH_Component).IsAssignableFrom(q.Type)); var o=(IGH_Component)p.CreateInstance(); o.CreateAttributes(); d.AddObject(o,false); return o; }
List<T> O<T>(IGH_Component c,string n)=>Out(c,n).VolatileData.AllData(true).Select(x=>(T)x.ScriptVariable()).ToList();
double A=HCMV*WCMV, Wy=WCMV*HCMV*HCMV/6, Wz=HCMV*WCMV*WCMV/6;   // cm2, cm3
var results=new Dictionary<string,(List<Line> lines,List<double> util)>();
var LOG=@"C:/Users/gonza/AppData/Local/Temp/claude/C--Users-gonza-Documents-GitHub-pyramid-roof/88d2013e-3524-4014-9052-f727e6ca9a4a/scratchpad/klog.txt"; void Lg(string s){ System.IO.File.AppendAllText(LOG,DateTime.Now.ToString("HH:mm:ss")+" "+s+"\n"); }
foreach(var f in new[]{"friend-16-diagrid","friend-16-diagrid-evenload-opentop"}){ Lg("start "+f);
 var io2=new GH_DocumentIO(); io2.Open(@"C:\Users\gonza\Documents\GitHub\pyramid-roof\polyframe2\"+f+".gh"); var d=io2.Document; d.Enabled=true;
 var perp=d.Objects.OfType<IGH_Component>().First(c=>c.Name=="PFPerp");
 var ex=Mk(d,"Explode PFoam"); ex.Params.Input[0].AddSource(perp.Params.Output[0]); var ie=Mk(d,"Inspect PFEdge"); ie.Params.Input[0].AddSource(ex.Params.Output[1]);
 d.NewSolution(false,GH_SolutionMode.Silent);
 var L=O<Line>(ie,"Line"); var X=O<int>(ie,"External");
 var nodes=new List<Point3d>(); int Id(Point3d p){ for(int i=0;i<nodes.Count;i++) if(nodes[i].DistanceTo(p)<1) return i; nodes.Add(p); return nodes.Count-1; }
 var bars=new List<Line>(); var seen=new HashSet<(int,int)>(); for(int i=0;i<L.Count;i++) if(X[i]==0){ int a=Id(L[i].From), b=Id(L[i].To); if(a==b) continue; var k=(Math.Min(a,b),Math.Max(a,b)); if(seen.Add(k)) bars.Add(new Line(nodes[a],nodes[b])); }
 var feet=new List<Point3d>(); for(int i=0;i<L.Count;i++) if(X[i]==2){ var v=L[i].Direction; v.Unitize(); if(Math.Abs(v.Z)<0.999){ foreach(var p in new[]{L[i].From,L[i].To}) if(nodes.Any(n=>n.DistanceTo(p)<1) && p.Z<500 && !feet.Any(q=>q.DistanceTo(p)<1)) feet.Add(p); } }
 d.Enabled=false; d.Dispose(); Lg("geometry bars "+bars.Count+" feet "+feet.Count);
 SetV(In(l2b,"Line"),bars.Cast<object>().ToArray()); SetV(In(sup,"Pos"),feet.Cast<object>().ToArray());
 In(asm,"Load").RemoveAllSources(); In(asm,"Load").AddSource(Out(grav,"Load")); In(asm,"Load").AddSource(Out(ml,"Load"));
 SetV(In(ml,"Vec"),new Vector3d(0,0,-7)); SetV(In(ml,"Mesh"),pyr);
 foreach(var o in doc.Objects.OfType<IGH_ActiveObject>()) o.ExpireSolution(false);
 Lg("solving"); doc.Enabled=true; var sw=System.Diagnostics.Stopwatch.StartNew(); doc.NewSolution(true,GH_SolutionMode.Silent); var ms=sw.ElapsedMilliseconds; Lg("solved "+ms);
 foreach(var c in doc.Objects.OfType<IGH_Component>()) if(c.RuntimeMessageLevel==GH_RuntimeMessageLevel.Error||(c.RuntimeMessageLevel==GH_RuntimeMessageLevel.Warning)) { var mm=string.Join(" | ",c.RuntimeMessages(GH_RuntimeMessageLevel.Error).Concat(c.RuntimeMessages(GH_RuntimeMessageLevel.Warning))).Replace("\n"," "); sb.AppendLine("  msg "+c.NickName+": "+mm.Substring(0,Math.Min(160,mm.Length))); }
 var mass=O<double>(asm,"Mass").FirstOrDefault(); var res=Out(an,"Resulting").VolatileData.AllData(true).FirstOrDefault(); var dmax=O<double>(an,"Maximum Displacement").FirstOrDefault();
 var Nv=O<double>(bf,"Normal Force"); var My=O<double>(bf,"Bending moment My"); var Mz=O<double>(bf,"Bending moment Mz");
 // per bar: 3 points (ts 0,.5,1)
 int nb=bars.Count, per=Nv.Count/Math.Max(1,nb); var util=new List<double>(); double maxC=0,maxT=0,maxM=0; int iC=0,iT=0; double maxN=0,minN=0;
 for(int b=0;b<nb;b++){ double uc=0,ut=0; for(int k=0;k<per;k++){ int ii=b*per+k; double n=Nv[ii], my=My[ii], mz=Mz[ii]; double s1=n/A, sb_=Math.Abs(my)*100/Wy+Math.Abs(mz)*100/Wz; double smin=s1-sb_, smax=s1+sb_; uc=Math.Max(uc,-smin/2.0); ut=Math.Max(ut,smax/0.29); maxM=Math.Max(maxM,Math.Max(Math.Abs(my),Math.Abs(mz))); maxN=Math.Max(maxN,n); minN=Math.Min(minN,n); }
   util.Add(Math.Max(uc,0)); if(uc>maxC){maxC=uc;iC=b;} if(ut>maxT){maxT=ut;iT=b;} }
 Point3d mid(int b)=>bars[b].PointAt(0.5);
 sb.AppendLine(f+": bars "+nb+" feet "+feet.Count+" solve "+ms+" ms | concrete mass "+(mass/1000).ToString("0.0")+" t | pyramid surface "+pyrA.ToString("0.0")+" m2 -> casing load "+(7*pyrA).ToString("0")+" kN | resulting force "+res);
 sb.AppendLine("  max displacement "+dmax.ToString("0.00")+" cm | N range "+minN.ToString("0.0")+" .. "+maxN.ToString("0.0")+" kN (Karamba: - = compression) | max |M| "+maxM.ToString("0.0")+" kNm");
 sb.AppendLine("  max compression stress / fcd(20 MPa) = "+maxC.ToString("0.00")+" at ("+(mid(iC).X/1000).ToString("0.0")+","+(mid(iC).Y/1000).ToString("0.0")+","+(mid(iC).Z/1000).ToString("0.0")+") | max tension stress / fctm(2.9 MPa) = "+maxT.ToString("0.0")+" at ("+(mid(iT).X/1000).ToString("0.0")+","+(mid(iT).Y/1000).ToString("0.0")+","+(mid(iT).Z/1000).ToString("0.0")+")");
 var buckF=Out(buck,"Buckling-load-factors").VolatileData.AllData(true).Select(x=>x.ToString()).ToList(); sb.AppendLine("  buckling load factors: "+string.Join(", ",buckF));
 var R=O<Vector3d>(rf,"Reaction Forces"); var RP=Out(rf,"Support Position").VolatileData.AllData(true).Select(x=>x.ScriptVariable()).ToList();
 var rs=new List<string>(); for(int i=0;i<R.Count;i++){ Point3d p= RP[i] is Plane pl? pl.Origin : (Point3d)RP[i]; var h=new Vector3d(R[i].X,R[i].Y,0); var o=new Vector3d(p.X,p.Y,0); o.Unitize(); rs.Add("("+(p.X/1000).ToString("0.0")+","+(p.Y/1000).ToString("0.0")+") V "+R[i].Z.ToString("0.0")+" H "+h.Length.ToString("0.0")+(h*o<0?" thrust out":" pull in")); }
 sb.AppendLine("  reactions per foot (V up, H horizontal): "+string.Join(" ; ",rs.Take(5))+(rs.Count>5?" ...":""));
 sb.AppendLine("  sum reactions "+string.Join(" ",Out(rf,"Sum of Reaction Forces").VolatileData.AllData(true)));
 results[f]=(bars,util);
}
// bake bars coloured by compression utilisation (stress / fcd), AP8 at x=0, 16 at x=+14 m
var KLay=__rhino_doc__.Layers.FindName("karamba check"); int li= KLay!=null? KLay.Index : __rhino_doc__.Layers.Add("karamba check",System.Drawing.Color.Gray);
foreach(var o in __rhino_doc__.Objects.FindByLayer(__rhino_doc__.Layers[li])) __rhino_doc__.Objects.Delete(o,true);
System.Drawing.Color Col(double u)=> u<0.4? System.Drawing.Color.FromArgb(60,110,220) : u<0.7? System.Drawing.Color.FromArgb(70,180,90) : u<0.9? System.Drawing.Color.FromArgb(240,200,40) : u<=1.0? System.Drawing.Color.FromArgb(245,130,30) : System.Drawing.Color.FromArgb(220,30,30);
foreach(var kv in results){ double dx= kv.Key.Contains("opentop")? 14000 : 0; var (kbars,util)=kv.Value; for(int i=0;i<kbars.Count;i++){ var l=kbars[i]; l.Transform(Rhino.Geometry.Transform.Translation(dx,0,0)); var u=util[i]; var pipe=Rhino.Geometry.Brep.CreatePipe(l.ToNurbsCurve(), u>0.9? 90: 50, false, Rhino.Geometry.PipeCapMode.Flat, true, 1, 0.1); if(pipe!=null && pipe.Length>0) __rhino_doc__.Objects.AddBrep(pipe[0],new Rhino.DocObjects.ObjectAttributes{LayerIndex=li,ColorSource=Rhino.DocObjects.ObjectColorSource.ColorFromObject,ObjectColor=Col(u)}); }
 var t=new Rhino.Geometry.TextEntity{ Plane=new Rhino.Geometry.Plane(new Rhino.Geometry.Point3d(dx-5000,-7600,0),Rhino.Geometry.Vector3d.XAxis,Rhino.Geometry.Vector3d.YAxis), PlainText=(kv.Key.Contains("opentop")?"16 feet + open top, even load":"16-feet diagrid (original)")+" - compression stress / fcd", TextHeight=500 }; __rhino_doc__.Objects.AddText(t,new Rhino.DocObjects.ObjectAttributes{LayerIndex=li}); }
var lg=new Rhino.Geometry.TextEntity{ Plane=new Rhino.Geometry.Plane(new Rhino.Geometry.Point3d(-5000,-9200,0),Rhino.Geometry.Vector3d.XAxis,Rhino.Geometry.Vector3d.YAxis), PlainText="blue <0.4   green 0.4-0.7   yellow 0.7-0.9   orange 0.9-1.0   red >1.0 (thick)", TextHeight=400 }; __rhino_doc__.Objects.AddText(lg,new Rhino.DocObjects.ObjectAttributes{LayerIndex=li});
__rhino_doc__.Views.Redraw(); Console.WriteLine("baked");

Console.WriteLine(sb.ToString());
