import pygame as pg
from objects.Texture import Texture
from objects.BoundingBox import BoundingBox
from lib.RoverMap import RoverMap


class RouteCourse:
    @staticmethod
    def build(mapPoints):
        objects=[];collisions=[]
        points=[pg.Vector2(RoverMap.mapToWorld(point)) for point in mapPoints]
        for segment,(start,end) in enumerate(zip(points,points[1:])):
            delta=end-start;normal=pg.Vector2(-delta.y,delta.x).normalize()
            for row,fraction in enumerate((0.5,)):
                for lane,offset in enumerate((-480,80 if segment%2 else -80,480)):
                    center=start+delta*fraction+normal*offset
                    if any(center.distance_to(point)<210 for point in points):continue
                    if any(center.distance_to(pg.Vector2(box.coords))<330 for box in collisions):continue
                    width=150; height=150
                    image=pg.Surface((width,height),pg.SRCALPHA)
                    pg.draw.polygon(image,'#543a32',[(0,35),(30,0),(115,0),(149,35),(149,125),(120,149),(25,149),(0,115)])
                    pg.draw.polygon(image,'#93634a',[(8,38),(34,8),(112,8),(139,41),(123,119),(32,127),(10,109)])
                    pg.draw.lines(image,'#ba8761',False,[(14,47),(39,18),(108,18),(132,45)],6)
                    pg.draw.lines(image,'#694634',False,[(78,23),(62,68),(93,110)],5)
                    rock=Texture(f'route.rock.{segment}.{row}.{lane}',center,0,1,image,45)
                    objects.append(rock)
                    collisions.append(BoundingBox(center,width,height))
        return objects,collisions
