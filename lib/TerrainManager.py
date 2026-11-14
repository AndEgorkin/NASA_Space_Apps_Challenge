import threading
import pygame as pg
from concurrent.futures import ThreadPoolExecutor
from lib.Chunk import Chunk

class TerrainManager:
    def __init__(self, chunkSize=1200):
        self.chunkSize = chunkSize
        self.loadedChunks = {}
        self.loadingTasks = {}
        self.cachedSurfaces = {}
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.lock = threading.Lock()

    def init(self, playerCoords, buffer):
        currChunkX = int(round(playerCoords[0] / self.chunkSize))
        currChunkY = int(round(playerCoords[1] / self.chunkSize))
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                coord = (currChunkX + dx, currChunkY + dy)
                self.loadingTasks[coord] = self.executor.submit(
                    Chunk.generateSurface, coord[0], coord[1], self.chunkSize
                )

    def update(self, playerCoords, buffer):
        currChunkX = int(round(playerCoords[0] / self.chunkSize))
        currChunkY = int(round(playerCoords[1] / self.chunkSize))

        neededCoords = set()
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                neededCoords.add((currChunkX + dx, currChunkY + dy))

        for coord in list(self.loadedChunks.keys()):
            if coord not in neededCoords:
                chunk = self.loadedChunks.pop(coord)
                if chunk in buffer:
                    buffer.remove(chunk)
                chunk.destroy()

        for coord, future in list(self.loadingTasks.items()):
            if coord not in neededCoords and future.cancel():
                del self.loadingTasks[coord]

        for coord, future in list(self.loadingTasks.items()):
            if future.done():
                surface = future.result()
                with self.lock:
                    self.cachedSurfaces[coord] = surface
                del self.loadingTasks[coord]
                if coord in neededCoords and coord not in self.loadedChunks:
                    chunk = Chunk(coord[0], coord[1], self.chunkSize, surface)
                    self.loadedChunks[coord] = chunk
                    buffer.append(chunk)

        for coord in neededCoords:
            if coord not in self.loadedChunks:
                if coord in self.cachedSurfaces:
                    chunk = Chunk(coord[0], coord[1], self.chunkSize, self.cachedSurfaces[coord])
                    self.loadedChunks[coord] = chunk
                    buffer.append(chunk)
                elif coord in self.loadingTasks:
                    continue
                else:
                    self.loadingTasks[coord] = self.executor.submit(
                        Chunk.generateSurface, coord[0], coord[1], self.chunkSize
                    )
