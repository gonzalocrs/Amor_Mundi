import json,sys
sys.stdout.reconfigure(encoding='utf-8')
t=open(sys.argv[1],encoding='utf-8').read()
i=t.find('{"error')
s=json.loads(t[i:t.rfind('}')+1])['message'] if i>=0 else t
s=s.split('content from: "C:')[0]
print('\n'.join(l for l in s.splitlines() if l.strip()))
