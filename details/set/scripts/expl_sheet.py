import io, json, math, pypdf, sys
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm
F="/usr/share/fonts/truetype/liberation/LiberationSans-"
for n,f in (("A","Regular"),("AB","Bold"),("AI","Italic")): pdfmetrics.registerFont(TTFont(n,F+f+".ttf"))
SCR="/tmp/claude-0/-home-claude/0f8208d9-0bf5-5d45-9dcd-a2d33e7bf201/scratchpad/"
EX=SCR+"artifact-files/fe341845-2c28-4311-88ab-99449afccf2c/drawings-2026-11-23/exploded/"
Y=lambda y: H-y

import sys
ROOF=sys.argv[1]; OUT=sys.argv[2]
R={"15x10":dict(json=SCR+"expl/formwork15v5.json",scale=150,title="15 X 10",split="whole courses",
     crown=("+11.44 TO +11.90","compression up to 15 kN (17 %)"),courses="18 COURSES + TOP COURSE, 422 PIECES",rib="worst bottom ribs 76 % used",
     ring="111 kN tension under typhoon",cols=("20 cast columns 36 x 36","28 % used"),foot=("1.20 m wide","108 kPa on the soil, tipping 1.70, sliding 2.04"),
     colsec=0.36,ribs=((280,220),(220,160),(180,120)),fw=1.2,blocks="2.36 x 2.03",n=dict(foot="strip + 4 blocks",col="20",rib="499 m",pcs="422 pieces",cr="11 pieces")),
   "10x10":dict(json=SCR+"expl/formwork10.json",scale=100,title="10 X 10",split="whole courses",
     crown=("+7.33 TO +7.79","compression up to 16 kN (12 %)"),courses="10 COURSES + TOP COURSE, 205 PIECES",rib="worst bottom ribs 60 % used",
     ring="54 kN tension under typhoon",cols=("16 cast columns 30 x 30","24 % used"),foot=("0.85 m wide","101 kPa on the soil, tipping 1.68, sliding 2.99"),
     colsec=0.30,ribs=((240,180),(200,140),(180,120)),fw=0.85,blocks="1.73 x 1.73",n=dict(foot="strip + 4 blocks",col="16",rib="288 m",pcs="205 pieces",cr="13 pieces"))}[ROOF]
D=json.load(open(EX+"elements-data.json"))[ROOF]
base=pypdf.PdfReader(SCR+"final-S101-S108.pdf").pages[2]
W=float(base.mediabox.width); H=float(base.mediabox.height)
b=io.BytesIO(); c=canvas.Canvas(b,pagesize=(W,H))
def txt(x,y,s,f="A",sz=6.8,anchor="l"):
    c.setFont(f,sz); (c.drawString if anchor=="l" else c.drawRightString if anchor=="r" else c.drawCentredString)(x,Y(y),s)
c.setFillColorRGB(1,1,1); c.rect(33,Y(1157),1402,1124,stroke=0,fill=1); c.rect(511.6*mm,(420-323.0)*mm,67.8*mm,33*mm,stroke=0,fill=1)
c.setFillColorRGB(0,0,0); c.setFont("A",17)
c.drawCentredString(546.85*mm,(420-303.5)*mm,"EXPLODED AXON"); c.drawCentredString(546.85*mm,(420-311.5)*mm,R["title"].replace(" X "," x ")+" ROOF")
txt(70,92,R["title"]+" STEPPED ROOF: EVERY ELEMENT, EXPLODED","AB",11.5)
txt(70,108,"Taken apart from the Rhino model, bottom to top: footing, columns, base ring step, rib rebar, printed formwork (each piece printed in one go with its rib tube), crown ring.",sz=6.8)
SC=R["scale"]; s=1000/SC*mm
items=json.load(open(R["json"]))["items"]
GRP=lambda ly: ly.split("/")[0]
style={"printed formwork":(0.16,0),"rib rebar":(0.22,0),"footing":(0.4,0),"columns":(0.4,0),"base ring step":(0.4,0),"crown ring":(0.4,0)}
xs=[p[0] for i in items for p in i["pts"]]; ys=[p[1] for i in items for p in i["pts"]]
x0m,x1m,y0m,y1m=min(xs),max(xs),min(ys),max(ys)
OX=95-x0m*s; OY=Y(1065)-y0m*s
P=lambda q:(OX+q[0]*s, OY+q[1]*s)
c.setLineCap(1); c.setLineJoin(1)
for i in items:
    lw,g=style.get(GRP(i["layer"]),(0.2,0)); c.setLineWidth(lw); c.setStrokeColorRGB(g,g,g)
    pts=[P(q) for q in i["pts"]]
    if len(pts)<2: continue
    pa=c.beginPath(); pa.moveTo(*pts[0])
    for q in pts[1:]: pa.lineTo(*q)
    if i["closed"]: pa.close()
    c.drawPath(pa,stroke=1,fill=0)
