import pygame as pg
from lib.AssetManager import AssetManager
from lib.Texture import Texture

class Main:
    pg.init()
    pg.mixer.init()
    AssetManager.init()
    
    SCREEN = pg.display.set_mode((1200, 830))
    CLOCK = pg.time.Clock()
    pg.display.set_caption('Caption')

    buffer = []
    scheduler = []
    
    isRunning = True
    @staticmethod
    def init():
        Main.buffer.append(Texture(
            (0,0), 10, 1, 
            AssetManager.get('assets.texture.test'),
            priority=0
        ))
        while Main.isRunning:
            Main.tick(Main.buffer)

    @staticmethod
    def tick(buffer):
        screen = Main.SCREEN
        mouse = pg.mouse.get_pos()

        for event in pg.event.get():
            if event.type == pg.QUIT:
                Main.isRunning = False

        Main.buffer.sort(
            key=lambda texture: texture.priority, reverse=True
        )

        screen.fill('#000000')
        for texture in Main.buffer:
            texture.update()
            texture.render(screen)

        pg.display.flip()
        Main.CLOCK.tick(60)

if __name__ == '__main__':
    Main.init() # Точка входа в программу