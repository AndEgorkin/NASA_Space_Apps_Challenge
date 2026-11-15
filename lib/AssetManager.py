import pygame as pg
import sys

from pathlib import Path

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
                continue

            relative = path.relative_to(AssetManager.BASE)
            key = 'assets.' + '.'.join(relative.with_suffix('').parts)

            if 'texture' in relative.parts:
                AssetManager.LOADED[key] = pg.image.load(path)
            elif 'sound' in relative.parts:
                AssetManager.LOADED[key] = pg.mixer.Sound(path)
            elif 'font' in relative.parts:
                AssetManager.LOADED[key] = pg.font.Font(path, 32)

            print(f'[INFO] Загружен ресурс по ключу {key}')

    @staticmethod
    def get(key):
        return AssetManager.LOADED[key]