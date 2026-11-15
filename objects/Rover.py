import math
import random
from collections import deque
import pygame as pg
from objects.BoundingBox import BoundingBox
from objects.Texture import Texture
from lib.AssetManager import AssetManager
from lib.EnvironmentManager import EnvironmentManager
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
    engineMinimumTemperatureC = -20.0
    engineMaximumTemperatureC = 75.0
    engineHeatingRate = 0.3
    engineCoolingRate = 0.01
    engineOverheatTemperatureC = 45.0
    engineColdTemperatureC = -10.0
    engineColdPowerScale = 0.006
    engineOverheatPowerScale = 0.02
    nightEnergyMultiplier = 0.5
    coldEnergyMultiplier = 0.015
    stormEnergyMultiplier = 0.2
    stationarySpeedThreshold = 1.0
    stationaryRechargeDelay = 3.0
    stationaryRechargeRate = 2.0
    energyLeakTemperatureC = 5.0
    energyLeakTemperatureRangeC = 10.0
    energyLeakEventRate = 1.0 / 20.0
    energyLeakDuration = 20.0
    energyLeakDrainRate = 0.8
    minimumPowerPercent = 0.0
    maximumPowerPercent = 200.0
    powerChangeStepPercent = 5.0
    powerPercent = 100.0
    charge = 100.0
    engineTemperatureC = 20.0
    stationaryTime = 0.0
    isCharging = False
    energyLeakTimeRemaining = 0.0
    energyLeakActive = False
    systemsOn = True
    gameOver = False
    systemsButtonRect = pg.Rect(0, 0, 0, 0)
    coords = [0.0, 0.0]
    rotation = 0.0
    scale = 6.0
    priority = float('inf')
    _cachedFactor = None
    _cachedScaledTexture = None
    _cachedWheelsRenderScale = None
    _cachedScaledWheels = None
    wheelSteeringInputAngle = 0.0
    wheelSteeringWobbleAngle = 0.0
    velocity = 0.0
    lateralVelocity = 0.0
    boundingBoxes = []
    previousGroundHeight = None
    uphillLoad = 0.0
    simulationTime = 0.0
    wheelTrackPoints = [deque(maxlen=3000) for _ in range(4)]
    wheelTrackSampleCounts = [0, 0, 0, 0]
    _wheelTrackSurfaceSize = None
    _wheelTrackSurfacePixelSize = None
    _wheelTrackSurface = None
    _scaledWheelTrackSurface = None

    def __init__(self):
        super().__init__(
            'rover.base',
            [0.0, 0.0],
            0.0,
            6,
            AssetManager.get('assets.texture.rover.base'),
            float('inf')
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

        self.hudFont = AssetManager.get('assets.font.cairopixel')
        self.boundingBoxes = []
        self.systemsButtonRect = pg.Rect(0, 0, 0, 0)
        self.resetSystems()

    def resetSystems(self):
        self.charge = 100.0
        self.powerPercent = 100.0
        self.engineTemperatureC = 20.0
        self.stationaryTime = 0.0
        self.isCharging = False
        self.energyLeakTimeRemaining = 0.0
        self.energyLeakActive = False
        self.systemsOn = True
        self.gameOver = False
        self.velocity = 0.0
        self.lateralVelocity = 0.0

    def adjustPower(self, wheelDelta):
        self.powerPercent = max(
            self.minimumPowerPercent,
            min(
                self.maximumPowerPercent,
                self.powerPercent + wheelDelta * self.powerChangeStepPercent
            )
        )

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
        pixelSize = max(
            1,
            round(self.wheelTrackPixelSize * Texture.zoomFactor)
        )
        if (
            self._wheelTrackSurfaceSize != screenSize
            or self._wheelTrackSurfacePixelSize != pixelSize
        ):
            trackSurfaceSize = (
                (screenWidth + pixelSize - 1) // pixelSize,
                (screenHeight + pixelSize - 1) // pixelSize
            )
            self._wheelTrackSurfaceSize = screenSize
            self._wheelTrackSurfacePixelSize = pixelSize
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

    def _collisionBox(self, coords=None, rotation=None):
        return BoundingBox(self.coords if coords is None else coords,
                           self.texture.get_width()*self.scale*0.8,
                           self.texture.get_height()*self.scale*0.8,
                           self.rotation if rotation is None else rotation)

    def _blockedPose(self, coords, rotation):
        roverBox=self._collisionBox(coords,rotation)
        return any(roverBox.penetration(obstacle) is not None for obstacle in self.boundingBoxes)

    def _moveWithCollisions(self, movement, rotationDelta):
        collided=False
        # Recover from an already overlapping pose without a blind backwards kick.
        for _ in range(16):
            roverBox=self._collisionBox()
            correction=next((vector for obstacle in self.boundingBoxes
                             if (vector:=roverBox.penetration(obstacle)) is not None),None)
            if correction is None:break
            self.coords[0]+=correction[0];self.coords[1]+=correction[1]
            collided=True
        radius=math.hypot(self.texture.get_width(),self.texture.get_height())*self.scale*0.4
        # Account for corner travel during a turn as well as center translation.
        stepLimit=min([4.0]+[max(0.1,min(box.halfWidth,box.halfHeight)/2) for box in self.boundingBoxes])
        steps=max(1,math.ceil((math.hypot(*movement)+abs(math.radians(rotationDelta))*radius)/stepLimit))
        dx,dy=movement[0]/steps,movement[1]/steps
        turn=rotationDelta/steps
        for _ in range(steps):
            angle=(self.rotation+turn+180)%360-180
            candidate=(self.coords[0]+dx,self.coords[1]+dy)
            if not self._blockedPose(candidate,angle):
                self.coords[:]=candidate;self.rotation=angle
                continue
            collided=True
            # Reject only blocked components: let a rover slide along a rock face.
            if not self._blockedPose(self.coords,angle):self.rotation=angle
            for axis,amount in sorted(((0,dx),(1,dy)),key=lambda item:abs(item[1]),reverse=True):
                candidate=list(self.coords);candidate[axis]+=amount
                if not self._blockedPose(candidate,self.rotation):self.coords[:]=candidate
        if collided:
            self.velocity=0.0
            self.lateralVelocity=0.0
        return collided

    def update(self, deltaTime=1.0 / 60.0, controlsEnabled=True):
        if self.gameOver:
            return
        deltaTime = min(max(deltaTime, 0.0), 1.0 / 30.0)
        self.simulationTime += deltaTime

        if self.systemsOn and controlsEnabled:
            keys = pg.key.get_pressed()
            throttle = float(keys[pg.K_w]) - float(keys[pg.K_s])
            steer = (
                float(keys[pg.K_a]) - float(keys[pg.K_d])
                if self.charge > 0.0
                else 0.0
            )
        else:
            throttle = 0.0
            steer = 0.0
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
        surfaceTemperature = EnvironmentManager.surfaceTemperatureC
        engineAmbientTemperature = max(
            self.engineMinimumTemperatureC,
            surfaceTemperature
        )
        self.engineTemperatureC += (
            engineAmbientTemperature - self.engineTemperatureC
        ) * (1.0 - math.exp(-self.engineCoolingRate * deltaTime))
        coldPowerLoss = max(
            0.0,
            self.engineColdTemperatureC - self.engineTemperatureC
        ) * self.engineColdPowerScale
        overheatPowerLoss = max(
            0.0,
            self.engineTemperatureC - self.engineOverheatTemperatureC
        ) * self.engineOverheatPowerScale
        enginePower = max(0.4, 1.0 - coldPowerLoss - overheatPowerLoss)
        surfaceGrip = max(
            0.6,
            1.0
            - max(0.0, -40.0 - surfaceTemperature) * 0.003
            - EnvironmentManager.stormIntensity * 0.1
        )
        driveGrip *= surfaceGrip
        driveTime = deltaTime
        if throttle != 0.0 and self.velocity * throttle < 0.0:
            stopTime = abs(self.velocity) / (self.braking * driveGrip)
            self._applyDeceleration(self.braking * driveGrip * deltaTime)
            driveTime = max(0.0, deltaTime - stopTime)
        if throttle != 0.0 and self.charge > 0.0:
            powerScale = self.powerPercent / 100.0
            self.velocity += (
                throttle * self.acceleration * powerScale * enginePower * driveGrip * driveTime
            )
            self.engineTemperatureC = min(
                self.engineMaximumTemperatureC,
                max(
                    self.engineMinimumTemperatureC,
                    self.engineTemperatureC
                    + self.engineHeatingRate
                    * abs(throttle)
                    * powerScale
                    * deltaTime
                )
            )
            chargeDrainMultiplier = (
                1.0
                + EnvironmentManager.nightBlend * self.nightEnergyMultiplier
                + max(0.0, -30.0 - surfaceTemperature)
                * self.coldEnergyMultiplier
                + EnvironmentManager.stormIntensity
                * self.stormEnergyMultiplier
            ) * (
                1.0
                + max(
                    0.0,
                    self.engineTemperatureC - self.engineOverheatTemperatureC
                ) * self.engineOverheatPowerScale
            )
            self.charge = max(
                0.0,
                self.charge
                - abs(throttle)
                * powerScale
                * chargeDrainMultiplier
                * deltaTime
            )
        else:
            resistance = (
                self.rollingResistance
                + abs(self.velocity) * 0.04
                + roughness * 20.0
            )
            self._applyDeceleration(resistance * deltaTime)

        if self.energyLeakTimeRemaining > 0.0:
            self.energyLeakTimeRemaining = max(
                0.0,
                self.energyLeakTimeRemaining - deltaTime
            )
            self.energyLeakActive = self.energyLeakTimeRemaining > 0.0
        else:
            coldExposure = max(
                0.0,
                min(
                    1.0,
                    (self.energyLeakTemperatureC - self.engineTemperatureC)
                    / self.energyLeakTemperatureRangeC
                )
            )
            if self.engineTemperatureC < self.energyLeakTemperatureC:
                coldExposure = 0.5 + coldExposure * 0.5
            leakChance = 1.0 - math.exp(
                -self.energyLeakEventRate
                * EnvironmentManager.nightBlend
                * coldExposure
                * deltaTime
            )
            self.energyLeakActive = random.random() < leakChance
            if self.energyLeakActive:
                self.energyLeakTimeRemaining = self.energyLeakDuration
        if self.energyLeakActive:
            self.charge = max(
                0.0,
                self.charge - self.energyLeakDrainRate * deltaTime
            )
        if self.charge <= 0.0:
            self.gameOver = True

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
        movement=((forwardX*self.velocity+rightX*self.lateralVelocity)*deltaTime,
                  (forwardY*self.velocity+rightY*self.lateralVelocity)*deltaTime)
        self._moveWithCollisions(movement,math.degrees(yawRate*deltaTime))
        if math.hypot(self.velocity, self.lateralVelocity) <= (
            self.stationarySpeedThreshold
        ):
            self.stationaryTime += deltaTime
        else:
            self.stationaryTime = 0.0
        self.isCharging = (
            not self.gameOver
            and EnvironmentManager.nightBlend < 0.5
            and self.stationaryTime >= self.stationaryRechargeDelay
            and self.charge < 100.0
        )
        if self.isCharging:
            self.charge = min(
                100.0,
                self.charge + self.stationaryRechargeRate * deltaTime
            )
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
        Texture.render(self, screen, offset)

    def renderHud(self, screen):
        condition = 'NIGHT' if EnvironmentManager.nightBlend >= 0.5 else 'DAYLIGHT'
        if EnvironmentManager.stormIntensity > 0.05:
            condition += ' / STORM'
        labels = (
            f'CHARGE {self.charge:3.0f}%',
            f'POWER {self.powerPercent:3.0f}%',
            f'ENGINE {self.engineTemperatureC:+.0f}°C',
            f'SURFACE {EnvironmentManager.surfaceTemperatureC:+.0f}°C',
            condition
        )
        if self.isCharging:
            labels += ('CHARGING',)
        lineHeight = self.hudFont.get_linesize() + 6
        for lineIndex, label in enumerate(labels):
            text = self.hudFont.render(label, True, (255, 255, 255))
            screen.blit(text, (24, 90 + lineIndex * lineHeight))
        messages = []
        if EnvironmentManager.solarFlareActive:
            messages.append('DANGER: SOLAR FLARE')
        if EnvironmentManager.stormIntensity > 0.05:
            messages.append('WARNING: SANDSTORM')
        if self.engineTemperatureC >= self.engineOverheatTemperatureC:
            messages.append('WARNING: ENGINE OVERHEATING')
        if self.energyLeakActive:
            messages.append('WARNING: ENERGY LEAK')
        if self.charge <= 20.0:
            messages.append('WARNING: LOW CHARGE')
        messageY = 90 + len(labels) * lineHeight
        for messageIndex, message in enumerate(messages):
            text = self.hudFont.render(message, True, (255, 48, 48))
            screen.blit(text, (24, messageY + messageIndex * lineHeight))
        timeLabel = self.hudFont.render(
            EnvironmentManager.clockLabel(),
            True,
            (255, 255, 255)
        )
        screen.blit(
            timeLabel,
            timeLabel.get_rect(topright=(screen.get_width() - 24, 20))
        )

    def renderSystemsButton(self, screen):
        label = '[on]' if self.systemsOn else '[off]'
        color = (80, 255, 110) if self.systemsOn else (255, 70, 70)
        text = self.hudFont.render(label, True, color)
        textRect = text.get_rect(
            bottomright=(screen.get_width() - 24, screen.get_height() - 24)
        )
        self.systemsButtonRect = textRect.inflate(24, 16)
        pg.draw.rect(screen, color, self.systemsButtonRect, 2)
        screen.blit(text, textRect)

    def renderGameOver(self, screen):
        if (pg.time.get_ticks() // 500) % 2 == 0:
            text = self.hudFont.render(
                '[SIGNAL LOST]',
                True,
                (255, 48, 48)
            )
            screen.blit(text, text.get_rect(center=screen.get_rect().center))
