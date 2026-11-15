import os
os.environ['SDL_VIDEODRIVER']='dummy'
os.environ['SDL_AUDIODRIVER']='dummy'
import unittest
from collections import deque
from types import SimpleNamespace
import pygame as pg
from lib.Missions import Missions
from lib.Survival import Survival
from lib.RoverMap import RoverMap
from objects.RouteCourse import RouteCourse
from objects.BoundingBox import BoundingBox


class InteractiveMissionTests(unittest.TestCase):
    def setUp(self):
        pg.init();self.screen=pg.display.set_mode((1200,830))
        self.missions=Missions();self.survival=Survival()

    def moveArm(self, goal):
        arm=self.missions.manipulator
        for _ in range(400):
            delta=goal-arm.tip
            if delta.length()<5:return
            arm.update(1/60,delta)
        self.fail('Arm cannot reach the target')

    def testSampleRequiresPickupAndStorage(self):
        coords=RoverMap.mapToWorld(self.missions.target(0))
        self.missions.roverAction(coords,self.survival)
        arm=self.missions.manipulator
        self.assertTrue(arm.active)
        self.missions.manipulatorAction(coords,self.survival)
        self.assertEqual(self.missions.progress[0],0)
        self.moveArm(arm.sample)
        self.missions.manipulatorAction(coords,self.survival)
        self.assertTrue(arm.carrying)
        self.assertEqual(self.missions.progress[0],0)
        self.moveArm(arm.tray)
        arm.render(self.screen)
        self.missions.manipulatorAction(coords,self.survival)
        self.assertFalse(arm.active)
        self.assertEqual(self.missions.progress[0],1)

    def testCancelAndSystemsFailureDoNotGrantSample(self):
        coords=RoverMap.mapToWorld(self.missions.target(0));arm=self.missions.manipulator
        self.missions.roverAction(coords,self.survival)
        arm.cancel()
        self.assertEqual(self.missions.progress[0],0)
        self.missions.roverAction(coords,self.survival)
        self.missions.updateManipulator(1/60,SimpleNamespace(coords=coords,gameOver=False,systemsOn=False),self.survival)
        self.assertFalse(arm.active)
        self.assertEqual(self.missions.progress[0],0)

    def testRocksLeaveReachableRouteAndHaveMatchingCollisionBounds(self):
        route=self.missions.definitions[6][2]
        rocks,boxes=RouteCourse.build(route)
        try:
            self.assertGreaterEqual(len(rocks),6)
            self.assertLessEqual(len(rocks),12)
            for rock,box in zip(rocks,boxes):
                self.assertEqual(tuple(rock.coords),box.coords)
                self.assertEqual(box.halfWidth*2,rock.texture.get_width()*rock.scale)
            points=[pg.Vector2(RoverMap.mapToWorld(point)) for point in route]
            for start,end in zip(points,points[1:]):
                direction=end-start
                normal=pg.Vector2(-direction.y,direction.x).normalize()
                # A generous full-rover opening must exist BETWEEN each row's
                # rocks, rather than requiring a detour around the whole field.
                self.assertTrue(any(
                    not any(box.intersects(BoundingBox((start+end)/2+normal*offset,160,180))
                            for box in boxes)
                    for offset in (-260,260)))
                # Verify a collision-free path for a full-size rover, not just a point.
                step=70
                def snapped(point):return (round(point.x/step),round(point.y/step))
                first,last=snapped(start),snapped(end)
                bounds=(min(first[0],last[0])-12,max(first[0],last[0])+12,
                        min(first[1],last[1])-12,max(first[1],last[1])+12)
                def clear(point):
                    rover=BoundingBox((point[0]*step,point[1]*step),110,140)
                    return not any(box.intersects(rover) for box in boxes)
                self.assertTrue(clear(first));self.assertTrue(clear(last))
                queue=deque([first]);visited={first}
                while queue and last not in visited:
                    x,y=queue.popleft()
                    for candidate in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
                        if (candidate not in visited and bounds[0]<=candidate[0]<=bounds[1]
                            and bounds[2]<=candidate[1]<=bounds[3] and clear(candidate)):
                            visited.add(candidate);queue.append(candidate)
                self.assertIn(last,visited)
        finally:
            for rock in rocks:rock.destroy()
