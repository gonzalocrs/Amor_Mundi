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

GH_Document ColourDoc(){ var d3=new GH_Document(); cur=d3;
 var hV=HIn("Forces",0);
 var bnd=Add("Bounds",200,0); In(bnd,"Numbers").AddSource(hV);
 var rmp=Add("Remap Numbers",400,0); In(rmp,"Value").AddSource(hV); W(bnd,"Domain",rmp,"Source");
 var gproxy=Instances.ComponentServer.ObjectProxies.First(q=>q.Desc.Name=="Gradient" && !q.Obsolete && typeof(GH_GradientControl).IsAssignableFrom(q.Type));
 var grad=(GH_GradientControl)gproxy.CreateInstance(); grad.CreateAttributes(); grad.Attributes.Pivot=new PointF(600,0); d3.AddObject(grad,false);
 var g=new Grasshopper.GUI.Gradient.GH_Gradient(); g.AddGrip(0.0,Color.FromArgb(40,90,220)); g.AddGrip(0.5,Color.FromArgb(150,90,200)); g.AddGrip(1.0,Color.FromArgb(220,40,40)); grad.Gradient=g;
 grad.Params.Input[2].AddSource(Out(rmp,"Mapped"));
 ((Param_Number)grad.Params.Input[0]).PersistentData.Clear(); ((Param_Number)grad.Params.Input[0]).PersistentData.Append(new GH_Number(0)); ((Param_Number)grad.Params.Input[1]).PersistentData.Clear(); ((Param_Number)grad.Params.Input[1]).PersistentData.Append(new GH_Number(1));
 HOut("Colours",grad.Params.Output[0],0); return d3; }

