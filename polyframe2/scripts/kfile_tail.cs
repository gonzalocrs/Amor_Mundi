var keep=new List<(string name,IGH_Component asm,IGH_Component an,IGH_Component bf,IGH_Component rf,IGH_Component buck,List<IGH_Component> all)>();
IGH_Component Mk(GH_Document d,string name){ var p=Instances.ComponentServer.ObjectProxies.First(q=>q.Desc.Name==name && !q.Obsolete && typeof(IGH_Component).IsAssignableFrom(q.Type)); var o=(IGH_Component)p.CreateInstance(); o.CreateAttributes(); d.AddObject(o,false); return o; }
List<T> O2<T>(IGH_Component c,string n)=>c.Params.Output.First(o=>o.Name.StartsWith(n)||o.NickName.StartsWith(n)).VolatileData.AllData(true).Select(x=>(T)x.ScriptVariable()).ToList();
Mesh Pyr(double dx){ var m=new Mesh(); var A=new Point3d(dx,0,6670); var C=new[]{new Point3d(dx-5000,-5000,0),new Point3d(dx+5000,-5000,0),new Point3d(dx+5000,5000,0),new Point3d(dx-5000,5000,0)}; int n=24;
 for(int f=0;f<4;f++){ var p=C[f]; var q=C[(f+1)%4]; var idx=new int[n+1,n+1];
  for(int i=0;i<=n;i++) for(int j=0;j<=n-i;j++){ double u=(double)i/n, v=(double)j/n; idx[i,j]=m.Vertices.Count; m.Vertices.Add(p+(q-p)*u+(A-p)*v); }
  for(int i=0;i<n;i++) for(int j=0;j<n-i;j++){ m.Faces.AddFace(idx[i,j],idx[i+1,j],idx[i,j+1]); if(j<n-i-1) m.Faces.AddFace(idx[i+1,j],idx[i+1,j+1],idx[i,j+1]); } }
 m.Normals.ComputeNormals(); m.Compact(); return m; }
(List<Line> bars,List<Point3d> feet) Geom(string f,double dx){
 var io2=new GH_DocumentIO(); io2.Open("C:/Users/gonza/Documents/GitHub/pyramid-roof/polyframe2/"+f+".gh"); var d=io2.Document; d.Enabled=true;
 var perp=d.Objects.OfType<IGH_Component>().First(c=>c.Name=="PFPerp");
 var ex=Mk(d,"Explode PFoam"); ex.Params.Input[0].AddSource(perp.Params.Output[0]); var ie=Mk(d,"Inspect PFEdge"); ie.Params.Input[0].AddSource(ex.Params.Output[1]);
 d.NewSolution(false,GH_SolutionMode.Silent);
 var L=O2<Line>(ie,"Line"); var X=O2<int>(ie,"External");
 var nodes=new List<Point3d>(); int Id(Point3d p){ for(int i=0;i<nodes.Count;i++) if(nodes[i].DistanceTo(p)<1) return i; nodes.Add(p); return nodes.Count-1; }
 var bars=new List<Line>(); var seen=new HashSet<(int,int)>(); for(int i=0;i<L.Count;i++) if(X[i]==0){ int a=Id(L[i].From), b=Id(L[i].To); if(a==b) continue; var k=(Math.Min(a,b),Math.Max(a,b)); if(seen.Add(k)) bars.Add(new Line(nodes[a],nodes[b])); }
 var feet=new List<Point3d>(); for(int i=0;i<L.Count;i++) if(X[i]==2){ var v=L[i].Direction; v.Unitize(); if(Math.Abs(v.Z)<0.999){ foreach(var p in new[]{L[i].From,L[i].To}) if(nodes.Any(n=>n.DistanceTo(p)<1) && p.Z<500 && !feet.Any(q=>q.DistanceTo(p)<1)) feet.Add(p); } }
 d.Enabled=false; d.Dispose(); var t=Transform.Translation(dx,0,0); for(int i=0;i<bars.Count;i++){ var l=bars[i]; l.Transform(t); bars[i]=l; } for(int i=0;i<feet.Count;i++){ var p=feet[i]; p.Transform(t); feet[i]=p; } return (bars,feet); }
float yy=0;
foreach(var (f,dx) in new[]{("friend-AP8-diagrid",0.0),("friend-16-diagrid",14000.0)}){
 var g=Geom(f,dx);
 var mat=Clone(oMat); var cs=Clone(oCs); var l2b=Clone(oL2B); var sup=Clone(oSup); var grav=Clone(oGrav); var ml=Clone(oML); var asm=Clone(oAsm); var an=Clone(oAn); var bf=Clone(oBF); var rf=Clone(oRF); var buck=Clone(oBuck); var th2=Clone(oTh2);
 #CHAIN
 SetV(In(th2,"Load Cases"),"G"); SetV(In(bf,"Load Case"),"G"); SetV(In(rf,"Load Case"),"G"); SetV(In(bf,"ts"),0.0,0.5,1.0); SetV(In(buck,"Number of Modes"),1);
 SetV(In(l2b,"Line"),g.bars.Cast<object>().ToArray()); SetV(In(sup,"Pos"),g.feet.Cast<object>().ToArray());
 SetV(In(ml,"Vec"),new Vector3d(0,0,-7)); SetV(In(ml,"Mesh"),Pyr(dx));
 var all=new List<IGH_Component>{mat,cs,l2b,sup,grav,ml,asm,an,bf,rf,buck,th2};
 float x=0; foreach(var c in all){ c.Attributes.Pivot=new System.Drawing.PointF(80+x,80+yy); x+=170; }
 keep.Add((f,asm,an,bf,rf,buck,all)); yy+=260;
}
src.Dispose();
