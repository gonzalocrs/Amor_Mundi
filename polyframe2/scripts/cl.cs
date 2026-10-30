using Grasshopper; using Grasshopper.Kernel; using System.Reflection;
var sb=new System.Text.StringBuilder();
foreach(var t in new[]{typeof(Grasshopper.Kernel.Special.GH_Cluster), typeof(Grasshopper.Kernel.Special.GH_ClusterInputHook), typeof(Grasshopper.Kernel.Special.GH_ClusterOutputHook)}){
 sb.AppendLine("## "+t.FullName);
 foreach(var m in t.GetMethods(BindingFlags.Instance|BindingFlags.Public|BindingFlags.Static|BindingFlags.DeclaredOnly)) sb.AppendLine("  m "+m.Name+"("+string.Join(", ",m.GetParameters().Select(p=>p.ParameterType.Name+" "+p.Name))+")");
 foreach(var p in t.GetProperties(BindingFlags.Instance|BindingFlags.Public|BindingFlags.DeclaredOnly)) sb.AppendLine("  p "+p.Name+" : "+p.PropertyType.Name);
}
Console.WriteLine(sb.ToString());
