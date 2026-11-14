from pathlib import Path

import pygame as pg


class MainMenu:
    def __init__(self, screen):
        self.screen = screen
        self.assetDirectory = Path(__file__).resolve().parent.parent / 'assets' / 'menu'
        self.background = self._loadImage('background.png')
        self.buttons = []
        self.font = pg.font.Font(None, 48)
        for index, name in enumerate(('play', 'load', 'settings', 'quit')):
            self.buttons.append((name, pg.Rect(32, 32 + index * 120, 200, 100),
                                 self._loadImage(name + '.png')))

    def _loadImage(self, filename):
        path = self.assetDirectory / filename
        if path.is_file():
            return pg.image.load(str(path)).convert_alpha()
        return None

    def run(self):
        clock = pg.time.Clock()
        while True:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    return False
                if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                    for name, rect, image in self.buttons:
                        if rect.collidepoint(event.pos):
                            if name == 'play':
                                return True
                            if name == 'quit':
                                return False
            self._render()
            pg.display.flip()
            clock.tick(60)

    def _render(self):
        self.screen.fill('#00b4df')
        if self.background is not None:
            # Cover the window without distorting the artwork; preserve its right edge.
            width, height = self.screen.get_size()
            scale = max(width / self.background.get_width(),
                        height / self.background.get_height())
            size = (round(self.background.get_width() * scale),
                    round(self.background.get_height() * scale))
            background = pg.transform.scale(self.background, size)
            self.screen.blit(background, (width - size[0], (height - size[1]) // 2))
        for name, rect, image in self.buttons:
            if image is not None:
                self.screen.blit(pg.transform.scale(image, rect.size), rect)
            else:
                pg.draw.rect(self.screen, '#00b4df', rect, border_radius=24)
                pg.draw.rect(self.screen, '#003e60', rect, 2, border_radius=24)
                label = self.font.render(name.upper(), True, '#003e60')
                self.screen.blit(label, label.get_rect(center=rect.center))
