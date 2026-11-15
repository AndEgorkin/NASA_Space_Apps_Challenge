import math
import random
from collections import deque
import pygame as pg
from objects.BoundingBox import BoundingBox
from objects.Texture import Texture
from lib.AssetManager import AssetManager
from lib.EnvironmentManager import EnvironmentManager
from objects.Chunk import Chunk

class Rover:
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
    texture = AssetManager.get('assets.texture.rover.base')
    wheelsTexture = AssetManager.get('assets.texture.rover.wheels')
    hudFont = AssetManager.get('assets.font.cairopixel')
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

    @classmethod
    def adjustPower(cls, wheelDelta):
        cls.powerPercent = max(
            cls.minimumPowerPercent,
            min(
                cls.maximumPowerPercent,
                cls.powerPercent + wheelDelta * cls.powerChangeStepPercent
            )
        )

    @classmethod
    def _applyDeceleration(cls, deceleration):
        if cls.velocity > 0.0:
            cls.velocity = max(0.0, cls.velocity - deceleration)
        elif cls.velocity < 0.0:
            cls.velocity = min(0.0, cls.velocity + deceleration)

    @classmethod
    def applyWind(cls, accelerationX, accelerationY, deltaTime):
        if deltaTime <= 0.0:
            return

        forwardX, forwardY, rightX, rightY = cls._getDirectionAxes()
        forwardAcceleration = accelerationX * forwardX + accelerationY * forwardY
        sideAcceleration = accelerationX * rightX + accelerationY * rightY
        cls.velocity += forwardAcceleration * deltaTime
        cls.lateralVelocity += sideAcceleration * deltaTime

    @classmethod
    def _getDirectionAxes(cls):
        angle = math.radians(cls.rotation)
        return (
            -math.sin(angle),
            math.cos(angle),
            math.cos(angle),
            math.sin(angle)
        )

    @classmethod
    def _getWheelPositions(cls, directionAxes):
        forwardX, forwardY, rightX, rightY = directionAxes
        halfWheelbase = cls.wheelbase / 2.0
        halfTrack = cls.trackWidth / 2.0
        wheelOffsets = (
            (halfWheelbase, -halfTrack),
            (halfWheelbase, halfTrack),
            (-halfWheelbase, -halfTrack),
            (-halfWheelbase, halfTrack)
        )
        return tuple(
            (
                cls.coords[0] + forwardX * along + rightX * across,
                cls.coords[1] + forwardY * along + rightY * across
            )
            for along, across in wheelOffsets
        )

    @classmethod
    def _updateWheelTracks(cls):
        wheelPositions = cls._getWheelPositions(cls._getDirectionAxes())
        frontWheelHeading = math.radians(
            cls.rotation
            + cls.wheelSteeringInputAngle
            + cls.wheelSteeringWobbleAngle
        )
        rearWheelHeading = math.radians(cls.rotation)
        wheelHeadings = (
            frontWheelHeading,
            frontWheelHeading,
            rearWheelHeading,
            rearWheelHeading
        )
        minimumDistanceSquared = cls.wheelTrackSpacing ** 2
        for wheelIndex, (points, position, heading) in enumerate(zip(
            cls.wheelTrackPoints,
            wheelPositions,
            wheelHeadings
        )):
            sampleIndex = cls.wheelTrackSampleCounts[wheelIndex]
            expirationTime = cls.simulationTime - cls.wheelTrackLifetime
            while points and points[0][4] <= expirationTime:
                points.popleft()

            if not points:
                points.append((
                    *position,
                    heading,
                    sampleIndex,
                    cls.simulationTime
                ))
                cls.wheelTrackSampleCounts[wheelIndex] += 1
                continue

            lastX, lastY = points[-1][:2]
            deltaX = position[0] - lastX
            deltaY = position[1] - lastY
            if deltaX * deltaX + deltaY * deltaY >= minimumDistanceSquared:
                points.append((
                    *position,
                    heading,
                    sampleIndex,
                    cls.simulationTime
                ))
                cls.wheelTrackSampleCounts[wheelIndex] += 1

    @classmethod
    def _renderWheelTracks(cls, screen, offset, screenSize):
        screenWidth, screenHeight = screenSize
        pixelSize = max(
            1,
            round(cls.wheelTrackPixelSize * Texture.zoomFactor)
        )
        if (
            cls._wheelTrackSurfaceSize != screenSize
            or cls._wheelTrackSurfacePixelSize != pixelSize
        ):
            trackSurfaceSize = (
                (screenWidth + pixelSize - 1) // pixelSize,
                (screenHeight + pixelSize - 1) // pixelSize
            )
            cls._wheelTrackSurfaceSize = screenSize
            cls._wheelTrackSurfacePixelSize = pixelSize
            cls._wheelTrackSurface = pg.Surface(
                trackSurfaceSize,
                pg.SRCALPHA
            )
            cls._scaledWheelTrackSurface = pg.Surface(
                screenSize,
                pg.SRCALPHA
            )
        cls._wheelTrackSurface.fill((0, 0, 0, 0))

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

        halfWidth = screenWidth / (2.0 * scaleFactor) + cls.wheelTrackWidth
        halfHeight = screenHeight / (2.0 * scaleFactor) + cls.wheelTrackWidth
        minX = offset[0] - halfWidth
        maxX = offset[0] + halfWidth
        minY = offset[1] - halfHeight
        maxY = offset[1] + halfHeight
        lineWidth = max(
            1,
            round(cls.wheelTrackWidth * scaleFactor / pixelSize)
        )
        treadWidth = max(1, round(2.0 * scaleFactor / pixelSize))

        for wheelIndex, track in enumerate(cls.wheelTrackPoints):
            side = -1.0 if wheelIndex % 2 == 0 else 1.0
            trackPoints = list(track)
            for startPoint, endPoint in zip(
                trackPoints,
                trackPoints[1:]
            ):
                age = max(0.0, cls.simulationTime - endPoint[4])
                fade = max(0.0, 1.0 - age / cls.wheelTrackLifetime)
                alpha = round(255.0 * cls.wheelTrackOpacity * fade)
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

                sideOffsetAmount = cls.wheelTrackSideOffset
                sideOffset = sideOffsetAmount / scaleFactor * side
                startCenter = (
                    startX + math.cos(startHeading) * sideOffset,
                    startY + math.sin(startHeading) * sideOffset
                )
                endCenter = (
                    endX + math.cos(endHeading) * sideOffset,
                    endY + math.sin(endHeading) * sideOffset
                )
                color = (*cls.wheelTrackColor[:3], alpha)
                pg.draw.line(
                    cls._wheelTrackSurface,
                    color,
                    toPixel(startCenter),
                    toPixel(endCenter),
                    lineWidth
                )

                if sampleIndex % 3 == 0:
                    treadHalfWidth = cls.wheelTrackWidth * 0.45
                    acrossX = math.cos(endHeading) * treadHalfWidth
                    acrossY = math.sin(endHeading) * treadHalfWidth
                    pg.draw.line(
                        cls._wheelTrackSurface,
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
            cls._wheelTrackSurface,
            screenSize,
            cls._scaledWheelTrackSurface
        )
        screen.blit(
            cls._scaledWheelTrackSurface,
            (-round(cameraRemainderX), round(cameraRemainderY)),
            special_flags=pg.BLEND_ALPHA_SDL2
        )

    @classmethod
    def update(cls, deltaTime=1.0 / 60.0):
        if cls.gameOver:
            return
        deltaTime = min(max(deltaTime, 0.0), 1.0 / 30.0)
        cls.simulationTime += deltaTime

        if cls.systemsOn:
            keys = pg.key.get_pressed()
            throttle = float(keys[pg.K_w]) - float(keys[pg.K_s])
            steer = (
                float(keys[pg.K_a]) - float(keys[pg.K_d])
                if cls.charge > 0.0
                else 0.0
            )
        else:
            throttle = 0.0
            steer = 0.0
        directionAxes = cls._getDirectionAxes()
        wheelPositions = cls._getWheelPositions(directionAxes)
        frontLeft, frontRight, rearLeft, rearRight = (
            Chunk.terrainHeight(*position)
            for position in wheelPositions
        )
        frontGrade = (
            frontLeft + frontRight - rearLeft - rearRight
        ) / (2.0 * cls.wheelbase)
        sideGrade = (
            frontRight + rearRight - frontLeft - rearLeft
        ) / (2.0 * cls.trackWidth)
        roughness = min(1.0, (abs(frontGrade) + abs(sideGrade)) * 180.0)

        groundHeight = Chunk.terrainPixelHeight(cls.coords[0], cls.coords[1])
        colorIndex = Chunk.terrainColorIndexFromHeight(groundHeight)
        if cls.previousGroundHeight is not None:
            colorRise = max(
                0,
                colorIndex - Chunk.terrainColorIndexFromHeight(
                    cls.previousGroundHeight
                )
            )
            heightChange = abs(groundHeight - cls.previousGroundHeight)
        else:
            colorRise = 0
            heightChange = 0.0
        cls.previousGroundHeight = groundHeight
        bump = min(1.0, max(0.0, heightChange * 18.0 - 0.04))
        uphillTarget = min(0.35, colorRise * 0.22)
        cls.uphillLoad = max(
            uphillTarget,
            cls.uphillLoad * math.exp(-2.8 * deltaTime)
        )

        driveGrip = max(
            0.35,
            1.0 - roughness * 0.55 - bump * 0.15 - cls.uphillLoad * 0.2
        )
        surfaceTemperature = EnvironmentManager.surfaceTemperatureC
        engineAmbientTemperature = max(
            cls.engineMinimumTemperatureC,
            surfaceTemperature
        )
        cls.engineTemperatureC += (
            engineAmbientTemperature - cls.engineTemperatureC
        ) * (1.0 - math.exp(-cls.engineCoolingRate * deltaTime))
        coldPowerLoss = max(
            0.0,
            cls.engineColdTemperatureC - cls.engineTemperatureC
        ) * cls.engineColdPowerScale
        overheatPowerLoss = max(
            0.0,
            cls.engineTemperatureC - cls.engineOverheatTemperatureC
        ) * cls.engineOverheatPowerScale
        enginePower = max(0.4, 1.0 - coldPowerLoss - overheatPowerLoss)
        surfaceGrip = max(
            0.6,
            1.0
            - max(0.0, -40.0 - surfaceTemperature) * 0.003
            - EnvironmentManager.stormIntensity * 0.1
        )
        driveGrip *= surfaceGrip
        if throttle != 0.0 and cls.velocity * throttle < 0.0:
            cls._applyDeceleration(cls.braking * driveGrip * deltaTime)
        elif throttle != 0.0 and cls.charge > 0.0:
            powerScale = cls.powerPercent / 100.0
            cls.velocity += (
                throttle
                * cls.acceleration
                * powerScale
                * enginePower
                * driveGrip
                * deltaTime
            )
            cls.engineTemperatureC = min(
                cls.engineMaximumTemperatureC,
                max(
                    cls.engineMinimumTemperatureC,
                    cls.engineTemperatureC
                    + cls.engineHeatingRate
                    * abs(throttle)
                    * powerScale
                    * deltaTime
                )
            )
            chargeDrainMultiplier = (
                1.0
                + EnvironmentManager.nightBlend * cls.nightEnergyMultiplier
                + max(0.0, -30.0 - surfaceTemperature)
                * cls.coldEnergyMultiplier
                + EnvironmentManager.stormIntensity
                * cls.stormEnergyMultiplier
            ) * (
                1.0
                + max(
                    0.0,
                    cls.engineTemperatureC - cls.engineOverheatTemperatureC
                ) * cls.engineOverheatPowerScale
            )
            cls.charge = max(
                0.0,
                cls.charge
                - abs(throttle)
                * powerScale
                * chargeDrainMultiplier
                * deltaTime
            )
        else:
            resistance = (
                cls.rollingResistance
                + abs(cls.velocity) * 0.04
                + roughness * 20.0
            )
            cls._applyDeceleration(resistance * deltaTime)

        if cls.energyLeakTimeRemaining > 0.0:
            cls.energyLeakTimeRemaining = max(
                0.0,
                cls.energyLeakTimeRemaining - deltaTime
            )
            cls.energyLeakActive = cls.energyLeakTimeRemaining > 0.0
        else:
            coldExposure = max(
                0.0,
                min(
                    1.0,
                    (cls.energyLeakTemperatureC - cls.engineTemperatureC)
                    / cls.energyLeakTemperatureRangeC
                )
            )
            if cls.engineTemperatureC < cls.energyLeakTemperatureC:
                coldExposure = 0.5 + coldExposure * 0.5
            leakChance = 1.0 - math.exp(
                -cls.energyLeakEventRate
                * EnvironmentManager.nightBlend
                * coldExposure
                * deltaTime
            )
            cls.energyLeakActive = random.random() < leakChance
            if cls.energyLeakActive:
                cls.energyLeakTimeRemaining = cls.energyLeakDuration
        if cls.energyLeakActive:
            cls.charge = max(
                0.0,
                cls.charge - cls.energyLeakDrainRate * deltaTime
            )
        if cls.charge <= 0.0:
            cls.gameOver = True

        cls.velocity -= (
            frontGrade * cls.terrainAccelerationScale * deltaTime
        )
        cls._applyDeceleration(cls.uphillLoad * 35.0 * deltaTime)
        cls._applyDeceleration(bump * 18.0 * deltaTime)
        cls.velocity = max(
            cls.maxReverseSpeed,
            min(cls.velocity, cls.maxSpeed)
        )

        speedLimit = (
            cls.maxSpeed
            if cls.velocity >= 0.0
            else abs(cls.maxReverseSpeed)
        )
        speedRatio = min(1.0, abs(cls.velocity) / speedLimit)
        steeringWobble = (
            0.65 * math.sin(cls.simulationTime * 6.0)
            + 0.35 * math.sin(cls.simulationTime * 11.5 + 1.2)
        )
        wobbleAmplitude = (
            5.0 + cls.uphillLoad * 15.0
        ) * speedRatio * (0.6 + roughness * 0.4)
        cls.wheelSteeringInputAngle += (
            cls.wheelSteeringLimit * steer - cls.wheelSteeringInputAngle
        ) * (1.0 - math.exp(-cls.wheelSteeringResponse * deltaTime))
        cls.wheelSteeringWobbleAngle = steeringWobble * wobbleAmplitude
        steeringAngle = math.radians(
            cls.maxSteeringAngle * steer + cls.wheelSteeringWobbleAngle
        )
        turnGrip = max(0.25, 1.0 - roughness * 0.65)
        yawRate = (
            cls.velocity / cls.wheelbase * math.tan(steeringAngle) * turnGrip
        ) if speedRatio > 0.01 else 0.0

        slip = min(
            0.72,
            0.05 + roughness * 0.55 + speedRatio * 0.1 + bump * 0.15
        )
        sideAcceleration = (
            yawRate * cls.velocity * slip
            - sideGrade * cls.terrainAccelerationScale
        )
        cls.lateralVelocity += sideAcceleration * deltaTime
        lateralDamping = 4.5 * (1.0 - roughness * 0.8) + 0.4
        cls.lateralVelocity *= math.exp(-lateralDamping * deltaTime)
        lateralLimit = max(12.0, abs(cls.velocity) * 0.45)
        cls.lateralVelocity = max(
            -lateralLimit,
            min(cls.lateralVelocity, lateralLimit)
        )
        forwardX, forwardY, rightX, rightY = directionAxes
        cls.rotation = (
            cls.rotation + math.degrees(yawRate * deltaTime) + 180.0
        ) % 360.0 - 180.0
        nextCoords = (
            cls.coords[0] + (
                forwardX * cls.velocity + rightX * cls.lateralVelocity
            ) * deltaTime,
            cls.coords[1] + (
                forwardY * cls.velocity + rightY * cls.lateralVelocity
            ) * deltaTime
        )
        roverBoundingBox = BoundingBox(
            nextCoords,
            cls.texture.get_width() * cls.scale * 0.8,
            cls.texture.get_height() * cls.scale * 0.8,
            cls.rotation
        )
        collidedBox = next(
            (
                boundingBox
                for boundingBox in cls.boundingBoxes
                if boundingBox.intersects(roverBoundingBox)
            ),
            None
        )
        if collidedBox is not None:
            movementX = nextCoords[0] - cls.coords[0]
            movementY = nextCoords[1] - cls.coords[1]
            movementLength = math.hypot(movementX, movementY)
            if movementLength > 0.0:
                recoilX = -movementX / movementLength
                recoilY = -movementY / movementLength
            else:
                recoilX = cls.coords[0] - collidedBox.coords[0]
                recoilY = cls.coords[1] - collidedBox.coords[1]
                recoilLength = math.hypot(recoilX, recoilY)
                if recoilLength == 0.0:
                    forwardX, forwardY, _, _ = cls._getDirectionAxes()
                    recoilX = -forwardX
                    recoilY = -forwardY
                else:
                    recoilX /= recoilLength
                    recoilY /= recoilLength

            cls.coords[0] += recoilX * 4.0
            cls.coords[1] += recoilY * 4.0
            cls.velocity = 0.0
            cls.lateralVelocity = 0.0
        else:
            cls.coords[0], cls.coords[1] = nextCoords
        if math.hypot(cls.velocity, cls.lateralVelocity) <= (
            cls.stationarySpeedThreshold
        ):
            cls.stationaryTime += deltaTime
        else:
            cls.stationaryTime = 0.0
        cls.isCharging = (
            not cls.gameOver
            and EnvironmentManager.nightBlend < 0.5
            and cls.stationaryTime >= cls.stationaryRechargeDelay
            and cls.charge < 100.0
        )
        if cls.isCharging:
            cls.charge = min(
                100.0,
                cls.charge + cls.stationaryRechargeRate * deltaTime
            )
        cls._updateWheelTracks()

    @classmethod
    def render(cls, screen, offset=(0.0, 0.0)):
        screenSize = screen.get_size()
        center = Texture.worldToScreen(cls.coords, screenSize, offset)
        renderScale = cls.scale * Texture.getScaleFactor(screenSize)
        cls._renderWheelTracks(screen, offset, screenSize)

        if cls._cachedWheelsRenderScale != renderScale:
            cls._cachedWheelsRenderScale = renderScale
            cls._cachedScaledWheels = pg.transform.scale_by(
                cls.wheelsTexture,
                renderScale
            )

        wheels = pg.transform.rotate(
            cls._cachedScaledWheels,
            cls.rotation
            + cls.wheelSteeringInputAngle
            + cls.wheelSteeringWobbleAngle
        )
        heading = math.radians(cls.rotation)
        wheelOffset = cls.wheelOffset * renderScale
        wheelCenter = (
            center[0] - math.sin(heading) * wheelOffset,
            center[1] - math.cos(heading) * wheelOffset
        )
        screen.blit(wheels, wheels.get_rect(center=wheelCenter))
        Texture.render(cls, screen, offset)

    @classmethod
    def renderHud(cls, screen):
        condition = 'NIGHT' if EnvironmentManager.nightBlend >= 0.5 else 'DAY'
        if EnvironmentManager.stormIntensity > 0.05:
            condition += ' / STORM'
        localHour = int(EnvironmentManager.displayedLocalTimeHour)
        localMinute = int(
            (EnvironmentManager.displayedLocalTimeHour - localHour) * 60.0
        )
        labels = (
            f'CHARGE {cls.charge:3.0f}%',
            f'POWER {cls.powerPercent:3.0f}%',
            f'ENGINE {cls.engineTemperatureC:+.0f}°C',
            f'SURFACE {EnvironmentManager.surfaceTemperatureC:+.0f}°C',
            condition
        )
        if cls.isCharging:
            labels += ('CHARGING',)
        lineHeight = cls.hudFont.get_linesize() + 6
        for lineIndex, label in enumerate(labels):
            text = cls.hudFont.render(label, True, (255, 255, 255))
            screen.blit(text, (24, 20 + lineIndex * lineHeight))
        messages = []
        if EnvironmentManager.solarFlareActive:
            messages.append('DANGER: SOLAR FLARE')
        if EnvironmentManager.stormIntensity > 0.05:
            messages.append('WARNING: SANDSTORM')
        if cls.engineTemperatureC >= cls.engineOverheatTemperatureC:
            messages.append('WARNING: ENGINE OVERHEATING')
        if cls.energyLeakActive:
            messages.append('WARNING: ENERGY LEAK')
        if cls.charge <= 20.0:
            messages.append('WARNING: LOW CHARGE')
        messageY = 20 + len(labels) * lineHeight
        for messageIndex, message in enumerate(messages):
            text = cls.hudFont.render(message, True, (255, 48, 48))
            screen.blit(text, (24, messageY + messageIndex * lineHeight))
        timeLabel = cls.hudFont.render(
            f'{localHour:02d}:{localMinute:02d} LMST',
            True,
            (255, 255, 255)
        )
        screen.blit(
            timeLabel,
            timeLabel.get_rect(topright=(screen.get_width() - 24, 20))
        )

    @classmethod
    def renderSystemsButton(cls, screen):
        label = '[on]' if cls.systemsOn else '[off]'
        color = (80, 255, 110) if cls.systemsOn else (255, 70, 70)
        text = cls.hudFont.render(label, True, color)
        textRect = text.get_rect(
            bottomright=(screen.get_width() - 24, screen.get_height() - 24)
        )
        cls.systemsButtonRect = textRect.inflate(24, 16)
        pg.draw.rect(screen, color, cls.systemsButtonRect, 2)
        screen.blit(text, textRect)

    @classmethod
    def renderGameOver(cls, screen):
        if (pg.time.get_ticks() // 500) % 2 == 0:
            text = cls.hudFont.render(
                '[SIGNAL LOST]',
                True,
                (255, 48, 48)
            )
            screen.blit(text, text.get_rect(center=screen.get_rect().center))
