using Grasshopper; using Grasshopper.Kernel; using Grasshopper.Kernel.Special; using Rhino.Geometry; using System.Drawing;
var io=new GH_DocumentIO(); io.Open(@"C:\Users\gonza\Documents\GitHub\pyramid-roof\polyframe2\friend-AP8-diagrid.gh"); var d=io.Document; d.Enabled=true; d.NewSolution(false,GH_SolutionMode.Silent);
var pc=d.Objects.OfType<GH_Cluster>().First(c=>c.NickName=="Angle from vertical");
var cols=new[]{Color.FromArgb(40,170,60),Color.FromArgb(240,200,30),Color.FromArgb(220,50,40)}; int n=0;
var L=__rhino_doc__.Layers.Add("AP8 diagrid (comparison)",Color.Gray);
var pyr=d.Objects.OfType<GH_Cluster>().First(c=>c.NickName.StartsWith("Plan + wall")).Params.Output.First(o=>o.NickName=="Reference pyramid").VolatileData.AllData(true).Select(x=>((Grasshopper.Kernel.Types.GH_Brep)x).Value).ToList();
var xf=Transform.Translation(14000,0,0);
for(int b=0;b<3;b++) foreach(var g in pc.Params.Output[b].VolatileData.AllData(true)){ var br=((Grasshopper.Kernel.Types.GH_Brep)g).Value.DuplicateBrep(); br.Transform(xf); var at=new Rhino.DocObjects.ObjectAttributes{ LayerIndex=L, ColorSource=Rhino.DocObjects.ObjectColorSource.ColorFromObject, ObjectColor=cols[b]}; __rhino_doc__.Objects.AddBrep(br,at); n++; }
foreach(var p in pyr){ var br=p.DuplicateBrep(); br.Transform(xf); var at=new Rhino.DocObjects.ObjectAttributes{ LayerIndex=L, ColorSource=Rhino.DocObjects.ObjectColorSource.ColorFromObject, ObjectColor=Color.FromArgb(200,200,200)}; __rhino_doc__.Objects.AddBrep(br,at); }
var t=new TextEntity{ Plane=new Plane(new Point3d(9000,-7500,0),Vector3d.XAxis,Vector3d.YAxis), PlainText="AP8 diagrid (8 feet)", TextHeight=600 }; __rhino_doc__.Objects.AddText(t,new Rhino.DocObjects.ObjectAttributes{LayerIndex=L});
var t2=new TextEntity{ Plane=new Plane(new Point3d(-5000,-7500,0),Vector3d.XAxis,Vector3d.YAxis), PlainText="16 feet (5 per side)", TextHeight=600 }; __rhino_doc__.Objects.AddText(t2,new Rhino.DocObjects.ObjectAttributes{LayerIndex=L});
var t3=new TextEntity{ Plane=new Plane(new Point3d(-19000,-7500,0),Vector3d.XAxis,Vector3d.YAxis), PlainText="16 feet - stage A", TextHeight=600 }; __rhino_doc__.Objects.AddText(t3,new Rhino.DocObjects.ObjectAttributes{LayerIndex=L});
d.Enabled=false; d.Dispose(); __rhino_doc__.Views.Redraw(); Console.WriteLine("baked "+n);
