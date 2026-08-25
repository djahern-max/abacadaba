from PIL import Image, ImageDraw, ImageFont

INK=(12,34,51); PAPER=(242,245,247); BEAD=(200,135,27); ROD=(122,148,166)
W,H=1200,630
F="/usr/share/fonts/truetype/google-fonts/Poppins-{}.ttf"

img=Image.new("RGB",(W,H),INK); d=ImageDraw.Draw(img)

# hairline rod running the full width, behind everything
d.line([(0,H-96),(W,H-96)],fill=(26,52,74),width=2)

def mark(size):
    S=size*4; m=Image.new("RGBA",(S,S),(0,0,0,0)); md=ImageDraw.Draw(m); u=S/32.0
    md.rounded_rectangle([0,0,S,S],radius=7.5*u,fill=PAPER+(255,))
    md.ellipse([(12.6-7.2)*u,(19-7.2)*u,(12.6+7.2)*u,(19+7.2)*u],fill=BEAD+(255,))
    md.rounded_rectangle([21.4*u,11.8*u,24.8*u,26.2*u],radius=1.7*u,fill=INK+(255,))
    return m.resize((size,size),Image.LANCZOS)

m=mark(104); img.paste(m,(96,150),m)

word="abacadaba"
f=ImageFont.truetype(F.format("Bold"),126)
x=96; y=300
for ch in word:
    d.text((x,y),ch,font=f,fill=PAPER if ch=="a" else BEAD)
    x+=f.getlength(ch)-3

fd=ImageFont.truetype(F.format("Medium"),30)
d.text((100,470),"SHORT CPE LESSONS YOU CAN ACTUALLY FINISH",font=fd,fill=ROD)

fu=ImageFont.truetype(F.format("Medium"),26)
d.text((96,H-70),"abacadaba.com",font=fu,fill=(90,116,135))

img.save("out/og-default.png",optimize=True)
print(img.size)
