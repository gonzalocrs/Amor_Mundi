#!/bin/bash
# run.sh body.cs [timeout]
S="C:/Users/gonza/AppData/Local/Temp/claude/C--Users-gonza-Documents-GitHub-pyramid-roof/88d2013e-3524-4014-9052-f727e6ca9a4a/scratchpad"
cat "$S/pre.cs" "$1" > "$S/_full.cs"
python "$S/mcp.py" run_csharp "$S/_full.cs" ${PORT:-10512} ${2:-60} > "$S/_out.txt" 2>&1
python "$S/out.py" "$S/_out.txt"
