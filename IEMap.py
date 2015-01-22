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


from pygame import Surface


class IEMapNode(object):
	"""Node"""
	def __init__(self, (tile_x, tile_y)=(32, 832), unit=None, walkable=True):
		self.walkable = walkable
		self.unit = unit
		self.tile = (tile_x, tile_y)


class IEMap(object):
	"""The map is composed of nodes."""
	def __init__(self, (w, h), (screen_w, screen_h),
			selected_node_color, unit_move_range_color,
				unit_attack_range_color, unit_played_color, players):
		self.w = w
		self.h = h
		self.map = [[IEMapNode() for i in range(h)] for j in range(w)]
		self.selection = None
		self.move_range = []
		self.attack_range = []
		square_x = screen_w / w
		square_y = screen_h / h
		self.tile_size = min(square_x, square_y)
		self.square = (self.tile_size, self.tile_size)
		
		self.selected_node_color = selected_node_color
		self.selected_node_background = Surface(self.square).convert_alpha()
		self.selected_node_background.fill(selected_node_color)
		
		self.unit_move_range_color = unit_move_range_color
		self.unit_move_range_background = Surface(self.square).convert_alpha()
		self.unit_move_range_background.fill(unit_move_range_color)

		self.unit_attack_range_color = unit_attack_range_color
		self.unit_attack_range_backgroud = Surface(self.square).convert_alpha()
		self.unit_attack_range_backgroud.fill(unit_attack_range_color)

		self.unit_played_color = unit_played_color
		self.unit_played_backgroud = Surface(self.square).convert_alpha()
		self.unit_played_backgroud.fill(unit_played_color)

		self.players = players

	def position_unit(self, unit, (x, y)):
		"""Set an unit to the coordinates."""
		try:
			self.map[x][y].unit = unit
		except IndexError:
			return False
		else:
			return True

	def screen_resize(self, (screen_w, screen_h)):
		square_x = screen_w / self.w
		square_y = screen_h / self.h
		self.tile_size = min(square_x, square_y)
		self.square = (self.tile_size, self.tile_size)

		self.selected_node_background = Surface(self.square).convert_alpha()
		self.selected_node_background.fill(self.selected_node_color)

		self.unit_move_range_background = Surface(self.square).convert_alpha()
		self.unit_move_range_background.fill(self.unit_move_range_color)

		self.unit_attack_range_backgroud = Surface(self.square).convert_alpha()
		self.unit_attack_range_backgroud.fill(self.unit_attack_range_color)

		self.unit_played_backgroud = Surface(self.square).convert_alpha()
		self.unit_played_backgroud.fill(self.unit_played_color)
		

	def mouse2cell(self, (cursor_x, cursor_y)):
		"""mouse position to map indexes."""
		x = cursor_x / self.tile_size
		y = cursor_y / self.tile_size
		if x >= self.w or y >= self.h:
			return (None, None)
		else:
			return (x, y)

	def where_is(self, unit):
		for i in range(self.w):
			for j in range(self.h):
				if self.map[i][j].unit == unit:
					return (i, j)
		return None

	def move(self, unit, (x, y)):
		(old_x, old_y) = self.where_is(unit)
		self.map[old_x][old_y].unit = None
		self.map[x][y].unit = unit

	def list_move_range(self, (x, y), Move):
		for px in range(x - Move, x + Move + 1):
			for py in range(y - Move, y + Move + 1):
				try:
					if self.map[px][py].unit is None:
						x_distance = abs(px - x)
						y_distance = abs(py - y)
						y_limit = Move - x_distance
						x_limit = Move - y_distance
						if self.map[px][py].walkable and x_distance <= x_limit and y_distance <= y_limit:
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
					if (x_distance <= x_limit_max and
						y_distance <= y_limit_max and
						x_distance >= x_limit_min and
						y_distance >= y_limit_min):
						self.attack_range.append((px, py))
					elif self.map[px][py].unit is not None and x_distance < x_limit_min and y_distance < y_limit_min:
						self.attack_range.append((px, py))
				except IndexError:
					pass

	def select(self, (x, y)):
		"""set selected."""
		active_player = self.get_active_player()
		
		if self.selection is None:
			unit = self.map[x][y].unit
			self.selection = (x, y)
			if unit is None or unit.played:
				self.move_range = []
				self.attack_range = []
			else:
				self.list_move_range((x, y), unit.Move)
				self.list_attack_range((x, y), unit.Move, unit.get_active_weapon().Range)
		else:
			sx, sy = self.selection
			prev_unit = self.map[sx][sy].unit
			curr_unit = self.map[x][y].unit
			
			if (x, y) == self.selection:
				self.selection = None
				self.move_range = []
				self.attack_range = []
			elif prev_unit is not None and not prev_unit.played and active_player.is_mine(prev_unit) and self.is_in_move_range((x, y)):
				self.move(prev_unit, (x, y))
				self.selection = None
				self.move_range = []
				self.attack_range = []
				prev_unit.played = True
			elif prev_unit is not None and not prev_unit.played and active_player.is_mine(prev_unit) and curr_unit is not None and not active_player.is_mine(curr_unit) and self.is_in_attack_range((x, y)):
				return 1
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
		if self.map[x][y].unit is None:
			return False
		else:
			return self.map[x][y].unit.played

	def get_active_player(self):
		for player in self.players:
			if player.my_turn:
				return player
		return None

	def whose_unit(self, unit):
		for player in self.players:
			for player_unit in player.units:
				if player_unit == unit:
					return player
		return None

	def whose_turn(self):
		for player in self.players:
			if player.my_turn:
				return player
		return None
