using Grasshopper; using Grasshopper.Kernel; using Rhino.Geometry;
IGH_Component Mk(GH_Document d,string name){ var p=Instances.ComponentServer.ObjectProxies.First(q=>q.Desc.Name==name && !q.Obsolete && typeof(IGH_Component).IsAssignableFrom(q.Type)); var o=(IGH_Component)p.CreateInstance(); o.CreateAttributes(); d.AddObject(o,false); return o; }
var io=new GH_DocumentIO(); io.Open(@"C:\Users\gonza\Documents\GitHub\pyramid-roof\polyframe2\friend-12-feet-2m-corners-opentop.gh"); var d=io.Document; d.Enabled=true;
var perp=d.Objects.OfType<IGH_Component>().First(c=>c.Name=="PFPerp");
var ex=Mk(d,"Explode PFoam"); ex.Params.Input[0].AddSource(perp.Params.Output[0]); var ie=Mk(d,"Inspect PFEdge"); ie.Params.Input[0].AddSource(ex.Params.Output[1]);
d.NewSolution(false,GH_SolutionMode.Silent);
var L=ie.Params.Output.First(o=>o.Name=="Line").VolatileData.AllData(true).Select(x=>(Line)x.ScriptVariable()).ToList(); var X=ie.Params.Output.First(o=>o.Name=="External").VolatileData.AllData(true).Select(x=>Convert.ToInt32(x.ScriptVariable())).ToList();
d.Enabled=false; d.Dispose();
var nodes=new List<Point3d>(); int Id(Point3d p){ for(int i=0;i<nodes.Count;i++) if(nodes[i].DistanceTo(p)<1) return i; nodes.Add(p); return nodes.Count-1; }
var bars=new List<(int a,int b)>(); var seen=new HashSet<(int,int)>(); for(int i=0;i<L.Count;i++) if(X[i]==0){ int a=Id(L[i].From), b=Id(L[i].To); if(a==b) continue; var k=(Math.Min(a,b),Math.Max(a,b)); if(seen.Add(k)) bars.Add(k); }
double zmin=nodes.Min(p=>p.Z);
// where are the steep bars
var groups=new Dictionary<string,List<string>>();
foreach(var bb in bars){ var p=nodes[bb.a]; var q=nodes[bb.b]; var v=q-p; double ang=Math.Atan2(Math.Sqrt(v.X*v.X+v.Y*v.Y),Math.Abs(v.Z))*180/Math.PI; string band= ang<=45?"<=45": ang<=60?"45-60": ang<=80?"60-80":">80"; var m=(p+q)/2; if(!groups.ContainsKey(band)) groups[band]=new List<string>(); groups[band].Add("z"+((m.Z-zmin)/1000).ToString("0.0")+"/r"+(Math.Sqrt(m.X*m.X+m.Y*m.Y)/1000).ToString("0.0")+"/L"+(v.Length/1000).ToString("0.00")); }
foreach(var g in groups){ Console.WriteLine(g.Key+": "+g.Value.Count+"  e.g. "+string.Join(" ",g.Value.Distinct().Take(8))); }
// print model 1:50, mm
double S=1.0/50, R=2.0, RN=2.6; var xf=Transform.Scale(Point3d.Origin,S)*Transform.Translation(0,0,-zmin);
var meshes=new List<Mesh>(); var mp=MeshingParameters.Default;
foreach(var bb in bars){ var a=nodes[bb.a]; var b=nodes[bb.b]; a.Transform(xf); b.Transform(xf); var c=new Cylinder(new Circle(new Plane(a,b-a),R),a.DistanceTo(b)); var m=Mesh.CreateFromCylinder(c,1,24); meshes.Add(m); }
foreach(var n in nodes){ var p=n; p.Transform(xf); meshes.Add(Mesh.CreateFromSphere(new Sphere(p,RN),24,16)); }
// foot pads 10 mm dia, 3 mm thick, bed at z=-3 -> shift up 3
foreach(var n in nodes.Where(n=>n.Z<zmin+50)){ var p=n; p.Transform(xf); var c=new Cylinder(new Circle(new Plane(new Point3d(p.X,p.Y,-3),Vector3d.ZAxis),5),3); meshes.Add(Mesh.CreateFromCylinder(c,1,32)); }
var up=Transform.Translation(0,0,3); int open=0; var all=new Mesh(); foreach(var m in meshes){ m.Transform(up); if(!m.IsClosed) open++; m.Normals.ComputeNormals(); all.Append(m); }
var bbx=all.GetBoundingBox(true); Console.WriteLine("pieces "+meshes.Count+" not closed "+open+" | bbox mm "+bbx.Min+" .. "+bbx.Max+" | faces "+all.Faces.Count);
var rd=__rhino_doc__; var old=rd.Objects.Find(new Guid("b126112b-7142-4a88-a5e9-cbada7031e83")); if(old!=null) rd.Objects.Delete(old,true);
// binary STL
all.Faces.ConvertQuadsToTriangles(); all.FaceNormals.ComputeFaceNormals();
var path=@"C:\Users\gonza\Documents\GitHub\pyramid-roof\polyframe2\print\friend-15-1to50.stl";
using(var bw=new System.IO.BinaryWriter(System.IO.File.Create(path))){ bw.Write(new byte[80]); bw.Write((uint)all.Faces.Count); for(int i=0;i<all.Faces.Count;i++){ var f=all.Faces[i]; var nn=all.FaceNormals[i]; bw.Write(nn.X); bw.Write(nn.Y); bw.Write(nn.Z); foreach(var vi in new[]{f.A,f.B,f.C}){ var v=all.Vertices[vi]; bw.Write(v.X); bw.Write(v.Y); bw.Write(v.Z);} bw.Write((ushort)0);} }
Console.WriteLine("stl "+new System.IO.FileInfo(path).Length+" bytes");
