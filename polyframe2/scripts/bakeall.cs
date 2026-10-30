using Grasshopper; using Grasshopper.Kernel; using Grasshopper.Kernel.Types; using Rhino.Geometry; using System.Drawing;
var rd=__rhino_doc__; Console.WriteLine("private doc objects before: "+rd.Objects.Count);
foreach(var o in rd.Objects.ToList()) rd.Objects.Delete(o,true);
rd.ModelUnitSystem=Rhino.UnitSystem.Millimeters;
var dir=@"C:\Users\gonza\Documents\GitHub\pyramid-roof\polyframe2\";
var items=new (string file,string title,string note)[]{
 ("friend-12-feet-near-corners-opentop","#14  12 feet, 1 m from corners, corners free, open top","PolyFrame all C | Karamba 0.56 | corners 0.73 m short"),
 ("friend-12-feet-2m-corners-opentop","#15  12 feet, 2 m from corners, corners free, open top","PolyFrame all C | Karamba 0.53 | 1,344 kN | corners 1.43 m short | CHOSEN"),
 ("friend-20-feet-2m-corners-opentop","#16  20 feet (5/side), 2 m from corners, open top","final all C | Karamba 0.37 | 1,434 kN | nodes 54 mm apart"),
 ("friend-15-pyramid-skin","#15 + outer pyramid skin (solid, non-structural)","base 13.90 m, apex 9.27 m, 53 deg, eaves 1.95 m, 200 mm clear"),
 ("friend-16-pyramid-skin","#16 + outer pyramid skin (solid, non-structural)","base 14.73 m, apex 9.82 m, eaves 2.36 m"),
 ("friend-15-pyramid-branches","#15 + outer pyramid as branches (printed formwork)","dome pattern projected up + 84 vertical posts"),
 ("friend-15-pyramid-branches-cut","#15 branches, pyramid cut flat at the top","cut 7.99 m, top opening 1.92 m"),
 ("friend-15-pyramid-branches-cut-eaves","#15 branches + eave/corner V branches","feet -> eave rim; corners close as V (eave not carried)"),
 ("friend-15-pyramid-branches-supported","#15 branches, skin stops at the feet","everything rests on the dome; no eaves"),
 ("friend-15-pyramid-branches-struts","#15 branches + sloped struts from the feet","eave edge raised 1.5 m; struts 48-63 deg"),
 ("friend-15-pyramid-branches-flatcorners","#15 branches, corner struts horizontal at eave height","corner struts 2.95 m flat (bending)"),
 ("friend-15-pyramid-branches-atbase","#15 branches, corners down at the shell base (LATEST)","eave at wall top, 1.95 m; struts flat 2.4-4.4 m (bending)")};
