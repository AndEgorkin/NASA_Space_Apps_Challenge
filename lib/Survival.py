import math
import pygame as pg
from lib.RoverMap import RoverMap
from lib.Interface import Interface as UI


class Survival:
    oxygenDuration = 20 * 60.0
    foodDuration = 15 * 60.0
    cargoCapacity = 5
    interactionRadius = 280

    def __init__(self):
        self.oxygen = self.oxygenDuration
        self.food = 100.0
        self.water = 0
        self.cargoIce = 0
        self.iceDiscovered = False
        self.deliveredWater = 0
        self.wateredPlants = 0
        self.message = ''
        self.messageTime = 0.0
        self.font = pg.font.Font(None, 23)

    @property
    def depleted(self):
        return self.oxygen <= 0 or self.food <= 0

    def update(self, seconds):
        seconds = max(0, seconds)
        self.oxygen = max(0, self.oxygen - seconds)
        self.food = max(0, self.food - seconds * 100 / self.foodDuration)
        self.messageTime = max(0, self.messageTime - seconds)

    def notify(self, message):
        self.message = message
        self.messageTime = 9

    def roverAction(self, coords):
        point = pg.Vector2(coords)
        deposit = RoverMap.mapToWorld(RoverMap.icePixel)
        if point.distance_to(deposit) <= self.interactionRadius:
            if not self.iceDiscovered:
                self.notify('Complete Mission 5 to discover underground ice before extracting it.')
            elif self.cargoIce >= self.cargoCapacity:
                self.notify('Ice cargo full. Return to base.')
            else:
                self.cargoIce += 1
                self.notify('Ice extracted into rover cargo. Deliver it to base for melting.')
        elif point.distance_to(RoverMap.baseCoords) <= RoverMap.baseInteractionRadius:
            if self.cargoIce:
                self.deliveredWater += self.cargoIce
                self.water += self.cargoIce
                self.cargoIce = 0
                self.notify('Ice delivered and melted: water added to base inventory.')
            else:
                self.notify('No ice in rover cargo.')

    def waterPlants(self):
        if self.water <= 0:
            self.notify('No water: discover ice in Mission 5 and deliver it to base.')
        elif self.food >= 99.9:
            self.notify('Food reserves are full.')
        else:
            self.wateredPlants += 1
            self.water -= 1
            self.food = min(100.0, self.food + 30)
            self.notify('Plants watered: +30 food, -1 water.')

    def roverHint(self, coords):
        point = pg.Vector2(coords)
        if point.distance_to(RoverMap.mapToWorld(RoverMap.icePixel)) <= self.interactionRadius:
            return 'E: extract ice' if self.iceDiscovered else 'E: investigate underground ice (Mission 5)'
        if point.distance_to(RoverMap.baseCoords) <= RoverMap.baseInteractionRadius:
            return 'E: unload and melt ice at base'
        return ''

    def render(self, screen, hint='', compact=False):
        width, height = screen.get_size()
        panel = pg.Rect(width-420,12,396,76) if compact else pg.Rect(width-300,48,284,142)
        UI.panel(screen,panel)
        total = math.ceil(self.oxygen)
        rows = [('OXYGEN  %02d:%02d' % divmod(total,60),self.oxygen/self.oxygenDuration,UI.cyan),
                (f'FOOD  {self.food:.0f}%',self.food/100,'#a4c879')]
        for index,(label,fraction,color) in enumerate(rows):
            x=panel.x+14+(index*188 if compact else 0)
            y=panel.y+10+(0 if compact else index*43)
            UI.text(screen,label,(x,y),21,UI.textColor)
            bar=pg.Rect(x,y+22,174 if compact else 256,5)
            pg.draw.rect(screen,'#283c4c',bar,border_radius=2)
            pg.draw.rect(screen,color if fraction>0.2 else '#ef7566',(bar.x,bar.y,round(bar.w*fraction),bar.h),border_radius=2)
        inventory=f'WATER  {self.water}     /     ROVER ICE  {self.cargoIce}/{self.cargoCapacity}'
        UI.text(screen,inventory,(panel.x+14,panel.y+(49 if compact else 108)),19,UI.muted)
        if hint:
            UI.text(screen,hint,(24,height-54),23,UI.accent)
        if self.messageTime > 0:
            # Wrap notices so mission reports remain readable at the screen edge.
            font=UI.font(23)
            lines=['']
            for word in self.message.split():
                candidate=(lines[-1]+' '+word).strip()
                if font.size(candidate)[0]>width-96:
                    lines.append(word)
                else:
                    lines[-1]=candidate
            box=pg.Rect(24,height-151,width-48,22*len(lines)+20)
            UI.panel(screen,box)
            for i,line in enumerate(lines):UI.text(screen,line,(box.x+12,box.y+10+i*22),23,UI.accent)
