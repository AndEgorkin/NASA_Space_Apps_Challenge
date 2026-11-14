import math
from functools import lru_cache
import pygame as pg
from lib.Texture import Texture

class Chunk(Texture):
    CRATER_CELL_SIZE = 650.0

    PALETTE = [
        (65, 22, 14),
        (85, 30, 18),
        (110, 42, 24),
        (135, 52, 28),
        (160, 65, 34),
        (185, 78, 40),
        (210, 98, 50),
        (235, 120, 65)
    ]

    def __init__(self, chunkX, chunkY, chunkSize=1200, surface=None):
        self.chunkX = chunkX
        self.chunkY = chunkY
        self.chunkSize = chunkSize
        
        worldX = chunkX * chunkSize
        worldY = chunkY * chunkSize
        if surface is None:
            surface = Chunk.generateSurface(chunkX, chunkY, chunkSize)

        super().__init__(
            f'mars.chunk.{chunkX}.{chunkY}',
            [worldX, worldY],
            0.0,
            1.0,
            surface,
            -100
        )

    @staticmethod
    def _hash2(x, y):
        h = (x * 374761393 + y * 668265263) ^ 0x5bf03635
        h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
        return (h ^ (h >> 16)) / 4294967295.0

    @staticmethod
    @lru_cache(maxsize=16384)
    def _pseudoGrad(gx, gy):
        val = Chunk._hash2(gx, gy) * math.tau
        return math.cos(val), math.sin(val)

    @staticmethod
    @lru_cache(maxsize=4096)
    def _craterCell(cellX, cellY):
        cellSize = Chunk.CRATER_CELL_SIZE
        if Chunk._hash2(cellX + 193, cellY - 71) < 0.18:
            return None

        centerX = (cellX + 0.15 + Chunk._hash2(cellX, cellY) * 0.7) * cellSize
        centerY = (cellY + 0.15 + Chunk._hash2(cellX + 61, cellY + 97) * 0.7) * cellSize
        radius = 40.0 + Chunk._hash2(cellX - 137, cellY + 53) ** 2.8 * 240.0
        return centerX, centerY, radius

    @staticmethod
    def _noise(worldX, worldY, scale):
        gx = worldX / scale
        gy = worldY / scale
        x0 = int(math.floor(gx))
        y0 = int(math.floor(gy))
        x1 = x0 + 1
        y1 = y0 + 1

        tx = gx - x0
        ty = gy - y0

        g00 = Chunk._pseudoGrad(x0, y0)
        g10 = Chunk._pseudoGrad(x1, y0)
        g01 = Chunk._pseudoGrad(x0, y1)
        g11 = Chunk._pseudoGrad(x1, y1)

        d00 = (gx - x0) * g00[0] + (gy - y0) * g00[1]
        d10 = (gx - x1) * g10[0] + (gy - y0) * g10[1]
        d01 = (gx - x0) * g01[0] + (gy - y1) * g01[1]
        d11 = (gx - x1) * g11[0] + (gy - y1) * g11[1]

        sx = tx * tx * (3 - 2 * tx)
        sy = ty * ty * (3 - 2 * ty)

        nx0 = d00 * (1 - sx) + d10 * sx
        nx1 = d01 * (1 - sx) + d11 * sx
        return nx0 * (1 - sy) + nx1 * sy

    @staticmethod
    def _craterHeight(worldX, worldY, edgeNoise):
        cellSize = Chunk.CRATER_CELL_SIZE
        cellX = math.floor(worldX / cellSize)
        cellY = math.floor(worldY / cellSize)
        height = 0.0

        for cx in range(cellX - 1, cellX + 2):
            for cy in range(cellY - 1, cellY + 2):
                crater = Chunk._craterCell(cx, cy)
                if crater is None:
                    continue

                centerX, centerY, radius = crater
                dx = worldX - centerX
                dy = worldY - centerY
                radiusLimit = radius * 1.2
                distanceSquared = dx * dx + dy * dy
                if distanceSquared >= radiusLimit * radiusLimit:
                    continue

                distance = math.sqrt(distanceSquared) / radius + edgeNoise * 0.55
                bowl = -0.24 * max(0.0, 1.0 - (distance / 0.86) ** 2)
                rimWidth = max(0.095, 8.0 / radius)
                rim = 0.28 * math.exp(-((distance - 0.98) / rimWidth) ** 2)
                ejecta = 0.08 * math.exp(-((distance - 1.12) / 0.22) ** 2)
                height += bowl + rim + ejecta

        return height

    @staticmethod
    def terrainHeight(worldX, worldY):
        detail = Chunk._noise(worldX, worldY, 120.0) * 0.85
        warp = detail * 70.0
        warpedX = worldX + warp
        warpedY = worldY - warp
        base = Chunk._noise(warpedX, warpedY, 1600.0)
        ridges = (1.0 - min(1.0, abs(detail))) ** 2.5
        craters = Chunk._craterHeight(worldX, worldY, detail)
        return base * 0.8 + ridges * 0.42 + detail * 0.24 + craters

    @staticmethod
    def terrainColorIndex(worldX, worldY):
        return Chunk.terrainColorIndexFromHeight(
            Chunk.terrainPixelHeight(worldX, worldY)
        )

    @staticmethod
    def terrainPixelHeight(worldX, worldY):
        pixelStep = 8.0
        worldX = (math.floor(worldX / pixelStep) + 0.5) * pixelStep
        worldY = (math.floor(worldY / pixelStep) + 0.5) * pixelStep
        return Chunk.terrainHeight(worldX, worldY)

    @staticmethod
    def terrainColorIndexFromHeight(height):
        val = (height - 0.2) * 0.75 + 0.5
        val = max(0.0, min(0.999, val))
        return int(val * len(Chunk.PALETTE))

    @staticmethod
    def generateSurface(chunkX, chunkY, chunkSize):
        pixelStep = 8
        lowResSize = chunkSize // pixelStep
        lowSurface = pg.Surface((lowResSize, lowResSize))
        pixelArray = pg.PixelArray(lowSurface)

        chunkCenterX = chunkX * chunkSize
        chunkCenterY = chunkY * chunkSize
        chunkStartX = chunkCenterX - chunkSize / 2
        chunkTopY = chunkCenterY + chunkSize / 2

        numColors = len(Chunk.PALETTE)
        
        for ly in range(lowResSize):
            worldY = chunkTopY - (ly + 0.5) * pixelStep
            for lx in range(lowResSize):
                worldX = chunkStartX + (lx + 0.5) * pixelStep

                raw = Chunk.terrainHeight(worldX, worldY)
                val = (raw - 0.2) * 0.75 + 0.5
                val = max(0.0, min(0.999, val))

                colorIdx = int(val * numColors)
                pixelArray[lx, ly] = Chunk.PALETTE[colorIdx]

        del pixelArray
        return pg.transform.scale(lowSurface, (chunkSize, chunkSize))
