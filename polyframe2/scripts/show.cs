if(SHOW){ foreach(var o in doc.Objects.OfType<IGH_ActiveObject>()) if(o is IGH_PreviewObject po) po.Hidden=true;
var pA=Add("PFPipe"); W(vc,"PFoam",pA,"PFoam"); Num(pA,"MinR",30); Num(pA,"MaxR",90); ((IGH_PreviewObject)pA).Hidden=true;
var mA=Add("Move"); W(pA,"Pipe",mA,"Geometry"); var vx=(Param_Vector)In(mA,"Motion"); vx.PersistentData.Clear(); vx.PersistentData.Append(new GH_Vector(new Vector3d(-14000,0,0)));
var cA=Add("Custom Preview"); W(mA,"Geometry",cA,"Geometry"); W(pA,"Color",cA,"Material");
var pB=Add("PFPipe"); W(perp,"PFoam",pB,"PFoam"); Num(pB,"MinR",30); Num(pB,"MaxR",90); ((IGH_PreviewObject)pB).Hidden=true;
var cB=Add("Custom Preview"); W(pB,"Pipe",cB,"Geometry"); W(pB,"Color",cB,"Material");
var old=Instances.ActiveCanvas.Document; Instances.DocumentServer.AddDocument(doc); Instances.ActiveCanvas.Document=doc; if(old!=null){ old.Enabled=false; Instances.DocumentServer.RemoveDocument(old); old.Dispose(); }
doc.NewSolution(false); }
