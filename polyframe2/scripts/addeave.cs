using Grasshopper; using Grasshopper.Kernel; using Grasshopper.Kernel.Types; using Grasshopper.Kernel.Parameters; using Grasshopper.Kernel.Special; using Rhino.Geometry; using System.Drawing;
var io=new GH_DocumentIO(); io.Open(@"C:\Users\gonza\Documents\GitHub\pyramid-roof\polyframe2\friend-15-pyramid-branches-cut.gh"); var doc=io.Document;
IGH_Component Add(string name,float x,float y,string outName=null){ var p=Instances.ComponentServer.ObjectProxies.First(q=>q.Desc.Name==name && !q.Obsolete && q.Kind==GH_ObjectType.CompiledObject && typeof(IGH_Component).IsAssignableFrom(q.Type) && !q.Desc.Category.StartsWith("Karamba") && (outName==null || ((IGH_Component)q.CreateInstance()).Params.Output.Any(o=>o.Name==outName))); var o=(IGH_Component)p.CreateInstance(); o.CreateAttributes(); o.Attributes.Pivot=new PointF(x,y); doc.AddObject(o,false); return o;}
IGH_Param In(IGH_Component c, string n)=> c.Params.Input.First(i=>i.Name==n||i.NickName==n);
IGH_Param Out(IGH_Component c, string n)=> c.Params.Output.First(i=>i.Name==n||i.NickName==n);
void W(IGH_Component a,string o,IGH_Component b,string i){ In(b,i).AddSource(Out(a,o)); }
void Set(IGH_Param q,IGH_Goo v){ var pd=q.GetType().GetProperty("PersistentData").GetValue(q); pd.GetType().GetMethod("Clear").Invoke(pd,null); pd.GetType().GetMethods().First(m=>m.Name=="Append"&&m.GetParameters().Length==1).Invoke(pd,new object[]{v}); }
var comps=doc.Objects.OfType<IGH_Component>().ToList();
var ep2=comps.First(c=>c.Name=="Extrude Point" && c.Params.Input[0].Sources.Any(s=>s.Attributes.GetTopLevel.DocObject is IGH_Component rc && rc.Name=="Rectangle"));
var rect=(IGH_Component)ep2.Params.Input[0].Sources[0].Attributes.GetTopLevel.DocObject;
var cd=comps.First(c=>c.Name=="Cull Duplicates"); var pp=comps.First(c=>c.Name=="Project Point");
var sR=doc.Objects.OfType<GH_NumberSlider>().First(s=>s.NickName=="Branch display radius (mm)");
var pc=comps.First(c=>c.Name=="Project Curve");
var cpOrange=comps.First(c=>c.Name=="Custom Preview" && c.Params.Input[0].Sources.Any(s=>s.Attributes.GetTopLevel.DocObject is IGH_Component pq && pq.Name=="Pipe" && pq.Params.Input[0].Sources.Any(z=>z.Attributes.GetTopLevel.DocObject==pc)));
var swO=cpOrange.Params.Input[1].Sources[0];
float X0=60, Y0=2500;
// 1. feet = dome nodes on the ground; take their projections on the skin
var dz=Add("Deconstruct",X0,Y0,"Z component"); W(cd,"Points",dz,"Point");
var lt=Add("Smaller Than",X0+140,Y0); W(dz,"Z component",lt,"First Number"); Set(In(lt,"Second Number"),new GH_Number(100));
var cf=Add("Cull Pattern",X0+280,Y0); W(pp,"Point",cf,"List"); W(lt,"Smaller than",cf,"Cull Pattern");
// 2. position of each foot along the eave rim (arc length), sorted
var ccp=Add("Curve Closest Point",X0+420,Y0); W(cf,"List",ccp,"Point"); W(rect,"Rectangle",ccp,"Curve");
var lp=Add("Length Parameter",X0+560,Y0); W(rect,"Rectangle",lp,"Curve"); W(ccp,"Parameter",lp,"Parameter");
var sl=Add("Sort List",X0+700,Y0); In(sl,"Keys").AddSource(lp.Params.Output[0]); W(cf,"List",sl,"Values A");
var tot=Add("Length",X0+560,Y0+100); W(rect,"Rectangle",tot,"Curve");
var shK=Add("Shift List",X0+840,Y0); W(sl,"Keys",shK,"List"); Set(In(shK,"Shift"),new GH_Integer(1)); Set(In(shK,"Wrap"),new GH_Boolean(true));
var shF=Add("Shift List",X0+840,Y0+100); W(sl,"Values A",shF,"List"); Set(In(shF,"Shift"),new GH_Integer(1)); Set(In(shF,"Wrap"),new GH_Boolean(true));
// 3. eave point halfway (along the rim) between consecutive feet; across a corner this lands on the corner
var df=Add("Subtraction",X0+980,Y0); W(shK,"List",df,"A"); W(sl,"Keys",df,"B");
var a1=Add("Addition",X0+1120,Y0); W(df,"Result",a1,"A"); W(tot,"Length",a1,"B");
var m1=Add("Modulus",X0+1260,Y0); W(a1,"Result",m1,"A"); W(tot,"Length",m1,"B");
var h=Add("Division",X0+1400,Y0); W(m1,"Result",h,"A"); Set(In(h,"B"),new GH_Number(2));
var a2=Add("Addition",X0+1540,Y0); W(sl,"Keys",a2,"A"); W(h,"Result",a2,"B");
var m2=Add("Modulus",X0+1680,Y0); W(a2,"Result",m2,"A"); W(tot,"Length",m2,"B");
var el=Add("Evaluate Length",X0+1820,Y0); W(rect,"Rectangle",el,"Curve"); W(m2,"Result",el,"Length"); Set(In(el,"Normalized"),new GH_Boolean(false));
// 4. each foot gets two branches down to the eave points on either side (continues the diamond rhythm to the eave)
var l1=Add("Line",X0+1960,Y0); W(sl,"Values A",l1,"Start Point"); W(el,"Point",l1,"End Point");
var l2=Add("Line",X0+1960,Y0+100); W(shF,"List",l2,"Start Point"); W(el,"Point",l2,"End Point");
var mg=Add("Merge",X0+2100,Y0); W(l1,"Line",mg,"Data 1"); W(l2,"Line",mg,"Data 2");
var pi=Add("Pipe",X0+2240,Y0); W(mg,"Result",pi,"Curve"); In(pi,"Radius").AddSource(sR);
var cpE=Add("Custom Preview",X0+2380,Y0); W(pi,"Pipe",cpE,"Geometry"); In(cpE,"Material").AddSource(swO);
foreach(var o in new IGH_DocumentObject[]{dz,lt,cf,ccp,lp,sl,tot,shK,shF,df,a1,m1,h,a2,m2,el,l1,l2,mg,pi}) if(o is IGH_PreviewObject po) po.Hidden=true;
var n=new GH_Panel(); n.CreateAttributes(); n.NickName="Eave branches - read me"; n.UserText="Fills the bare eave strip and the 4 corners. Each foot (its point on the skin, directly above the dome foot) gets two branches running down to the eave rim: to the points halfway (along the rim) to its neighbouring feet. Between the two feet next to a corner that halfway point IS the plan corner, so every corner closes as a V. Result: the diamond rhythm of the dome continues down to the eave. Follows all sliders."; n.Attributes.Pivot=new PointF(X0,Y0+120); doc.AddObject(n,false); n.Attributes.Bounds=new RectangleF(X0,Y0+120,440,100); n.Properties.Colour=Color.FromArgb(255,255,220,160);
var gr=new GH_Group(); gr.CreateAttributes(); gr.NickName="8  Eave + corner branches (feet down to the eave rim)"; gr.Colour=Color.FromArgb(80,255,200,150); foreach(var o in new IGH_DocumentObject[]{dz,lt,cf,ccp,lp,sl,tot,shK,shF,df,a1,m1,h,a2,m2,el,l1,l2,mg,pi,cpE,n}) gr.AddObject(o.InstanceGuid); doc.AddObject(gr,false);
doc.Enabled=true; doc.NewSolution(false);
foreach(var o in doc.Objects.OfType<IGH_ActiveObject>()) if(o.RuntimeMessageLevel==GH_RuntimeMessageLevel.Error) Console.WriteLine("ERR "+o.NickName+": "+string.Join("|",o.RuntimeMessages(GH_RuntimeMessageLevel.Error)));
Console.WriteLine("feet "+Out(cf,"List").VolatileData.DataCount+" | eave pts: "+string.Join(" ",Out(el,"Point").VolatileData.AllData(true).Select(x=>{ var p=(Point3d)x.ScriptVariable(); return "("+(p.X/1000).ToString("0.00")+","+(p.Y/1000).ToString("0.00")+")"; })));
var L=Out(mg,"Result").VolatileData.AllData(true).Select(x=>((GH_Line)x).Value).ToList(); Console.WriteLine("eave branches "+L.Count+" length "+(L.Sum(l=>l.Length)/1000).ToString("0.0")+" m, each "+(L.Min(l=>l.Length)/1000).ToString("0.00")+"-"+(L.Max(l=>l.Length)/1000).ToString("0.00")+" m");
var arch=new GH_IO.Serialization.GH_Archive(); arch.CreateNewRoot(false); arch.AppendObject(doc,"Definition"); Console.WriteLine("write "+arch.WriteToFile(@"C:\Users\gonza\Documents\GitHub\pyramid-roof\polyframe2\friend-15-pyramid-branches-cut-eaves.gh",true,false));
var old=Instances.ActiveCanvas.Document; Instances.DocumentServer.AddDocument(doc); Instances.ActiveCanvas.Document=doc; if(old!=null){ old.Enabled=false; Instances.DocumentServer.RemoveDocument(old); old.Dispose(); }
doc.NewSolution(false);
