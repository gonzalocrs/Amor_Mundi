import json,sys,urllib.request,base64
S=sys.argv[1]; tag=sys.argv[2]; port=sys.argv[3] if len(sys.argv)>3 else '10512'
def call(name,args):
    req=urllib.request.Request(f'http://127.0.0.1:{port}/',data=json.dumps({'jsonrpc':'2.0','id':1,'method':'tools/call','params':{'name':name,'arguments':args}}).encode(),headers={'Content-Type':'application/json'})
    return json.load(urllib.request.urlopen(req,timeout=60))
bb={'boxMin':{'x':-6000,'y':-6000,'z':0},'boxMax':{'x':6000,'y':6000,'z':7000}}
for nm,args in [('persp',dict(width=900,height=600,view='perspective',displayMode='Shaded',**bb)),('top',dict(width=600,height=600,view='top',displayMode='Wireframe',**bb))]:
    r=call('get_viewport_image',args)
    for c in r['result']['content']:
        if c['type']=='image': open(f'{S}/{tag}_{nm}.jpg','wb').write(base64.b64decode(c['data']))
