import pygame
import logging

from pathlib import Path


RESOURCES_PATH = Path('resources')
IMAGE_PATH =   RESOURCES_PATH / 'images'
SOUNDS_PATH =  RESOURCES_PATH / 'sounds'
MUSIC_PATH =   RESOURCES_PATH / 'music'
FONTS_PATH =   RESOURCES_PATH / 'fonts'
LOCALE_PATH =  RESOURCES_PATH / 'locale'
MAPS_PATH =    RESOURCES_PATH / 'maps'
SPRITES_PATH = RESOURCES_PATH / 'sprites'
DATA_PATH =    RESOURCES_PATH / 'data'

__logger = logging.getLogger(__name__)


def __load_log(path):
    __logger.debug('Loading %s' % path)

def load_image(fname):
    path = str(IMAGE_PATH / fname)
    __load_log(path)
    return pygame.image.load(path)

def load_sound(fname):
    path = str(SOUNDS_PATH / fname)
    __load_log(path)
    return pygame.mixer.Sound(path)

def load_font(name, size):
    path = FONTS_PATH / name
    __load_log(path)
    return pygame.font.Font(str(path), size)

def load_sprite(fname):
    path = str(sprite_path(fname))
    __load_log(path)
    return pygame.image.load(path)

def load_data(fname):
    path = str(DATA_PATH / fname)
    __load_log(path)
    return open(path, 'r')

def load_music(fname):
    path = str(MUSIC_PATH / fname)
    __load_log(path)
    pygame.mixer.music.load(path)

def play_music(fname, loop=-1, pos=0):
    load_music(fname)
    pygame.mixer.music.play(loop, pos)

def map_path(fname):
    if Path(fname).suffix == '':
        fname += '.tmx'
    return str(MAPS_PATH / fname)

def is_map(fname):
    path = Path(fname)
    return path.is_file() and path.suffix == '.tmx'

def sprite_path(fname: str):
    """Return the path to a sprite by filename with or without file extension"""
    if '.' not in fname:
        for f in SPRITES_PATH.iterdir():
            if f.name == fname + '.png' or f.name == fname + '.jpg':
                fname = f.name
                break
    return SPRITES_PATH / fname

def list_sounds():
    return SOUNDS_PATH.iterdir()

def list_maps():
    ls = MAPS_PATH.iterdir()
    return [f.name for f in ls if is_map(f)]


