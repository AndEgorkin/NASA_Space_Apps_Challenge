import pygame as pg
from lib.Interface import Interface as UI


class LandslideSurvey:
    # Fictional local survey image: the cliff is north of the debris deposits.
    clusters = ((180,95),(280,175),(210,275))
    directions = ('NORTH','EAST','SOUTH','WEST')

    def __init__(self):
        self.active=False
        self.marked=set()
        self.phase=0
        self.selected=None
        self.message=''

    def start(self, mapped=False):
        self.active=True
        self.phase=int(mapped)
        self.marked=set(range(3)) if mapped else set()
        self.selected=None
        self.message='Click the three debris clusters to map the landslide.' if not mapped else 'Which way did the debris travel from the cliff?'

    def cancel(self):
        self.active=False

    @staticmethod
    def layout(screenSize):
        panel=pg.Rect(0,0,740,560);panel.center=(screenSize[0]//2,screenSize[1]//2)
        field=pg.Rect(panel.x+20,panel.y+100,460,350)
        buttons=[pg.Rect(panel.x+510,panel.y+190+i*48,205,40) for i in range(4)]
        return panel,field,buttons

    def handleEvent(self, event, screenSize):
        if not self.active:return None
        _,field,buttons=self.layout(screenSize)
        if self.phase==0:
            if event.type==pg.MOUSEBUTTONDOWN and event.button==1 and field.collidepoint(event.pos):
                local=pg.Vector2(event.pos)-pg.Vector2(field.topleft)
                found=next((i for i,point in enumerate(self.clusters) if local.distance_to(point)<=34),None)
                if found is None:
                    self.message='Look for groups of angular rocks below the cliff.'
                else:
                    self.marked.add(found)
                    self.message=f'Debris clusters mapped: {len(self.marked)}/3'
                    if len(self.marked)==3:
                        self.phase=1
                        self.message='Mapping complete. Which way did the debris travel from the cliff?'
                        return 'mapped'
            return None
        if event.type==pg.MOUSEBUTTONDOWN and event.button==1:
            for index,button in enumerate(buttons):
                if button.collidepoint(event.pos):self.selected=index
        elif event.type==pg.KEYDOWN:
            choices={pg.K_w:0,pg.K_UP:0,pg.K_d:1,pg.K_RIGHT:1,pg.K_s:2,pg.K_DOWN:2,pg.K_a:3,pg.K_LEFT:3}
            if event.key in choices:self.selected=choices[event.key]
            elif event.key==pg.K_e:
                if self.selected is None:
                    self.message='Choose a direction first: arrows, WASD, or click a button.'
                elif self.selected!=2:
                    self.message='Look again: the cliff is north; the debris spreads below it.'
                else:
                    self.active=False
                    return 'complete'
        return None

    def render(self, screen):
        if not self.active:return
        panel,field,buttons=self.layout(screen.get_size())
        shade=pg.Surface(screen.get_size(),pg.SRCALPHA);shade.fill((3,9,15,180));screen.blit(shade,(0,0))
        UI.panel(screen,panel)
        UI.text(screen,'IUS CHASMA / LANDSLIDE SURVEY',(panel.x+22,panel.y+20),30,UI.cyan)
        UI.text(screen,'Map the debris. Use the cliff and deposits as evidence.',(panel.x+22,panel.y+57),23,UI.muted)
        pg.draw.rect(screen,'#5c4035',field,border_radius=5)
        for y in range(field.y+35,field.bottom,27):
            pg.draw.line(screen,'#6c4b3b',(field.x+6,y),(field.right-6,y-12),2)
        # Three parallel exposed layers at the cliff; the debris fan lies below.
        for i,color in enumerate(('#d29b70','#a17051','#7e533e')):
            pg.draw.lines(screen,color,False,[(field.x+35,field.y+15+i*12),(field.x+200,field.y+26+i*12),(field.right-30,field.y+12+i*12)],8)
        UI.text(screen,'N / CLIFF EDGE',(field.x+10,field.y+5),20,'#ffffff')
        fan=[(field.x+205,field.y+55),(field.x+80,field.bottom-15),(field.right-60,field.bottom-15)]
        pg.draw.polygon(screen,'#795240',fan)
        for i,point in enumerate(self.clusters):
            center=pg.Vector2(field.topleft)+point
            for j,(dx,dy) in enumerate(((-18,3),(2,-12),(15,8),(-3,18))):
                x,y=center.x+dx,center.y+dy
                pg.draw.polygon(screen,'#b38260',[(x-10,y-5),(x-4,y-13),(x+11,y-6),(x+8,y+10),(x-9,y+9)])
                pg.draw.line(screen,'#e0ae80',(x-5,y-9),(x+8,y-6),2)
            if i in self.marked:
                pg.draw.circle(screen,UI.cyan,center,34,2)
                UI.text(screen,str(i+1),(center.x+27,center.y-30),22,UI.cyan)
        UI.text(screen,'S',(field.centerx,field.bottom-22),20,'white')
        UI.text(screen,f'MAPPED {len(self.marked)}/3',(panel.x+510,panel.y+110),25,UI.cyan)
        UI.text(screen,'FLOW DIRECTION',(panel.x+510,panel.y+151),23,UI.textColor)
        for i,button in enumerate(buttons):
            UI.panel(screen,button,'#294654' if self.selected==i else UI.panelColor)
            UI.text(screen,self.directions[i],(button.x+15,button.y+10),24,UI.cyan if self.selected==i else UI.muted)
        UI.text(screen,'E: confirm direction',(panel.x+510,panel.y+401),21,UI.accent)
        UI.text(screen,'Esc: cancel survey',(panel.x+510,panel.y+430),21,UI.muted)
        words=self.message.split();lines=['']
        for word in words:
            candidate=(lines[-1]+' '+word).strip()
            if UI.font(23).size(candidate)[0]>panel.width-44:lines.append(word)
            else:lines[-1]=candidate
        for i,line in enumerate(lines):UI.text(screen,line,(panel.x+22,panel.y+475+i*24),23,UI.accent)
        UI.text(screen,'Simplified survey illustration, not a measured orbital image.',(panel.x+22,panel.bottom-23),18,UI.muted)
