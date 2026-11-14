import pygame as pg
from lib.AssetManager import AssetManager

class Main:
    pg.init()
    pg.mixer.init()
    AssetManager.init()
    
    SCREEN = pg.display.set_mode((1200, 830))
    CLOCK = pg.time.Clock()
    pg.display.set_caption('Caption')
    
    isRunning = True
    buffer = []

    @staticmethod
    def init():
        while Main.isRunning:
            Main.update(Main.buffer)
            Main.render(Main.buffer)

    @staticmethod
    def update(buffer):
        pass

    @staticmethod
    def render(buffer):
        Main.SCREEN.fill('#000000');

        pg.display.flip();
        Main.CLOCK.tick(60);

if __name__ == '__main__':
    Main.init() # Точка входа в программу