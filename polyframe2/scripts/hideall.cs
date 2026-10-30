var d=Rhino.RhinoDoc.ActiveDoc; int n=0; foreach(var o in d.Objects.Where(o=>o.Visible).ToList()){ d.Objects.Hide(o.Id,true); n++; } d.Views.Redraw(); Console.WriteLine("hidden "+n);
