foreach(var L in __rhino_doc__.Layers) if(L.Name.Contains("rror")){ var objs=__rhino_doc__.Objects.FindByLayer(L); Console.WriteLine(L.FullPath+" objs "+(objs?.Length??0));
 if(objs!=null){ foreach(var o in objs.Take(12)){ var bb=o.Geometry.GetBoundingBox(true); Console.WriteLine(" "+o.ObjectType+" "+bb.Min+" .. "+bb.Max); } foreach(var o in objs) __rhino_doc__.Objects.Delete(o,true);} }
Console.WriteLine("objs total "+__rhino_doc__.Objects.Count);
