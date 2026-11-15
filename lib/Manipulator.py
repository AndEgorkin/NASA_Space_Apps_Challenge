import math
import pygame as pg
from lib.Interface import Interface as UI


class Manipulator:
    def __init__(self):
        self.active = False
        self.tip = pg.Vector2(0,-80)
        self.sample = pg.Vector2(145,-145)
        self.tray = pg.Vector2(-145,-55)
        self.carrying = False
        self.message = ''

    def start(self):
        self.active = True
        self.tip.update(0,-80)
        self.carrying = False
        self.message = 'Move the gripper to the sample with WASD, then press E.'

    def cancel(self):
        self.active = False
        self.carrying = False

    def update(self, seconds, direction=None):
        if not self.active:
            return
        if direction is None:
            keys=pg.key.get_pressed()
            direction=(int(keys[pg.K_d])-int(keys[pg.K_a]),int(keys[pg.K_s])-int(keys[pg.K_w]))
        movement=pg.Vector2(direction)
        if movement.length_squared():
            self.tip += movement.normalize()*150*min(max(seconds,0),0.1)
        self.tip.x=max(-235,min(235,self.tip.x))
        self.tip.y=max(-245,min(-20,self.tip.y))
        if self.tip.length()>260:
            self.tip.scale_to_length(260)

    def interact(self):
        if not self.active:
            return False
        target=self.tray if self.carrying else self.sample
        if self.tip.distance_to(target)>22:
            self.message='Move closer to the storage tray.' if self.carrying else 'Move closer to the rock sample.'
            return False
        if not self.carrying:
            self.carrying=True
            self.message='Sample secured. Move to the left tray with WASD and press E.'
            return False
        self.active=False
        self.carrying=False
        return True

    def render(self, screen):
        if not self.active:
            return
        box=pg.Rect(0,0,620,420);box.center=screen.get_rect().center
        shade=pg.Surface(screen.get_size(),pg.SRCALPHA);shade.fill((3,9,15,175));screen.blit(shade,(0,0))
        UI.panel(screen,box)
        UI.text(screen,'ROVER / SAMPLE MANIPULATOR',(box.x+22,box.y+18),28,UI.cyan)
        UI.text(screen,'WASD: move   E: grab / store   Esc: cancel',(box.x+22,box.y+49),22,UI.muted)
        pivot=pg.Vector2(box.centerx,box.bottom-85)
        for x in range(box.x+20,box.right-20,30):pg.draw.line(screen,'#213545',(x,box.y+85),(x,box.bottom-65))
        for y in range(box.y+90,box.bottom-60,30):pg.draw.line(screen,'#213545',(box.x+20,y),(box.right-20,y))
        tray=pivot+self.tray;sample=pivot+self.sample;tip=pivot+self.tip
        pg.draw.rect(screen,'#537b82',(tray.x-30,tray.y-24,60,48),2,border_radius=5)
        UI.text(screen,'TRAY',(tray.x-22,tray.y+27),20,UI.cyan)
        if not self.carrying:
            pg.draw.polygon(screen,'#d18f62',[(sample.x-15,sample.y+10),(sample.x-9,sample.y-14),(sample.x+14,sample.y-8),(sample.x+18,sample.y+10)])
            UI.text(screen,'SAMPLE',(sample.x-30,sample.y+24),20,UI.accent)
        # Two equal articulated links, solved from the gripper position.
        delta=self.tip;distance=max(1,delta.length());half=delta/2
        perpendicular=pg.Vector2(-delta.y,delta.x)/distance
        elbow=pivot+half+perpendicular*math.sqrt(max(0,150**2-(distance/2)**2))
        pg.draw.lines(screen,'#758d9e',False,[pivot,elbow,tip],12)
        for joint in (pivot,elbow,tip):pg.draw.circle(screen,UI.cyan,joint,7)
        pg.draw.lines(screen,UI.accent,False,[(tip.x-12,tip.y-12),(tip.x-12,tip.y),(tip.x+12,tip.y),(tip.x+12,tip.y-12)],3)
        if self.carrying:pg.draw.circle(screen,'#d18f62',(tip.x,tip.y-10),9)
        UI.text(screen,self.message,(box.x+18,box.bottom-37),20,UI.textColor)
