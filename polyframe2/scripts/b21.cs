GH_Document cur2=null;
#gen
var g=GenTree(500,200,1);
// test PFBuild on subsets: by triangle type index within sector (9 types + 8 fan) 
int per=9+8;
foreach(var keep in new[]{"fan","fan+W","fan+W+Z","fan+W+Z+Y","all-but-X","all"}){
 var docT=new GH_Document(); cur2=docT;
 var sel=new List<Brep>();
 for(int i=0;i<g.tets.Count;i++){ int t=i%per; string ty= t==0?"foot": t==1?"X": t==2?"Y": (t==3||t==4)?"Z": (t>=5&&t<=8)?"W":"fan";
   bool k= keep=="all" || (keep=="all-but-X" && ty!="X") || (keep.Contains(ty) && !(keep=="fan" && ty!="fan"));
   if(keep=="fan+W") k= ty=="fan"||ty=="W"; if(keep=="fan+W+Z") k= ty=="fan"||ty=="W"||ty=="Z"; if(keep=="fan+W+Z+Y") k= ty=="fan"||ty=="W"||ty=="Z"||ty=="Y"; if(keep=="fan") k= ty=="fan";
   if(k) sel.Add(g.tets[i]); }
 var bp=new Param_Brep(); bp.CreateAttributes(); docT.AddObject(bp,false); foreach(var t in sel) bp.PersistentData.Append(new GH_Brep(t));
 var bld=(IGH_Component)Instances.ComponentServer.EmitObject(new Guid("e99d404e-47c7-4572-ad31-9463a4abe4af")); bld.CreateAttributes(); docT.AddObject(bld,false); bld.Params.Input[0].AddSource(bp); ((Param_Number)bld.Params.Input[1]).PersistentData.Append(new GH_Number(0.1)); ((Param_Number)bld.Params.Input[2]).PersistentData.Append(new GH_Number(0.1));
 docT.Enabled=true; docT.NewSolution(false,GH_SolutionMode.Silent);
 sb.AppendLine(keep+" n="+sel.Count+" : "+bld.RuntimeMessageLevel+" "+string.Join("|",bld.RuntimeMessages(GH_RuntimeMessageLevel.Error)).Replace("\n"," ").Substring(0,Math.Min(120,string.Join("|",bld.RuntimeMessages(GH_RuntimeMessageLevel.Error)).Length)));
}
Console.WriteLine(sb.ToString());
