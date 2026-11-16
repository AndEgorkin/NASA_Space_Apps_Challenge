import os
os.environ['SDL_VIDEODRIVER']='dummy'
os.environ['SDL_AUDIODRIVER']='dummy'
import math
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import pygame as pg
from lib.AssetManager import AssetManager
from lib.GameSettings import GameSettings
from lib.SettingsMenu import SettingsMenu
from lib.MainMenu import MainMenu
from lib.Survival import Survival
from lib.EnvironmentManager import EnvironmentManager
from objects.Rover import Rover


class SettingsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pg.init();cls.screen=pg.display.set_mode((1200,830));AssetManager.init()

    def setUp(self):
        self.previous=GameSettings.current()

    def tearDown(self):
        GameSettings.apply(self.previous)

    def testChangesReachSimulationAndPreserveConsumedSupplyTime(self):
        state=Survival();state.update(120)
        values=GameSettings.current()
        values.update(oxygenMinutes=45,provisionsMinutes=30,leakTemperature=-3,leakRange=18,stormChance=40,flareChance=60,leakChance=25)
        GameSettings.apply(values,state)
        self.assertEqual(state.oxygen,45*60-120)
        self.assertAlmostEqual(state.food,100-120/(30*60)*100)
        self.assertEqual(Rover.energyLeakTemperatureC,-3)
        self.assertEqual(Rover.energyLeakTemperatureRangeC,18)
        self.assertAlmostEqual(EnvironmentManager.stormChance,0.4)
        self.assertAlmostEqual(EnvironmentManager.solarFlareChance,0.6)
        self.assertAlmostEqual(1-math.exp(-Rover.energyLeakEventRate*20),0.25)
        self.assertEqual(Survival().oxygen,45*60)

    def testDisabledAndMaximumEventChances(self):
        values=GameSettings.current()
        values.update(stormChance=0,flareChance=0,leakChance=0)
        GameSettings.apply(values)
        self.assertEqual(Rover.energyLeakEventRate,0)
        self.assertEqual(EnvironmentManager.stormChance,0)
        self.assertEqual(EnvironmentManager.solarFlareChance,0)
        values['leakChance']=100;GameSettings.apply(values)
        self.assertTrue(math.isfinite(Rover.energyLeakEventRate))
        self.assertAlmostEqual(GameSettings.current()['leakChance'],100)

    def testDefaultButtonDraftAndApply(self):
        values=GameSettings.current();values['oxygenMinutes']=60
        GameSettings.apply(values)
        menu=SettingsMenu(self.screen)
        menu.handleEvent(pg.event.Event(pg.MOUSEBUTTONDOWN,button=1,pos=menu.defaultsButton.center))
        self.assertEqual(menu.values,GameSettings.defaults)
        self.assertEqual(Survival.oxygenDuration,3600)
        result=menu.handleEvent(pg.event.Event(pg.MOUSEBUTTONDOWN,button=1,pos=menu.applyButton.center))
        self.assertEqual(result,'apply')
        for key,expected in GameSettings.defaults.items():self.assertAlmostEqual(GameSettings.current()[key],expected)

    def testCancelDoesNotChangeSimulationAndSlidersClamp(self):
        menu=SettingsMenu(self.screen)
        menu.setFromMouse(0,-5000);self.assertEqual(menu.values['leakTemperature'],-80)
        menu.setFromMouse(0,5000);self.assertEqual(menu.values['leakTemperature'],50)
        menu.handleEvent(pg.event.Event(pg.KEYDOWN,key=pg.K_RIGHT))
        self.assertEqual(menu.values['leakTemperature'],50)
        self.assertEqual(menu.handleEvent(pg.event.Event(pg.KEYDOWN,key=pg.K_ESCAPE)),'cancel')
        self.assertEqual(GameSettings.current(),self.previous)

    def testValidationAndSupplyReduction(self):
        values=GameSettings.current();values['leakRange']=0
        GameSettings.apply(values)
        self.assertEqual(Rover.energyLeakTemperatureRangeC,1)
        values=GameSettings.current();values['oxygenMinutes']=float('nan')
        with self.assertRaises(ValueError):GameSettings.apply(values)
        state=Survival();state.update(120)
        values=GameSettings.current();values['oxygenMinutes']=1
        GameSettings.apply(values,state)
        self.assertEqual(state.oxygen,0)

    def testApplyZeroLeakClearsActiveLeakAndRenders(self):
        rover=SimpleNamespace(energyLeakActive=True,energyLeakTimeRemaining=12)
        menu=SettingsMenu(self.screen,Survival(),rover);menu.values['leakChance']=0
        menu.apply()
        self.assertFalse(rover.energyLeakActive)
        self.assertEqual(rover.energyLeakTimeRemaining,0)
        menu.render()

    def testSettingsOpensFromMenuByMouseAndKeyboard(self):
        menu=MainMenu(self.screen);menu.selected=2
        with patch('lib.MainMenu.SettingsMenu.run',return_value='quit') as opened:
            pg.event.clear();pg.event.post(pg.event.Event(pg.KEYDOWN,key=pg.K_RETURN))
            self.assertFalse(menu.run());opened.assert_called_once()
        rect=menu.buttons[2][1]
        with patch('lib.MainMenu.SettingsMenu.run',return_value='quit') as opened:
            pg.event.clear();pg.event.post(pg.event.Event(pg.MOUSEBUTTONDOWN,button=1,pos=rect.center))
            self.assertFalse(menu.run());opened.assert_called_once()

    def testEnergyConsumptionScalesActualDriveDrain(self):
        keys={pg.K_w:True,pg.K_s:False,pg.K_a:False,pg.K_d:False}
        def drain(percent):
            values=GameSettings.current();values['energyUse']=percent
            GameSettings.apply(values)
            rover=Rover();rover.charge=60
            try:
                with patch('pygame.key.get_pressed',return_value=keys), patch('random.random',return_value=1), patch.multiple(EnvironmentManager,nightBlend=0,surfaceTemperatureC=-23,stormIntensity=0), patch('objects.Chunk.Chunk.terrainHeight',return_value=0), patch('objects.Chunk.Chunk.terrainPixelHeight',return_value=0.42):
                    for _ in range(60):rover.update(1/60)
                return 60-rover.charge
            finally:rover.destroy()
        baseline=drain(100)
        self.assertGreater(baseline,0)
        self.assertAlmostEqual(drain(200),baseline*2)
        self.assertAlmostEqual(drain(0),0)

    def testRechargeSpeedAndProvisionsGainApplyToGameplay(self):
        values=GameSettings.current();values.update(rechargeRate=3.2,provisionsGain=12)
        GameSettings.apply(values)
        rover=Rover();rover.charge=50;rover.systemsOn=False;rover.stationaryTime=4
        try:
            with patch('random.random',return_value=1), patch.multiple(EnvironmentManager,nightBlend=0,surfaceTemperatureC=-23,stormIntensity=0), patch('objects.Chunk.Chunk.terrainHeight',return_value=0), patch('objects.Chunk.Chunk.terrainPixelHeight',return_value=0.42):
                rover.update(1/60)
            self.assertAlmostEqual(rover.charge,50+3.2/60)
        finally:rover.destroy()
        state=Survival();state.food=80;state.water=2
        state.waterPlants()
        self.assertEqual(state.food,92);self.assertEqual(state.water,1)
        state.waterPlants()
        self.assertEqual(state.food,100);self.assertEqual(state.water,0)
        self.assertIn('+8 provisions',state.message)

    def testScrollingAndKeyboardCanReachNewSliders(self):
        menu=SettingsMenu(self.screen)
        menu.handleEvent(pg.event.Event(pg.MOUSEWHEEL,y=-8))
        self.assertGreater(menu.scroll,0)
        self.assertTrue(menu.contentRect.collidepoint(menu.sliders[-1].center))
        menu.selected=len(GameSettings.specs)-2
        menu.handleEvent(pg.event.Event(pg.KEYDOWN,key=pg.K_DOWN))
        self.assertEqual(menu.selected,len(GameSettings.specs)-1)
        self.assertTrue(menu.contentRect.collidepoint(menu.sliders[-1].center))
        menu.handleEvent(pg.event.Event(pg.KEYDOWN,key=pg.K_RIGHT))
        self.assertEqual(menu.values['provisionsGain'],self.previous['provisionsGain']+1)
        menu.render()
