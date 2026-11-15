import os
os.environ['SDL_VIDEODRIVER']='dummy'
os.environ['SDL_AUDIODRIVER']='dummy'
import unittest
import pygame as pg
from Main import Main
from lib.AssetManager import AssetManager
from lib.BaseLocation import BaseLocation
from lib.EnvironmentManager import EnvironmentManager
from lib.Missions import Missions
from lib.Survival import Survival


class SleepTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pg.init();cls.screen=pg.display.set_mode((1200,830));AssetManager.init()

    def setUp(self):
        EnvironmentManager.reset()
        Main.base=BaseLocation(self.screen)
        Main.base.room='crew';Main.base.position.update(120,80)
        Main.survival=Survival();Main.missions=Missions();Main.scene='base'

    def tearDown(self):
        EnvironmentManager.reset()

    def setHour(self, hour):
        EnvironmentManager.dayNightTimer=((hour-12)%24)/24*EnvironmentManager.solDuration
        EnvironmentManager._advanceClock(0)

    def testBedReachableAndInteractionRequiresProximity(self):
        self.assertFalse(Main.base._blocked(Main.base.position))
        self.assertTrue(Main.base.canSleep())
        event=pg.event.Event(pg.KEYDOWN,key=pg.K_e)
        self.assertEqual(Main.base.handleEvent(event),'sleep')
        Main.base.position.update(120,120)
        self.assertIsNone(Main.base.handleEvent(event))
        self.setHour(22);Main.sleepAtBase()
        self.assertEqual(EnvironmentManager.localTimeHour,22)

    def testNightSkipsToMorningAndConsumesResources(self):
        self.setHour(22)
        Main.sleepAtBase()
        skipped=11/24*EnvironmentManager.solDuration
        self.assertAlmostEqual(EnvironmentManager.localTimeHour,9)
        self.assertEqual(EnvironmentManager.displayedLocalTimeHour,9)
        self.assertTrue(EnvironmentManager.isDay)
        self.assertAlmostEqual(Main.survival.oxygen,Survival.oxygenDuration-skipped)
        self.assertAlmostEqual(Main.survival.food,100-skipped*100/900)
        self.assertEqual(Main.base.room,'crew')

    def testDaytimeDoesNotSkipAndLowOxygenLoses(self):
        Main.sleepAtBase()
        self.assertEqual(EnvironmentManager.localTimeHour,12)
        self.assertEqual(Main.survival.oxygen,Survival.oxygenDuration)
        self.setHour(2);Main.survival.oxygen=1
        Main.sleepAtBase()
        self.assertEqual(Main.scene,'depleted')
        self.assertEqual(Main.survival.oxygen,0)

    def testClockAdvancesWithoutRoverAtBase(self):
        from unittest.mock import patch
        with patch('random.random',return_value=1):
            EnvironmentManager.update(30,self.screen.get_size())
        self.assertAlmostEqual(EnvironmentManager.localTimeHour,13.2)
        self.assertIn('13:12',EnvironmentManager.clockLabel())
