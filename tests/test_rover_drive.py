import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
import unittest
from unittest.mock import patch
import pygame as pg
from lib.AssetManager import AssetManager
from objects.Rover import Rover


class RoverDriveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pg.init()
        AssetManager.init()

    def setUp(self):
        self.rover = Rover()
        self.rover.coords[:] = [0, -500]
        self.keys = {key: False for key in (pg.K_w, pg.K_s, pg.K_a, pg.K_d)}

    def tearDown(self):
        self.rover.destroy()

    def testForwardAfterIdleAtSpawn(self):
        with patch('pygame.key.get_pressed', return_value=self.keys):
            for _ in range(60):
                self.rover.update(1/60)
            startY = self.rover.coords[1]
            self.keys[pg.K_w] = True
            for _ in range(120):
                self.rover.update(1/60)
        self.assertGreater(self.rover.velocity, 20)
        self.assertGreater(self.rover.coords[1], startY + 20)

    def testForwardStillBrakesSignificantReverseSpeed(self):
        self.rover.velocity = -50
        self.keys[pg.K_w] = True
        with patch('pygame.key.get_pressed', return_value=self.keys):
            self.rover.update(1/60)
            self.assertLess(self.rover.velocity, 0)
            self.assertGreater(self.rover.velocity, -50)
            for _ in range(120):
                self.rover.update(1/60)
            self.assertGreater(self.rover.velocity, 0)
