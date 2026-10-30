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
 var st=Add("Smaller Than",1250,0); W(s2,"Result",st,"First Number"); Num(st,"Second Number",35);
 var dp=Add("Dispatch",1400,100); In(dp,"List").AddSource(hP); W(st,"… or Equal to",dp,"Dispatch pattern");
 var dl=Add("Dispatch",1400,0); In(dl,"List").AddSource(hA); W(st,"… or Equal to",dl,"Dispatch pattern");
 var la=Add("List Length",1550,-100); W(dl,"List A",la,"List"); var lb=Add("List Length",1550,0); W(dl,"List B",lb,"List");
 var ln=Add("Length",1550,100); W(dl,"List B",ln,"Curve"); var ma=Add("Mass Addition",1700,100); W(ln,"Length",ma,"Input");
 var dv=Add("Division",1850,100); W(ma,"Result",dv,"A"); Num(dv,"B",1000);
 HOut("Printed pipes (<=35 from vertical)",Out(dp,"List A"),0); HOut("Cast pipes (>35)",Out(dp,"List B"),100); HOut("Printed count",Out(la,"Length"),200); HOut("Cast count",Out(lb,"Length"),300); HOut("Cast length (m)",Out(dv,"Result"),400);
 cur=outer; return MakeCluster(dpc,outer,"Print / cast split","Bars within 35 deg of true vertical = printed (green); over 35 deg = cast (orange): ring bars and flat crown bars",x,y);
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
var g=Swatch(Color.FromArgb(255,40,170,60),pc.Attributes.Pivot.X+260,pc.Attributes.Pivot.Y-30); var o=Swatch(Color.FromArgb(255,240,140,30),pc.Attributes.Pivot.X+260,pc.Attributes.Pivot.Y+20);
var c1=Add("Custom Preview",pc.Attributes.Pivot.X+420,pc.Attributes.Pivot.Y-40); In(c1,"Geometry").AddSource(pc.Params.Output[0]); In(c1,"Material").AddSource(g);
var c2=Add("Custom Preview",pc.Attributes.Pivot.X+420,pc.Attributes.Pivot.Y+20); In(c2,"Geometry").AddSource(pc.Params.Output[1]); In(c2,"Material").AddSource(o);
var pan=new GH_Panel(); pan.CreateAttributes(); pan.NickName="Stage B: printed count | cast count | cast length (m)"; pan.Attributes.Pivot=new PointF(pc.Attributes.Pivot.X+260,pc.Attributes.Pivot.Y+70); pan.Attributes.Bounds=new RectangleF(pc.Attributes.Pivot.X+260,pc.Attributes.Pivot.Y+70,260,80); doc.AddObject(pan,false);
pan.AddSource(pc.Params.Output[2]); pan.AddSource(pc.Params.Output[3]); pan.AddSource(pc.Params.Output[4]);
var gr=new GH_Group(); gr.CreateAttributes(); gr.NickName="5  Print (green, <=35 deg from vertical) / cast (orange) - stage B"; gr.Colour=Color.FromArgb(80,200,255,200); foreach(var ob in new IGH_DocumentObject[]{pc,g,o,c1,c2,pan}) gr.AddObject(ob.InstanceGuid); doc.AddObject(gr,false);
doc.NewSolution(false);
Console.WriteLine("printed "+string.Join(" ",pc.Params.Output[2].VolatileData.AllData(true))+" cast "+string.Join(" ",pc.Params.Output[3].VolatileData.AllData(true))+" cast length m "+string.Join(" ",pc.Params.Output[4].VolatileData.AllData(true)));
