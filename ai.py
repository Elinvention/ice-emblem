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
	def __init__(self, _map, units_manager, team, battle):
		self.map = _map
		self.path = _map.path
		self.units_manager = units_manager
		self.battle = battle
		self.own_units = team.units
		self.enemy_units = units_manager.get_enemies(team)
		self.logger = logging.getLogger('AI')

	def __call__(self):
		self.refresh()
		for unit in self.own_units:
			self.logger.info("Thinking what to do with %s..." % unit.name)
			attackable_enemies_coord = self.map.nearby_enemies(unit)
			if len(attackable_enemies_coord) > 0:
				target = self.coord_best_target(attackable_enemies_coord)
				attacking = unit
				defending = self.map.get_unit(target)
				self.logger.debug("%s attack %s." % (attacking.name, defending.name))
				self.battle(attacking, defending)
			else:
				enemies = self.list_coord_enemies_in_area(unit)
				self.logger.debug("Units next to %s: %s" % (unit.name, enemies))
				if len(enemies) > 1:
					target = self.coord_best_target(enemies)
					path = self.path.shortest_path(unit.coord, target, unit.move)
					if len(path) > unit.move:
						dest = path[-1]
					else:
						dest = path[-2]
					attacking = unit
					defending = self.map.get_unit(target)
					logging.debug("AI: %s can reach %s from %s." % (attacking.name, defending.name, dest))
					self.map.move(unit, dest)
					self.battle(attacking, defending)
				else:
					target = self.coord_nearest_enemy(unit.coord)
					path = self.path.shortest_path(unit.coord, target, unit.move)
					self.logger.debug("Unit %s can't reach any enemy. Target is %s, path is %s." % (unit.name, target, path))
					dest = path[-1]  # furthest reachable location
					self.map.move(unit, dest)
					unit.played = True

	def coord_nearest_enemy(self, own_coord):
		l = [(len(self.path.shortest_path(own_coord, enemy.coord)), enemy.coord) for enemy in self.enemy_units]
		l.sort(key=itemgetter(0))
		nearest_enemy = l[0][1]
		return nearest_enemy

	def list_coord_enemies_in_area(self, unit):
		radius = unit.move + unit.get_weapon_range()
		attack_area = self.path.area(unit.coord, radius)
		enemies_coord = []
		for coord in attack_area:
			unit_attack = self.map.get_unit(coord)
			if unit_attack is not None and self.units_manager.are_enemies(unit_attack, unit):
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
		random.shuffle(self.own_units)
		random.shuffle(self.enemy_units)


