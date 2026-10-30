using System.Reflection; using Grasshopper; using Grasshopper.Kernel; using Grasshopper.Kernel.Types; using Grasshopper.Kernel.Parameters;
var KA=AppDomain.CurrentDomain.GetAssemblies().First(a=>a.GetName().Name=="KarambaCommon");
var KG=AppDomain.CurrentDomain.GetAssemblies().First(a=>a.GetName().Name=="karamba");
Type KT(string n){ return KA.GetType(n)??KG.GetType(n)??throw new Exception("type "+n); }
var tP3=KT("Karamba.Geometry.Point3"); var tV3=KT("Karamba.Geometry.Vector3"); var tL3=KT("Karamba.Geometry.Line3");
object P3(double x,double y,double z)=>Activator.CreateInstance(tP3,x,y,z);
object V3(double x,double y,double z)=>Activator.CreateInstance(tV3,x,y,z);
object L3(object a,object b)=>Activator.CreateInstance(tL3,a,b);
System.Collections.IList NewList(Type t)=>(System.Collections.IList)Activator.CreateInstance(typeof(List<>).MakeGenericType(t));
var tk=Activator.CreateInstance(KT("KarambaCommon.Toolkit"));
object Fac(string n)=>tk.GetType().GetProperty(n).GetValue(tk);
// call: pick method by name + param count, fill missing optionals with Type.Missing / defaults
object Call(object target,string name,object[] args,out object[] all,int nParams=-1){
 var ms=target.GetType().GetMethods().Where(m=>m.Name==name && (nParams<0||m.GetParameters().Length==nParams)).ToList();
 foreach(var m in ms){ var ps=m.GetParameters(); if(ps.Length<args.Length) continue; bool ok=true; var full=new object[ps.Length];
   for(int i=0;i<ps.Length;i++){ if(i<args.Length){ var a=args[i]; if(a!=null && !ps[i].ParameterType.IsByRef && !ps[i].ParameterType.IsAssignableFrom(a.GetType())){ ok=false; break; } full[i]=a; } else if(ps[i].IsOut){ full[i]=null; } else if(ps[i].HasDefaultValue){ full[i]=ps[i].DefaultValue; } else { ok=false; break; } }
   if(!ok) continue; var r=m.Invoke(target,full); all=full; return r; }
 throw new Exception("no overload "+name+" for "+args.Length+" args: "+string.Join(" | ",ms.Select(m=>string.Join(",",m.GetParameters().Select(p=>p.ParameterType.Name)))));
}
var flow=Enum.Parse(KT("Karamba.Materials.FemMaterial+FlowHypothesis"),"rankine");
object[] tmp;
// material C30/37 cast (as in the 19 Oct roof model): E 3280 kN/cm2, G = E/2.4, gamma 24 kN/m3, ft 0.29, fc -2.0 kN/cm2
var mat=Call(Fac("Material"),"IsotropicMaterial",new object[]{"Concrete","C30/37 cast",3280.0,3280.0/2.4,3280.0/2.4,24.0,0.29,-2.0,flow,1e-5,null},out tmp,11);
var tCroSec=KT("Karamba.CrossSections.CroSec"); var tBE=KT("Karamba.Elements.BuilderElement"); var tSup=KT("Karamba.Supports.Support"); var tLoad=KT("Karamba.Loads.Load");
object Build(List<(double[] a,double[] b)> lines,List<double[]> sup,List<(double[] p,double kN)> loads,double hcm,double wcm,bool selfw,out string info,out double mass){
 var cs=Call(Fac("CroSec"),"Trapezoid",new object[]{hcm,wcm,wcm,mat},out tmp);
 var L=NewList(tL3); foreach(var l in lines) L.Add(L3(P3(l.a[0],l.a[1],l.a[2]),P3(l.b[0],l.b[1],l.b[2])));
 var ids=new List<string>{"rib"}; var css=NewList(tCroSec); css.Add(cs);
 var logger=Activator.CreateInstance(KT("Karamba.Utilities.MessageLogger"));
 object[] lt; var elems=Call(Fac("Part"),"LineToBeam",new object[]{L,ids,css,logger},out lt,12);
 var sups=NewList(tSup); var hinged=Fac("Support").GetType().GetProperty("SupportHingedConditions").GetValue(Fac("Support"));
 foreach(var s in sup) sups.Add(Call(Fac("Support"),"Support",new object[]{P3(s[0],s[1],s[2]),hinged},out tmp,3));
 var lds=NewList(tLoad); if(selfw) lds.Add(Call(Fac("Load"),"GravityLoad",new object[]{V3(0,0,-1),"LC0"},out tmp));
 foreach(var l in loads) lds.Add(Call(Fac("Load"),"PointLoad",new object[]{P3(l.p[0],l.p[1],l.p[2]),V3(0,0,-l.kN),V3(0,0,0),"LC0",false},out tmp,5));
 var elist=NewList(tBE); foreach(var e in (System.Collections.IEnumerable)elems) elist.Add(e);
 object[] at; var model=Call(Fac("Model"),"AssembleModel",new object[]{elist,sups,lds},out at,14);
 info=(string)at[3]; mass=(double)at[4]; return model;
}
object Analyze(object model,out double maxDisp,out string warn){ object[] a; var m=Call(Fac("Algorithms"),"AnalyzeThI",new object[]{model},out a); var md=(System.Collections.IEnumerable)a[1]; maxDisp=md.Cast<double>().Max(); warn=(string)a[4]; return m; }
IGH_Component KC(GH_Document d,string guid){ var o=(IGH_Component)Instances.ComponentServer.EmitObject(new Guid(guid)); o.CreateAttributes(); d.AddObject(o,false); return o; }
(GH_Document d, IGH_Param pm) ModelDoc(object model){ var d=new GH_Document(); var pm=(IGH_Param)Activator.CreateInstance(KG.GetType("Karamba.GHopper.Models.Param_Model")); pm.CreateAttributes(); d.AddObject(pm,false);
 var goo=Activator.CreateInstance(KG.GetType("Karamba.GHopper.Models.GH_Model"),model); var pd=pm.GetType().GetProperty("PersistentData").GetValue(pm); pd.GetType().GetMethod("Append",new[]{goo.GetType()}).Invoke(pd,new[]{goo}); return (d,pm); }
