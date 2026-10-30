void NumsG(IGH_Component c,string n,IEnumerable<double> v){ var q=In(c,n); if(q is Param_GenericObject pg){ pg.PersistentData.Clear(); foreach(var x in v) pg.PersistentData.Append(new GH_Number(x)); return;} var p=(Param_Number)q; p.PersistentData.Clear(); foreach(var x in v) p.PersistentData.Append(new GH_Number(x)); }
const string MUL="ce46b74e-00c9-43c4-805a-193b69ea4a11", ADDN="a0d62394-a118-422d-abb3-6af115c75b25", SUB="9c007a04-d0d9-48e4-9da3-9ba142bc4d46", ROTG="b7798b74-037e-4f0c-8ac7-dc1043d093e0";

// ================= Cluster 1: octagon force diagram =================
var d1=new GH_Document(); cur=d1;
var hN=HIn("Density n",0); var hQ=HIn("Octagon proportion",100); var hD=HIn("Cone depth",200); var hS=HIn("Plan side",300); var hR=HIn("Ref apex",400);
var div=Add("Division",150,0); Num(div,"A",1000.0/3.0); In(div,"B").AddSource(hN);
var hex=Add("Hexagonal",300,0); Pl(hex,"Plane",Plane.WorldXY); W(div,"Result",hex,"Size"); Int(hex,"Extent X",41); Int(hex,"Extent Y",41);
var li=Add("List Item",450,0); W(hex,"Points",li,"List"); In(li,"List").DataMapping=GH_DataMapping.Flatten; Int(li,"Index",840);
// octagon = square (half 923.88) with corners cut; vertices at perimeter positions t_k = base_k + sign_k * e, e = 0.25 - 0.176777*Q
var rq=Add("Rectangle",600,-200); W(li,"Item",rq,"Plane"); var dm=new GH_Interval(new Interval(-923.8795,923.8795)); ((Param_Interval)In(rq,"X Size")).PersistentData.Clear(); ((Param_Interval)In(rq,"X Size")).PersistentData.Append(dm); ((Param_Interval)In(rq,"Y Size")).PersistentData.Clear(); ((Param_Interval)In(rq,"Y Size")).PersistentData.Append(dm);
var m1=AddG(MUL,450,-120); In(m1,"A").AddSource(hQ); Num(m1,"B",-0.1767767);
var a1=AddG(ADDN,600,-120); W(m1,"Result",a1,"A"); Num(a1,"B",0.25);
var m2=AddG(MUL,750,-120); W(a1,"Result",m2,"A"); NumsG(m2,"B",new double[]{-1,1,-1,1,-1,1,-1,1}); In(m2,"A").DataMapping=GH_DataMapping.None;
var a2=AddG(ADDN,900,-120); W(m2,"Result",a2,"A"); NumsG(a2,"B",new double[]{1,0,0.25,0.25,0.5,0.5,0.75,0.75});
var evo=Add("Evaluate Length",1050,-160); W(rq,"Rectangle",evo,"Curve"); W(a2,"Result",evo,"Length"); Bool(evo,"Normalized",true);
var oct=Add("PolyLine",1200,-160); W(evo,"Point",oct,"Vertices"); Bool(oct,"Closed",true);
var pic=Add("Point In Curve",1350,-80); W(hex,"Points",pic,"Point"); In(pic,"Point").DataMapping=GH_DataMapping.Flatten; W(oct,"Polyline",pic,"Curve");
var gt=Add("Larger Than",1500,-80); W(pic,"Relationship",gt,"First Number"); Num(gt,"Second Number",1);
var cull=Add("Cull Pattern",1650,-80); W(pic,"Point",cull,"List"); W(gt,"Larger than",cull,"Cull Pattern");
var mrg=AddG("3cadddef-1e2b-4c09-9390-0e8f78f7609f",1800,0); In(mrg,"Data 1").AddSource(Out(evo,"Point")); In(mrg,"Data 2").AddSource(Out(cull,"List"));
var del=Add("Delaunay Mesh",1950,0); W(mrg,"Result",del,"Points"); In(del,"Points").DataMapping=GH_DataMapping.Flatten; Pl(del,"Plane",Plane.WorldXY);
var fb=Add("Face Boundaries",2100,0); W(del,"Mesh",fb,"Mesh");
var bs=Add("Boundary Surfaces",2250,0); W(fb,"Boundaries",bs,"Edges"); In(bs,"Edges").DataMapping=GH_DataMapping.Graft;
var neg=Add("Negative",750,120); In(neg,"Value").AddSource(hD);
var uz=Add("Unit Z",900,120); W(neg,"Result",uz,"Factor");
var mv=Add("Move",1050,120); W(li,"Item",mv,"Geometry"); W(uz,"Unit vector",mv,"Motion");
var ep=Add("Extrude Point",2400,0); W(bs,"Surfaces",ep,"Base"); W(mv,"Geometry",ep,"Point");
var flat=new Param_Brep(); flat.CreateAttributes(); flat.NickName="Cells"; flat.Attributes.Pivot=new PointF(2550,0); flat.AddSource(Out(ep,"Extrusion")); flat.DataMapping=GH_DataMapping.Flatten; d1.AddObject(flat,false);
// the 8 boundary tets (one per octagon edge, starting with the (-,-) diagonal edge) -> centroids
var exo=Add("Explode",1350,240); W(oct,"Polyline",exo,"Curve");
var cmid=Add("Curve Middle",1500,240); W(exo,"Segments",cmid,"Curve");
var mcp=Add("Mesh Closest Point",2100,240); W(cmid,"Midpoint",mcp,"Point"); W(del,"Mesh",mcp,"Mesh");
var lib=Add("List Item",2600,240); lib.Params.Input[0].AddSource(flat); W(mcp,"Index",lib,"Index");
var vol=AddG("7c0523e8-79c9-45a2-8777-cf0d46bc5432",2750,240); W(lib,"Item",vol,"Geometry");
// wall line = plan square from (-s/2,-s/2); Divide Curve 8 -> corner, mid, corner ... (same order as the octagon edges)
var hs=Add("Division",450,400); In(hs,"A").AddSource(hS); Num(hs,"B",-2);
var org=Add("Construct Point",600,400); W(hs,"Result",org,"X coordinate"); W(hs,"Result",org,"Y coordinate"); Num(org,"Z coordinate",0);
var wall=Add("Rectangle",750,400); W(org,"Point",wall,"Plane"); In(wall,"X Size").AddSource(hS); In(wall,"Y Size").AddSource(hS);
var dv=Add("Divide Curve",900,400); W(wall,"Rectangle",dv,"Curve"); Int(dv,"Count",8);
var dup=Add("Duplicate Data",1050,480); W(wall,"Rectangle",dup,"Data"); Int(dup,"Number",8); Bool(dup,"Order",true);
// stage A display offset = -1.4 * side in X
var mo=AddG(MUL,600,560); In(mo,"A").AddSource(hS); Num(mo,"B",-1.4);
var ux=Add("Unit X",750,560); W(mo,"Result",ux,"Factor");
// reference pyramid
var pl=Add("PolyLine",1200,640); W(dv,"Points",pl,"Vertices"); Bool(pl,"Closed",true);
var rbs=Add("Boundary Surfaces",1350,640); W(pl,"Polyline",rbs,"Edges");
var rpt=Add("Construct Point",1350,740); Num(rpt,"X coordinate",0); Num(rpt,"Y coordinate",0); In(rpt,"Z coordinate").AddSource(hR);
var rep=Add("Extrude Point",1500,640); W(rbs,"Surfaces",rep,"Base"); W(rpt,"Point",rep,"Point");
HOut("Force cells",flat,0); HOut("Support targets",Out(vol,"Centroid"),100); HOut("Support points",Out(dv,"Points"),200); HOut("Wall line x8",Out(dup,"Data"),300); HOut("Wall line",Out(wall,"Rectangle"),400); HOut("Stage A offset",Out(ux,"Unit vector"),500); HOut("Reference pyramid",Out(rep,"Extrusion"),600);

