#r "C:/Users/gonza/AppData/Roaming/McNeel/Rhinoceros/packages/8.0/Karamba3D/3.1.60921/net8.0-windows/KarambaCommon.dll"
#r "C:/Users/gonza/AppData/Roaming/McNeel/Rhinoceros/packages/8.0/Karamba3D/3.1.60921/net8.0-windows/Karamba.gha"
using Grasshopper; using Grasshopper.Kernel; using Grasshopper.Kernel.Types; using Grasshopper.Kernel.Parameters;
using Karamba.Geometry; using Karamba.Utilities; using KarambaCommon;
var k3d=new Toolkit();
var mat=k3d.Material.IsotropicMaterial("Concrete","C30/37 cast",3280,3280/2.4,3280/2.4,24,0.29,-2.0,Karamba.Materials.FemMaterial.FlowHypothesis.rankine,1e-5,null);
Karamba.Models.Model Build(List<Line3> lines,List<Point3> sup,List<(Point3 p,double kN)> loads,double h,double w,bool selfw,out string info,out double mass){
 var cs=k3d.CroSec.Trapezoid(h,w,w,mat);
 var log=new MessageLogger(); List<Karamba.Nodes.Point3> dummy=null;
 var elems=k3d.Part.LineToBeam(lines,new List<string>{"rib"},new List<Karamba.CrossSections.CroSec>{cs},log,out var outNodes);
 var sups=sup.Select(s=>k3d.Support.Support(s,k3d.Support.SupportHingedConditions)).ToList();
 var lds=new List<Karamba.Loads.Load>(); if(selfw) lds.Add(k3d.Load.GravityLoad(new Vector3(0,0,-1),"LC0"));
 foreach(var l in loads) lds.Add(k3d.Load.PointLoad(l.p,new Vector3(0,0,-l.kN),new Vector3(),"LC0"));
 var model=k3d.Model.AssembleModel(elems,sups,lds,out info,out mass,out var cog,out var msg,out var warn);
 return model;
}
IGH_Component KC(GH_Document d,string guid){ var o=(IGH_Component)Instances.ComponentServer.EmitObject(new Guid(guid)); o.CreateAttributes(); d.AddObject(o,false); return o; }
var lines=new List<Line3>{ new Line3(new Point3(0,0,0),new Point3(2.5,0,0)), new Line3(new Point3(2.5,0,0),new Point3(5,0,0)) };
var sup=new List<Point3>{new Point3(0,0,0),new Point3(5,0,0)};
var m=Build(lines,sup,new List<(Point3,double)>{(new Point3(2.5,0,0),10.0)},25,15,false,out var info,out var mass);
m=k3d.Algorithms.AnalyzeThI(m,out var maxD,out var gF,out var en,out var warn);
Console.WriteLine("mass "+mass.ToString("0.0")+" kg (expect 0.15*0.25*5*2400/... ~ "+(0.15*0.25*5*24/9.81*1000).ToString("0")+" kg via gamma 24) | maxDisp "+string.Join(",",maxD.Select(x=>x.ToString("0.00000")))+" (hand 0.00407 m) warn "+warn);
// beam forces via GH component
var d=new GH_Document(); var pm=new Karamba.GHopper.Models.Param_Model(); pm.CreateAttributes(); d.AddObject(pm,false); pm.PersistentData.Append(new Karamba.GHopper.Models.GH_Model(m));
var bf=KC(d,"4f255ff1-ffed-4f54-99ab-f8f82c48a624"); bf.Params.Input[0].AddSource(pm);
d.Enabled=true; d.NewSolution(false,GH_SolutionMode.Silent);
foreach(var o in bf.Params.Output.Skip(1)) Console.WriteLine(o.Name+": "+string.Join(" ",o.VolatileData.AllData(true).Take(12).Select(x=>x.ToString())));
Console.WriteLine("bf msgs: "+string.Join("|",bf.RuntimeMessages(GH_RuntimeMessageLevel.Warning).Concat(bf.RuntimeMessages(GH_RuntimeMessageLevel.Error))));
foreach(var i in bf.Params.Input) Console.WriteLine(" in "+i.Name+" data "+string.Join(",",i.VolatileData.AllData(true).Take(6)));
