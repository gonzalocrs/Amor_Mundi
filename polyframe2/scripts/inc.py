import sys;S=sys.argv[1]
b=open(S+'/'+sys.argv[2]+'.cs').read()
for k,f in [('#gen','gen'),('#show','show'),('#force12','force12'),('#form12','form12'),('#force8','force8'),('#form8','form8'),('#include','force'),('#form','form'),('#report2','report2'),('#report','report')]: b=b.replace(k,open(S+'/'+f+'.cs').read())
open(S+'/'+sys.argv[2]+'x.cs','w').write(b)
