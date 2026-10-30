using Grasshopper;
var d=Instances.ActiveCanvas.Document; Console.WriteLine("canvas doc "+d?.FilePath+" modified "+d?.IsModified+" objs "+d?.ObjectCount+" | docs open "+Instances.DocumentServer.DocumentCount+" | rhino doc modified "+__rhino_doc__.Modified+" path "+__rhino_doc__.Path);