int cols=4; double sp=20000; var log=new System.Text.StringBuilder();
for(int n=0;n<items.Length;n++){
 var it=items[n]; double dx=(n%cols)*sp, dy=-(n/cols)*sp*1.25; var xf=Transform.Translation(dx,dy,0);
 var io=new GH_DocumentIO(); if(!io.Open(dir+it.file+".gh")){ log.AppendLine("cannot open "+it.file); continue; }
 var d=io.Document; d.Enabled=true; d.NewSolution(false,GH_SolutionMode.Silent);
 var li=rd.Layers.Add(it.title,Color.Gray); if(li<0) li=rd.Layers.FindName(it.title).Index;
 int cnt=0;
 foreach(var cp in d.Objects.OfType<IGH_Component>().Where(c=>c.Name=="Custom Preview" && !((IGH_PreviewObject)c).Hidden)){
   // skip the stage A copy shown on the left (fed by a Move)
   if(cp.Params.Input[0].Sources.Any(s=>s.Attributes.GetTopLevel.DocObject is IGH_Component m && m.Name=="Move")) continue;
   var geo=cp.Params.Input[0].VolatileData.AllData(true).ToList(); var mats=cp.Params.Input[1].VolatileData.AllData(true).Select(x=>x.ScriptVariable()).ToList();
   for(int i=0;i<geo.Count;i++){
     object mo= mats.Count==0? null : mats[Math.Min(i,mats.Count-1)]; Color col=Color.SteelBlue; int alpha=255;
     if(mo is Rhino.Display.DisplayMaterial dm){ col=dm.Diffuse; alpha=(int)(255*(1-dm.Transparency)); } else if(mo is Color cc) col=cc;
     var att=new Rhino.DocObjects.ObjectAttributes{LayerIndex=li,ColorSource=Rhino.DocObjects.ObjectColorSource.ColorFromObject,ObjectColor=Color.FromArgb(255,col)};
     var g=geo[i].ScriptVariable();
     if(g is Brep b){ b=b.DuplicateBrep(); b.Transform(xf); rd.Objects.AddBrep(b,att); cnt++; }
     else if(g is Mesh m){ m=m.DuplicateMesh(); m.Transform(xf); rd.Objects.AddMesh(m,att); cnt++; }
     else if(g is Surface sf){ var bb=sf.ToBrep(); bb.Transform(xf); rd.Objects.AddBrep(bb,att); cnt++; }
     else if(g is Extrusion ex){ var bb=ex.ToBrep(); bb.Transform(xf); rd.Objects.AddBrep(bb,att); cnt++; }
     else if(g is Curve c){ c=c.DuplicateCurve(); c.Transform(xf); rd.Objects.AddCurve(c,att); cnt++; }
     else if(g is Line ln){ ln.Transform(xf); rd.Objects.AddLine(ln,att); cnt++; }
   } }
 // wall outline + labels
 var att2=new Rhino.DocObjects.ObjectAttributes{LayerIndex=li,ColorSource=Rhino.DocObjects.ObjectColorSource.ColorFromObject,ObjectColor=Color.FromArgb(120,120,120)};
 var sq=new Polyline(new[]{new Point3d(-5000,-5000,0),new Point3d(5000,-5000,0),new Point3d(5000,5000,0),new Point3d(-5000,5000,0),new Point3d(-5000,-5000,0)}); sq.Transform(xf); rd.Objects.AddPolyline(sq,att2);
 rd.Objects.AddText(new TextEntity{Plane=new Plane(new Point3d(dx-8000,dy-8600,0),Vector3d.XAxis,Vector3d.YAxis),PlainText=it.title,TextHeight=450},new Rhino.DocObjects.ObjectAttributes{LayerIndex=li});
 rd.Objects.AddText(new TextEntity{Plane=new Plane(new Point3d(dx-8000,dy-9400,0),Vector3d.XAxis,Vector3d.YAxis),PlainText=it.note+" | "+it.file+".gh",TextHeight=300},new Rhino.DocObjects.ObjectAttributes{LayerIndex=li});
 log.AppendLine(it.file+": "+cnt+" objects"); d.Enabled=false; d.Dispose();
}
// print models (scaled 1:50 and 1:100 meshes), placed at true print size next to the grid
foreach(var (f,ox) in new[]{("friend-15-1to50",0.0),("friend-15-1to100",300.0)}){
  var path=dir+@"print\"+f+".stl"; var li=rd.Layers.Add("print "+f.Replace("friend-15-",""),Color.Orange); if(li<0) li=rd.Layers.FindName("print "+f.Replace("friend-15-","")).Index;
  var bytes=System.IO.File.ReadAllBytes(path); int nt=BitConverter.ToInt32(bytes,80); var m=new Mesh(); int p=84;
  for(int t=0;t<nt;t++){ p+=12; int b0=m.Vertices.Count; for(int k=0;k<3;k++){ m.Vertices.Add(BitConverter.ToSingle(bytes,p),BitConverter.ToSingle(bytes,p+4),BitConverter.ToSingle(bytes,p+8)); p+=12; } m.Faces.AddFace(b0,b0+1,b0+2); p+=2; }
  m.Vertices.CombineIdentical(true,true); m.Normals.ComputeNormals(); m.Compact(); m.Transform(Transform.Translation(4*sp+ox,0,0));
  rd.Objects.AddMesh(m,new Rhino.DocObjects.ObjectAttributes{LayerIndex=li,ColorSource=Rhino.DocObjects.ObjectColorSource.ColorFromObject,ObjectColor=Color.Orange});
  rd.Objects.AddText(new TextEntity{Plane=new Plane(new Point3d(4*sp+ox-100,-160,0),Vector3d.XAxis,Vector3d.YAxis),PlainText="print "+f.Replace("friend-15-","")+" (true size, mm)",TextHeight=12},new Rhino.DocObjects.ObjectAttributes{LayerIndex=li});
  log.AppendLine(f+": "+nt+" triangles"); }
rd.Views.Redraw(); Console.WriteLine(log.ToString()); Console.WriteLine("objects "+rd.Objects.Count);
