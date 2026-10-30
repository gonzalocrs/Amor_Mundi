#!/bin/bash
S="C:/Users/gonza/AppData/Local/Temp/claude/C--Users-gonza-Documents-GitHub-pyramid-roof/88d2013e-3524-4014-9052-f727e6ca9a4a/scratchpad"
D_PAT='new[]{true,false}'; P="${PAT:-$D_PAT}"; RT="${ROT:--157.5}"
python - "$S" "$1" "$2" "$RT" "$P" "${B:-b15}" <<'PY'
import sys;S,n,d,r,p,b=sys.argv[1:7]
t=open(S+'/'+b+'.cs').read().replace('__N__',n).replace('__D__',d).replace('__ROT__',r).replace('__PAT__',p)
for k,v in (sys.argv[7:] and []): pass
import os
for kv in os.environ.get('EXTRA','').split(';'):
    if '=' in kv: k,v=kv.split('=',1); t=t.replace(k,v)
open(S+'/'+b+'a.cs','w').write(t)
PY
B2="${B:-b15}"; python "$S/inc.py" "$S" ${B2}a; "$S/run.sh" "$S/${B2}ax.cs" ${T:-60}
