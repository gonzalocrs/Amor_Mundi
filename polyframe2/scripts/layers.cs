var rd=__rhino_doc__; foreach(var L in rd.Layers){ var n=rd.Objects.FindByLayer(L)?.Length??0; if(n>0) Console.WriteLine(L.Index+" '"+L.FullPath+"' "+n); }
