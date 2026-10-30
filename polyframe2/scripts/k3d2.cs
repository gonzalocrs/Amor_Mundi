using System.Reflection;
var asms=AppDomain.CurrentDomain.GetAssemblies().Where(a=>a.GetName().Name.StartsWith("Karamba")).ToList();
var types=asms.SelectMany(a=>{try{return a.GetTypes();}catch(ReflectionTypeLoadException e){return e.Types.Where(t=>t!=null);}}).ToList();
foreach(var n in new[]{"Line3","Point3","Vector3","MessageLogger","GH_Model","FlowHypothesis","Model","CroSec","BuildingElement","ModelBeam"}) foreach(var t in types.Where(t=>t.Name==n).Take(3)) Console.WriteLine(n+" -> "+t.FullName+" ["+t.Assembly.GetName().Name+"]");
foreach(var a in asms) Console.WriteLine(a.GetName().Name+" @ "+a.Location);
var gm=types.FirstOrDefault(t=>t.Name=="GH_Model"); if(gm!=null) foreach(var c in gm.GetConstructors()) Console.WriteLine("GH_Model ctor("+string.Join(",",c.GetParameters().Select(p=>p.ParameterType.Name))+")");
var fh=types.FirstOrDefault(t=>t.Name=="FlowHypothesis"); if(fh!=null) Console.WriteLine("FlowHypothesis: "+string.Join(",",Enum.GetNames(fh)));
var ml=types.FirstOrDefault(t=>t.Name=="MessageLogger"); if(ml!=null) foreach(var c in ml.GetConstructors()) Console.WriteLine("MessageLogger ctor("+string.Join(",",c.GetParameters().Select(p=>p.ParameterType.Name))+")");
