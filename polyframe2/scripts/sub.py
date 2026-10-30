import sys
src,dst,key,val=sys.argv[1:5]
open(dst,'w').write(open(src).read().replace(key,val.replace('/',chr(92))))
