# -*- coding: utf-8 -*-
#
#  IEUnit.py, Ice Emblem's unit class.
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
import os.path
import random


class IEUnit(object):
	"""
	This class is a unit with stats
	"""
	def __init__(self, name, HP_max, HP, LV, E, Str, Skill, Spd, Luck, Def, Res, Move, Con, Aid, Trv, Affin, Cond, WRank):
		self.name	=	str(name)   	# name of the character
		self.HP_max	=	int(HP_max) 	# Maximum HP
		self.HP 	=	int(HP)     	# Current HP
		self.LV 	=	int(LV)     	# Level
		self.E  	=	int(E)      	# Experience
		self.Str	=	int(Str)    	# Strength determines the damage inflicted to the enemy
		self.Skill	=	int(Skill)  	# Skill chance of hitting the enemy
		self.Spd	=	int(Spd)    	# Speed chance to avoid enemy's attack
		self.Luck	=	int(Luck)   	# Luck influences many things
		self.Def	=	int(Def)    	# Defence reduces phisical damages
		self.Res	=	int(Res)    	# Resistence reduces magical damages
		self.Move	=	int(Move)   	# Movement determines how far the unit can move in a turn
		self.Con	=	int(Con)    	# Constitution, or phisical size. Affects rescues.
		self.Aid	=	int(Aid)    	# Max rescuing constitution. Units with lower Con can be rescued.
		self.Trv	=	Trv         	# Traveler. The unit with whom this unit is traveling.
		self.Affin	=	Affin       	# Elemental Affinity. Determines compatibility with other units.
		self.Cond	=	Cond        	# Health conditions.
		self.WRank	=	WRank       	# Weapons' Levels.
		self.Items	=	[]          	# List of items
		self.played	=	False       	# Wether unit was used or not in a turn
		path = os.path.abspath('sprites/' + self.name + '.png')
		try:
			self.image = pygame.image.load(path).convert_alpha()
		except pygame.error, e:
			print("Couldn't load " + path)
			print(e)
			self.image = None

	def __str__(self):
		return """
Unit: "%s"
	HP: %d/%d
	LV: %d E: %d
	Str: %d	Skill: %d
	Spd: %d	Luck: %d
	Def: %d	Res: %d
	Move: %d	Con: %d
	Aid: %d	Trv: %s
	Affin: %s	Cond: %s
	WRank: %s
	Items: %s
	Played: %s
""" % (self.name,
			self.HP, self.HP_max, self.LV, self.E, self.Str,
			self.Skill, self.Spd, self.Luck, self.Def,
			self.Res, self.Move, self.Con, self.Aid, self.Trv,
			self.Affin, self.Cond, self.WRank, self.Items, self.played)

	def get_active_weapon(self):
		"""Returns the active weapon if it exists, None otherwise."""
		for item in self.Items:
			if item.active:
				return item
		return None

	def give_weapon(self, weapon, active=True):
		"""Gives a weapon to the unit. The weapon becomes active by default."""
		weapon.active = active
		self.Items.append(weapon)

	def inflict_damage(self, dmg):
		"""Inflicts damages to the unit."""
		self.HP -= dmg
		if self.HP <= 0:
			self.HP = 0
			print("%s died" % self.name)

	def attack_turns(self, enemy):
		self_turns = enemy_turns = 1
		if self.Spd > enemy.Spd:
			self_turns += 1
		elif enemy.Spd > self.Spd:
			enemy_turns += 1
		return (self_turns, enemy_turns)

	def get_range(self):
		active_weapon = self.get_active_weapon()
		return active_weapon.Range if active_weapon is not None else 1

	def number_of_attacks(self, enemy):
		self_attacks = enemy_attacks = 1

		if self.Spd > enemy.Spd:
			self_attacks += 1
		elif enemy.Spd > self.Spd:
			enemy_attacks += 1

		return (self_attacks, enemy_attacks)

	def life_percent(self):
		return int(float(self.HP) / float(self.HP_max) * 100.0)

	def attack(self, enemy):
		"""
		This unit attacks another.
		0 -> miss
		1 -> hit
		2 -> broken weapon
		"""

		active_weapon = self.get_active_weapon()

		if active_weapon is None or active_weapon.Uses == 0:
			dmg = self.Str
			hit = self.Skill * 2 + self.Luck / 2
			print("%s attacks %s" % (self.name, enemy.name))
			print("Dmg: %d  Hit: %d" % (dmg, hit))
			if random.randrange(0, 100) > hit:
				print("%s misses %s" % (self.name, enemy.name))
				ret = 0
			else:
				print("%s inflicts %s %d damages" % (self.name, enemy.name, dmg))
				enemy.inflict_damage(dmg)
				ret = 1
		else:
			dmg = self.Str + active_weapon.Might  # TODO
			hit = (self.Skill * 2) + active_weapon.Hit + (self.Luck / 2)
			print("%s attacks %s using %s" % (self.name, enemy.name, active_weapon.name))
			print("Dmg: %d  Hit: %d" % (dmg, hit))
			if random.randrange(0, 100) > hit:
				print("%s misses %s" % (self.name, enemy.name))
				ret = 0
			else:
				print("%s inflicts %s %d damages" % (self.name, enemy.name, dmg))
				enemy.inflict_damage(dmg)
				if active_weapon.use() == 0:
					ret = 2
				else:
					ret = 1
		return ret

class IEPlayer(object):
	"""This class represents the player status and which units belong to."""

	number_of_players = 0
	
	def __init__(self, name, color, my_turn=False, units=[]):
		self.number_of_players += 1
		self.name = name
		self.units = units
		self.color = color
		self.my_turn = my_turn

	def is_mine(self, unit):
		"""Tells wether a unit belongs to this player or not"""
		return unit in self.units

	def is_turn_over(self):
		for unit in self.units:
			if not unit.played:
				return False
		return True

	def end_turn(self):
		for unit in self.units:
			unit.played = False
		self.my_turn = False
		print("Player %s ends its turn" % self.name)

	def begin_turn(self):
		self.my_turn = True
		for unit in self.units:
			unit.played = False
		print("Player %s begins its turn" % self.name)

	def is_defeated(self):
		return True if len(self.units) == 0 else False
