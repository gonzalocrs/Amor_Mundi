#!/bin/bash
# exp3.sh N D IT ML COEF
S="C:/Users/gonza/AppData/Local/Temp/claude/C--Users-gonza-Documents-GitHub-pyramid-roof/88d2013e-3524-4014-9052-f727e6ca9a4a/scratchpad"
sed -e "s/__N__/$1/;s/__D__/$2/;s/__IT__/$3/;s/__ML__/$4/;s/__COEF__/${5:-1}/" "$S/b12.cs" > "$S/b12a.cs"
python "$S/inc.py" "$S" b12a; "$S/run.sh" "$S/b12ax.cs" ${6:-60}
sed 's/var TAGS=new\[\]{"VC","LO"};/var TAGS=new[]{"PERP"};/' "$S/readx.cs" > "$S/readp.cs"
python "$S/mcp.py" run_csharp "$S/readp.cs" 10512 30 > "$S/_o.txt"; python "$S/out.py" "$S/_o.txt" | grep -E "^(PERP|msg)"
