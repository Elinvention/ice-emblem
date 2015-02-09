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


def distance(p0, p1):
	return abs(p0[0] - p1[0]) + abs(p0[1] - p1[1])


class IEMapNode(object):
	"""Node"""

	def __init__(self, tile, unit=None, walkable=True, Def_bonus=0):
		self.tile = tile
		self.unit = unit
		self.walkable = walkable
		self.Def_bonus = Def_bonus

	def is_obstacle(self, color=None):
		if color is not None:
			return (not self.walkable or
				(self.unit is not None and self.unit.color != color))
		else:
			return not self.walkable or self.unit is not None


class IEMap(object):
	"""The map is composed of nodes."""
	def __init__(self, map_path, (screen_w, screen_h), highlight_colors,
				units):
		tmx_data = pytmx.load_pygame(map_path)
		#map_data = pyscroll.data.TiledMapData(tmx_data)
		#self.map_layer = pyscroll.BufferedRenderer(map_data, (screen_w, screen_h))
		self.h = tmx_data.height
		self.w = tmx_data.width
		self.tile_size = min(screen_w / self.w, screen_h / self.h)
		self.square = (self.tile_size, self.tile_size)
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

		self.prev_sel = None
		self.curr_sel = None
		self.move_area = []
		self.attack_area = []

		self.highlight_colors = highlight_colors
		self.highlight_surfaces = {}
		for highlight, color in self.highlight_colors.iteritems():
			self.highlight_surfaces[highlight] = pygame.Surface(self.square).convert_alpha()
			self.highlight_surfaces[highlight].fill(color)

	def render(self, (screen_w, screen_h)):
		"""Renders the map returning a Surface"""

		map_w = self.tile_size * self.w
		map_h = self.tile_size * self.h
		side = self.tile_size

		rendering = pygame.Surface((map_w, map_h))

		#if self.background_color:
		#	rendering.fill(pygame.Color(self.background_color))

		# deref these heavily used references for speed
		smoothscale = pygame.transform.smoothscale

		for i in range(self.w):
			for j in range(self.h):
				tile = self.nodes[i][j].tile
				tile = smoothscale(tile, self.square)
				rendering.blit(tile, (i * self.tile_size, j * self.tile_size))

				node = self.nodes[i][j]
				unit = node.unit
				if unit is not None and unit.color is not None:
					pos = (i * side + side / 2, j * side + side / 2)
					pygame.draw.circle(rendering, unit.color, pos, side / 2, 5)

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

				if self.is_selected((i, j)):
					rendering.blit(self.highlight_surfaces['selected'], (i * side, j * side))
				elif self.is_in_move_range((i, j)):
					rendering.blit(self.highlight_surfaces['move'], (i * side, j * side))
				elif self.is_in_attack_range((i, j)):
					rendering.blit(self.highlight_surfaces['attack'], (i * side, j * side))
				elif self.is_played((i, j)):
					rendering.blit(self.highlight_surfaces['played'], (i * side, j * side))

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
		for highlight, color in self.highlight_colors.iteritems():
			self.highlight_surfaces[highlight] = pygame.Surface(self.square).convert_alpha()
			self.highlight_surfaces[highlight].fill(color)

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

	def update_move_area(self, (x, y)):
		"""
		Recursive algorithm to find all areas the selected unit can move to.
		
		"""
		unit = self.get_unit(x, y)
		Move = unit.Move
		weapon_range = unit.get_weapon_range()

		def find((px, py), already_visited=[], counter=0):
			next_checks = [(px, py)]
			if px > x:
				next_checks.extend([(px + 1, py), (px, py + 1), (px, py - 1)])
			elif py > y:
				next_checks.extend([(px + 1, py), (px, py + 1), (px - 1, py)])
			elif px < x:
				next_checks.extend([(px, py + 1), (px - 1, py), (px, py - 1)])
			elif py < y:
				next_checks.extend([(px + 1, py), (px - 1, py), (px, py - 1)])

			ret = []
			for next_check in next_checks:
				try:
					node = self.get_node(next_check)
				except IndexError:
					#print("%s outside map!" % str(next_check))
					continue
				if next_check not in already_visited:
					#print("Checking %s" % str(next_check))
					if counter > Move:
						break
					elif distance((x, y), next_check) > Move:
						#print("%s too far from %s" % (str(next_check), (x, y)))
						already_visited.append(next_check)
					elif node.is_obstacle(unit.color):
						#print("%s obstacle" % str(next_check))
						already_visited.append(next_check)
					else:
						#print("%s added!" % str(next_check))
						already_visited.append(next_check)
						ret.append(next_check)
						ret.extend(find(next_check, already_visited, counter + 1))
			return ret

		a1 = find((x + 1, y))
		a2 = find((x, y + 1))
		a3 = find((x - 1, y))
		a4 = find((x, y - 1))
		self.move_area = [(x, y)] + a1 + a2 + a3 + a4

	def get_node(self, a, b=None):
		x, y = a
		return self.nodes[x][y]

	def update_attack_area(self, (x, y)):
		"""
		Returns a list of map coordinates that the unit can reach to attack
		"""
		weapon_range = self.get_unit(x, y).get_weapon_range()
		self.attack_area = []

		for (x, y) in self.move_area:
			for i in range(x - weapon_range, x + weapon_range + 1):
				for j in range(y - weapon_range, y + weapon_range + 1):
					if (i, j) not in self.move_area:
						if distance((x, y), (i, j)) <= weapon_range:
							self.attack_area.append((i, j))

	def nearby_units(self, (x, y), colors=[]):
		unit = self.nodes[x][y].unit
		unit_range = self.nodes[x][y].unit.get_weapon_range()
		nearby_list = []

		for i in range(x - unit_range, x + unit_range + 1):
			for j in range(y - unit_range, y + unit_range + 1):
				if (x, y) != (i, j) and distance((x, y), (i, j)) <= unit_range:
					try:
						nodes_unit = self.get_unit(i, j)
						if nodes_unit is not None:
							if (not colors) or (nodes_unit.color not in colors):
								nearby_list.append((i, j))
					except IndexError:
						pass

		return nearby_list

	def path(self, (ax, ay), (bx, by)):
		"""
		We need to implement a basic Dijkstra's algorithm
		https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm
		to find the shortest path from a to b
		"""

	def is_in_move_range(self, (x, y)):
		return (x, y) in self.move_area

	def is_in_attack_range(self, (x, y)):
		return (x, y) in self.attack_area

	def is_selected(self, (x, y)):
		return (self.curr_sel == (x, y))

	def reset_selection(self):
		self.curr_sel = None
		self.prev_sel = None
		self.move_area = []
		self.attack_area = []

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
		try:
			x, y = a
		except TypeError:
			return self.nodes[a][b].unit
		else:
			return self.nodes[x][y].unit

	def handle_click(self, mouse_pos, active_player):
		try:
			x, y = self.mouse2cell(mouse_pos)
		except ValueError, e:
			return

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
				if prev_unit == curr_unit:
					#n_units_nearby = len(self.nearby_units(self.curr_sel))
					#if n_units_nearby > 0:
					return 1
				else:
					self.prev_sel = self.curr_sel
					self.update_move_area(self.curr_sel)
					self.update_attack_area(self.curr_sel)
			elif self.can_selection_move(active_player):

				self.move(self.prev_sel, self.curr_sel)
				n_units_nearby = len(self.nearby_units(self.curr_sel))

				if n_units_nearby > 0:
					return 1
				else:
					prev_unit.played = True
					self.reset_selection()

			elif self.can_selection_attack(active_player):
				self.reset_selection()
				return 2
			else:
				self.reset_selection()
				self.curr_sel = self.prev_sel = (x, y)

				if curr_unit is not None and not curr_unit.played:
					self.update_move_area((x, y))
					self.update_attack_area((x, y))
		return 0

	def action(self, action):
		nx, ny = self.curr_sel
		px, py = self.prev_sel
		curr_unit = self.nodes[nx][ny].unit
		prev_unit = self.nodes[px][py].unit

		if action == 0:  # if user choose Wait
			self.reset_selection()
			curr_unit.played = True

		elif action == 1:  # if user choose Attack
			self.move_area = []
			self.attack_area = self.nearby_units(self.curr_sel, [curr_unit.color])

		elif action == -1:  # if user cancel
			# Move unit back
			self.move(self.curr_sel, self.prev_sel)
			self.reset_selection()

	def is_attack_click(self, mouse_pos):
		try:
			x, y = self.mouse2cell(mouse_pos)
		except ValueError, e:
			return False

		return (x, y) in self.attack_area
