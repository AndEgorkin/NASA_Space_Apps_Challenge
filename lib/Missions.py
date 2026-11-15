import pygame as pg
from lib.RoverMap import RoverMap
from objects.Texture import Texture


class Missions:
    # Prototype positions on the supplied image, not georeferenced survey sites.
    definitions = (
        ('The Ancient Water Mystery', 'Hebes / Candor', ((315,205),),
         ('Collect a layered rock sample', 'Measure mineral composition'),
         'Minerals may indicate ancient interaction with water.'),
        ('The Great Landslide', 'Ius Chasma', ((170,295),),
         ('Map the debris', 'Inspect exposed rock layers'),
         'Debris and rock layers help reconstruct the landslide history.'),
        ('The Mysterious Dark Streaks', 'Melas / Coprates', ((410,300),),
         ('Compare seasonal images', 'Take a remote measurement'),
         'The cause is debated: salts or dry flows are possible; liquid water is unconfirmed.'),
        ('The Geological Archive', 'Hebes Chasma', ((255,165),),
         ('Photograph rock layers', 'Compare the sequence of layers'),
         'Layer order reveals the relative sequence of geological events.'),
        ('The Lost Underground Reservoir', 'Eastern Valles', (tuple(RoverMap.icePixel),),
         ('Map collapsed terrain', 'Scan and discover underground ice'),
         'Underground ice found in this fictional research site. Deliver it to base to make water.'),
        ('The Planetary Fracture', 'Noctis Labyrinthus', ((90,225),),
         ('Map the fractures', 'Measure an elevation profile'),
         'Fractures reveal clues to tectonics and the uplift of Tharsis.'),
        ('The Impossible Route', 'Canyon route', ((430,345),(390,365),(350,390)),
         ('Check slope at waypoint 1', 'Check traction at waypoint 2', 'Complete the safe route'),
         'Topography and traction constrain rover routes.'),
        ('The Canyon Research Station', 'Base plateau', ((480,365),),
         ('Deploy the station after delivering water and watering plants',),
         'The station has water and provisions: the prototype life-support cycle is complete.')
    )
    radius = 280

    def __init__(self):
        self.progress = [0] * len(self.definitions)
        self.analysed = False
        self.font = pg.font.Font(None, 22)

    def done(self, index):
        return self.progress[index] >= len(self.definitions[index][3]) and (index != 0 or self.analysed)

    @property
    def completed(self):
        return sum(self.done(i) for i in range(len(self.definitions)))

    @property
    def allDone(self):
        return self.completed == len(self.definitions)

    def ending(self, survival):
        # Exhaustion takes precedence over completion at the deadline.
        if survival.depleted:
            return 'depleted'
        if self.allDone:
            return 'won'
        return None

    def target(self, index):
        points = self.definitions[index][2]
        return points[min(self.progress[index], len(points)-1)]

    def nearby(self, coords):
        for i in range(len(self.definitions)):
            if self.done(i) or self.progress[i] >= len(self.definitions[i][3]):
                continue
            if pg.Vector2(coords).distance_to(RoverMap.mapToWorld(self.target(i))) <= (RoverMap.baseInteractionRadius if i == 7 else self.radius):
                return i
        return None

    def hint(self, coords):
        index = self.nearby(coords)
        if index is None:
            return ''
        return f'E: {index+1}. {self.definitions[index][3][self.progress[index]]}'

    def roverAction(self, coords, survival):
        index = self.nearby(coords)
        if index is None:
            return
        if index == 7 and (survival.deliveredWater < 1 or survival.wateredPlants < 1):
            survival.notify('Station: first deliver water and water the plants at base.')
            return
        self.progress[index] += 1
        if index == 0 and self.progress[index] == len(self.definitions[index][3]):
            survival.notify('Sample ready. Press E at the base computer to analyse minerals.')
        elif self.done(index):
            if index == 4:
                survival.iceDiscovered = True
            survival.notify(f'Mission {index+1} complete. ' + self.definitions[index][4])
        else:
            survival.notify(f'Mission {index+1}: step complete. Press E for the next step.')

    def analyseAtBase(self, survival, roverCoords):
        if self.progress[0] >= len(self.definitions[0][3]) and not self.analysed:
            if pg.Vector2(roverCoords).distance_to(RoverMap.baseCoords) > RoverMap.baseInteractionRadius:
                survival.notify('Resuming rover control. Bring the sample back to base for analysis.')
                return False
            self.analysed = True
            survival.notify('Mission 1: analysis complete. ' + self.definitions[0][4])
            return True
        return False

    def renderStatus(self, screen, position=(16,48)):
        label = self.font.render(f'Missions: {self.completed}/8  |  M: map and objectives', True, '#ffdc8a')
        screen.blit(label, position)

    def renderList(self, screen, x, y):
        for i, (title, location, points, actions, result) in enumerate(self.definitions):
            done = self.done(i)
            color = '#83d674' if done else '#ffdc8a'
            rows = [f'{i+1}. {title}', location]
            if done:
                rows.append('Complete')
            elif i == 0 and self.progress[i] >= len(actions):
                rows.append('Analyse at the base computer (E)')
            else:
                rows.append(f'Step {self.progress[i]+1}/{len(actions)}: E at the marker')
            for row, text in enumerate(rows):
                screen.blit(self.font.render(text, True, color if row != 1 else '#b0bbc8'), (x,y+i*65+row*18))

    def renderWorld(self, screen, cameraOffset):
        bounds = screen.get_rect().inflate(80, 80)
        for i, definition in enumerate(self.definitions):
            if self.done(i):
                continue
            point = Texture.worldToScreen(RoverMap.mapToWorld(self.target(i)), screen.get_size(), cameraOffset)
            if not bounds.collidepoint(point):
                continue
            pg.draw.circle(screen, '#ffbc55', point, 24, 3)
            label = self.font.render(f'{i+1}. {definition[0]}', True, '#ffdc8a')
            screen.blit(label, label.get_rect(midbottom=(point[0],point[1]-30)))
