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

from operator import itemgetter

import utils
import action
import state as s

from unit import Team


class AI(Team):
    def __init__(self, name, color, relation, units, boss, music):
        super().__init__(name, color, relation, units, boss, music)
        self.logger = logging.getLogger('AI')

    def __iter__(self):
        _map = s.loaded_map
        _path = _map.path
        random.shuffle(self.units)
        for unit in self.units:
            if s.winner is not None:
                return
            self.logger.info("Thinking what to do with %s...", unit.name)
            attackable_enemies = _map.nearby_enemies(unit)
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
                    path = _path.shortest_path(unit.coord, target.coord, unit.movement)
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
                    path = _path.shortest_path(unit.coord, target.coord, unit.movement)
                    self.logger.debug("Unit %s can't reach any enemy. Target is %s, path is %s." % (unit.name, target.name, path))
                    if path:
                        dest = path[-1]
                        yield action.Move(unit, dest)
                    unit.played = True

    def nearest_enemy(self, unit):
        """
        Finds the nearest enemy.
        """
        _path = s.loaded_map.path
        enemy_units = s.units_manager.get_enemies(self)
        random.shuffle(enemy_units)
        l = [(len(_path.shortest_path(unit.coord, enemy.coord)), enemy) for enemy in enemy_units]
        l.sort(key=itemgetter(0))
        nearest_enemy = l[0][1]
        return nearest_enemy

    def enemies_in_walkable_area(self, unit):
        """
        Return the enemies in his area
        """
        _path = s.loaded_map.path
        move_area = _path.area(unit.coord, unit.movement, False)
        min_range, max_range = unit.get_weapon_range()
        enemies = set()
        for (x, y) in move_area:
            for i in range(x - max_range, x + max_range + 1):
                for j in range(y - max_range, y + max_range + 1):
                    if min_range <= utils.distance((x, y), (i, j)) <= max_range:
                        try:
                            enemy = s.loaded_map.get_unit((i, j))
                            if enemy and s.units_manager.are_enemies(enemy, unit):
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
