#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  main.py
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
import traceback
import logging
import os
import sys

import gettext
gettext.install('ice-emblem', 'locale')

from item import Item, Weapon
from map import Map
from unit import Unit, Player
from game import Game

from colors import *


def main(screen):
	
	parser = argparse.ArgumentParser(description=_('Ice Emblem, the free software clone of Fire Emblem'))
	parser.add_argument('-s','--skip', action='store_true', help=_('Skip main menu'), required=False)
	parser.add_argument('-m','--map', action='store', help=_('Which map to load'), default=None, required=False)
	args = parser.parse_args()

	logging.basicConfig(level=logging.DEBUG)
	logging.info(_('Welcome to %s!') % 'Ice Emblem 0.1')

	colors = dict(selected=(255, 200, 0, 100), move=(0, 0, 255, 75), attack=(255, 0, 0, 75), played=(100, 100, 100, 150))
	music = dict(overworld='music/Ireland\'s Coast - Video Game.ogg', battle='music/The Last Encounter Short Loop.ogg', menu='music/Beyond The Clouds (Dungeon Plunder).ogg')

	units = {}
	with open('data/characters.txt', 'r') as f:
		reader = csv.reader(f, delimiter='\t')
		reader.__next__()
		for row in reader:
			units[row[0]] = (Unit(row[0], row[1], row[2], row[3],
				row[4], row[5], row[6], row[7], row[8], row[9], row[10],
				row[11], row[12], row[13], row[14], row[15], row[16],
				row[17]))
			logging.debug(row[0] + " loaded")

	weapons = {}
	with open('data/weapons.txt', 'r') as f:
		reader = csv.reader(f, delimiter='\t')
		fields = reader.__next__()
		for row in reader:
			weapons[row[0]] = (Weapon(row[0], row[1], row[2], row[3],
				row[4], row[5], row[6], row[7], row[8], row[9], None))
			logging.debug(row[0] + " loaded")

	units['Boss'].give_weapon(weapons['Biga Feroce'])
	units['Pirate Tux'].give_weapon(weapons['Stuzzicadenti'])
	units['Soldier'].give_weapon(weapons['Bronze Sword'])
	units['Pirate'].give_weapon(weapons['Bronze Bow'])
	units['Ninja'].give_weapon(weapons['Knife'])
	units['Skeleton'].give_weapon(weapons['Nosferatu'])

	player1_units = [units['Boss'], units['Skeleton'], units['Soldier']]
	player2_units = [units['Pirate Tux'], units['Ninja'], units['Pirate']]

	player1 = Player(_("Blue Team"), BLUE, True, player1_units)
	player2 = Player(_("Red Team"), RED, False, player2_units)

	map_file = None
	if args.map is not None:
		map_file = os.path.join('maps', args.map + '.tmx')
		logging.debug(_('Loading map: %s') % map_file)
	elif args.skip:
		map_file = os.path.join('maps', 'default.tmx')
		logging.debug(_('Loading default map: %s') % map_file)
	else:
		logging.debug(_('No map on command line: choose the map via the main menu'))

	MAIN_GAME = Game(screen, units, [player1, player2], map_file, music, colors)

	# If the player keeps pressing the same key for 200 ms, a KEYDOWN
	# event will be generated every 50 ms
	pygame.key.set_repeat(200, 50)

	if not args.skip:
		MAIN_GAME.main_menu()
		pygame.mixer.stop()

	MAIN_GAME.play_overworld_music()

	done = False
	while not done:
		for event in pygame.event.get():  # User did something
			if event.type == pygame.QUIT:  # If user clicked close
				done = True
			else:
				MAIN_GAME.handle_event(event)

		if MAIN_GAME.winner is not None:
			MAIN_GAME.victory_screen()
			done = True
		else:
			MAIN_GAME.screen.fill(BLACK)
			MAIN_GAME.blit_map()
			MAIN_GAME.blit_info()
			MAIN_GAME.blit_fps()
			pygame.display.flip()
			MAIN_GAME.clock.tick(25)


if __name__ == '__main__':
	try:
		pygame.init()
		screen = pygame.display.set_mode((800, 600), pygame.RESIZABLE)
		pygame.display.set_caption("Ice Emblem")
		main(screen)

	except (KeyboardInterrupt, SystemExit):
		# game was interrupted by the user
		print(_("Interrupted by user, exiting."))

		# we're not playing anymore, go away
		pygame.quit()
		sys.exit(0)

	except:
		# other error
		kind_error_message = _("""
Oops, something went wrong. Dumping brain contents:

%s
%s
%s

Please mail this stack trace to %s
along with a short description of what you did when this crash happened
so that the error can be fixed.

Thank you!
-- the Ice Emblem team

""") % ('~' * 80, traceback.format_exc(), '~' * 80, "elia.argentieri@openmailbox.org")

		print(kind_error_message)
		
		# we're not playing anymore, go away
		pygame.quit()
		sys.exit(0)

	# we got here, so everything was normal
	print()
	print("~" * 80)
	print(_("Game terminated normally."))

	pygame.quit()
	sys.exit(0)
