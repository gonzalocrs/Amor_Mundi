var rd=__rhino_doc__; foreach(var l in rd.Layers.Where(l=>!l.IsDeleted)) { int n=rd.Objects.FindByLayer(l)?.Length??0; if(n>0) Console.WriteLine(l.Name+" "+n+(l.IsVisible?"":" HIDDEN")); }
