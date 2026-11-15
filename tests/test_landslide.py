import os
os.environ['SDL_VIDEODRIVER']='dummy'
os.environ['SDL_AUDIODRIVER']='dummy'
import unittest
from types import SimpleNamespace
import pygame as pg
from lib.Missions import Missions
from lib.Survival import Survival
from lib.RoverMap import RoverMap


class LandslideTests(unittest.TestCase):
    def setUp(self):
        pg.init();self.screen=pg.display.set_mode((1200,830))
        self.missions=Missions();self.survival=Survival()
        self.coords=RoverMap.mapToWorld(self.missions.target(1))
        self.missions.roverAction(self.coords,self.survival)
        self.survey=self.missions.landslideSurvey

    def event(self,event):
        self.missions.handleInteractionEvent(event,self.coords,self.survival,self.screen.get_size())

    def click(self,point):
        self.event(pg.event.Event(pg.MOUSEBUTTONDOWN,button=1,pos=point))

    def key(self,key):
        self.event(pg.event.Event(pg.KEYDOWN,key=key))

    def markAll(self):
        field=self.survey.layout(self.screen.get_size())[1]
        for x,y in self.survey.clusters:self.click((field.x+x,field.y+y))

    def testMappingRequiresThreeDistinctClusters(self):
        self.key(pg.K_e)
        self.assertEqual(self.missions.progress[1],0)
        field=self.survey.layout(self.screen.get_size())[1]
        self.click((field.x+5,field.y+5))
        self.assertEqual(len(self.survey.marked),0)
        for _ in range(3):self.click((field.x+180,field.y+95))
        self.assertEqual(len(self.survey.marked),1)
        self.assertEqual(self.missions.progress[1],0)
        self.markAll()
        self.assertEqual(self.missions.progress[1],1)
        self.assertFalse(self.missions.done(1))

    def testWrongDirectionCannotCompleteButCorrectAnswerCan(self):
        self.markAll();self.key(pg.K_e)
        self.assertFalse(self.missions.done(1))
        self.key(pg.K_w);self.key(pg.K_e)
        self.assertFalse(self.missions.done(1))
        buttons=self.survey.layout(self.screen.get_size())[2]
        self.click(buttons[2].center);self.key(pg.K_e)
        self.assertTrue(self.missions.done(1))
        self.assertFalse(self.survey.active)
        self.missions.roverAction(self.coords,self.survival)
        self.assertEqual(self.missions.progress[1],2)

    def testCancelResumesMappedPhaseAndPowerLossCancels(self):
        self.markAll();self.missions.cancelInteraction()
        self.assertEqual(self.missions.progress[1],1)
        self.missions.roverAction(self.coords,self.survival)
        self.assertEqual(self.survey.phase,1)
        self.assertEqual(len(self.survey.marked),3)
        self.missions.updateInteractions(1/60,SimpleNamespace(coords=self.coords,gameOver=False,systemsOn=False),self.survival)
        self.assertFalse(self.survey.active)
        self.assertFalse(self.missions.done(1))

    def testRemoteCompletionBlockedAndSurveyRenders(self):
        self.survey.render(self.screen)
        self.markAll();self.survey.render(self.screen)
        self.missions.handleInteractionEvent(pg.event.Event(pg.KEYDOWN,key=pg.K_e),(50000,50000),self.survival,self.screen.get_size())
        self.assertFalse(self.survey.active)
        self.assertFalse(self.missions.done(1))
