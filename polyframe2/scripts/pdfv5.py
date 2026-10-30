import sys,os
from PIL import Image, ImageDraw, ImageFont
import pymupdf
S,R=sys.argv[1:3]
W,H=1700,1100
F=lambda s: ImageFont.truetype("C:/Windows/Fonts/arial.ttf",s); FB=lambda s: ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf",s)
src=pymupdf.open(R+'/friend-iterations-review-v4.pdf')
rest=[]
for i in range(1,src.page_count):
    pm=src[i].get_pixmap(dpi=100); rest.append(Image.frombytes("RGB",[pm.width,pm.height],pm.samples))
rows=[("#","Iteration","Feet","PolyFrame final shape","Karamba comp/fcd","Bars <=35 deg","Known flaw","File"),
("1","Panel A frame","4","exact, all C","-","-","not the sheet's look","friend-A-4corners"),
("2","Panel A shell (ex 3(7))","4","exact, all C (136 bars)","-","-","free edges 1.3 m vs 2.3 m","friend-A-shell"),
("3","AP8 frame","8","stage B all C","-","-","not the sheet's look","friend-AP8-buttresses"),
("4","AP12 frame","12","stage B all C","-","-","not the sheet's look","friend-AP12-buttresses"),
("5","AP8 shell GUESS","8","stage B all C","-","-","not symmetric","friend-AP8-shell-GUESS"),
("6","AP8 shell v2 (rings)","8","stage B all C","-","24/248","96 horizontal ring bars","friend-AP8-shell-v2 (+printcast)"),
("7","AP12 shell","12","stage B all C","-","112/516","rings horizontal; stage A tension","friend-AP12-shell"),
("8","AP8 diagrid","8","stage B all C","1.03 (corner legs)","24/272","stage A 40 tension","friend-AP8-diagrid"),
("9","16-feet diagrid (5/side)","16","A and B all C","1.17 (mid-face)","16/192","mid-side feet idle","friend-16-diagrid"),
("10","AP8 even load (hub)","8","A and B all C","0.58","24/272","48 flat hub bars; ring overlap","friend-AP8-diagrid-evenload"),
("11","AP8 even load OPEN TOP","8","stage B all C","0.52","32/296","nodes 20 mm apart at ring","friend-AP8-diagrid-evenload-opentop"),
("12","AP8 even load 4 rings","8","stage B all C","0.90 (corner legs)","40/224","32 flat bars; stage A tension","friend-AP8-diagrid-evenload-4ring"),
("13","16 FEET (5/side) + OPEN TOP","16","A and B all C","0.52","36/176","4 tiny 14 mm bars at ring","friend-16-diagrid-evenload-opentop"),
("14","12 FEET near corners + OPEN","12","A and B all C","0.56","20/132","corners 0.73 m short; net 2.6 m above pyramid","friend-12-feet-near-corners-opentop"),
("15","12 FEET 2 m from corners + OPEN","12","A and B all C","0.53","20/132","corners 1.43 m short","friend-12-feet-2m-corners-opentop"),
("16","20 FEET 2 m from corners + OPEN","20","B all C (A tension)","0.37","76/260","corners 1.43 m short; nodes 54 mm","friend-20-feet-2m-corners-opentop")]
p=Image.new('RGB',(W,H),'white'); d=ImageDraw.Draw(p)
d.text((40,30),"Friend's roof variants - all iterations (PolyFrame 2, 10x10 m plan, apex ~6.67 m)",font=FB(30),fill='black')
d.text((40,72),"All files in polyframe2 (not committed). 3D review: friend-iterations-review-v5.3dm, one layer per iteration. C = compression.",font=F(15),fill='black')
d.text((40,92),"Karamba: cast C30/37, ribs 150x250, rigid joints, feet pinned, self-weight + 7 kN/m2 (assumed) on the pyramid surface; elastic stress check, no rebar.",font=F(15),fill='black')
xs=[40,80,330,390,580,760,880,1220]; y=130
for i,r in enumerate(rows):
    f=FB(15) if (i==0 or r[0] in ('15','16')) else F(15)
    for x,c in zip(xs,r): d.text((x,y),c,font=f,fill='black')
    y+=24; d.line((40,y-6,W-40,y-6),fill=(200,200,200))
ov=Image.open(S+'/review5_persp.png'); ov.thumbnail((W-80,H-y-30)); p.paste(ov,(40,y+8))
q=Image.new('RGB',(W,H),'white'); d=ImageDraw.Draw(q)
d.text((40,25),"16  20 feet (5 per side, 1.5 m apart, outer 2 m from corners), corners free, OPEN TOP, even load",font=FB(20),fill='black')
im=Image.open(R+'/friend-20-feet-2m-corners-opentop.png').convert('RGB'); im.thumbnail((W//2-60,H-90)); q.paste(im,(40,65))
a1=Image.open(S+'/c15_top.png').convert('RGB'); a1.thumbnail((W//4-30,W//4-30)); a2=Image.open(S+'/c16_top.png').convert('RGB'); a2.thumbnail((W//4-30,W//4-30))
q.paste(a1,(W//2+20,90)); q.paste(a2,(W//2+20+W//4,90))
d.text((W//2+20,65),"#15 (12 feet) top",font=FB(15),fill='black'); d.text((W//2+20+W//4,65),"#16 (20 feet) top",font=FB(15),fill='black')
rows2=[("Karamba (150x250, self-wt + 7 kN/m2)","#15 (12 feet)","#16 (20 feet)"),
("Total load carried","1,344 kN","1,434 kN"),("Rib concrete","17.7 t","26.7 t"),
("Max compression / fcd","0.53","0.37"),("Bending tension / fctm (rebar)","3.3","2.4"),("Max bending","8.3 kNm","5.9 kNm"),
("Axial force range","-62..+2.4 kN","-61..+9.2 kN"),("Max deflection","4.8 mm","3.5 mm"),("Buckling factor","40.7","69.0"),
("Outer foot (2 m from corner) V / H","107 / 43 kN","70 / 24 kN"),("Quarter foot (1.5 m from mid) V / H","-","64 / 19 kN"),("Mid-side foot V / H","123 / 28 kN","89 / 21 kN"),
("PolyFrame stage A","all C","has tension (-28 kN)"),("PolyFrame final max / mean deviation","7.7 / 1.5 deg","11.1 / 2.3 deg"),("Closest node pair","191 mm","54 mm (16 pairs <200)"),
("Net reach on diagonal (corner 7.07 m)","5.64 m","5.64 m"),("Height above ref. pyramid","up to 2.3 m","up to 2.8 m")]
y=110+W//4
for i,r in enumerate(rows2):
    f=FB(14) if i==0 else F(14)
    for x,c in zip((W//2+20,W//2+330,W//2+500),r): d.text((x,y),c,font=f,fill='black')
    y+=23
d.text((W//2+20,y+10),"Final forms both all compression; feet held at exact points. Not verified: 7 kN/m2 assumed,",font=F(13),fill='black')
d.text((W//2+20,y+28),"no wind/seismic, elastic check without rebar.",font=F(13),fill='black')
p.save(R+'/friend-iterations-review-v5.pdf',save_all=True,append_images=rest+[q],resolution=100)
print('pages',2+len(rest))
