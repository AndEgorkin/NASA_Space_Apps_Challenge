import pygame as pg

from lib.AssetManager import AssetManager
from lib.BaseLocation import BaseLocation
from lib.Camera import Camera
from lib.MainMenu import MainMenu
from lib.EnvironmentManager import EnvironmentManager
from lib.TerrainManager import TerrainManager
from objects.Rover import Rover

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
        AssetManager.init()

        cls.screen = pg.display.set_mode((1200, 830))
        cls.clock = pg.time.Clock()
        cls.buffer = []
        cls.camera = None
        cls.rover = None
        cls.isRunning = True
        pg.display.set_caption('NASA Competition Program')

        cls.base = BaseLocation(cls.screen)
        cls.scene = 'menu'
        try:
            while cls.isRunning:
                if cls.scene == 'menu':
                    if not MainMenu(cls.screen).run():
                        break
                    cls.scene = 'base'
                    cls.clock.tick()
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
                        if action == 'rover':
                            cls.startRover()
                            break
                    if cls.isRunning and cls.scene == 'base':
                        cls.base.update(deltaTime)
                        cls.base.render()
                        pg.display.flip()
                else:
                    cls.tick()
        finally:
            pg.quit()

    @classmethod
    def startRover(cls):
        if cls.rover is None:
            cls.rover = Rover()
            cls.camera = Camera(cls.rover.coords)
            EnvironmentManager.dustTexture = AssetManager.get('assets.texture.dust')
            cls.buffer.append(cls.rover)
            TerrainManager.loadInitialChunks(cls.rover.coords, cls.buffer)
        cls.scene = 'rover'
        cls.clock.tick()

    @classmethod
    def tick(cls):
        deltaTime = min(cls.clock.get_time() / 1000.0, 1.0 / 30.0)

        for event in pg.event.get():
            if event.type == pg.QUIT:
                cls.isRunning = False
                return
            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                cls.scene = 'base'
                return

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

        pg.display.flip()
        cls.clock.tick(60)

if __name__ == '__main__':
    Main.run()
