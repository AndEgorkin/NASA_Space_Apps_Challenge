import math
import random
import pygame as pg
from objects.Texture import Texture

class EnvironmentManager:
    dayNightDuration = 60.0
    dayNightTransitionDuration = 6.0
    stormCheckInterval = 30.0
    stormDuration = 30.0
    stormTransitionDuration = 5.0
    stormChance = 0.3
    dustParticleCount = 24
    windAcceleration = 90.0
    nightAlpha = 155
    dayAlpha = 18
    vignetteAlpha = 55
    angleSteps = 12
    isDay = True
    dayNightTimer = 0.0
    elapsedTime = 0.0
    stormCheckTimer = 0.0
    stormTimeRemaining = 0.0
    stormIntensity = 0.0
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
    def update(cls, deltaTime, screenSize):
        deltaTime = max(0.0, deltaTime)
        cls.elapsedTime += deltaTime
        cls.dayNightTimer += deltaTime

        if cls.dayNightTimer >= cls.dayNightDuration:
            cls.dayNightTimer %= cls.dayNightDuration
            cls.isDay = not cls.isDay

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

        screenWidth, screenHeight = screenSize
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

    @classmethod
    def applyWeather(cls, rover, deltaTime):
        if cls.stormIntensity <= 0.0 or deltaTime <= 0.0:
            return

        gust = 0.8 + 0.2 * math.sin(cls.elapsedTime * 0.7)
        rover.applyWind(
            -cls.windAcceleration * gust * cls.stormIntensity,
            0.0,
            deltaTime
        )

    @classmethod
    def getCameraOffset(cls, cameraCoords, screenSize):
        scaleFactor = Texture.getScaleFactor(screenSize)
        return (
            cameraCoords[0] - cls.cameraShake[0] / scaleFactor,
            cameraCoords[1] + cls.cameraShake[1] / scaleFactor
        )

    @classmethod
    def _getNightBlend(cls):
        transitionDuration = min(
            cls.dayNightTransitionDuration,
            cls.dayNightDuration
        )
        if transitionDuration <= 0.0:
            return 0.0 if cls.isDay else 1.0

        halfTransition = transitionDuration * 0.5

        if cls.isDay:
            if cls.dayNightTimer < halfTransition:
                progress = cls.dayNightTimer / halfTransition
                return 0.5 * (1.0 - progress * progress * (3.0 - 2.0 * progress))
            if cls.dayNightTimer >= cls.dayNightDuration - halfTransition:
                progress = (
                    cls.dayNightTimer - (cls.dayNightDuration - halfTransition)
                ) / halfTransition
                return 0.5 * progress * progress * (3.0 - 2.0 * progress)
            return 0.0

        if cls.dayNightTimer < halfTransition:
            progress = cls.dayNightTimer / halfTransition
            return 0.5 + 0.5 * progress * progress * (3.0 - 2.0 * progress)
        if cls.dayNightTimer >= cls.dayNightDuration - halfTransition:
            progress = (
                cls.dayNightTimer - (cls.dayNightDuration - halfTransition)
            ) / halfTransition
            return 1.0 - 0.5 * progress * progress * (3.0 - 2.0 * progress)

        return 1.0

    @staticmethod
    def _createVignette(screenSize, color, center):
        screenWidth, screenHeight = screenSize
        vignette = pg.Surface(screenSize, pg.SRCALPHA)
        vignette.fill((*color, 255))

        steps = 64
        for step in range(steps + 1):
            progress = step / steps
            ellipseWidth = max(1, round(screenWidth * (1.0 - 0.88 * progress)))
            ellipseHeight = max(1, round(screenHeight * (1.0 - 0.84 * progress)))
            rect = pg.Rect(0, 0, ellipseWidth, ellipseHeight)
            rect.center = (
                round(screenWidth * center[0]),
                round(screenHeight * center[1])
            )
            alpha = round(255 * (1.0 - progress) ** 1.5)
            pg.draw.ellipse(vignette, (*color, alpha), rect)

        return vignette

    @classmethod
    def render(cls, screen):
        screenSize = screen.get_size()
        nightBlend = cls._getNightBlend()

        if cls.nightOverlay is None or cls.nightOverlay.get_size() != screenSize:
            cls.nightOverlay = pg.Surface(screenSize, pg.SRCALPHA)
            cls.nightOverlay.fill((10, 15, 35, 255))
            cls.dayOverlay = pg.Surface(screenSize, pg.SRCALPHA)
            cls.dayOverlay.fill((240, 190, 115, 255))
            cls.dayVignette = cls._createVignette(
                screenSize,
                (53, 27, 18),
                (0.46, 0.44)
            )
            cls.nightVignette = cls._createVignette(
                screenSize,
                (12, 17, 47),
                (0.53, 0.49)
            )

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