// operate on the example 3(7) document currently on the private canvas
var doc=Instances.ActiveCanvas.Document; cur=doc;
IGH_DocumentObject ByName(string n)=>doc.Objects.First(o=>o.Name==n);
// 1) remove my temporary test components and the example's C# point mover
foreach(var o in doc.Objects.Where(o=>(o is IGH_Component c && (c.NickName=="TX"||c.NickName=="TE"||c.NickName=="TV"||c.Name=="Separate PFEdges By Type"||c.Name=="C# Script"||c.Name=="Display Vertex ID"))).ToList()) doc.RemoveObject(o,false);
foreach(var o in doc.Objects.OfType<Param_Point>().Where(p=>p.Recipients.Count==0).ToList()) doc.RemoveObject(o,false);
foreach(var o in doc.Objects.OfType<GH_NumberSlider>().Where(s=>s.Recipients.Count==0).ToList()) doc.RemoveObject(o,false);
foreach(var o in doc.Objects.OfType<GH_Group>().ToList()) doc.RemoveObject(o,false);
foreach(var o in doc.Objects.OfType<GH_Panel>().Where(p=>p.UserText.StartsWith("Various")).ToList()) doc.RemoveObject(o,false);
var bld=(IGH_Component)ByName("PFBuild"); var ad=(IGH_Component)ByName("Algebraic Dual"); var vc=(IGH_Component)ByName("Algebraic Vertex Constraints"); var ec=(IGH_Component)ByName("Algebraic Edge Constraints"); var snu=(IGH_Component)ByName("Scale NU"); var brep=doc.Objects.First(o=>o.Name=="Brep");
var idPanel=doc.Objects.OfType<GH_Panel>().First(p=>p.Recipients.Any(r=>r.Attributes.GetTopLevel.DocObject==vc));
idPanel.NickName="Support vertex IDs (from the example)";
var sZ=doc.Objects.OfType<GH_NumberSlider>().First(s=>s.Recipients.Any(r=>r.Attributes.GetTopLevel.DocObject==snu)); sZ.NickName="Force depth (Scale Z)"; sZ.Slider.Minimum=0.3m; sZ.Slider.Maximum=2m; sZ.Slider.DecimalPlaces=3; sZ.SetSliderValue(0.66m);
foreach(var s in doc.Objects.OfType<GH_NumberSlider>().Where(s=>s.Recipients.Any(r=>r.Attributes.GetTopLevel.DocObject==ad))) s.NickName="Dual scale";
foreach(var s in doc.Objects.OfType<GH_NumberSlider>().Where(s=>s.Recipients.Any(r=>r.Attributes.GetTopLevel.DocObject==vc))) s.NickName="Constraint scale";
// 2) supports: 4 corners of the plan, same order as the example (-,+),(-,-),(+,-),(+,+)
var vpts=vc.Params.Input[2]; vpts.RemoveAllSources(); ((Param_Geometry)vpts).PersistentData.Clear();
var sS=new GH_NumberSlider(); sS.CreateAttributes(); sS.NickName="Plan side (mm)"; sS.Slider.Minimum=4000; sS.Slider.Maximum=16000; sS.Slider.DecimalPlaces=0; sS.Slider.Type=Grasshopper.GUI.Base.GH_SliderAccuracy.Integer; sS.SetSliderValue(10000); doc.AddObject(sS,false);
var sR=new GH_NumberSlider(); sR.CreateAttributes(); sR.NickName="Ref apex (mm)"; sR.Slider.Minimum=1000; sR.Slider.Maximum=12000; sR.Slider.DecimalPlaces=0; sR.Slider.Type=Grasshopper.GUI.Base.GH_SliderAccuracy.Integer; sR.SetSliderValue(6670); doc.AddObject(sR,false);
var dS=new GH_Document(); cur=dS;
var hS=HIn("Plan side",0); var hR=HIn("Ref apex",100);
var sp=Add("Polygon",200,0); Pl(sp,"Plane",Plane.WorldXY); In(sp,"Radius").AddSource(hS); Int(sp,"Segments",4); Num(sp,"Fillet Radius",0);
var sel=Add("Evaluate Length",400,0); W(sp,"Polygon",sel,"Curve"); Nums(sel,"Length",new[]{0.375,0.625,0.875,0.125}); Bool(sel,"Normalized",true);
var pl=Add("PolyLine",600,100); W(sel,"Point",pl,"Vertices"); Bool(pl,"Closed",true);
var rbs=Add("Boundary Surfaces",800,100); W(pl,"Polyline",rbs,"Edges");
var rpt=Add("Construct Point",800,200); Num(rpt,"X coordinate",0); Num(rpt,"Y coordinate",0); In(rpt,"Z coordinate").AddSource(hR);
var rep=Add("Extrude Point",1000,100); W(rbs,"Surfaces",rep,"Base"); W(rpt,"Point",rep,"Point");
HOut("Corner supports",Out(sel,"Point"),0); HOut("Reference pyramid",Out(rep,"Extrusion"),100);
cur=doc;
var cS=MakeCluster(dS,doc,"Plan + reference","4 corner points of the square plan (order (-,+),(-,-),(+,-),(+,+) = example's vertex IDs) and the grey 53.1 deg reference pyramid",0,0);
CIn(cS,"Plan side").AddSource(sS); CIn(cS,"Ref apex").AddSource(sR); vpts.AddSource(COut(cS,"Corner supports"));
// 3) edge constraint (2 short edges on the free-edge arches that would flip to tension)
var eIds=new GH_Panel(); eIds.CreateAttributes(); eIds.NickName="Arch edge IDs"; eIds.UserText="113\n126"; eIds.Properties.Multiline=false; doc.AddObject(eIds,false);
var sL=new GH_NumberSlider(); sL.CreateAttributes(); sL.NickName="Arch edge length (mm)"; sL.Slider.Minimum=50; sL.Slider.Maximum=1500; sL.Slider.DecimalPlaces=0; sL.Slider.Type=Grasshopper.GUI.Base.GH_SliderAccuracy.Integer; sL.SetSliderValue(300); doc.AddObject(sL,false);
var dupL=Add("Duplicate Data",0,0); In(dupL,"Data").AddSource(sL); Int(dupL,"Number",2); Bool(dupL,"Order",true);
ec.Params.Input[1].RemoveAllSources(); ec.Params.Input[1].AddSource(eIds); ec.Params.Input[2].RemoveAllSources(); ec.Params.Input[2].AddSource(Out(dupL,"Data"));
// 4) display + check
var pp=Add("PFPipe",0,0); W(ec,"PFoam",pp,"PFoam"); Num(pp,"MinR",40); Num(pp,"MaxR",120); Hide(pp);
var cA=MakeCluster(ColourDoc(),doc,"Colour by force","Blue = low compression, red = high (PFPipe force magnitude)",0,0); cur=doc; CIn(cA,"Forces").AddSource(Out(pp,"Force"));
var cpv=Add("Custom Preview",0,0); W(pp,"Pipe",cpv,"Geometry"); In(cpv,"Material").AddSource(COut(cA,"Colours"));
var kd=new GH_Document(); cur=kd; var hP=HIn("Form PFoam",0);
var ex4=Add("Explode PFoam",200,0); In(ex4,"PFoam").AddSource(hP); var sep=Add("Separate PFEdges By Type",400,0); W(ex4,"PFEdges",sep,"PFEdge"); var ie4=Add("Inspect PFEdge",600,0); W(sep,"Internal",ie4,"PFEdge"); var bn4=Add("Bounds",800,0); W(ie4,"Force",bn4,"Numbers");
HOut("Bar force range",Out(bn4,"Domain"),0); cur=doc;
var kk=MakeCluster(kd,doc,"Bar force check","Signed force range of all bars (+ = compression; a negative minimum = tension somewhere)",0,0); CIn(kk,"Form PFoam").AddSource(Out(ec,"PFoam")); Hide(kk);
var pan=new GH_Panel(); pan.CreateAttributes(); pan.NickName="Bar force range"; doc.AddObject(pan,false); pan.AddSource(COut(kk,"Bar force range"));
var swp=Instances.ComponentServer.ObjectProxies.First(q=>q.Desc.Name=="Colour Swatch" && !q.Obsolete);
var swo=(IGH_Param)swp.CreateInstance(); swo.CreateAttributes(); doc.AddObject(swo,false); var swProp=swo.GetType().GetProperty("SwatchColour"); if(swProp!=null) swProp.SetValue(swo,Color.FromArgb(70,150,150,150));
var cpr=Add("Custom Preview",0,0); In(cpr,"Geometry").AddSource(COut(cS,"Reference pyramid")); In(cpr,"Material").AddSource(swo);
foreach(var o in new IGH_DocumentObject[]{bld,ad,vc,ec,snu,cS}) Hide(o);
if(brep is IGH_PreviewObject bp) bp.Hidden=true;
var note=new GH_Panel(); note.CreateAttributes(); note.NickName="Notes"; note.UserText="PolyFrame example 3(7) 'single-layer shell', adapted: same force diagram, supports moved to the 4 corners of the 10x10 plan, force depth (Scale Z) tuned for apex ~6.67 m. Two short bars on the free-edge arches (IDs 113, 126) flip to tension when the shell gets taller; Algebraic Edge Constraints keeps them at a positive length (exact algebraic, 0 deg). Edge IDs are only valid for this force diagram."; doc.AddObject(note,false);
// 5) layout (left to right)
void At(IGH_DocumentObject o,float x,float y){ o.Attributes.Pivot=new PointF(x,y); o.Attributes.ExpireLayout(); }
At(brep,60,60); At(sZ,60,120); At(snu,330,90); At(bld,520,90); At(ad,720,90); At(doc.Objects.OfType<GH_NumberSlider>().First(s=>s.NickName=="Dual scale"),520,200);
At(sS,60,300); At(sR,60,350); At(cS,330,320); At(idPanel,720,260); idPanel.Attributes.Bounds=new RectangleF(720,260,140,90);
At(vc,980,180); At(doc.Objects.OfType<GH_NumberSlider>().First(s=>s.NickName=="Constraint scale"),720,380);
At(eIds,980,360); eIds.Attributes.Bounds=new RectangleF(980,360,120,50); At(sL,960,430); At(dupL,1180,430); At(ec,1240,250);
At(pp,1480,150); At(cA,1680,200); At(cpv,1880,150); At(kk,1480,330); At(pan,1680,330); pan.Attributes.Bounds=new RectangleF(1680,330,220,40);
At(swo,1700,420); At(cpr,1880,420); At(note,60,480); note.Attributes.Bounds=new RectangleF(60,480,700,70);
foreach(var o in doc.Objects) o.Attributes.ExpireLayout();
GH_Group Grp(string name,Color col,params IGH_DocumentObject[] objs){ var gr=new GH_Group(); gr.CreateAttributes(); gr.NickName=name; gr.Colour=col; foreach(var o in objs) gr.AddObject(o.InstanceGuid); doc.AddObject(gr,false); return gr; }
Grp("1  Force diagram = PF example 3(7)  (play: Force depth)",Color.FromArgb(80,170,200,255),brep,sZ,snu,bld,ad,doc.Objects.OfType<GH_NumberSlider>().First(s=>s.NickName=="Dual scale"));
Grp("2  Supports: 4 plan corners (play: Plan side)",Color.FromArgb(120,255,230,150),sS,sR,cS,idPanel,vc,doc.Objects.OfType<GH_NumberSlider>().First(s=>s.NickName=="Constraint scale"));
Grp("3  Keep the 2 arch edges in compression",Color.FromArgb(80,170,255,180),eIds,sL,dupL,ec);
Grp("4  Display + check",Color.FromArgb(80,220,220,220),pp,cA,cpv,kk,pan,swo,cpr);
var swt=System.Diagnostics.Stopwatch.StartNew(); doc.NewSolution(false); sb.AppendLine("solve ms "+swt.ElapsedMilliseconds);
foreach(var o in doc.Objects.OfType<IGH_ActiveObject>()) if(o.RuntimeMessageLevel!=GH_RuntimeMessageLevel.Blank) sb.AppendLine("msg "+o.Name+": "+o.RuntimeMessageLevel+" "+string.Join(" | ",o.RuntimeMessages(GH_RuntimeMessageLevel.Error).Concat(o.RuntimeMessages(GH_RuntimeMessageLevel.Warning))));
sb.AppendLine("force range "+string.Join(" ",pan.VolatileData.AllData(true))+" pipes "+Out(pp,"Pipe").VolatileData.DataCount+" objs "+doc.ObjectCount);
var ax=Out(pp,"Axes").VolatileData.AllData(true).Select(x=>((GH_Line)x).Value).ToList(); var bb=BoundingBox.Empty; foreach(var l in ax){bb.Union(l.From);bb.Union(l.To);} sb.AppendLine("bbox "+bb.Min+" .. "+bb.Max);
Console.WriteLine(sb.ToString());
