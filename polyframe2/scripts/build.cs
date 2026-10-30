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

// ================= Cluster 1: pyramid force diagram =================
var d1=new GH_Document(); cur=d1;
var hN=HIn("Density n",0); var hD=HIn("Cone depth",100); var hS=HIn("Plan side",200); var hR=HIn("Ref apex",300);
var div=Add("Division",150,0); Num(div,"A",1000.0/3.0); In(div,"B").AddSource(hN);       // hex size = R/(3n), R = 1000
var hex=Add("Hexagonal",300,0); Pl(hex,"Plane",Plane.WorldXY); W(div,"Result",hex,"Size"); Int(hex,"Extent X",41); Int(hex,"Extent Y",41);
var li=Add("List Item",450,0); W(hex,"Points",li,"List"); In(li,"List").DataMapping=GH_DataMapping.Flatten; Int(li,"Index",840);   // centre lattice point
var poly=Add("Polygon",600,0); W(li,"Item",poly,"Plane"); Num(poly,"Radius",1000); Int(poly,"Segments",4); Num(poly,"Fillet Radius",0);  // diamond = square at 45 deg
var pic=Add("Point In Curve",750,-80); W(hex,"Points",pic,"Point"); In(pic,"Point").DataMapping=GH_DataMapping.Flatten; W(poly,"Polygon",pic,"Curve");
var gt=Add("Larger Than",900,-80); W(pic,"Relationship",gt,"First Number"); Num(gt,"Second Number",1);
var cull=Add("Cull Pattern",1050,-80); W(pic,"Point",cull,"List"); W(gt,"Larger than",cull,"Cull Pattern");
var disc=Add("Discontinuity",900,40); W(poly,"Polygon",disc,"Curve"); Int(disc,"Level",1);
var mrg=AddG("3cadddef-1e2b-4c09-9390-0e8f78f7609f",1200,0); In(mrg,"Data 1").AddSource(Out(disc,"Points")); In(mrg,"Data 2").AddSource(Out(cull,"List"));
var del=Add("Delaunay Mesh",1350,0); W(mrg,"Result",del,"Points"); In(del,"Points").DataMapping=GH_DataMapping.Flatten; Pl(del,"Plane",Plane.WorldXY);
var fb=Add("Face Boundaries",1500,0); W(del,"Mesh",fb,"Mesh");
var bs=Add("Boundary Surfaces",1650,0); W(fb,"Boundaries",bs,"Edges"); In(bs,"Edges").DataMapping=GH_DataMapping.Graft;
var neg=Add("Negative",750,120); In(neg,"Value").AddSource(hD);
var uz=Add("Unit Z",900,120); W(neg,"Result",uz,"Factor");
var mv=Add("Move",1050,120); W(li,"Item",mv,"Geometry"); W(uz,"Unit vector",mv,"Motion");
var ep=Add("Extrude Point",1800,0); W(bs,"Surfaces",ep,"Base"); W(mv,"Geometry",ep,"Point");
var flat=new Param_Brep(); flat.CreateAttributes(); flat.NickName="Cells"; flat.Attributes.Pivot=new PointF(1950,0); flat.AddSource(Out(ep,"Extrusion")); flat.DataMapping=GH_DataMapping.Flatten; d1.AddObject(flat,false);
// boundary tets -> their centroids (targets used to find the 4 support cells)
var el=Add("Evaluate Length",900,240); W(poly,"Polygon",el,"Curve"); Nums(el,"Length",new[]{0.125,0.375,0.625,0.875}); Bool(el,"Normalized",true);
var mcp=Add("Mesh Closest Point",1500,240); W(el,"Point",mcp,"Point"); W(del,"Mesh",mcp,"Mesh");
var lib=Add("List Item",2050,240); lib.Params.Input[0].AddSource(flat); W(mcp,"Index",lib,"Index");
var vol=AddG("7c0523e8-79c9-45a2-8777-cf0d46bc5432",2200,240); W(lib,"Item",vol,"Geometry");
// supports: edge midpoints of a 4-gon of radius = side -> (+-side/2, +-side/2), same order as the diamond edges
var sp=Add("Polygon",600,380); Pl(sp,"Plane",Plane.WorldXY); In(sp,"Radius").AddSource(hS); Int(sp,"Segments",4); Num(sp,"Fillet Radius",0);
var sel=Add("Evaluate Length",900,380); W(sp,"Polygon",sel,"Curve"); Nums(sel,"Length",new[]{0.125,0.375,0.625,0.875}); Bool(sel,"Normalized",true);
// reference pyramid
var pl=Add("PolyLine",1200,500); W(sel,"Point",pl,"Vertices"); Bool(pl,"Closed",true);
var rbs=Add("Boundary Surfaces",1500,500); W(pl,"Polyline",rbs,"Edges");
var rpt=Add("Construct Point",1500,600); Num(rpt,"X coordinate",0); Num(rpt,"Y coordinate",0); In(rpt,"Z coordinate").AddSource(hR);
var rep=Add("Extrude Point",1800,500); W(rbs,"Surfaces",rep,"Base"); W(rpt,"Point",rep,"Point");
HOut("Force cells",flat,0); HOut("Support targets",Out(vol,"Centroid"),100); HOut("Support points",Out(sel,"Point"),200); HOut("Reference pyramid",Out(rep,"Extrusion"),300);

