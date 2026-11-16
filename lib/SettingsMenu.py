import pygame as pg
from lib.GameSettings import GameSettings
from lib.Interface import Interface as UI


class SettingsMenu:
    def __init__(self, screen, survival=None, rover=None):
        self.screen=screen
        self.survival=survival
        self.rover=rover
        self.values=GameSettings.current()
        self.selected=0
        self.dragging=None
        self.panel=pg.Rect(0,0,1000,740);self.panel.center=screen.get_rect().center
        self.scroll=0
        self.contentRect=pg.Rect(self.panel.x+14,self.panel.y+100,self.panel.w-28,480)
        self.sliders=[pg.Rect(self.panel.x+470,self.panel.y+132+i*68,340,8)
                      for i in range(len(GameSettings.specs))]
        self.defaultsButton=pg.Rect(self.panel.x+24,self.panel.bottom-88,330,44)
        self.cancelButton=pg.Rect(self.panel.right-286,self.panel.bottom-88,112,44)
        self.applyButton=pg.Rect(self.panel.right-158,self.panel.bottom-88,134,44)

    def scrollBy(self, amount):
        self.scroll=max(0,min(max(0,len(GameSettings.specs)*68-self.contentRect.h),self.scroll+amount))
        for i,bar in enumerate(self.sliders):bar.y=self.panel.y+132+i*68-self.scroll

    def revealSelected(self):
        top=self.panel.y+109+self.selected*68-self.scroll
        if top<self.contentRect.top:self.scrollBy(top-self.contentRect.top)
        elif top+54>self.contentRect.bottom:self.scrollBy(top+54-self.contentRect.bottom)

    def setFromMouse(self, index, x):
        key,_,minimum,maximum,step,_,_=GameSettings.specs[index]
        bar=self.sliders[index]
        fraction=max(0,min(1,(x-bar.x)/bar.w))
        self.values[key]=min(maximum,max(minimum,round((minimum+fraction*(maximum-minimum))/step)*step))

    def apply(self):
        GameSettings.apply(self.values,self.survival)
        if self.rover is not None and GameSettings.current()['leakChance']==0:
            self.rover.energyLeakActive=False
            self.rover.energyLeakTimeRemaining=0

    def handleEvent(self, event):
        if event.type==pg.QUIT:return 'quit'
        if event.type==pg.KEYDOWN:
            if event.key==pg.K_ESCAPE:return 'cancel'
            if event.key in (pg.K_UP,pg.K_DOWN,pg.K_TAB):
                self.selected=(self.selected+(-1 if event.key==pg.K_UP else 1))%len(GameSettings.specs)
                self.revealSelected()
            elif event.key in (pg.K_LEFT,pg.K_RIGHT):
                key,_,minimum,maximum,step,_,_=GameSettings.specs[self.selected]
                self.values[key]=min(maximum,max(minimum,self.values[key]+(-step if event.key==pg.K_LEFT else step)))
            elif event.key==pg.K_RETURN:
                self.apply();return 'apply'
        elif event.type==pg.MOUSEWHEEL:
            self.scrollBy(-event.y*48)
        elif event.type==pg.MOUSEBUTTONDOWN and event.button==1:
            if self.defaultsButton.collidepoint(event.pos):
                self.values=dict(GameSettings.defaults)
            elif self.cancelButton.collidepoint(event.pos):return 'cancel'
            elif self.applyButton.collidepoint(event.pos):
                self.apply();return 'apply'
            else:
                for i,bar in enumerate(self.sliders):
                    if self.contentRect.collidepoint(event.pos) and bar.inflate(24,32).collidepoint(event.pos):
                        self.selected=self.dragging=i
                        self.setFromMouse(i,event.pos[0]);break
        elif event.type==pg.MOUSEMOTION and self.dragging is not None:
            self.setFromMouse(self.dragging,event.pos[0])
        elif event.type==pg.MOUSEBUTTONUP and event.button==1:
            self.dragging=None
        return None

    def run(self):
        clock=pg.time.Clock()
        while True:
            # Read one event at a time, leaving queued events for the parent menu.
            event=pg.event.poll()
            while event.type!=pg.NOEVENT:
                result=self.handleEvent(event)
                if result is not None:return result
                event=pg.event.poll()
            self.render();pg.display.flip();clock.tick(60)

    def render(self):
        self.screen.fill(UI.background);UI.panel(self.screen,self.panel)
        x,y=self.panel.topleft
        UI.text(self.screen,'EXPEDITION SETTINGS',(x+24,y+22),36,UI.cyan)
        UI.text(self.screen,'Tune survival and rover hazards. Apply to use your changes.',(x+24,y+63),23,UI.muted)
        previousClip=self.screen.get_clip()
        self.screen.set_clip(self.contentRect)
        for i,(key,label,minimum,maximum,step,unit,helpText) in enumerate(GameSettings.specs):
            top=y+109+i*68-self.scroll
            color=UI.accent if i==self.selected else UI.textColor
            UI.text(self.screen,label,(x+24,top),26,color)
            UI.text(self.screen,helpText,(x+24,top+29),18,UI.muted)
            bar=self.sliders[i];fraction=(self.values[key]-minimum)/(maximum-minimum)
            pg.draw.rect(self.screen,'#314758',bar,border_radius=4)
            pg.draw.rect(self.screen,UI.cyan,(bar.x,bar.y,round(bar.w*fraction),bar.h),border_radius=4)
            pg.draw.circle(self.screen,color,(round(bar.x+bar.w*fraction),bar.centery),8)
            value=self.values[key]
            labelValue=f'{value:.1f}' if abs(value-round(value))>0.01 else str(round(value))
            UI.text(self.screen,f'{labelValue} {unit}',(x+838,top+11),25,color)
        self.screen.set_clip(previousClip)
        maximum=max(0,len(GameSettings.specs)*68-self.contentRect.h)
        if maximum:
            track=pg.Rect(self.panel.right-12,self.contentRect.top,4,self.contentRect.h)
            pg.draw.rect(self.screen,'#314758',track,border_radius=2)
            thumbHeight=max(30,track.h*self.contentRect.h/(len(GameSettings.specs)*68))
            thumb=pg.Rect(track.x,track.y+(track.h-thumbHeight)*self.scroll/maximum,4,thumbHeight)
            pg.draw.rect(self.screen,UI.cyan,thumb,border_radius=2)
        UI.text(self.screen,'Supply time already consumed is kept. Shorter budgets may exhaust reserves.',(x+24,y+598),20,UI.muted)
        UI.text(self.screen,'Session only. Scroll for more; arrows adjust; Enter applies; Esc cancels.',(x+24,y+623),20,UI.muted)
        for button,label in ((self.defaultsButton,'Set to default (realistic)'),(self.cancelButton,'Cancel'),(self.applyButton,'Apply')):
            UI.panel(self.screen,button,'#26434f' if button==self.applyButton else UI.panelColor)
            text=UI.font(25).render(label,True,UI.cyan if button==self.applyButton else UI.textColor)
            self.screen.blit(text,text.get_rect(center=button.center))
