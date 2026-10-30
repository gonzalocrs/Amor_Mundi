var rd=Rhino.RhinoDoc.ActiveDoc; Console.WriteLine("rhino doc: "+(rd.Path??"(unsaved)")+" objs "+rd.Objects.Count);
var gh=Rhino.RhinoApp.GetPlugInObject("Grasshopper"); Console.WriteLine("gh plugin "+(gh!=null));
try{ Console.WriteLine("gh editor loaded "+Grasshopper.Instances.DocumentEditor!=null); foreach(var d in Grasshopper.Instances.DocumentServer) Console.WriteLine(" gh doc "+d.DisplayName+" "+d.FilePath); }catch(Exception e){ Console.WriteLine("gh not loaded: "+e.Message); }
