S="C:/Users/gonza/AppData/Local/Temp/claude/C--Users-gonza-Documents-GitHub-pyramid-roof/88d2013e-3524-4014-9052-f727e6ca9a4a/scratchpad"; R="C:/Users/gonza/Documents/GitHub/pyramid-roof/polyframe2"; python - "$S" "$R" <<'EOF'
import sys,os
from PIL import Image, ImageDraw, ImageFont
import pymupdf
S,R=sys.argv[1:3]
W,H=1700,1100
F=lambda s: ImageFont.truetype("C:/Windows/Fonts/arial.ttf",s); FB=lambda s: ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf",s)
src=pymupdf.open(R+'/friend-iterations-review.pdf')
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
("13","16 FEET (5/side) + OPEN TOP","16","A and B all C","0.52","36/176","4 tiny 14 mm bars at ring","friend-16-diagrid-evenload-opentop")]
p=Image.new('RGB',(W,H),'white'); d=ImageDraw.Draw(p)
d.text((40,30),"Friend's roof variants - all iterations (PolyFrame 2, 10x10 m plan, apex ~6.67 m)",font=FB(30),fill='black')
d.text((40,72),"All files in polyframe2 (not committed). 3D review: friend-iterations-review-v2.3dm, one layer per iteration. C = compression.",font=F(15),fill='black')
d.text((40,92),"Karamba: cast C30/37, ribs 150x250, rigid joints, feet pinned, self-weight + 7 kN/m2 (assumed) on the pyramid surface; elastic stress check, no rebar.",font=F(15),fill='black')
xs=[40,80,330,390,580,760,880,1220]; y=130
for i,r in enumerate(rows):
    f=FB(15) if (i==0 or r[0] in ('9','11','13')) else F(15)
    for x,c in zip(xs,r): d.text((x,y),c,font=f,fill='black')
    y+=28; d.line((40,y-6,W-40,y-6),fill=(200,200,200))
ov=Image.open(S+'/review2_persp.png'); ov.thumbnail((W-80,H-y-30)); p.paste(ov,(40,y+8))
q=Image.new('RGB',(W,H),'white'); d=ImageDraw.Draw(q)
d.text((40,25),"13  16 feet (5 per side) + OPEN TOP, re-found for even load - Karamba vs original 16-feet diagrid (left)",font=FB(20),fill='black')
im=Image.open(R+'/friend-16-diagrid-evenload-opentop.png').convert('RGB'); im.thumbnail((W//2-60,H-90)); q.paste(im,(40,65))
im2=Image.open(S+'/where_16_open.png').convert('RGB'); im2.thumbnail((W//2-60,H-90)); q.paste(im2,(W//2+20,65))
d.text((W//2+20,H-30),"Close-ups of #9 (5 per side) and #11 (hollow top) as they appear in the 3dm",font=F(15),fill='black')
p.save(R+'/friend-iterations-review-v2.pdf',save_all=True,append_images=rest+[q],resolution=100)
print('pages',2+len(rest))
EOF
ls -la "$R"/friend-iterations-review-v2.* "$R"/friend-16-diagrid-evenload-opentop*