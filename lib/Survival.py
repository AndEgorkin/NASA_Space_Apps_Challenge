import math
import pygame as pg
from lib.RoverMap import RoverMap


class Survival:
    oxygenDuration = 20 * 60.0
    foodDuration = 15 * 60.0
    cargoCapacity = 5
    interactionRadius = 280

    def __init__(self):
        self.oxygen = self.oxygenDuration
        self.food = 100.0
        self.water = 0
        self.cargoWater = 0
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
        self.messageTime = 4

    def roverAction(self, coords):
        point = pg.Vector2(coords)
        well = RoverMap.mapToWorld(RoverMap.canyonPixel)
        if point.distance_to(well) <= self.interactionRadius:
            if self.cargoWater >= self.cargoCapacity:
                self.notify('Water cargo full. Return to base.')
            else:
                self.cargoWater += 1
                self.notify('Water collected into rover cargo.')
        elif point.distance_to(RoverMap.baseCoords) <= 650:
            if self.cargoWater:
                self.water += self.cargoWater
                self.cargoWater = 0
                self.notify('Water delivered to base inventory.')
            else:
                self.notify('No water in rover cargo.')

    def waterPlants(self):
        if self.water <= 0:
            self.notify('No water: collect at the canyon and deliver to base.')
        elif self.food >= 99.9:
            self.notify('Food reserves are full.')
        else:
            self.water -= 1
            self.food = min(100.0, self.food + 30)
            self.notify('Plants watered: +30 food, -1 water.')

    def roverHint(self, coords):
        point = pg.Vector2(coords)
        if point.distance_to(RoverMap.mapToWorld(RoverMap.canyonPixel)) <= self.interactionRadius:
            return 'E: collect water from well'
        if point.distance_to(RoverMap.baseCoords) <= 650:
            return 'E: unload water at base'
        return ''

    def render(self, screen, hint=''):
        width, height = screen.get_size()
        panel = pg.Rect(width - 300, 48, 284, 136)
        pg.draw.rect(screen, '#101823', panel, border_radius=8)
        total = math.ceil(self.oxygen)
        rows = [('OXYGEN  %02d:%02d' % divmod(total, 60), self.oxygen / self.oxygenDuration, '#60caff'),
                (f'FOOD  {self.food:.0f}%', self.food / 100, '#83d674')]
        for index, (label, fraction, color) in enumerate(rows):
            y = panel.y + 10 + index * 42
            screen.blit(self.font.render(label, True, 'white'), (panel.x+12, y))
            bar = pg.Rect(panel.x+12, y+22, 260, 10)
            pg.draw.rect(screen, '#364452', bar)
            pg.draw.rect(screen, color if fraction > 0.2 else '#ef645c', (bar.x,bar.y,round(bar.w*fraction),bar.h))
        inventory = f'Water: {self.water}  |  Rover cargo: {self.cargoWater}/{self.cargoCapacity}'
        screen.blit(self.font.render(inventory, True, 'white'), (panel.x+12,panel.y+105))
        if hint:
            screen.blit(self.font.render(hint, True, '#ffcd79'), (16,height-54))
        if self.messageTime > 0:
            screen.blit(self.font.render(self.message, True, '#ffcd79'), (16,height-80))
