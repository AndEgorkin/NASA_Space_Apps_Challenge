import os
os.environ['SDL_VIDEODRIVER']='dummy'
os.environ['SDL_AUDIODRIVER']='dummy'
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
import pygame as pg
from lib.RoverMap import RoverMap
from lib.RoverSave import RoverSave


class MapTests(unittest.TestCase):
    def testProjectionAndBorders(self):
        self.assertEqual(RoverMap.worldToMap((0,0)), RoverMap.basePixel)
        for coords in [(1000,2000),(-10000,-4000),(0,0)]:
            actual=RoverMap.mapToWorld(RoverMap.worldToMap(coords))
            self.assertAlmostEqual(actual[0],coords[0]);self.assertAlmostEqual(actual[1],coords[1])
        rect=pg.Rect(0,0,768,558)
        for point in [(-100,200),(900,200),(300,-100),(300,800),(-1000,-1000)]:
            edge=RoverMap.edgePosition(point,rect)
            self.assertTrue(rect.collidepoint(edge))
            self.assertTrue(min(abs(edge.x-12),abs(edge.x-756),abs(edge.y-12),abs(edge.y-546))<0.01)

    def testHeadingMatchesProjectedRoverForward(self):
        from objects.Rover import Rover
        rover = Rover.__new__(Rover)
        for rotation in (0, 45, 90, 135, 180, -90, 270, 360):
            rover.rotation = rotation
            forwardX, forwardY, _, _ = rover._getDirectionAxes()
            origin = RoverMap.worldToMap((0, 0))
            projected = RoverMap.worldToMap((forwardX * 100, forwardY * 100)) - origin
            self.assertLess(projected.normalize().distance_to(RoverMap.headingOnMap(rotation)), 0.00001)

    def testPersistenceAndBadSave(self):
        original=RoverSave.path
        with tempfile.TemporaryDirectory() as folder:
            try:
                RoverSave.path=Path(folder)/'rover.json'
                rover=SimpleNamespace(coords=[0,0],rotation=0)
                RoverSave.load(rover,RoverMap.spawnCoords)
                self.assertEqual(tuple(rover.coords),RoverMap.spawnCoords)
                rover.coords[:]=[1300,-2500];rover.rotation=42
                RoverSave.save(rover)
                loaded=SimpleNamespace(coords=[0,0],rotation=0)
                RoverSave.load(loaded,RoverMap.spawnCoords)
                self.assertEqual(loaded.coords,rover.coords);self.assertEqual(loaded.rotation,42)
                RoverSave.path.write_text('invalid')
                RoverSave.load(loaded,RoverMap.spawnCoords)
                self.assertEqual(tuple(loaded.coords),RoverMap.spawnCoords)
            finally:
                RoverSave.path=original

    def testMapRendersInsideAndOutside(self):
        pg.init();screen=pg.display.set_mode((1200,830)); chart=RoverMap()
        for position in [(0,0),(50000,0),(0,50000),(-50000,-50000)]:
            chart.render(screen,SimpleNamespace(coords=position,rotation=45))
