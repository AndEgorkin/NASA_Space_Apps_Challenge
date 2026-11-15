import pygame as pg

from lib.AssetManager import AssetManager


class Main:
    @staticmethod
    def run():
        pg.init()
        try:
            pg.mixer.init()
            AssetManager.init()
            screen = pg.display.set_mode((1200, 830))
            pg.display.set_caption('NASA Competition Program')
            clock = pg.time.Clock()
            from objects.Rover import Rover
            from scenes.MarsSurface import MarsSurface

            isRunning = True

            while isRunning:
                deltaTime = min(clock.get_time() / 1000.0, 1.0 / 30.0)
                for event in pg.event.get():
                    if event.type == pg.QUIT:
                        isRunning = False
                    elif (
                        event.type == pg.MOUSEWHEEL
                        and Rover.systemsOn
                        and not Rover.gameOver
                    ):
                        Rover.adjustPower(event.y)
                    elif (
                        event.type == pg.MOUSEBUTTONDOWN
                        and event.button == 1
                        and not Rover.gameOver
                        and Rover.systemsButtonRect.collidepoint(event.pos)
                    ):
                        Rover.systemsOn = not Rover.systemsOn

                if Rover.charge <= 0.0:
                    Rover.gameOver = True
                if not Rover.gameOver:
                    MarsSurface.updateCameraZoom(deltaTime)
                if not Rover.gameOver:
                    MarsSurface.update(deltaTime, screen.get_size())
                    if Rover.charge <= 0.0:
                        Rover.gameOver = True
                MarsSurface.render(screen)
                if Rover.gameOver:
                    Rover.renderGameOver(screen)
                pg.display.flip()
                clock.tick(60)
        finally:
            pg.quit()


if __name__ == '__main__':
    Main.run()
