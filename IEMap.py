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


def distance(p0, p1):
    return abs(p0[0] - p1[0]) + abs(p0[1] - p1[1])


class IEMapNode(object):
	"""Node"""
	GRASS = (32, 672)
	DIRT = (32, 832)
	CASTLE1 = (32, 545)
	CASTLE2 = (192, 545)
	CASTLE3 = (130, 545)
	WATER = (32, 160)
	
	def __init__(self, (tile_x, tile_y)=DIRT, unit=None, walkable=True, Def_bonus=0):
		self.walkable = walkable
		self.unit = unit
		self.tile = (tile_x, tile_y)
		self.Def_bonus = Def_bonus


class IEMap(object):
	"""The map is composed of nodes."""
	def __init__(self, (w, h), (screen_w, screen_h)):
		self.w = w
		self.h = h
		self.nodes = [[IEMapNode() for i in range(h)] for j in range(w)]
		self.tile_size = min(screen_w / w, screen_h / h)
		self.square = (self.tile_size, self.tile_size)

	def position_unit(self, unit, (x, y)):
		"""Set an unit to the coordinates."""
		self.nodes[x][y].unit = unit

	def screen_resize(self, (screen_w, screen_h)):
		self.tile_size = min(screen_w / self.w, screen_h / self.h)
		self.square = (self.tile_size, self.tile_size)

	def mouse2cell(self, (cursor_x, cursor_y)):
		"""mouse position to map indexes."""
		x = cursor_x / self.tile_size
		y = cursor_y / self.tile_size
		if x >= self.w or y >= self.h:
			raise ValueError('%d >= %d or %d >= %d' % (x, self.w, y, self.h))
		return (x, y)

	def where_is(self, unit):
		for i in range(self.w):
			for j in range(self.h):
				if self.nodes[i][j].unit == unit:
					return (i, j)
		return None

	def move(self, (old_x, old_y), (x, y)):
		if (old_x, old_y) != (x, y):
			self.nodes[x][y].unit = self.nodes[old_x][old_y].unit
			self.nodes[old_x][old_y].unit = None

	def is_played(self, (x, y)):
		if self.nodes[x][y].unit is None:
			return None
		else:
			return self.nodes[x][y].unit.played

	def remove_unit(self, unit):
		x, y = coord = self.where_is(unit)
		if coord is not None:
			self.nodes[x][y].unit = None
			return True
		else:
			return False

	def list_move_area(self, (x, y), Move):
		move_area = []
		for px in range(x - Move, x + Move + 1):
			for py in range(y - Move, y + Move + 1):
				try:
					if self.nodes[px][py].unit is None:
						x_distance = abs(px - x)
						y_distance = abs(py - y)
						y_limit = Move - x_distance
						x_limit = Move - y_distance
						if self.nodes[px][py].walkable and x_distance <= x_limit and y_distance <= y_limit:
							move_area.append((px, py))
				except IndexError:
					pass
		return move_area

	def list_attack_area(self, (x, y), Move, weapon_range=1):
		attack_area = []
		for px in range(x - Move - weapon_range, x + Move + weapon_range + 1):
			for py in range(y - Move - weapon_range, y + Move + weapon_range + 1):
				x_distance = abs(px - x)
				y_distance = abs(py - y)
				y_limit_max = Move + weapon_range - x_distance
				x_limit_max = Move + weapon_range - y_distance
				y_limit_min = Move + 1 - x_distance
				x_limit_min = Move + 1 - y_distance
				try:
					if (x_distance <= x_limit_max and
						y_distance <= y_limit_max and
						x_distance >= x_limit_min and
						y_distance >= y_limit_min):
						attack_area.append((px, py))
					elif self.nodes[px][py].unit is not None and x_distance < x_limit_min and y_distance < y_limit_min:
						attack_area.append((px, py))
				except IndexError:
					pass
		return attack_area

	def number_of_nearby_units(self, (x, y), unit_range):
		counter = 0
		for i in range(x - unit_range, x + unit_range + 1):
			for j in range(y - unit_range, y + unit_range + 1):
				if (x, y) != (i, j) and distance((x, y), (i, j)) <= unit_range:
					try:
						if self.nodes[i][j].unit is not None:
							counter += 1
					except IndexError:
						pass
		return counter

	def list_nearby_units(self, (x, y), unit_range):
		_list = []
		for i in range(x - unit_range, x + unit_range + 1):
			for j in range(y - unit_range, y + unit_range + 1):
				if (x, y) != (i, j) and distance((x, y), (i, j)) <= unit_range:
					try:
						if self.nodes[i][j].unit is not None:
							_list.append((i, j))
					except IndexError:
						pass
		return _list

	def path(self, (ax, ay), (bx, by)):
		"""
		We need to implement a basic Dijkstra's algorithm
		https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm
		to find the shortest path from a to b
		"""
