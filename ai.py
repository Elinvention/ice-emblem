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

"""
http://www.checkmarkgames.com/2012/03/building-strategy-game-ai.html
"""


import logging
import random
from operator import itemgetter


class AI(object):
	def __init__(self, map, color, battle):
		self.map    = map
		self.color  = color
		self.battle = battle
		self.enemy_sprite = []
		self.own_sprite   = []
		for sprite in self.map.sprites:
			if sprite.unit.color != color:
				self.enemy_sprite.append(sprite)
			else:
				self.own_sprite.append(sprite)

	def __call__(self):
		self.refresh()
		for sprite in self.own_sprite:
			logging.info("AI: Thinking what to do with %s..." % sprite.unit.name)
			self.map.path.obstacles = self.map.list_obstacles(sprite.unit)
			attackable_enemies_coord = self.map.nearby_units(sprite.coord, [self.color])
			if len(attackable_enemies_coord) > 0:
				target = self.coord_best_target(attackable_enemies_coord)
				attacking = sprite.unit
				defending = self.map.get_unit(target)
				logging.debug("AI: %s attack %s." % (attacking.name, defending.name))
				self.battle(attacking, defending)
			else:
				enemies = self.list_coord_enemies_in_area(sprite)
				if len(enemies) > 1:
					target = self.coord_best_target(enemies)
					path = self.map.path.shortest_path(sprite.coord, target, sprite.unit.move)
					if len(path) > sprite.unit.move:
						dest = path[-1]
					else:
						dest = path[-2]
					attacking = sprite.unit
					defending = self.map.get_unit(target)
					logging.debug("AI: %s can reach %s from %s." % (attacking.name, defending.name, dest))
					self.map.move(sprite.coord, dest)
					self.battle(attacking, defending)
				else:
					target = self.coord_nearest_enemy(sprite.coord)
					path = self.map.path.shortest_path(sprite.coord, target, sprite.unit.move)
					logging.debug("AI: Unit %s can't reach any enemy. Target is %s, path is %s." % (sprite.unit.name, target, path))
					dest = path[-1]  # furthest reachable location
					self.map.move(sprite.coord, dest)
					sprite.unit.played = True

	def coord_nearest_enemy(self, own_coord):
		l = [ (len(self.map.path.shortest_path(own_coord, enemy_sprite.coord)), enemy_sprite.coord) for enemy_sprite in self.enemy_sprite ]
		l.sort(key=itemgetter(0))
		nearest_enemy = l[0][1]
		return nearest_enemy

	def list_coord_enemies_in_area(self, sprite):
		radius = sprite.unit.move + sprite.unit.get_weapon_range()
		attack_area = self.map.path.area(sprite.coord, radius)
		enemies_coord = []
		for coord in attack_area:
			unit = self.map.get_unit(coord)
			if unit is not None and unit.color != sprite.unit.color:
				enemies_coord.append(coord)
		return enemies_coord

	def coord_best_target(self, enemies_coord):
		enemies_unit = [self.map.get_unit(coord) for coord in enemies_coord]
		enemies_values = [ u.value() for u in enemies_unit ]
		ranking = list(zip(enemies_values, enemies_coord))
		ranking.sort(key=itemgetter(0))
		best = ranking[0][1]
		return best

	def refresh(self):
		for sprite in self.own_sprite:
			if sprite is None:
				self.own_sprite.remove(sprite)
		for sprite in self.enemy_sprite:
			if sprite is None:
				self.enemy_sprite.remove(sprite)
		random.shuffle(self.own_sprite)
		random.shuffle(self.enemy_sprite)
		self.map.path.reset()