// ================= Cluster 2: support vertex IDs =================
var d2=new GH_Document(); cur=d2;
var hF=HIn("Force PFoam",0); var hT=HIn("Support targets",100);
var exf=Add("Explode PFoam",200,0); In(exf,"PFoam").AddSource(hF);
var ipc=Add("Inspect PFCell",400,0); W(exf,"PFCells",ipc,"PFCell");
var cps=Add("Closest Points",600,100); In(cps,"Point").AddSource(hT); W(ipc,"Centroid",cps,"Cloud"); Int(cps,"Count",1);
var lid=Add("List Item",800,0); W(ipc,"ID",lid,"List"); W(cps,"CP Index",lid,"Index"); In(lid,"Index").DataMapping=GH_DataMapping.Flatten;
HOut("Support IDs",Out(lid,"Item"),0);

// ================= Cluster 3 (built twice): colour by force =================
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

// ================= Cluster 4 (built twice): checks =================
GH_Document CheckDoc(){ var d4=new GH_Document(); cur=d4;
 var hP=HIn("Form PFoam",0); var hI=HIn("Support IDs",100); var hW=HIn("Wall line",200);
 var ex4=Add("Explode PFoam",200,0); In(ex4,"PFoam").AddSource(hP);
 var sep=Add("Separate PFEdges By Type",400,0); W(ex4,"PFEdges",sep,"PFEdge");
 var ie4=Add("Inspect PFEdge",600,0); W(sep,"Internal",ie4,"PFEdge");
 var bnF=Add("Bounds",800,-100); W(ie4,"Force",bnF,"Numbers");
 // deviation = angle between each bar and the normal of its dual force face, folded to 0..90
 var enp=Add("End Points",800,0); W(ie4,"Line",enp,"Curve");
 var v2=Add("Vector 2Pt",950,0); W(enp,"Start",v2,"Point A"); W(enp,"End",v2,"Point B");
 var iff=Add("Inspect PFFace",800,100); W(ie4,"Dual",iff,"PFFace");
 var dpl=Add("Deconstruct Plane",950,100); W(iff,"Plane",dpl,"Plane");
 var ang=Add("Angle",1100,50); W(v2,"Vector",ang,"Vector A"); W(dpl,"Z-Axis",ang,"Vector B");
 var deg=Add("Degrees",1250,50); W(ang,"Angle",deg,"Radians");
 var s1=AddG(SUB,1400,50); W(deg,"Degrees",s1,"A"); Num(s1,"B",90);
 var ab=Add("Absolute",1550,50); W(s1,"Result",ab,"Value");
 var s2=AddG(SUB,1700,50); Num(s2,"A",90); W(ab,"Result",s2,"B");
 var bnD=Add("Bounds",1850,0); W(s2,"Result",bnD,"Numbers");
 var avD=Add("Average",1850,100); W(s2,"Result",avD,"Input");
 // feet: distance of the 8 support vertices to the wall line
 var iv4=Add("Inspect PFVertex",400,250); W(ex4,"PFVertices",iv4,"PFVertex");
 var mi=Add("Member Index",600,250); W(iv4,"ID",mi,"Set"); In(mi,"Member").AddSource(hI);
 var lpt=Add("List Item",800,250); W(iv4,"Point",lpt,"List"); W(mi,"Index",lpt,"Index"); In(lpt,"Index").DataMapping=GH_DataMapping.Flatten;
 var ccp=Add("Curve Closest Point",950,250); W(lpt,"Item",ccp,"Point"); In(ccp,"Curve").AddSource(hW);
 var bnW=Add("Bounds",1100,250); W(ccp,"Distance",bnW,"Numbers");
 var avW=Add("Average",1100,350); W(ccp,"Distance",avW,"Input");
 HOut("Bar force range",Out(bnF,"Domain"),0); HOut("Deviation range (deg)",Out(bnD,"Domain"),100); HOut("Mean deviation (deg)",Out(avD,"Arithmetic mean"),200); HOut("Foot-to-wall range (mm)",Out(bnW,"Domain"),300); HOut("Mean foot-to-wall (mm)",Out(avW,"Arithmetic mean"),400);
 return d4; }

