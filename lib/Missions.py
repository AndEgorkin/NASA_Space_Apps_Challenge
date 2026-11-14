import pygame as pg
from lib.RoverMap import RoverMap
from objects.Texture import Texture


class Missions:
    # Prototype positions on the supplied image, not georeferenced survey sites.
    definitions = (
        ('Древняя вода', 'Hebes / Candor', ((315,205),),
         ('Взять образец слоистых пород', 'Измерить минералы'),
         'Минералы могут указывать на древнее взаимодействие с водой.'),
        ('Огромный оползень', 'Ius Chasma', ((170,295),),
         ('Нанести обломки на карту', 'Изучить обнажённые слои'),
         'Обломки и слои помогают восстановить историю оползня.'),
        ('Тёмные полосы', 'Melas / Coprates', ((410,300),),
         ('Сравнить сезонные снимки', 'Провести дистанционное измерение'),
         'Причина полос спорна: соли и сухие потоки возможны; жидкая вода не доказана.'),
        ('Геологический архив', 'Hebes Chasma', ((255,165),),
         ('Сфотографировать слои', 'Сопоставить порядок слоёв'),
         'Порядок слоёв даёт относительную последовательность событий.'),
        ('Подземный резервуар', 'Eastern Valles', ((600,280),),
         ('Картировать провалы', 'Сравнить высоты русел'),
         'Древние русла совместимы с выходом воды; современный резервуар не подтверждён.'),
        ('Разлом планеты', 'Noctis Labyrinthus', ((90,225),),
         ('Картировать трещины', 'Измерить профиль высот'),
         'Разломы позволяют исследовать тектонику и влияние поднятия Tharsis.'),
        ('Невозможный маршрут', 'Canyon route', ((430,345),(390,365),(350,390)),
         ('Проверить склон: точка 1', 'Проверить сцепление: точка 2', 'Завершить безопасный маршрут'),
         'Рельеф и сцепление ограничивают доступные пути ровера.'),
        ('Исследовательская станция', 'Base plateau', ((480,365),),
         ('Развернуть станцию после доставки воды и полива',),
         'Станция снабжена водой и пищей: прототип жизненного цикла завершён.')
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
            if pg.Vector2(coords).distance_to(RoverMap.mapToWorld(self.target(i))) <= self.radius:
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
            survival.notify('Станция: сначала доставьте воду и полейте растения на базе.')
            return
        self.progress[index] += 1
        if index == 0 and self.progress[index] == len(self.definitions[index][3]):
            survival.notify('Образец готов. E у компьютера базы: анализ минералов.')
        elif self.done(index):
            survival.notify(f'Миссия {index+1} завершена. ' + self.definitions[index][4])
        else:
            survival.notify(f'Миссия {index+1}: этап выполнен. Следующий этап — E.')

    def analyseAtBase(self, survival, roverCoords):
        if self.progress[0] >= len(self.definitions[0][3]) and not self.analysed:
            if pg.Vector2(roverCoords).distance_to(RoverMap.baseCoords) > 650:
                survival.notify('Сначала привезите ровер с образцом обратно к базе.')
                return True
            self.analysed = True
            survival.notify('Миссия 1: анализ завершён. ' + self.definitions[0][4])
            return True
        return False

    def renderStatus(self, screen):
        label = self.font.render(f'Миссии: {self.completed}/8  |  M: карта и задания', True, '#ffdc8a')
        screen.blit(label, (16,48))

    def renderList(self, screen, x, y):
        for i, (title, location, points, actions, result) in enumerate(self.definitions):
            done = self.done(i)
            color = '#83d674' if done else '#ffdc8a'
            rows = [f'{i+1}. {title}', location]
            if done:
                rows.append('Выполнено')
            elif i == 0 and self.progress[i] >= len(actions):
                rows.append('Анализ: компьютер базы (E)')
            else:
                rows.append(f'Этап {self.progress[i]+1}/{len(actions)}: E у точки')
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
