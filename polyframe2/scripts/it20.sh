#!/bin/bash
S="C:/Users/gonza/AppData/Local/Temp/claude/C--Users-gonza-Documents-GitHub-pyramid-roof/88d2013e-3524-4014-9052-f727e6ca9a4a/scratchpad"
sed -e "s/__FR__/new double[]{$1}/;s/__DEP__/$2/;s/MM=3;/MM=${MM:-3};/;s/__PTS__/${PTS:-false}/" "$S/even_iter20.cs" > "$S/e20_a.cs"
python "$S/inc.py" "$S" e20_a; "$S/run.sh" "$S/e20_ax.cs" 60
