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
import argparse
import traceback
import logging
import os
import sys
import gettext
import utils
from colors import *

import resources


os.chdir(os.path.dirname(os.path.abspath(__file__)))

VERSION = utils.read('VERSION').strip('\n')

# Gettext work around for Windows
if sys.platform.startswith('win'):
	logging.debug('Windows detected')
	import locale
	if os.getenv('LANG') is None:
		logging.debug('Windows did not provide the LANG environment variable.')
		lang, enc = locale.getdefaultlocale()
		os.environ['LANG'] = lang
		logging.debug('Language: %s' % lang)
gettext.install('ice-emblem', resources.LOCALE_PATH)  # load translations


try:
	# command-line argument parsing
	parser = argparse.ArgumentParser(description=_('Ice Emblem, the free software clone of Fire Emblem'))
	parser.add_argument('--version', action='version', version='Ice Emblem '+VERSION)
	parser.add_argument('-s', '--skip', action='store_true', help=_('Skip main menu'), required=False)
	parser.add_argument('-m', '--map', action='store', help=_('Which map to load'), default=None, required=False)
	parser.add_argument('-l', '--logging', action='store', help=_('Choose logging level'), default=20, type=int, required=False)
	parser.add_argument('-f', '--file', action='store', help=_('Log file'), default=None, required=False)
	args = parser.parse_args()

	# log to screen
	logging.basicConfig(level=args.logging, filename=args.file, filemode='a')
	logging.info(_('Welcome to %s!') % ('Ice Emblem ' + VERSION))
	logging.info(_('You are using Pygame version %s.') % pygame.version.ver)
	if pygame.version.vernum < (1, 9, 2):
		logging.warning(_('You are running a version of Pygame that might be outdated.'))
		logging.warning(_('Ice Emblem is tested only with Pygame 1.9.2+.'))

	pygame.mixer.pre_init(frequency=44100, size=-16, channels=2)
	pygame.init()
	pygame.display.set_icon(resources.load_image('icon.png'))
	screen = pygame.display.set_mode((1280, 720), pygame.RESIZABLE)
	pygame.display.set_caption("Ice Emblem " + VERSION)
	# If the player keeps pressing the same key for 200 ms, a KEYDOWN
	# event will be generated every 50 ms
	pygame.key.set_repeat(200, 50)

	import map
	import game

	map_file = None
	if args.map is not None:
		map_file = resources.map_path(args.map)
		logging.debug(_('Loading map: %s') % map_file)
	elif args.skip:
		map_file = resources.map_path('default.tmx')
		logging.debug(_('Loading default map: %s') % map_file)
	else:
		logging.debug(_('No map on command line: choose the map via the main menu'))

	MAIN_GAME = game.Game(screen, map_file)

	if not args.skip:
		MAIN_GAME.main_menu()

	MAIN_GAME.play()

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

Please open a report on our issue tracker lacated at %s
along with a short description of what you did when this crash happened
so that the error can be fixed.

Thank you!
-- the Ice Emblem team

""") % ('-' * 80 + '\n', traceback.format_exc(), '-' * 80, "https://gitlab.com/Elinvention/ice-emblem/issues")

	print(kind_error_message)

	fname = args.file if args.file else "traceback.log"
	with open(fname, 'a') as f:
		traceback.print_exc(file=f)
		f.write('\n' + '-' * 80 + '\n\n')

	# we're not playing anymore, go away
	utils.return_to_os()

# we got here, so everything was normal
print()
print("-" * 80)
print(_("Game terminated normally."))

utils.return_to_os()

