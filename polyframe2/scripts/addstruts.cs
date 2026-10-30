using Grasshopper; using Grasshopper.Kernel; using Grasshopper.Kernel.Types; using Grasshopper.Kernel.Parameters; using Grasshopper.Kernel.Special; using Rhino.Geometry; using System.Drawing;
var io=new GH_DocumentIO(); io.Open(@"C:\Users\gonza\Documents\GitHub\pyramid-roof\polyframe2\friend-15-pyramid-branches-cut-eaves.gh"); var doc=io.Document;
IGH_Component Add(string name,float x,float y,string outName=null){ var p=Instances.ComponentServer.ObjectProxies.First(q=>q.Desc.Name==name && !q.Obsolete && q.Kind==GH_ObjectType.CompiledObject && typeof(IGH_Component).IsAssignableFrom(q.Type) && !q.Desc.Category.StartsWith("Karamba") && (outName==null || ((IGH_Component)q.CreateInstance()).Params.Output.Any(o=>o.Name==outName))); var o=(IGH_Component)p.CreateInstance(); o.CreateAttributes(); o.Attributes.Pivot=new PointF(x,y); doc.AddObject(o,false); return o;}
IGH_Param In(IGH_Component c, string n)=> c.Params.Input.First(i=>i.Name==n||i.NickName==n);
IGH_Param Out(IGH_Component c, string n)=> c.Params.Output.First(i=>i.Name==n||i.NickName==n);
void W(IGH_Component a,string o,IGH_Component b,string i){ In(b,i).AddSource(Out(a,o)); }
void Set(IGH_Param q,IGH_Goo v){ var pd=q.GetType().GetProperty("PersistentData").GetValue(q); pd.GetType().GetMethod("Clear").Invoke(pd,null); pd.GetType().GetMethods().First(m=>m.Name=="Append"&&m.GetParameters().Length==1).Invoke(pd,new object[]{v}); }
IGH_DocumentObject Top(IGH_Param p)=>p.Attributes.GetTopLevel.DocObject;
void Rewire(IGH_Param from,IGH_Param to){ foreach(var c in doc.Objects.OfType<IGH_Component>().ToList()) foreach(var i in c.Params.Input) if(i.Sources.Contains(from)){ i.RemoveSource(from); i.AddSource(to); } }
var comps=doc.Objects.OfType<IGH_Component>().ToList();
var ep2=comps.First(c=>c.Name=="Extrude Point" && c.Params.Input[0].Sources.Any(s=>Top(s) is IGH_Component rc && rc.Name=="Rectangle"));
var rect=(IGH_Component)Top(ep2.Params.Input[0].Sources[0]);
var sB=doc.Objects.OfType<GH_NumberSlider>().First(s=>s.NickName=="Skin base side (mm)"); var sH=doc.Objects.OfType<GH_NumberSlider>().First(s=>s.NickName=="Skin apex height (mm)");
var sR=doc.Objects.OfType<GH_NumberSlider>().First(s=>s.NickName=="Branch display radius (mm)");
var sl=comps.First(c=>c.Name=="Sort List"); var shF=comps.First(c=>c.Name=="Shift List" && Top(In(c,"List").Sources[0])==sl && In(c,"List").Sources[0].Name.StartsWith("Values"));
var el=comps.First(c=>c.Name=="Evaluate Length");
float X0=60, Y0=2900;
// eave edge raised to height h so struts from the feet can slope up to it
var sE=new GH_NumberSlider(); sE.CreateAttributes(); sE.NickName="Eave edge height above wall top (mm)"; sE.Slider.Minimum=300; sE.Slider.Maximum=2500; sE.Slider.DecimalPlaces=0; sE.Slider.Type=Grasshopper.GUI.Base.GH_SliderAccuracy.Integer; sE.SetSliderValue(1500); sE.Attributes.Pivot=new PointF(X0,Y0); doc.AddObject(sE,false);
var r=Add("Division",X0+260,Y0); In(r,"A").AddSource(sE); In(r,"B").AddSource(sH);
var om=Add("Subtraction",X0+400,Y0); Set(In(om,"A"),new GH_Number(1)); W(r,"Result",om,"B");
var side=Add("Multiplication",X0+540,Y0); In(side,"A").AddSource(sB); W(om,"Result",side,"B");
var hf=Add("Division",X0+680,Y0); W(side,"Result",hf,"A"); Set(In(hf,"B"),new GH_Number(-2));
var org=Add("Construct Point",X0+820,Y0); W(hf,"Result",org,"X coordinate"); W(hf,"Result",org,"Y coordinate"); In(org,"Z coordinate").AddSource(sE);
var er=Add("Rectangle",X0+960,Y0); W(org,"Point",er,"Plane"); W(side,"Result",er,"X Size"); W(side,"Result",er,"Y Size");
// everything that used the base rectangle at wall-top level (eave points, hips, rims, skin surface) now uses the raised eave edge; the full pyramid used for projection is unchanged
foreach(var c in doc.Objects.OfType<IGH_Component>().ToList()) if(c!=ep2 && c.Name!="Boundary Surfaces") foreach(var i in c.Params.Input) if(i.Sources.Contains(Out(rect,"Rectangle"))){ i.RemoveSource(Out(rect,"Rectangle")); i.AddSource(Out(er,"Rectangle")); }
// struts: from each dome foot (on the wall top) up and out to the two eave points beside it; at the corners both struts meet the corner
var dc=Add("Deconstruct",X0+260,Y0+120,"Z component"); W(sl,"Values A",dc,"Point");
var ft=Add("Construct Point",X0+400,Y0+120); W(dc,"X component",ft,"X coordinate"); W(dc,"Y component",ft,"Y coordinate"); Set(In(ft,"Z coordinate"),new GH_Number(0));
var dc2=Add("Deconstruct",X0+260,Y0+220,"Z component"); W(shF,"List",dc2,"Point");
var ft2=Add("Construct Point",X0+400,Y0+220); W(dc2,"X component",ft2,"X coordinate"); W(dc2,"Y component",ft2,"Y coordinate"); Set(In(ft2,"Z coordinate"),new GH_Number(0));
var s1=Add("Line",X0+540,Y0+120); W(ft,"Point",s1,"Start Point"); W(el,"Point",s1,"End Point");
var s2=Add("Line",X0+540,Y0+220); W(ft2,"Point",s2,"Start Point"); W(el,"Point",s2,"End Point");
var mg=Add("Merge",X0+680,Y0+160); W(s1,"Line",mg,"Data 1"); W(s2,"Line",mg,"Data 2");
var pi=Add("Pipe",X0+820,Y0+160); W(mg,"Result",pi,"Curve"); In(pi,"Radius").AddSource(sR);
var swp=Instances.ComponentServer.ObjectProxies.First(q=>q.Desc.Name=="Colour Swatch" && !q.Obsolete); var sw=(IGH_Param)swp.CreateInstance(); sw.CreateAttributes(); sw.Attributes.Pivot=new PointF(X0+820,Y0+260); doc.AddObject(sw,false); sw.GetType().GetProperty("SwatchColour")?.SetValue(sw,Color.FromArgb(255,90,170,190));
var cp=Add("Custom Preview",X0+960,Y0+160); W(pi,"Pipe",cp,"Geometry"); In(cp,"Material").AddSource(sw);
// strut angles from vertical and lengths
var ln=Add("Length",X0+960,Y0+260); W(mg,"Result",ln,"Curve"); var bl=Add("Bounds",X0+1100,Y0+260); W(ln,"Length",bl,"Numbers");
foreach(var o in new IGH_DocumentObject[]{r,om,side,hf,org,er,dc,ft,dc2,ft2,s1,s2,mg,pi,ln,bl}) if(o is IGH_PreviewObject po) po.Hidden=true;
var pz=new GH_Panel(); pz.CreateAttributes(); pz.NickName="Strut length range (mm)"; pz.Attributes.Pivot=new PointF(X0+1240,Y0+260); pz.Attributes.Bounds=new RectangleF(X0+1240,Y0+260,180,30); pz.AddSource(Out(bl,"Domain")); doc.AddObject(pz,false);
var pe=new GH_Panel(); pe.CreateAttributes(); pe.NickName="Eave overhang past the wall line (mm)"; pe.Attributes.Pivot=new PointF(X0+1240,Y0); pe.Attributes.Bounds=new RectangleF(X0+1240,Y0,180,30); doc.AddObject(pe,false);
var ov=Add("Subtraction",X0+1100,Y0); W(hf,"Result",ov,"A"); Set(In(ov,"B"),new GH_Number(-5000)); var neg=Add("Multiplication",X0+1170,Y0+60); W(ov,"Result",neg,"A"); Set(In(neg,"B"),new GH_Number(-1)); pe.AddSource(Out(neg,"Result"));
var n=new GH_Panel(); n.CreateAttributes(); n.NickName="Sloped struts - read me"; n.UserText="Eaves and corners are back, now carried by SLOPED STRUTS from the dome feet. Each foot sends two struts up and out to the eave points beside it (halfway along the eave to the next foot); between the two feet next to a corner that point is the corner, so each corner sits on a V of struts. The eave edge is raised (slider, default 1.5 m above the wall top) so the struts can slope: with the edge at wall-top level they would be flat and could only work in bending. Higher eave edge = steeper struts but a shorter overhang. The struts land on the feet, i.e. directly on the supports, so their outward push goes into the wall/footing, not into the dome."; n.Attributes.Pivot=new PointF(X0,Y0+340); doc.AddObject(n,false); n.Attributes.Bounds=new RectangleF(X0,Y0+340,460,130); n.Properties.Colour=Color.FromArgb(255,255,220,160);
var gr=new GH_Group(); gr.CreateAttributes(); gr.NickName="9  Sloped struts from the feet to the corners and eave (raised eave edge)"; gr.Colour=Color.FromArgb(80,150,210,230); foreach(var o in new IGH_DocumentObject[]{sE,r,om,side,hf,org,er,dc,ft,dc2,ft2,s1,s2,mg,pi,sw,cp,ln,bl,pz,pe,ov,neg,n}) gr.AddObject(o.InstanceGuid); doc.AddObject(gr,false);
doc.Enabled=true; doc.NewSolution(false);
foreach(var o in doc.Objects.OfType<IGH_ActiveObject>()) if(o.RuntimeMessageLevel==GH_RuntimeMessageLevel.Error) Console.WriteLine("ERR "+o.NickName+": "+string.Join("|",o.RuntimeMessages(GH_RuntimeMessageLevel.Error)));
var L=Out(mg,"Result").VolatileData.AllData(true).Select(x=>((GH_Line)x).Value).ToList();
Console.WriteLine("struts "+L.Count+" | "+string.Join(" ",L.Take(6).Select(l=>{ var v=l.Direction; return (l.Length/1000).ToString("0.00")+"m@"+(Math.Atan2(Math.Sqrt(v.X*v.X+v.Y*v.Y),Math.Abs(v.Z))*180/Math.PI).ToString("0")+"deg"; }))+" | eave overhang "+string.Join(" ",Out(neg,"Result").VolatileData.AllData(true))+" | eave pts "+string.Join(" ",Out(el,"Point").VolatileData.AllData(true).Take(3)));
var arch=new GH_IO.Serialization.GH_Archive(); arch.CreateNewRoot(false); arch.AppendObject(doc,"Definition"); Console.WriteLine("write "+arch.WriteToFile(@"C:\Users\gonza\Documents\GitHub\pyramid-roof\polyframe2\friend-15-pyramid-branches-struts.gh",true,false));
var old=Instances.ActiveCanvas.Document; Instances.DocumentServer.AddDocument(doc); Instances.ActiveCanvas.Document=doc; if(old!=null){ old.Enabled=false; Instances.DocumentServer.RemoveDocument(old); old.Dispose(); }
doc.NewSolution(false);
