using Grasshopper; using Grasshopper.Kernel; using Grasshopper.Kernel.Types; using Rhino.Geometry; using System.Drawing;
var rd=__rhino_doc__;
{ var all=rd.Objects.GetObjectList(new Rhino.DocObjects.ObjectEnumeratorSettings{HiddenObjects=true,LockedObjects=true}).ToList(); foreach(var o in all) rd.Objects.Purge(o); foreach(var l in rd.Layers.Where(l=>!l.IsDeleted && l.Index!=rd.Layers.CurrentLayerIndex).ToList()) rd.Layers.Purge(l.Index,true); }
rd.ModelUnitSystem=Rhino.UnitSystem.Millimeters;
var dir=@"C:\Users\gonza\Documents\GitHub\pyramid-roof\polyframe2\";
// 1. all 16 iterations from the review set (#1-#16), minus the grey reference-pyramid hip lines
var f=Rhino.FileIO.File3dm.Read(dir+"friend-iterations-review-v5.3dm"); var map=new Dictionary<int,int>(); int added=0, skipped=0;
foreach(var l in f.AllLayers){ if(l.Name=="Default") { map[l.Index]=rd.Layers.CurrentLayerIndex; continue; } int i=rd.Layers.FindName(l.Name)?.Index ?? -1; if(i<0) i=rd.Layers.Add(l.Name,l.Color); map[l.Index]=i; }
foreach(var o in f.Objects){ var g=o.Geometry;
  if(g is LineCurve lc){ var a=lc.PointAtStart; var b=lc.PointAtEnd; if(Math.Abs(Math.Max(a.Z,b.Z)-6670)<1 && Math.Abs(Math.Min(a.Z,b.Z))<1){ skipped++; continue; } }
  var att=o.Attributes.Duplicate(); att.LayerIndex=map.ContainsKey(o.Attributes.LayerIndex)? map[o.Attributes.LayerIndex] : rd.Layers.CurrentLayerIndex; rd.Objects.Add(g,att); added++; }
Console.WriteLine("review objects added "+added+", reference hip lines removed "+skipped);
// 2. #15 with the outer branch pyramid (latest), as item 17 in the same grid (4 cols, 16 m, rows 1.2x)
var items=new (string file,string title,string note)[]{ ("friend-15-pyramid-branches-atbase","17 #15 + outer pyramid as branches (printed formwork, non-structural)","posts on dome nodes | top cut 7.99 m | eave at wall top 1.95 m | struts from the feet | friend-15-pyramid-branches-atbase.gh") };
int cols=4; double sp=16000;
for(int k=0;k<items.Length;k++){ int n=16+k; var it=items[k]; double dx=(n%cols)*sp, dy=-(n/cols)*sp*1.2; var xf=Transform.Translation(dx,dy,0);
 var io=new GH_DocumentIO(); io.Open(dir+it.file+".gh"); var d=io.Document; d.Enabled=true; d.NewSolution(false,GH_SolutionMode.Silent);
 int li=rd.Layers.Add(it.title,Color.Gray); if(li<0) li=rd.Layers.FindName(it.title).Index; int cnt=0;
 foreach(var cp in d.Objects.OfType<IGH_Component>().Where(c=>c.Name=="Custom Preview" && !((IGH_PreviewObject)c).Hidden)){
   if(cp.Params.Input[0].Sources.Any(s=>s.Attributes.GetTopLevel.DocObject is IGH_Component m && m.Name=="Move")) continue;
   if(cp.Params.Input[0].Sources.Any(s=>s.NickName=="Reference pyramid"||s.Name=="Reference pyramid")) continue;
   var geo=cp.Params.Input[0].VolatileData.AllData(true).ToList(); var mats=cp.Params.Input[1].VolatileData.AllData(true).Select(x=>x.ScriptVariable()).ToList();
   for(int i=0;i<geo.Count;i++){ object mo= mats.Count==0? null : mats[Math.Min(i,mats.Count-1)]; Color col=Color.SteelBlue; if(mo is Rhino.Display.DisplayMaterial dm) col=dm.Diffuse; else if(mo is Color cc) col=cc;
     var att=new Rhino.DocObjects.ObjectAttributes{LayerIndex=li,ColorSource=Rhino.DocObjects.ObjectColorSource.ColorFromObject,ObjectColor=Color.FromArgb(255,col)};
     var g=geo[i].ScriptVariable(); if(g is Brep b){ b=b.DuplicateBrep(); b.Transform(xf); rd.Objects.AddBrep(b,att); cnt++; } else if(g is Mesh m){ m=m.DuplicateMesh(); m.Transform(xf); rd.Objects.AddMesh(m,att); cnt++; } } }
 var att2=new Rhino.DocObjects.ObjectAttributes{LayerIndex=li,ColorSource=Rhino.DocObjects.ObjectColorSource.ColorFromObject,ObjectColor=Color.FromArgb(150,150,150)};
 var sq=new Polyline(new[]{new Point3d(-5000,-5000,0),new Point3d(5000,-5000,0),new Point3d(5000,5000,0),new Point3d(-5000,5000,0),new Point3d(-5000,-5000,0)}); sq.Transform(xf); rd.Objects.AddPolyline(sq,att2);
 rd.Objects.AddText(new TextEntity{Plane=new Plane(new Point3d(dx-5000,dy-8200,0),Vector3d.XAxis,Vector3d.YAxis),PlainText=it.title,TextHeight=420},new Rhino.DocObjects.ObjectAttributes{LayerIndex=li});
 rd.Objects.AddText(new TextEntity{Plane=new Plane(new Point3d(dx-5000,dy-9000,0),Vector3d.XAxis,Vector3d.YAxis),PlainText=it.note,TextHeight=280},new Rhino.DocObjects.ObjectAttributes{LayerIndex=li});
 Console.WriteLine(it.file+": "+cnt+" objects at ("+dx+","+dy+")"); d.Enabled=false; d.Dispose(); }
