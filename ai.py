# -*- coding: utf-8 -*-
#
#  ai.py, Ice Emblem's main game class.
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


# http://www.checkmarkgames.com/2012/03/building-strategy-game-ai.html

import logging
import utils
import random
from operator import itemgetter


class AI(object):
	def __init__(self, map, color, battle):
		self.map   = map
		self.color = color
		self.battle = battle
		self.enemy = []
		self.own   = []
		for sprite in self.map.sprites:
			if sprite.unit.color != color:
				self.enemy.append(sprite)
			else:
				self.own.append(sprite)

	def __call__(self):
		self.refresh()
		#kill_list = kills(self.enemy)  # Trovo la classifica delle best kill
		for sprite in self.own:
			attackable_enemies = self.map.nearby_units(sprite.coord, self.color)
			if len(attackable_enemies) > 0:
				target = self.find_next_target(attackable_enemies)
				self.battle(sprite.unit, self.map.get_unit(target))
			else:
				enemies = self.enemy_on_area(sprite)
				if len(enemies) > 0:
					target = self.find_next_target(enemies)
					self.map.move(sprite.coord, target)
					self.battle(sprite.unit, self.map.get_unit(enemies[0]))
				else:
					enemies = self.nearest_unit(sprite.coord)
					self.map.move(sprite.coord, enemies)
					sprite.unit.played = True

	def nearest_unit(self, coord):
		self.map.path.dijkstra(coord)
		l = [ (len(self.map.path.shortest_path(sprite.coord)), sprite) for sprite in self.enemy ]
		l.sort(key=itemgetter(0))
		path_to_best = self.map.path.shortest_path(l[0][1].coord)
		return path_to_best[self.map.get_unit(coord).move - 1]

	def enemy_on_area(self, sprite):
		self.map.path.dijkstra(sprite.coord)
		attack_area = self.map.path.area(sprite.unit.move + sprite.unit.get_weapon_range())
		enemies = [ coord for coord in attack_area if self.map.get_unit(coord) is not None ]
		return enemies

	def find_next_target(self, enemies_coord):
		enemies_unit = list(map(self.map.get_unit, enemies_coord))
		enemies_values = [ u.value() for u in enemies_unit ]
		ranking = list(zip(enemies_values, enemies_coord))
		ranking.sort(key=itemgetter(0))
		best = ranking[0][1]
		return best

	def refresh(self):
		for sprite in self.own:
			if sprite is None:
				self.own.remove(sprite)
		for sprite in self.enemy:
			if sprite is None:
				self.enemy.remove(sprite)
		random.shuffle(self.own)
		random.shuffle(self.enemy)


