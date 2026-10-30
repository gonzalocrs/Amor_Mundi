using Grasshopper; using Grasshopper.Kernel; using Rhino.Geometry;
var sb=new System.Text.StringBuilder();
var doc=Instances.ActiveCanvas.Document;
IGH_Component C(string nn)=>doc.Objects.OfType<IGH_Component>().FirstOrDefault(c=>c.NickName==nn);
List<object> D(IGH_Component c,string n)=> c.Params.Output.First(o=>o.Name==n).VolatileData.AllData(true).Select(g=>g.ScriptVariable()).ToList();
var ie=C("E_LO"); var F=D(ie,"Force").Select(x=>Convert.ToDouble(x)).ToList(); var X=D(ie,"External").Select(x=>Convert.ToInt32(x)).ToList(); var L=D(ie,"Line").Cast<Line>().ToList(); var ID=D(ie,"ID");
for(int i=0;i<F.Count;i++) if(X[i]==0 && (L[i].Length<100 || F[i]<0)) sb.AppendLine("id "+ID[i]+" len "+L[i].Length.ToString("0.###")+" F "+F[i].ToString("0")+" from "+L[i].From+" dir "+(L[i].To-L[i].From));
Console.WriteLine(sb.ToString());
