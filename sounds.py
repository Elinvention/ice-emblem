import pygame
import resources
import logging
import random


if not pygame.mixer.get_init():
    pygame.mixer.init()


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
                    sounds[fpath.stem].set_volume(float(v))
    except FileNotFoundError:
        pass


for f in resources.list_sounds():
    if f.is_file() and f.suffix in extensions:
        sounds[f.stem] = pygame.mixer.Sound(str(f))
        parse_cfg(f.with_suffix('.cfg'))
    elif f.is_dir():
        sounds[f.name] = []
        for fd in f.iterdir():
            if fd.suffix in extensions:
                sounds[f.name].append(pygame.mixer.Sound(str(fd)))
                parse_cfg(fd.with_suffix('.cfg'))

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
    except KeyError:
        __logger.error("Could not stop sound %s.", sound)

def get(sound):
    if isinstance(sounds[sound], pygame.mixer.Sound):
        return sounds[sound]
    return random.choice(sounds[sound])

