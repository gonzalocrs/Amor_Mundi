#!/bin/bash
S="C:/Users/gonza/AppData/Local/Temp/claude/C--Users-gonza-Documents-GitHub-pyramid-roof/88d2013e-3524-4014-9052-f727e6ca9a4a/scratchpad"
sed -e "s/__FR__/new double[]{$1}/;s/__DEP__/$2/;s/MM=3;/MM=${MM:-3};/;s/__PTS__/${PTS:-false}/" "$S/even_iter12n2.cs" > "$S/e12n_a.cs"
python "$S/inc.py" "$S" e12n_a; "$S/run.sh" "$S/e12n_ax.cs" 60