// ================= Cluster 2: support vertex IDs =================
var d2=new GH_Document(); cur=d2;
var hF=HIn("Force PFoam",0); var hT=HIn("Support targets",100);
var exf=Add("Explode PFoam",200,0); In(exf,"PFoam").AddSource(hF);
var ipc=Add("Inspect PFCell",400,0); W(exf,"PFCells",ipc,"PFCell");
var cps=Add("Closest Points",600,100); In(cps,"Point").AddSource(hT); W(ipc,"Centroid",cps,"Cloud"); Int(cps,"Count",1);
var lid=Add("List Item",800,0); W(ipc,"ID",lid,"List"); W(cps,"CP Index",lid,"Index"); In(lid,"Index").DataMapping=GH_DataMapping.Flatten;
HOut("Support IDs",Out(lid,"Item"),0);

// ================= Cluster 3: colour by force =================
var d3=new GH_Document(); cur=d3;
var hV=HIn("Forces",0);
var bnd=Add("Bounds",200,0); In(bnd,"Numbers").AddSource(hV);
var rmp=Add("Remap Numbers",400,0); In(rmp,"Value").AddSource(hV); W(bnd,"Domain",rmp,"Source");
var gproxy=Instances.ComponentServer.ObjectProxies.First(q=>q.Desc.Name=="Gradient" && !q.Obsolete && typeof(GH_GradientControl).IsAssignableFrom(q.Type));
var grad=(GH_GradientControl)gproxy.CreateInstance(); grad.CreateAttributes(); grad.Attributes.Pivot=new PointF(600,0); d3.AddObject(grad,false);
var g=new Grasshopper.GUI.Gradient.GH_Gradient(); g.AddGrip(0.0,Color.FromArgb(40,90,220)); g.AddGrip(0.5,Color.FromArgb(150,90,200)); g.AddGrip(1.0,Color.FromArgb(220,40,40)); grad.Gradient=g;
grad.Params.Input[2].AddSource(Out(rmp,"Mapped"));
((Param_Number)grad.Params.Input[0]).PersistentData.Clear(); ((Param_Number)grad.Params.Input[0]).PersistentData.Append(new GH_Number(0)); ((Param_Number)grad.Params.Input[1]).PersistentData.Clear(); ((Param_Number)grad.Params.Input[1]).PersistentData.Append(new GH_Number(1));
HOut("Colours",grad.Params.Output[0],0);

