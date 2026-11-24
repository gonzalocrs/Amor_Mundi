import io, json, sys, pypdf
from PIL import Image, ImageChops
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm
F="/usr/share/fonts/truetype/liberation/LiberationSans-"
for n,f in (("A","Regular"),("AB","Bold"),("AI","Italic")): pdfmetrics.registerFont(TTFont(n,F+f+".ttf"))
SCR="/tmp/claude-0/-home-claude/0f8208d9-0bf5-5d45-9dcd-a2d33e7bf201/scratchpad/"
KM=SCR+"artifact-files/fe341845-2c28-4311-88ab-99449afccf2c/drawings-2026-11-23/karamba-model/"
ROOF,CASE,OUT=sys.argv[1],sys.argv[2],sys.argv[3]
TT=json.load(open(KM+"karamba-model-tables.json")); T=TT[ROOF]
DV=json.load(open(KM+"../design-values-D2.json"))[ROOF]
base=pypdf.PdfReader(SCR+"final-S101-S108.pdf").pages[2]
W=float(base.mediabox.width); H=float(base.mediabox.height); Y=lambda y:H-y
b=io.BytesIO(); c=canvas.Canvas(b,pagesize=(W,H))
def txt(x,y,s,f="A",sz=7.4,a="l"):
    c.setFont(f,sz); (c.drawString if a=="l" else c.drawRightString if a=="r" else c.drawCentredString)(x,Y(y),s)
c.setFillColorRGB(1,1,1); c.rect(33,Y(1157),1402,1124,stroke=0,fill=1); c.rect(511.6*mm,(420-323.0)*mm,67.8*mm,33*mm,stroke=0,fill=1)
c.setFillColorRGB(0,0,0); c.setFont("A",17)
title="15 x 10" if ROOF=="15x10" else "10 x 10"
c.drawCentredString(546.85*mm,(420-303.5)*mm,"KARAMBA MODEL"); c.drawCentredString(546.85*mm,(420-311.5)*mm,title+" ROOF")
txt(70,92,"THE KARAMBA MODEL: EVERY ELEMENT ASSEMBLED · %s STEPPED ROOF"%title.upper(),"AB",15)
txt(70,110,"The %s roof as analysed in Karamba3D, built from the same Rhino and Grasshopper model as the drawings. The printed pieces are in the model, tied to the ribs through their tubes, with mortar bed joints that can only push."%title,sz=7.4)
def render(CASE,bx0,by0,bx1,by1):
    G=TT["render"]["legends"]["%s %s"%(ROOF,CASE)]; lc=G["load_case"]; al=12.0 if CASE=="LONG" else 24.0
    L=dict(load_case=lc,allowable_MPa=al,max_compression_MPa=G["actual_extremes_MPa_my_section_check"]["compression"],max_tension_MPa=-G["actual_extremes_MPa_my_section_check"]["tension"])
    L["max_compression_utilisation"]=L["max_compression_MPa"]/al
    # render box
    c.setLineWidth(0.6); c.rect(bx0,Y(by1),bx1-bx0,by1-by0,stroke=1,fill=0)
    im=Image.open(KM+"karamba-model-%s-%s.png"%(ROOF,CASE)).convert("RGB")
    bb=ImageChops.difference(im,Image.new("RGB",im.size,(255,255,255))).getbbox(); pad=20
    im=im.crop((max(bb[0]-pad,0),max(bb[1]-pad,0),min(bb[2]+pad,im.width),min(bb[3]+pad,im.height)))
    bw,bh=bx1-bx0-30,by1-by0-30; k=min(bw/im.width,bh/im.height); iw,ih=im.width*k,im.height*k
    jb=io.BytesIO(); im.save(jb,'JPEG',quality=88); jb.seek(0)
    c.drawImage(ImageReader(jb),bx0+(bx1-bx0-iw)/2,Y(by0+(by1-by0+ih)/2),iw,ih)
    # legend bar (Karamba BeamView axial stress, fixed range)
    rng=4 if CASE=="LONG" else 7
    lx,ly=bx0+20,by0+26
    RED=(180/255,6/255,55/255); BLU=(86/255,69/255,172/255)
    for i in range(100):
        t=i/99*2-1   # -1 compression(red) .. +1 tension(blue)
        e=RED if t<0 else BLU; a=abs(t)
        c.setFillColorRGB(*[1-(1-v)*a for v in e]); c.rect(lx+i*1.8,Y(ly+9),1.9,9,stroke=0,fill=1)
    c.setFillColorRGB(0,0,0); c.setLineWidth(0.3); c.rect(lx,Y(ly+9),180,9,stroke=1,fill=0)
    txt(lx,ly+19,"−%d"%rng,sz=6.3); txt(lx+90,ly+19,"0","A",6.3,"c"); txt(lx+180,ly+19,"+%d MPa"%rng,"A",6.3,"r")
    txt(lx,ly+28,"compression","AI",6.3); txt(lx+180,ly+28,"tension","AI",6.3,"r")
    txt(lx,ly-5,"AXIAL STRESS, %s (KARAMBA BEAMVIEW)"%("LONG" if CASE=="LONG" else "TYPHOON "+lc),"AB",6.3)
    cases={"LONG":"LONG (weight)","SHORT":"worst typhoon case %s"%lc}
    txt(bx0,by1+13,"Karamba3D, %s %s: axial stress at the worst fibre of every member, bending included (red compression, blue tension, full colour beyond ±%d MPa)."%(title,cases[CASE],rng),"AI",6.8)
    txt(bx0,by1+22,"Highest compression %.1f MPa = %d %% of the %.0f MPa allowable; highest tension %.1f MPa, taken by the bars. Printed formwork shown as a pale see-through layer; footing (grey) checked by hand."%(L["max_compression_MPa"],round(L["max_compression_utilisation"]*100),L["allowable_MPa"],L["max_tension_MPa"]),"AI",6.8)
    
