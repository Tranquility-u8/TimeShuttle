"""Bake the replaceable printed clock fascias. Live time is rendered in UE."""
from pathlib import Path
import math
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
FONTS = Path("C:/Windows/Fonts")
SIZE = 1024, 1824
PAPER = "#d1d3cf"
INK = "#172a30"
RULE = "#838e8c"


def draw_face(is_reference):
    im = Image.new("RGB", SIZE, PAPER)
    d = ImageDraw.Draw(im)
    accent = "#225f63" if is_reference else "#79503b"
    def tx(x,y,v,sz=28,col=INK,bold=False,mono=False):
        filename = ("consolab.ttf" if bold else "consola.ttf") if mono else ("ARIALNB.TTF" if bold else "ARIALN.TTF")
        d.text((x,y), v, font=ImageFont.truetype(str(FONTS/filename),sz), fill=col, anchor="lt")
    def line(x,y,x2,y2,color=RULE,w=2):
        d.line((x,y,x2,y2),fill=color,width=w)
    d.rectangle((0,0,1023,300),fill=accent)
    tx(63,58,"A" if is_reference else "B",161,"#f2f0e5",True)
    tx(224,73,"REFERENCE" if is_reference else "TEST CLOCK",67,"#f2f0e5",True)
    tx(226,175,"PRIMARY STANDARD" if is_reference else "COMPARISON CHANNEL",27,"#d5e1de",False,True)
    line(55,257,966,257,"#b7c5bf",2)
    tx(56,271,"TEMPORAL METROLOGY     /     SERIES 04",16,"#eff1e9",False,True)
    tx(60,373,"TIMEBASE" if is_reference else "ELAPSED COUNT",49,INK,True)
    tx(60,452,"UTC  /  HOURS, MINUTES, SECONDS" if is_reference else "LATCHED  /  SIX-DECADE REGISTER",22,accent,False,True)
    # This dark field accepts an independently modelled display or counter assembly.
    d.rounded_rectangle((63,513,961,845),radius=15,fill="#26383b",outline="#586463",width=5)
    tx(94,555,"01    LOCAL READOUT",20,"#a1b2ae",False,True)
    line(91,794,927,794,"#60716e",2)
    tx(89,810,"EXT. REF    /    10 MHz" if is_reference else "NONVOLATILE    /    ROLL COUNT",17,"#c2cbc3",False,True)
    tx(62,942,"STABILITY TRACE" if is_reference else "PHASE RESIDUAL",37,INK,True)
    tx(63,1004,"OSCILLATOR A     /     MONITOR" if is_reference else "CHANNEL B     /     LAST WINDOW",20,accent,False,True)
    d.rectangle((63,1065,961,1303),fill="#c4c9c4",outline=RULE,width=2)
    for x in range(83,953,38):
        line(x,1080,x,1287,"#a6b1aa",1)
    for y in range(1096,1304,38):
        line(77,y,947,y,"#a6b1aa",1)
    pts=[]
    for x in range(82,944,3):
        t=(x-82)/862
        if is_reference:
            y=1195-8*math.sin(t*60)-3*math.sin(t*290)
            if int(t*9.0)%2==0 and (t*9)%1<.10:
                y-=45
        else:
            if t>.75: break
            y=1190-22*math.sin(t*43)-5*math.sin(t*150)-min(65,max(0,t-.52)*240)
        pts.append((x,round(y)))
    d.line(pts,fill=accent,width=5)
    for x in range(83,950,39):
        line(x,1328,x,1345 if (x-83)%117==0 else 1337,INK,2)
    tx(63,1380,"INTERNAL RESERVE" if is_reference else "HOLD ON LOSS",26,INK,True)
    tx(62,1441,"CELL STATUS" if is_reference else "CAPTURE STATE",18,INK,False,True)
    line(62,1500,959,1500)
    tx(65,1550,"TC–04   /   A01" if is_reference else "TC–04   /   B01",34,INK,True,True)
    tx(66,1611,"INSTRUMENT ENGINEERING",18,accent,True)
    for i in range(33):
        x=721+i*6
        line(x,1562,x,1622,INK,1 if i%3==0 else 3)
    tx(63,1718,"TIMING SYSTEMS    /    CALIBRATION LAB",18,INK,False,True)
    line(64,1682,961,1682)
    im.save(ROOT/"Textures"/("T_TC_ReferenceFace.png" if is_reference else "T_TC_TestFace.png"))


if __name__=="__main__":
    draw_face(True)
    draw_face(False)
