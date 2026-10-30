using Grasshopper; using Grasshopper.Kernel; using Grasshopper.Kernel.Types; using Grasshopper.Kernel.Parameters; using Grasshopper.Kernel.Special; using Rhino.Geometry; using System.Drawing;
var io=new GH_DocumentIO(); io.Open(@"C:\Users\gonza\Documents\GitHub\pyramid-roof\polyframe2\friend-15-pyramid-branches-struts.gh"); var doc=io.Document;
IGH_Component Add(string name,float x,float y,string outName=null){ var p=Instances.ComponentServer.ObjectProxies.First(q=>q.Desc.Name==name && !q.Obsolete && q.Kind==GH_ObjectType.CompiledObject && typeof(IGH_Component).IsAssignableFrom(q.Type) && !q.Desc.Category.StartsWith("Karamba") && (outName==null || ((IGH_Component)q.CreateInstance()).Params.Output.Any(o=>o.Name==outName))); var o=(IGH_Component)p.CreateInstance(); o.CreateAttributes(); o.Attributes.Pivot=new PointF(x,y); doc.AddObject(o,false); return o;}
IGH_Param In(IGH_Component c, string n)=> c.Params.Input.First(i=>i.Name==n||i.NickName==n);
IGH_Param Out(IGH_Component c, string n)=> c.Params.Output.First(i=>i.Name==n||i.NickName==n);
void W(IGH_Component a,string o,IGH_Component b,string i){ In(b,i).AddSource(Out(a,o)); }
void Set(IGH_Param q,IGH_Goo v){ var pd=q.GetType().GetProperty("PersistentData").GetValue(q); pd.GetType().GetMethod("Clear").Invoke(pd,null); pd.GetType().GetMethods().First(m=>m.Name=="Append"&&m.GetParameters().Length==1).Invoke(pd,new object[]{v}); }
IGH_DocumentObject Top(IGH_Param p)=>p.Attributes.GetTopLevel.DocObject;
var comps=doc.Objects.OfType<IGH_Component>().ToList();
var sE=doc.Objects.OfType<GH_NumberSlider>().First(s=>s.NickName=="Eave edge height above wall top (mm)");
var el=comps.First(c=>c.Name=="Evaluate Length");
var er=comps.First(c=>c.Name=="Rectangle" && In(c,"Plane").Sources.Any(s=>Top(s) is IGH_Component cp && cp.Name=="Construct Point" && In(cp,"Z coordinate").Sources.Contains(sE)));
// the two strut start points (feet at z=0)
var fts=comps.Where(c=>c.Name=="Construct Point" && In(c,"Z coordinate").SourceCount==0 && In(c,"X coordinate").Sources.Any(s=>Top(s) is IGH_Component dc && dc.Name=="Deconstruct")).ToList();
Console.WriteLine("strut start components "+fts.Count);
float X0=60, Y0=3400;
// which eave points are corners of the eave edge
var dco=Add("Discontinuity",X0,Y0); W(er,"Rectangle",dco,"Curve");
var cl=Add("Closest Point",X0+140,Y0); W(el,"Point",cl,"Point"); W(dco,"Points",cl,"Cloud");
var lt=Add("Smaller Than",X0+280,Y0); W(cl,"Distance",lt,"First Number"); Set(In(lt,"Second Number"),new GH_Number(1));
var pk=Add("Multiplication",X0+420,Y0); W(lt,"Smaller than",pk,"A"); In(pk,"B").AddSource(sE);
// corner struts start on the foot post at eave height -> horizontal; side struts still start on the foot (sloped)
foreach(var f in fts){ In(f,"Z coordinate").RemoveAllSources(); W(pk,"Result",f,"Z coordinate"); }
foreach(var o in new IGH_DocumentObject[]{dco,cl,lt,pk}) if(o is IGH_PreviewObject po) po.Hidden=true;
var n=new GH_Panel(); n.CreateAttributes(); n.NickName="Flat corners - read me"; n.UserText="Corner struts are now HORIZONTAL: they leave the two foot posts next to each corner at eave height and run flat to the corner, so each corner is a flat horizontal V at the eave. Side struts stay sloped from the feet. NOTE: a horizontal strut cannot carry the corner's weight by compression alone - the two flat members work as short cantilevers off the posts (bending), or need a tie/diagonal underneath. To be checked in Karamba once the skin weight is known."; n.Attributes.Pivot=new PointF(X0,Y0+80); doc.AddObject(n,false); n.Attributes.Bounds=new RectangleF(X0,Y0+80,440,100); n.Properties.Colour=Color.FromArgb(255,255,220,160);
var gr=new GH_Group(); gr.CreateAttributes(); gr.NickName="10  Corner struts flat (horizontal at eave height)"; gr.Colour=Color.FromArgb(80,150,210,230); foreach(var o in new IGH_DocumentObject[]{dco,cl,lt,pk,n}) gr.AddObject(o.InstanceGuid); doc.AddObject(gr,false);
doc.Enabled=true; doc.NewSolution(false);
foreach(var o in doc.Objects.OfType<IGH_ActiveObject>()) if(o.RuntimeMessageLevel==GH_RuntimeMessageLevel.Error) Console.WriteLine("ERR "+o.NickName+": "+string.Join("|",o.RuntimeMessages(GH_RuntimeMessageLevel.Error)));
var mg=comps.First(c=>c.Name=="Merge" && c.Params.Input[0].Sources.Any(s=>Top(s) is IGH_Component l && l.Name=="Line" && In(l,"Start Point").Sources.Any(z=>fts.Contains(Top(z)))));
var L=Out(mg,"Result").VolatileData.AllData(true).Select(x=>((GH_Line)x).Value).ToList();
Console.WriteLine("struts "+L.Count+": "+string.Join(" ",L.Select(l=>{ var v=l.Direction; return (l.Length/1000).ToString("0.00")+"@"+(Math.Atan2(Math.Sqrt(v.X*v.X+v.Y*v.Y),Math.Abs(v.Z))*180/Math.PI).ToString("0"); }).Distinct()));
var arch=new GH_IO.Serialization.GH_Archive(); arch.CreateNewRoot(false); arch.AppendObject(doc,"Definition"); Console.WriteLine("write "+arch.WriteToFile(@"C:\Users\gonza\Documents\GitHub\pyramid-roof\polyframe2\friend-15-pyramid-branches-flatcorners.gh",true,false));
var old=Instances.ActiveCanvas.Document; Instances.DocumentServer.AddDocument(doc); Instances.ActiveCanvas.Document=doc; if(old!=null){ old.Enabled=false; Instances.DocumentServer.RemoveDocument(old); old.Dispose(); }
doc.NewSolution(false);
