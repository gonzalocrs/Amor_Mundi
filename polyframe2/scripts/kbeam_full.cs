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
In(th2,"Model").AddSource(Out(asm,"Model")); In(buck,"Model").AddSource(Out(th2,"Analysed")); SetV(In(buck,"Number of Modes"),3);
// hand check: 5 m simply supported 15x25 cm beam, self-weight only (gamma 24): w=0.9 kN/m, M=2.81 kNm, delta=1.14 mm, R=2.25 kN, mass 459 kg
SetV(In(l2b,"Line"),new Line(new Point3d(0,0,0),new Point3d(2500,0,0)),new Line(new Point3d(2500,0,0),new Point3d(5000,0,0)));
SetV(In(sup,"Pos"),new Point3d(0,0,0),new Point3d(5000,0,0));
In(asm,"Load").RemoveAllSources(); In(asm,"Load").AddSource(Out(grav,"Load"));
doc.Enabled=true; doc.NewSolution(false,GH_SolutionMode.Silent);
foreach(var c in doc.Objects.OfType<IGH_Component>()) if(c.RuntimeMessageLevel!=GH_RuntimeMessageLevel.Blank) sb.AppendLine("msg "+c.NickName+": "+string.Join(" | ",c.RuntimeMessages(GH_RuntimeMessageLevel.Error).Concat(c.RuntimeMessages(GH_RuntimeMessageLevel.Warning))).Replace("\n"," ").Substring(0,Math.Min(200,string.Join(" | ",c.RuntimeMessages(GH_RuntimeMessageLevel.Error).Concat(c.RuntimeMessages(GH_RuntimeMessageLevel.Warning))).Length)));
sb.AppendLine("Assemble outputs: "+string.Join(" | ",asm.Params.Output.Skip(1).Select(o=>o.Name+"="+string.Join(",",o.VolatileData.AllData(true).Take(3)))));
sb.AppendLine("Analyse outputs: "+string.Join(" | ",an.Params.Output.Skip(1).Select(o=>o.Name+"="+string.Join(",",o.VolatileData.AllData(true).Take(3)))));
sb.AppendLine("My: "+string.Join(" ",Out(bf,"Bending moment My").VolatileData.AllData(true).Take(8))+" | Vz "+string.Join(" ",Out(bf,"Shear force Vz").VolatileData.AllData(true).Take(8)));
sb.AppendLine("Reactions: "+string.Join(" ",Out(rf,"Reaction Forces").VolatileData.AllData(true))+" | moments "+string.Join(" ",Out(rf,"Reaction Moments").VolatileData.AllData(true)));
sb.AppendLine("support settings (cloned): "+sup.Message);
sb.AppendLine(srcInfo);
Console.WriteLine(sb.ToString());