var lines=new List<(double[],double[])>{ (new double[]{0,0,0},new double[]{2.5,0,0}), (new double[]{2.5,0,0},new double[]{5,0,0}) };
var m=Build(lines,new List<double[]>{new double[]{0,0,0},new double[]{5,0,0}},new List<(double[],double)>{(new double[]{2.5,0,0},10.0)},25,15,false,out var info,out var mass);
var ma=Analyze(m,out var md,out var w);
Console.WriteLine("mass "+mass.ToString("0.0")+" kg (0.15x0.25x5 m x 2446 kg/m3 = "+(0.15*0.25*5*24/9.81*1000).ToString("0")+") | maxDisp "+md.ToString("0.00000")+" m (hand PL^3/48EI = 0.00407 m) | warn '"+w+"'");
var (d,pm)=ModelDoc(ma);
var bf=KC(d,"4f255ff1-ffed-4f54-99ab-f8f82c48a624"); bf.Params.Input[0].AddSource(pm);
var rf=KC(d,"4786a421-313c-4673-b8b0-20b59742a7f2"); rf.Params.Input[0].AddSource(pm);
d.Enabled=true; d.NewSolution(false,GH_SolutionMode.Silent);
foreach(var o in bf.Params.Output.Skip(1).Take(6)) Console.WriteLine("BF "+o.Name+": "+string.Join(" ",o.VolatileData.AllData(true).Take(12).Select(x=>x.ToString())));
foreach(var o in rf.Params.Output.Skip(1).Take(5)) Console.WriteLine("RF "+o.Name+": "+string.Join(" ",o.VolatileData.AllData(true).Take(6).Select(x=>x.ToString())));
Console.WriteLine("ts default: "+string.Join(",",bf.Params.Input[3].VolatileData.AllData(true))+" | msgs "+string.Join("|",bf.RuntimeMessages(GH_RuntimeMessageLevel.Warning).Concat(bf.RuntimeMessages(GH_RuntimeMessageLevel.Error))));
