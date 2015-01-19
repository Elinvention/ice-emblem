#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Ice Emblem.py
#
#  Copyright 2014 Elia Argentieri <elia.argentieri@openmailbox.org>
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
#
#

import random
import time
import pygame
import csv
import sys

from pygame.locals import *

from ie_item import ie_item, ie_weapon
from ie_map import ie_map
from ie_unit import ie_unit

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255,200,0)


def battle(attacking, defending):
	at = 1
	dt = 1
	if attacking.Spd > defending.Spd:
		at += 1
	elif defending.Spd > attacking.Spd:
		dt += 1

	for i in range(at + dt):
		aw = attacking.getActiveWeapon()
		if aw is None or aw.Uses == 0:
			dmg = attacking.Str
			hit = attacking.Skill * 2 + attacking.Luck / 2
			print("%s attacks %s x%d" % (attacking.name, defending.name, at))
			print("Dmg: %d  Hit: %d" % (dmg, hit))
			if random.randrange(0, 100) > hit:
				print("%s misses %s" % (attacking.name, defending.name))
			else:
				print("%s inflicts %s %d damages" % (attacking.name, defending.name, dmg))
				defending.inflictDamage(dmg)
		else:
			dmg = attacking.Str + ((aw.Might))  # TODO
			hit = (attacking.Skill * 2) + aw.Hit + (attacking.Luck / 2)
			print("%s attacks %s using %s x%d" % (attacking.name, defending.name, aw.name, at))
			print("Dmg: %d  Hit: %d" % (dmg, hit))
			if random.randrange(0, 100) > hit:
				print("%s misses %s" % (attacking.name, defending.name))
			else:
				print("%s inflicts %s %d damages" % (attacking.name, defending.name, dmg))
				defending.inflictDamage(dmg)
				if not aw.use():
					break

		if defending.HP == 0:
			break

		at -= 1

		if dt > 0:
			t = attacking
			attacking = defending
			defending = t
			t = at
			at = dt
			dt = t


def draw_map(screen, iemap):
	screenx = screen.get_size()[0]
	screeny = screen.get_size()[1]
	screenxy = screen.get_rect()

	dx = screenx / iemap.dim[0]
	dy = screeny / iemap.dim[1]

	node_background = pygame.Surface((dx - 2, dy - 2)).convert()
	node_background.fill(GREEN)

	selected_node_background = pygame.Surface((dx - 2, dy - 2)).convert()
	selected_node_background.fill(YELLOW)

	unit_range_move_background = pygame.Surface((dx - 2, dy - 2)).convert()
	unit_range_move_background.fill(BLUE)

	unit_attack_range_backgroud = pygame.Surface((dx - 2, dy - 2)).convert()
	unit_attack_range_backgroud.fill(RED)

	screen.fill(BLACK)

	FONT = pygame.font.SysFont("Liberation Sans", 12)

	for i in range(0, iemap.dim[0]):
		pygame.draw.line(screen, WHITE, (i * dx, 0), (i * dx, screeny), 1)
		for j in range(0, iemap.dim[1]):
			pygame.draw.line(screen, WHITE, (0, j * dy), (screenx, j * dy), 1)

			node = iemap.matrix[i][j]
			unit = node.unit

			if iemap.isSelected((i, j)):
				screen.blit(selected_node_background, (i * dx + 1, j * dy + 1))
			elif iemap.is_in_range((i, j)):
				screen.blit(unit_range_move_background, (i * dx + 1, j * dy + 1))
			else:
				screen.blit(node_background, (i * dx + 1, j * dy + 1))

			if unit is not None:
				if unit.image is None:
					scritta = FONT.render(unit.name, 1, BLACK)
					screen.blit(scritta, (i * dx + 1, j * dy + 1))
				else:
					if unit.image.get_size()[0] - 2 > dx or unit.image.get_size()[1] - 2 > dy:
						iemap.matrix[i][j].unit.image = pygame.transform.smoothscale(unit.image, (dx - 2, dy - 2))
						unit.image = iemap.matrix[i][j].unit.image
					screen.blit(unit.image, (i * dx + 1, j * dy + 1))

	pygame.display.flip()


def main_menu(screen):
	main_menu_sound = pygame.mixer.Sound('music/Beyond The Clouds (Dungeon Plunder).ogg')
	main_menu_sound.play()
	screen_rect = screen.get_rect()
	main_menu_image = pygame.image.load('Logo.jpg').convert()
	main_menu_image = pygame.transform.smoothscale(main_menu_image, (screen_rect.w, screen_rect.h))
	screen.blit(main_menu_image, (0, 0))
	pygame.display.flip()
	
	done = False
	while not done:
		event = pygame.event.wait()
		if event.type == QUIT:  # If user clicked clos
			pygame.quit()
			sys.exit()
		elif event.type == MOUSEBUTTONDOWN:
			if event.button == 1:
				done = True


def main():

	"""data = csv.reader(open('characters.csv'), delimiter='\t')
	# Read the column names from the first line of the file
	fields = data.next()
	for row in data:
		# Zip together the field names and values
		items = zip(fields, row)
	item = {}
	# Add the value to our dictionary
	for (name, value) in items:
		item[name] = value.strip()"""
	
	pygame.init()
	screen = pygame.display.set_mode((800,600))
	pygame.display.set_caption("Ice Emblem")
	clock = pygame.time.Clock()

	characters = []
	with open('characters.csv', 'r') as f:
		reader = csv.reader(f, delimiter='\t')
		fields = reader.next()
		for row in reader:
			characters.append(ie_unit(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11], row[12], row[13], row[14], row[15], row[16], row[17]))
			print(row[0] + " loaded")

	w1 = ie_weapon("Biga feroce", 'E', 5, 10, 75, 3, 2, 20, 100, 20)
	w2 = ie_weapon("Stuzzicadenti", 'E', 2, 1, 100, 20, 1, 1, 1, 1)
	# print(w1)
	# print(w2)

	characters[0].giveWeapon(w1)
	characters[1].giveWeapon(w2)

	# while p1.HP > 0 and p2.HP > 0:
	#    print(p1)
	#    print(p2)
	#    print("------------------------------")
	#    battle(p1, p2)

	iemap = ie_map((15, 10))
	iemap.setUnit(characters[0], (1, 2))
	iemap.setUnit(characters[1], (9, 9))

	main_menu(screen)

	pygame.mixer.fadeout(2000)
	time.sleep(2)

	done = False
	while not done:
		for event in pygame.event.get():  # User did something
			if event.type == QUIT:  # If user clicked clos
				done=True  # Flag that we are done so we exit this loop
			elif event.type == MOUSEBUTTONDOWN:
				if event.button == 1:
					iemap.select(screen.get_rect(), event.pos)
		draw_map(screen, iemap)
		clock.tick(10)

	pygame.quit()
	return 0


if __name__ == '__main__':
	main()
