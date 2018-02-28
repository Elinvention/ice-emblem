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


import logging
import random
import utils
import action
from operator import itemgetter


class AI(object):
    def __init__(self, _map, units_manager, team):
        self.map = _map
        self.path = _map.path
        self.units_manager = units_manager
        self.own_units = team.units
        self.enemy_units = units_manager.get_enemies(team)
        self.logger = logging.getLogger('AI')

    def __iter__(self):
        self.refresh()
        for unit in self.own_units:
            self.logger.info("Thinking what to do with %s...", unit.name)
            attackable_enemies = self.map.nearby_enemies(unit)
            self.logger.info("Nearby attackable enemies: %s", attackable_enemies)
            if len(attackable_enemies) > 0:
                target = self.best_target(attackable_enemies)
                self.logger.debug("%s attacks %s.", unit.name, target.name)
                yield action.Attack(unit, target)
            else:
                enemies = self.enemies_in_walkable_area(unit)
                self.logger.debug("Units next to %s: %s", unit.name, enemies)
                if len(enemies) > 0:
                    target = self.best_target(enemies)
                    path = self.path.shortest_path(unit.coord, target.coord, unit.movement)
                    if path:
                        dest = path[-1]
                        self.logger.debug("%s will reach %s from %s.", unit.name, target.name, dest)
                        yield action.Move(unit, dest)
                        yield action.Attack(unit, target)
                    else:
                        self.logger.debug("%s can't reach %s. Wait.", unit.name, target.name)
                        unit.played = True
                else:
                    target = self.nearest_enemy(unit)
                    path = self.path.shortest_path(unit.coord, target.coord, unit.movement)
                    self.logger.debug("Unit %s can't reach any enemy. Target is %s, path is %s." % (unit.name, target.name, path))
                    if path:
                        dest = path[-1]
                        yield action.Move(unit, dest)
                    unit.played = True

    def nearest_enemy(self, unit):
        """
        Finds the nearest enemy.
        """
        l = [(len(self.path.shortest_path(unit.coord, enemy.coord)), enemy) for enemy in self.enemy_units]
        l.sort(key=itemgetter(0))
        nearest_enemy = l[0][1]
        return nearest_enemy

    def enemies_in_walkable_area(self, unit):
        """
        Return the enemies in his area
        """
        move_area = self.path.area(unit.coord, unit.movement, False)
        min_range, max_range = unit.get_weapon_range()
        enemies = set()
        for (x, y) in move_area:
            for i in range(x - max_range, x + max_range + 1):
                for j in range(y - max_range, y + max_range + 1):
                    if min_range <= utils.distance((x, y), (i, j)) <= max_range:
                        try:
                            enemy = self.map.get_unit((i, j))
                            if enemy and self.units_manager.are_enemies(enemy, unit):
                                enemies.add(enemy)
                        except KeyError:
                            pass
        return enemies

    def best_target(self, enemies):
        """
        Choose the best enemy to attack from a list
        """
        enemies_values = [ u.value() for u in enemies ]
        ranking = list(zip(enemies_values, enemies))
        ranking.sort(key=itemgetter(0))
        best = ranking[0][1]
        return best

    def refresh(self):
        random.shuffle(self.own_units)
        random.shuffle(self.enemy_units)

