# -*- coding: utf-8 -*-
#
#  Unit.py, Ice Emblem's unit class.
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
import random
import logging

import utils
import resources
import string

from typing import Tuple, List, Dict
from gettext import gettext as _
from abc import ABC, abstractmethod


class Items(list):
    def __init__(self, active=None, *args):
        super().__init__(*args)
        self._active = active

    @property
    def active(self):
        return self._active

    @active.setter
    def active(self, value):
        if value in self:
            self._active = value
        else:
            raise ValueError("Active Item must be in list")


class HealthCondition(ABC):
    ICON = pygame.Surface((10, 10))

    def __init__(self, unit):
        self.unit = unit

    @abstractmethod
    def turn_begin(self):
        pass

    @abstractmethod
    def turn_end(self):
        pass

    @abstractmethod
    def attack(self, damage):
        pass

    @abstractmethod
    def defend(self, damage):
        pass


class NormalHealthCondition(HealthCondition):
    def turn_begin(self):
        return

    def turn_end(self):
        return

    def attack(self, damage):
        return damage

    def defend(self, damage):
        return damage

    def __str__(self):
        return f"OK"


class HealingHealthCondition(NormalHealthCondition):
    def __init__(self, unit, amount):
        super().__init__(unit)
        self.amount = amount

    def turn_begin(self):
        self.unit.heal(self.amount)

    def __str__(self):
        return f"Healing (+{self.amount} HP/turn)"


class PoisonedHealthCondition(NormalHealthCondition):
    def __init__(self, unit, amount):
        super().__init__(unit)
        self.amount = amount

    def turn_end(self):
        self.unit.inflict_damage(self.amount)

    def __str__(self):
        return f"Poisoned (-{self.amount} HP/turn)"


class ElementalAffinity(ABC):
    ICON = None
    NAME = ""
    DESCRIPTION = ""

    def attack(self, unit, ally, att):
        if isinstance(ally.affinity, type(self)):
            print(f"There is affinity between {unit} and {ally}. Attack * 2.")
            return att * 2
        return att

    def __str__(self):
        return self.NAME


class AnimaAffinity(ElementalAffinity):
    NAME = _("Anima")
    DESCRIPTION = _("")


class DarkAffinity(ElementalAffinity):
    NAME = _("Dark")
    DESCRIPTION = _("")


class FireAffinity(ElementalAffinity):
    NAME = _("Fire")
    DESCRIPTION = _("")


class IceAffinity(ElementalAffinity):
    NAME = _("Ice")
    DESCRIPTION = _("")


class LightAffinity(ElementalAffinity):
    NAME = _("Light")
    DESCRIPTION = _("")


class ThunderAffinity(ElementalAffinity):
    NAME = _("Thunder")
    DESCRIPTION = _("")


class WindAffinity(ElementalAffinity):
    NAME = _("Wind")
    DESCRIPTION = _("")


