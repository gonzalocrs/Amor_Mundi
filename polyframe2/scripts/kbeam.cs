// hand check: 5 m simply supported 15x25 cm beam, self-weight only (gamma 24): w=0.9 kN/m, M=2.81 kNm, delta=1.14 mm, R=2.25 kN, mass 459 kg
SetV(In(l2b,"Line"),new Line(new Point3d(0,0,0),new Point3d(2500,0,0)),new Line(new Point3d(2500,0,0),new Point3d(5000,0,0)));
SetV(In(sup,"Pos"),new Point3d(0,0,0),new Point3d(5000,0,0));
In(asm,"Load").RemoveAllSources(); In(asm,"Load").AddSource(Out(grav,"Load"));
doc.Enabled=true; doc.NewSolution(false,GH_SolutionMode.Silent);
foreach(var c in doc.Objects.OfType<IGH_Component>()) if(c.RuntimeMessageLevel!=GH_RuntimeMessageLevel.Blank) sb.AppendLine("msg "+c.NickName+": "+string.Join(" | ",c.RuntimeMessages(GH_RuntimeMessageLevel.Error).Concat(c.RuntimeMessages(GH_RuntimeMessageLevel.Warning))).Replace("\n"," ").Substring(0,Math.Min(200,string.Join(" | ",c.RuntimeMessages(GH_RuntimeMessageLevel.Error).Concat(c.RuntimeMessages(GH_RuntimeMessageLevel.Warning))).Length)));
sb.AppendLine("Assemble outputs: "+string.Join(" | ",asm.Params.Output.Skip(1).Select(o=>o.Name+"="+string.Join(",",o.VolatileData.AllData(true).Take(3)))));
sb.AppendLine("Analyse outputs: "+string.Join(" | ",an.Params.Output.Skip(1).Select(o=>o.Name+"="+string.Join(",",o.VolatileData.AllData(true).Take(3)))));
sb.AppendLine("My: "+string.Join(" ",Out(bf,"Bending moment My").VolatileData.AllData(true).Take(8))+" | Vz "+string.Join(" ",Out(bf,"Shear force Vz").VolatileData.AllData(true).Take(8)));
sb.AppendLine("Reactions: "+string.Join(" ",Out(rf,"Reaction Forces").VolatileData.AllData(true))+" | moments "+string.Join(" ",Out(rf,"Reaction Moments").VolatileData.AllData(true)));
sb.AppendLine("support settings (cloned): "+sup.Message);
sb.AppendLine(srcInfo);
Console.WriteLine(sb.ToString());
