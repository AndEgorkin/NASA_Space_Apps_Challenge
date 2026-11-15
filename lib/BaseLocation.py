from lib.AssetManager import AssetManager
from lib.BaseInterior import BaseInterior
from lib.Interface import Interface as UI
from lib.EnvironmentManager import EnvironmentManager
import math

import pygame as pg


class BaseLocation:
    # Coordinates are measured in the original 240 x 140 room artwork.
    roomAssets = {
        'main': 'assets.base.CorrdorMain', 'corridor': 'assets.base.Corridor1',
        'control': 'assets.base.ControlRoom', 'crew': 'assets.base.CrewCabins',
        'plants': 'assets.base.PlantRoom'
    }
    roomNames = {
        'main': 'Central corridor', 'corridor': 'East corridor',
        'control': 'Control Room', 'crew': 'Crew cabins', 'plants': 'Farming station'
    }
    # Each exit specifies its destination and a safe arrival point away from the trigger.
    exits = {
        'main': [('left', 'control', (220, 75)), ('right', 'corridor', (12, 75))],
        'corridor': [('left', 'main', (228, 75)), ('top', 'crew', (120, 128)),
                     ('bottom', 'plants', (120, 15))],
        'control': [('right', 'main', (12, 75))],
        'crew': [('bottom', 'corridor', (120, 12))],
        'plants': [('top', 'corridor', (120, 128))]
    }

    def __init__(self, screen):
        self.screen = screen
        self.rooms = {}
        self.wallMasks = {}
        for name, assetKey in self.roomAssets.items():
            image = AssetManager.get(assetKey)
            self.rooms[name] = image
            mask = pg.mask.Mask(image.get_size())
            for x in range(image.get_width()):
                for y in range(image.get_height()):
                    if image.get_at((x, y))[:3] == (0, 0, 0):
                        mask.set_at((x, y))
            self.wallMasks[name] = mask
        self.objects = {
            'main': [pg.Rect(50, 0, 139, 3), pg.Rect(50, 137, 139, 3)],
            'corridor': [],
            'control': [pg.Rect(11, 33, 28, 72)],
            'crew': [pg.Rect(62, 34, 120, 30)],
            'plants': [pg.Rect(27, 38, 91, 91), pg.Rect(120, 38, 91, 91)]
        }
        sheet = AssetManager.get('assets.player.operator-walk')
        cellWidth, cellHeight = sheet.get_width() // 4, sheet.get_height() // 4
        cells = [[sheet.subsurface((column * cellWidth, row * cellHeight,
                                    cellWidth, cellHeight))
                  for column in range(4)] for row in range(4)]
        # Use the union of every frame's visible bounds: the north-facing head
        # sits higher in its cell than the south-facing head.
        cropBounds = cells[0][0].get_bounding_rect()
        for row in cells:
            for cell in row:
                cropBounds.union_ip(cell.get_bounding_rect())
        self.walkFrames = [[cell.subsurface(cropBounds).copy().convert_alpha() for cell in row]
                           for row in cells]
        self._scaledFrames = {}
        self.facing = 0
        self.walkTime = 0.0
        self.isWalking = False
        self.playerMask = pg.mask.Mask((10, 16), fill=True)
        self.position = pg.Vector2(120, 75)
        self.room = 'main'
        self.font = pg.font.Font(None, 25)
        self.interiors = {name: BaseInterior.build(name, self.exits[name]) for name in self.rooms}
        self._scaledRoom = None
        self._renderKey = None

    def canControl(self):
        return self.room == 'control' and pg.Rect(39, 29, 16, 80).collidepoint(self.position)

    def canWaterPlants(self):
        return self.room == 'plants' and 24 <= self.position.x <= 214 and 18 <= self.position.y <= 37

    def canSleep(self):
        # Approach the lower edge of the beds; their collision extends to y=64.
        return self.room == 'crew' and 62 <= self.position.x <= 182 and 77 <= self.position.y <= 91

    def handleEvent(self, event):
        if event.type == pg.QUIT:
            return 'quit'
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_ESCAPE:
                return 'menu'
            if event.key == pg.K_e and self.canControl():
                return 'rover'
            if event.key == pg.K_e and self.canWaterPlants():
                return 'water'
            if event.key == pg.K_e and self.canSleep():
                return 'sleep'
        return None

    def _blocked(self, position):
        # Collide with the entire visible body, including the head at upper walls.
        rect = pg.Rect(0, 0, 10, 16)
        rect.midbottom = (round(position.x), round(position.y) + 2)
        return (self.wallMasks[self.room].overlap(self.playerMask, rect.topleft) is not None
                or any(rect.colliderect(obj) for obj in self.objects[self.room]))

    def update(self, deltaTime, direction=None):
        if direction is None:
            keys = pg.key.get_pressed()
            direction = (int(keys[pg.K_d] or keys[pg.K_RIGHT]) - int(keys[pg.K_a] or keys[pg.K_LEFT]),
                         int(keys[pg.K_s] or keys[pg.K_DOWN]) - int(keys[pg.K_w] or keys[pg.K_UP]))
        previousPosition = self.position.copy()
        movement = pg.Vector2(direction)
        if movement.length_squared():
            if abs(movement.x) > abs(movement.y):
                self.facing = 2 if movement.x > 0 else 1
            else:
                self.facing = 0 if movement.y > 0 else 3
        if movement.length_squared():
            movement = movement.normalize() * 42 * min(max(deltaTime, 0), 0.1)
        # Small steps prevent crossing even a one-pixel wall at low frame rates.
        steps = max(1, math.ceil(movement.length() / 0.5))
        for _ in range(steps):
            for axis in (0, 1):
                candidate = self.position.copy()
                candidate[axis] += movement[axis] / steps
                if not self._blocked(candidate):
                    self.position = candidate
            if self._transition():
                self.isWalking = False
                self.walkTime = 0.0
                return
            self.position.x = max(3, min(237, self.position.x))
            self.position.y = max(3, min(137, self.position.y))

        self.isWalking = self.position.distance_squared_to(previousPosition) > 0.0001
        self.walkTime = self.walkTime + min(max(deltaTime, 0), 0.1) if self.isWalking else 0.0

    def _transition(self):
        x, y = self.position
        for edge, destination, arrival in self.exits[self.room]:
            reached = ((edge == 'top' and y <= 3 and 54 <= x <= 184)
                       or (edge == 'bottom' and y >= 137 and 54 <= x <= 184)
                       or (edge == 'left' and x <= 3 and 30 <= y <= 110)
                       or (edge == 'right' and x >= 237 and 30 <= y <= 110))
            if reached:
                self.room = destination
                self.position.update(arrival)
                return True
        return False

    @staticmethod
    def _scalePlayerFrame(source, size):
        # Own the pixel format rather than inheriting SDL surface flags.
        frame = pg.Surface(size, pg.SRCALPHA, 32)
        pg.transform.smoothscale(source.convert_alpha(), size, frame)
        width, height = size
        # Some backends/sprite exports expose transparent padding as opaque black.
        # Remove only background connected to the border, preserving dark details.
        pending = [(x,y) for x in range(width) for y in (0,height-1)]
        pending += [(x,y) for y in range(height) for x in (0,width-1)]
        visited = set()
        while pending:
            x,y = pending.pop()
            if (x,y) in visited or not (0 <= x < width and 0 <= y < height):
                continue
            visited.add((x,y))
            color = frame.get_at((x,y))
            if color.a == 0 or max(color.r,color.g,color.b) <= 3:
                frame.set_at((x,y),(0,0,0,0))
                pending.extend(((x-1,y),(x+1,y),(x,y-1),(x,y+1)))
        # Explicit premultiplied blending also handles surfaces whose normal
        # per-pixel alpha blit path differs between SDL builds.
        return frame.premul_alpha()

    def render(self, hint=None):
        width, height = self.screen.get_size()
        scale = min((width - 48) / 240, (height - 180) / 140)
        size = (round(240 * scale), round(140 * scale))
        offset = ((width - size[0]) // 2, 100 + (height - 180 - size[1]) // 2)
        key = (self.room, size)
        if self._renderKey != key:
            self._scaledRoom = pg.transform.smoothscale(self.interiors[self.room], size)
            self._renderKey = key
        self.screen.fill('#101823')
        self.screen.blit(self._scaledRoom, offset)
        pg.draw.rect(self.screen, UI.border, (offset[0]-2,offset[1]-2,size[0]+4,size[1]+4),2,border_radius=4)
        frame = int(self.walkTime * 8) % 4 if self.isWalking else 0
        spriteSize = (round(12 * scale), round(16 * scale))
        if spriteSize not in self._scaledFrames:
            self._scaledFrames = {spriteSize: [
                [self._scalePlayerFrame(source, spriteSize) for source in row]
                for row in self.walkFrames
            ]}
        image = self._scaledFrames[spriteSize][self.facing][frame]
        feet = (round(offset[0] + self.position.x * scale),
                round(offset[1] + (self.position.y + 2) * scale))
        self.screen.blit(image, image.get_rect(midbottom=feet), special_flags=pg.BLEND_PREMULTIPLIED)
        # Room identification and controls stay outside the play area.
        UI.text(self.screen,EnvironmentManager.clockLabel(),(width//2-100,20),23,UI.cyan)
        UI.text(self.screen,'DAYLIGHT' if EnvironmentManager.isDay else 'NIGHT',(width//2-100,47),19,UI.muted)
        UI.text(self.screen,'ARES  /  HABITAT',(24,16),20,UI.cyan)
        UI.text(self.screen,self.roomNames[self.room].upper(),(24,38),32)
        UI.text(self.screen,'WASD / ARROWS   MOVE     |     ESC   MISSION MENU',(24,height-28),20,UI.muted)
        action = None
        if self.canControl():action='Access rover terminal'
        elif self.canWaterPlants():action='Water the hydroponic beds'
        elif self.canSleep():action='Rest in crew quarters'
        if hint:
            action = hint.removeprefix('E: ')
        if action:
            prompt=pg.Rect(width//2-170,height-73,340,38)
            UI.panel(self.screen,prompt)
            UI.key(self.screen,'E',(prompt.x+7,prompt.y+5))
            UI.text(self.screen,action,(prompt.x+49,prompt.y+10),23)
