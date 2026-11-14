import math
from collections import deque
import pygame as pg
from objects.Texture import Texture
from lib.AssetManager import AssetManager
from objects.Chunk import Chunk

class Rover(Texture):
    maxSpeed = 180.0
    maxReverseSpeed = -80.0
    acceleration = 55.0
    braking = 100.0
    rollingResistance = 12.0
    wheelbase = 140.0
    trackWidth = 110.0
    maxSteeringAngle = 35.0
    terrainAccelerationScale = 250.0
    wheelSteeringLimit = 12.0
    wheelSteeringResponse = 9.0
    wheelOffset = 6.0
    wheelTrackSpacing = 5.0
    wheelTrackPointLimit = 3000
    wheelTrackLifetime = 30.0
    wheelTrackOpacity = 0.4
    wheelTrackWidth = 20.0
    wheelTrackPixelSize = 4
    wheelTrackSideOffset = 4.0
    wheelTrackColor = (48, 29, 23, 255)

    def __init__(self):
        super().__init__(
            'rover.base',
            [0.0, 0.0],
            0.0,
            6,
            AssetManager.get('assets.texture.rover.base'),
            100
        )
        self.wheelsTexture = AssetManager.get('assets.texture.rover.wheels')
        self._cachedWheelsRenderScale = None
        self._cachedScaledWheels = None
        self.wheelSteeringInputAngle = 0.0
        self.wheelSteeringWobbleAngle = 0.0
        self.velocity = 0.0
        self.lateralVelocity = 0.0
        self.previousGroundHeight = None
        self.uphillLoad = 0.0
        self.simulationTime = 0.0
        self.wheelTrackPoints = [
            deque(maxlen=self.wheelTrackPointLimit)
            for _ in range(4)
        ]
        self.wheelTrackSampleCounts = [0, 0, 0, 0]
        self._wheelTrackSurfaceSize = None
        self._wheelTrackSurface = None
        self._scaledWheelTrackSurface = None

    def _applyDeceleration(self, deceleration):
        if self.velocity > 0.0:
            self.velocity = max(0.0, self.velocity - deceleration)
        elif self.velocity < 0.0:
            self.velocity = min(0.0, self.velocity + deceleration)

    def applyWind(self, accelerationX, accelerationY, deltaTime):
        if deltaTime <= 0.0:
            return

        forwardX, forwardY, rightX, rightY = self._getDirectionAxes()
        forwardAcceleration = accelerationX * forwardX + accelerationY * forwardY
        sideAcceleration = accelerationX * rightX + accelerationY * rightY
        self.velocity += forwardAcceleration * deltaTime
        self.lateralVelocity += sideAcceleration * deltaTime

    def _getDirectionAxes(self):
        angle = math.radians(self.rotation)
        return (
            -math.sin(angle),
            math.cos(angle),
            math.cos(angle),
            math.sin(angle)
        )

    def _getWheelPositions(self, directionAxes):
        forwardX, forwardY, rightX, rightY = directionAxes
        halfWheelbase = self.wheelbase / 2.0
        halfTrack = self.trackWidth / 2.0
        wheelOffsets = (
            (halfWheelbase, -halfTrack),
            (halfWheelbase, halfTrack),
            (-halfWheelbase, -halfTrack),
            (-halfWheelbase, halfTrack)
        )
        return tuple(
            (
                self.coords[0] + forwardX * along + rightX * across,
                self.coords[1] + forwardY * along + rightY * across
            )
            for along, across in wheelOffsets
        )

    def _updateWheelTracks(self):
        wheelPositions = self._getWheelPositions(self._getDirectionAxes())
        frontWheelHeading = math.radians(
            self.rotation
            + self.wheelSteeringInputAngle
            + self.wheelSteeringWobbleAngle
        )
        rearWheelHeading = math.radians(self.rotation)
        wheelHeadings = (
            frontWheelHeading,
            frontWheelHeading,
            rearWheelHeading,
            rearWheelHeading
        )
        minimumDistanceSquared = self.wheelTrackSpacing ** 2
        for wheelIndex, (points, position, heading) in enumerate(zip(
            self.wheelTrackPoints,
            wheelPositions,
            wheelHeadings
        )):
            sampleIndex = self.wheelTrackSampleCounts[wheelIndex]
            expirationTime = self.simulationTime - self.wheelTrackLifetime
            while points and points[0][4] <= expirationTime:
                points.popleft()

            if not points:
                points.append((
                    *position,
                    heading,
                    sampleIndex,
                    self.simulationTime
                ))
                self.wheelTrackSampleCounts[wheelIndex] += 1
                continue

            lastX, lastY = points[-1][:2]
            deltaX = position[0] - lastX
            deltaY = position[1] - lastY
            if deltaX * deltaX + deltaY * deltaY >= minimumDistanceSquared:
                points.append((
                    *position,
                    heading,
                    sampleIndex,
                    self.simulationTime
                ))
                self.wheelTrackSampleCounts[wheelIndex] += 1

    def _renderWheelTracks(self, screen, offset, screenSize):
        screenWidth, screenHeight = screenSize
        pixelSize = self.wheelTrackPixelSize
        if self._wheelTrackSurfaceSize != screenSize:
            trackSurfaceSize = (
                (screenWidth + pixelSize - 1) // pixelSize,
                (screenHeight + pixelSize - 1) // pixelSize
            )
            self._wheelTrackSurfaceSize = screenSize
            self._wheelTrackSurface = pg.Surface(
                trackSurfaceSize,
                pg.SRCALPHA
            )
            self._scaledWheelTrackSurface = pg.Surface(
                screenSize,
                pg.SRCALPHA
            )
        self._wheelTrackSurface.fill((0, 0, 0, 0))

        scaleFactor = Texture.getScaleFactor(screenSize)
        centerPixelX = round(screenWidth / (2.0 * pixelSize))
        centerPixelY = round(screenHeight / (2.0 * pixelSize))
        cameraPixelX = round(offset[0] * scaleFactor / pixelSize)
        cameraPixelY = round(offset[1] * scaleFactor / pixelSize)
        cameraRemainderX = offset[0] * scaleFactor - cameraPixelX * pixelSize
        cameraRemainderY = offset[1] * scaleFactor - cameraPixelY * pixelSize

        def toPixel(worldPoint):
            worldPixelX = round(worldPoint[0] * scaleFactor / pixelSize)
            worldPixelY = round(worldPoint[1] * scaleFactor / pixelSize)
            return (
                centerPixelX + worldPixelX - cameraPixelX,
                centerPixelY - worldPixelY + cameraPixelY
            )

        halfWidth = screenWidth / (2.0 * scaleFactor) + self.wheelTrackWidth
        halfHeight = screenHeight / (2.0 * scaleFactor) + self.wheelTrackWidth
        minX = offset[0] - halfWidth
        maxX = offset[0] + halfWidth
        minY = offset[1] - halfHeight
        maxY = offset[1] + halfHeight
        lineWidth = max(
            1,
            round(self.wheelTrackWidth * scaleFactor / pixelSize)
        )
        treadWidth = max(1, round(2.0 * scaleFactor / pixelSize))

        for wheelIndex, track in enumerate(self.wheelTrackPoints):
            side = -1.0 if wheelIndex % 2 == 0 else 1.0
            trackPoints = list(track)
            for startPoint, endPoint in zip(
                trackPoints,
                trackPoints[1:]
            ):
                age = max(0.0, self.simulationTime - endPoint[4])
                fade = max(0.0, 1.0 - age / self.wheelTrackLifetime)
                alpha = round(255.0 * self.wheelTrackOpacity * fade)
                if alpha == 0:
                    continue

                startX, startY, startHeading = startPoint[:3]
                endX, endY, endHeading, sampleIndex = endPoint[:4]
                if not (
                    minX <= startX <= maxX
                    and minY <= startY <= maxY
                    and minX <= endX <= maxX
                    and minY <= endY <= maxY
                ):
                    continue

                sideOffsetAmount = self.wheelTrackSideOffset
                sideOffset = sideOffsetAmount / scaleFactor * side
                startCenter = (
                    startX + math.cos(startHeading) * sideOffset,
                    startY + math.sin(startHeading) * sideOffset
                )
                endCenter = (
                    endX + math.cos(endHeading) * sideOffset,
                    endY + math.sin(endHeading) * sideOffset
                )
                color = (*self.wheelTrackColor[:3], alpha)
                pg.draw.line(
                    self._wheelTrackSurface,
                    color,
                    toPixel(startCenter),
                    toPixel(endCenter),
                    lineWidth
                )

                if sampleIndex % 3 == 0:
                    treadHalfWidth = self.wheelTrackWidth * 0.45
                    acrossX = math.cos(endHeading) * treadHalfWidth
                    acrossY = math.sin(endHeading) * treadHalfWidth
                    pg.draw.line(
                        self._wheelTrackSurface,
                        color,
                        toPixel((
                            endCenter[0] - acrossX,
                            endCenter[1] - acrossY
                        )),
                        toPixel((
                            endCenter[0] + acrossX,
                            endCenter[1] + acrossY
                        )),
                        treadWidth
                    )

        pg.transform.scale(
            self._wheelTrackSurface,
            screenSize,
            self._scaledWheelTrackSurface
        )
        screen.blit(
            self._scaledWheelTrackSurface,
            (-round(cameraRemainderX), round(cameraRemainderY)),
            special_flags=pg.BLEND_ALPHA_SDL2
        )

    def update(self, deltaTime=1.0 / 60.0):
        deltaTime = min(max(deltaTime, 0.0), 1.0 / 30.0)
        self.simulationTime += deltaTime

        keys = pg.key.get_pressed()
        throttle = float(keys[pg.K_w]) - float(keys[pg.K_s])
        steer = float(keys[pg.K_a]) - float(keys[pg.K_d])
        directionAxes = self._getDirectionAxes()
        wheelPositions = self._getWheelPositions(directionAxes)
        frontLeft, frontRight, rearLeft, rearRight = (
            Chunk.terrainHeight(*position)
            for position in wheelPositions
        )
        frontGrade = (
            frontLeft + frontRight - rearLeft - rearRight
        ) / (2.0 * self.wheelbase)
        sideGrade = (
            frontRight + rearRight - frontLeft - rearLeft
        ) / (2.0 * self.trackWidth)
        roughness = min(1.0, (abs(frontGrade) + abs(sideGrade)) * 180.0)

        groundHeight = Chunk.terrainPixelHeight(self.coords[0], self.coords[1])
        colorIndex = Chunk.terrainColorIndexFromHeight(groundHeight)
        if self.previousGroundHeight is not None:
            colorRise = max(
                0,
                colorIndex - Chunk.terrainColorIndexFromHeight(
                    self.previousGroundHeight
                )
            )
            heightChange = abs(groundHeight - self.previousGroundHeight)
        else:
            colorRise = 0
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
        if throttle != 0.0:
            driveTime = deltaTime
            if self.velocity * throttle < 0.0:
                # Use the rest of this frame for acceleration after coming to a stop.
                # Tiny downhill drift must not consume every frame's throttle input.
                stopTime = abs(self.velocity) / (self.braking * driveGrip)
                self._applyDeceleration(self.braking * driveGrip * deltaTime)
                driveTime = max(0.0, deltaTime - stopTime)
            self.velocity += throttle * self.acceleration * driveGrip * driveTime
        else:
            resistance = (
                self.rollingResistance
                + abs(self.velocity) * 0.04
                + roughness * 20.0
            )
            self._applyDeceleration(resistance * deltaTime)

        self.velocity -= (
            frontGrade * self.terrainAccelerationScale * deltaTime
        )
        self._applyDeceleration(self.uphillLoad * 35.0 * deltaTime)
        self._applyDeceleration(bump * 18.0 * deltaTime)
        self.velocity = max(
            self.maxReverseSpeed,
            min(self.velocity, self.maxSpeed)
        )

        speedLimit = (
            self.maxSpeed
            if self.velocity >= 0.0
            else abs(self.maxReverseSpeed)
        )
        speedRatio = min(1.0, abs(self.velocity) / speedLimit)
        steeringWobble = (
            0.65 * math.sin(self.simulationTime * 6.0)
            + 0.35 * math.sin(self.simulationTime * 11.5 + 1.2)
        )
        wobbleAmplitude = (
            5.0 + self.uphillLoad * 15.0
        ) * speedRatio * (0.6 + roughness * 0.4)
        self.wheelSteeringInputAngle += (
            self.wheelSteeringLimit * steer - self.wheelSteeringInputAngle
        ) * (1.0 - math.exp(-self.wheelSteeringResponse * deltaTime))
        self.wheelSteeringWobbleAngle = steeringWobble * wobbleAmplitude
        steeringAngle = math.radians(
            self.maxSteeringAngle * steer + self.wheelSteeringWobbleAngle
        )
        turnGrip = max(0.25, 1.0 - roughness * 0.65)
        yawRate = (
            self.velocity / self.wheelbase * math.tan(steeringAngle) * turnGrip
        ) if speedRatio > 0.01 else 0.0

        slip = min(
            0.72,
            0.05 + roughness * 0.55 + speedRatio * 0.1 + bump * 0.15
        )
        sideAcceleration = (
            yawRate * self.velocity * slip
            - sideGrade * self.terrainAccelerationScale
        )
        self.lateralVelocity += sideAcceleration * deltaTime
        lateralDamping = 4.5 * (1.0 - roughness * 0.8) + 0.4
        self.lateralVelocity *= math.exp(-lateralDamping * deltaTime)
        lateralLimit = max(12.0, abs(self.velocity) * 0.45)
        self.lateralVelocity = max(
            -lateralLimit,
            min(self.lateralVelocity, lateralLimit)
        )
        forwardX, forwardY, rightX, rightY = directionAxes
        self.rotation = (
            self.rotation + math.degrees(yawRate * deltaTime) + 180.0
        ) % 360.0 - 180.0
        self.coords[0] += (
            forwardX * self.velocity + rightX * self.lateralVelocity
        ) * deltaTime
        self.coords[1] += (
            forwardY * self.velocity + rightY * self.lateralVelocity
        ) * deltaTime
        self._updateWheelTracks()

    def render(self, screen, offset=(0.0, 0.0)):
        screenSize = screen.get_size()
        center = Texture.worldToScreen(self.coords, screenSize, offset)
        renderScale = self.scale * Texture.getScaleFactor(screenSize)
        self._renderWheelTracks(screen, offset, screenSize)

        if self._cachedWheelsRenderScale != renderScale:
            self._cachedWheelsRenderScale = renderScale
            self._cachedScaledWheels = pg.transform.scale_by(
                self.wheelsTexture,
                renderScale
            )

        wheels = pg.transform.rotate(
            self._cachedScaledWheels,
            self.rotation
            + self.wheelSteeringInputAngle
            + self.wheelSteeringWobbleAngle
        )
        heading = math.radians(self.rotation)
        wheelOffset = self.wheelOffset * renderScale
        wheelCenter = (
            center[0] - math.sin(heading) * wheelOffset,
            center[1] - math.cos(heading) * wheelOffset
        )
        screen.blit(wheels, wheels.get_rect(center=wheelCenter))
        super().render(screen, offset)