// ================= Cluster 4: bar force check =================
var d4=new GH_Document(); cur=d4;
var hP=HIn("Form PFoam",0);
var ex4=Add("Explode PFoam",200,0); In(ex4,"PFoam").AddSource(hP);
var sep=Add("Separate PFEdges By Type",400,0); W(ex4,"PFEdges",sep,"PFEdge");
var ie4=Add("Inspect PFEdge",600,0); W(sep,"Internal",ie4,"PFEdge");
var bn4=Add("Bounds",800,0); W(ie4,"Force",bn4,"Numbers");
HOut("Bar force range",Out(bn4,"Domain"),0);

// ================= main document =================
var doc=new GH_Document(); cur=doc;
GH_NumberSlider Sl(string name,double min,double max,double val,int dec,float x,float y){ var s=new GH_NumberSlider(); s.CreateAttributes(); s.NickName=name; s.Slider.Minimum=(decimal)min; s.Slider.Maximum=(decimal)max; s.Slider.DecimalPlaces=dec; s.Slider.Type= dec==0? Grasshopper.GUI.Base.GH_SliderAccuracy.Integer : Grasshopper.GUI.Base.GH_SliderAccuracy.Float; s.SetSliderValue((decimal)val); s.Attributes.Pivot=new PointF(x,y); doc.AddObject(s,false); return s; }
var sN=Sl("Density n",0.8,3.0,1.2,2,60,100); var sD=Sl("Cone depth (mm)",200,1000,375,0,60,150); var sS=Sl("Plan side (mm)",4000,16000,10000,0,60,200); var sR=Sl("Ref apex (mm)",1000,12000,6670,0,60,250);
var c1=MakeCluster(d1,doc,"Pyramid force diagram","Square cone force diagram: hex lattice inside a 45-deg square, Delaunay, each triangle joined to a point below. Cap faces = vertical loads, the 4 side faces = the 4 support reactions.",380,175);
CIn(c1,"Density n").AddSource(sN); CIn(c1,"Cone depth").AddSource(sD); CIn(c1,"Plan side").AddSource(sS); CIn(c1,"Ref apex").AddSource(sR);
var bld=Add("PFBuild",620,120); In(bld,"Brep").AddSource(COut(c1,"Force cells")); Num(bld,"Absolute Tolerance",0.1); Num(bld,"Planarity Tolerance",0.1); Hide(bld);
var c2=MakeCluster(d2,doc,"Support IDs","Finds the form vertices (= force cells) that carry the 4 reactions",820,200);
CIn(c2,"Force PFoam").AddSource(Out(bld,"Force PFoam")); CIn(c2,"Support targets").AddSource(COut(c1,"Support targets"));
var ad=Add("Algebraic Dual",820,90); W(bld,"Force PFoam",ad,"Force PFoam"); Num(ad,"Scale",1); Bool(ad,"Flip",false); Hide(ad);
var vc=Add("Algebraic Vertex Constraints",1060,140); W(ad,"Algebraic Form",vc,"Algebraic Form"); In(vc,"PFVertex IDs").AddSource(COut(c2,"Support IDs")); In(vc,"Constraints").AddSource(COut(c1,"Support points")); Num(vc,"Scale",1); Hide(vc);
var pp=Add("PFPipe",1300,120); W(vc,"PFoam",pp,"PFoam"); Num(pp,"MinR",40); Num(pp,"MaxR",120); Hide(pp);
var c3=MakeCluster(d3,doc,"Colour by force","Blue = low compression, red = high (PFPipe force magnitude)",1500,170); CIn(c3,"Forces").AddSource(Out(pp,"Force"));
var cpv=Add("Custom Preview",1740,170); W(pp,"Pipe",cpv,"Geometry"); In(cpv,"Material").AddSource(COut(c3,"Colours"));
var c4=MakeCluster(d4,doc,"Bar force check","Signed force range of all bars (+ = compression, a negative minimum = tension somewhere)",1300,300); CIn(c4,"Form PFoam").AddSource(Out(vc,"PFoam"));
var pan=new GH_Panel(); pan.CreateAttributes(); pan.NickName="Bar force range"; pan.Attributes.Pivot=new PointF(1470,330); pan.Attributes.Bounds=new RectangleF(1470,330,250,56); pan.AddSource(COut(c4,"Bar force range")); doc.AddObject(pan,false);
var swp=Instances.ComponentServer.ObjectProxies.First(q=>q.Desc.Name=="Colour Swatch" && !q.Obsolete);
var swo=(IGH_Param)swp.CreateInstance(); swo.CreateAttributes(); swo.Attributes.Pivot=new PointF(1560,420); doc.AddObject(swo,false);
var swProp=swo.GetType().GetProperty("SwatchColour"); if(swProp!=null) swProp.SetValue(swo,Color.FromArgb(70,150,150,150)); else sb.AppendLine("swatch props: "+string.Join(",",swo.GetType().GetProperties().Select(p=>p.Name)));
var cpr=Add("Custom Preview",1740,420); In(cpr,"Geometry").AddSource(COut(c1,"Reference pyramid")); In(cpr,"Material").AddSource(swo);
Hide(c1); Hide(c2); Hide(c4);
// groups
GH_Group Grp(string name,Color col,params IGH_DocumentObject[] objs){ var gr=new GH_Group(); gr.CreateAttributes(); gr.NickName=name; gr.Colour=col; foreach(var o in objs) gr.AddObject(o.InstanceGuid); doc.AddObject(gr,false); return gr; }
Grp("1  Sliders - play here",Color.FromArgb(120,255,230,150),sN,sD,sS,sR);
Grp("2  Force diagram (PolyFrame build)",Color.FromArgb(80,170,200,255),c1,bld,c2);
Grp("3  Exact algebraic form, 4 corners pinned",Color.FromArgb(80,170,255,180),ad,vc);
Grp("4  Display + check",Color.FromArgb(80,220,220,220),pp,c3,cpv,c4,pan,swo,cpr);
// attach to canvas
var old=Instances.ActiveCanvas.Document; Instances.DocumentServer.AddDocument(doc); Instances.ActiveCanvas.Document=doc; if(old!=null){ old.Enabled=false; Instances.DocumentServer.RemoveDocument(old); old.Dispose(); }
var swt=System.Diagnostics.Stopwatch.StartNew(); doc.Enabled=true; doc.NewSolution(false); sb.AppendLine("solve ms "+swt.ElapsedMilliseconds);
foreach(var o in doc.Objects.OfType<IGH_ActiveObject>()) if(o.RuntimeMessageLevel!=GH_RuntimeMessageLevel.Blank) sb.AppendLine("msg "+o.NickName+": "+o.RuntimeMessageLevel+" "+string.Join(" | ",o.RuntimeMessages(GH_RuntimeMessageLevel.Error).Concat(o.RuntimeMessages(GH_RuntimeMessageLevel.Warning))));
sb.AppendLine("c1 in: "+string.Join(",",c1.Params.Input.Select(p=>p.NickName))+" out: "+string.Join(",",c1.Params.Output.Select(p=>p.NickName+"="+p.VolatileData.DataCount)));
sb.AppendLine("c2 out: "+string.Join(",",c2.Params.Output.Select(p=>p.NickName+"="+string.Join(" ",p.VolatileData.AllData(true)))));
sb.AppendLine("pipes "+Out(pp,"Pipe").VolatileData.DataCount+" colours "+COut(c3,"Colours").VolatileData.DataCount+" range "+string.Join(" ",COut(c4,"Bar force range").VolatileData.AllData(true)));
sb.AppendLine("visible objs "+doc.ObjectCount);
Console.WriteLine(sb.ToString());
