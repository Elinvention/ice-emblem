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


import pygame
import csv
import argparse

from IEItem import IEItem, IEWeapon
from IEMap import IEMap, IEMapNode
from IEUnit import IEUnit, IEPlayer
from IEGame import IEGame

from Colors import *

def main():

	parser = argparse.ArgumentParser(description='Ice Emblem, the free software clone of Fire Emblem')
	parser.add_argument('-s','--skip', action='store_true', help='Skip main menu', required=False)
	args = parser.parse_args()

	player1 = IEPlayer("Blue Team", BLUE, True)
	player2 = IEPlayer("Red Team", RED)

	test_map = IEMap((15, 10), (800, 600))  # Create a 15x10 map on a 800x600 screen

	test_map.nodes[5][5].tile = IEMapNode.GRASS
	test_map.nodes[4][5].tile = (80, 870)
	test_map.nodes[4][6].tile = (80, 934)
	test_map.nodes[5][6].tile = IEMapNode.CASTLE1
	test_map.nodes[6][5].tile = (160, 870)
	test_map.nodes[8][8].tile = IEMapNode.CASTLE2
	test_map.nodes[2][8].tile = IEMapNode.CASTLE3
	test_map.nodes[2][7].tile = IEMapNode.GRASS
	test_map.nodes[2][9].tile = IEMapNode.GRASS
	test_map.nodes[1][8].tile = IEMapNode.GRASS
	test_map.nodes[3][8].tile = IEMapNode.GRASS
	test_map.nodes[2][2].tile = IEMapNode.WATER
	test_map.nodes[2][2].walkable = False


	colors = dict(selected=YELLOW_A50, move_range=BLUE_A50, attack_range=RED_A50, played=GREY_A200)
	music = dict(overworld='music/Ireland\'s Coast - Video Game.ogg', battle='music/The Last Encounter Short Loop.ogg', menu='music/Beyond The Clouds (Dungeon Plunder).ogg')
	
	MAIN_GAME = IEGame([player1, player2], test_map, 'sprites/tileset.png', music, colors)

	units = {}
	with open('data/characters.txt', 'r') as f:
		reader = csv.reader(f, delimiter='\t')
		fields = reader.next()
		for row in reader:
			units[row[0]] = (IEUnit(row[0], row[1], row[2], row[3],
				row[4], row[5], row[6], row[7], row[8], row[9], row[10],
				row[11], row[12], row[13], row[14], row[15], row[16],
				row[17]))
			print(row[0] + " loaded")

	weapons = {}
	with open('data/weapons.txt', 'r') as f:
		reader = csv.reader(f, delimiter='\t')
		fields = reader.next()
		for row in reader:
			weapons[row[0]] = (IEWeapon(row[0], row[1], row[2], row[3],
				row[4], row[5], row[6], row[7], row[8], row[9]))
			print(row[0] + " loaded")
	
	units['Boss'].give_weapon(weapons['Biga Feroce'])
	units['Pirate Tux'].give_weapon(weapons['Stuzzicadenti'])
	units['Soldier'].give_weapon(weapons['Bronze Sword'])
	units['Pirate'].give_weapon(weapons['Bronze Bow'])
	units['Ninja'].give_weapon(weapons['Knife'])
	units['Skeleton'].give_weapon(weapons['Nosferatu'])

	player1.units = [units['Boss'], units['Skeleton'], units['Soldier']]
	player2.units = [units['Pirate Tux'], units['Ninja'], units['Pirate']]

	test_map.position_unit(units['Boss'], (5, 2))
	test_map.position_unit(units['Pirate Tux'], (6, 3))
	test_map.position_unit(units['Soldier'], (3, 4))
	test_map.position_unit(units['Pirate'], (4, 5))
	test_map.position_unit(units['Ninja'], (5, 6))
	test_map.position_unit(units['Skeleton'], (5, 7))

	if not args.skip:
		MAIN_GAME.main_menu()
		pygame.mixer.stop()
	MAIN_GAME.play_overworld_music()
	
	done = False
	while not done:
		for event in pygame.event.get():  # User did something
			if event.type == pygame.QUIT:  # If user clicked close
				done = True
			elif event.type == pygame.MOUSEBUTTONDOWN: # user click on map
				MAIN_GAME.handle_click(event)
			elif event.type == pygame.MOUSEMOTION:
				MAIN_GAME.handle_mouse_motion(event)
			elif event.type == pygame.VIDEORESIZE: # user resized window
				# It looks like this is the only way to update pygame's display
				# However this causes some issues while resizing the window
				MAIN_GAME.screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)
				MAIN_GAME.screen_resize(event.size) # update map sizes

		if MAIN_GAME.winner is not None:
			MAIN_GAME.victory_screen()
			done = True
		else:
			MAIN_GAME.draw_map()
			MAIN_GAME.draw_fps()
			pygame.display.flip()
			MAIN_GAME.clock.tick(10)

	pygame.quit()
	return 0


if __name__ == '__main__':
	main()
