import pygame as pg
from objects.Texture import Texture
from lib.RoverMap import RoverMap


class IceDeposit(Texture):
    def __init__(self):
        # A fictional excavation site for the reservoir mission prototype.
        image = pg.Surface((240,180),pg.SRCALPHA)
        pg.draw.ellipse(image,'#674839',(5,10,230,160))
        pg.draw.ellipse(image,'#302d30',(25,28,190,120))
        for points in (((48,110),(64,65),(102,47),(113,107)),
                       ((102,123),(113,63),(155,42),(173,113)),
                       ((158,118),(178,76),(205,91),(193,128))):
            pg.draw.polygon(image,'#91c7d8',points)
            pg.draw.lines(image,'#def7fb',False,points[:3],4)
        pg.draw.rect(image,'#b58559',(15,22,8,110))
        pg.draw.rect(image,'#efb65c',(8,18,22,9))
        super().__init__('research.ice',RoverMap.mapToWorld(RoverMap.icePixel),0,1.5,image,55)
