import math

from lib.AssetManager import AssetManager
from lib.Camera import Camera
from lib.EnvironmentManager import EnvironmentManager
from lib.TerrainManager import TerrainManager
from objects.BoundingBox import BoundingBox
from objects.Rover import Rover
from objects.Texture import Texture


class MarsSurface:
    objects = []
    camera = Camera(Rover.coords)
    station = Texture(
        'station',
        (-400, 600),
        30,
        7.5,
        AssetManager.get('assets.texture.station')
    )
    objects = [Rover, station]
    EnvironmentManager.dustTexture = AssetManager.get('assets.texture.dust')
    zoomInFactor = 1.6
    zoomTransitionDuration = 0.45
    zoomTarget = 1.0
    zoomStart = 1.0
    zoomElapsed = zoomTransitionDuration

    textureWidth, textureHeight = station.texture.get_size()
    scale = station.scale
    rotation = math.radians(station.rotation)
    cosRotation = math.cos(rotation)
    sinRotation = math.sin(rotation)
    for left, top, right, bottom in (
        (0, 0, 80, 128),
        (80, 0, 128, 96)
    ):
        localX = ((left + right) / 2.0 - textureWidth / 2.0) * scale
        localY = (textureHeight / 2.0 - (top + bottom) / 2.0) * scale
        boxCoords = (
            station.coords[0] + cosRotation * localX - sinRotation * localY,
            station.coords[1] + sinRotation * localX + cosRotation * localY
        )
        Rover.boundingBoxes.append(BoundingBox(
            boxCoords,
            (right - left) * scale,
            (bottom - top) * scale,
            station.rotation
        ))

    del (
        textureWidth,
        textureHeight,
        scale,
        rotation,
        cosRotation,
        sinRotation,
        left,
        top,
        right,
        bottom,
        localX,
        localY,
        boxCoords
    )
    TerrainManager.loadInitialChunks(Rover.coords, objects)

    @classmethod
    def updateCameraZoom(cls, deltaTime):
        target = cls.zoomInFactor if not Rover.systemsOn else 1.0
        if target != cls.zoomTarget:
            cls.zoomTarget = target
            cls.zoomStart = Texture.zoomFactor
            cls.zoomElapsed = 0.0

        cls.zoomElapsed = min(
            cls.zoomTransitionDuration,
            cls.zoomElapsed + max(0.0, deltaTime)
        )
        progress = cls.zoomElapsed / cls.zoomTransitionDuration
        easedProgress = progress * progress * (3.0 - 2.0 * progress)
        Texture.zoomFactor = (
            cls.zoomStart + (cls.zoomTarget - cls.zoomStart) * easedProgress
        )

    @classmethod
    def update(cls, deltaTime, screenSize):
        TerrainManager.update(Rover.coords, cls.objects)
        EnvironmentManager.update(deltaTime, screenSize, Rover)
        cls.objects.sort(key=lambda texture: texture.priority)
        for texture in cls.objects:
            texture.update(deltaTime)
        cls.camera.follow(Rover.coords)

    @classmethod
    def render(cls, screen):
        screen.fill('#883a21')
        screenSize = screen.get_size()
        scaleFactor = Texture.getScaleFactor(screenSize)
        cameraShake = EnvironmentManager.cameraShake
        cameraOffset = (
            cls.camera.coords[0] - cameraShake[0] / scaleFactor,
            cls.camera.coords[1] + cameraShake[1] / scaleFactor
        )
        for texture in cls.objects:
            texture.render(screen, cameraOffset)
        EnvironmentManager.render(screen)
        if not Rover.gameOver:
            if Rover.systemsOn:
                Rover.renderHud(screen)
            Rover.renderSystemsButton(screen)
