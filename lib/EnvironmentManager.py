import math
import random
import pygame as pg
from objects.Texture import Texture

class EnvironmentManager:
    solDuration = 180.0
    clockUpdateInterval = 2.0
    hourlySurfaceTemperaturesC = (
        -70.0, -74.0, -77.0, -79.0, -80.0, -80.0,
        -80.0, -74.0, -63.0, -53.0, -43.0, -36.0,
        -30.0, -26.0, -23.0, -24.0, -26.0, -32.0,
        -38.0, -47.0, -55.0, -60.0, -64.0, -67.0
    )
    stormDayCoolingC = 12.0
    stormNightWarmingC = 15.0
    stormCheckInterval = 30.0
    stormDuration = 30.0
    stormTransitionDuration = 15.0
    stormChance = 0.2
    sandstormOnStart = False
    solarFlareCheckInterval = 45.0
    solarFlareChance = 0.25
    solarFlarePixelCount = 1200
    solarFlareInitialPixelCount = 4
    solarFlareRampDuration = 8.0
    solarFlareRecoveryDuration = 4.0
    solarFlareOnStart = False
    dustParticleCount = 24
    windAcceleration = 90.0
    nightAlpha = 155
    dayAlpha = 18
    vignetteAlpha = 55
    angleSteps = 12
    startingLocalTimeHour = 12.0
    isDay = True
    dayNightTimer = (
        (startingLocalTimeHour - 12.0) / 24.0 * solDuration
    )
    localTimeHour = startingLocalTimeHour
    displayedLocalTimeHour = startingLocalTimeHour
    clockUpdateTimer = 0.0
    nightBlend = 0.0
    surfaceTemperatureC = hourlySurfaceTemperaturesC[12]
    elapsedTime = 0.0
    stormCheckTimer = 0.0
    stormTimeRemaining = 0.0
    stormIntensity = 0.0
    solarFlareCheckTimer = 0.0
    solarFlareActive = False
    solarFlarePixels = []
    solarFlareElapsed = 0.0
    solarFlareRecoveryActive = False
    solarFlareRecoveryElapsed = 0.0
    solarFlareRecoveryStartCount = 0
    sandstormEnabled = False
    dustTexture = None
    dustParticles = []
    dustFrameSets = []
    dustParticlesActive = False
    dustScreenSize = None
    nightOverlay = None
    dayOverlay = None
    dayVignette = None
    nightVignette = None
    cameraShake = (0.0, 0.0)

    @classmethod
    def _createSolarFlarePixel(cls, screenSize):
        screenWidth, screenHeight = screenSize
        return {
            'x': random.randrange(screenWidth),
            'y': random.randrange(screenHeight),
            'size': random.choice((1, 2, 3))
        }

    @classmethod
    def _startSolarFlare(cls, screenSize):
        cls.solarFlareActive = True
        cls.solarFlareElapsed = 0.0
        cls.solarFlareRecoveryActive = False
        cls.solarFlareRecoveryElapsed = 0.0
        cls.solarFlareRecoveryStartCount = 0
        cls.solarFlarePixels = [
            cls._createSolarFlarePixel(screenSize)
            for _ in range(cls.solarFlareInitialPixelCount)
        ]

    @classmethod
    def update(cls, deltaTime, screenSize, rover):
        deltaTime = max(0.0, deltaTime)
        cls.elapsedTime += deltaTime
        cls.dayNightTimer = (cls.dayNightTimer + deltaTime) % cls.solDuration
        cls.localTimeHour = (
            12.0 + cls.dayNightTimer / cls.solDuration * 24.0
        ) % 24.0
        cls.clockUpdateTimer += deltaTime
        if cls.clockUpdateTimer >= cls.clockUpdateInterval:
            cls.clockUpdateTimer %= cls.clockUpdateInterval
            cls.displayedLocalTimeHour = cls.localTimeHour
        cls.nightBlend = cls._getNightBlend()
        cls.isDay = cls.nightBlend < 0.5

        cls.stormCheckTimer += deltaTime
        if cls.sandstormEnabled:
            cls.stormTimeRemaining = max(
                0.0,
                cls.stormTimeRemaining - deltaTime
            )
            cls.sandstormEnabled = cls.stormTimeRemaining > 0.0

        if cls.stormCheckTimer >= cls.stormCheckInterval:
            cls.stormCheckTimer %= cls.stormCheckInterval
            if not cls.sandstormEnabled and random.random() < cls.stormChance:
                cls.sandstormEnabled = True
                cls.stormTimeRemaining = cls.stormDuration
                cls.stormIntensity = 0.0

        if cls.sandstormOnStart:
            cls.sandstormOnStart = False
            cls.sandstormEnabled = True
            cls.stormTimeRemaining = cls.stormDuration
            cls.stormIntensity = 0.0
            cls.stormCheckTimer = 0.0

        screenWidth, screenHeight = screenSize
        if not cls.solarFlareActive and cls.isDay:
            if cls.solarFlareOnStart:
                cls.solarFlareOnStart = False
                cls._startSolarFlare(screenSize)
            else:
                cls.solarFlareCheckTimer += deltaTime
                if cls.solarFlareCheckTimer >= cls.solarFlareCheckInterval:
                    cls.solarFlareCheckTimer %= cls.solarFlareCheckInterval
                    if random.random() < cls.solarFlareChance:
                        cls._startSolarFlare(screenSize)

        if cls.solarFlareActive:
            if rover.systemsOn:
                if cls.solarFlareRecoveryActive:
                    cls.solarFlareRecoveryActive = False
                    cls.solarFlareElapsed = (
                        len(cls.solarFlarePixels)
                        / cls.solarFlarePixelCount
                        * cls.solarFlareRampDuration
                    )
                cls.solarFlareElapsed = min(
                    cls.solarFlareRampDuration,
                    cls.solarFlareElapsed + deltaTime
                )
                targetPixelCount = max(
                    cls.solarFlareInitialPixelCount,
                    round(
                        cls.solarFlarePixelCount
                        * cls.solarFlareElapsed
                        / cls.solarFlareRampDuration
                    )
                )
                if cls.solarFlareElapsed >= cls.solarFlareRampDuration:
                    rover.gameOver = True
            else:
                if not cls.solarFlareRecoveryActive:
                    cls.solarFlareRecoveryActive = True
                    cls.solarFlareRecoveryElapsed = 0.0
                    cls.solarFlareRecoveryStartCount = len(
                        cls.solarFlarePixels
                    )
                cls.solarFlareRecoveryElapsed = min(
                    cls.solarFlareRecoveryDuration,
                    cls.solarFlareRecoveryElapsed + deltaTime
                )
                recoveryProgress = (
                    cls.solarFlareRecoveryElapsed
                    / cls.solarFlareRecoveryDuration
                )
                targetPixelCount = round(
                    cls.solarFlareRecoveryStartCount
                    * (1.0 - recoveryProgress)
                )

            if len(cls.solarFlarePixels) > targetPixelCount:
                del cls.solarFlarePixels[targetPixelCount:]
            else:
                cls.solarFlarePixels.extend(
                    cls._createSolarFlarePixel(screenSize)
                    for _ in range(
                        targetPixelCount - len(cls.solarFlarePixels)
                    )
                )
            if deltaTime > 0.0:
                for pixel in cls.solarFlarePixels:
                    pixel['x'] = random.randrange(screenWidth)
                    pixel['y'] = random.randrange(screenHeight)
            if not cls.solarFlarePixels:
                cls.solarFlareActive = False
                cls.solarFlareElapsed = 0.0
                cls.solarFlareRecoveryActive = False
                cls.solarFlareRecoveryElapsed = 0.0
                cls.solarFlareRecoveryStartCount = 0

        if cls.dustTexture is not None and cls.dustScreenSize != screenSize:
            cls.dustScreenSize = screenSize
            scaleFactor = Texture.getScaleFactor(screenSize) * 6.0
            sizeFactors = (44.0, 80.0, 118.0)
            cls.dustFrameSets = []
            frameBounds = []
            for sizeFactor in sizeFactors:
                size = max(1, round(sizeFactor * scaleFactor))
                baseImage = pg.transform.smoothscale(
                    cls.dustTexture,
                    (size, size)
                )
                frames = [
                    pg.transform.rotate(
                        baseImage,
                        i * (360.0 / cls.angleSteps)
                    )
                    for i in range(cls.angleSteps)
                ]
                cls.dustFrameSets.append(frames)
                frameBounds.append((
                    max(frame.get_width() for frame in frames) * 0.5,
                    max(frame.get_height() for frame in frames) * 0.5
                ))

            activationLevels = [
                (index + random.random()) / cls.dustParticleCount
                for index in range(cls.dustParticleCount)
            ]
            random.shuffle(activationLevels)
            cls.dustParticles = []
            for index in range(cls.dustParticleCount):
                frameSetIndex = random.randrange(len(cls.dustFrameSets))
                baseY = random.uniform(0.0, screenHeight)
                halfWidth, halfHeight = frameBounds[frameSetIndex]
                cls.dustParticles.append({
                    'x': screenWidth + halfWidth,
                    'y': baseY,
                    'baseY': baseY,
                    'speed': random.uniform(100.0, 260.0) * scaleFactor,
                    'rotation': random.uniform(0.0, 360.0),
                    'rotationSpeed': random.uniform(-80.0, 80.0),
                    'sway': random.uniform(3.0, 12.0) * scaleFactor,
                    'swaySpeed': random.uniform(0.5, 1.5),
                    'phase': random.uniform(0.0, math.tau),
                    'activation': activationLevels[index],
                    'active': False,
                    'frames': cls.dustFrameSets[frameSetIndex],
                    'halfWidth': halfWidth,
                    'halfHeight': halfHeight
                })

        transitionDuration = min(
            cls.stormTransitionDuration,
            cls.stormDuration * 0.5
        )
        if cls.sandstormEnabled and transitionDuration > 0.0:
            elapsedStormTime = cls.stormDuration - cls.stormTimeRemaining
            if elapsedStormTime < transitionDuration:
                transition = elapsedStormTime / transitionDuration
            elif cls.stormTimeRemaining < transitionDuration:
                transition = cls.stormTimeRemaining / transitionDuration
            else:
                transition = 1.0
            transition = max(0.0, min(1.0, transition))
            cls.stormIntensity = transition * transition * (3.0 - 2.0 * transition)
        else:
            cls.stormIntensity = 0.0

        hourIndex = int(cls.localTimeHour)
        hourFraction = cls.localTimeHour - hourIndex
        previousTemperature = cls.hourlySurfaceTemperaturesC[
            (hourIndex - 1) % 24
        ]
        currentTemperature = cls.hourlySurfaceTemperaturesC[hourIndex]
        nextTemperature = cls.hourlySurfaceTemperaturesC[
            (hourIndex + 1) % 24
        ]
        followingTemperature = cls.hourlySurfaceTemperaturesC[
            (hourIndex + 2) % 24
        ]
        hourFractionSquared = hourFraction * hourFraction
        clearTemperature = 0.5 * (
            2.0 * currentTemperature
            + (-previousTemperature + nextTemperature) * hourFraction
            + (
                2.0 * previousTemperature
                - 5.0 * currentTemperature
                + 4.0 * nextTemperature
                - followingTemperature
            ) * hourFractionSquared
            + (
                -previousTemperature
                + 3.0 * currentTemperature
                - 3.0 * nextTemperature
                + followingTemperature
            ) * hourFractionSquared * hourFraction
        )
        clearTemperature = max(-80.0, min(-23.0, clearTemperature))
        stormTemperatureOffset = (
            cls.nightBlend * cls.stormNightWarmingC
            - (1.0 - cls.nightBlend) * cls.stormDayCoolingC
        )
        cls.surfaceTemperatureC = (
            clearTemperature
            + stormTemperatureOffset * cls.stormIntensity
        )

        if cls.stormIntensity <= 0.0:
            if cls.dustParticlesActive:
                for particle in cls.dustParticles:
                    particle['active'] = False
                cls.dustParticlesActive = False
            cls.cameraShake = (0.0, 0.0)
            return

        time = cls.elapsedTime
        cls.cameraShake = (
            (2.0 * math.sin(time * 3.0) + math.sin(time * 5.0))
            * cls.stormIntensity,
            (1.5 * math.sin(time + 0.8) + 0.7 * math.sin(time * 37.0))
            * cls.stormIntensity
        )

        hasActiveParticles = False
        for particle in cls.dustParticles:
            shouldBeActive = cls.stormIntensity >= particle['activation']
            if shouldBeActive and not particle['active']:
                particle['x'] = screenWidth + particle['halfWidth']
                particle['baseY'] = random.uniform(0.0, screenHeight)
            particle['active'] = shouldBeActive
            if not shouldBeActive:
                continue

            hasActiveParticles = True
            particle['x'] -= particle['speed'] * deltaTime
            particle['y'] = particle['baseY'] + math.sin(
                cls.elapsedTime * particle['swaySpeed'] + particle['phase']
            ) * particle['sway']
            particle['rotation'] = (particle['rotation'] + particle['rotationSpeed'] * deltaTime) % 360.0

            halfWidth = particle['halfWidth']
            if particle['x'] < -halfWidth:
                particle['x'] = screenWidth + halfWidth
                particle['baseY'] = random.uniform(0.0, screenHeight)
        cls.dustParticlesActive = hasActiveParticles

        if deltaTime > 0.0:
            gust = 0.8 + 0.2 * math.sin(cls.elapsedTime * 0.7)
            rover.applyWind(
                -cls.windAcceleration * gust * cls.stormIntensity,
                0.0,
                deltaTime
            )

    @classmethod
    def _getNightBlend(cls):
        solarElevation = max(
            0.0,
            math.sin(math.tau * (cls.localTimeHour - 6.0) / 24.0)
        )
        daylightBlend = solarElevation * solarElevation * (
            3.0 - 2.0 * solarElevation
        )
        return 1.0 - daylightBlend

    @classmethod
    def render(cls, screen, showSolarFlare=True):
        screenSize = screen.get_size()
        nightBlend = cls.nightBlend

        if cls.nightOverlay is None or cls.nightOverlay.get_size() != screenSize:
            cls.nightOverlay = pg.Surface(screenSize, pg.SRCALPHA)
            cls.nightOverlay.fill((10, 15, 35, 255))
            cls.dayOverlay = pg.Surface(screenSize, pg.SRCALPHA)
            cls.dayOverlay.fill((240, 190, 115, 255))
            vignettes = []
            screenWidth, screenHeight = screenSize
            for color, center in (
                ((53, 27, 18), (0.46, 0.44)),
                ((12, 17, 47), (0.53, 0.49))
            ):
                vignette = pg.Surface(screenSize, pg.SRCALPHA)
                vignette.fill((*color, 255))
                for step in range(65):
                    progress = step / 64
                    ellipseWidth = max(
                        1,
                        round(screenWidth * (1.0 - 0.88 * progress))
                    )
                    ellipseHeight = max(
                        1,
                        round(screenHeight * (1.0 - 0.84 * progress))
                    )
                    rect = pg.Rect(0, 0, ellipseWidth, ellipseHeight)
                    rect.center = (
                        round(screenWidth * center[0]),
                        round(screenHeight * center[1])
                    )
                    alpha = round(255 * (1.0 - progress) ** 1.5)
                    pg.draw.ellipse(vignette, (*color, alpha), rect)
                vignettes.append(vignette)
            cls.dayVignette, cls.nightVignette = vignettes

        cls.dayOverlay.set_alpha(round(cls.dayAlpha * (1.0 - nightBlend)))
        cls.nightOverlay.set_alpha(round(cls.nightAlpha * nightBlend))
        screen.blit(cls.dayOverlay, (0, 0))
        screen.blit(cls.nightOverlay, (0, 0))

        if cls.stormIntensity > 0.0:
            screenRect = screen.get_rect()
            stepAngle = 360.0 / cls.angleSteps
            dustAlpha = round(90 * cls.stormIntensity)
            for particle in cls.dustParticles:
                if not particle['active']:
                    continue
                frameIdx = int(particle['rotation'] / stepAngle) % cls.angleSteps
                image = particle['frames'][frameIdx]
                image.set_alpha(dustAlpha)
                rect = image.get_rect(center=(particle['x'], particle['y']))
                if rect.colliderect(screenRect):
                    screen.blit(image, rect)

        vignetteStrength = min(
            255,
            cls.vignetteAlpha + round(25 * cls.stormIntensity)
        )
        cls.dayVignette.set_alpha(
            round(vignetteStrength * (1.0 - nightBlend))
        )
        cls.nightVignette.set_alpha(
            round((vignetteStrength + 25) * nightBlend)
        )
        screen.blit(cls.dayVignette, (0, 0))
        screen.blit(cls.nightVignette, (0, 0))
        if showSolarFlare and cls.solarFlareActive:
            for pixel in cls.solarFlarePixels:
                pg.draw.rect(
                    screen,
                    (255, 255, 255),
                    (
                        pixel['x'],
                        pixel['y'],
                        pixel['size'],
                        pixel['size']
                    )
                )
