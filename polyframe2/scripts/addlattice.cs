using Grasshopper; using Grasshopper.Kernel; using Grasshopper.Kernel.Types; using Grasshopper.Kernel.Parameters; using Grasshopper.Kernel.Special; using Rhino.Geometry; using System.Drawing;
var io=new GH_DocumentIO(); io.Open(@"C:\Users\gonza\Documents\GitHub\pyramid-roof\polyframe2\__IN__.gh"); var doc=io.Document;
IGH_Component Add(string name,float x,float y){ var p=Instances.ComponentServer.ObjectProxies.First(q=>q.Desc.Name==name && !q.Obsolete && q.Kind==GH_ObjectType.CompiledObject && typeof(IGH_Component).IsAssignableFrom(q.Type) && !q.Desc.Category.StartsWith("Karamba") && !q.Desc.Category.StartsWith("Params")); var o=(IGH_Component)p.CreateInstance(); o.CreateAttributes(); o.Attributes.Pivot=new PointF(x,y); doc.AddObject(o,false); return o;}
IGH_Param In(IGH_Component c, string n)=> c.Params.Input.First(i=>i.Name==n||i.NickName==n);
IGH_Param Out(IGH_Component c, string n)=> c.Params.Output.First(i=>i.Name==n||i.NickName==n);
void W(IGH_Component a,string o,IGH_Component b,string i){ In(b,i).AddSource(Out(a,o)); }
void Set(IGH_Param q,IGH_Goo v){ var pd=q.GetType().GetProperty("PersistentData").GetValue(q); pd.GetType().GetMethod("Clear").Invoke(pd,null); pd.GetType().GetMethods().First(m=>m.Name=="Append"&&m.GetParameters().Length==1).Invoke(pd,new object[]{v}); }
var ep2=doc.Objects.OfType<IGH_Component>().First(c=>c.Name=="Extrude Point" && c.Params.Input[0].Sources.Any(s=>s.Attributes.GetTopLevel.DocObject is IGH_Component rc && rc.Name=="Rectangle"));
var cpSkin=doc.Objects.OfType<IGH_Component>().First(c=>c.Name=="Custom Preview" && c.Params.Input[0].Sources.Any(s=>s.Attributes.GetTopLevel.DocObject==ep2));
((IGH_PreviewObject)cpSkin).Hidden=true;
var perp=doc.Objects.OfType<IGH_Component>().First(c=>c.Name=="PFPerp");
float X0=60, Y0=1500;
var ex=Add("Explode PFoam",X0,Y0); In(ex,"PFoam").AddSource(Out(perp,"PFoam"));
var sep=Add("Separate PFEdges By Type",X0+160,Y0); W(ex,"PFEdges",sep,"PFEdge");
var ie=Add("Inspect PFEdge",X0+320,Y0); W(sep,"Internal",ie,"PFEdge");
var uz=Add("Unit Z",X0+320,Y0+120);
var pc=Add("Project Curve",X0+500,Y0); W(ie,"Line",pc,"Curve"); W(ep2,"Extrusion",pc,"Brep"); W(uz,"Unit vector",pc,"Direction");
var en=Add("End Points",X0+500,Y0+120); W(ie,"Line",en,"Curve");
var mg=Add("Merge",X0+640,Y0+120); W(en,"Start",mg,"Data 1"); W(en,"End",mg,"Data 2");
var fl=Add("Flatten Tree",X0+760,Y0+120); W(mg,"Result",fl,"Tree");
var cd=Add("Cull Duplicates",X0+880,Y0+120); W(fl,"Tree",cd,"Points"); Set(In(cd,"Tolerance"),new GH_Number(5));
var pp=Add("Project Point",X0+1020,Y0+120); W(cd,"Points",pp,"Point"); W(uz,"Unit vector",pp,"Direction"); W(ep2,"Extrusion",pp,"Geometry");
var ln=Add("Line",X0+1160,Y0+120); W(cd,"Points",ln,"Start Point"); W(pp,"Point",ln,"End Point");
var be=Add("Brep Edges",X0+640,Y0-120); W(ep2,"Extrusion",be,"Brep");
var swp=Instances.ComponentServer.ObjectProxies.First(q=>q.Desc.Name=="Colour Swatch" && !q.Obsolete);
IGH_Param Sw(Color c,float x,float y){ var s=(IGH_Param)swp.CreateInstance(); s.CreateAttributes(); s.Attributes.Pivot=new PointF(x,y); doc.AddObject(s,false); s.GetType().GetProperty("SwatchColour")?.SetValue(s,c); return s; }
var sR=new GH_NumberSlider(); sR.CreateAttributes(); sR.NickName="Branch display radius (mm)"; sR.Slider.Minimum=10; sR.Slider.Maximum=200; sR.Slider.DecimalPlaces=0; sR.Slider.Type=Grasshopper.GUI.Base.GH_SliderAccuracy.Integer; sR.SetSliderValue(50); sR.Attributes.Pivot=new PointF(X0+1160,Y0-200); doc.AddObject(sR,false);
IGH_Component PipeOf(IGH_Component src,string o,float y){ var p=Add("Pipe",X0+1320,y); W(src,o,p,"Curve"); In(p,"Radius").AddSource(sR); return p; }
var p1=PipeOf(pc,"Curve",Y0); var p2=PipeOf(ln,"Line",Y0+120); var p3=PipeOf(be,"Interior",Y0-60); var p4=PipeOf(be,"Naked",Y0-120);
var s1=Sw(Color.FromArgb(255,235,140,40),X0+1460,Y0); var s2=Sw(Color.FromArgb(255,150,150,150),X0+1460,Y0+120);
IGH_Component CP(IGH_Component src,IGH_Param sw,float y){ var c=Add("Custom Preview",X0+1600,y); W(src,"Pipe",c,"Geometry"); In(c,"Material").AddSource(sw); return c; }
var c1=CP(p1,s1,Y0); var c2=CP(p2,s2,Y0+120); var c3=CP(p3,s1,Y0-60); var c4=CP(p4,s1,Y0-120);
foreach(var o in new IGH_DocumentObject[]{ex,sep,ie,pc,en,mg,fl,cd,pp,ln,be,p1,p2,p3,p4}) if(o is IGH_PreviewObject po) po.Hidden=true;
var n=new GH_Panel(); n.CreateAttributes(); n.NickName="Outer branch skin - read me"; n.UserText="OUTER PYRAMID AS A BRANCH SYSTEM (printed formwork, NOT structural). Orange = the dome branches projected straight up (Z) onto the pyramid faces, so every outer branch sits directly above an inner one (same pattern, split at the hips), plus the 4 hips and the eave edge. Grey = vertical posts from each dome node up to the skin: they hand the formwork weight down to the nodes as VERTICAL loads only, which keeps the dome compression-only. Pyramid size comes from the skin sliders (group 5). __TXT__"; n.Attributes.Pivot=new PointF(X0,Y0+260); doc.AddObject(n,false); n.Attributes.Bounds=new RectangleF(X0,Y0+260,460,150); n.Properties.Colour=Color.FromArgb(255,255,220,160);
var gr=new GH_Group(); gr.CreateAttributes(); gr.NickName="6  Outer pyramid as branches (projected dome pattern) + vertical posts"; gr.Colour=Color.FromArgb(80,255,190,120); foreach(var o in new IGH_DocumentObject[]{ex,sep,ie,uz,pc,en,mg,fl,cd,pp,ln,be,sR,p1,p2,p3,p4,s1,s2,c1,c2,c3,c4,n}) gr.AddObject(o.InstanceGuid); doc.AddObject(gr,false);
var old=Instances.ActiveCanvas.Document; Instances.DocumentServer.AddDocument(doc); Instances.ActiveCanvas.Document=doc; if(old!=null){ old.Enabled=false; Instances.DocumentServer.RemoveDocument(old); old.Dispose(); }
doc.Enabled=true; var sw=System.Diagnostics.Stopwatch.StartNew(); doc.NewSolution(false); Console.WriteLine("solve ms "+sw.ElapsedMilliseconds);
foreach(var o in doc.Objects.OfType<IGH_ActiveObject>()) if(o.RuntimeMessageLevel==GH_RuntimeMessageLevel.Error) Console.WriteLine("ERR "+o.NickName+": "+string.Join("|",o.RuntimeMessages(GH_RuntimeMessageLevel.Error)));
var cur=Out(pc,"Curve").VolatileData.AllData(true).Select(x=>((GH_Curve)x).Value).ToList();
var mids=new List<Point3d>(); double Lout=0; var angs=new List<double>(); int nseg=0;
foreach(var c in cur){ var m=c.PointAtNormalizedLength(0.5); if(mids.Any(q=>q.DistanceTo(m)<5)) continue; mids.Add(m); Lout+=c.GetLength(); Polyline pl; if(c.TryGetPolyline(out pl)){ for(int i=0;i<pl.Count-1;i++){ var v=pl[i+1]-pl[i]; if(v.Length<1) continue; angs.Add(Math.Atan2(Math.Sqrt(v.X*v.X+v.Y*v.Y),Math.Abs(v.Z))*180/Math.PI); nseg++; } } else { var v=c.PointAtEnd-c.PointAtStart; angs.Add(Math.Atan2(Math.Sqrt(v.X*v.X+v.Y*v.Y),Math.Abs(v.Z))*180/Math.PI); nseg++; } }
var posts=Out(ln,"Line").VolatileData.AllData(true).Select(x=>((GH_Line)x).Value).ToList();
Console.WriteLine("raw projected "+cur.Count+" | outer branches "+mids.Count+" (segments "+nseg+"), length "+(Lout/1000).ToString("0.0")+" m | angle from vertical: <=35 "+angs.Count(a=>a<=35)+", 35-45 "+angs.Count(a=>a>35&&a<=45)+", 45-60 "+angs.Count(a=>a>45&&a<=60)+", >60 "+angs.Count(a=>a>60)+" | posts "+posts.Count+" length "+(posts.Sum(l=>l.Length)/1000).ToString("0.0")+" m, range "+(posts.Count>0?(posts.Min(l=>l.Length)/1000).ToString("0.00")+"-"+(posts.Max(l=>l.Length)/1000).ToString("0.00"):"-")+" m | nodes "+Out(cd,"Points").VolatileData.DataCount);
var arch=new GH_IO.Serialization.GH_Archive(); arch.CreateNewRoot(false); arch.AppendObject(doc,"Definition"); Console.WriteLine("write "+arch.WriteToFile(@"C:\Users\gonza\Documents\GitHub\pyramid-roof\polyframe2\__OUT__.gh",true,false));
