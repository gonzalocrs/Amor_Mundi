using Grasshopper; using Grasshopper.Kernel; using System.Reflection;
var p=Instances.ComponentServer.ObjectProxies.Where(x=>x.Desc.Name.Contains("C#")&&!x.Obsolete).Select(x=>x.Desc.Name+" | "+x.Guid+" | "+x.Type.FullName).ToList();
Console.WriteLine(string.Join("\n",p));
var t=Instances.ComponentServer.ObjectProxies.First(x=>x.Guid==new Guid("a9a8ebd2-fff5-4c44-a8f5-739736d129ba")).Type;
foreach(var m in t.GetProperties(BindingFlags.Instance|BindingFlags.Public)) Console.WriteLine(" p "+m.Name+":"+m.PropertyType.Name);
foreach(var m in t.GetMethods(BindingFlags.Instance|BindingFlags.Public|BindingFlags.DeclaredOnly)) Console.WriteLine(" m "+m.Name);
