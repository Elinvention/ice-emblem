# -*- coding: utf-8 -*-
#
#  IEMap.py, Ice Emblem's map class.
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

import pygame, time # temporary


class IEMapNode(object):
	"""Node"""
	def __init__(self, unit=None, walkable=True):
		self.walkable = walkable
		self.unit = unit


class IEMap(object):
	"""The map is composed of nodes."""
	def __init__(self, (w, h), (screen_w, screen_h)):
		self.w = w
		self.h = h
		self.matrix = [[IEMapNode() for i in range(h)] for j in range(w)]
		self.selection = None
		self.move_range = []
		self.attack_range = []
		square_x = screen_w / w
		square_y = screen_h / h
		self.square = min(square_x, square_y)

	def position_unit(self, unit, (x, y)):
		"""Set an unit to the coordinates."""
		try:
			self.matrix[x][y].unit = unit
		except IndexError:
			return False
		else:
			return True

	def screen_resize(self, (screen_w, screen_h)):
		square_x = screen_w / self.w
		square_y = screen_h / self.h
		self.square = min(square_x, square_y)

	def mouse2cell(self, (cursor_x, cursor_y)):
		"""mouse position to matrix indexes."""
		x = cursor_x / self.square
		y = cursor_y / self.square
		if x >= self.w or y >= self.h:
			return (None, None)
		else:
			return (x, y)

	def where_is(self, unit):
		for i in range(self.w):
			for j in range(self.h):
				if self.matrix[i][j].unit == unit:
					return (i, j)
		return None

	def move(self, unit, (x, y)):
		(old_x, old_y) = self.where_is(unit)
		self.matrix[old_x][old_y].unit = None
		self.matrix[x][y].unit = unit

	def list_move_range(self, (x, y), Move):
		for px in range(x - Move, x + Move + 1):
			for py in range(y - Move, y + Move + 1):
				try:
					if self.matrix[px][py].unit is None:
						x_distance = abs(px - x)
						y_distance = abs(py - y)
						y_limit = Move - x_distance
						x_limit = Move - y_distance
						if self.matrix[px][py].walkable and x_distance <= x_limit and y_distance <= y_limit:
							self.move_range.append((px, py))
				except IndexError:
					pass

	def list_attack_range(self, (x, y), Move, weapon_range=1):
		for px in range(x - Move - weapon_range, x + Move + weapon_range + 1):
			for py in range(y - Move - weapon_range, y + Move + weapon_range + 1):
				x_distance = abs(px - x)
				y_distance = abs(py - y)
				y_limit_max = Move + weapon_range - x_distance
				x_limit_max = Move + weapon_range - y_distance
				y_limit_min = Move + 1 - x_distance
				x_limit_min = Move + 1 - y_distance
				try:
					if (self.matrix[px][py].walkable and
						x_distance <= x_limit_max and
						y_distance <= y_limit_max and
						x_distance >= x_limit_min and
						y_distance >= y_limit_min):
						self.attack_range.append((px, py))
				except IndexError:
					pass

	def select(self, (pointer_x, pointer_y)):
		"""set selected."""

		x, y = self.mouse2cell((pointer_x, pointer_y))

		if x is None or y is None:
			return

		if self.selection is None:
			unit = self.matrix[x][y].unit
			self.selection = (x, y)
			if unit is None or unit.played:
				self.move_range = []
				self.attack_range = []
			else:
				self.list_move_range((x, y), unit.Move)
				self.list_attack_range((x, y), unit.Move, unit.get_active_weapon().Range)
		else:
			sx, sy = self.selection
			prev_unit = self.matrix[sx][sy].unit
			curr_unit = self.matrix[x][y].unit
			
			if (x, y) == self.selection:
				self.selection = None
				self.move_range = []
				self.attack_range = []
			elif prev_unit is not None and not prev_unit.played and self.is_in_move_range((x, y)):
				self.move(prev_unit, (x, y))
				self.selection = None
				self.move_range = []
				self.attack_range = []
				#prev_unit.played = True
			elif prev_unit is not None and not prev_unit.played and curr_unit is not None and self.is_in_attack_range((x, y)):
				print("Attack!!!")
				pygame.mixer.Sound('music/The Last Encounter Short Loop.ogg').play(-1)
				# battle()
				time.sleep(40)
				pygame.mixer.fadeout(2000)
				time.sleep(2)
			else:
				self.selection = (x, y)
				self.move_range = []
				self.attack_range = []
				if curr_unit is not None and not curr_unit.played:
					self.list_move_range((x, y), curr_unit.Move)
					self.list_attack_range((x, y), curr_unit.Move, curr_unit.get_active_weapon().Range)

	def is_in_move_range(self, (x, y)):
		return (x, y) in self.move_range

	def is_in_attack_range(self, (x, y)):
		return (x, y) in self.attack_range

	def is_selected(self, (x, y)):
		return (self.selection == (x, y))

	def is_played(self, (x, y)):
		if self.matrix[x][y].unit is None:
			return False
		else:
			return self.matrix[x][y].unit.played
