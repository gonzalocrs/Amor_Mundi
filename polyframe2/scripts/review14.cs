using Grasshopper; using Grasshopper.Kernel; using Grasshopper.Kernel.Types; using Rhino.Geometry; using System.Drawing;
var rd=__rhino_doc__; foreach(var o in rd.Objects.GetObjectList(new Rhino.DocObjects.ObjectEnumeratorSettings{HiddenObjects=true,NormalObjects=false,LockedObjects=false}).ToList()) rd.Objects.Show(o,true);
// clear my private scratch document
{ var kl=rd.Layers.FindName("karamba check"); if(kl!=null) foreach(var o in rd.Objects.FindByLayer(kl)) rd.Objects.Delete(o,true); }
var items=new (string file,string title,string note)[]{ ("friend-12-feet-near-corners-opentop","14 12 feet (1 m from corners + mid) + OPEN TOP, corners free","12 feet | A and B all C | Karamba 0.56 | corners 0.73 m short") };
int cols=4; double sp=16000; var log=new System.Text.StringBuilder();
for(int n0=0;n0<items.Length;n0++){
 int n=13+n0; var it=items[n0]; double dx=(n%cols)*sp, dy=-(n/cols)*sp*1.2; var xf=Transform.Translation(dx,dy,0);
 var io=new GH_DocumentIO(); if(!io.Open("C:/Users/gonza/Documents/GitHub/pyramid-roof/polyframe2/"+it.file+".gh")){ log.AppendLine("cannot open "+it.file); continue; }
 var d=io.Document; d.Enabled=true; var sw=System.Diagnostics.Stopwatch.StartNew(); d.NewSolution(false,GH_SolutionMode.Silent);
 var pipes=d.Objects.OfType<IGH_Component>().Where(c=>c.Name=="PFPipe").ToList();
 var pp=pipes.FirstOrDefault(c=>c.Params.Input[0].Sources.Any(s=>s.Attributes.GetTopLevel.DocObject.Name=="PFPerp")) ?? pipes.LastOrDefault();
 int li=rd.Layers.Add(it.title, Color.Gray); if(li<0) li=rd.Layers.FindName(it.title).Index;
 int cnt=0;
 if(pp!=null){ var P=pp.Params.Output.First(o=>o.Name=="Pipe").VolatileData.AllData(true).Select(x=>((GH_Brep)x).Value).ToList(); var C=pp.Params.Output.First(o=>o.Name=="Color").VolatileData.AllData(true).Select(x=>((GH_Colour)x).Value).ToList();
   // rescale pipes thinner for readability: re-pipe axes at r=40
   var ax=pp.Params.Output.First(o=>o.Name=="Axes").VolatileData.AllData(true).Select(x=>((GH_Line)x).Value).ToList();
   for(int i=0;i<ax.Count;i++){ var l=ax[i]; l.Transform(xf); var b=Brep.CreatePipe(l.ToNurbsCurve(),45,false,PipeCapMode.Flat,true,1,0.1); if(b==null||b.Length==0) continue; var col= i<C.Count? C[i] : Color.SteelBlue; rd.Objects.AddBrep(b[0],new Rhino.DocObjects.ObjectAttributes{LayerIndex=li,ColorSource=Rhino.DocObjects.ObjectColorSource.ColorFromObject,ObjectColor=col}); cnt++; } }
 // reference pyramid edges
 var A=new Point3d(0,0,6670); var Cn=new[]{new Point3d(-5000,-5000,0),new Point3d(5000,-5000,0),new Point3d(5000,5000,0),new Point3d(-5000,5000,0)};
 var att=new Rhino.DocObjects.ObjectAttributes{LayerIndex=li,ColorSource=Rhino.DocObjects.ObjectColorSource.ColorFromObject,ObjectColor=Color.FromArgb(150,150,150)};
 for(int k=0;k<4;k++){ var l1=new Line(Cn[k],Cn[(k+1)%4]); l1.Transform(xf); rd.Objects.AddLine(l1,att); var l2=new Line(Cn[k],A); l2.Transform(xf); rd.Objects.AddLine(l2,att); }
 var t1=new TextEntity{Plane=new Plane(new Point3d(dx-5000,dy-6200,0),Vector3d.XAxis,Vector3d.YAxis),PlainText=it.title,TextHeight=420}; rd.Objects.AddText(t1,new Rhino.DocObjects.ObjectAttributes{LayerIndex=li});
 var t2=new TextEntity{Plane=new Plane(new Point3d(dx-5000,dy-7000,0),Vector3d.XAxis,Vector3d.YAxis),PlainText=it.note+" | "+it.file+".gh",TextHeight=280}; rd.Objects.AddText(t2,new Rhino.DocObjects.ObjectAttributes{LayerIndex=li});
 log.AppendLine(it.file+": "+cnt+" bars baked, solve "+sw.ElapsedMilliseconds+" ms");
 d.Enabled=false; d.Dispose();
}
rd.Views.Redraw(); Console.WriteLine(log.ToString());
