var rd=Rhino.RhinoDoc.ActiveDoc; Console.WriteLine("units "+rd.ModelUnitSystem);
var bb=new Rhino.Geometry.BoundingBox(-21000,-8000,0,8000,8000,10000);
foreach(var v in rd.Views){ v.ActiveViewport.ZoomBoundingBox(bb); } rd.Views.Redraw(); Console.WriteLine("zoomed");