LAB=[("crown ring","CROWN RING "+R["crown"][0],["cast ring 25 x 25 in the printed top-course U formwork;","closes the opening, "+R["crown"][1]]),
     ("printed formwork","PRINTED FORMWORK: "+R["courses"],["each piece printed in one go with its rib tube and growth band,","3 cm walls; "+R["split"]+", courses lifted 1.2 m apart:","through the gaps the room faces show the rib tube channels"]),
     ("rib rebar","RIB REBAR",["bars laid in the tube channels, continuous from the base ring","to the crown ring; the cores are cast in one pour; "+R["rib"]]),
     ("base ring step","BASE RING STEP +2.00 TO +2.40",["cast ring 40 x 40 in a printed U formwork; ties the four","sides at the eave, "+R["ring"]]),
     ("columns","COLUMNS ±0.00 TO +2.00",[R["cols"][0]+", centred under the base ring;",R["cols"][1]]),
     ("footing","RECTANGULAR STRIP FOOTING -0.80 TO -0.30",[R["foot"][0]+", straight trenches, square corner blocks;",R["foot"][1]])]
LX=OX+x1m*s+70; prev=None
for key,t,lines in LAB:
    gi=[i for i in items if GRP(i["layer"])==key]
    if key=="columns":
        its=[i for i in gi if len(i["pts"])>1 and max(q[0] for q in i["pts"])<x1m-1.5]
        it=max(its,key=lambda i:sum(q[0] for q in i["pts"])/len(i["pts"]))
        m=(sum(q[0] for q in it["pts"])/len(it["pts"]), sum(q[1] for q in it["pts"])/len(it["pts"]))
    else: m=max((q for i in gi for q in i["pts"]),key=lambda q:q[0])
    ax,ay=P(m); ly=min(ay,(prev-52) if prev is not None else ay); prev=ly
    c.setLineWidth(0.35); c.setStrokeColorRGB(0,0,0); pa=c.beginPath(); pa.moveTo(ax,ay); pa.lineTo(LX-30,ly); pa.lineTo(LX-6,ly); c.drawPath(pa,stroke=1,fill=0); c.circle(ax,ay,1.3,stroke=0,fill=1)
    c.setFont("AB",8.5); c.drawString(LX,ly+1.5,t); c.setFont("A",6.8)
    for k,l in enumerate(lines): c.drawString(LX,ly-9-k*8.5,l)
txt(70,1110,"EXPLODED AXONOMETRIC OF THE %s FROM THE SOUTH-WEST 1:%d (%s, COURSES LIFTED 1.2 M, PIECES PULLED 0.15 M OUT)"%(R["title"],SC,R["split"].upper()),"AB",6.8)
S10=100*mm; RX=905
txt(RX,140,"TYPICAL SECTIONS 1:10","AB",8.5)
def hatch(path_fn, angles, step=4.0, lw=0.3):
    c.saveState(); pa=c.beginPath(); path_fn(pa); c.clipPath(pa,stroke=0,fill=0)
    c.setLineWidth(lw)
    for a in angles:
        ca,sa=math.cos(math.radians(a)),math.sin(math.radians(a))
        for k in range(-200,200):
            o=k*step; cx,cy=o*-sa,o*ca
            c.line(cx-2000*ca+1000,cy-2000*sa+600,cx+2000*ca+1000,cy+2000*sa+600)
    c.restoreState()
def rectp(x,y,w,h): return lambda pa: pa.rect(x,y,w,h)
def box(x,y,w,h,lw=0.6): c.setLineWidth(lw); c.rect(x,y,w,h,stroke=1,fill=0)
def ring_sec(cx,ytop,cast,wall):   # cast square in printed U (open top)
    o=cast+2*wall; x=cx-o*S10/2; yb=Y(ytop)-(cast+wall)*S10
    # printed U
    def U(pa):
        pa.moveTo(x,yb); pa.lineTo(x+o*S10,yb); pa.lineTo(x+o*S10,yb+(cast+wall)*S10); pa.lineTo(x+(o-wall)*S10,yb+(cast+wall)*S10)
        pa.lineTo(x+(o-wall)*S10,yb+wall*S10); pa.lineTo(x+wall*S10,yb+wall*S10); pa.lineTo(x+wall*S10,yb+(cast+wall)*S10); pa.lineTo(x,yb+(cast+wall)*S10); pa.close()
    hatch(U,[45],2.2,0.25); c.setLineWidth(0.6); pa=c.beginPath(); U(pa); c.drawPath(pa,stroke=1,fill=0)
    cx0=x+wall*S10; cy0=yb+wall*S10
    hatch(rectp(cx0,cy0,cast*S10,cast*S10),[45,-45],4.0,0.25); box(cx0,cy0,cast*S10,cast*S10)
    return yb
