import math
import pygame as pg
from lib.Texture import Texture
from lib.AssetManager import AssetManager
from lib.Chunk import Chunk

class Rover(Texture):
    def __init__(self):
        super().__init__(
            'rover.base', 
            [0.0, 0.0], 
            0.0, 
            5, 
            AssetManager.get('assets.texture.rover.base'),
            100
        )
        self.velocity = 0.0
        self.lateralVelocity = 0.0
        self.maxSpeed = 180.0
        self.maxReverseSpeed = -80.0
        self.acceleration = 55.0
        self.braking = 100.0
        self.rollingResistance = 12.0
        self.wheelbase = 140.0
        self.trackWidth = 110.0
        self.maxSteeringAngle = 35.0
        self.previousGroundHeight = None
        self.uphillLoad = 0.0
        self.simulationTime = 0.0

    def _applyDeceleration(self, deceleration):
        if self.velocity > 0.0:
            self.velocity = max(0.0, self.velocity - deceleration)
        elif self.velocity < 0.0:
            self.velocity = min(0.0, self.velocity + deceleration)

    def _sampleTerrain(self, forwardX, forwardY, rightX, rightY):
        halfWheelbase = self.wheelbase / 2.0
        halfTrack = self.trackWidth / 2.0

        wheelPositions = (
            (halfWheelbase, -halfTrack),
            (halfWheelbase, halfTrack),
            (-halfWheelbase, -halfTrack),
            (-halfWheelbase, halfTrack)
        )
        heights = [
            Chunk.terrainHeight(
                self.coords[0] + forwardX * along + rightX * across,
                self.coords[1] + forwardY * along + rightY * across
            )
            for along, across in wheelPositions
        ]

        frontGrade = (heights[0] + heights[1] - heights[2] - heights[3]) / (
            2.0 * self.wheelbase
        )
        sideGrade = (heights[1] + heights[3] - heights[0] - heights[2]) / (
            2.0 * self.trackWidth
        )
        roughness = min(1.0, (abs(frontGrade) + abs(sideGrade)) * 180.0)

        return frontGrade, sideGrade, roughness

    def update(self, deltaTime=1.0 / 60.0):
        deltaTime = min(max(deltaTime, 0.0), 1.0 / 30.0)
        self.simulationTime += deltaTime
        keys = pg.key.get_pressed()
        throttle = 0.0
        if keys[pg.K_w]:
            throttle += 1.0
        if keys[pg.K_s]:
            throttle -= 1.0

        angle = math.radians(self.rotation)
        forwardX = -math.sin(angle)
        forwardY = math.cos(angle)
        rightX = math.cos(angle)
        rightY = math.sin(angle)
        frontGrade, sideGrade, roughness = self._sampleTerrain(
            forwardX, forwardY, rightX, rightY
        )

        groundHeight = Chunk.terrainPixelHeight(self.coords[0], self.coords[1])
        colorIndex = Chunk.terrainColorIndexFromHeight(groundHeight)
        colorRise = 0
        if self.previousGroundHeight is not None:
            colorRise = max(
                0,
                colorIndex
                - Chunk.terrainColorIndexFromHeight(self.previousGroundHeight)
            )
            heightChange = abs(groundHeight - self.previousGroundHeight)
        else:
            heightChange = 0.0
        self.previousGroundHeight = groundHeight
        bump = min(1.0, max(0.0, heightChange * 18.0 - 0.04))

        uphillTarget = min(0.35, colorRise * 0.22)
        self.uphillLoad = max(
            uphillTarget,
            self.uphillLoad * math.exp(-2.8 * deltaTime)
        )

        driveGrip = max(
            0.35,
            1.0 - roughness * 0.55 - bump * 0.15 - self.uphillLoad * 0.2
        )
        if throttle and self.velocity * throttle < 0.0:
            self.velocity += throttle * self.braking * driveGrip * deltaTime
        elif throttle:
            self.velocity += throttle * self.acceleration * driveGrip * deltaTime
        else:
            resistance = (
                self.rollingResistance
                + abs(self.velocity) * 0.04
                + roughness * 20.0
            )
            self._applyDeceleration(resistance * deltaTime)

        self.velocity -= frontGrade * 250.0 * deltaTime
        self._applyDeceleration(self.uphillLoad * 35.0 * deltaTime)
        if bump > 0.0:
            self._applyDeceleration(bump * 18.0 * deltaTime)
        self.velocity = max(self.maxReverseSpeed, min(self.velocity, self.maxSpeed))

        steer = float(keys[pg.K_a]) - float(keys[pg.K_d])
        speedRatio = min(1.0, abs(self.velocity) / self.maxSpeed)
        steeringWobble = (
            0.65 * math.sin(self.simulationTime * 6.0)
            + 0.35 * math.sin(self.simulationTime * 11.5 + 1.2)
        )
        wobbleAmplitude = (
            5.0 + self.uphillLoad * 15.0
        ) * speedRatio * (0.6 + roughness * 0.4)
        steeringAngle = math.radians(
            self.maxSteeringAngle * steer + steeringWobble * wobbleAmplitude
        )
        turnGrip = max(0.25, 1.0 - roughness * 0.65)
        yawRate = (
            self.velocity / self.wheelbase
            * math.tan(steeringAngle)
            * turnGrip
        ) if speedRatio > 0.01 else 0.0

        slip = min(0.72, 0.05 + roughness * 0.55 + speedRatio * 0.1 + bump * 0.15)
        sideAcceleration = yawRate * self.velocity * slip - sideGrade * 250.0
        self.lateralVelocity += sideAcceleration * deltaTime
        lateralDamping = 4.5 * (1.0 - roughness * 0.8) + 0.4
        self.lateralVelocity *= math.exp(-lateralDamping * deltaTime)
        lateralLimit = max(12.0, abs(self.velocity) * 0.45)
        self.lateralVelocity = max(
            -lateralLimit,
            min(self.lateralVelocity, lateralLimit)
        )

        self.rotation = (
            self.rotation + math.degrees(yawRate * deltaTime) + 180.0
        ) % 360.0 - 180.0
        self.coords[0] += (forwardX * self.velocity + rightX * self.lateralVelocity) * deltaTime
        self.coords[1] += (forwardY * self.velocity + rightY * self.lateralVelocity) * deltaTime

    def render(self, screen, offset=(0.0, 0.0)):
        super().render(screen, offset)
