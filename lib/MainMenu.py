import math
import pygame as pg
from lib.AssetManager import AssetManager
from lib.Interface import Interface as UI


class MainMenu:
    def __init__(self, screen):
        self.screen = screen
        self.background = AssetManager.get('assets.menu.background')
        self.selected = 0
        self.entries = [('play', 'Begin / resume expedition', True),
                        ('load', 'Save slots coming soon', False),
                        ('settings', 'Configuration coming soon', False),
                        ('quit', 'Close mission control', True)]
        width, height = screen.get_size()
        scale = min(width / 1200, height / 830)
        self.scale = scale
        self.buttons = [(name, pg.Rect(round(64*scale),round((292+i*86)*scale),
                                       round(340*scale),round(70*scale)))
                        for i,(name,_,_) in enumerate(self.entries)]
        factor = max(width/self.background.get_width(),height/self.background.get_height())
        size = (round(self.background.get_width()*factor),round(self.background.get_height()*factor))
        self.backdrop = pg.transform.smoothscale(self.background,size)
        self.backdropOffset = (width-size[0],(height-size[1])//2)
        self.shade = pg.Surface((width,height),pg.SRCALPHA)
        for x in range(width):
            alpha = round(240-155*(x/max(1,width-1))**0.7)
            pg.draw.line(self.shade,(5,15,26,alpha),(x,0),(x,height))

    def run(self):
        clock = pg.time.Clock()
        while True:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    return False
                if event.type == pg.MOUSEMOTION:
                    for i,(_,rect) in enumerate(self.buttons):
                        if rect.collidepoint(event.pos):self.selected=i
                if event.type == pg.KEYDOWN:
                    if event.key in (pg.K_DOWN,pg.K_UP,pg.K_TAB):
                        self.selected = (self.selected + (-1 if event.key==pg.K_UP else 1)) % 4
                    elif event.key in (pg.K_RETURN,pg.K_SPACE):
                        if self.selected==0:return True
                        if self.selected==3:return False
                if event.type == pg.MOUSEBUTTONDOWN and event.button==1:
                    for name,rect in self.buttons:
                        if rect.collidepoint(event.pos):
                            if name=='play':return True
                            if name=='quit':return False
            self._render()
            pg.display.flip()
            clock.tick(60)

    def _render(self):
        self.screen.blit(self.backdrop,self.backdropOffset)
        self.screen.blit(self.shade,(0,0))
        s=self.scale
        def text(label,x,y,size,color=None):
            UI.text(self.screen,label,(round(x*s),round(y*s)),max(14,round(size*s)),color)
        text('ARES  /  EXPEDITION CONTROL',64,66,23,UI.cyan)
        pg.draw.line(self.screen,UI.cyan,(round(64*s),round(103*s)),(round(130*s),round(103*s)),2)
        text('THE LONG',60,133,76)
        text('WAY HOME',60,195,76)
        text('Eight discoveries. One chance to return.',64,264,24,UI.muted)
        for index, ((name,subtitle,enabled),(_,rect)) in enumerate(zip(self.entries,self.buttons)):
            active=index==self.selected and enabled
            UI.panel(self.screen,rect,'#213b4d' if active else '#101e2b')
            if active:
                pg.draw.rect(self.screen,UI.accent,rect,2,border_radius=10)
                pg.draw.rect(self.screen,UI.accent,(rect.x,rect.y+12,4,rect.h-24))
            color=UI.textColor if enabled else '#607587'
            UI.text(self.screen,name.upper(),(rect.x+round(22*s),rect.y+round(12*s)),round(30*s),color)
            UI.text(self.screen,subtitle,(rect.x+round(22*s),rect.y+round(43*s)),max(14,round(19*s)),UI.muted if enabled else '#607587')
            if active:UI.text(self.screen,'>',(rect.right-round(30*s),rect.y+round(23*s)),round(28*s),UI.accent)
        text('MARS SURFACE OPERATIONS',64,719,20,UI.muted)
        text('20 MIN OXYGEN  /  8 RESEARCH MISSIONS',64,746,20,UI.cyan)
        text('ARROWS TO SELECT   /   ENTER TO CONFIRM',64,788,18,UI.muted)
        width,height=self.screen.get_size()
        pulse=120+round(60*math.sin(pg.time.get_ticks()/900))
        pg.draw.circle(self.screen,(80,pulse,160),(width-round(225*s),height-round(52*s)),4)
        UI.text(self.screen,'UPLINK STANDBY',(width-round(210*s),height-round(62*s)),max(14,round(20*s)),UI.cyan)
