import pygame as pg

class Texture:
    def __init__(self, coords, rotation, scale, texture, priority=0):
        self.coords = coords
        self.rotation = rotation
        self.scale = scale
        self.texture = texture
        self.priority = priority

    def update(self):
        pass

    def render(self, screen):
        screen_width, screen_height = screen.get_size()

        factor = min(screen_width / 1920, screen_height / 1080)

        x = screen_width / 2 + self.coords[0] * factor
        y = screen_height / 2 - self.coords[1] * factor

        texture = pg.transform.rotozoom(
            self.texture,
            self.rotation,
            self.scale * factor
        )

        rect = texture.get_rect(center=(x, y))
        screen.blit(texture, rect)