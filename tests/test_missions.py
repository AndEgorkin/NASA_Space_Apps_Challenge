import os
os.environ['SDL_VIDEODRIVER']='dummy'
os.environ['SDL_AUDIODRIVER']='dummy'
import unittest
import pygame as pg
from lib.Missions import Missions
from lib.Survival import Survival
from lib.RoverMap import RoverMap


class MissionTests(unittest.TestCase):
    def setUp(self):
        pg.font.init()
        self.missions=Missions()
        self.survival=Survival()

    def pressAt(self, index):
        coords=RoverMap.mapToWorld(self.missions.target(index))
        self.missions.roverAction(coords,self.survival)
        if index == 0 and self.missions.manipulator.active:
            arm=self.missions.manipulator
            arm.tip.update(arm.sample)
            self.missions.manipulatorAction(coords,self.survival)
            arm.tip.update(arm.tray)
            self.missions.manipulatorAction(coords,self.survival)

    def testCompleteAllAndEvacuate(self):
        for i in range(7):
            for _ in self.missions.definitions[i][3]:
                self.pressAt(i)
        self.assertEqual(self.missions.completed,6)
        self.assertFalse(self.missions.analysed)
        self.missions.analyseAtBase(self.survival,(10000,10000))
        self.assertFalse(self.missions.analysed)
        self.missions.analyseAtBase(self.survival,(0,0))
        self.assertEqual(self.missions.completed,7)
        self.pressAt(7)
        self.assertFalse(self.missions.allDone)
        self.survival.roverAction(RoverMap.mapToWorld(RoverMap.icePixel))
        self.survival.roverAction((0,0))
        self.survival.food=80
        self.survival.waterPlants()
        self.pressAt(7)
        self.assertTrue(self.missions.allDone)
        self.assertEqual(self.missions.ending(self.survival),'won')
        self.survival.oxygen=0
        self.assertEqual(self.missions.ending(self.survival),'depleted')

    def testRouteRequiresAllLocationsAndNoRemoteCompletion(self):
        self.missions.roverAction((50000,50000),self.survival)
        self.assertEqual(self.missions.completed,0)
        first=RoverMap.mapToWorld(self.missions.target(6))
        self.pressAt(6)
        self.missions.roverAction(first,self.survival)
        self.assertEqual(self.missions.progress[6],1)
        for _ in range(len(self.missions.definitions[6][3])-1):self.pressAt(6)
        self.assertTrue(self.missions.done(6))
        self.pressAt(6)
        self.assertEqual(self.missions.progress[6],len(self.missions.definitions[6][3]))

    def testOxygenExpiryWithoutCompletionLoses(self):
        self.survival.update(Survival.oxygenDuration)
        self.assertEqual(self.missions.ending(self.survival),'depleted')

    def testUndeliveredSampleDoesNotBlockRoverControl(self):
        self.pressAt(0);self.pressAt(0)
        # False lets the terminal continue into Main.startRover instead of
        # consuming E on a failed analysis and trapping the player on base.
        self.assertFalse(self.missions.analyseAtBase(self.survival,(10000,10000)))
        self.assertFalse(self.missions.done(0))
        self.assertTrue(self.missions.analyseAtBase(self.survival,RoverMap.baseCoords))
        self.assertTrue(self.missions.done(0))
        self.assertFalse(self.missions.analyseAtBase(self.survival,RoverMap.baseCoords))
