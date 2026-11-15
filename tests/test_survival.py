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
        self.state.iceDiscovered = True

    def testTwentyMinutesAndConstantFoodConsumption(self):
        self.state.update(600)
        self.assertEqual(self.state.oxygen, 600)
        self.assertAlmostEqual(self.state.food,100/3)
        self.state.update(600)
        self.assertEqual(self.state.oxygen,0)
        self.assertEqual(self.state.food,0)
        self.assertTrue(self.state.depleted)

    def testWaterDeliveryAndFoodLoop(self):
        well = RoverMap.mapToWorld(RoverMap.icePixel)
        self.state.roverAction(well)
        self.assertEqual(self.state.cargoIce,1)
        self.assertEqual(self.state.water,0)
        self.state.food=50
        self.state.waterPlants()
        self.assertEqual(self.state.food,50)
        self.state.roverAction((0,0))
        self.assertEqual(self.state.water,1)
        self.assertEqual(self.state.cargoIce,0)
        self.state.waterPlants()
        self.assertEqual(self.state.water,0)
        self.assertEqual(self.state.food,80)

    def testCapacityRangeAndFullFood(self):
        self.state.roverAction((50000,50000))
        self.assertEqual(self.state.cargoIce,0)
        for _ in range(10):
            self.state.roverAction(RoverMap.mapToWorld(RoverMap.icePixel))
        self.assertEqual(self.state.cargoIce,5)
        self.state.roverAction((0,0))
        self.state.waterPlants()
        self.assertEqual(self.state.water,5)
        self.state.food=90
        self.state.waterPlants()
        self.assertEqual(self.state.food,100)
        self.assertEqual(self.state.water,4)

    def testDiscoveryLocksExtractionUntilMissionFive(self):
        from lib.Missions import Missions
        state=Survival();missions=Missions()
        coords=RoverMap.mapToWorld(RoverMap.icePixel)
        state.roverAction(coords)
        self.assertEqual(state.cargoIce,0)
        missions.roverAction(coords,state)
        self.assertFalse(state.iceDiscovered)
        state.roverAction(coords)
        self.assertEqual(state.cargoIce,0)
        missions.roverAction(coords,state)
        self.assertTrue(missions.done(4))
        self.assertTrue(state.iceDiscovered)
        self.assertEqual(state.cargoIce,0)
        state.roverAction(coords)
        self.assertEqual(state.cargoIce,1)
        self.assertEqual(state.water,0)
        state.roverAction((50000,50000))
        self.assertEqual(state.water,0)
        state.roverAction((0,0))
        self.assertEqual(state.water,1)
        self.assertEqual(state.cargoIce,0)
        self.assertEqual(state.deliveredWater,1)
        # The former well location no longer provides any resource.
        state.roverAction(RoverMap.mapToWorld((280,295)))
        self.assertEqual(state.cargoIce,0)
