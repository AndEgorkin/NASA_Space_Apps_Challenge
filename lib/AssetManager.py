import pygame as pg
from pathlib import Path
import sys

class AssetManager:
    LOADED = {}
    BASE = Path(
        getattr(
            sys, 
            '_MEIPASS', 
            Path(__file__).parent.parent
            )
    ) / 'assets'
    
    
    @staticmethod
    def init(directory=BASE):
        for path in directory.iterdir():
            if path.is_dir():
                AssetManager.init(path)
            else:
                key = 'assets.' + (
                    str(path.relative_to(AssetManager.BASE))
                    .replace('\\', '.')
                    [:-len(path.suffix)]
                )
                if '\\texture\\' in str(path): # Все текстуры хранятся по пути assets/texture
                    AssetManager.LOADED[key] = pg.image.load(path)
                elif '\\sound\\' in str(path): # Все звуки хранятся по пути assets/sound
                    AssetManager.LOADED[key] = pg.mixer.Sound(path)
                print(f'[INFO] Загружен ресурс по ключу {key}')

    @staticmethod
    def get(key):
        return AssetManager.LOADED[key]