render('LONG',70,140,890,600)
render('SHORT',70,650,890,1110)
CASE=sys.argv[2]
# right column
RX,RR=930,1415
def table(y,head,cols,rows,bold_last=False):
    txt(RX,y,head,"AB",9.5); y+=18
    for x,t,a in cols: txt(x,y,t,"AB",6.6,a)
    c.setLineWidth(0.9); c.line(RX,Y(y+3.5),RR,Y(y+3.5)); y+=14
    for n,r in enumerate(r for r in rows):
        f="AB" if (bold_last and n==len(rows)-1) else "A"
        for (x,_,a),v in zip(cols,r): txt(x,y,v,f,7.0,a)
        c.setLineWidth(0.35); c.line(RX,Y(y+4),RR,Y(y+4)); y+=13.5
    return y
sec=lambda s:s.split(";")[0].replace("solid round D","Ø").replace(" (cast core","").replace("printed tube around it not counted as stiffness)","").replace(" x "," × ")
names={"rib_bottom":"Ribs, bottom band (cast core)","rib_middle":"Ribs, middle band","rib_top":"Ribs, top band","ring":"Base ring +2.00","crown":"Crown ring","column":"Columns","course":"Printed courses","fin":"Piece end walls (fins)"}
rows=[]
for e in T["elements"]:
    s=sec(e["section_mm"]).strip()
    if e["id"]=="column": s=s.split(",")[0]+", fixed base"
    if e["id"]=="course": s="box 450 × 500, open head joints"
    if e["id"]=="fin": s="2 walls 80 × 300, push only"
    rows.append((names[e["id"]],e["id"],s,str(e["bars"])))
y=table(160,"ELEMENTS IN THE MODEL",[(RX,"ELEMENT","l"),(1105,"ID","l"),(1180,"SECTION, MM","l"),(RR,"BARS","r")],rows)
txt(RX,y+4,T["material"].replace("allowable","allowables")+".","AI",6.3)
y=table(y+40,"LOAD CASES",[(RX,"CASE","l"),(1045,"COMBINATION","l"),(1300,"USED FOR","l")],
  [("LONG","1.0 G + finishes 1.47 kN/m²","long-term, upper render"),
   ("W ±X, ±Y, 45°","LONG + typhoon qp 2.6 kN/m²","short-term, lower render (worst)"),
   ("LIVE X, Y","LONG + 0.6 kN/m² on half roof","long-term"),
   ("EQ X, Y","LONG + 0.14 × weight sideways","short-term")])
