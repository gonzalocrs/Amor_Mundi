using Grasshopper; using Grasshopper.Kernel; using Grasshopper.Kernel.Types; using Grasshopper.Kernel.Parameters; using Grasshopper.Kernel.Special; using Rhino.Geometry; using System.Drawing;
var io=new GH_DocumentIO(); io.Open(@"C:\Users\gonza\Documents\GitHub\pyramid-roof\polyframe2\friend-15-pyramid-branches-cut.gh"); var doc=io.Document;
IGH_Component Add(string name,float x,float y,string outName=null){ var p=Instances.ComponentServer.ObjectProxies.First(q=>q.Desc.Name==name && !q.Obsolete && q.Kind==GH_ObjectType.CompiledObject && typeof(IGH_Component).IsAssignableFrom(q.Type) && !q.Desc.Category.StartsWith("Karamba") && (outName==null || ((IGH_Component)q.CreateInstance()).Params.Output.Any(o=>o.Name==outName))); var o=(IGH_Component)p.CreateInstance(); o.CreateAttributes(); o.Attributes.Pivot=new PointF(x,y); doc.AddObject(o,false); return o;}
IGH_Param In(IGH_Component c, string n)=> c.Params.Input.First(i=>i.Name==n||i.NickName==n);
IGH_Param Out(IGH_Component c, string n)=> c.Params.Output.First(i=>i.Name==n||i.NickName==n);
void W(IGH_Component a,string o,IGH_Component b,string i){ In(b,i).AddSource(Out(a,o)); }
void Set(IGH_Param q,IGH_Goo v){ var pd=q.GetType().GetProperty("PersistentData").GetValue(q); pd.GetType().GetMethod("Clear").Invoke(pd,null); pd.GetType().GetMethods().First(m=>m.Name=="Append"&&m.GetParameters().Length==1).Invoke(pd,new object[]{v}); }
IGH_DocumentObject Top(IGH_Param p)=>p.Attributes.GetTopLevel.DocObject;
var comps=doc.Objects.OfType<IGH_Component>().ToList();
var ep2=comps.First(c=>c.Name=="Extrude Point" && c.Params.Input[0].Sources.Any(s=>Top(s) is IGH_Component rc && rc.Name=="Rectangle"));
var rect=(IGH_Component)Top(ep2.Params.Input[0].Sources[0]);
var cd=comps.First(c=>c.Name=="Cull Duplicates"); var pp=comps.First(c=>c.Name=="Project Point");
var hip=comps.First(c=>c.Name=="Line" && In(c,"Start Point").Sources.Any(s=>Top(s) is IGH_Component dc && dc.Name=="Discontinuity"));
var d1=(IGH_Component)Top(In(hip,"Start Point").Sources[0]);
var rim=comps.First(c=>c.Name=="Merge" && c.Params.Input[0].Sources.Any(s=>Top(s)==rect));
var uz=comps.First(c=>c.Name=="Unit Z");
float X0=60, Y0=2500;
// feet on the skin (posts stand on the dome feet), sorted around the plan
var dz=Add("Deconstruct",X0,Y0,"Z component"); W(cd,"Points",dz,"Point");
var lt=Add("Smaller Than",X0+140,Y0); W(dz,"Z component",lt,"First Number"); Set(In(lt,"Second Number"),new GH_Number(100));
var cf=Add("Cull Pattern",X0+280,Y0); W(pp,"Point",cf,"List"); W(lt,"Smaller than",cf,"Cull Pattern");
var ccp=Add("Curve Closest Point",X0+420,Y0); W(cf,"List",ccp,"Point"); W(rect,"Rectangle",ccp,"Curve");
var lp=Add("Length Parameter",X0+560,Y0); W(rect,"Rectangle",lp,"Curve"); W(ccp,"Parameter",lp,"Parameter");
var sl=Add("Sort List",X0+700,Y0); In(sl,"Keys").AddSource(lp.Params.Output[0]); W(cf,"List",sl,"Values A");
var sh=Add("Shift List",X0+840,Y0); W(sl,"Values A",sh,"List"); Set(In(sh,"Shift"),new GH_Integer(1)); Set(In(sh,"Wrap"),new GH_Boolean(true));
// lower edge of the skin = chain foot-to-foot, laid on the skin (bends up over the hip at each corner)
var ch=Add("Line",X0+980,Y0); W(sl,"Values A",ch,"Start Point"); W(sh,"List",ch,"End Point");
var pcE=Add("Project Curve",X0+1120,Y0); W(ch,"Line",pcE,"Curve"); W(ep2,"Extrusion",pcE,"Brep"); W(uz,"Unit vector",pcE,"Direction");
// hips start where the corner chord crosses them (nothing below that point is carried by the dome)
var mid=Add("Curve Middle",X0+1120,Y0+100); W(ch,"Line",mid,"Curve");
var clp=Add("Closest Point",X0+1260,Y0+100); W(d1,"Points",clp,"Point"); W(mid,"Midpoint",clp,"Cloud");
var pph=Add("Project Point",X0+1400,Y0+100); W(clp,"Closest Point",pph,"Point"); W(uz,"Unit vector",pph,"Direction"); W(ep2,"Extrusion",pph,"Geometry");
In(hip,"Start Point").RemoveAllSources(); W(pph,"Point",hip,"Start Point");
// rims: drop the eave rectangle (not carried), keep the top cut, add the foot-to-foot lower edge
var r2=In(rim,"Data 2").Sources.ToList(); In(rim,"Data 1").RemoveAllSources(); In(rim,"Data 2").RemoveAllSources(); foreach(var s in r2) In(rim,"Data 1").AddSource(s); W(pcE,"Curve",rim,"Data 2");
foreach(var o in new IGH_DocumentObject[]{dz,lt,cf,ccp,lp,sl,sh,ch,pcE,mid,clp,pph}) if(o is IGH_PreviewObject po) po.Hidden=true;
var n=new GH_Panel(); n.CreateAttributes(); n.NickName="Skin rests on the dome - read me"; n.UserText="Every part of the outer branch skin now rests on the dome. The skin STOPS at the feet: its lower edge is the chain foot-to-foot (on the skin, 2.6 m above the wall top, each foot point sits on a 2.6 m post on a dome foot). Across each corner that chain is one branch bridging two foot posts, bending up over the hip (the corner below it would have no dome under it, so it is left out). Hips start where that corner branch crosses them. The eave strip beyond the walls is removed: there is no dome under it, so it could only hang as a cantilever or rest on the walls. Every outer branch now spans between posts or branch joints carried by posts."; n.Attributes.Pivot=new PointF(X0,Y0+160); doc.AddObject(n,false); n.Attributes.Bounds=new RectangleF(X0,Y0+160,460,130); n.Properties.Colour=Color.FromArgb(255,255,220,160);
var gr=new GH_Group(); gr.CreateAttributes(); gr.NickName="8  Skin stops at the feet: lower edge foot-to-foot, hips trimmed (all carried by the dome)"; gr.Colour=Color.FromArgb(80,200,230,255); foreach(var o in new IGH_DocumentObject[]{dz,lt,cf,ccp,lp,sl,sh,ch,pcE,mid,clp,pph,n}) gr.AddObject(o.InstanceGuid); doc.AddObject(gr,false);
doc.Enabled=true; doc.NewSolution(false);
foreach(var o in doc.Objects.OfType<IGH_ActiveObject>()) if(o.RuntimeMessageLevel==GH_RuntimeMessageLevel.Error) Console.WriteLine("ERR "+o.NickName+": "+string.Join("|",o.RuntimeMessages(GH_RuntimeMessageLevel.Error)));
Console.WriteLine("feet "+Out(cf,"List").VolatileData.DataCount+" | edge branches "+Out(pcE,"Curve").VolatileData.DataCount+" | hip starts "+string.Join(" ",Out(pph,"Point").VolatileData.AllData(true).Select(x=>{ var p=(Point3d)x.ScriptVariable(); return "("+(p.X/1000).ToString("0.00")+","+(p.Y/1000).ToString("0.00")+","+(p.Z/1000).ToString("0.00")+")"; })));
var E=Out(pcE,"Curve").VolatileData.AllData(true).Select(x=>((GH_Curve)x).Value).ToList(); Console.WriteLine("edge lengths "+string.Join(" ",E.Select(c=>(c.GetLength()/1000).ToString("0.00")))+" | max z "+(E.Max(c=>c.GetBoundingBox(true).Max.Z)/1000).ToString("0.00"));
var arch=new GH_IO.Serialization.GH_Archive(); arch.CreateNewRoot(false); arch.AppendObject(doc,"Definition"); Console.WriteLine("write "+arch.WriteToFile(@"C:\Users\gonza\Documents\GitHub\pyramid-roof\polyframe2\friend-15-pyramid-branches-supported.gh",true,false));
var old=Instances.ActiveCanvas.Document; Instances.DocumentServer.AddDocument(doc); Instances.ActiveCanvas.Document=doc; if(old!=null){ old.Enabled=false; Instances.DocumentServer.RemoveDocument(old); old.Dispose(); }
doc.NewSolution(false);
