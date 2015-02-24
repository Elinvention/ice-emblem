# -*- coding: utf-8 -*-
#
#  Map.py, Ice Emblem's map class.
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


import tmx
import pygame


def distance(p0, p1):
	return abs(p0[0] - p1[0]) + abs(p0[1] - p1[1])


class MapNode(object):
	"""Node"""

	def __init__(self, coord, tile, unit=None, weight=1, bonus_defence=0):
		self.x, self.y = coord
		self.tile = tile
		self.unit = unit
		self.weight = 1
		self.bonus_defence = bonus_defence

	def __str__(self):
		return ("<MapNode (%d:%d) %s %d %d>" %
				(self.x, self.y,
				self.unit.name if self.unit is not None else 'None',
				self.weight, self.bonus_defence))

	def is_obstacle(self, color=None):
		if color is not None:
			return (self.weight == float('inf') or
				(self.unit is not None and self.unit.color != color))
		else:
			return self.weight == float('inf') or self.unit is not None

	def get_unit_color(self):
		return self.unit.color if self.unit is not None else None


class Map(object):
	"""The map is composed of nodes."""
	def __init__(self, map_path, screen_size, highlight_colors, units):
		(screen_w, screen_h) = screen_size
		tmx_data = tmx.load(map_path, screen_size)
		self.h = tmx_data.height
		self.w = tmx_data.width
		self.tile_size = min(screen_w // self.w, screen_h // self.h)
		self.square = (self.tile_size, self.tile_size)

		# this part is a hacky way to reuse this class to render the map
		# instead of built in tmx.py method. Probabily something con be
		# done to reduce code duplication and memory
		self.nodes = [[] for _ in range(self.w)]

		for layer in tmx_data.layers:
			if layer.visible and isinstance(layer, tmx.Layer):
				# iterate over the tiles in the layer
				for cell in layer:
					if cell is not None:
						x, y = (cell.x, cell.y)
						image = cell.tile.surface
						try:  # if there are more layers fuse them togheter
							tile = self.nodes[x][y].tile.convert_alpha()
							tile.blit(image, (0,0))
							self.nodes[x][y].tile = tile
						except IndexError:
							node = MapNode((x, y), image)
							self.nodes[x].append(node)

		for layer in tmx_data.layers:
			if layer.visible and isinstance(layer, tmx.ObjectLayer):
				for obj in layer.objects:
					if obj.type == 'unit':
						x = obj.px // tmx_data.tile_width
						y = obj.py // tmx_data.tile_height
						self[x, y].unit = units[obj.name]

		self.prev_sel = None
		self.curr_sel = None
		self.move_area = []
		self.attack_area = []
		self.arrow = []
		self.arrow_image = pygame.Surface((20, 20)).convert()
		self.arrow_image.fill((255, 0, 0))  # TODO: should be an image not a filled square

		self.highlight_colors = highlight_colors
		self.highlight_surfaces = {}
		for highlight, color in self.highlight_colors.items():
			self.highlight_surfaces[highlight] = pygame.Surface(self.square).convert_alpha()
			self.highlight_surfaces[highlight].fill(color)

	def __getitem__(self, pos):
		(x, y) = pos
		return self.nodes[x][y]

	def dijkstra(self, source):
		"""
		Implementation of Dijkstra's Algorithm.
		See https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm for
		reference.
		This method computes the distance of every node of the map from
		a given source node.
		You can then feed the shortest_path method with this method's
		return value to find the shortest path from any node to the
		source node.
		"""
		dist = [[None for _ in range(self.h)] for _ in range(self.w)]
		prev = [[None for _ in range(self.h)] for _ in range(self.w)]
		sx, sy = source
		dist[sx][sy] = 0     # Distance from source to source
		prev[sx][sy] = None  # Previous node in optimal path initialization

		Q = []
		for i in range(self.w):  # Initialization
			for j in range(self.h):
				if (i, j) != source:  # Where v has not yet been removed from Q (unvisited nodes)
					dist[i][j] = float('inf')  # Unknown distance function from source to v
					prev[i][j] = None  # Previous node in optimal path from source
				Q.append((i, j))  # All nodes initially in Q (unvisited nodes)

		source_node = self.get_node(source)
		while Q:
			u0, u1 = Q[0]
			min_dist = dist[u0][u1]
			u = (u0, u1)

			for el in Q:
				i, j = el
				if dist[i][j] < min_dist:
					min_dist = dist[i][j]
					u0, u1 = u = el  #  Source node in first case

			Q.remove(u)  

			# where v has not yet been removed from Q.
			for v in self.neighbors(u):
				v0, v1 = v
				node = self.get_node(v)

				source_unit_color = source_node.get_unit_color()

				if node.is_obstacle(source_unit_color):
					dist[v0][v1] = float('inf')
					prev[v0][v1] = None
				else:
					alt = dist[u0][u1] + node.weight

					# A shorter path to v has been found
					if alt < dist[v0][v1]:  
						dist[v0][v1] = alt
						prev[v0][v1] = u

		return dist, prev

	def check_coord(self, coord):
		x, y = coord
		if 0 <= x < self.w and 0 <= y < self.h:
			return True
		else:
			return False

	def neighbors(self, coord):
		"""
		Returns a list containing all existing neighbors of a node.
		coord must be a valid coordinate i.e. self.check_coord(coord).
		"""
		x, y = coord

		if not self.check_coord(coord):
			raise ValueError("Invalid coordinates")

		n = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
		ret = [tuple(y for y in x) for x in n if self.check_coord(x)]

		return ret

	def shortest_path(self, prev, target):
		"""
		This method wants the second list returned by the dijkstra
		method and a target node. The shortest path between target and
		source previously specified when calling the dijkstra method
		will be returned as a list.
		"""
		S = []
		u0, u1 = u = target

		# Construct the shortest path with a stack S
		while prev[u0][u1] is not None:
			S.insert(0, u)  # Push the vertex onto the stack
			u0, u1 = u = prev[u0][u1]  # Traverse from target to source

		return S

	def render(self, screen_size, font):
		"""Renders the map returning a Surface"""

		(screen_w, screen_h) = screen_size

		map_w = self.tile_size * self.w
		map_h = self.tile_size * self.h
		side = self.tile_size

		rendering = pygame.Surface((map_w, map_h))

		# deref these heavily used references for speed
		smoothscale = pygame.transform.smoothscale
		circle = pygame.draw.circle
		blit = rendering.blit

		for i in range(self.w):
			for j in range(self.h):
				node = self.get_node(i, j)
				tile = smoothscale(node.tile, self.square)
				blit(tile, (i * self.tile_size, j * self.tile_size))
				unit = node.unit

				if unit is not None and unit.color is not None:
					pos = (i * side + side // 2, j * side + side // 2)
					circle(rendering, unit.color, pos, side // 2, 5)

					if unit.image is None:
						text = font.render(unit.name, 1, BLACK)
						blit(text, (i * side, j * side))
					else:
						image_w, image_h = unit.image.get_size()
						if (image_w, image_h) != (side, side - 5):
							if image_w > image_h:
								aspect_ratio = float(image_h / image_w)
								resized_w = side
								resized_h = int(aspect_ratio * resized_w)
							else:
								aspect_ratio = float(image_w / image_h)
								resized_h = side - 5
								resized_w = int(aspect_ratio * resized_h)
							image = smoothscale(unit.image, (resized_w, resized_h))
						else:
							image = unit.image

						blit(image, (i * side + side // 2 - image.get_size()[0] // 2, j * side))

					hp_bar_length = int(unit.hp / unit.hp_max * side)
					hp_bar = pygame.Surface((hp_bar_length, 5))
					hp_bar.fill((0, 255, 0))
					blit(hp_bar, (i * side, j * side + side - 5))  # hp bar

				if self.is_selected((i, j)):
					blit(self.highlight_surfaces['selected'], (i * side, j * side))
				elif self.is_in_move_range((i, j)):
					blit(self.highlight_surfaces['move'], (i * side, j * side))
				elif self.is_in_attack_range((i, j)):
					blit(self.highlight_surfaces['attack'], (i * side, j * side))
				elif unit is not None and unit.played:
					blit(self.highlight_surfaces['played'], (i * side, j * side))

				# arrow
				if (i, j) in self.arrow:
					pos = (i * side + side // 2 - self.arrow_image.get_width() // 2, j * side + side // 2 - self.arrow_image.get_height() // 2)
					blit(self.arrow_image, pos)

		horizontal_line = pygame.Surface((map_w, 2)).convert_alpha()
		horizontal_line.fill((0, 0, 0, 100))
		vertical_line = pygame.Surface((2, map_h)).convert_alpha()
		vertical_line.fill((0, 0, 0, 100))

		for i in range(self.w):
			blit(vertical_line, (i * self.tile_size - 1, 0))
		for j in range(self.h):
			blit(horizontal_line, (0, j * self.tile_size - 1))
		return rendering

	def position_unit(self, unit, coord):
		"""Set an unit to the coordinates."""
		(x, y) = coord
		self.nodes[x][y].unit = unit

	def screen_resize(self, screen_size):
		"""
		On screen resize this method has to be called to resize every
		tile.
		"""
		(screen_w, screen_h) = screen_size
		self.tile_size = min(screen_w // self.w, screen_h // self.h)
		self.square = (self.tile_size, self.tile_size)
		for highlight, color in self.highlight_colors.items():
			h = pygame.Surface(self.square).convert_alpha()
			self.highlight_surfaces[highlight] = h
			self.highlight_surfaces[highlight].fill(color)

	def mouse2cell(self, cursor_coord):
		"""mouse position to map indexes."""

		(cursor_x, cursor_y) = cursor_coord

		x = int(cursor_x // self.tile_size)
		y = int(cursor_y // self.tile_size)

		if x >= self.w or y >= self.h:
			raise ValueError('%d >= %d or %d >= %d' % (x, self.w, y, self.h))

		return (x, y)

	def where_is(self, unit):
		"""
		This method finds a unit and returns its position.
		"""
		for i in range(self.w):
			for j in range(self.h):
				if self.nodes[i][j].unit == unit:
					return (i, j)
		return None

	def move(self, old_coord, new_coord):
		"""
		This method moves a unit from a node to another one. If the two
		coordinates are the same no action is performed.
		"""
		(old_x, old_y) = old_coord
		(x, y) = new_coord

		if old_coord != new_coord:
			print('Unit %s moved from %d:%d to %d:%d' %
				(self.get_unit(old_x, old_y).name, old_x, old_y, x, y))
			self.nodes[x][y].unit = self.nodes[old_x][old_y].unit
			self.nodes[old_x][old_y].unit = None

	def remove_unit(self, unit):
		"""
		Remove a unit from the map. Raises a ValueError if the unit
		couldn't be found.
		"""
		x, y = coord = self.where_is(unit)
		if coord is not None:
			self.nodes[x][y].unit = None
		else:
			raise ValueError("Can't find unit " + str(unit))

	def update_move_area(self, coord):
		"""
		Updates the area which will be highlighted on the map to show
		which nodes can be reached by the selected unit.
		"""
		(x, y) = coord
		unit = self.get_unit(coord)
		move = unit.move
		weapon_range = unit.get_weapon_range()
		self.move_area = []

		dist, prev = self.dijkstra(coord)

		for i in range(self.w):
			for j in range(self.h):
				if dist[i][j] <= move:
					self.move_area.append((i, j))

	def get_node(self, a, b=None):
		if b is None:
			x, y = a
			return self[x, y]
		else:
			return self[a, b]

	def update_attack_area(self, coord):
		"""
		Updates the area which will be highlighted on the map to show
		how far the selected unit can attack.
		"""
		(x, y) = coord
		weapon_range = self.get_unit(x, y).get_weapon_range()
		self.attack_area = []

		for (x, y) in self.move_area:
			for i in range(x - weapon_range, x + weapon_range + 1):
				for j in range(y - weapon_range, y + weapon_range + 1):
					if (i, j) not in self.move_area:
						if distance((x, y), (i, j)) <= weapon_range:
							self.attack_area.append((i, j))

	def update_arrow(self, target):
		if self.curr_sel is not None and self.move_area:
			dist, prev = self.dijkstra(self.curr_sel)
			self.arrow = self.shortest_path(prev, target)
		else:
			self.arrow = []

	def nearby_units(self, coord, colors=[]):
		"""
		Returns a list of coordinates that can be reached by the
		attacking unit to attack. If colors is empty the list will also
		contain same team units. Otherwise only units with a different
		color will be included.
		"""
		(x, y) = coord
		unit = self.nodes[x][y].unit
		unit_range = self.nodes[x][y].unit.get_weapon_range()
		nearby_list = []

		for i in range(x - unit_range, x + unit_range + 1):
			for j in range(y - unit_range, y + unit_range + 1):
				if (x, y) != (i, j) and distance((x, y), (i, j)) <= unit_range:
					try:
						node_unit = self.get_unit(i, j)
						if node_unit is not None:
							if (not colors) or (node_unit.color not in colors):
								nearby_list.append((i, j))
					except IndexError:
						pass

		return nearby_list

	def is_in_move_range(self, coord):
		return coord in self.move_area

	def is_in_attack_range(self, coord):
		return coord in self.attack_area

	def is_selected(self, coord):
		return self.curr_sel == coord

	def reset_selection(self):
		self.curr_sel = None
		self.prev_sel = None
		self.move_area = []
		self.attack_area = []
		self.arrow = []

	def can_selection_move(self, active_player):
		nx, ny = self.curr_sel
		sx, sy = self.prev_sel
		prev_unit = self.nodes[sx][sy].unit
		curr_unit = self.nodes[nx][ny].unit

		return (prev_unit is not None and not prev_unit.played and
			active_player.is_mine(prev_unit) and
			self.is_in_move_range(self.curr_sel))

	def sel_distance(self):
		return distance(self.curr_sel, self.prev_sel)

	def can_selection_attack(self, active_player):
		nx, ny = self.curr_sel
		sx, sy = self.prev_sel
		prev_unit = self.nodes[sx][sy].unit
		curr_unit = self.nodes[nx][ny].unit

		return (prev_unit is not None and not prev_unit.played and
			active_player.is_mine(prev_unit) and
			curr_unit is not None and
			not active_player.is_mine(curr_unit) and
			self.sel_distance() <= prev_unit.get_weapon_range())

	def get_unit(self, a, b=None):
		if b is None:
			x, y = a
			return self[x, y].unit
		else:
			return self[a, b].unit

	def handle_click(self, mouse_pos, active_player):
		try:
			x, y = self.mouse2cell(mouse_pos)
		except ValueError:
			return []

		self.curr_sel = (x, y)

		if self.prev_sel is None:
			unit = self.get_unit(x, y)
			if unit is None or unit.played:
				self.move_area = []
				self.attack_area = []
			else:
				self.update_move_area((x, y))
				self.update_attack_area((x, y))
			self.prev_sel = self.curr_sel
		else:
			prev_unit = self.get_unit(self.prev_sel)
			curr_unit = self.get_unit(self.curr_sel)

			if prev_unit is not None and curr_unit is not None:
				if prev_unit == curr_unit and not prev_unit.played and active_player.is_mine(prev_unit):
					enemies_nearby = len(self.nearby_units(self.curr_sel, [prev_unit.color]))
					if enemies_nearby > 0:
						return [("Attack", self.attack_callback), ("Wait", self.wait_callback)]
					else:
						return[("Wait", self.wait_callback)]
				else:
					self.prev_sel = self.curr_sel
					self.update_move_area(self.curr_sel)
					self.update_attack_area(self.curr_sel)
			elif self.can_selection_move(active_player):

				self.move(self.prev_sel, self.curr_sel)
				enemies_nearby = len(self.nearby_units(self.curr_sel, [prev_unit.color]))

				if enemies_nearby > 0:
					return [("Attack", self.attack_callback), ("Wait", self.wait_callback)]
				else:
					return[("Wait", self.wait_callback)]

			else:
				self.reset_selection()
				self.curr_sel = self.prev_sel = (x, y)

				if curr_unit is not None and not curr_unit.played:
					self.update_move_area((x, y))
					self.update_attack_area((x, y))
		return []

	def wait_callback(self):
		unit = self.get_unit(self.curr_sel)
		self.reset_selection()
		unit.played = True

	def attack_callback(self):
		unit = self.get_unit(self.curr_sel)
		self.move_area = []
		self.attack_area = self.nearby_units(self.curr_sel, [unit.color])

	def rollback_callback(self):
		self.move(self.curr_sel, self.prev_sel)
		self.reset_selection()

	def is_attack_click(self, mouse_pos):
		try:
			x, y = self.mouse2cell(mouse_pos)
		except ValueError:
			return False

		return (x, y) in self.attack_area
