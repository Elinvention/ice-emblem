#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  utils.py
#
#  Copyright 2015 Elia Argentieri <elia.argentieri@openmailbox.org>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.


import pygame
import sys
import yaml

from pathlib import Path


def timeit(f):

    def timed(*args, **kw):
        ts = pygame.time.get_ticks()
        result = f(*args, **kw)
        te = pygame.time.get_ticks()
        print('func:%r args:[%r, %r] took: %d millis' % \
            (f.__name__, args, kw, te-ts))
        return result

    return timed

def parse_yaml(path, module):
    objects = {}
    with open(path, 'r') as f:
        data = yaml.safe_load(f)
        for u in data:
            u_class = module.__dict__[list(u.keys())[0]]
            kwargs = list(u.values())[0]
            objects[kwargs['name']] = u_class(**kwargs)
    return objects

def distance(p0, p1):
    return abs(p0[0] - p1[0]) + abs(p0[1] - p1[1])

def resize_keep_ratio(size, max_size):
    w, h = size
    max_w, max_h = max_size
    resize_ratio = min(max_w / w, max_h / h)
    return int(w * resize_ratio), int(h * resize_ratio)

def resize_cover(size, max_size):
    w, h = size
    max_w, max_h = max_size
    resize_ratio = max(max_w / w, max_h / h)
    return int(w * resize_ratio), int(h * resize_ratio)

def center(rect1, rect2, xoffset=0, yoffset=0):
    """Center rect2 in rect1 with offset."""
    return (rect1.centerx - rect2.centerx + xoffset, rect1.centery - rect2.centery + yoffset)

def return_to_os(*args):
    pygame.quit()
    sys.exit(0)


def get_version():
    version_file_path = Path(__file__).absolute().parent / 'VERSION'
    return open(version_file_path).read().strip('\n')
