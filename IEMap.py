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


import pytmx
import pygame
#import pyscroll

def distance(p0, p1):
	return abs(p0[0] - p1[0]) + abs(p0[1] - p1[1])


class IEMapNode(object):
	"""Node"""

	def __init__(self, tile, unit=None, walkable=True, Def_bonus=0):
		self.tile = tile
		self.unit = unit
		self.walkable = walkable
		self.Def_bonus = Def_bonus


class IEMap(object):
	"""The map is composed of nodes."""
	def __init__(self, map_path, (screen_w, screen_h), units, players):
		tmx_data = pytmx.load_pygame(map_path)
		#map_data = pyscroll.data.TiledMapData(tmx_data)
		#self.map_layer = pyscroll.BufferedRenderer(map_data, (screen_w, screen_h))
		self.h = tmx_data.height
		self.w = tmx_data.width
		self.tile_size = min(screen_w / self.w, screen_h / self.h)
		self.square = (self.tile_size, self.tile_size)
		self.players = players
		self.nodes = [[] for x in range(self.w)]
		for layer in tmx_data.visible_layers:
			if isinstance(layer, pytmx.TiledTileLayer):
				# iterate over the tiles in the layer
				for x, y, image in layer.tiles():
					try:  # if there are more layers fuse them togheter
						tile = self.nodes[x][y].tile.convert_alpha()
						tile.blit(image, (0,0))
						self.nodes[x][y].tile = tile
					except IndexError:
						#print('IndexError %d:%d' % (x, y))
						node = IEMapNode(image)
						self.nodes[x].append(node)

		for layer in tmx_data.visible_layers:
			if isinstance(layer, pytmx.TiledObjectGroup):
				for obj in layer:
					if obj.type == 'unit':
						x = int(obj.x / tmx_data.tilewidth)
						y = int(obj.y / tmx_data.tileheight)
						self.nodes[x][y].unit = units[obj.name]

		self.background_color = tmx_data.background_color

	def whose_unit(self, unit):
		for player in self.players:
			for player_unit in player.units:
				if player_unit == unit:
					return player
		return None

	def render(self, (screen_w, screen_h)):
		"""Renders the map returning a Surface"""

		map_w = self.tile_size * self.w
		map_h = self.tile_size * self.h
		side = self.tile_size

		rendering = pygame.Surface((map_w, map_h))

		if self.background_color:
			rendering.fill(pygame.Color(self.background_color))

		# deref these heavily used references for speed
		smoothscale = pygame.transform.smoothscale

		for i in range(self.w):
			for j in range(self.h):
				tile = self.nodes[i][j].tile
				tile = smoothscale(tile, self.square)
				rendering.blit(tile, (i * self.tile_size, j * self.tile_size))

				node = self.nodes[i][j]
				unit = node.unit
				if unit is not None:
					#rect = pygame.Rect((i * side, j * side), (side, side)) # color
					#pygame.draw.rect(rendering, self.whose_unit(unit).color, rect, 1)
					pos = (i * side + side / 2, j * side + side / 2)
					pygame.draw.circle(rendering, self.whose_unit(unit).color, pos, side / 2, 5)

					if unit.image is None:
						scritta = self.SMALL_FONT.render(unit.name, 1, BLACK)
						rendering.blit(scritta, (i * side, j * side))
					else:
						image_w, image_h = unit.image.get_size()
						if (image_w, image_h) != (side, side - 5):
							if image_w > image_h:
								aspect_ratio = float(image_h) / float(image_w)
								resized_w = side
								resized_h = int(aspect_ratio * resized_w)
							else:
								aspect_ratio = float(image_w) / float(image_h)
								resized_h = side - 5
								resized_w = int(aspect_ratio * resized_h)
							image = pygame.transform.smoothscale(unit.image, (resized_w, resized_h))
						else:
							image = unit.image
						rendering.blit(image, (i * side + side / 2 - image.get_size()[0] / 2, j * side))

					HP_bar_length = int((float(unit.HP) / float(unit.HP_max)) * float(side))
					HP_bar = pygame.Surface((HP_bar_length, 5))
					HP_bar.fill((0, 255, 0))
					rendering.blit(HP_bar, (i * side, j * side + side - 5)) # HP bar

		horizontal_line = pygame.Surface((map_w, 2)).convert_alpha()
		horizontal_line.fill((0, 0, 0, 100))
		vertical_line = pygame.Surface((2, map_h)).convert_alpha()
		vertical_line.fill((0, 0, 0, 100))

		for i in range(self.w):
			rendering.blit(vertical_line, (i * self.tile_size - 1, 0))
		for j in range(self.h):
			rendering.blit(horizontal_line, (0, j * self.tile_size - 1))
		return rendering

	def position_unit(self, unit, (x, y)):
		"""Set an unit to the coordinates."""
		self.nodes[x][y].unit = unit

	def screen_resize(self, (screen_w, screen_h)):
		self.tile_size = min(screen_w / self.w, screen_h / self.h)
		self.square = (self.tile_size, self.tile_size)

	def mouse2cell(self, (cursor_x, cursor_y)):
		"""mouse position to map indexes."""
		x = int(cursor_x / self.tile_size)
		y = int(cursor_y / self.tile_size)
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
			print('Unit %s moved from %d:%d to %d:%d' % (self.nodes[old_x][old_y].unit.name, old_x, old_y, x, y))
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