// 3. print models at true size, left of the grid
foreach(var (fn,ox) in new[]{("friend-15-1to50",0.0),("friend-15-1to100",300.0)}){
  var path=dir+@"print\"+fn+".stl"; var nm="print "+fn.Replace("friend-15-",""); var li=rd.Layers.Add(nm,Color.Orange); if(li<0) li=rd.Layers.FindName(nm).Index;
  var bytes=System.IO.File.ReadAllBytes(path); int nt=BitConverter.ToInt32(bytes,80); var m=new Mesh(); int p=84;
  for(int t=0;t<nt;t++){ p+=12; int b0=m.Vertices.Count; for(int k=0;k<3;k++){ m.Vertices.Add(BitConverter.ToSingle(bytes,p),BitConverter.ToSingle(bytes,p+4),BitConverter.ToSingle(bytes,p+8)); p+=12; } m.Faces.AddFace(b0,b0+1,b0+2); p+=2; }
  m.Vertices.CombineIdentical(true,true); m.Normals.ComputeNormals(); m.Compact(); m.Transform(Transform.Translation(ox-14000,0,0));
  rd.Objects.AddMesh(m,new Rhino.DocObjects.ObjectAttributes{LayerIndex=li,ColorSource=Rhino.DocObjects.ObjectColorSource.ColorFromObject,ObjectColor=Color.Orange});
  rd.Objects.AddText(new TextEntity{Plane=new Plane(new Point3d(ox-14100,-160,0),Vector3d.XAxis,Vector3d.YAxis),PlainText=nm+" (true size, mm)",TextHeight=12},new Rhino.DocObjects.ObjectAttributes{LayerIndex=li}); }
rd.Views.Redraw();
Console.WriteLine("objects "+rd.Objects.GetObjectList(new Rhino.DocObjects.ObjectEnumeratorSettings()).Count()+" layers "+rd.Layers.Count(l=>!l.IsDeleted));
foreach(var l in rd.Layers.Where(l=>!l.IsDeleted)) Console.WriteLine(" "+l.Name);
