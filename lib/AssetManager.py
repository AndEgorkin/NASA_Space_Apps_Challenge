import pygame as pg
from pathlib import Path
import sys

class AssetManager:
    _BASE = Path(
        getattr(
            sys, 
            '_MEIPASS', 
            Path(__file__).parent.parent
            )
    ) / 'assets'
    
    _LOADED = {}

    @staticmethod
    def load(directory):
        for path in directory.iterdir():
            if path.is_dir():
                AssetManager.load(path)
            else:
                key = 'assets.' + (
                    str(path.relative_to(AssetManager._BASE))
                    .replace('\\', '.')
                    [:-len(path.suffix)]
                )
                if '\\texture\\' in str(path): # Все текстуры хранятся по пути assets/texture
                    AssetManager._LOADED[key] = pg.image.load(path)
                elif '\\sound\\' in str(path): # Все звуки хранятся по пути assets/sound
                    AssetManager._LOADED[key] = pg.mixer.Sound(path)
    @staticmethod
    def get(self, key):
        return self._LOADED[key]