class Unit(object):
    """
    This class is a unit with stats
    """

    ALLOWED_TERRAINS = ['earth']

    def __init__(self, name, health, level, experience, strength, skill, speed, luck, defence, resistance, movement,
                 constitution, aid, affinity, wrank, health_max=None):
        self.name         = str(name)          # name of the Unit
        self.health       = int(health)        # current health
        self.health_max   = health_max if health_max else self.health  # maximum health
        self.health_prev  = health             # HP before an attack
        self.level        = int(level)         # level
        self.level_prev   = self.level
        self.experience   = int(experience)    # experience
        self.exp_prev     = experience
        self.strength     = int(strength)      # strength determines the damage inflicted to the enemy
        self.skill        = int(skill)         # skill chance of hitting the enemy
        self.speed        = int(speed)         # speed chance to avoid enemy's attack
        self.luck         = int(luck)          # luck influences many things
        self.defence      = int(defence)       # defence reduces physical damages
        self.resistance   = int(resistance)    # resistance reduces magical damages
        self.movement     = int(movement)      # movement determines how far the unit can move in a turn
        self.constitution = int(constitution)  # constitution, or physical size. affects rescues.
        self.aid          = int(aid)           # max rescuing constitution. units with lower con can be rescued.
        self.affinity     = affinity           # elemental affinity. determines compatibility with other units.
        self.condition    = NormalHealthCondition(self)
        self.wrank        = wrank              # weapons' levels.
        self.items        = Items()            # list of items
        self.played       = False              # whether unit was used or not in a turn
        self.team         = None               # team
        self.coord        = None
        self.modified     = True
        try:
            self.image = resources.load_sprite(self.name).convert_alpha()
            new_size = utils.resize_keep_ratio(self.image.get_size(), (200, 200))
            self.image = pygame.transform.smoothscale(self.image, new_size)
        except FileNotFoundError:
            logging.warning("Couldn't load %s! Loading default image", resources.sprite_path(self.name))
            self.image = resources.load_sprite('no_image.png').convert_alpha()

    def __repr__(self):
        return "<Unit %s at %s>" % (self.name, self.coord)

    def __str__(self):
        return (
            'Unit: "{name}"\n'
            'HP: {health}/{health_max}\n'
            'LV: {level}\tEXP: {experience}\n'
            'Str: {strength}\tSkill: {skill}\n'
            'Spd: {speed}\tLuck: {luck}\n'
            'Def: {defence}\tRes: {resistance}\n'
            'Move: {movement}\tCon: {constitution}\n'
            'Aid: {aid}\tAffin: {affinity}\n'
            'Weapon: {items.active}'
            .format_map(self.__dict__)
        )

    @property
    def weapon(self):
        return self.items.active

    def give_weapon(self, weapon, activate=True) -> None:
        """
        Gives a weapon to the unit. The weapon becomes active by default if
        its rank is lower or equals to the rank of the unit. 
        """
        self.items.append(weapon)
        if activate:
            weapon_class = weapon.__class__.__name__
            if weapon_class in self.wrank and weapon.rank <= self.wrank[weapon_class]:
                self.items.active = weapon
            else:
                print("Unit %s can't use a %s" % (self.name, weapon_class))
        self.modified = True

    def health_variation(self, amount: int):
        self.health += amount
        if self.health <= 0:
            self.health = 0
            print(_("%s died") % self.name)
        elif self.health > self.health_max:
            self.health = self.health_max
            print(_("%s fully recovered.") % self.name)
        self.modified = True

    def inflict_damage(self, dmg: int) -> None:
        """Inflicts damages to the unit."""
        if dmg > 0:
            self.health_variation(-dmg)

    def heal(self, amount):
        if amount > 0:
            self.health_variation(amount)

    def get_weapon_range(self) -> Tuple[int, int]:
        active_weapon = self.items.active
        if active_weapon:
            return active_weapon.min_range, active_weapon.max_range
        return 1, 1

    def number_of_attacks(self, enemy: 'Unit') -> Tuple[int, int]:
        """
        Returns a tuple: how many times this unit can attack the enemy
        and how many times the enemy can attack this unit in a single battle
        """
        distance = utils.distance(self.coord, enemy.coord)
        self_attacks = enemy_attacks = 1

        if self.speed > enemy.speed:
            self_attacks += 1
        elif enemy.speed > self.speed:
            enemy_attacks += 1

        self_range = self.get_weapon_range()
        enemy_range = enemy.get_weapon_range()
        if not self_range[0] <= distance <= self_range[1]:
            self_attacks = 0
        if not enemy_range[0] <= distance <= enemy_range[1]:
            enemy_attacks = 0

        return self_attacks, enemy_attacks

    def life_percent(self) -> int:
        return int(float(self.health) / float(self.health_max) * 100.0)

    def attack(self, enemy: 'Unit') -> Tuple[str, int]:
        if self.weapon is None or self.weapon.uses == 0:
            print(_("%s attacks %s with his bare hands") % (self.name, enemy.name))
            hit_probability = self.skill * 2 + self.luck / 2
            dmg = self.strength - enemy.defence
            critical_probability = self.skill // 2 - enemy.luck
        else:
            print(_("%s attacks %s with %s") % (self.name, enemy.name, self.weapon.name))
            hit_probability = (self.skill * 2) + self.weapon.hit + (self.luck / 2)
            dmg = (self.strength + self.weapon.might) - enemy.defence
            # TODO add damage modifiers like HealthCondition, ElementalAffinity
            critical_probability = self.skill // 2 + self.weapon.crit - enemy.luck

        print("Dmg: %d  Hit: %d" % (dmg, hit_probability))
        hit = random.randrange(0, 100) < hit_probability
        critical = random.randrange(0, 100) < critical_probability

        if not hit:
            print("Misses")
            return 'miss', 0
        elif dmg <= 0:
            print("Null attack")
            return 'null', 0
        elif critical:
            print("Triple attack")
            dmg *= 3
            enemy.inflict_damage(dmg)
            if self.weapon is not None:
                self.weapon.use()
            return 'critical', dmg
        else:
            print(_("%s inflicts %s %d damage points") % (self.name, enemy.name, dmg))
            enemy.inflict_damage(dmg)
            if self.weapon is not None:
                self.weapon.use()
            return 'hit', dmg

    def value(self) -> int:
        """
        the return value is used by ai to choose who enemy attack
        """
        # TODO add type unit influence
        return self.health + self.strength + self.skill + self.speed + self.luck + self.defence

    def prepare_battle(self) -> None:
        self.health_prev = self.health
        self.level_prev = self.level

    def get_damage(self) -> int:
        return self.health_prev - self.health

    def gain_exp(self, enemy: 'Unit') -> None:
        self.exp_prev = self.experience
        exp = 1
        damages = enemy.get_damage()
        if damages > 0:
            lv_diff = abs(enemy.level - self.level)
            if enemy.level < self.level:
                exp += damages // lv_diff
            else:
                exp += damages * lv_diff
            exp += random.randrange(0, self.luck // 2 + 1)
        if enemy.health == 0:
            exp += damages // 2
        if exp > 100:
            exp = 100
        self.experience += exp
        if self.experience >= 100:
            self.experience %= 100
            self.level_up()
        self.modified = True
        print(_("%s gained %d experience points! EXP: %d") % (self.name, exp, self.experience))

    def gained_exp(self) -> int:
        """Return the gained experience with latest battle"""
        if self.experience > self.exp_prev:
            return self.experience - self.exp_prev
        return self.experience + 100 - self.exp_prev

    def level_up(self) -> None:
        self.level_prev = self.level
        self.level += 1
        print(_("%s levelled up!") % self.name)

    def levelled_up(self) -> bool:
        """Returns True if the latest attack caused a level-up"""
        return self.level > self.level_prev

    def is_dead(self) -> bool:
        return self.health == 0

    def was_modified(self) -> bool:
        """Tells whether the unit was modified since last call"""
        m = self.modified
        self.modified = False
        return m

    def move(self, coord) -> None:
        self.modified = True
        self.coord = coord

    def wait(self) -> None:
        self.played = True


class Flying(Unit):
    pass


class Water(Unit):
    pass


class UnitFactory(ABC):
    @staticmethod
    @abstractmethod
    def make_unit() -> Unit:
        raise NotImplementedError("Method not implemented.")


class RandomUnitFactory(UnitFactory):
    @staticmethod
    def make_unit() -> Unit:
        name = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        health = random.randint(5, 70)
        level = health // 4
        experience = 0
        strength = random.randint(1, 20)
        skill = random.randint(1, 20)
        speed = random.randint(1, 20)
        luck = random.randint(1, 20)
        defence = random.randint(1, 20)
        resistance = random.randint(1, 20)
        movement = random.randint(1, 10)
        constitution = random.randint(1, 5)
        aid = random.randint(1, 5)
        affinity = IceAffinity()
        wrank = {k: random.randint(0, 3) for k in ["Lance", "Sword", "Bow", "Axe"]}
        return Unit(name, health, level, experience, strength, skill, speed, luck, defence, resistance, movement,
                    constitution, aid, affinity, wrank, health_max=None)


class Team(object):
    """Every unit is part of a Team."""

    def __init__(self, name: str, color: Tuple[int, int, int], relation: int, units: List[Unit], boss: Unit,
                 music: Dict[str, str]):
        """
        :param name: name of the Team
        :param color: color of the Team
        :param relation: used to represent relationship between teams.
            Two Teams can be allied, neutral or enemy. If the difference
            between the two teams' value is 0 they are allied, if it is
            1 they are neutral otherwise they are enemy.
        :param units: units part of the team
        :param boss: the boss of this team that must be inside the units list
        :param music: Dictionary
        """
        self.name = name
        self.color = color
        self.relation = relation
        for unit in units:
            unit.team = self
        self.units = units
        self.boss = boss
        self.music = music
        self.music_pos = {k: 0 for k, v in music.items()}

    def __str__(self) -> str:
        units = "["
        for unit in self.units:
            units += unit.name + ', '
        return '%s: %s]' % (self.name, units)

    def is_mine(self, unit: Unit) -> bool:
        """Tells wether a unit belongs to this player or not"""
        return unit in self.units

    def is_turn_over(self) -> bool:
        for unit in self.units:
            if not unit.played:
                return False
        return True

    def end_turn(self) -> None:
        for unit in self.units:
            unit.played = True
        print(_("Team %s ends its turn") % self.name)

    def begin_turn(self) -> None:
        for unit in self.units:
            unit.played = False
        print(_("Team %s begins its turn") % self.name)

    def is_defeated(self) -> bool:
        return len(self.units) == 0

    def remove_unit(self, unit: Unit) -> None:
        unit.team = None
        self.units.remove(unit)

    def is_enemy(self, team: 'Team') -> bool:
        return abs(team.relation - self.relation) > 1

    def is_neutral(self, team: 'Team') -> bool:
        return abs(team.relation - self.relation) == 1

    def is_allied(self, team: 'Team') -> bool:
        return team.relation == self.relation

    def is_boss(self, unit: Unit) -> bool:
        return unit == self.boss

    def list_played(self) -> List[Unit]:
        return [u for u in self.units if u.played]

    def play_music(self, music_key: str, resume: bool = False) -> None:
        music_pos = pygame.mixer.music.get_pos() // 1000
        try:
            pygame.mixer.music.load(self.music[music_key])
            # resume and loop indefinitely
            if not resume:
                self.music_pos[music_key] = 0
            pygame.mixer.music.play(-1, self.music_pos[music_key])
            self.music_pos[music_key] += music_pos
        except TypeError:
            logging.warning("No music for team %s.", self.name)
        except KeyError:
            logging.warning("Couldn't find key %s!", music_key)
        except pygame.error:
            logging.warning("Can't play %s", music_key)


class UnitsManager(object):
    def __init__(self, teams: List[Team]) -> None:
        """
        Manage all units in a match.
        :param teams:
        """
        self.teams: List[Team] = teams
        self.active_team: Team = self.teams[0]
        self.units: List[Unit] = [u for t in teams for u in t.units]

    def switch_turn(self) -> Team:
        self.active_team.end_turn()
        active_team_index = (self.teams.index(self.active_team) + 1) % len(self.teams)
        self.active_team = self.teams[active_team_index]
        self.active_team.begin_turn()
        return self.active_team

    def get_units(self, **kwargs) -> List[Unit]:
        found = []
        for unit in self.units:
            for attr in kwargs:
                if getattr(unit, attr) == kwargs[attr]:
                    if unit not in found:
                        found.append(unit)
        return found

    def get_enemies(self, team: Team) -> List[Unit]:
        enemies = []
        for enemy in self.units:
            if enemy not in enemies:
                if enemy.team.is_enemy(team):
                    enemies += enemy.team.units
        return enemies

    @staticmethod
    def are_enemies(unit1: Unit, unit2: Unit) -> bool:
        return unit1.team.is_enemy(unit2.team)

    @staticmethod
    def are_neutrals(unit1: Unit, unit2: Unit) -> bool:
        return unit1.team.is_neutral(unit2.team)

    @staticmethod
    def are_allied(unit1: Unit, unit2: Unit) -> bool:
        return unit1.team.is_allied(unit2.team)

    def kill_unit(self, unit: Unit) -> None:
        self.units.remove(unit)
        unit.team.units.remove(unit)
