import math
import pygame as pg

from lib.AssetManager import AssetManager
from lib.Camera import Camera
from lib.EnvironmentManager import EnvironmentManager
from lib.RoverMap import RoverMap
from lib.RoverSave import RoverSave
from lib.TerrainManager import TerrainManager
from objects.BoundingBox import BoundingBox
from objects.Rover import Rover
from objects.Texture import Texture
from objects.WaterWell import WaterWell


class MarsSurface:
    zoomInFactor = 1.6
    zoomTransitionDuration = 0.45

    def __init__(self):
        EnvironmentManager.reset()
        self.rover = Rover()
        RoverSave.load(self.rover, RoverMap.spawnCoords)
        self.station = Texture('station', RoverMap.baseCoords, 30, 7.5,
                               AssetManager.get('assets.texture.station'), 50)
        self.objects = [self.rover, self.station, WaterWell()]
        self._addStationCollisions()
        self._ensureSafeSpawn()
        self.camera = Camera(self.rover.coords)
        self.zoomTarget = self.zoomStart = Texture.zoomFactor = 1.0
        self.zoomElapsed = self.zoomTransitionDuration
        EnvironmentManager.dustTexture = AssetManager.get('assets.texture.dust')
        TerrainManager.loadInitialChunks(self.rover.coords, self.objects)

    def _addStationCollisions(self):
        # Same two rotated building rectangles as main; both use the rendered scale.
        width, height = self.station.texture.get_size()
        angle = math.radians(self.station.rotation)
        for left, top, right, bottom in ((0,0,80,128), (80,0,128,96)):
            localX = ((left+right)/2-width/2) * self.station.scale
            localY = (height/2-(top+bottom)/2) * self.station.scale
            coords = (self.station.coords[0]+math.cos(angle)*localX-math.sin(angle)*localY,
                      self.station.coords[1]+math.sin(angle)*localX+math.cos(angle)*localY)
            self.rover.boundingBoxes.append(BoundingBox(coords,(right-left)*self.station.scale,
                                                       (bottom-top)*self.station.scale,self.station.rotation))

    def _ensureSafeSpawn(self):
        box = BoundingBox(self.rover.coords, self.rover.texture.get_width()*self.rover.scale*0.8,
                          self.rover.texture.get_height()*self.rover.scale*0.8, self.rover.rotation)
        if any(obstacle.intersects(box) for obstacle in self.rover.boundingBoxes):
            self.rover.coords[:] = RoverMap.spawnCoords

    def handleEvent(self, event):
        if self.rover.gameOver:
            return
        if event.type == pg.MOUSEWHEEL and self.rover.systemsOn:
            self.rover.adjustPower(event.y)
        elif (event.type == pg.MOUSEBUTTONDOWN and event.button == 1
              and self.rover.systemsButtonRect.collidepoint(event.pos)):
            self.rover.systemsOn = not self.rover.systemsOn

    def updateCameraZoom(self, deltaTime):
        target = self.zoomInFactor if not self.rover.systemsOn else 1.0
        if target != self.zoomTarget:
            self.zoomTarget = target
            self.zoomStart = Texture.zoomFactor
            self.zoomElapsed = 0.0
        self.zoomElapsed = min(self.zoomTransitionDuration, self.zoomElapsed+max(0,deltaTime))
        progress = self.zoomElapsed/self.zoomTransitionDuration
        eased = progress*progress*(3-2*progress)
        Texture.zoomFactor = self.zoomStart+(self.zoomTarget-self.zoomStart)*eased

    def update(self, deltaTime, screenSize, controlsEnabled=True):
        if self.rover.gameOver:
            return
        self.updateCameraZoom(deltaTime)
        TerrainManager.update(self.rover.coords,self.objects)
        EnvironmentManager.update(deltaTime,screenSize,self.rover)
        self.objects.sort(key=lambda texture: texture.priority)
        for texture in self.objects:
            if texture is self.rover:
                texture.update(deltaTime,controlsEnabled)
            else:
                texture.update(deltaTime)
        self.camera.follow(self.rover.coords)

    def render(self, screen, missions):
        screen.fill('#883a21')
        factor = Texture.getScaleFactor(screen.get_size())
        shake = EnvironmentManager.cameraShake
        offset = (self.camera.coords[0]-shake[0]/factor,self.camera.coords[1]+shake[1]/factor)
        for texture in self.objects:
            texture.render(screen,offset)
        missions.renderWorld(screen,offset)
        EnvironmentManager.render(screen)
        self.renderControls(screen)

    def renderControls(self, screen):
        if self.rover.systemsOn:
            self.rover.renderHud(screen)
        self.rover.renderSystemsButton(screen)

    def reset(self):
        self.rover.resetSystems()
        self.rover.coords[:] = RoverMap.spawnCoords
        self.rover.rotation = 0.0
        self.rover.previousGroundHeight = None
        self.rover.uphillLoad = 0.0
        self.rover.wheelTrackPoints = [type(points)(maxlen=self.rover.wheelTrackPointLimit)
                                      for points in self.rover.wheelTrackPoints]
        EnvironmentManager.reset()
        self.camera.coords[:] = self.rover.coords
        self.zoomTarget = self.zoomStart = Texture.zoomFactor = 1.0
        self.zoomElapsed = self.zoomTransitionDuration

    def renderMapStatus(self, screen):
        self.rover.renderSystemsButton(screen)
        status = f'Charge {self.rover.charge:.0f}% | Power {self.rover.powerPercent:.0f}%'
        if EnvironmentManager.solarFlareActive:
            status += ' | SOLAR FLARE: switch systems OFF!'
        elif not self.rover.systemsOn:
            status += ' | Systems OFF: protected'
        color = '#ff6666' if EnvironmentManager.solarFlareActive else 'white'
        text = pg.font.Font(None, 24).render(status, True, color)
        screen.blit(text, (24, 62))