def col_sec(cx,ytop,a):
    x=cx-a*S10/2; yb=Y(ytop)-a*S10
    hatch(rectp(x,yb,a*S10,a*S10),[45,-45],4.0,0.25); box(x,yb,a*S10,a*S10); return yb
def rib_sec(cx,ytop,tube,core):
    r=tube/2*S10; cy=Y(ytop)-r
    def ann(pa): pa.circle(cx,cy,r); pa.circle(cx,cy,core/2*S10)
    c.saveState(); pa=c.beginPath(); pa.circle(cx,cy,r); c.clipPath(pa,stroke=0,fill=0); hatch(lambda p:p.circle(cx,cy,r),[45],2.2,0.25); c.restoreState()
    c.setFillColorRGB(1,1,1); c.circle(cx,cy,core/2*S10,stroke=0,fill=1); c.setFillColorRGB(0,0,0)
    hatch(lambda p:p.circle(cx,cy,core/2*S10),[45,-45],4.0,0.25)
    c.setLineWidth(0.6); c.circle(cx,cy,r,stroke=1,fill=0); c.circle(cx,cy,core/2*S10,stroke=1,fill=0)
    return cy-r
def cap(cx,y,lines):
    for k,l in enumerate(lines): txt(cx,y+k*8.3,l,"AB" if k==0 else "A",6.3,"c")

B1=330
def top_for(h): return B1-h*S10
ring_sec(990,top_for(0.43),0.40,0.03); cap(990,B1+14,["BASE RING STEP","cast 400 x 400, printed U 30"])
ring_sec(1150,top_for(0.28),0.25,0.03); cap(1150,B1+14,["CROWN RING","cast 250 x 250, printed U 30"])
cs=R["colsec"]; col_sec(1300,top_for(cs),cs); cap(1300,B1+14,["COLUMN","%d x %d"%(cs*1000,cs*1000)])
B2=500
for cx,band,(t,co) in zip((975,1080,1170),("BOTTOM","MIDDLE","TOP"),R["ribs"]):
    rib_sec(cx,B2-t/1000*S10,t/1000,co/1000); cap(cx,B2+14,["RIB, %s BAND"%band,"tube Ø%d, core Ø%d"%(t,co)])
S20=50*mm; fwm=R["fw"]; fx=1250; fy=Y(B2)+0.5*S20
hatch(rectp(fx,fy-0.5*S20,fwm*S20,0.5*S20),[45,-45],4.0,0.25); box(fx,fy-0.5*S20,fwm*S20,0.5*S20)
cap(fx+fwm*S20/2,B2+14,["STRIP FOOTING 1:20","%d x 500, top -0.30"%(fwm*1000),"corner blocks "+R["blocks"]])
txt(RX,590,"Single hatch = 3D printed concrete (formwork, tubes), crossed hatch = cast concrete.","AI",6.3)
sy=660
txt(RX,sy,"ELEMENT SCHEDULE · "+R["title"],"AB",8.5)
cols=[(RX,"ELEMENT","l"),(1250,"NO.","r"),(1330,"m³","r"),(1415,"t","r")]
for x,t,a in cols: txt(x,sy+22,t,"AB",6.26,a)
c.setLineWidth(1.0); c.line(RX,Y(sy+25),1417,Y(sy+25))
rows=[("Rectangular strip footing","rectangular strip footing","foot"),("Columns","columns","col"),("Base ring step","base ring step",None),
      ("Ribs (printed tubes + cast cores)","rib net","rib"),("Printed courses","printed courses","pcs"),("Crown ring","crown ring","cr")]
y=sy+36; tv=[0,0]
for lab,key,nk in rows:
    a=D[key]; vals=[R["n"][nk] if nk else "4 sides","%.1f"%a["volume_m3"],"%.1f"%a["weight_t"]]
    txt(RX,y,lab)
    for (x,_,al),v in zip(cols[1:],vals): txt(x,y,v,"A",6.8,al)
    tv[0]+=a["volume_m3"]; tv[1]+=a["weight_t"]
    c.setLineWidth(0.4); c.line(RX,Y(y+3.5),1417,Y(y+3.5)); y+=11.6
y+=4; txt(RX,y,"Total","AB")
for (x,_,al),v in zip(cols[2:],["%.1f"%tv[0],"%.1f"%tv[1]]): txt(x,y,v,"AB",6.8,al)
y+=16
txt(RX,y,"Weights at 2.4 t/m³ on the volumes measured in the Rhino model. Rib net = rib length x printed tube section (the core is inside","AI",6.3)
txt(RX,y+8.5,"the tube); the printed pieces and U formwork are counted as solid concrete walls.","AI",6.3)
print(ROOF,tv,"axon right",OX+x1m*s,"top",Y(OY+y1m*s),"LX",LX)
c.save(); base.merge_page(pypdf.PdfReader(b).pages[0])
w=pypdf.PdfWriter(); w.add_page(base); w.write(OUT)
