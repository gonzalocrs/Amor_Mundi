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