txt(RX,y+4,"Finishes = formwork top-up 0.34 + insulation and finishes 1.13 kN/m². Typhoon V0 46 m/s and EQ zone factor 0.7 assumed, to confirm.","AI",6.3)
wk,wt=T["weight_kN"],T["weight_t"]
y=table(y+40,"TOTAL WEIGHT",[(RX,"","l"),(1330,"kN","r"),(RR,"t","r")],
  [("Roof above the columns: ribs, rings, printed courses","%.1f"%wk["roof_above_columns"],"%.1f"%wt["roof_above_columns"]),
   ("Columns","%.1f"%wk["columns"],"%.1f"%(wk["columns"]/9.81)),
   ("Whole structure, down to the footing","%.1f"%wk["whole_structure_vertical_reaction_LONG"],"%.1f"%wt["whole_structure"])],bold_last=True)
txt(RX,y+4,"1 t = 9.81 kN. The whole weight is Karamba's total vertical reaction under LONG: every kilonewton reaches the footing.","AI",6.3)
txt(RX,y+12.5,"The strip footing itself is not in Karamba (hand check). The exploded-axon schedule (%s) is higher because it adds the footing"%("S103, 268.2 t" if ROOF=="15x10" else "S104, 147.9 t"),"AI",6.3)
txt(RX,y+21,"and measures the printed pieces from the Rhino solids.","AI",6.3)
y+=48; txt(RX,y,"HOW THE PRINTED PIECES WORK","AB",9.5); y+=17
ca=DV["casing"]
for l in ["– Each piece is printed around its rib tube and the core is cast through it: the rib ties every piece.",
          "– The mortar bed joints between courses only push: the end walls that cross them are compression-only,",
          "   and Karamba removes any that would pull, case by case. Head joints along a course are taken as open.",
          "– About %d %% of the weight reaches the base ring through the pieces, at %s MPa or less."%(round(ca["share_of_weight_through_casing"]*100),"1.6" if ROOF=="15x10" else "1.0"),
          "– Under typhoon up to %d of %d end walls lift off; the ribs carry their load around them."%(ca["end_walls_lifting_off_max"],ca["end_walls_total"]),
          "– Grip between tube and cast core: %.2f MPa at most. No steel or ties across the joints."%ca["tube_core_shear_MPa_max"]]:
    txt(RX,y,l,sz=7.0); y+=11
y+=24; txt(RX,y,"RESULTS, ALL 10 LOAD CASES","AB",9.5); y+=6
rw=DV["rib_worst_long_term"]; rs=DV["rib_worst_short_term"]; dfl=DV["deflection_mm"]
y=table(y+10,"",[(RX,"CHECK","l"),(1250,"RESULT","l")],[
  ("Worst rib, long-term","%d %% (bottom band, %s)"%(rw["util_pct"],rw["case"].replace("LIVE","LIVE "))),
  ("Worst rib, short-term","%d %% (bottom band, %s)"%(rs["util_pct"],rs["case"])),
  ("Columns","%d %% long-term, %d %% short-term"%(DV["columns"]["util_long"]["util_pct"],DV["columns"]["util_short"]["util_pct"])),
  ("Crown ring","%d %%"%DV["crown_ring"]["util_short"]["util_pct"]),
  ("Deflection","%.1f mm LONG, %.1f mm max"%(dfl["LONG"],dfl["max"])),
  ("First buckling factor","43" if ROOF=="15x10" else "85.5")])
c.save(); base.merge_page(pypdf.PdfReader(b).pages[0])
w=pypdf.PdfWriter(); w.add_page(base); w.write(OUT)
