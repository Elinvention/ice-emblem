import pygame
import os
import resources
import logging
import random

print(pygame.mixer.get_init())

__logger = logging.getLogger('Sounds')
sounds = {}

for f in resources.list_sounds():
	p = os.path.join(resources.SOUNDS_PATH, f)
	if os.path.isfile(p) and (f.endswith('.ogg') or f.endswith('.wav')):
		sounds[f[:-4]] = pygame.mixer.Sound(p)
	elif os.path.isdir(p):
		lsdir = os.listdir(p)
		sounds[f] = [pygame.mixer.Sound(os.path.join(p, f)) for f in lsdir if f.endswith('.ogg') or f.endswith('.wav')]

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
		for s in self.sounds[sound]:
			s.stop()

def get(sound):
	if isinstance(sounds[sound], pygame.mixer.Sound):
		return sounds[sound]
	return random.choice(sounds[sound])

