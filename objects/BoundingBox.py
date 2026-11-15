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
        return self.penetration(other) is not None

    def penetration(self, other):
        """Smallest world-space displacement that moves this box out of other."""
        ownCos,ownSin=math.cos(self.rotation),math.sin(self.rotation)
        otherCos,otherSin=math.cos(other.rotation),math.sin(other.rotation)
        ownAxes=((ownCos,ownSin),(-ownSin,ownCos))
        otherAxes=((otherCos,otherSin),(-otherSin,otherCos))
        delta=(other.coords[0]-self.coords[0],other.coords[1]-self.coords[1])
        minimum=float('inf');separation=None
        for axis in ownAxes+otherAxes:
            distance=delta[0]*axis[0]+delta[1]*axis[1]
            radius=(self.halfWidth*abs(ownAxes[0][0]*axis[0]+ownAxes[0][1]*axis[1])
                    + self.halfHeight*abs(ownAxes[1][0]*axis[0]+ownAxes[1][1]*axis[1])
                    + other.halfWidth*abs(otherAxes[0][0]*axis[0]+otherAxes[0][1]*axis[1])
                    + other.halfHeight*abs(otherAxes[1][0]*axis[0]+otherAxes[1][1]*axis[1]))
            overlap=radius-abs(distance)
            if overlap<=1e-8:return None
            if overlap<minimum:
                minimum=overlap
                direction=-1 if distance>=0 else 1
                separation=(axis[0]*direction*(overlap+0.02),axis[1]*direction*(overlap+0.02))
        return separation
