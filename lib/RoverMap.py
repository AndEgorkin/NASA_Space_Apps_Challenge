from lib.AssetManager import AssetManager
import pygame as pg


class RoverMap:
    # One image pixel = 16 world units, north is positive world Y.
    imageSize = (768, 558)
    unitsPerPixel = 16.0
    basePixel = pg.Vector2(480, 365)
    icePixel = pg.Vector2(600, 280)
    baseCoords = (0.0, 0.0)
    spawnCoords = (0.0, -900.0)
    baseInteractionRadius = 850

    def __init__(self):
        self.image = AssetManager.get('assets.map.GameMap')
        self.font = pg.font.Font(None, 26)
        self.scaled = None
        self.size = None

    @classmethod
    def worldToMap(cls, coords):
        return pg.Vector2(cls.basePixel.x + coords[0] / cls.unitsPerPixel,
                          cls.basePixel.y - coords[1] / cls.unitsPerPixel)

    @classmethod
    def mapToWorld(cls, coords):
        return ((coords[0] - cls.basePixel.x) * cls.unitsPerPixel,
                (cls.basePixel.y - coords[1]) * cls.unitsPerPixel)

    @staticmethod
    def headingOnMap(rotation):
        # Rover forward is (-sin(angle), cos(angle)) in world coordinates.
        # The map reverses Y, so zero heading points up and turns reverse sign.
        return pg.Vector2(0, -1).rotate(-rotation)

    @staticmethod
    def edgePosition(point, rect):
        # Intersect the ray from the map center with its inset border.
        inner = rect.inflate(-24, -24)
        center = pg.Vector2(inner.center)
        direction = pg.Vector2(point) - center
        if not direction.length_squared():
            return center
        factors = []
        if direction.x:
            factors.append((inner.width / 2) / abs(direction.x))
        if direction.y:
            factors.append((inner.height / 2) / abs(direction.y))
        return center + direction * min(factors)

    def render(self, screen, rover, missions=None):
        width, height = screen.get_size()
        rightPanel = 350 if missions is not None else 0
        scale = min((width - 80 - rightPanel) / self.imageSize[0], (height - 120) / self.imageSize[1])
        size = (round(self.imageSize[0] * scale), round(self.imageSize[1] * scale))
        if self.size != size:
            self.scaled = pg.transform.smoothscale(self.image, size)
            self.size = size
        rect = self.scaled.get_rect(center=((width - rightPanel) // 2, height // 2))
        screen.fill('#101823')
        screen.blit(self.scaled, rect)
        pg.draw.rect(screen, '#adb9c7', rect, 2)
        def project(point):
            return pg.Vector2(rect.x + point[0] * size[0] / self.imageSize[0],
                              rect.y + point[1] * size[1] / self.imageSize[1])
        base = project(self.basePixel)
        pg.draw.rect(screen, '#7bdefb', (base.x-7,base.y-7,14,14))
        screen.blit(self.font.render('BASE', True, '#b5edff'), base + (12,-12))
        ice = project(self.icePixel)
        pg.draw.circle(screen, '#68c9ed', ice, 8)
        waterLabel = self.font.render('Ice deposit / Mission 5', True, '#a0e6ff')
        screen.blit(waterLabel, (24, height - 38))
        if missions is not None:
            route=[project(point) for point in missions.definitions[6][2]]
            pg.draw.lines(screen,'#b39769',False,route,2)
            for waypoint in route:pg.draw.circle(screen,'#b39769',waypoint,3)
            for i, definition in enumerate(missions.definitions):
                marker = project(missions.target(i))
                color = '#83d674' if missions.done(i) else '#ffb544'
                pg.draw.circle(screen, '#101823', marker, 11)
                number = self.font.render(str(i+1), True, color)
                screen.blit(number, number.get_rect(center=marker))
                # Full titles and locations are listed in the adjacent panel.
                name = self.font.render(definition[1], True, color)
                screen.blit(name, marker + ((12,18) if i == 7 else (12,-18)))
            missions.renderList(screen, width-rightPanel+4, 210)
        point = project(self.worldToMap(rover.coords))
        if rect.collidepoint(point):
            forward = self.headingOnMap(rover.rotation)
            side = forward.rotate(90)
            pg.draw.polygon(screen, '#50ff98', [point+forward*12,point-forward*8+side*7,point-forward*8-side*7])
            pg.draw.circle(screen, '#102d22', point, 3)
        else:
            edge = self.edgePosition(point, rect)
            tangent = (point - pg.Vector2(rect.center)).normalize().rotate(90)
            pg.draw.line(screen, '#50ff98', edge-tangent*16, edge+tangent*16, 7)
            screen.blit(self.font.render('ROVER', True, '#50ff98'), edge + (10,-25))
        label = 'M / Esc: close | Green: rover | Blue: base / ice'
        screen.blit(self.font.render(label, True, 'white'), (24,20))
