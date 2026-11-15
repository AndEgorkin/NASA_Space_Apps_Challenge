import os
os.environ['SDL_VIDEODRIVER']='dummy'
os.environ['SDL_AUDIODRIVER']='dummy'
import unittest
import pygame as pg
from lib.AssetManager import AssetManager
from lib.BaseLocation import BaseLocation


class SpriteTransparencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pg.init();cls.screen=pg.display.set_mode((1200,830));AssetManager.init()

    def testFloorPreservedWithTransparentOrBlackPadding(self):
        base=BaseLocation(self.screen)
        floor=(30,48,62)
        for row in base.walkFrames:
            for source in row:
                flattened=pg.Surface(source.get_size())
                flattened.fill('black');flattened.blit(source,(0,0))
                for inputFrame in (source,flattened):
                    image=base._scalePlayerFrame(inputFrame,(56,74))
                    canvas=pg.Surface((56,74));canvas.fill(floor)
                    canvas.blit(image,(0,0),special_flags=pg.BLEND_PREMULTIPLIED)
                    for point in ((0,0),(55,0),(0,73),(55,73),(2,30),(53,30)):
                        self.assertEqual(canvas.get_at(point)[:3],floor)
                    self.assertGreater(pg.mask.from_surface(image).count(),0)

    def testDarkInteriorDetailsRemainOpaque(self):
        source=pg.Surface((20,20),pg.SRCALPHA)
        pg.draw.rect(source,'orange',(4,4,12,12))
        pg.draw.rect(source,'black',(8,8,4,4))
        image=BaseLocation._scalePlayerFrame(source,(20,20))
        self.assertEqual(image.get_at((10,10)).a,255)
        self.assertEqual(image.get_at((0,0)).a,0)
