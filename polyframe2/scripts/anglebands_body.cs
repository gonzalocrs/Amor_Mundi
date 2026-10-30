const string SUB="9c007a04-d0d9-48e4-9da3-9ba142bc4d46";
GH_Cluster PrintCast(GH_Document outer,float x,float y){
 var dpc=new GH_Document(); cur=dpc;
 var hA=HIn("Axes",0); var hP=HIn("Pipes",100);
 var ep=Add("End Points",200,0); In(ep,"Curve").AddSource(hA);
 var v2=Add("Vector 2Pt",350,0); W(ep,"Start",v2,"Point A"); W(ep,"End",v2,"Point B");
 var uz=Add("Unit Z",350,100); Num(uz,"Factor",1);
 var an=Add("Angle",500,0); W(v2,"Vector",an,"Vector A"); W(uz,"Unit vector",an,"Vector B");
 var dg=Add("Degrees",650,0); W(an,"Angle",dg,"Radians");
 var s1=AddG(SUB,800,0); W(dg,"Degrees",s1,"A"); Num(s1,"B",90);
 var ab=Add("Absolute",950,0); W(s1,"Result",ab,"Value");
 var s2=AddG(SUB,1100,0); Num(s2,"A",90); W(ab,"Result",s2,"B");   // angle from vertical, 0..90
 var st=Add("Smaller Than",1250,0); W(s2,"Result",st,"First Number"); Num(st,"Second Number",35); var st3=Add("Larger Than",1250,300); W(s2,"Result",st3,"First Number"); Num(st3,"Second Number",80);
 var dp=Add("Dispatch",1400,100); In(dp,"List").AddSource(hP); W(st,"… or Equal to",dp,"Dispatch pattern"); var lean=Add("Dispatch",1400,250); W(s2,"Result",lean,"List"); W(st,"… or Equal to",lean,"Dispatch pattern"); var dq=Add("Dispatch",1550,250); W(dp,"List B",dq,"List"); var sq=Add("Smaller Than",1550,350); W(lean,"List B",sq,"First Number"); Num(sq,"Second Number",60); W(sq,"… or Equal to",dq,"Dispatch pattern"); var cnt80=Add("Cull Pattern",1550,450); W(s2,"Result",cnt80,"List"); W(st3,"Larger than",cnt80,"Cull Pattern"); var n80=Add("List Length",1700,450); W(cnt80,"List",n80,"List"); var ly=Add("List Length",1700,250); W(dq,"List A",ly,"List"); var lr=Add("List Length",1700,350); W(dq,"List B",lr,"List");
 var dl=Add("Dispatch",1400,0); In(dl,"List").AddSource(hA); W(st,"… or Equal to",dl,"Dispatch pattern");
 var la=Add("List Length",1550,-100); W(dl,"List A",la,"List"); var lb=Add("List Length",1550,0); W(dl,"List B",lb,"List");
 var ln=Add("Length",1550,100); W(dl,"List B",ln,"Curve"); var ma=Add("Mass Addition",1700,100); W(ln,"Length",ma,"Input");
 var dv=Add("Division",1850,100); W(ma,"Result",dv,"A"); Num(dv,"B",1000);
 HOut("Green <=35",Out(dp,"List A"),0); HOut("Yellow 35-60",Out(dq,"List A"),100); HOut("Red >60",Out(dq,"List B"),200); HOut("Count <=35",Out(la,"Length"),300); HOut("Count 35-60",Out(ly,"Length"),400); HOut("Count >60",Out(lr,"Length"),500); HOut("Count >80 (horizontal)",Out(n80,"Length"),600);
 cur=outer; return MakeCluster(dpc,outer,"Angle from vertical","Bars by angle from true vertical: green <=35, yellow 35-60, red >60; counts incl. near-horizontal (>80)",x,y);
}
var doc=Instances.ActiveCanvas.Document; cur=doc;
var pipes=doc.Objects.OfType<IGH_Component>().Where(c=>c.Name=="PFPipe").ToList();
// stage B pipe = the one fed by PFPerp
var ppB=pipes.First(p=>p.Params.Input[0].Sources.Any(s=>s.Attributes.GetTopLevel.DocObject.Name=="PFPerp"));
var pc=PrintCast(doc,ppB.Attributes.Pivot.X+200,ppB.Attributes.Pivot.Y+330);
pc.Params.Input[0].AddSource(Out(ppB,"Axes")); pc.Params.Input[1].AddSource(Out(ppB,"Pipe"));
// hide the force-coloured stage B preview, add green/orange previews
foreach(var cp in doc.Objects.OfType<IGH_Component>().Where(c=>c.Name=="Custom Preview" && c.Params.Input[0].Sources.Any(s=>s.Attributes.GetTopLevel.DocObject==ppB))) ((IGH_PreviewObject)cp).Hidden=true;
IGH_Param Swatch(Color c,float x,float y){ var swp=Instances.ComponentServer.ObjectProxies.First(q=>q.Desc.Name=="Colour Swatch" && !q.Obsolete); var s=(IGH_Param)swp.CreateInstance(); s.CreateAttributes(); s.Attributes.Pivot=new PointF(x,y); doc.AddObject(s,false); s.GetType().GetProperty("SwatchColour").SetValue(s,c); return s; }
var g=Swatch(Color.FromArgb(255,40,170,60),pc.Attributes.Pivot.X+260,pc.Attributes.Pivot.Y-60); var o=Swatch(Color.FromArgb(255,240,200,30),pc.Attributes.Pivot.X+260,pc.Attributes.Pivot.Y-10); var rr=Swatch(Color.FromArgb(255,220,50,40),pc.Attributes.Pivot.X+260,pc.Attributes.Pivot.Y+40);
var c1=Add("Custom Preview",pc.Attributes.Pivot.X+420,pc.Attributes.Pivot.Y-40); In(c1,"Geometry").AddSource(pc.Params.Output[0]); In(c1,"Material").AddSource(g);
var c2=Add("Custom Preview",pc.Attributes.Pivot.X+420,pc.Attributes.Pivot.Y+20); In(c2,"Geometry").AddSource(pc.Params.Output[1]); In(c2,"Material").AddSource(o); var c3=Add("Custom Preview",pc.Attributes.Pivot.X+420,pc.Attributes.Pivot.Y+80); In(c3,"Geometry").AddSource(pc.Params.Output[2]); In(c3,"Material").AddSource(rr);
var pan=new GH_Panel(); pan.CreateAttributes(); pan.NickName="Stage B bars: <=35 | 35-60 | >60 | >80 (horizontal)"; pan.Attributes.Pivot=new PointF(pc.Attributes.Pivot.X+260,pc.Attributes.Pivot.Y+70); pan.Attributes.Bounds=new RectangleF(pc.Attributes.Pivot.X+260,pc.Attributes.Pivot.Y+70,260,80); doc.AddObject(pan,false);
pan.AddSource(pc.Params.Output[3]); pan.AddSource(pc.Params.Output[4]); pan.AddSource(pc.Params.Output[5]); pan.AddSource(pc.Params.Output[6]);
var gr=new GH_Group(); gr.CreateAttributes(); gr.NickName="5  Stage B bars by angle from true vertical (green <=35, yellow 35-60, red >60)"; gr.Colour=Color.FromArgb(80,200,255,200); foreach(var ob in new IGH_DocumentObject[]{pc,g,o,rr,c1,c2,c3,pan}) gr.AddObject(ob.InstanceGuid); doc.AddObject(gr,false);
doc.NewSolution(false);
Console.WriteLine("bands "+string.Join(" | ",pc.Params.Output.Skip(3).Select(o=>o.NickName+"="+string.Join(" ",o.VolatileData.AllData(true)))));
