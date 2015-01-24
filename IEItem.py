# -*- coding: utf-8 -*-
#
#  IEItem.py, Ice Emblem's item class.
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


class IEItem(object):
	"""Generic item class"""
	def __init__(self, name, descr=""):
		self.name = name
		self.descr = descr

	def __str__(self):
		return "Item:\r\n\tName: \"%s\"\r\n\tDescription: \"%s\"" % (self.name, self.descr)


class IEWeapon(IEItem):
	"""Swords, Lances, Axes, Bows, Tomes, Staffs"""
	def __init__(self, name, Rank, Might, Weight, Hit, Crit, Range, Uses, Worth, Exp, descr=""):
		self.name = name
		self.descr = descr
		self.Rank	=	Rank
		self.Might	=	Might
		self.Weight	=	Weight
		self.Hit	=	Hit
		self.Crit	=	Crit
		self.Range	=	Range
		self.MUses	=	Uses
		self.Uses	=	Uses
		self.Worth	=	Worth
		self.Exp	=	Exp
		self.active	=	False

	def toggleActive(self):
		self.active = not self.active

	def use(self):
		self.Uses -= 1
		if self.Uses <= 0:
			self.Uses = 0
			print("%s is broken" % self.name)
			return 0
		else:
			return self.Uses

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
""" % (self.name, self.descr, self.Rank, self.Might, self.Weight, self.Hit, self.Crit, self.Range, self.Uses, self.MUses, self.Worth, self.Exp, self.active)

# class ie_sword (ie_weapon):
# 	pass
