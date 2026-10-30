#!/bin/bash
# exp.sh N D MIN MAX TOL SRC MU wait
S="C:/Users/gonza/AppData/Local/Temp/claude/C--Users-gonza-Documents-GitHub-pyramid-roof/88d2013e-3524-4014-9052-f727e6ca9a4a/scratchpad"
sed -e "s/__N__/$1/;s/__D__/$2/;s/__MIN__/$3/;s/__MAX__/$4/;s/__TOL__/$5/;s/__SRC__/$6/;s/__MU__/$7/;s/__VS__/${VS:-1}/;s/__SUP__/${SUP:-{5,45,43,6\}}/;s/__CP__/${CP:-new[]{new Point3d(-HX,-HY,0),new Point3d(HX,-HY,0),new Point3d(HX,HY,0),new Point3d(-HX,HY,0)\}}/;s/__HX__/${HX:-5000}/;s/__HY__/${HY:-5000}/" "$S/b10.cs" > "$S/b10a.cs"
python "$S/inc.py" "$S" b10a; "$S/run.sh" "$S/b10ax.cs" 60
sleep ${8:-4}
python "$S/mcp.py" run_csharp "$S/readx.cs" 10512 30 > "$S/_o.txt"; python "$S/out.py" "$S/_o.txt"
