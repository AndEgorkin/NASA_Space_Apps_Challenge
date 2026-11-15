import math


class BoundingBox:
    def __init__(self, coords, width, height, rotation=0.0):
        self.coords = tuple(coords)
        halfWidth = width / 2.0
        halfHeight = height / 2.0
        self.halfWidth = halfWidth
        self.halfHeight = halfHeight
        self.rotation = math.radians(rotation)

    def intersects(self, other):
        ownCos = math.cos(self.rotation)
        ownSin = math.sin(self.rotation)
        otherCos = math.cos(other.rotation)
        otherSin = math.sin(other.rotation)
        ownAxes = ((ownCos, ownSin), (-ownSin, ownCos))
        otherAxes = ((otherCos, otherSin), (-otherSin, otherCos))
        deltaX = other.coords[0] - self.coords[0]
        deltaY = other.coords[1] - self.coords[1]

        for axis in ownAxes + otherAxes:
            distance = abs(deltaX * axis[0] + deltaY * axis[1])
            ownRadius = (
                self.halfWidth * abs(ownAxes[0][0] * axis[0] + ownAxes[0][1] * axis[1])
                + self.halfHeight * abs(ownAxes[1][0] * axis[0] + ownAxes[1][1] * axis[1])
            )
            otherRadius = (
                other.halfWidth * abs(otherAxes[0][0] * axis[0] + otherAxes[0][1] * axis[1])
                + other.halfHeight * abs(otherAxes[1][0] * axis[0] + otherAxes[1][1] * axis[1])
            )
            if distance > ownRadius + otherRadius + 1e-9:
                return False
        return True
