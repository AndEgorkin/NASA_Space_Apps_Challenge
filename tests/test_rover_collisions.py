import os
os.environ['SDL_VIDEODRIVER']='dummy'
os.environ['SDL_AUDIODRIVER']='dummy'
import unittest
import pygame as pg
from lib.AssetManager import AssetManager
from objects.Rover import Rover
from objects.BoundingBox import BoundingBox


class RoverCollisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pg.init();pg.display.set_mode((1200,830));AssetManager.init()

    def setUp(self):
        self.rover=Rover()
        self.rover.texture=pg.Surface((20,30))
        self.rover.scale=1
        self.rover.coords[:]=[0,0]

    def tearDown(self):
        self.rover.destroy()

    def assertClear(self):
        self.assertFalse(self.rover._blockedPose(self.rover.coords,self.rover.rotation))

    def testCannotTunnelThroughThinWall(self):
        self.rover.boundingBoxes=[BoundingBox((50,0),1,1000)]
        self.assertTrue(self.rover._moveWithCollisions((300,0),0))
        self.assertLess(self.rover.coords[0],42)
        self.assertClear()

    def testNoRepeatedRecoilAndCanReverseAway(self):
        self.rover.boundingBoxes=[BoundingBox((50,0),10,1000)]
        self.rover._moveWithCollisions((80,0),0)
        position=self.rover.coords[:]
        for _ in range(20):self.rover._moveWithCollisions((5,0),0)
        self.assertEqual(self.rover.coords,position)
        self.rover._moveWithCollisions((-20,0),0)
        self.assertAlmostEqual(self.rover.coords[0],position[0]-20)
        self.assertClear()

    def testSlidesAlongWallWithoutEnteringIt(self):
        self.rover.boundingBoxes=[BoundingBox((50,0),10,1000)]
        self.rover._moveWithCollisions((70,100),0)
        self.assertGreater(self.rover.coords[1],90)
        self.assertLess(self.rover.coords[0],38)
        self.assertClear()

    def testRotationCornersDoNotEnterObstacle(self):
        self.rover.coords[:]=[0,0]
        self.rover.boundingBoxes=[BoundingBox((15,0),4,100)]
        self.rover._moveWithCollisions((0,0),180)
        self.assertLess(self.rover.rotation,90)
        self.assertClear()

    def testRecoversFromOverlapAndRespectsRotatedWall(self):
        self.rover.boundingBoxes=[BoundingBox((0,0),40,40,30)]
        self.rover._moveWithCollisions((0,0),0)
        self.assertClear()
        self.rover.coords[:]=[-100,0]
        self.rover._moveWithCollisions((200,0),0)
        self.assertLess(self.rover.coords[0],0)
        self.assertClear()
