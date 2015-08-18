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
import utils
from item import Item, Weapon
from map import Map
from unit import Unit
from game import Game

from colors import *


# Work around for Windows
if sys.platform.startswith('win'):
	logging.debug('Windows detected')
	import locale
	if os.getenv('LANG') is None:
		logging.debug('Windows did not provide the LANG environment variable')
		lang, enc = locale.getdefaultlocale()
		os.environ['LANG'] = lang
gettext.install('ice-emblem', 'locale')  # load translations

def csv_to_objects_dict(path, _class):
	objects = {}
	with open(path, 'r') as f:
		reader = csv.reader(f, delimiter='\t')
		reader.__next__()
		for row in reader:
			objects[row[0]] = (_class(*row))
			logging.debug(_("%s loaded") % row[0])
	return objects


def main(screen):
	# command-line argument parsing
	parser = argparse.ArgumentParser(description=_('Ice Emblem, the free software clone of Fire Emblem'))
	parser.add_argument('-s','--skip', action='store_true', help=_('Skip main menu'), required=False)
	parser.add_argument('-m','--map', action='store', help=_('Which map to load'), default=None, required=False)
	args = parser.parse_args()

	# log to screen
	logging.basicConfig(level=logging.DEBUG)
	logging.info(_('Welcome to %s!') % 'Ice Emblem 0.1')
	logging.info(_('You are using Pygame version %s.') % pygame.version.ver)
	if pygame.version.vernum < (1, 9, 2):
		logging.warning(_('You are running a version of Pygame that might be outdated.'))
		logging.warning(_('Ice Emblem is tested only with Pygame 1.9.2+.'))

	units = csv_to_objects_dict(os.path.join('data', 'characters.txt'), Unit)
	weapons = csv_to_objects_dict(os.path.join('data', 'weapons.txt'), Weapon)

	# TODO: units inventory to file
	units['Boss'].give_weapon(weapons['Biga Feroce'])
	units['Pirate Tux'].give_weapon(weapons['Stuzzicadenti'])
	units['Soldier'].give_weapon(weapons['Bronze Sword'])
	units['Pirate'].give_weapon(weapons['Bronze Bow'])
	units['Ninja'].give_weapon(weapons['Knife'])
	units['Skeleton'].give_weapon(weapons['Nosferatu'])

	map_file = None
	if args.map is not None:
		map_file = os.path.join('maps', args.map + '.tmx')
		logging.debug(_('Loading map: %s') % map_file)
	elif args.skip:
		map_file = os.path.join('maps', 'default.tmx')
		logging.debug(_('Loading default map: %s') % map_file)
	else:
		logging.debug(_('No map on command line: choose the map via the main menu'))

	MAIN_GAME = Game(screen, units, map_file)

	# If the player keeps pressing the same key for 200 ms, a KEYDOWN
	# event will be generated every 50 ms
	pygame.key.set_repeat(200, 50)

	if not args.skip:
		MAIN_GAME.main_menu()

	MAIN_GAME.play()


if __name__ == '__main__':
	try:
		pygame.init()
		pygame.display.set_icon(pygame.image.load(os.path.join('images', 'icon.png')))
		screen = pygame.display.set_mode((800, 600), pygame.RESIZABLE)
		pygame.display.set_caption("Ice Emblem")
		main(screen)

	except (KeyboardInterrupt, SystemExit):
		# game was interrupted by the user
		print(_("Interrupted by user, exiting."))

		# we're not playing anymore, go away
		utils.return_to_os()

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
		utils.return_to_os()

	# we got here, so everything was normal
	print()
	print("~" * 80)
	print(_("Game terminated normally."))

	utils.return_to_os()
