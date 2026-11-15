import pygame as pg
from lib.Interface import Interface as UI


class BaseInterior:
    scale = 4
    outlines = {
        'main': [(44,0),(195,0),(195,23),(240,23),(240,116),(195,116),(195,140),(44,140),(44,116),(0,116),(0,23),(44,23)],
        'corridor': [(44,0),(198,0),(198,140),(44,140),(44,116),(0,116),(0,23),(44,23)],
        'control': [(4,16),(240,16),(240,124),(4,124)],
        'crew': [(33,20),(48,5),(191,5),(206,20),(206,140),(33,140)],
        'plants': [(18,0),(221,0),(221,135),(18,135)]
    }

    @classmethod
    def build(cls, room, exits):
        s=cls.scale
        surface=pg.Surface((240*s,140*s));surface.fill('#080f18')
        points=[(x*s,y*s) for x,y in cls.outlines[room]]
        pg.draw.polygon(surface,'#1c2b38',points)
        tiles=pg.Surface(surface.get_size(),pg.SRCALPHA)
        tiles.fill('#1e303e')
        for x in range(0,240,16):pg.draw.line(tiles,'#263c4b',(x*s,0),(x*s,140*s),s//2)
        for y in range(0,140,16):pg.draw.line(tiles,'#263c4b',(0,y*s),(240*s,y*s),s//2)
        mask=pg.Surface(surface.get_size(),pg.SRCALPHA)
        pg.draw.polygon(mask,'white',points)
        tiles.blit(mask,(0,0),special_flags=pg.BLEND_RGBA_MULT);surface.blit(tiles,(0,0))
        pg.draw.polygon(surface,'#455b68',points,3*s)
        pg.draw.polygon(surface,'#293e4e',points,s)
        def rect(color,box,border=0,radius=0):
            pg.draw.rect(surface,color,[round(v*s) for v in box],border*s,border_radius=radius*s)
        def label(text,pos,size=6,color=UI.muted):
            UI.text(surface,text,(pos[0]*s,pos[1]*s),size*s,color)
        for edge,destination,arrival in exits:
            box={'left':(0,52,4,35),'right':(236,52,4,35),'top':(102,0,36,3),'bottom':(102,137,36,3)}[edge]
            rect('#68d9ce',box)
        if room=='main':
            rect('#364b59',(50,0,139,3));rect('#364b59',(50,137,139,3))
            label('01 / OPERATIONS',(71,28),7,UI.textColor)
            label('< CONTROL',(6,65),6,UI.cyan)
            label('HABITAT >',(177,65),6,UI.cyan)
            label('RESEARCH OUTPOST',(77,105),6)
            for x in (58,180):
                rect('#536979',(x,40,2,57));rect(UI.accent,(x,53,2,29))
            label('ARES / 01',(99,91),7,UI.accent)
            for y in (10,128):
                for x in (68,154):rect('#7098a4',(x,y,17,1))
        elif room=='corridor':
            label('02 / HABITAT',(76,62),7,UI.textColor)
            label('CREW CABINS',(92,13),6,UI.cyan)
            label('HYDROPONICS',(90,121),6,UI.cyan)
            label('< OPERATIONS',(6,81),5)
            for x in (53,186):rect('#4c6677',(x,30,1,80))
        elif room=='control':
            rect('#0b151e',(11,33,28,72),radius=2)
            rect('#4a6070',(11,33,28,72),1,2)
            for y in (40,61,82):
                rect('#254858',(15,y,20,15),radius=1)
                rect('#5ed6ca',(17,y+2,16,1))
                for k in range(4):rect('#477f8c',(17,y+5+k*2,9+k,1))
            rect('#354754',(39,62,6,14),radius=2)
            label('03 / CONTROL ROOM',(78,36),8,UI.textColor)
            label('REMOTE EXPLORATION DIVISION',(78,48),5)
            label('ROVER TELEMETRY',(84,70),6,UI.cyan)
            label('LINK AVAILABLE / TERMINAL 01',(84,83),5)
            label('OPERATIONS >',(190,109),5,UI.cyan)
        elif room=='crew':
            for x in (62,124):
                rect('#0d1722',(x,34,58,30),radius=2)
                rect('#4d6473',(x,34,58,30),1,2)
                rect('#b1b9ac',(x+3,37,12,24),radius=1)
                rect('#3f7f88',(x+17,37,37,24),radius=1)
                rect('#68a9aa',(x+17,37,4,24))
                rect('#152b3b',(x+42,37,12,24))
            label('04 / CREW QUARTERS',(72,19),7,UI.textColor)
            label('REST. RECOVER. CONTINUE.',(73,100),6)
            label('HABITAT',(105,126),5,UI.cyan)
        elif room=='plants':
            label('05 / HYDROPONICS',(76,13),7,UI.textColor)
            label('WATER ACCESS / UPPER AISLE',(73,25),5,UI.cyan)
            for x in (27,120):
                rect('#50616b',(x,38,91,91),radius=2)
                rect('#1c2d2a',(x+3,41,85,85),radius=1)
                for y in range(45,123,13):
                    rect('#4b3b2d',(x+6,y,79,9))
                    rect('#486373',(x+6,y+10,79,1))
                    for col in range(7):
                        center=((x+11+col*11)*s,(y+4)*s)
                        pg.draw.ellipse(surface,'#396f52',(center[0]-3*s,center[1]-2*s,6*s,4*s))
                        pg.draw.line(surface,'#9ab979',(center[0],center[1]-2*s),(center[0],center[1]+2*s),s)
        return surface
