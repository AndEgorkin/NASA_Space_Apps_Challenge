import os
os.environ['SDL_VIDEODRIVER']='dummy'
os.environ['SDL_AUDIODRIVER']='dummy'
import unittest
import pygame as pg
from lib.Survival import Survival
from lib.RoverMap import RoverMap


class SurvivalTests(unittest.TestCase):
    def setUp(self):
        pg.font.init()
        self.state = Survival()

    def testTwentyMinutesAndConstantFoodConsumption(self):
        self.state.update(600)
        self.assertEqual(self.state.oxygen, 600)
        self.assertAlmostEqual(self.state.food,100/3)
        self.state.update(600)
        self.assertEqual(self.state.oxygen,0)
        self.assertEqual(self.state.food,0)
        self.assertTrue(self.state.depleted)

    def testWaterDeliveryAndFoodLoop(self):
        well = RoverMap.mapToWorld(RoverMap.canyonPixel)
        self.state.roverAction(well)
        self.assertEqual(self.state.cargoWater,1)
        self.assertEqual(self.state.water,0)
        self.state.food=50
        self.state.waterPlants()
        self.assertEqual(self.state.food,50)
        self.state.roverAction((0,0))
        self.assertEqual(self.state.water,1)
        self.assertEqual(self.state.cargoWater,0)
        self.state.waterPlants()
        self.assertEqual(self.state.water,0)
        self.assertEqual(self.state.food,80)

    def testCapacityRangeAndFullFood(self):
        self.state.roverAction((50000,50000))
        self.assertEqual(self.state.cargoWater,0)
        for _ in range(10):
            self.state.roverAction(RoverMap.mapToWorld(RoverMap.canyonPixel))
        self.assertEqual(self.state.cargoWater,5)
        self.state.roverAction((0,0))
        self.state.waterPlants()
        self.assertEqual(self.state.water,5)
        self.state.food=90
        self.state.waterPlants()
        self.assertEqual(self.state.food,100)
        self.assertEqual(self.state.water,4)
