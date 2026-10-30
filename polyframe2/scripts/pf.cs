using Grasshopper;
var sb=new System.Text.StringBuilder();
sb.AppendLine("units "+__rhino_doc__.ModelUnitSystem+" tol "+__rhino_doc__.ModelAbsoluteTolerance);
foreach(var p in Instances.ComponentServer.ObjectProxies.Where(p=>p.Desc.Category=="PolyFrame"||p.Desc.Category.StartsWith("PolyFrame")).OrderBy(p=>p.Desc.SubCategory))
 sb.AppendLine(p.Desc.SubCategory+" | "+p.Desc.Name+" | "+p.Guid+" | obs="+p.Obsolete+" | "+p.Desc.Description.Replace("\n"," ").Substring(0,Math.Min(140,p.Desc.Description.Length)));
Console.WriteLine(sb.ToString());
