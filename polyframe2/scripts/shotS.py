import json,sys,urllib.request,base64
from PIL import Image
S,R,name=sys.argv[1:4]
def call(args):
    req=urllib.request.Request('http://127.0.0.1:10512/',data=json.dumps({'jsonrpc':'2.0','id':1,'method':'tools/call','params':{'name':'get_viewport_image','arguments':args}}).encode(),headers={'Content-Type':'application/json'})
    r=json.load(urllib.request.urlopen(req,timeout=60))
    for c in r['result']['content']:
        if c['type']=='image': return Image.open(__import__('io').BytesIO(base64.b64decode(c['data'])))
bb=dict(boxMin={'x':-8000,'y':-8000,'z':0},boxMax={'x':8000,'y':8000,'z':10000})
ims=[call(dict(width=1000,height=600,view='perspective',displayMode='Shaded',**bb)),call(dict(width=1000,height=400,view='front',displayMode='Shaded',**bb)),call(dict(width=1000,height=480,view='top',displayMode='Shaded',**bb))]
w=max(i.width for i in ims); h=sum(i.height for i in ims); im=Image.new('RGB',(w,h),(155,160,168)); y=0
for i in ims: im.paste(i,(0,y)); y+=i.height
im.save(R+'/'+name+'.png'); print('png ok')
