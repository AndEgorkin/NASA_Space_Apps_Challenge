import pygame as pg

from lib.EnvironmentManager import EnvironmentManager
from lib.AssetManager import AssetManager
from lib.BaseLocation import BaseLocation
from lib.MainMenu import MainMenu
from lib.RoverMap import RoverMap
from lib.RoverSave import RoverSave
from lib.Survival import Survival
from lib.Missions import Missions
from scenes.MarsSurface import MarsSurface

class Main:
    screen = None
    clock = None
    buffer = []
    camera = None
    rover = None
    isRunning = True

    @classmethod
    def run(cls):
        pg.init()
        pg.mixer.init()

        cls.screen = pg.display.set_mode((1200, 830))
        AssetManager.init()
        cls.clock = pg.time.Clock()
        cls.buffer = []
        cls.camera = None
        cls.rover = None
        cls.isRunning = True
        pg.display.set_caption('The Mars mission')

        EnvironmentManager.reset()
        cls.base = BaseLocation(cls.screen)
        cls.roverMap = RoverMap()
        cls.mapOpen = False
        cls.saveElapsed = 0.0
        cls.survival = Survival()
        cls.missions = Missions()
        cls.survivalTicks = pg.time.get_ticks()
        cls.scene = 'menu'
        try:
            while cls.isRunning:
                if cls.scene not in ('menu', 'depleted', 'won', 'signalLost'):
                    now = pg.time.get_ticks()
                    cls.survival.update((now - cls.survivalTicks) / 1000.0)
                    cls.survivalTicks = now
                    ending = cls.missions.ending(cls.survival)
                    if ending is not None:
                        cls.scene = ending
                    elif cls.rover is not None and cls.rover.gameOver:
                        cls.scene = 'signalLost'
                if cls.scene == 'menu':
                    if not MainMenu(cls.screen).run():
                        break
                    cls.scene = 'base'
                    cls.survivalTicks = pg.time.get_ticks()
                    cls.clock.tick()
                elif cls.scene in ('depleted', 'won', 'signalLost'):
                    cls.showEnding()
                elif cls.scene == 'base':
                    deltaTime = cls.clock.tick(60) / 1000.0
                    for event in pg.event.get():
                        action = cls.base.handleEvent(event)
                        if action == 'quit':
                            cls.isRunning = False
                            break
                        if action == 'menu':
                            cls.scene = 'menu'
                            break
                        if action == 'sleep':
                            cls.sleepAtBase()
                            break
                        if action == 'water':
                            cls.survival.waterPlants()
                        if action == 'rover':
                            if cls.missions.analyseAtBase(cls.survival, cls.rover.coords if cls.rover else RoverMap.spawnCoords):
                                break
                            cls.startRover()
                            break
                    if cls.isRunning and cls.scene == 'base':
                        cls.base.update(deltaTime)
                        hint = 'E: water plants (+provisions)' if cls.base.canWaterPlants() else ''
                        if cls.base.canSleep():
                            hint = 'E: sleep until 09:00' if not EnvironmentManager.isDay else 'E: rest (night only)'
                        cls.base.render(hint)
                        cls.survival.render(cls.screen, compact=True)
                        cls.missions.renderStatus(cls.screen, (24,75))
                        pg.display.flip()
                else:
                    cls.tick()
        finally:
            RoverSave.save(cls.rover)
            pg.quit()

    @classmethod
    def sleepAtBase(cls):
        if not cls.base.canSleep():
            return
        skipped = EnvironmentManager.skipNight()
        if skipped <= 0:
            cls.survival.notify('It is daylight. You can sleep here at night.')
            return
        cls.survival.update(skipped)
        cls.base.isWalking = False
        cls.base.walkTime = 0.0
        cls.survival.notify('You slept until 09:00. Oxygen and provisions were consumed during sleep.')
        cls.survivalTicks = pg.time.get_ticks()
        ending = cls.missions.ending(cls.survival)
        if ending is not None:
            cls.scene = ending

    @classmethod
    def showEnding(cls):
        if cls.scene == 'won':
            reason = 'All 8 missions complete. Rescue has arrived: you are going home!'
        elif cls.scene == 'signalLost':
            reason = 'Rover signal lost. Mission failed.'
        else:
            reason = 'Oxygen depleted. Mission failed.' if cls.survival.oxygen <= 0 else 'Provisions depleted. Mission failed.'
        for event in pg.event.get():
            if event.type == pg.QUIT:
                cls.isRunning = False
            elif event.type == pg.KEYDOWN and event.key == pg.K_RETURN:
                cls.survival = Survival()
                cls.missions = Missions()
                cls.mapOpen = False
                if cls.rover is not None:
                    cls.surface.reset()
                cls.base = BaseLocation(cls.screen)
                cls.scene = 'base'
                cls.survivalTicks = pg.time.get_ticks()
        cls.screen.fill('#101823')
        label = pg.font.Font(None, 30).render(reason, True, 'white')
        cls.screen.blit(label, label.get_rect(center=cls.screen.get_rect().center))
        prompt = pg.font.Font(None, 28).render('Enter: new attempt', True, '#ffdc8a')
        cls.screen.blit(prompt, prompt.get_rect(center=(cls.screen.get_width()//2, cls.screen.get_height()//2+50)))
        pg.display.flip()
        cls.clock.tick(60)

    @classmethod
    def startRover(cls):
        if cls.rover is None:
            cls.surface = MarsSurface()
            cls.rover = cls.surface.rover
            cls.buffer = cls.surface.objects
            cls.camera = cls.surface.camera
        cls.mapOpen = False
        cls.scene = 'rover'
        cls.clock.tick()

    @classmethod
    def tick(cls):
        deltaTime = min(cls.clock.get_time() / 1000.0, 1.0 / 30.0)

        for event in pg.event.get():
            if event.type == pg.QUIT:
                cls.isRunning = False
                RoverSave.save(cls.rover)
                return
            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                if getattr(cls, 'mapOpen', False):
                    cls.mapOpen = False
                    continue
                RoverSave.save(cls.rover)
                cls.scene = 'base'
                return
            cls.surface.handleEvent(event)
            if event.type == pg.KEYDOWN and event.key == pg.K_m:
                cls.mapOpen = not cls.mapOpen
            if event.type == pg.KEYDOWN and event.key == pg.K_e and not cls.mapOpen and cls.rover.systemsOn and not cls.rover.gameOver:
                cls.survival.roverAction(cls.rover.coords)
                cls.missions.roverAction(cls.rover.coords, cls.survival)

        cls.surface.update(deltaTime, cls.screen.get_size(), controlsEnabled=not cls.mapOpen)
        if cls.mapOpen:
            cls.roverMap.render(cls.screen, cls.rover, cls.missions)
            cls.survival.render(cls.screen)
            cls.surface.renderMapStatus(cls.screen)
            pg.display.flip()
            cls.clock.tick(60)
            return
        cls.saveElapsed += deltaTime
        if cls.saveElapsed >= 5:
            RoverSave.save(cls.rover)
            cls.saveElapsed = 0.0
        cls.surface.render(cls.screen, cls.missions)
        hint = pg.font.Font(None, 24).render('M: map  |  Esc: base', True, 'white')
        cls.screen.blit(hint, (16, 16))

        actionHint = cls.missions.hint(cls.rover.coords) or cls.survival.roverHint(cls.rover.coords)
        cls.survival.render(cls.screen, actionHint)
        cls.missions.renderStatus(cls.screen)
        pg.display.flip()
        cls.clock.tick(60)

if __name__ == '__main__':
    Main.run()
