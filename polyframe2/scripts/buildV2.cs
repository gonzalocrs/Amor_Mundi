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

// explicit D8-symmetric cap triangulation, octagon edge k (k=0 faces (-,-)), m angular divisions per sector (even), R rings
// returns tets (cap triangle + apex) and the 8 reaction-cell centroids
(List<Brep> tets, List<Point3d> targets, List<Polyline> tris) GenTets(int R,int m,double depth,double Fexp,double Q=1){
 double b=1000*Math.Cos(Math.PI/8), a=Q*b*(1+Math.Tan(Math.PI/8));
 var V=new[]{new Point3d(-b,-a+b,0),new Point3d(-a+b,-b,0),new Point3d(a-b,-b,0),new Point3d(b,-a+b,0),new Point3d(b,a-b,0),new Point3d(a-b,b,0),new Point3d(-a+b,b,0),new Point3d(-b,a-b,0)};
 var C=Point3d.Origin; var apex=new Point3d(0,0,-depth);
 var tris=new List<Polyline>(); var targets=new List<Point3d>();
 double F(int r)=>Math.Pow((double)r/(R+1),Fexp);
 for(int k=0;k<8;k++){ var A=V[k]; var B=V[(k+1)%8];
  Point3d P(int r,int j){ if(r==0) return C; var e=A+(B-A)*((double)j/m); return C+(e-C)*F(r); }
  // centre fan
  for(int j=0;j<m;j++) tris.Add(new Polyline(new[]{C,P(1,j),P(1,j+1),C}));
  // strips, diagonals mirrored about the sector axis
  for(int r=1;r<R;r++) for(int j=0;j<m;j++){
    if(j<m/2){ tris.Add(new Polyline(new[]{P(r,j),P(r+1,j),P(r+1,j+1),P(r,j)})); tris.Add(new Polyline(new[]{P(r,j),P(r+1,j+1),P(r,j+1),P(r,j)})); }
    else     { tris.Add(new Polyline(new[]{P(r,j),P(r+1,j),P(r,j+1),P(r,j)})); tris.Add(new Polyline(new[]{P(r,j+1),P(r+1,j),P(r+1,j+1),P(r,j+1)})); } }
  // outer band: fans to the two octagon vertices + the reaction triangle in the middle
  for(int j=0;j<m;j++){ var cv=(j<m/2)?A:B; tris.Add(new Polyline(new[]{P(R,j),cv,P(R,j+1),P(R,j)})); }
  var mid=P(R,m/2); tris.Add(new Polyline(new[]{mid,A,B,mid}));
  targets.Add((mid+A+B+apex)/4.0);
 }
 var tets=new List<Brep>();
 foreach(var t in tris){ var s=Brep.CreateFromCornerPoints(t[0],t[1],t[2],0.001); var ext=Surface.CreateExtrusionToPoint(new PolylineCurve(t),apex);
   var pts=new[]{t[0],t[1],t[2],apex}; var faces=new List<Brep>{ Brep.CreateFromCornerPoints(pts[0],pts[1],pts[2],0.001), Brep.CreateFromCornerPoints(pts[0],pts[1],pts[3],0.001), Brep.CreateFromCornerPoints(pts[1],pts[2],pts[3],0.001), Brep.CreateFromCornerPoints(pts[2],pts[0],pts[3],0.001)};
   var j=Brep.JoinBreps(faces,0.001); tets.Add(j[0]); }
 return (tets,targets,tris);
}

const string MUL="ce46b74e-00c9-43c4-805a-193b69ea4a11", SUB="9c007a04-d0d9-48e4-9da3-9ba142bc4d46";
// ================= Cluster 1: force diagram presets (GUESS, internalized like PF example 3(7)) =================
var d1=new GH_Document(); cur=d1;
var hP=HIn("Preset",0); var hZ=HIn("Force depth",100);
var presets=new[]{(3,2),(4,2),(5,2),(6,2),(5,4)};
var pb=new Param_Brep(); pb.CreateAttributes(); pb.NickName="Cells (presets)"; pb.Attributes.Pivot=new PointF(200,0); d1.AddObject(pb,false);
var pt=new Param_Point(); pt.CreateAttributes(); pt.NickName="Reaction cell centroids"; pt.Attributes.Pivot=new PointF(200,100); d1.AddObject(pt,false);
for(int i=0;i<presets.Length;i++){ var gg=GenTets(presets[i].Item1,presets[i].Item2,1000,1,0.85); var path=new Grasshopper.Kernel.Data.GH_Path(i); foreach(var t in gg.tets) pb.PersistentData.Append(new GH_Brep(t),path); foreach(var q in gg.targets) pt.PersistentData.Append(new GH_Point(q),path); }
var tb1=Add("Tree Branch",400,0); In(tb1,"Tree").AddSource(pb); In(tb1,"Path").AddSource(hP);
var tb2=Add("Tree Branch",400,100); In(tb2,"Tree").AddSource(pt); In(tb2,"Path").AddSource(hP);
var sn1=Add("Scale NU",600,0); W(tb1,"Branch",sn1,"Geometry"); Pl(sn1,"Plane",Plane.WorldXY); Num(sn1,"Scale X",1); Num(sn1,"Scale Y",1); In(sn1,"Scale Z").AddSource(hZ);
var sn2=Add("Scale NU",600,100); W(tb2,"Branch",sn2,"Geometry"); Pl(sn2,"Plane",Plane.WorldXY); Num(sn2,"Scale X",1); Num(sn2,"Scale Y",1); In(sn2,"Scale Z").AddSource(hZ);
HOut("Force cells",Out(sn1,"Geometry"),0); HOut("Support targets",Out(sn2,"Geometry"),100);

