import pygame as pg

from lib.AssetManager import AssetManager
from lib.Texture import Texture
from lib.Camera import Camera
from lib.TerrainManager import TerrainManager
from Rover import Rover

class Main:
    pg.init()
    pg.mixer.init()
    AssetManager.init()
    
    SCREEN = pg.display.set_mode((1200, 830))
    CLOCK = pg.time.Clock()
    pg.display.set_caption('NASA Competition Program')

    buffer = []
    scheduler = []
    camera = None
    rover = None
    terrainManager = None
    
    isRunning = True

    @staticmethod
    def init():
        Main.rover = Rover()
        Main.camera = Camera(Main.rover.coords)
        Main.terrainManager = TerrainManager(chunkSize=1200)

        Main.buffer.append(Main.rover)
        Main.terrainManager.init(Main.rover.coords, Main.buffer)

        while Main.isRunning:
            Main.tick(Main.buffer)

    @staticmethod
    def tick(buffer):
        deltaTime = min(Main.CLOCK.get_time() / 1000.0, 1.0 / 30.0)
        screen = Main.SCREEN
        mouse = pg.mouse.get_pos()

        for event in pg.event.get():
            if event.type == pg.QUIT:
                Main.isRunning = False

        if Main.terrainManager and Main.rover:
            Main.terrainManager.update(Main.rover.coords, Main.buffer)

        Main.buffer.sort(
            key=lambda texture: texture.priority
        )

        screen.fill('#000000')
        for texture in Main.buffer:
            texture.update(deltaTime)

        if Main.camera and Main.rover:
            Main.camera.follow(Main.rover.coords)

        cameraOffset = Main.camera.coords if Main.camera else (0.0, 0.0)

        for texture in Main.buffer:
            texture.render(screen, cameraOffset)

        pg.display.flip()
        Main.CLOCK.tick(60)

if __name__ == '__main__':
    Main.init()