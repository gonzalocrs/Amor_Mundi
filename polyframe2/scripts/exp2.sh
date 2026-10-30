#!/bin/bash
# exp2.sh N D MIN MAX SUPT wait
S="C:/Users/gonza/AppData/Local/Temp/claude/C--Users-gonza-Documents-GitHub-pyramid-roof/88d2013e-3524-4014-9052-f727e6ca9a4a/scratchpad"
sed -e "s/__N__/$1/;s/__D__/$2/;s/__MIN__/$3/;s/__MAX__/$4/;s/__SUPT__/$5/;s/__VS__/${VS:-1}/;s/__ADS__/${ADS:-1}/" "$S/b11.cs" > "$S/b11a.cs"
python "$S/inc.py" "$S" b11a; "$S/run.sh" "$S/b11ax.cs" 60
sleep ${6:-3}
python "$S/mcp.py" run_csharp "$S/readx.cs" 10512 30 > "$S/_o.txt"; python "$S/out.py" "$S/_o.txt" | grep -E "^(VC|LO|msg|solved)"
