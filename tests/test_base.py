import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
import unittest
from collections import deque
import pygame as pg
from lib.BaseLocation import BaseLocation
from Main import Main


class BaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pg.init()
        cls.screen = pg.display.set_mode((1200, 830))

    def setUp(self):
        self.base = BaseLocation(self.screen)

    def testAllDoorwaysReachableAndArrivalsSafe(self):
        starts = {'main': (120, 75), 'corridor': (12, 75), 'control': (220, 75),
                  'crew': (120, 128), 'plants': (120, 15)}
        for room, start in starts.items():
            self.base.room = room
            visited = {start}
            queue = deque([start])
            while queue:
                x, y = queue.popleft()
                for point in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
                    if (point not in visited and 3 <= point[0] <= 237 and 3 <= point[1] <= 137
                            and not self.base._blocked(pg.Vector2(point))):
                        visited.add(point)
                        queue.append(point)
            for edge, destination, arrival in self.base.exits[room]:
                candidates = {'top': [(x,3) for x in range(54,185)],
                              'bottom': [(x,137) for x in range(54,185)],
                              'left': [(3,y) for y in range(30,111)],
                              'right': [(237,y) for y in range(30,111)]}[edge]
                point = next((p for p in candidates if p in visited), None)
                self.assertIsNotNone(point, (room, edge))
                self.base.room = room
                self.base.position.update(point)
                self.assertTrue(self.base._transition())
                self.assertEqual(self.base.room, destination)
                self.assertFalse(self.base._blocked(self.base.position), (destination, arrival))
                self.assertFalse(self.base._transition(), 'must not bounce back')
                self.base.room = room
            if room == 'control':
                self.assertIn((45,75), visited)

    def testObjectsAndWallsBlockMovement(self):
        self.base.room = 'control'
        self.base.position.update(45,75)
        self.assertTrue(self.base.canControl())
        for _ in range(100):
            self.base.update(0.1, (-1,0))
        self.assertGreaterEqual(round(self.base.position.x) - 5, 39)
        self.assertFalse(self.base._blocked(self.base.position))
        self.base.room = 'plants'
        self.base.position.update(70,25)
        for _ in range(100):
            self.base.update(0.1, (0,1))
        self.assertLess(self.base.position.y,38)

    def testUpperWallsStopWholeBody(self):
        for room, start in [('control', (120,75)), ('crew', (120,100))]:
            self.base.room = room
            self.base.position.update(start)
            for _ in range(100):
                self.base.update(0.1, (0,-1))
            rect = pg.Rect(0,0,10,16)
            rect.midbottom = (round(self.base.position.x), round(self.base.position.y)+2)
            self.assertIsNone(self.base.wallMasks[room].overlap(self.base.playerMask, rect.topleft))
            self.assertGreater(rect.top,0)
            self.assertFalse(self.base.isWalking)

    def testLeftControlRoomAndAnimation(self):
        self.base.position.update(4,75)
        self.base.update(0.1, (-1,0))
        self.assertEqual(self.base.room, 'control')
        self.base.position.update(100,75)
        self.base.update(0.1, (1,0))
        self.assertEqual(self.base.facing,2)
        self.assertTrue(self.base.isWalking)
        self.assertGreater(self.base.walkTime,0)
        self.assertEqual(len(self.base.walkFrames),4)
        self.assertTrue(all(len(row)==4 for row in self.base.walkFrames))
        self.base.update(0.1,(0,0))
        self.assertFalse(self.base.isWalking)
        self.assertEqual(self.base.walkTime,0)

    def testInteractionAndEscape(self):
        event = lambda key: pg.event.Event(pg.KEYDOWN, key=key)
        self.assertIsNone(self.base.handleEvent(event(pg.K_e)))
        self.base.room = 'control'
        self.base.position.update(45,75)
        self.assertEqual(self.base.handleEvent(event(pg.K_e)), 'rover')
        self.assertEqual(self.base.handleEvent(event(pg.K_ESCAPE)), 'menu')
        Main.scene = 'rover'
        Main.clock = pg.time.Clock()
        pg.event.clear()
        pg.event.post(event(pg.K_ESCAPE))
        Main.tick()
        self.assertEqual(Main.scene, 'base')


if __name__ == '__main__':
    unittest.main()
