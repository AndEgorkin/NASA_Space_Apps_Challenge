import os
os.environ['SDL_VIDEODRIVER']='dummy'
os.environ['SDL_AUDIODRIVER']='dummy'
import unittest
from unittest.mock import patch
import pygame as pg
from lib.AssetManager import AssetManager
from lib.EnvironmentManager import EnvironmentManager
from lib.RoverMap import RoverMap
from objects.BoundingBox import BoundingBox
from objects.Rover import Rover
from objects.Texture import Texture
from scenes.MarsSurface import MarsSurface


class RoverSystemsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pg.init();cls.screen=pg.display.set_mode((1200,830));AssetManager.init()

    def setUp(self):
        self.rover=Rover()
        self.environment=patch.multiple(EnvironmentManager,
            nightBlend=0.0, surfaceTemperatureC=-23.0, stormIntensity=0.0,
            dayNightTimer=0.0, stormChance=0.0, solarFlareChance=0.0,
            sandstormEnabled=False, sandstormOnStart=False, solarFlareOnStart=False,
            solarFlareActive=False, solarFlarePixels=[], solarFlareElapsed=0.0,
            solarFlareRecoveryActive=False, stormCheckTimer=0.0, solarFlareCheckTimer=0.0)
        self.environment.start()
        self.keys={key:False for key in (pg.K_w,pg.K_s,pg.K_a,pg.K_d)}
        self.keyboard=patch('pygame.key.get_pressed', return_value=self.keys)
        self.keyboard.start()
        self.random=patch('random.random', return_value=1.0);self.random.start()

    def tearDown(self):
        self.rover.destroy();self.environment.stop();self.keyboard.stop();self.random.stop()
        Texture.zoomFactor=1.0

    def driveForSecond(self):
        self.keys[pg.K_w]=True
        for _ in range(60):self.rover.update(1/60)

    def testColdNightCostsMoreThanDay(self):
        self.driveForSecond();dayCost=100-self.rover.charge
        self.rover.resetSystems();EnvironmentManager.nightBlend=1
        EnvironmentManager.surfaceTemperatureC=-80
        self.driveForSecond()
        self.assertGreater(100-self.rover.charge,dayCost)

    def testPowerBoundsSystemsOffAndCharging(self):
        self.rover.adjustPower(100);self.assertEqual(self.rover.powerPercent,200)
        self.rover.adjustPower(-100);self.assertEqual(self.rover.powerPercent,0)
        self.rover.resetSystems();self.rover.systemsOn=False
        self.rover.charge=60;self.keys[pg.K_w]=True
        for _ in range(240):self.rover.update(1/60)
        self.assertGreater(self.rover.charge,60)
        self.assertTrue(self.rover.isCharging)
        self.rover.charge=60;self.rover.stationaryTime=5
        EnvironmentManager.nightBlend=1
        self.rover.update(1/60)
        self.assertEqual(self.rover.charge,60)
        self.assertFalse(self.rover.isCharging)

    def testLeakAndBatteryFailure(self):
        EnvironmentManager.nightBlend=1.0
        self.rover.energyLeakTimeRemaining=10;self.rover.energyLeakActive=True
        self.rover.charge=0.001
        self.rover.update(1/60)
        self.assertTrue(self.rover.gameOver)

    def testDaylightCannotStartOrContinueLeak(self):
        self.rover.engineTemperatureC=-20
        self.rover.charge=60
        for blend in (0.0,0.2,0.49):
            EnvironmentManager.nightBlend=blend
            self.rover.energyLeakActive=True
            self.rover.energyLeakTimeRemaining=20
            with patch('random.random',return_value=0):
                self.rover.update(1/60)
                self.assertFalse(self.rover.energyLeakActive)
                self.assertEqual(self.rover.energyLeakTimeRemaining,0)
                self.assertEqual(self.rover.charge,60)
                self.rover.update(1/60)
                self.assertFalse(self.rover.energyLeakActive)

    def testColdNightLeakStopsAtDaylight(self):
        self.rover.engineTemperatureC=-20
        self.rover.charge=60
        EnvironmentManager.nightBlend=1
        with patch('random.random',return_value=0):self.rover.update(1/60)
        self.assertTrue(self.rover.energyLeakActive)
        self.assertLess(self.rover.charge,60)
        charge=self.rover.charge
        EnvironmentManager.nightBlend=0.49
        self.rover.update(1/60)
        self.assertFalse(self.rover.energyLeakActive)
        self.assertEqual(self.rover.charge,charge)

    def testNasaSolAndTemperatureProfile(self):
        EnvironmentManager.update(EnvironmentManager.solDuration/2,self.screen.get_size(),self.rover)
        self.assertAlmostEqual(EnvironmentManager.localTimeHour,0)
        self.assertEqual(EnvironmentManager.surfaceTemperatureC,-70)
        EnvironmentManager.update(EnvironmentManager.solDuration/2,self.screen.get_size(),self.rover)
        self.assertAlmostEqual(EnvironmentManager.localTimeHour,12)
        self.assertEqual(EnvironmentManager.surfaceTemperatureC,-30)
        self.assertEqual(min(EnvironmentManager.hourlySurfaceTemperaturesC),-80)
        self.assertEqual(max(EnvironmentManager.hourlySurfaceTemperaturesC),-23)

    def testFlareRecoverOrLose(self):
        EnvironmentManager._startSolarFlare(self.screen.get_size())
        self.rover.systemsOn=False
        EnvironmentManager.update(4,self.screen.get_size(),self.rover)
        self.assertFalse(EnvironmentManager.solarFlareActive)
        self.assertFalse(self.rover.gameOver)
        EnvironmentManager._startSolarFlare(self.screen.get_size())
        self.rover.systemsOn=True
        EnvironmentManager.update(8,self.screen.get_size(),self.rover)
        self.assertTrue(self.rover.gameOver)

    def testStationCollisionZoomAndFreshSpawn(self):
        self.rover.destroy()
        with patch('lib.TerrainManager.TerrainManager.loadInitialChunks'):
            scene=MarsSurface()
        try:
            self.assertEqual(tuple(scene.rover.coords),RoverMap.spawnCoords)
            box=BoundingBox(scene.rover.coords,100,120)
            self.assertFalse(any(obstacle.intersects(box) for obstacle in scene.rover.boundingBoxes))
            scene.rover.coords[:]=scene.rover.boundingBoxes[0].coords
            scene.rover.velocity=50
            scene.rover.update(1/60)
            self.assertEqual(scene.rover.velocity,0)
            scene.rover.systemsOn=False;scene.updateCameraZoom(0.45)
            self.assertAlmostEqual(Texture.zoomFactor,1.6)
            scene.rover.systemsOn=True;scene.updateCameraZoom(0.45)
            self.assertAlmostEqual(Texture.zoomFactor,1)
            scene.render(self.screen, __import__('lib.Missions',fromlist=['Missions']).Missions())
        finally:
            for obj in scene.objects:obj.destroy()
