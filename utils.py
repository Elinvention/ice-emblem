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

def timeit(f):

	def timed(*args, **kw):
		ts = pygame.time.get_ticks()
		result = f(*args, **kw)
		te = pygame.time.get_ticks()
		print('func:%r args:[%r, %r] took: %d millis' % \
			(f.__name__, args, kw, te-ts))
		return result

	return timed

def distance(p0, p1):
	return abs(p0[0] - p1[0]) + abs(p0[1] - p1[1])

def resize_keep_ratio(size, max_size):
	w, h = size
	max_w, max_h = max_size
	resize_ratio = min(max_w / w, max_h / h)
	return int(w * resize_ratio), int(h * resize_ratio)

def center(rect1, rect2, xoffset=0, yoffset=0):
	"""Center rect2 in rect1 with offset."""
	return (rect1.centerx - rect2.centerx + xoffset, rect1.centery - rect2.centery + yoffset)

def return_to_os(*args):
	pygame.quit()
	sys.exit(0)

def videoresize_handler(event):
	"""
	The minum window size is 800x600.
	On Debian Jessie there is an issue that makes the window kind of
	"rebel" while trying to resize it.
	"""
	screen_size = event.size
	if screen_size[0] < 800:
		screen_size = (800, screen_size[1])
	if screen_size[1] < 600:
		screen_size = (screen_size[0], 600)
	return pygame.display.set_mode(screen_size, pygame.RESIZABLE)
