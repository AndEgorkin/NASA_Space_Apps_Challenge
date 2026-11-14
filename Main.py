import pygame as pg

from lib.AssetManager import AssetManager
from lib.BaseLocation import BaseLocation
from lib.Camera import Camera
from lib.MainMenu import MainMenu
from lib.EnvironmentManager import EnvironmentManager
from lib.TerrainManager import TerrainManager
from objects.Rover import Rover
from objects.Texture import Texture
from lib.RoverMap import RoverMap
from lib.RoverSave import RoverSave
from lib.Survival import Survival
from objects.WaterWell import WaterWell

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
        pg.display.set_caption('NASA Competition Program')

        cls.base = BaseLocation(cls.screen)
        cls.roverMap = RoverMap()
        cls.mapOpen = False
        cls.saveElapsed = 0.0
        cls.survival = Survival()
        cls.survivalTicks = pg.time.get_ticks()
        cls.scene = 'menu'
        try:
            while cls.isRunning:
                if cls.scene != 'menu':
                    now = pg.time.get_ticks()
                    cls.survival.update((now - cls.survivalTicks) / 1000.0)
                    cls.survivalTicks = now
                    if cls.survival.depleted:
                        cls.scene = 'depleted'
                if cls.scene == 'menu':
                    if not MainMenu(cls.screen).run():
                        break
                    cls.scene = 'base'
                    cls.survivalTicks = pg.time.get_ticks()
                    cls.clock.tick()
                elif cls.scene == 'depleted':
                    cls.showDepleted()
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
                        if action == 'water':
                            cls.survival.waterPlants()
                        if action == 'rover':
                            cls.startRover()
                            break
                    if cls.isRunning and cls.scene == 'base':
                        cls.base.update(deltaTime)
                        cls.base.render()
                        hint = 'E: water plants (+food)' if cls.base.canWaterPlants() else ''
                        cls.survival.render(cls.screen, hint)
                        pg.display.flip()
                else:
                    cls.tick()
        finally:
            RoverSave.save(cls.rover)
            pg.quit()

    @classmethod
    def showDepleted(cls):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                cls.isRunning = False
            elif event.type == pg.KEYDOWN and event.key == pg.K_RETURN:
                cls.survival = Survival()
                cls.base = BaseLocation(cls.screen)
                cls.scene = 'base'
                cls.survivalTicks = pg.time.get_ticks()
        cls.screen.fill('#101823')
        reason = 'Oxygen depleted' if cls.survival.oxygen <= 0 else 'Food depleted'
        label = pg.font.Font(None, 40).render(reason + ' - Enter: retry', True, 'white')
        cls.screen.blit(label, label.get_rect(center=cls.screen.get_rect().center))
        pg.display.flip()
        cls.clock.tick(60)

    @classmethod
    def startRover(cls):
        if cls.rover is None:
            cls.rover = Rover()
            cls.buffer.append(WaterWell())
            RoverSave.load(cls.rover, RoverMap.spawnCoords)
            cls.buffer.append(Texture('base.exterior', RoverMap.baseCoords, 0, 0.6,
                                      AssetManager.get('assets.texture.base-exterior'), 50))
            cls.camera = Camera(cls.rover.coords)
            EnvironmentManager.dustTexture = AssetManager.get('assets.texture.dust')
            cls.buffer.append(cls.rover)
            TerrainManager.loadInitialChunks(cls.rover.coords, cls.buffer)
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
            if event.type == pg.KEYDOWN and event.key == pg.K_m:
                cls.mapOpen = not cls.mapOpen
            if event.type == pg.KEYDOWN and event.key == pg.K_e and not cls.mapOpen:
                cls.survival.roverAction(cls.rover.coords)

        if cls.mapOpen:
            cls.roverMap.render(cls.screen, cls.rover)
            cls.survival.render(cls.screen)
            pg.display.flip()
            cls.clock.tick(60)
            return
        cls.saveElapsed += deltaTime
        if cls.saveElapsed >= 5:
            RoverSave.save(cls.rover)
            cls.saveElapsed = 0.0
        TerrainManager.update(cls.rover.coords, cls.buffer)
        screenSize = cls.screen.get_size()
        EnvironmentManager.update(deltaTime, screenSize)
        EnvironmentManager.applyWeather(cls.rover, deltaTime)

        cls.buffer.sort(key=lambda texture: texture.priority)

        cls.screen.fill('#000000')
        for texture in cls.buffer:
            texture.update(deltaTime)

        cls.camera.follow(cls.rover.coords)
        cameraOffset = EnvironmentManager.getCameraOffset(
            cls.camera.coords,
            screenSize
        )

        for texture in cls.buffer:
            texture.render(cls.screen, cameraOffset)

        EnvironmentManager.render(cls.screen)
        hint = pg.font.Font(None, 24).render('M: map  |  Esc: base', True, 'white')
        cls.screen.blit(hint, (16, 16))

        cls.survival.render(cls.screen, cls.survival.roverHint(cls.rover.coords))
        pg.display.flip()
        cls.clock.tick(60)

if __name__ == '__main__':
    Main.run()
