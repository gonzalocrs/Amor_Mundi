using System.Reflection;
var asms=AppDomain.CurrentDomain.GetAssemblies().Where(a=>a.GetName().Name.StartsWith("Karamba")||a.GetName().Name.StartsWith("KarambaCommon")).ToList();
foreach(var a in asms) Console.WriteLine("asm "+a.GetName().Name+" "+a.GetName().Version);
var tk=asms.SelectMany(a=>{try{return a.GetTypes();}catch(ReflectionTypeLoadException e){return e.Types.Where(t=>t!=null);}}).FirstOrDefault(t=>t.FullName=="KarambaCommon.Toolkit");
Console.WriteLine("Toolkit: "+tk);
if(tk!=null){ foreach(var p in tk.GetProperties()) { Console.WriteLine(" prop "+p.Name+" : "+p.PropertyType.FullName);
  foreach(var m in p.PropertyType.GetMethods(BindingFlags.Public|BindingFlags.Instance|BindingFlags.DeclaredOnly)) Console.WriteLine("     "+m.Name+"("+string.Join(", ",m.GetParameters().Select(q=>q.ParameterType.Name+" "+q.Name+(q.IsOut?" [out]":"")+(q.HasDefaultValue?"="+q.DefaultValue:"")))+") -> "+m.ReturnType.Name); } }