// ================= main document =================
var doc=new GH_Document(); cur=doc;
GH_NumberSlider Sl(string name,double min,double max,double val,int dec,float x,float y){ var s=new GH_NumberSlider(); s.CreateAttributes(); s.NickName=name; s.Slider.Minimum=(decimal)min; s.Slider.Maximum=(decimal)max; s.Slider.DecimalPlaces=dec; s.Slider.Type= dec==0? Grasshopper.GUI.Base.GH_SliderAccuracy.Integer : Grasshopper.GUI.Base.GH_SliderAccuracy.Float; s.SetSliderValue((decimal)val); s.Attributes.Pivot=new PointF(x,y); doc.AddObject(s,false); return s; }
var sN=Sl("Density n",0.8,2.5,1.2,2,60,100); var sQ=Sl("Octagon proportion",0.6,1.3,0.8,2,60,150); var sD=Sl("Cone depth (mm)",150,800,280,0,60,200); var sS=Sl("Plan side (mm)",4000,16000,10000,0,60,250); var sR=Sl("Ref apex (mm)",1000,12000,6670,0,60,300);
var sIt=Sl("PFPerp iterations",0,3000,1000,0,1060,420); var sCo=Sl("Pull strength",0,100,10,1,1060,470);
var c1=MakeCluster(d1,doc,"Octagon force diagram","Cone force diagram on an octagon cap: hex lattice inside a square with cut corners, Delaunay, each triangle joined to a point below. Cap faces = vertical loads; the 8 side faces = 8 reactions (diagonal edges -> corner buttresses, straight edges -> mid-side buttresses). Octagon proportion < 1 makes the mid-side reactions smaller.",380,200);
CIn(c1,"Density n").AddSource(sN); CIn(c1,"Octagon proportion").AddSource(sQ); CIn(c1,"Cone depth").AddSource(sD); CIn(c1,"Plan side").AddSource(sS); CIn(c1,"Ref apex").AddSource(sR);
var bld=Add("PFBuild",640,110); In(bld,"Brep").AddSource(COut(c1,"Force cells")); Num(bld,"Absolute Tolerance",0.1); Num(bld,"Planarity Tolerance",0.1); Hide(bld);
var c2=MakeCluster(d2,doc,"Support IDs","Form vertices (= force cells) carrying the 8 reactions, in wall order: corner, mid, corner, ...",840,210);
CIn(c2,"Force PFoam").AddSource(Out(bld,"Force PFoam")); CIn(c2,"Support targets").AddSource(COut(c1,"Support targets"));
var ad=Add("Algebraic Dual",840,90); W(bld,"Force PFoam",ad,"Force PFoam"); Num(ad,"Scale",1); Bool(ad,"Flip",false); Hide(ad);
var vc=Add("Algebraic Vertex Constraints",1080,150); W(ad,"Algebraic Form",vc,"Algebraic Form"); In(vc,"PFVertex IDs").AddSource(COut(c2,"Support IDs")); In(vc,"Constraints").AddSource(COut(c1,"Support points")); Num(vc,"Scale",1); Hide(vc);
// stage A display (moved left)
var ppA=Add("PFPipe",1340,40); W(vc,"PFoam",ppA,"PFoam"); Num(ppA,"MinR",40); Num(ppA,"MaxR",120); Hide(ppA);
var cA=MakeCluster(ColourDoc(),doc,"Colour by force","Blue = low compression, red = high (PFPipe force magnitude)",1540,90); cur=doc; CIn(cA,"Forces").AddSource(Out(ppA,"Force"));
var mvA=Add("Move",1540,10); W(ppA,"Pipe",mvA,"Geometry"); In(mvA,"Motion").AddSource(COut(c1,"Stage A offset")); Hide(mvA);
var cpA=Add("Custom Preview",1740,40); W(mvA,"Geometry",cpA,"Geometry"); In(cpA,"Material").AddSource(COut(cA,"Colours"));
var kA=MakeCluster(CheckDoc(),doc,"Check","Bar force range (+ = compression), deviation of bars from their force faces, distance of the 8 feet to the wall line",1340,200); cur=doc;
CIn(kA,"Form PFoam").AddSource(Out(vc,"PFoam")); CIn(kA,"Support IDs").AddSource(COut(c2,"Support IDs")); CIn(kA,"Wall line").AddSource(COut(c1,"Wall line"));
// stage B
var pvc=Add("PFVertex Constraints",1300,440); W(vc,"PFoam",pvc,"PFoam"); In(pvc,"PFVertex ID").AddSource(COut(c2,"Support IDs")); In(pvc,"Constraint").AddSource(COut(c1,"Wall line x8")); In(pvc,"Coefficient").AddSource(sCo); Bool(pvc,"On",true); Hide(pvc);
var perp=Add("PFPerp",1500,440); W(pvc,"PFoam",perp,"PFoam"); In(perp,"Max Iteration").AddSource(sIt); Num(perp,"Deviation",0.1); Num(perp,"Minimum Edge Length",10); Hide(perp);
var ppB=Add("PFPipe",1700,420); W(perp,"PFoam",ppB,"PFoam"); Num(ppB,"MinR",40); Num(ppB,"MaxR",120); Hide(ppB);
var cB=MakeCluster(ColourDoc(),doc,"Colour by force","Blue = low compression, red = high (PFPipe force magnitude)",1900,470); cur=doc; CIn(cB,"Forces").AddSource(Out(ppB,"Force"));
var cpB=Add("Custom Preview",2100,420); W(ppB,"Pipe",cpB,"Geometry"); In(cpB,"Material").AddSource(COut(cB,"Colours"));
var kB=MakeCluster(CheckDoc(),doc,"Check","Bar force range (+ = compression), deviation of bars from their force faces, distance of the 8 feet to the wall line",1700,580); cur=doc;
CIn(kB,"Form PFoam").AddSource(Out(perp,"PFoam")); CIn(kB,"Support IDs").AddSource(COut(c2,"Support IDs")); CIn(kB,"Wall line").AddSource(COut(c1,"Wall line"));
GH_Panel Pan(string name,GH_Cluster k,float x,float y){ var pan=new GH_Panel(); pan.CreateAttributes(); pan.NickName=name; pan.Attributes.Pivot=new PointF(x,y); pan.Attributes.Bounds=new RectangleF(x,y,300,150); foreach(var o in k.Params.Output) pan.AddSource(o); doc.AddObject(pan,false); return pan; }
var pA=Pan("Stage A: forces | dev range | mean dev | feet-to-wall range | mean",kA,1560,170);
var pB=Pan("Stage B: forces | dev range | mean dev | feet-to-wall range | mean",kB,1920,560);
var swp=Instances.ComponentServer.ObjectProxies.First(q=>q.Desc.Name=="Colour Swatch" && !q.Obsolete);
var swo=(IGH_Param)swp.CreateInstance(); swo.CreateAttributes(); swo.Attributes.Pivot=new PointF(1940,760); doc.AddObject(swo,false);
var swProp=swo.GetType().GetProperty("SwatchColour"); if(swProp!=null) swProp.SetValue(swo,Color.FromArgb(70,150,150,150));
var cpr=Add("Custom Preview",2100,760); In(cpr,"Geometry").AddSource(COut(c1,"Reference pyramid")); In(cpr,"Material").AddSource(swo);
Hide(c1); Hide(c2); Hide(kA); Hide(kB);
GH_Group Grp(string name,Color col,params IGH_DocumentObject[] objs){ var gr=new GH_Group(); gr.CreateAttributes(); gr.NickName=name; gr.Colour=col; foreach(var o in objs) gr.AddObject(o.InstanceGuid); doc.AddObject(gr,false); return gr; }
Grp("1  Sliders - play here",Color.FromArgb(120,255,230,150),sN,sQ,sD,sS,sR);
Grp("2  Force diagram (PolyFrame build)",Color.FromArgb(80,170,200,255),c1,bld,c2);
Grp("3  Stage A - exact algebraic, 8 feet pinned (shown left)",Color.FromArgb(80,170,255,180),ad,vc,ppA,cA,mvA,cpA,kA,pA);
Grp("4  Stage B - pull 8 feet onto wall line, PFPerp",Color.FromArgb(80,255,200,170),sIt,sCo,pvc,perp,ppB,cB,cpB,kB,pB,swo,cpr);
var old=Instances.ActiveCanvas.Document; Instances.DocumentServer.AddDocument(doc); Instances.ActiveCanvas.Document=doc; if(old!=null){ old.Enabled=false; Instances.DocumentServer.RemoveDocument(old); old.Dispose(); }
var swt=System.Diagnostics.Stopwatch.StartNew(); doc.Enabled=true; doc.NewSolution(false); sb.AppendLine("solve ms "+swt.ElapsedMilliseconds);
foreach(var o in doc.Objects.OfType<IGH_ActiveObject>()) if(o.RuntimeMessageLevel!=GH_RuntimeMessageLevel.Blank) sb.AppendLine("msg "+o.NickName+": "+o.RuntimeMessageLevel+" "+string.Join(" | ",o.RuntimeMessages(GH_RuntimeMessageLevel.Error).Concat(o.RuntimeMessages(GH_RuntimeMessageLevel.Warning))));
sb.AppendLine("IDs "+string.Join(" ",COut(c2,"Support IDs").VolatileData.AllData(true)));
foreach(var k in new[]{kA,kB}) sb.AppendLine("check: "+string.Join(" | ",k.Params.Output.Select(o=>string.Join(" ",o.VolatileData.AllData(true)))));
sb.AppendLine("pipes A "+Out(ppA,"Pipe").VolatileData.DataCount+" B "+Out(ppB,"Pipe").VolatileData.DataCount+" objs "+doc.ObjectCount);
Console.WriteLine(sb.ToString());
