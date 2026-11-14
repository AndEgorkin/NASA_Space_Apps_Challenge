import pygame as pg

class Texture:
    IDS = []
    
    def __init__(self, id, coords, rotation, scale, texture, priority=0):
        if id in Texture.IDS:
            raise Exception('[ERROR] Идентификатор текстуры должен быть уникальным')
        Texture.IDS.append(id)
        self.id = id
        self.coords = list(coords)
        self.rotation = rotation
        self.scale = scale
        self.texture = texture
        self.priority = priority
        self._cachedFactor = None
        self._cachedScaledTexture = None

    def destroy(self):
        if self.id in Texture.IDS:
            Texture.IDS.remove(self.id)

    @staticmethod
    def screenToWorld(screenCoords, screenSize, offset=(0.0, 0.0)):
        screenWidth, screenHeight = screenSize
        factor = min(screenWidth / 1920, screenHeight / 1080)
        worldX = (screenCoords[0] - screenWidth / 2) / factor + offset[0]
        worldY = (screenHeight / 2 - screenCoords[1]) / factor + offset[1]
        return worldX, worldY

    @staticmethod
    def worldToScreen(worldCoords, screenSize, offset=(0.0, 0.0)):
        screenWidth, screenHeight = screenSize
        factor = min(screenWidth / 1920, screenHeight / 1080)
        screenX = screenWidth / 2 + (worldCoords[0] - offset[0]) * factor
        screenY = screenHeight / 2 - (worldCoords[1] - offset[1]) * factor
        return screenX, screenY

    def update(self, deltaTime=1.0 / 60.0):
        pass

    def render(self, screen, offset=(0.0, 0.0)):
        screenSize = screen.get_size()
        x, y = Texture.worldToScreen(self.coords, screenSize, offset)
        factor = min(screenSize[0] / 1920, screenSize[1] / 1080)

        if self.rotation == 0.0:
            if self._cachedFactor != factor or self._cachedScaledTexture is None:
                self._cachedFactor = factor
                self._cachedScaledTexture = pg.transform.scale_by(
                    self.texture,
                    self.scale * factor
                )
            texture = self._cachedScaledTexture
        else:
            texture = pg.transform.scale_by(
                self.texture,
                self.scale * factor
            )
            texture = pg.transform.rotate(texture, self.rotation)

        rect = texture.get_rect(center=(x, y))
        screen.blit(texture, rect)
