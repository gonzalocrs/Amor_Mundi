using Grasshopper.Kernel.Types; using Grasshopper; using Grasshopper.Kernel; using Grasshopper.Kernel.Special; using Rhino.Geometry;
var d=Instances.ActiveCanvas.Document;
foreach(var o in d.Objects){
 string s=o.Name+" ["+o.NickName+"] "+o.InstanceGuid.ToString().Substring(0,8);
 if(o is GH_NumberSlider sl) s+=" val="+sl.CurrentValue;
 if(o is GH_Panel p) s+=" text='"+p.UserText.Replace("\r","").Replace("\n","|")+"'";
 if(o is IGH_Param pr && pr.SourceCount>0) s+=" <- "+string.Join(",",pr.Sources.Select(x=>x.Attributes.GetTopLevel.DocObject.Name));
 if(o is IGH_Component c){ s+=" IN "+string.Join("; ",c.Params.Input.Select(i=>i.Name+(i.SourceCount>0?"<-"+string.Join("/",i.Sources.Select(x=>x.Attributes.GetTopLevel.DocObject.Name+"."+x.NickName)):"")+(i.DataMapping!=GH_DataMapping.None?"("+i.DataMapping+")":""))); }
 Console.WriteLine(s);
}
var vc=d.Objects.OfType<IGH_Component>().First(c=>c.Name=="Algebraic Vertex Constraints");
Console.WriteLine("VC ids data: "+string.Join(",",vc.Params.Input[1].VolatileData.AllData(true)));
Console.WriteLine("VC pts: "+string.Join(" ",vc.Params.Input[2].VolatileData.AllData(true)));
var ad=d.Objects.OfType<IGH_Component>().First(c=>c.Name=="Algebraic Dual");
var sn=d.Objects.OfType<IGH_Component>().First(c=>c.Name=="Scale NU");
var bb=BoundingBox.Empty; foreach(var g in sn.Params.Output[0].VolatileData.AllData(true)) bb.Union(((GH_Brep)g).Value.GetBoundingBox(true)); Console.WriteLine("force bbox "+bb.Min+" .. "+bb.Max);
