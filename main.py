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

from datetime import datetime
#from datetime import timedelta

import time
import pygame
import csv
import sys
import os.path

from IEItem import IEItem, IEWeapon
from IEMap import IEMap
from IEUnit import IEUnit, IEPlayer

from Colors import *

def timestamp_millis_64():
    return int((datetime.utcnow() - datetime(1970, 1, 1)).total_seconds() * 1000) 

def draw_map(screen, iemap, clock, tileset):
	"""Let's draw everything!"""
	screen_w, screen_h = screen.get_size()
	#screen_rect = screen.get_rect()

	square = (iemap.tile_size - 2, iemap.tile_size - 2)
	side = iemap.tile_size

	map_w = square * iemap.w
	map_h = square * iemap.h

	screen.fill(BLACK)

	FONT = pygame.font.SysFont("Liberation Sans", 24)

	for i in range(0, iemap.w):
		# pygame.draw.line(screen, WHITE, (i * side, 0), (i * side, map_h), 1)
		for j in range(0, iemap.h):
			# pygame.draw.line(screen, WHITE, (0, j * side), (map_w, j * side), 1)

			node = iemap.map[i][j]
			unit = node.unit

			node_background = tileset.subsurface(pygame.Rect(iemap.map[i][j].tile, (64, 64)))
			node_background = pygame.transform.smoothscale(node_background, square)
			screen.blit(node_background, (i * side, j * side))

			if iemap.is_selected((i, j)):
				screen.blit(iemap.selected_node_background, (i * side, j * side))
			elif iemap.is_in_move_range((i, j)):
				screen.blit(iemap.unit_move_range_background, (i * side, j * side))
			elif iemap.is_in_attack_range((i, j)):
				screen.blit(iemap.unit_attack_range_backgroud, (i * side, j * side))
			elif iemap.is_played((i, j)):
				screen.blit(iemap.unit_played_backgroud, (i * side, j * side))

			if unit is not None:
				if unit.image is None:
					scritta = FONT.render(unit.name, 1, BLACK)
					screen.blit(scritta, (i * side, j * side))
				else:
					if unit.image.get_size() != square:
						image = pygame.transform.smoothscale(unit.image, square)
					else:
						image = unit.image
					screen.blit(image, (i * side, j * side))

	fps = clock.get_fps()
	fpslabel = FONT.render(str(int(fps)) + ' FPS', True, WHITE)
	rec = fpslabel.get_rect(top=5, right=screen_w - 5)
	screen.blit(fpslabel, rec)

	cell_x, cell_y = iemap.mouse2cell(pygame.mouse.get_pos())
	if cell_x is not None and cell_y is not None:
		cell_label = FONT.render('X: %d Y: %d' % (cell_x, cell_y), True, WHITE)
		rec = cell_label.get_rect(bottom=screen_h - 5, left=5)
		screen.blit(cell_label, rec)
	pygame.display.flip()

def center(rect1, rect2, xoffset=0, yoffset=0):
	"""Center rect2 in rect1 with offset."""
	return (rect1.centerx - rect2.centerx + xoffset, rect1.centery - rect2.centery + yoffset)

def wait_for_user_input(clock, timeout=-1):
	"""
	This function waits for the user to left-click somewhere and,
	if the timeout argument is positive, exits after the specified
	number of milliseconds.
	"""
	done = False

	now = start = timestamp_millis_64()
	
	while not done and (now - start < timeout or timeout < 0):
		for event in pygame.event.get():
			if event.type == pygame.QUIT:  # If user clicked close
				pygame.quit()
				sys.exit()
			elif event.type == pygame.MOUSEBUTTONDOWN:
				if event.button == 1:
					done = True
		clock.tick(10)
		now = timestamp_millis_64()

def main_menu(screen, clock): # Main Menu
	pygame.mixer.Sound('music/Beyond The Clouds (Dungeon Plunder).ogg').play()
	
	screen_rect = screen.get_rect()

	screen.fill(BLACK)

	path = os.path.abspath('fonts/Medieval Sharp/MedievalSharp.ttf')
	FONT = pygame.font.Font(path, 48)
	elinvention = FONT.render("Elinvention", 1, WHITE)
	presents = FONT.render("PRESENTS", 1, WHITE)
	
	screen.blit(elinvention, center(screen_rect, elinvention.get_rect()))
	
	screen.blit(presents, center(screen_rect, presents.get_rect(), yoffset=FONT.get_linesize()))
	
	pygame.display.flip()

	wait_for_user_input(clock, 6000)

	path = os.path.abspath('images/Ice_Emblem_Logo_prototype4.png')
	main_menu_image = pygame.image.load(path).convert_alpha()
	main_menu_image = pygame.transform.smoothscale(main_menu_image, (screen_rect.w, screen_rect.h))

	click_to_start = FONT.render("Click to Start", 1, ICE)
	
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
	with open('data/characters.csv', 'r') as f:
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

	player1 = IEPlayer("Player 1", [characters[0]], BLUE, True)
	player2 = IEPlayer("Player 2", [characters[1]], RED)

	test_map = IEMap((15, 10), screen.get_size(), YELLOW_A50, BLUE_A50, RED_A50, GREY_A50)

	test_map.position_unit(characters[0], (1, 2))
	test_map.position_unit(characters[1], (9, 9))
	test_map.map[5][5].tile =(32, 672)
	test_map.map[4][5].tile =(80, 870)
	test_map.map[4][6].tile =(80, 934)
	test_map.map[5][6].tile =(32, 545)
	test_map.map[6][5].tile =(160, 870)
	test_map.map[8][8].tile =(130, 545)
	test_map.map[2][8].tile =(192, 545)
	test_map.map[2][2].tile =(32, 160)

	main_menu(screen, clock)

	path = os.path.abspath('sprites/tileset.png')
	tileset = pygame.image.load(path).convert()

	done = False
	while not done:
		for event in pygame.event.get():  # User did something
			if event.type == pygame.QUIT:  # If user clicked close
				done = True
			elif event.type == pygame.MOUSEBUTTONDOWN: # user click on map
				if event.button == 1:
					map_coords = test_map.mouse2cell(event.pos)
					if map_coords is not None:
						sel = test_map.select(map_coords)
						if sel == 1:
							print("Attack!!!")
							pygame.mixer.Sound('music/The Last Encounter Short Loop.ogg').play()
							# battle()
							# pygame.mixer.fadeout(2000)
					if player1.my_turn:
						if player1.is_turn_over():
							player1.end_turn()
					elif player2.my_turn:
						if player2.is_turn_over():
							player2.end_turn()
			elif event.type == pygame.VIDEORESIZE: # user resized window
				# It looks like this is the only way to update pygame's display
				# However this causes some issues while resizing the window
				screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)
				test_map.screen_resize(event.size) # update map sizes

		draw_map(screen, test_map, clock, tileset)
		clock.tick(10)

	pygame.quit()
	return 0


if __name__ == '__main__':
	main()
