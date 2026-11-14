import pygame as pg
from objects.Texture import Texture
from lib.RoverMap import RoverMap


class WaterWell(Texture):
    def __init__(self):
        # A simple procedural prototype; no external image loading is needed.
        image = pg.Surface((220, 220), pg.SRCALPHA)
        pg.draw.ellipse(image, '#704f40', (20,70,180,130))
        pg.draw.ellipse(image, '#c5b29c', (20,35,180,130))
        pg.draw.ellipse(image, '#192d3c', (45,55,130,85))
        pg.draw.ellipse(image, '#4288aa', (65,85,90,40))
        pg.draw.rect(image, '#c1a07b', (24,25,15,110))
        pg.draw.rect(image, '#c1a07b', (181,25,15,110))
        pg.draw.rect(image, '#c1a07b', (24,25,172,14))
        pg.draw.line(image, '#ead4a5', (110,35),(110,100),4)
        super().__init__('canyon.well', RoverMap.mapToWorld(RoverMap.canyonPixel),
                         0, 1.5, image, 55)
