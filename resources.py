import os
import pygame
import logging


RESOURCES_PATH = os.path.relpath("resources")
IMAGE_PATH = os.path.join(RESOURCES_PATH, "images")
SOUNDS_PATH = os.path.join(RESOURCES_PATH, "sounds")
MUSIC_PATH =  os.path.join(RESOURCES_PATH, "music")
FONTS_PATH =  os.path.join(RESOURCES_PATH, "fonts")
LOCALE_PATH = os.path.join(RESOURCES_PATH, "locale")
MAPS_PATH = os.path.join(RESOURCES_PATH, "maps")
SPRITES_PATH = os.path.join(RESOURCES_PATH, "sprites")
DATA_PATH = os.path.join(RESOURCES_PATH, "data")

__logger = logging.getLogger('Resources')


def __load_log(path):
	__logger.debug('Loading %s' % path)

def load_image(fname):
	path = os.path.join(IMAGE_PATH, fname)
	__load_log(path)
	return pygame.image.load(path)

def load_sound(fname):
	path = os.path.join(SOUNDS_PATH, fname)
	__load_log(path)
	return pygame.mixer.Sound(path)

def load_font(fname, size):
	path = os.path.join(FONTS_PATH, fname)
	__load_log(path)
	return pygame.font.Font(path, size)

def load_sprite(fname):
	if '.' not in fname:
		for f in os.listdir(SPRITES_PATH):
			if f == fname + '.png' or f == fname + '.jpg':
				fname = f
	path = os.path.join(SPRITES_PATH, fname)
	__load_log(path)
	return pygame.image.load(path)

def load_data(fname):
	path = os.path.join(DATA_PATH, fname)
	__load_log(path)
	return open(path, 'r')

def load_music(fname):
	path = os.path.join(MUSIC_PATH, fname)
	__load_log(path)
	pygame.mixer.music.load(path)

def map_path(fname):
	if '.' not in fname:
		fname += '.tmx'
	return os.path.join(MAPS_PATH, fname)

def music_path(fname):
	return os.path.join(MUSIC_PATH, fname)

def data_path(fname):
	return os.path.join(DATA_PATH, fname)

def list_sounds():
	return os.listdir(SOUNDS_PATH)

def list_maps():
	ls = os.listdir(MAPS_PATH)
	return [f for f in ls if os.path.isfile(map_path(f)) and f.endswith('.tmx')]


