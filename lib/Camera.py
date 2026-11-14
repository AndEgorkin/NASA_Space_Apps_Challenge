class Camera:
    def __init__(self, targetCoords=(0.0, 0.0), smoothness=0.08):
        self.coords = list(targetCoords)
        self.smoothness = smoothness

    def follow(self, targetCoords):
        self.coords[0] += (targetCoords[0] - self.coords[0]) * self.smoothness
        self.coords[1] += (targetCoords[1] - self.coords[1]) * self.smoothness