// ================= Cluster 1b: plan, wall, reference =================
var d1b=new GH_Document(); cur=d1b;
var hS=HIn("Plan side",0); var hR=HIn("Ref apex",100);
var hs=Add("Division",200,0); In(hs,"A").AddSource(hS); Num(hs,"B",-2);
var org=Add("Construct Point",350,0); W(hs,"Result",org,"X coordinate"); W(hs,"Result",org,"Y coordinate"); Num(org,"Z coordinate",0);
var wall=Add("Rectangle",500,0); W(org,"Point",wall,"Plane"); In(wall,"X Size").AddSource(hS); In(wall,"Y Size").AddSource(hS);
var dv=Add("Divide Curve",650,0); W(wall,"Rectangle",dv,"Curve"); Int(dv,"Count",8);
var cpc=Add("Cull Pattern",800,60); W(dv,"Points",cpc,"List"); var pq=(Param_Boolean)In(cpc,"Cull Pattern"); pq.PersistentData.Clear(); pq.PersistentData.Append(new GH_Boolean(true)); pq.PersistentData.Append(new GH_Boolean(false));
var dup=Add("Duplicate Data",800,140); W(wall,"Rectangle",dup,"Data"); Int(dup,"Number",8); Bool(dup,"Order",true);
var mo=AddG(MUL,350,220); In(mo,"A").AddSource(hS); Num(mo,"B",-1.4); var ux=Add("Unit X",500,220); W(mo,"Result",ux,"Factor");
var pl=Add("PolyLine",650,300); W(cpc,"List",pl,"Vertices"); Bool(pl,"Closed",true);
var rbs=Add("Boundary Surfaces",800,300); W(pl,"Polyline",rbs,"Edges");
var rpt=Add("Construct Point",800,400); Num(rpt,"X coordinate",0); Num(rpt,"Y coordinate",0); In(rpt,"Z coordinate").AddSource(hR);
var rep=Add("Extrude Point",950,300); W(rbs,"Surfaces",rep,"Base"); W(rpt,"Point",rep,"Point");
HOut("Corner points",Out(cpc,"List"),0); HOut("Wall line x8",Out(dup,"Data"),100); HOut("Wall line",Out(wall,"Rectangle"),200); HOut("Stage A offset",Out(ux,"Unit vector"),300); HOut("Reference pyramid",Out(rep,"Extrusion"),400);
// ================= Cluster 2: support vertex IDs =================
var d2=new GH_Document(); cur=d2;
var hF=HIn("Force PFoam",0); var hT=HIn("Support targets",100);
var exf=Add("Explode PFoam",200,0); In(exf,"PFoam").AddSource(hF);
var ipc=Add("Inspect PFCell",400,0); W(exf,"PFCells",ipc,"PFCell");
var cps=Add("Closest Points",600,100); In(cps,"Point").AddSource(hT); W(ipc,"Centroid",cps,"Cloud"); Int(cps,"Count",1);
var lid=Add("List Item",800,0); W(ipc,"ID",lid,"List"); W(cps,"CP Index",lid,"Index"); In(lid,"Index").DataMapping=GH_DataMapping.Flatten;
HOut("Support IDs",Out(lid,"Item"),0);

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
var vl=new GH_ValueList(); vl.CreateAttributes(); vl.NickName="Branching preset (GUESS)"; vl.ListItems.Clear(); foreach(var kv in new[]{("3 rings","0"),("4 rings","1"),("5 rings","2"),("6 rings","3"),("5 rings, 2x spokes (stage A has tension)","4")}) vl.ListItems.Add(new GH_ValueListItem(kv.Item1,kv.Item2)); vl.SelectItem(2); vl.Attributes.Pivot=new PointF(60,100); doc.AddObject(vl,false);
var sD=Sl("Force depth (Scale Z)",0.15,1.5,0.41,3,60,200); var sS=Sl("Plan side (mm)",4000,16000,10000,0,60,250); var sR=Sl("Ref apex (mm)",1000,12000,6670,0,60,300);
var sIt=Sl("PFPerp iterations",0,3000,1000,0,1060,420); var sCo=Sl("Pull strength",0,100,10,1,1060,470);
var c1=MakeCluster(d1,doc,"Force diagram presets (GUESS)","GUESSED force diagrams (not the friend's): octagon cap (proportion 0.85), explicit 8-fold symmetric triangulation from rings x spokes toward the 8 feet, joined to one point below; internalized like PF example 3(7). Scale Z = cone depth.",380,140);
CIn(c1,"Preset").AddSource(vl); CIn(c1,"Force depth").AddSource(sD);
var c1b=MakeCluster(d1b,doc,"Plan + wall + reference","Wall points/line of the square plan, 4 corner points, grey 53.1 deg reference pyramid",380,300);
CIn(c1b,"Plan side").AddSource(sS); CIn(c1b,"Ref apex").AddSource(sR);
var bld=Add("PFBuild",640,110); In(bld,"Brep").AddSource(COut(c1,"Force cells")); Num(bld,"Absolute Tolerance",0.1); Num(bld,"Planarity Tolerance",0.1); Hide(bld);
var c2=MakeCluster(d2,doc,"Support IDs","Form vertices (= force cells) carrying the 8 reactions, in wall order: corner, mid, corner, ...",840,210);
CIn(c2,"Force PFoam").AddSource(Out(bld,"Force PFoam")); CIn(c2,"Support targets").AddSource(COut(c1,"Support targets"));
var ad=Add("Algebraic Dual",840,90); W(bld,"Force PFoam",ad,"Force PFoam"); Num(ad,"Scale",1); Bool(ad,"Flip",false); Hide(ad);
var vc=Add("Algebraic Vertex Constraints",1080,150); W(ad,"Algebraic Form",vc,"Algebraic Form"); var cid=Add("Cull Pattern",960,240); In(cid,"List").AddSource(COut(c2,"Support IDs")); In(cid,"List").DataMapping=GH_DataMapping.Flatten; var pq2=(Param_Boolean)In(cid,"Cull Pattern"); pq2.PersistentData.Clear(); pq2.PersistentData.Append(new GH_Boolean(true)); pq2.PersistentData.Append(new GH_Boolean(false));
W(cid,"List",vc,"PFVertex IDs"); In(vc,"Constraints").AddSource(COut(c1b,"Corner points")); Num(vc,"Scale",1); Hide(vc);
// stage A display (moved left)
var ppA=Add("PFPipe",1340,40); W(vc,"PFoam",ppA,"PFoam"); Num(ppA,"MinR",40); Num(ppA,"MaxR",120); Hide(ppA);
var cA=MakeCluster(ColourDoc(),doc,"Colour by force","Blue = low compression, red = high (PFPipe force magnitude)",1540,90); cur=doc; CIn(cA,"Forces").AddSource(Out(ppA,"Force"));
var mvA=Add("Move",1540,10); W(ppA,"Pipe",mvA,"Geometry"); In(mvA,"Motion").AddSource(COut(c1b,"Stage A offset")); Hide(mvA);
var cpA=Add("Custom Preview",1740,40); W(mvA,"Geometry",cpA,"Geometry"); In(cpA,"Material").AddSource(COut(cA,"Colours"));
var kA=MakeCluster(CheckDoc(),doc,"Check","Bar force range (+ = compression), deviation of bars from their force faces, distance of the 8 feet to the wall line",1340,200); cur=doc;
CIn(kA,"Form PFoam").AddSource(Out(vc,"PFoam")); CIn(kA,"Support IDs").AddSource(COut(c2,"Support IDs")); CIn(kA,"Wall line").AddSource(COut(c1b,"Wall line"));
// stage B
var pvc=Add("PFVertex Constraints",1300,440); W(vc,"PFoam",pvc,"PFoam"); In(pvc,"PFVertex ID").AddSource(COut(c2,"Support IDs")); In(pvc,"Constraint").AddSource(COut(c1b,"Wall line x8")); In(pvc,"Coefficient").AddSource(sCo); Bool(pvc,"On",true); Hide(pvc);
var perp=Add("PFPerp",1500,440); W(pvc,"PFoam",perp,"PFoam"); In(perp,"Max Iteration").AddSource(sIt); Num(perp,"Deviation",0.1); Num(perp,"Minimum Edge Length",10); Hide(perp);
var ppB=Add("PFPipe",1700,420); W(perp,"PFoam",ppB,"PFoam"); Num(ppB,"MinR",40); Num(ppB,"MaxR",120); Hide(ppB);
var cB=MakeCluster(ColourDoc(),doc,"Colour by force","Blue = low compression, red = high (PFPipe force magnitude)",1900,470); cur=doc; CIn(cB,"Forces").AddSource(Out(ppB,"Force"));
var cpB=Add("Custom Preview",2100,420); W(ppB,"Pipe",cpB,"Geometry"); In(cpB,"Material").AddSource(COut(cB,"Colours"));
var kB=MakeCluster(CheckDoc(),doc,"Check","Bar force range (+ = compression), deviation of bars from their force faces, distance of the 8 feet to the wall line",1700,580); cur=doc;
CIn(kB,"Form PFoam").AddSource(Out(perp,"PFoam")); CIn(kB,"Support IDs").AddSource(COut(c2,"Support IDs")); CIn(kB,"Wall line").AddSource(COut(c1b,"Wall line"));
GH_Panel Pan(string name,GH_Cluster k,float x,float y){ var pan=new GH_Panel(); pan.CreateAttributes(); pan.NickName=name; pan.Attributes.Pivot=new PointF(x,y); pan.Attributes.Bounds=new RectangleF(x,y,300,150); foreach(var o in k.Params.Output) pan.AddSource(o); doc.AddObject(pan,false); return pan; }
var pA=Pan("Stage A: forces | dev range | mean dev | feet-to-wall range | mean",kA,1560,170);
var pB=Pan("Stage B: forces | dev range | mean dev | feet-to-wall range | mean",kB,1920,560);
var swp=Instances.ComponentServer.ObjectProxies.First(q=>q.Desc.Name=="Colour Swatch" && !q.Obsolete);
var swo=(IGH_Param)swp.CreateInstance(); swo.CreateAttributes(); swo.Attributes.Pivot=new PointF(1940,760); doc.AddObject(swo,false);
var swProp=swo.GetType().GetProperty("SwatchColour"); if(swProp!=null) swProp.SetValue(swo,Color.FromArgb(70,150,150,150));
var cpr=Add("Custom Preview",2100,760); In(cpr,"Geometry").AddSource(COut(c1b,"Reference pyramid")); In(cpr,"Material").AddSource(swo);
Hide(c1); Hide(c1b); Hide(c2); Hide(kA); Hide(kB);
GH_Group Grp(string name,Color col,params IGH_DocumentObject[] objs){ var gr=new GH_Group(); gr.CreateAttributes(); gr.NickName=name; gr.Colour=col; foreach(var o in objs) gr.AddObject(o.InstanceGuid); doc.AddObject(gr,false); return gr; }
Grp("1  Play here",Color.FromArgb(120,255,230,150),vl,sD,sS,sR);
Grp("2  Force diagram - GUESS, 8-fold symmetric (PolyFrame build)",Color.FromArgb(80,170,200,255),c1,c1b,bld,c2);
Grp("3  Stage A - exact algebraic, 4 corners pinned (shown left)",Color.FromArgb(80,170,255,180),ad,cid,vc,ppA,cA,mvA,cpA,kA,pA);
Grp("4  Stage B - pull 8 feet onto wall line, PFPerp",Color.FromArgb(80,255,200,170),sIt,sCo,pvc,perp,ppB,cB,cpB,kB,pB,swo,cpr);
var old=Instances.ActiveCanvas.Document; Instances.DocumentServer.AddDocument(doc); Instances.ActiveCanvas.Document=doc; if(old!=null){ old.Enabled=false; Instances.DocumentServer.RemoveDocument(old); old.Dispose(); }
var swt=System.Diagnostics.Stopwatch.StartNew(); doc.Enabled=true; doc.NewSolution(false); sb.AppendLine("solve ms "+swt.ElapsedMilliseconds);
foreach(var o in doc.Objects.OfType<IGH_ActiveObject>()) if(o.RuntimeMessageLevel!=GH_RuntimeMessageLevel.Blank) sb.AppendLine("msg "+o.NickName+": "+o.RuntimeMessageLevel+" "+string.Join(" | ",o.RuntimeMessages(GH_RuntimeMessageLevel.Error).Concat(o.RuntimeMessages(GH_RuntimeMessageLevel.Warning))));
sb.AppendLine("IDs "+string.Join(" ",COut(c2,"Support IDs").VolatileData.AllData(true)));
foreach(var k in new[]{kA,kB}) sb.AppendLine("check: "+string.Join(" | ",k.Params.Output.Select(o=>string.Join(" ",o.VolatileData.AllData(true)))));
sb.AppendLine("pipes A "+Out(ppA,"Pipe").VolatileData.DataCount+" B "+Out(ppB,"Pipe").VolatileData.DataCount+" objs "+doc.ObjectCount);
Console.WriteLine(sb.ToString());
