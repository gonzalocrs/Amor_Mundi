using Grasshopper; using Grasshopper.Kernel; using Grasshopper.Kernel.Types; using Grasshopper.Kernel.Parameters; using Grasshopper.Kernel.Special; using Rhino.Geometry; using System.Drawing;
var io=new GH_DocumentIO(); io.Open(@"C:\Users\gonza\Documents\GitHub\pyramid-roof\polyframe2\friend-15-pyramid-branches.gh"); var doc=io.Document;
IGH_Component Add(string name,float x,float y,string outName=null){ var p=Instances.ComponentServer.ObjectProxies.First(q=>q.Desc.Name==name && !q.Obsolete && q.Kind==GH_ObjectType.CompiledObject && typeof(IGH_Component).IsAssignableFrom(q.Type) && !q.Desc.Category.StartsWith("Karamba") && (outName==null || ((IGH_Component)q.CreateInstance()).Params.Output.Any(o=>o.Name==outName))); var o=(IGH_Component)p.CreateInstance(); o.CreateAttributes(); o.Attributes.Pivot=new PointF(x,y); doc.AddObject(o,false); return o;}
IGH_Param In(IGH_Component c, string n)=> c.Params.Input.First(i=>i.Name==n||i.NickName==n);
IGH_Param Out(IGH_Component c, string n)=> c.Params.Output.First(i=>i.Name==n||i.NickName==n);
void W(IGH_Component a,string o,IGH_Component b,string i){ In(b,i).AddSource(Out(a,o)); }
void Set(IGH_Param q,IGH_Goo v){ var pd=q.GetType().GetProperty("PersistentData").GetValue(q); pd.GetType().GetMethod("Clear").Invoke(pd,null); pd.GetType().GetMethods().First(m=>m.Name=="Append"&&m.GetParameters().Length==1).Invoke(pd,new object[]{v}); }
var sB=doc.Objects.OfType<GH_NumberSlider>().First(s=>s.NickName=="Skin base side (mm)"); var sH=doc.Objects.OfType<GH_NumberSlider>().First(s=>s.NickName=="Skin apex height (mm)");
var comps=doc.Objects.OfType<IGH_Component>().ToList();
var ep2=comps.First(c=>c.Name=="Extrude Point" && c.Params.Input[0].Sources.Any(s=>s.Attributes.GetTopLevel.DocObject is IGH_Component rc && rc.Name=="Rectangle"));
var rect=(IGH_Component)ep2.Params.Input[0].Sources[0].Attributes.GetTopLevel.DocObject;
var cpSkin=comps.First(c=>c.Name=="Custom Preview" && c.Params.Input[0].Sources.Any(s=>s.Attributes.GetTopLevel.DocObject==ep2));
var pp=comps.First(c=>c.Name=="Project Point");
var be=comps.First(c=>c.Name=="Brep Edges");
var pipes=comps.Where(c=>c.Name=="Pipe" && c.Params.Input[0].Sources.Any(s=>s.Attributes.GetTopLevel.DocObject==be)).ToList();
var pInt=pipes.First(c=>c.Params.Input[0].Sources.Any(s=>s.Name=="Interior")); var pNak=pipes.First(c=>c.Params.Input[0].Sources.Any(s=>s.Name=="Naked"));
float X0=60, Y0=2100;
var pcv=comps.First(c=>c.Name=="Project Curve");
var dk=Add("Discontinuity",X0-160,Y0+40); W(pcv,"Curve",dk,"Curve"); var mgz=Add("Merge",X0-160,Y0-40); W(pp,"Point",mgz,"Data 1"); W(dk,"Points",mgz,"Data 2");
var flz=Add("Flatten Tree",X0-80,Y0-40); W(mgz,"Result",flz,"Tree");
var dz=Add("Deconstruct",X0,Y0,"Z component"); W(flz,"Tree",dz,"Point");
var bn=Add("Bounds",X0+160,Y0); W(dz,"Z component",bn,"Numbers");
var dd=Add("Deconstruct Domain",X0+300,Y0); W(bn,"Domain",dd,"Domain");
var sO=new GH_NumberSlider(); sO.CreateAttributes(); sO.NickName="Cut height above top of branches (mm)"; sO.Slider.Minimum=-1000; sO.Slider.Maximum=2000; sO.Slider.DecimalPlaces=0; sO.Slider.Type=Grasshopper.GUI.Base.GH_SliderAccuracy.Integer; sO.SetSliderValue(0); sO.Attributes.Pivot=new PointF(X0,Y0+80); doc.AddObject(sO,false);
var zc=Add("Addition",X0+440,Y0); W(dd,"End",zc,"A"); In(zc,"B").AddSource(sO);
var r=Add("Division",X0+580,Y0); W(zc,"Result",r,"A"); In(r,"B").AddSource(sH);
var om=Add("Subtraction",X0+720,Y0); Set(In(om,"A"),new GH_Number(1)); W(r,"Result",om,"B");
var ts=Add("Multiplication",X0+860,Y0); In(ts,"A").AddSource(sB); W(om,"Result",ts,"B");
var hf=Add("Division",X0+1000,Y0); W(ts,"Result",hf,"A"); Set(In(hf,"B"),new GH_Number(-2));
var org2=Add("Construct Point",X0+1140,Y0); W(hf,"Result",org2,"X coordinate"); W(hf,"Result",org2,"Y coordinate"); W(zc,"Result",org2,"Z coordinate");
var rect2=Add("Rectangle",X0+1280,Y0); W(org2,"Point",rect2,"Plane"); W(ts,"Result",rect2,"X Size"); W(ts,"Result",rect2,"Y Size");
var rs=Add("Ruled Surface",X0+1420,Y0); W(rect,"Rectangle",rs,"Curve A"); W(rect2,"Rectangle",rs,"Curve B");
var d1=Add("Discontinuity",X0+1280,Y0+120); W(rect,"Rectangle",d1,"Curve"); var d2=Add("Discontinuity",X0+1280,Y0+200); W(rect2,"Rectangle",d2,"Curve");
var hip=Add("Line",X0+1420,Y0+160); W(d1,"Points",hip,"Start Point"); W(d2,"Points",hip,"End Point");
var mg=Add("Merge",X0+1420,Y0+260); W(rect,"Rectangle",mg,"Data 1"); W(rect2,"Rectangle",mg,"Data 2");
// rewire edge pipes: hips and the two horizontal rims (eave + top cut) instead of the pointed pyramid edges
In(pInt,"Curve").RemoveAllSources(); W(hip,"Line",pInt,"Curve"); In(pNak,"Curve").RemoveAllSources(); W(mg,"Result",pNak,"Curve");
In(cpSkin,"Geometry").RemoveAllSources(); W(rs,"Surface",cpSkin,"Geometry");
foreach(var o in new IGH_DocumentObject[]{dk,mgz,flz,dz,bn,dd,zc,r,om,ts,hf,org2,rect2,rs,d1,d2,hip,mg}) if(o is IGH_PreviewObject po) po.Hidden=true;
var pz=new GH_Panel(); pz.CreateAttributes(); pz.NickName="Cut height (mm)"; pz.Attributes.Pivot=new PointF(X0+580,Y0+80); pz.Attributes.Bounds=new RectangleF(X0+580,Y0+80,160,30); pz.AddSource(Out(zc,"Result")); doc.AddObject(pz,false);
var pt=new GH_Panel(); pt.CreateAttributes(); pt.NickName="Top opening side (mm)"; pt.Attributes.Pivot=new PointF(X0+860,Y0+80); pt.Attributes.Bounds=new RectangleF(X0+860,Y0+80,160,30); pt.AddSource(Out(ts,"Result")); doc.AddObject(pt,false);
var n=new GH_Panel(); n.CreateAttributes(); n.NickName="Cut pyramid - read me"; n.UserText="The outer pyramid is CUT FLAT at the top (truncated), not pointed. Default cut = the highest point of the outer branches (where the projected crown-ring branches cross the hips), so no branch is cut; the slider raises/lowers it. If you lower it below 0, branches above the cut still show - they would have to be trimmed. The square top opening sits above the dome's open crown ring. Hips and the eave + top rims are drawn as branches; the solid skin preview (group 5) now shows the truncated surface (preview off by default). The fit check in group 5 still uses the full pyramid, which is the same below the cut."; n.Attributes.Pivot=new PointF(X0,Y0+160); doc.AddObject(n,false); n.Attributes.Bounds=new RectangleF(X0,Y0+160,440,110); n.Properties.Colour=Color.FromArgb(255,255,220,160);
var gr=new GH_Group(); gr.CreateAttributes(); gr.NickName="7  Cut the pyramid flat at the top of the branches"; gr.Colour=Color.FromArgb(80,200,230,160); foreach(var o in new IGH_DocumentObject[]{dk,mgz,flz,dz,bn,dd,sO,zc,r,om,ts,hf,org2,rect2,rs,d1,d2,hip,mg,pz,pt,n}) gr.AddObject(o.InstanceGuid); doc.AddObject(gr,false);
doc.Enabled=true; doc.NewSolution(false);
foreach(var o in doc.Objects.OfType<IGH_ActiveObject>()) if(o.RuntimeMessageLevel==GH_RuntimeMessageLevel.Error) Console.WriteLine("ERR "+o.NickName+": "+string.Join("|",o.RuntimeMessages(GH_RuntimeMessageLevel.Error)));
Console.WriteLine("cut z "+string.Join(" ",Out(zc,"Result").VolatileData.AllData(true))+" | top side "+string.Join(" ",Out(ts,"Result").VolatileData.AllData(true))+" | hips "+Out(hip,"Line").VolatileData.DataCount+" rims "+Out(mg,"Result").VolatileData.DataCount+" | ruled "+Out(rs,"Surface").VolatileData.DataCount);
var arch=new GH_IO.Serialization.GH_Archive(); arch.CreateNewRoot(false); arch.AppendObject(doc,"Definition"); Console.WriteLine("write "+arch.WriteToFile(@"C:\Users\gonza\Documents\GitHub\pyramid-roof\polyframe2\friend-15-pyramid-branches-cut.gh",true,false));
var old=Instances.ActiveCanvas.Document; Instances.DocumentServer.AddDocument(doc); Instances.ActiveCanvas.Document=doc; if(old!=null){ old.Enabled=false; Instances.DocumentServer.RemoveDocument(old); old.Dispose(); }
doc.NewSolution(false);
