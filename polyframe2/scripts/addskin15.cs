using Grasshopper; using Grasshopper.Kernel; using Grasshopper.Kernel.Types; using Grasshopper.Kernel.Parameters; using Grasshopper.Kernel.Special; using Rhino.Geometry; using System.Drawing;
var io=new GH_DocumentIO(); io.Open(@"C:\Users\gonza\Documents\GitHub\pyramid-roof\polyframe2\friend-12-feet-2m-corners-opentop.gh"); var doc=io.Document;
IGH_Component Add(string name,float x,float y){ var p=Instances.ComponentServer.ObjectProxies.First(q=>q.Desc.Name==name && !q.Obsolete && q.Kind==GH_ObjectType.CompiledObject && typeof(IGH_Component).IsAssignableFrom(q.Type)); var o=(IGH_Component)p.CreateInstance(); o.CreateAttributes(); o.Attributes.Pivot=new PointF(x,y); doc.AddObject(o,false); return o;}
IGH_Param In(IGH_Component c, string n)=> c.Params.Input.First(i=>i.Name==n||i.NickName==n);
IGH_Param Out(IGH_Component c, string n)=> c.Params.Output.First(i=>i.Name==n||i.NickName==n);
void W(IGH_Component a,string o,IGH_Component b,string i){ In(b,i).AddSource(Out(a,o)); }
void Num(IGH_Component c,string n,double v){ var q=In(c,n); var p=(Param_Number)q; p.PersistentData.Clear(); p.PersistentData.Append(new GH_Number(v)); }
GH_NumberSlider Sl(string name,double min,double max,double val,int dec,float x,float y){ var s=new GH_NumberSlider(); s.CreateAttributes(); s.NickName=name; s.Slider.Minimum=(decimal)min; s.Slider.Maximum=(decimal)max; s.Slider.DecimalPlaces=dec; s.Slider.Type= dec==0? Grasshopper.GUI.Base.GH_SliderAccuracy.Integer : Grasshopper.GUI.Base.GH_SliderAccuracy.Float; s.SetSliderValue((decimal)val); s.Attributes.Pivot=new PointF(x,y); doc.AddObject(s,false); return s; }
float X0=60, Y0=900;
var sB=Sl("Skin base side (mm)",10000,20000,13900,0,X0,Y0); var sH=Sl("Skin apex height (mm)",6670,14000,9270,0,X0,Y0+50);
var hs=Add("Division",X0+260,Y0); In(hs,"A").AddSource(sB); { var q=In(hs,"B"); var pd=q.GetType().GetProperty("PersistentData").GetValue(q); pd.GetType().GetMethod("Clear").Invoke(pd,null); pd.GetType().GetMethods().First(m=>m.Name=="Append"&&m.GetParameters().Length==1).Invoke(pd,new object[]{ q is Param_Number? (object)new GH_Number(-2) : new GH_Number(-2)}); }
var org=Add("Construct Point",X0+400,Y0); W(hs,"Result",org,"X coordinate"); W(hs,"Result",org,"Y coordinate"); Num(org,"Z coordinate",0);
var rect=Add("Rectangle",X0+540,Y0); W(org,"Point",rect,"Plane"); In(rect,"X Size").AddSource(sB); In(rect,"Y Size").AddSource(sB);
var bs=Add("Boundary Surfaces",X0+680,Y0); W(rect,"Rectangle",bs,"Edges");
var ap=Add("Construct Point",X0+540,Y0+90); Num(ap,"X coordinate",0); Num(ap,"Y coordinate",0); In(ap,"Z coordinate").AddSource(sH);
var ep=Add("Extrude Point",X0+820,Y0); W(bs,"Surfaces",ep,"Base"); W(ap,"Point",ep,"Point");
var swp=Instances.ComponentServer.ObjectProxies.First(q=>q.Desc.Name=="Colour Swatch" && !q.Obsolete); var sw=(IGH_Param)swp.CreateInstance(); sw.CreateAttributes(); sw.Attributes.Pivot=new PointF(X0+820,Y0+90); doc.AddObject(sw,false); var swProp=sw.GetType().GetProperty("SwatchColour"); if(swProp!=null) swProp.SetValue(sw,Color.FromArgb(90,230,170,90));
var ep2=Add("Extrude Point",X0+820,Y0-90); W(rect,"Rectangle",ep2,"Base"); W(ap,"Point",ep2,"Point");
var cp=Add("Custom Preview",X0+980,Y0); W(ep2,"Extrusion",cp,"Geometry"); In(cp,"Material").AddSource(sw);
// clearance check against the final form nodes
var perp=doc.Objects.OfType<IGH_Component>().First(c=>c.Name=="PFPerp");
var ex=Add("Explode PFoam",X0+260,Y0+200); In(ex,"PFoam").AddSource(Out(perp,"PFoam"));
var iv=Add("Inspect PFVertex",X0+400,Y0+200); W(ex,"PFVertices",iv,"PFVertex");
var gn=Add("Gate Not",X0+560,Y0+260); W(iv,"External",gn,"A");
var cpI=Add("Cull Pattern",X0+700,Y0+200); W(iv,"Point",cpI,"List"); W(gn,"Result",cpI,"Cull Pattern");
var cap=Add("Cap Holes",X0+980,Y0+90); W(ep,"Extrusion",cap,"Brep");
var pib=Add("Point In Brep",X0+1120,Y0+200); var uz=Add("Unit Z",X0+860,Y0+300); Num(uz,"Factor",60); var mv=Add("Move",X0+980,Y0+260); W(cpI,"List",mv,"Geometry"); W(uz,"Unit vector",mv,"Motion");
W(cap,"Brep",pib,"Brep"); In(pib,"Point").AddSource(Out(mv,"Geometry"));
var bcp=Add("Brep Closest Point",X0+1120,Y0+300); W(cpI,"List",bcp,"Point"); W(ep2,"Extrusion",bcp,"Brep");
var mm=Add("Bounds",X0+1300,Y0+300); W(bcp,"Distance",mm,"Numbers");
var mass=Add("Mass Addition",X0+1300,Y0+200); W(pib,"Inside",mass,"Input");
var ll=Add("List Length",X0+1300,Y0+120); W(cpI,"List",ll,"List");
var ar=Add("Area",X0+1120,Y0+400); W(ep2,"Extrusion",ar,"Geometry");
GH_Panel Pan(string name,IGH_Param src,float x,float y){ var pan=new GH_Panel(); pan.CreateAttributes(); pan.NickName=name; pan.Attributes.Pivot=new PointF(x,y); pan.Attributes.Bounds=new RectangleF(x,y,220,40); pan.AddSource(src); doc.AddObject(pan,false); return pan; }
var p1=Pan("Dome nodes inside the skin (must equal total)",Out(mass,"Result"),X0+1460,Y0+200); var p0=Pan("Dome nodes (total)",Out(ll,"Length"),X0+1460,Y0+120);
var p2=Pan("Node-to-skin distance range (mm, to the sloped faces; feet are far from them)",Out(mm,"Domain"),X0+1460,Y0+300); var p3=Pan("Skin area, 4 sloped faces (mm2)",Out(ar,"Area"),X0+1460,Y0+400);
var n=new GH_Panel(); n.CreateAttributes(); n.NickName="Outer pyramid skin - read me"; n.UserText="NON-STRUCTURAL OUTER PYRAMID SKIN around the unchanged compression dome. Default: same 53.1 deg slope as the original 10x10 / 6.67 m pyramid, scaled up until every bar centreline is at least 200 mm inside the skin (perpendicular). Result: base 13.90 x 13.90 m, apex 9.27 m, eaves 1.95 m past the walls, gap dome-to-skin up to ~1.6 m. The skin's base is at the top of the walls (z=0), so it overhangs the walls as eaves. Its weight must reach the dome only as VERTICAL loads at nodes (posts), which keeps the dome compression-only; Karamba already assumed 7 kN/m2 over a 10x10 pyramid surface, so a bigger skin is MORE load - re-check. Slide base/apex to test other sizes; 'Dome nodes inside the skin' must equal 'Dome nodes (total)' (test points are lifted 60 mm so feet sitting on the base plane count as inside)."; n.Attributes.Pivot=new PointF(X0,Y0+130); doc.AddObject(n,false); n.Attributes.Bounds=new RectangleF(X0,Y0+130,440,150); n.Properties.Colour=Color.FromArgb(255,255,220,160);
var gr=new GH_Group(); gr.CreateAttributes(); gr.NickName="5  Outer pyramid skin (not structural) + fit check"; gr.Colour=Color.FromArgb(80,255,210,140); foreach(var o in new IGH_DocumentObject[]{sB,sH,hs,org,rect,bs,ap,ep,ep2,gn,cpI,uz,mv,sw,cp,ex,iv,cap,pib,bcp,mm,mass,ll,ar,p0,p1,p2,p3,n}) gr.AddObject(o.InstanceGuid); doc.AddObject(gr,false); foreach(var o in new IGH_DocumentObject[]{org,rect,bs,ap,ep,ep2,ex,iv,cpI,cap,pib,bcp,mv,uz,ar}) if(o is IGH_PreviewObject po) po.Hidden=true;
var old=Instances.ActiveCanvas.Document; Instances.DocumentServer.AddDocument(doc); Instances.ActiveCanvas.Document=doc; if(old!=null){ old.Enabled=false; Instances.DocumentServer.RemoveDocument(old); old.Dispose(); }
doc.Enabled=true; doc.NewSolution(false);
Console.WriteLine("total "+string.Join(" ",Out(ll,"Length").VolatileData.AllData(true))+" inside "+string.Join(" ",Out(mass,"Result").VolatileData.AllData(true))+" dist "+string.Join(" ",Out(mm,"Domain").VolatileData.AllData(true))+" area "+string.Join(" ",Out(ar,"Area").VolatileData.AllData(true)));
foreach(var o in doc.Objects.OfType<IGH_ActiveObject>()) if(o.RuntimeMessageLevel==GH_RuntimeMessageLevel.Error) Console.WriteLine("ERR "+o.NickName+": "+string.Join("|",o.RuntimeMessages(GH_RuntimeMessageLevel.Error)));
var arch=new GH_IO.Serialization.GH_Archive(); arch.CreateNewRoot(false); arch.AppendObject(doc,"Definition"); Console.WriteLine("write "+arch.WriteToFile(@"C:\Users\gonza\Documents\GitHub\pyramid-roof\polyframe2\friend-15-pyramid-skin.gh",true,false));
