from pathlib import Path
import math

import pygame as pg


class BaseLocation:
    # Coordinates are measured in the original 240 x 140 room artwork.
    roomFiles = {
        'main': 'CorrdorMain.webp', 'corridor': 'Corridor1.webp',
        'control': 'ControlRoom.webp', 'crew': 'CrewCabins.webp',
        'plants': 'PlantRoom.webp'
    }
    roomNames = {
        'main': 'Central corridor', 'corridor': 'East corridor',
        'control': 'Control Room', 'crew': 'Crew cabins', 'plants': 'Farming station'
    }
    # Each exit specifies its destination and a safe arrival point away from the trigger.
    exits = {
        'main': [('top', 'control', (220, 75)), ('right', 'corridor', (12, 75))],
        'corridor': [('left', 'main', (228, 75)), ('top', 'crew', (120, 128)),
                     ('bottom', 'plants', (120, 15))],
        'control': [('right', 'main', (120, 12))],
        'crew': [('bottom', 'corridor', (120, 12))],
        'plants': [('top', 'corridor', (120, 128))]
    }

    def __init__(self, screen):
        self.screen = screen
        root = Path(__file__).resolve().parent.parent / 'assets'
        self.rooms = {}
        self.wallMasks = {}
        for name, filename in self.roomFiles.items():
            image = pg.image.load(str(root / 'base' / filename)).convert()
            self.rooms[name] = image
            mask = pg.mask.Mask(image.get_size())
            for x in range(image.get_width()):
                for y in range(image.get_height()):
                    if image.get_at((x, y))[:3] == (0, 0, 0):
                        mask.set_at((x, y))
            self.wallMasks[name] = mask
        self.objects = {
            'main': [pg.Rect(0, 24, 3, 90), pg.Rect(50, 137, 139, 3)],
            'corridor': [],
            'control': [pg.Rect(11, 33, 28, 72)],
            'crew': [pg.Rect(62, 34, 120, 30)],
            'plants': [pg.Rect(27, 38, 91, 91), pg.Rect(120, 38, 91, 91)]
        }
        # The temporary portrait is displayed with its original proportions.
        portrait = pg.image.load(str(root / 'player' / 'Player.png')).convert_alpha()
        self.playerImage = pg.transform.smoothscale(portrait, (8, 20))
        self.playerMask = pg.mask.Mask((6, 5), fill=True)
        self.position = pg.Vector2(120, 75)
        self.room = 'main'
        self.font = pg.font.Font(None, 25)
        self._scaledRoom = None
        self._renderKey = None

    def canControl(self):
        return self.room == 'control' and pg.Rect(39, 29, 16, 80).collidepoint(self.position)

    def handleEvent(self, event):
        if event.type == pg.QUIT:
            return 'quit'
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_ESCAPE:
                return 'menu'
            if event.key == pg.K_e and self.canControl():
                return 'rover'
        return None

    def _blocked(self, position):
        rect = pg.Rect(0, 0, 6, 5)
        rect.center = (round(position.x), round(position.y))
        return (self.wallMasks[self.room].overlap(self.playerMask, rect.topleft) is not None
                or any(rect.colliderect(obj) for obj in self.objects[self.room]))

    def update(self, deltaTime, direction=None):
        if direction is None:
            keys = pg.key.get_pressed()
            direction = (int(keys[pg.K_d] or keys[pg.K_RIGHT]) - int(keys[pg.K_a] or keys[pg.K_LEFT]),
                         int(keys[pg.K_s] or keys[pg.K_DOWN]) - int(keys[pg.K_w] or keys[pg.K_UP]))
        movement = pg.Vector2(direction)
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
                return
            self.position.x = max(3, min(237, self.position.x))
            self.position.y = max(3, min(137, self.position.y))

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

    def render(self):
        width, height = self.screen.get_size()
        scale = min(width / 240, (height - 64) / 140)
        size = (round(240 * scale), round(140 * scale))
        offset = ((width - size[0]) // 2, 48 + (height - 64 - size[1]) // 2)
        key = (self.room, size)
        if self._renderKey != key:
            self._scaledRoom = pg.transform.scale(self.rooms[self.room], size)
            self._renderKey = key
        self.screen.fill('#101823')
        self.screen.blit(self._scaledRoom, offset)
        # Show barriers at unavailable exits rather than leaving invisible walls.
        if self.room == 'main':
            for barrier in self.objects['main']:
                pg.draw.rect(self.screen, '#596473',
                             (offset[0] + barrier.x * scale, offset[1] + barrier.y * scale,
                              max(2, barrier.w * scale), max(2, barrier.h * scale)))
        image = pg.transform.scale(self.playerImage, (round(8 * scale), round(20 * scale)))
        feet = (round(offset[0] + self.position.x * scale),
                round(offset[1] + (self.position.y + 2) * scale))
        self.screen.blit(image, image.get_rect(midbottom=feet))
        label = self.roomNames[self.room] + '  |  WASD / Arrows: move  |  Esc: menu'
        self.screen.blit(self.font.render(label, True, 'white'), (16, 12))
        if self.canControl():
            self.screen.blit(self.font.render('E: control rover', True, '#ffab40'), (16, height - 28))
