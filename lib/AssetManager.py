import sys
from pathlib import Path

import pygame as pg


class AssetManager:
    BASE = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent.parent)) / 'assets'
    LOADED = {}
    imageExtensions = {'.png', '.jpg', '.jpeg', '.bmp'}
    soundExtensions = {'.wav', '.ogg', '.mp3'}

    @classmethod
    def init(cls, directory=None):
        directory = cls.BASE if directory is None else Path(directory)
        for path in sorted(directory.rglob('*')):
            if not path.is_file():
                continue
            relative = path.relative_to(cls.BASE)
            key = 'assets.' + '.'.join(relative.with_suffix('').parts)
            if key in cls.LOADED:
                continue
            extension = path.suffix.lower()
            if extension in cls.imageExtensions:
                asset = pg.image.load(str(path))
                if pg.display.get_surface() is not None:
                    asset = asset.convert_alpha()
            elif extension in cls.soundExtensions:
                asset = pg.mixer.Sound(str(path))
            else:
                continue
            cls.LOADED[key] = asset
            print(f'[INFO] Loaded asset {key}')

    @classmethod
    def get(cls, key):
        return cls.LOADED[key]
