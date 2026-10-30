var f=Rhino.FileIO.File3dm.Read(@"C:\Users\gonza\Documents\GitHub\pyramid-roof\polyframe2\friend-all-iterations-clean-2026-10-29.3dm");
Console.WriteLine("objects "+f.Objects.Count+" layers: "+string.Join(" | ",f.AllLayers.Select(l=>l.Name+"="+f.Objects.Count(o=>o.Attributes.LayerIndex==l.Index))));
