import sys,os
from PIL import Image, ImageDraw, ImageFont
import pymupdf
S,R=sys.argv[1:3]
W,H=1700,1100
F=lambda s: ImageFont.truetype("C:/Windows/Fonts/arial.ttf",s); FB=lambda s: ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf",s)
src=pymupdf.open(R+'/friend-iterations-review-v3.pdf')
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
("15","12 FEET 2 m from corners + OPEN","12","A and B all C","0.53","20/132","corners 1.43 m short","friend-12-feet-2m-corners-opentop")]
p=Image.new('RGB',(W,H),'white'); d=ImageDraw.Draw(p)
d.text((40,30),"Friend's roof variants - all iterations (PolyFrame 2, 10x10 m plan, apex ~6.67 m)",font=FB(30),fill='black')
d.text((40,72),"All files in polyframe2 (not committed). 3D review: friend-iterations-review-v4.3dm, one layer per iteration. C = compression.",font=F(15),fill='black')
d.text((40,92),"Karamba: cast C30/37, ribs 150x250, rigid joints, feet pinned, self-weight + 7 kN/m2 (assumed) on the pyramid surface; elastic stress check, no rebar.",font=F(15),fill='black')
xs=[40,80,330,390,580,760,880,1220]; y=130
for i,r in enumerate(rows):
    f=FB(15) if (i==0 or r[0] in ('14','15')) else F(15)
    for x,c in zip(xs,r): d.text((x,y),c,font=f,fill='black')
    y+=25; d.line((40,y-6,W-40,y-6),fill=(200,200,200))
ov=Image.open(S+'/review4_persp.png'); ov.thumbnail((W-80,H-y-30)); p.paste(ov,(40,y+8))
q=Image.new('RGB',(W,H),'white'); d=ImageDraw.Draw(q)
d.text((40,25),"15  12 feet (2 m from each corner + mid-side), corners free, OPEN TOP, re-found for even load",font=FB(20),fill='black')
im=Image.open(R+'/friend-12-feet-2m-corners-opentop.png').convert('RGB'); im.thumbnail((W//2-60,H-90)); q.paste(im,(40,65))
a1=Image.open(S+'/c14_top.png').convert('RGB'); a1.thumbnail((W//4-30,W//4-30)); a2=Image.open(S+'/c15_top.png').convert('RGB'); a2.thumbnail((W//4-30,W//4-30))
q.paste(a1,(W//2+20,90)); q.paste(a2,(W//2+20+W//4,90))
d.text((W//2+20,65),"#14 (feet 1 m from corners) top",font=FB(15),fill='black'); d.text((W//2+20+W//4,65),"#15 (feet 2 m from corners) top",font=FB(15),fill='black')
rows2=[("Karamba (150x250, self-wt + 7 kN/m2)","#14 (1 m)","#15 (2 m)"),
("Max compression / fcd","0.56","0.53"),("Bending tension / fctm (rebar)","3.1","3.3"),("Max bending","10.0 kNm","8.3 kNm"),
("Axial force range","-73..+4.5 kN","-62..+2.4 kN"),("Max deflection","5.6 mm","4.8 mm"),("Buckling factor","49.3","40.7"),
("Rib concrete","18.2 t","17.7 t"),("Near-corner foot V / H","86 / 42 kN","107 / 43 kN"),("Mid-side foot V / H","165 / 37 kN","123 / 28 kN"),
("PolyFrame max / mean deviation","10.1 / 2.3 deg","7.7 / 1.5 deg"),("Closest node pair","236 mm","191 mm"),
("Net reach on diagonal (corner 7.07 m)","6.34 m","5.64 m"),("Corner not covered","0.73 m","1.43 m"),("Height above ref. pyramid","up to 2.6 m","up to 2.3 m")]
y=110+W//4
for i,r in enumerate(rows2):
    f=FB(14) if i==0 else F(14)
    for x,c in zip((W//2+20,W//2+330,W//2+500),r): d.text((x,y),c,font=f,fill='black')
    y+=23
d.text((W//2+20,y+10),"Both: all compression in stage A and B; feet held at exact points. Not verified: 7 kN/m2 assumed,",font=F(13),fill='black')
d.text((W//2+20,y+28),"no wind/seismic, elastic check without rebar.",font=F(13),fill='black')
p.save(R+'/friend-iterations-review-v4.pdf',save_all=True,append_images=rest+[q],resolution=100)
print('pages',2+len(rest))
