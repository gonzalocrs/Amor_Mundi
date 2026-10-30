import json,sys,urllib.request
# usage: mcp.py tool [script_file|json_args]
tool=sys.argv[1]; arg=sys.argv[2] if len(sys.argv)>2 else '{}'
if tool in('run_csharp','run_python'):
    args={'script':open(arg,encoding='utf-8').read()}
else: args=json.loads(arg)
port=sys.argv[3] if len(sys.argv)>3 else '10500'
req=urllib.request.Request(f'http://127.0.0.1:{port}/',data=json.dumps({'jsonrpc':'2.0','id':1,'method':'tools/call','params':{'name':tool,'arguments':args}}).encode(),headers={'Content-Type':'application/json'})
r=json.load(urllib.request.urlopen(req,timeout=float(sys.argv[4]) if len(sys.argv)>4 else 120))
sys.stdout.reconfigure(encoding='utf-8')
if 'error' in r: print('ERR',r['error'])
else:
    for c in r['result']['content']:
        if c['type']=='text': print(c['text'])
        else: print('[',c['type'],']')
