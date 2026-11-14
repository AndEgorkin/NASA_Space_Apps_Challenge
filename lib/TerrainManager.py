import threading
from concurrent.futures import ThreadPoolExecutor
from objects.Chunk import Chunk

class TerrainManager:
    chunkSize = 1200
    loadedChunks = {}
    loadingTasks = {}
    cachedSurfaces = {}
    executor = ThreadPoolExecutor(max_workers=1)
    lock = threading.Lock()

    @classmethod
    def loadInitialChunks(cls, playerCoords, buffer):
        currChunkX = int(round(playerCoords[0] / cls.chunkSize))
        currChunkY = int(round(playerCoords[1] / cls.chunkSize))

        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                coord = (currChunkX + dx, currChunkY + dy)
                if coord in cls.loadedChunks:
                    continue

                surface = cls.cachedSurfaces.get(coord)
                if surface is None:
                    surface = Chunk.generateSurface(
                        coord[0],
                        coord[1],
                        cls.chunkSize
                    )
                    with cls.lock:
                        cls.cachedSurfaces[coord] = surface

                chunk = Chunk(coord[0], coord[1], cls.chunkSize, surface)
                cls.loadedChunks[coord] = chunk
                buffer.append(chunk)

    @classmethod
    def update(cls, playerCoords, buffer):
        currChunkX = int(round(playerCoords[0] / cls.chunkSize))
        currChunkY = int(round(playerCoords[1] / cls.chunkSize))

        neededCoords = set()
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                neededCoords.add((currChunkX + dx, currChunkY + dy))

        for coord in list(cls.loadedChunks.keys()):
            if coord not in neededCoords:
                chunk = cls.loadedChunks.pop(coord)
                if chunk in buffer:
                    buffer.remove(chunk)
                chunk.destroy()

        for coord, future in list(cls.loadingTasks.items()):
            if coord not in neededCoords and future.cancel():
                del cls.loadingTasks[coord]

        for coord, future in list(cls.loadingTasks.items()):
            if future.done():
                surface = future.result()
                with cls.lock:
                    cls.cachedSurfaces[coord] = surface
                del cls.loadingTasks[coord]
                if coord in neededCoords and coord not in cls.loadedChunks:
                    chunk = Chunk(coord[0], coord[1], cls.chunkSize, surface)
                    cls.loadedChunks[coord] = chunk
                    buffer.append(chunk)

        for coord in neededCoords:
            if coord not in cls.loadedChunks:
                if coord in cls.cachedSurfaces:
                    chunk = Chunk(coord[0], coord[1], cls.chunkSize, cls.cachedSurfaces[coord])
                    cls.loadedChunks[coord] = chunk
                    buffer.append(chunk)
                elif coord in cls.loadingTasks:
                    continue
                else:
                    cls.loadingTasks[coord] = cls.executor.submit(
                        Chunk.generateSurface, coord[0], coord[1], cls.chunkSize
                    )
