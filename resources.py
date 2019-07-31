"""
Resources are cool. Contains a map of Ice Emblem file system and provides access to resources.
"""


import pygame
import logging

from pathlib import Path


if not pygame.font.get_init():
    pygame.font.init()

RESOURCES_PATH = Path(__file__).absolute().parent / 'resources'  #: resources directory
IMAGE_PATH =   RESOURCES_PATH / 'images'  #: images directory
SOUNDS_PATH =  RESOURCES_PATH / 'sounds'
MUSIC_PATH =   RESOURCES_PATH / 'music'
FONTS_PATH =   RESOURCES_PATH / 'fonts'
LOCALE_PATH =  RESOURCES_PATH / 'locale'
MAPS_PATH =    RESOURCES_PATH / 'maps'
SPRITES_PATH = RESOURCES_PATH / 'sprites'
DATA_PATH =    RESOURCES_PATH / 'data'

__logger = logging.getLogger(__name__)


def __load_log(path):
    __logger.debug('Loading %s', path)


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


def sprite_path(name: str):
    """
    Return the path to a sprite by filename with or without file extension.

    :param name: The name of the sprite. Doesn't need file extension. png and jpg files are supported.
    :return: the absolute path to a sprite resource.
    """
    if '.' not in name:
        for f in SPRITES_PATH.iterdir():
            if f.name == name + '.png' or f.name == name + '.jpg':
                name = f.name
                break
    return SPRITES_PATH / name


def list_sounds():
    return SOUNDS_PATH.iterdir()


def list_maps():
    ls = MAPS_PATH.iterdir()
    return [f.name for f in ls if is_map(f)]


