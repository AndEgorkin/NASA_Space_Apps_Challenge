import pygame as pg


class Interface:
    background = '#09121c'
    panelColor = '#101e2b'
    border = '#2b4356'
    textColor = '#e9f1f4'
    muted = '#8ba3b4'
    accent = '#f7ad60'
    cyan = '#6ddacf'
    fonts = {}

    @classmethod
    def font(cls, size):
        if size not in cls.fonts:
            cls.fonts[size] = pg.font.Font(None, size)
        return cls.fonts[size]

    @classmethod
    def text(cls, screen, text, position, size=24, color=None):
        surface = cls.font(size).render(text, True, color or cls.textColor)
        screen.blit(surface, position)
        return surface.get_rect(topleft=position)

    @classmethod
    def panel(cls, screen, rect, color=None):
        pg.draw.rect(screen, color or cls.panelColor, rect, border_radius=10)
        pg.draw.rect(screen, cls.border, rect, 1, border_radius=10)

    @classmethod
    def key(cls, screen, label, position):
        rect = pg.Rect(position, (30, 28))
        pg.draw.rect(screen, cls.accent, rect, border_radius=5)
        text = cls.font(23).render(label, True, cls.background)
        screen.blit(text, text.get_rect(center=rect.center))
