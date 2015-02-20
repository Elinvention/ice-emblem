# -*- coding: utf-8 -*-
#
#  Item.py, Ice Emblem's item class.
#
#  Copyright 2015 Elia Argentieri <elia.argentieri@openmailbox.org>
#  Copyright 2015 Luca Argentieri <luca99.argentieri@gmail.com>
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


class Item(object):
	"""Generic item class"""
	def __init__(self, name, Worth, descr=""):
		self.name	=	name
		self.descr	=	descr
		self.Worth	=	int(Worth)  # Price

	def __str__(self):
		return "Item:\r\n\tName: \"%s\"\r\n\tDescription: \"%s\"" % \
			(self.name, self.descr)


class Weapon(Item):
	"""Swords, Lances, Axes, Bows, Tomes, Staffs"""
	def __init__(self, name, rank, might, weight, hit, crit, range,
				uses, worth, exp, effective, descr=""):
		Item.__init__(self, name, worth, descr)
		self.rank   	=	rank    	# rank necessary to use it
		self.might  	=	int(might)	# damage
		self.weight 	=	int(weight)	# weight affects on speed
		self.hit    	=	int(hit)	# probability to hit the enemy
		self.crit   	=	int(crit)	# probability of triple damage
		self.range  	=	int(range)	# attack distance
		self.muses  	=	int(uses)	# max number of uses
		self.uses   	=	int(uses)	# number of remaining uses
		self.exp    	=	int(exp)	# exp increases unit's weapon rank
		self.active 	=	False
		self.effective	=	effective

	def toggle_active(self):
		self.active = not self.active

	def use(self):
		self.uses -= 1
		if self.uses <= 0:
			self.uses = 0
			print("%s is broken" % self.name)
			return 0
		else:
			return self.uses

	def __str__(self):
		return """
Weapon "%s":
	Description: "%s"
	Rank: %c
	Might: %d
	Weight: %d
	Hit: %d
	Crit: %d
	Range: %d
	Uses: %d/%d
	Worth: %d
	Exp: %d
	active: %d
""" % (self.name, self.descr, self.rank, self.might, self.weight,
		self.hit, self.crit, self.range, self.uses, self.muses,
		self.worth, self.exp, self.active)

	def get_might(self, enemy, weak):
		enemy_weapon = enemy.get_active_weapon()

		if not enemy_weapon.active:
			raise ValueError("Enemy weapon is not active")

		if isinstance(enemy_weapon, weak):
			might = self.might + (self.might / 10)
		else:
			might = self.might

		for effect in self.effective:
			if isinstance(effect, enemy):
				might += might / 10

		return might


class Sword(Weapon):
	def __init__(self, name, rank, might, weight, hit, crit, range, uses, worth, exp, effective, descr=""):
		Weapon.__init__(name, rank, might, weight, hit, crit, range, uses, worth, exp, effective, descr="")

	def get_might(self, enemy_weapon):
		return Weapon.get_might(enemy_weapon, Axe)


class Lance(Weapon):
	def __init__(self, name, rank, might, weight, hit, crit, range, uses, worth, exp, effective, descr=""):
		Item.__init__(name, rank, might, weight, hit, crit, range, uses, worth, exp, effective, descr="")

	def get_might(self, enemy_weapon):
		return Weapon.get_might(enemy_weapon, Sword)


class Axe(Weapon):
	def __init__(self, name, rank, might, weight, hit, crit, range, uses, worth, exp, effective, descr=""):
		Item.__init__(name, rank, might, weight, hit, crit, range, uses, worth, exp, effective, descr="")

	def get_might(self, enemy_weapon):
		return Weapon.get_might(enemy_weapon, Lance)


class Bow(Weapon):
	def __init__(self, name, rank, might, weight, hit, crit, range, uses, worth, exp, effective, descr=""):
		Item.__init__(name, rank, might, weight, hit, crit, range, uses, worth, exp, effective, descr="")

	def get_might(self, enemy):
		might = self.might
		for effect in self.effective:
			if isinstance(effect, enemy):
				might += self.might / 10

		return might


class LightTome(Weapon):
	def __init__(self, name, rank, might, weight, hit, crit, range, uses, worth, exp, effective, descr=""):
		Item.__init__(name, rank, might, weight, hit, crit, range, uses, worth, exp, effective, descr="")

	def get_might(self, enemy_weapon):
		return Weapon.get_might(enemy_weapon, DarkTome)


class DarkTome(Weapon):
	def __init__(self, name, rank, might, weight, hit, crit, range, uses, worth, exp, effective, descr=""):
		Item.__init__(name, rank, might, weight, hit, crit, range, uses, worth, exp, effective, descr="")

	def get_might(self, enemy_weapon):
		return Weapon.get_might(enemy_weapon, AnimaTome)


class AnimaTome(Weapon):
	def __init__(self, name, rank, might, weight, hit, crit, range, uses, worth, exp, effective, descr=""):
		Item.__init__(name, rank, might, weight, hit, crit, range, uses, worth, exp, effective, descr="")

	def get_might(self, enemy_weapon):
		return Weapon.get_might(enemy_weapon, LightTome)


class Staff(Item):
	def __init__(self, name, rank, range, uses, worth, exp, descr=""):
		Item.__init__(name, rank, range, uses, worth, exp, descr="")
		self.rank	=	rank    	# rank necessary to use it
		self.range	=	int(range)	# attack distance
		self.muses	=	int(uses)	# max number of uses
		self.uses	=	int(uses)	# number of remaining uses
		self.exp	=	int(exp)	# exp increases unit's weapon rank
		self.active	=	False


class Armour(Item):
	def __init__(self, name, rank, defence, weight, uses, worth, exp, effective, descr=""):
		Item.__init__(self, name, worth, descr)
		self.rank   	=	rank    	# rank necessary to use it
		self.defence	=	int(defence)# damage
		self.weight 	=	int(weight)	# weight affects on speed
		self.muses  	=	int(uses)	# max number of uses
		self.uses   	=	int(uses)	# number of remaining uses
		self.exp    	=	int(exp)	# exp increases unit's weapon rank
		self.active 	=	False
		self.effective	=	effective

	def toggle_active(self):
		self.active = not self.active

	def use(self):
		self.uses -= 1
		if self.uses <= 0:
			self.uses = 0
			print("%s is broken" % self.name)
			return 0
		else:
			return self.uses

	def __str__(self):
		return """
Armour "%s":
	Description: "%s"
	Rank: %c
	Defence: %d
	Weight: %d
	Uses: %d/%d
	Worth: %d
	Exp: %d
	active: %d
""" % (self.name, self.descr, self.rank, self.defence, self.weight,
		self.uses, self.muses, self.worth, self.exp, self.active)
