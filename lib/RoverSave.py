import json
import math
from pathlib import Path


class RoverSave:
    path = Path(__file__).resolve().parent.parent / 'saves' / 'rover.json'

    @classmethod
    def load(cls, rover, defaultCoords):
        rover.coords[:] = defaultCoords
        try:
            data = json.loads(cls.path.read_text())
            values = [float(data[key]) for key in ('x', 'y', 'rotation')]
            if not all(math.isfinite(value) for value in values):
                return
            rover.coords[:] = values[:2]
            rover.rotation = values[2] % 360
        except (OSError, ValueError, TypeError, KeyError):
            pass

    @classmethod
    def save(cls, rover):
        if rover is None:
            return
        try:
            cls.path.parent.mkdir(exist_ok=True)
            temporary = cls.path.with_suffix('.tmp')
            temporary.write_text(json.dumps(dict(x=rover.coords[0],y=rover.coords[1],rotation=rover.rotation)))
            temporary.replace(cls.path)
        except OSError as error:
            print(f'[WARNING] Could not save rover: {error}')
