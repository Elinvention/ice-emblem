import pygame
import os
import resources
import logging
import random


__logger = logging.getLogger('Sounds')
extensions = ['.ogg', '.wav']
sounds = {}


def parse_cfg(fpath):
	try:
		with open(fpath, 'r') as f:
			__logger.debug('Found config file %s' % fpath)
			for line in f:
				k, v = line.split('=')
				if k == 'volume' and 0 <= float(v) <= 1.0:
					sounds[root].set_volume(float(v))
	except FileNotFoundError:
		pass


for f in resources.list_sounds():
	p = os.path.join(resources.SOUNDS_PATH, f)
	root, ext = os.path.splitext(f)
	if os.path.isfile(p) and ext in extensions:
		sounds[root] = pygame.mixer.Sound(p)
		parse_cfg(os.path.join(resources.SOUNDS_PATH, root + '.cfg'))
	elif os.path.isdir(p):
		lsdir = os.listdir(p)
		sounds[f] = []
		for fd in lsdir:
			root, ext = os.path.splitext(fd)
			if ext in extensions:
				sounds[f].append(pygame.mixer.Sound(os.path.join(p, fd)))
				parse_cfg(os.path.join(p, root + '.cfg'))

__logger.debug("Sounds initialized!")

def play(sound, *args):
	try:
		sounds[sound].play(*args)
	except AttributeError:
		random.choice(sounds[sound]).play(*args)
	except KeyError:
		__logger.error("Could not play sound %s: file not found.", sound)

def stop(sound):
	try:
		sounds[sound].stop()
	except AttributeError:
		for s in sounds[sound]:
			s.stop()

def get(sound):
	if isinstance(sounds[sound], pygame.mixer.Sound):
		return sounds[sound]
	return random.choice(sounds[sound])

