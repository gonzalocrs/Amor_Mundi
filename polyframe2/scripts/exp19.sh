#!/bin/bash
# exp19.sh R M D FE IT PIN8
S="C:/Users/gonza/AppData/Local/Temp/claude/C--Users-gonza-Documents-GitHub-pyramid-roof/88d2013e-3524-4014-9052-f727e6ca9a4a/scratchpad"
sed -e "s/__R__/$1/;s/__M__/$2/;s/__D__/$3/;s/__FE__/$4/;s/__IT__/$5/;s/__PIN8__/$6/;s/__Q__/${Q:-1}/;s/__SHOW__/${SHOW:-false}/;s/__TREE__/${TREE:-false}/;s/__NF__/${NF:-8}/;s/__STAG__/${STAG:-false}/;s/__DIA__/${DIA:-false}/;s/__DIA2__/${DIA2:-false}/;s/__R0__/${R0:-400}/;s/__ZN__/${ZN:-new int[]{64,32,16}}/;s/__ZR__/${ZR:-new double[]{840,870,930}}/" "$S/b19.cs" > "$S/b19a.cs"
python "$S/inc.py" "$S" b19a; "$S/run.sh" "$S/b19ax.cs" 120
