#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Ice Emblem.py
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


import time
import pygame
import csv
import sys

from IEItem import IEItem, IEWeapon
from IEMap import IEMap
from IEUnit import IEUnit

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 200, 0)
GREY = (160, 160, 160)


def draw_map(screen, iemap, clock):
	"""Let's draw everything!"""
	screen_w, screen_h = screen.get_size()
	#screen_rect = screen.get_rect()

	square = iemap.square

	map_w = square * iemap.w
	map_h = square * iemap.h

	node_background = pygame.Surface((square - 2, square - 2)).convert()
	node_background.fill(GREEN)

	selected_node_background = pygame.Surface((square - 2, square - 2)).convert()
	selected_node_background.fill(YELLOW)

	unit_move_range_background = pygame.Surface((square - 2, square - 2)).convert()
	unit_move_range_background.fill(BLUE)

	unit_attack_range_backgroud = pygame.Surface((square - 2, square - 2)).convert()
	unit_attack_range_backgroud.fill(RED)

	unit_played_backgroud = pygame.Surface((square - 2, square - 2)).convert()
	unit_played_backgroud.fill(GREY)

	screen.fill(BLACK)

	FONT = pygame.font.SysFont("Liberation Sans", 24)

	for i in range(0, iemap.w):
		pygame.draw.line(screen, WHITE, (i * square, 0), (i * square, map_h), 1)
		for j in range(0, iemap.h):
			pygame.draw.line(screen, WHITE, (0, j * square), (map_w, j * square), 1)

			node = iemap.matrix[i][j]
			unit = node.unit

			if iemap.is_selected((i, j)):
				screen.blit(selected_node_background, (i * square + 1, j * square + 1))
			elif iemap.is_in_move_range((i, j)):
				screen.blit(unit_move_range_background, (i * square + 1, j * square + 1))
			elif iemap.is_in_attack_range((i, j)):
				screen.blit(unit_attack_range_backgroud, (i * square + 1, j * square + 1))
			elif iemap.is_played((i, j)):
				screen.blit(unit_played_backgroud, (i * square + 1, j * square + 1))
			else:
				screen.blit(node_background, (i * square + 1, j * square + 1))

			if unit is not None:
				if unit.image is None:
					scritta = FONT.render(unit.name, 1, BLACK)
					screen.blit(scritta, (i * square + 1, j * square + 1))
				else:
					if unit.image.get_size()[0] != square - 2 or unit.image.get_size()[1] != square - 2:
						image = pygame.transform.smoothscale(unit.image, (square - 2, square - 2))
					else:
						image = unit.image
					screen.blit(image, (i * square + 1, j * square + 1))

	fps = clock.get_fps()
	fpslabel = FONT.render(str(int(fps)) + ' FPS', True, (255, 255, 255))
	rec = fpslabel.get_rect(top=5, right=screen_w - 5)
	screen.blit(fpslabel, rec)
	pygame.display.flip()

def center(rect1, rect2, xoffset=0, yoffset=0):
	"""Center rect2 in rect1 with offset."""
	return (rect1.centerx - rect2.centerx + xoffset, rect1.centery - rect2.centery + yoffset)

def wait_for_user_input(clock, timeout=-1):
	"""
	This function waits for the user to left-click somewhere and,
	if the timeout argument is positive, exits after the specified
	number of seconds.
	"""
	done = False

	now = start = time.time()
	
	while not done and (now - start < timeout or timeout < 0):
		for event in pygame.event.get():
			if event.type == pygame.QUIT:  # If user clicked close
				pygame.quit()
				sys.exit()
			elif event.type == pygame.MOUSEBUTTONDOWN:
				if event.button == 1:
					done = True
		clock.tick(10)
		now = time.time()

def main_menu(screen, clock): # Main Menu
	pygame.mixer.Sound('music/Beyond The Clouds (Dungeon Plunder).ogg').play()
	
	screen_rect = screen.get_rect()

	screen.fill(BLACK)
	FONT = pygame.font.SysFont("Liberation Sans", 36)
	elinvention = FONT.render("Elinvention", 1, WHITE)
	presents = FONT.render("PRESENTS", 1, WHITE)
	
	screen.blit(elinvention, center(screen_rect, elinvention.get_rect()))
	
	screen.blit(presents, center(screen_rect, presents.get_rect(), yoffset=FONT.get_linesize()))
	
	pygame.display.flip()

	wait_for_user_input(clock, 6)

	
	main_menu_image = pygame.image.load('logo-tmp.jpg').convert()
	main_menu_image = pygame.transform.smoothscale(main_menu_image, (screen_rect.w, screen_rect.h))

	click_to_start = FONT.render("Click to Start", 1, BLACK)
	
	screen.blit(main_menu_image, (0, 0))
	screen.blit(click_to_start, center(screen_rect, click_to_start.get_rect(), yoffset=200))
	
	pygame.display.flip()
	
	wait_for_user_input(clock)

	pygame.mixer.fadeout(2000)
	time.sleep(2)


def main():
	pygame.init()
	# pygame.FULLSCREEN    create a fullscreen display
	# pygame.DOUBLEBUF     recommended for HWSURFACE or OPENGL
	# pygame.HWSURFACE     hardware accelerated, only in FULLSCREEN
	# pygame.OPENGL        create an OpenGL renderable display
	# pygame.RESIZABLE     display window should be sizeable
	# pygame.NOFRAME       display window will have no border or controls
	screen = pygame.display.set_mode((800,600), pygame.RESIZABLE)
	pygame.display.set_caption("Ice Emblem")
	clock = pygame.time.Clock()

	characters = []
	with open('characters.csv', 'r') as f:
		reader = csv.reader(f, delimiter='\t')
		fields = reader.next()
		for row in reader:
			characters.append(IEUnit(row[0], row[1], row[2], row[3],
				row[4], row[5], row[6], row[7], row[8], row[9], row[10],
				row[11], row[12], row[13], row[14], row[15], row[16],
				row[17]))
			print(row[0] + " loaded")

	w1 = IEWeapon("Biga feroce", 'E', 5, 10, 75, 3, 2, 20, 100, 20)
	w2 = IEWeapon("Stuzzicadenti", 'E', 2, 1, 100, 20, 1, 1, 1, 1)

	characters[0].give_weapon(w1)
	characters[1].give_weapon(w2)

	iemap = IEMap((15, 10), screen.get_size())
	iemap.position_unit(characters[0], (1, 2))
	iemap.position_unit(characters[1], (9, 9))

	main_menu(screen, clock)

	done = False
	while not done:
		for event in pygame.event.get():  # User did something
			if event.type == pygame.QUIT:  # If user clicked close
				done = True
			elif event.type == pygame.MOUSEBUTTONDOWN: # user click on map
				if event.button == 1:
					iemap.select(event.pos)
			elif event.type == pygame.VIDEORESIZE: # user resized window
				# It looks like this is the only way to update pygame's display
				# However this causes some issues while resizing the window
				screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)
				iemap.screen_resize(event.size) # update map sizes

		draw_map(screen, iemap, clock)
		clock.tick(10)

	pygame.quit()
	return 0


if __name__ == '__main__':
	main()
