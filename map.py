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
import os.path
import logging
import utils
from unit import Unit
from colors import *


class UnitSprite(pygame.sprite.Sprite):
	def __init__(self, size, obj, unit, *groups):
		"""
		size: sprite size in pixels
		obj: unit data from tmx
		unit: unit object
		groups: sprites layer
		"""
		super(UnitSprite, self).__init__(*groups)

		self.unit = unit
		w, h = size
		self.x, self.y = self.coord = (obj.px // w), (obj.py // h)
		pos = self.x * w, self.y * h

		self.image = pygame.Surface(size).convert_alpha()
		self.rect = rect = pygame.Rect(pos, size)

		self.update()

	def update(self, new_coord=None):
		if new_coord is not None:
			self.x, self.y = self.coord = new_coord
			self.rect.topleft = self.x * self.rect.w, self.y * self.rect.h

		w, h = self.rect.size
		w2, h2 = w // 2, h // 2
		mw, mh = img_max_size = (w, h - 5)
		mw2, mh2 = mw // 2, mh // 2

		self.image.fill((0, 0, 0, 0))
		pygame.draw.circle(self.image, self.unit.color, (mw2, mh2), mh2, 3)

		src_img = self.unit.image
		if src_img is None:
			self.image.blit(src_img, utils.center(self.image.get_rect(), src_img.get_rect()))
		else:
			image_size = utils.resize_keep_ratio(src_img.get_size(), img_max_size)
			resized_image = pygame.transform.smoothscale(src_img, image_size).convert_alpha()
			self.image.blit(resized_image, utils.center(self.image.get_rect(), resized_image.get_rect()))

		hp_bar_length = int(self.unit.hp / self.unit.hp_max * self.rect.w)
		hp_bar = pygame.Surface((hp_bar_length, 5))
		hp_bar.fill((0, 255, 0))
		self.image.blit(hp_bar, (0, self.rect.h - 5))


class Terrain(object):
	def __init__(self, tile):
		self.name = tile.properties.get('name', _('Unknown'))
		self.moves = float(tile.properties.get('moves', 1))  # how many moves are required to move a unit through
		self.defense = int(tile.properties.get('defense', 0))  # bonus defense
		self.avoid = int(tile.properties.get('avoid', 0))  # bonus avoid
		self.allowed = tile.properties.get('allowed', _('any'))
		self.surface = tile.surface


class Cursor(pygame.sprite.Sprite):
	def __init__(self, tilemap, img_path, *groups):
		super(Cursor, self).__init__(*groups)
		self.image = pygame.image.load(img_path).convert_alpha()
		self.tilesize = tilemap.tile_width, tilemap.tile_height
		self.rect = pygame.Rect((0, 0), self.tilesize)
		self.coord = (0, 0)
		self.tilemap = tilemap

	def update(self, event):
		if event.type == pygame.KEYDOWN:
			cx, cy = self.coord
			if event.key == pygame.K_UP:
				cx, cy = (cx, (cy - 1) % self.tilemap.height)
			elif event.key == pygame.K_DOWN:
				cx, cy = (cx, (cy + 1) % self.tilemap.height)
			elif event.key == pygame.K_LEFT:
				cx, cy = ((cx - 1) % self.tilemap.width, cy)
			elif event.key == pygame.K_RIGHT:
				cx, cy = ((cx + 1) % self.tilemap.width, cy)

			self.rect.x = cx * self.tilemap.tile_width
			self.rect.y = cy * self.tilemap.tile_height
			self.coord = cx, cy
		elif event.type == pygame.MOUSEMOTION:
			cx, cy = self.tilemap.index_at(*event.pos)
			if 0 <= cx < self.tilemap.width and 0 <= cy < self.tilemap.height:
				self.rect.x = cx * self.tilemap.tile_width
				self.rect.y = cy * self.tilemap.tile_height
				self.coord = cx, cy


class CellHighlight(pygame.sprite.Sprite):
	def __init__(self, tilemap, *groups):
		super(CellHighlight, self).__init__(*groups)

		self.w, self.h = tilemap.width, tilemap.height
		self.tile_size = self.tw, self.th = tilemap.tile_width, tilemap.tile_height

		self.highlight_colors = dict(selected=SELECTED, move=MOVE, attack=ATTACK, played=PLAYED)
		self.highlight_surfaces = {}
		for highlight, color in self.highlight_colors.items():
			self.highlight_surfaces[highlight] = pygame.Surface(self.tile_size).convert_alpha()
			self.highlight_surfaces[highlight].fill(color)

		self.horizontal_line = pygame.Surface((tilemap.px_width, 2)).convert_alpha()
		self.horizontal_line.fill((0, 0, 0, 100))
		self.vertical_line = pygame.Surface((2, tilemap.px_height)).convert_alpha()
		self.vertical_line.fill((0, 0, 0, 100))

		self.image = pygame.Surface((tilemap.px_width, tilemap.px_height)).convert_alpha()
		self.image.fill((0, 0, 0, 0))

		for i in range(self.w):
			self.image.blit(self.vertical_line, (i * self.tw - 1, 0))
		for j in range(self.h):
			self.image.blit(self.horizontal_line, (0, j * self.th - 1))

		self.rect = pygame.Rect((0, 0), (tilemap.px_width, tilemap.px_height))

	def update(self, selected, move, attack, played):
		self.image.fill((0, 0, 0, 0))

		blit = self.image.blit

		if selected is not None:
			x, y = selected
			blit(self.highlight_surfaces['selected'], (x * self.tw, y * self.th))

		for (x, y) in move:
			blit(self.highlight_surfaces['move'], (x * self.tw, y * self.th))

		for (x, y) in attack:
			blit(self.highlight_surfaces['attack'], (x * self.tw, y * self.th))

		for (x, y) in played:
			blit(self.highlight_surfaces['played'], (x * self.tw, y * self.th))

		for i in range(self.w):
			self.image.blit(self.vertical_line, (i * self.tw - 1, 0))
		for j in range(self.h):
			self.image.blit(self.horizontal_line, (0, j * self.th - 1))

class Arrow(pygame.sprite.Sprite):
	"""

	"""
	def __init__(self, screen_size, image_path, tilesize, *groups):
		super(Arrow, self).__init__(*groups)
		self.source_image = pygame.image.load(image_path)

		self.arrow = {}

		self.path = []
		self.source = None

		self.set_tilesize(tilesize)

		self.image = pygame.Surface(screen_size).convert_alpha()
		self.image.fill((0, 0, 0, 0))
		self.rect = pygame.Rect((0, 0), screen_size)

	def update(self, path, source=None):
		if source is not None:
			self.source = source
		self.path = path
		self.image.fill((0, 0, 0, 0))
		for (x, y) in self.path:
			img = self.get_arrow_part((x, y))
			pos = (x * self.tilesize[0], y * self.tilesize[1])
			self.image.blit(img, pos)

	def set_tilesize(self, tilesize):
		self.tilesize = tilesize
		w, h = self.source_image.get_size()
		rw, rh = rectsize = (w // 4, h // 4)

		arrow_parts = []
		for j in range(4):
			for i in range(4):
				pos = (i * rw, j * rh)
				rect = pygame.Rect(pos, rectsize)
				img = pygame.Surface.subsurface(self.source_image, rect)
				img = pygame.transform.smoothscale(img, tilesize)
				arrow_parts.append(img)

		self.arrow = {
			'horizontal': arrow_parts[1],
			'vertical': arrow_parts[4],
			'topleft': arrow_parts[0],
			'topright': arrow_parts[3],
			'bottomleft': arrow_parts[12],
			'bottomright': arrow_parts[15],
			'up': arrow_parts[5],
			'down': arrow_parts[10],
			'left': arrow_parts[9],
			'right': arrow_parts[6],
		}

	def get_arrow_part(self, coord):
		index = self.path.index(coord)
		a = self.path[index - 1] if index - 1 >= 0 else self.source
		b = self.path[index]
		c = self.path[index + 1] if (index + 1) < len(self.path) else None

		if c is None:
			ax, ay = a
			bx, by = b
			if bx == ax + 1:
				return self.arrow['right']
			elif bx == ax - 1:
				return self.arrow['left']
			elif by == ay + 1:
				return self.arrow['down']
			elif by == ay - 1:
				return self.arrow['up']
		else:
			ax, ay = a
			bx, by = b
			cx, cy = c
			if ax == bx == cx:
				return self.arrow['vertical']
			elif ay == by == cy:
				return self.arrow['horizontal']

			elif (ax == bx and ay < by and bx < cx and by == cy) or (cx == bx and by == ay and cy < by and bx < ax):
				return self.arrow['bottomleft']

			elif (ax == bx and ay < by and bx > cx and by == cy) or (ax < bx and ay == by and bx == cx and by > cy):
				return self.arrow['bottomright']

			elif (ax == bx and ay > by and bx > cx and by == cy) or (ax < bx and ay == by and bx == cx and by < cy):
				return self.arrow['topright']

			elif (ax == bx and ay > by and bx < cx and by == cy) or (ax > bx and ay == by and bx == cx and by < cy):
				return self.arrow['topleft']

			else:
				raise ValueError("ArrowError: " + str((a, b, c)))


class Pathfinder(object):
	def __init__(self, matrix):
		self.matrix = matrix
		self.w, self.h = len(self.matrix), len(self.matrix[0])
		self.reset()

	def reset(self):
		self.obstacles = []  # additional obstacles (depends on selected unit)
		self.source = None  # dijkstra executed with this node as source
		self.target = None  # shortest path target
		self.shortest = None  # shortest path output
		self.max_distance = None
		self.dist = None  # results of dijkstra
		self.prev = None

	def check_coord(self, coord):
		x, y = coord
		return 0 <= x < self.w and 0 <= y < self.h

	def neighbors(self, coord):
		x, y = coord

		if not self.check_coord(coord):
			raise ValueError("Invalid coordinates")

		n = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
		return [ x for x in n if self.check_coord(x) ]

	def __set_source(self, source):
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
		self.shortest = None

		self.dist = [[None for _ in range(self.h)] for _ in range(self.w)]
		self.prev = [[None for _ in range(self.h)] for _ in range(self.w)]

		sx, sy = self.source = source
		self.dist[sx][sy] = 0     # Distance from source to source
		self.prev[sx][sy] = None  # Previous node in optimal path initialization

		Q = []
		for i in range(self.w):  # Initialization
			for j in range(self.h):
				if (i, j) != source:  # Where v has not yet been removed from Q (unvisited nodes)
					self.dist[i][j] = float('inf')  # Unknown distance function from source to v
					self.prev[i][j] = None  # Previous node in optimal path from source
				Q.append((i, j))  # All nodes initially in Q (unvisited nodes)

		while Q:
			u0, u1 = Q[0]
			min_dist = self.dist[u0][u1]
			u = (u0, u1)

			for el in Q:
				i, j = el
				if self.dist[i][j] < min_dist:
					min_dist = self.dist[i][j]
					u0, u1 = u = el  #  Source node in first case

			Q.remove(u)

			# where v has not yet been removed from Q.
			for v in self.neighbors(u):
				v0, v1 = v

				alt = self.dist[u0][u1] + self.matrix[v0][v1]
				# A shorter path to v has been found
				if alt < self.dist[v0][v1]:
					self.dist[v0][v1] = alt
					self.prev[v0][v1] = u

			for obs0, obs1 in self.obstacles:
				self.dist[obs0][obs1] = float('inf')
				#self.prev[obs0][obs1] = None

	def __set_target(self, target, max_distance=float('inf')):
		"""
		This method wants the second list returned by the dijkstra
		method and a target node. The shortest path between target and
		source previously specified when calling the dijkstra method
		will be returned as a list.
		"""
		self.max_distance = max_distance
		S = []
		u0, u1 = u = self.target = target

		# Construct the shortest path with a stack S
		while self.prev[u0][u1] is not None:
			if self.dist[u0][u1] <= max_distance:
				S.insert(0, u)  # Push the vertex onto the stack
			u0, u1 = u = self.prev[u0][u1]  # Traverse from target to source

		self.shortest = S
		return S

	def shortest_path(self, source, target, max_distance=float('inf')):
		if self.source != source:
			self.__set_source(source)
			self.__set_target(target, max_distance)
		elif self.target != target or self.max_distance != max_distance:
			self.__set_target(target, max_distance)
		return self.shortest

	def area(self, source, max_distance):
		if self.source != source:
			self.__set_source(source)
			self.target = None
			self.shortest = None
		h, w = range(self.h), range(self.w)
		return [ (i, j) for j in h for i in w if self.dist[i][j] <= max_distance ]


class Map(object):
	"""
	This class should handle every aspect related to the Map in Ice Emblem.
	"""

	def __init__(self, map_path, screen_size, units, origin=(0,0)):
		"""
		Loads a .tmx tilemap, initializes layers like sprites, cursor,
		arrow, highlight. It also generate a cost matrix to be used by
		the Path class.
		"""
		self.tilemap = tmx.load(map_path, (screen_size[0] - 200, screen_size[1]))
		self.tile_size = (self.tilemap.tile_width, self.tilemap.tile_height)

		self.sprites_layer = tmx.SpriteLayer()
		self.sprites = []

		for obj in self.tilemap.layers['Sprites'].objects:
			if obj.type == 'unit' and obj.name in units:
				self.sprites.append(UnitSprite(self.tile_size, obj, units[obj.name], self.sprites_layer))

		cursor_layer = tmx.SpriteLayer()
		self.cursor = Cursor(self.tilemap, os.path.join('images', 'cursor.png'), cursor_layer)

		arrow_layer = tmx.SpriteLayer()
		self.arrow = Arrow((self.tilemap.px_width, self.tilemap.px_height), os.path.join('images', 'arrow.png'), self.tile_size, arrow_layer)

		highlight_layer = tmx.SpriteLayer()
		self.highlight = CellHighlight(self.tilemap, highlight_layer)

		self.tilemap.layers.append(highlight_layer)
		self.tilemap.layers.append(self.sprites_layer)
		self.tilemap.layers.append(arrow_layer)
		self.tilemap.layers.append(cursor_layer)

		self.tilemap.set_focus(0, 0)

		self.prev_sel = None
		self.curr_sel = None
		self.move_area = []
		self.attack_area = []

		self.move_x, self.move_y = 0, 0

		# This matrix is used by dijkstra
		w, h = range(self.tilemap.width), range(self.tilemap.height)
		matrix = [[ self.get_terrain(x, y).moves for y in h ] for x in w]
		self.path = Pathfinder(matrix)

	def list_obstacles(self, unit=None):
		"""
		Provides a list of coordinates that are an obstacle for the unit
		"""
		w, h = range(self.tilemap.width), range(self.tilemap.height)
		return [ (x, y) for y in h for x in w if self.is_obstacle((x, y), unit) ]

	def __getitem__(self, pos):
		(x, y) = pos
		return self.nodes[x][y]

	def is_obstacle(self, coord, unit):
		for sprite in self.sprites:
			if sprite.coord == coord and sprite.unit.color != unit.color:
				return True
		return self.get_terrain(*coord).allowed != _('any')

	def check_coord(self, coord):
		x, y = coord
		return 0 <= x < self.tilemap.width and 0 <= y < self.tilemap.height

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

	def screen_resize(self, screen_size):
		"""
		On screen resize this method has to be called to resize every
		tile.
		"""
		viewport_size = (screen_size[0] - 200, screen_size[1])
		self.tilemap.viewport = pygame.Rect(self.tilemap.viewport.topleft, viewport_size)
		self.tilemap.view_w, self.tilemap.view_h = viewport_size

	def mouse2cell(self, cursor_coord):
		"""mouse position to map index."""
		x, y = cursor_coord
		map_index = self.tilemap.index_at(x, y)
		if self.check_coord(map_index):
			return map_index
		else:
			raise ValueError('(%d:%d) Cursor out of map')

	def where_is(self, unit):
		"""
		This method finds a unit and returns its position.
		"""
		for sprite in self.sprites:
			if sprite.unit == unit:
				return sprite.coord

		raise ValueError("Couldn't find " + str(unit))

	def move(self, old_coord, new_coord):
		"""
		This method moves a unit from a node to another one. If the two
		coordinates are the same no action is performed.
		"""
		if old_coord != new_coord:
			if self.get_unit(new_coord) is not None:
				raise ValueError("Destination %s is already occupied by another unit" % str(new_coord))
			for sprite in self.sprites:
				if sprite.coord == old_coord:
					sprite.update(new_coord)
					print(_('Unit %s moved from %s to %s') %
					(sprite.unit.name, str(old_coord), str(new_coord)))

	def kill_unit(self, unit):
		"""
		Removes a unit from the map. Raises a ValueError if the unit
		couldn't be found.
		"""
		sprite = self.find_sprite(unit)
		if sprite is not None:
			self.sprites_layer.remove(sprite)  # invisible
			self.sprites.remove(sprite)  # dead
		else:
			raise ValueError("Unit not found")

	def update_move_area(self, coord):
		"""
		Updates the area which will be highlighted on the map to show
		which nodes can be reached by the selected unit.
		"""
		unit = self.get_unit(coord)

		if self.path.source != coord:
			self.path.obstacles = self.list_obstacles(unit)

		self.move_area = self.path.area(coord, unit.move)

	def get_unit(self, coord):
		for sprite in self.sprites:
			if sprite.coord == coord:
				return sprite.unit

	def get_sprite(self, coord):
		for sprite in self.sprites:
			if sprite.coord == coord:
				return sprite.unit

	def find_sprite(self, unit):
		for sprite in self.sprites:
			if sprite.unit == unit:
				return sprite

	def update_attack_area(self, coord):
		"""
		Updates the area which will be highlighted on the map to show
		how far the selected unit can attack.
		"""
		weapon_range = self.get_unit(coord).get_weapon_range()
		self.attack_area = []

		for (x, y) in self.move_area:
			for i in range(x - weapon_range, x + weapon_range + 1):
				for j in range(y - weapon_range, y + weapon_range + 1):
					if (i, j) not in self.move_area and (i, j) not in self.attack_area:
						if utils.distance((x, y), (i, j)) <= weapon_range:
							self.attack_area.append((i, j))

	def update_arrow(self, target):
		if self.curr_sel is not None and self.move_area:
			path = self.path.shortest_path(self.curr_sel, target, self.get_unit(self.curr_sel).move)
			self.arrow.update(path, self.curr_sel)
		else:
			self.arrow.update([])

	def update_highlight(self):
		self.highlight.update(self.curr_sel, self.move_area, self.attack_area, self.list_played())

	def nearby_units(self, coord, colors=[]):
		"""
		Returns a list of coordinates that can be reached by the
		attacking unit to attack. If colors is empty the list will also
		contain same team units. Otherwise only units with a different
		color will be included.
		"""
		(x, y) = coord
		unit = self.get_unit(coord)
		unit_range = unit.get_weapon_range()
		nearby_list = []

		for i in range(x - unit_range, x + unit_range + 1):
			for j in range(y - unit_range, y + unit_range + 1):
				if (x, y) != (i, j) and utils.distance((x, y), (i, j)) <= unit_range:
					try:
						node_unit = self.get_unit((i, j))
						if node_unit is not None:
							if (not colors) or (node_unit.color not in colors):
								nearby_list.append((i, j))
					except IndexError:
						pass
		return nearby_list

	def reset_selection(self):
		logging.debug(_('Selection reset'))
		self.curr_sel = None
		self.prev_sel = None
		self.move_area = []
		self.attack_area = []
		self.arrow.update([])
		self.update_highlight()

	def can_selection_move(self, active_player):
		prev_unit = self.get_unit(self.prev_sel)
		curr_unit = self.get_unit(self.curr_sel)

		return (prev_unit is not None and not prev_unit.played and
			active_player.is_mine(prev_unit) and
			self.curr_sel in self.move_area)

	def sel_distance(self):
		return distance(self.curr_sel, self.prev_sel)

	def can_selection_attack(self, active_player):
		prev_unit = self.get_unit(self.prev_sel)
		curr_unit = self.get_unit(self.curr_sel)

		return (prev_unit is not None and not prev_unit.played and
			active_player.is_mine(prev_unit) and
			curr_unit is not None and
			not active_player.is_mine(curr_unit) and
			self.sel_distance() <= prev_unit.get_weapon_range())

	def handle_click(self, event, active_player):
		if event.button == 1:
			try:
				coord = self.mouse2cell(event.pos)
			except ValueError:
				return []
			ret = self.select(coord, active_player)
			self.update_highlight()
			return ret
		elif event.button == 3:
			self.reset_selection()
			return []

	def list_played(self):
		r = []
		for sprite in self.sprites:
			if sprite.unit.played:
				r.append(sprite.coord)
		return r

	def handle_mouse_motion(self, event):
		try:
			coord = self.mouse2cell(event.pos)
			self.update_arrow(coord)
		except ValueError:
			pass
		self.cursor.update(event)

		x, y = event.pos
		border = 50
		speed = 5
		if x < border:
			self.move_x = -speed
		elif x > self.tilemap.view_w - border:
			self.move_x = speed
		else:
			self.move_x = 0

		if y < border:
			self.move_y = -speed
		elif y > self.tilemap.view_h - border:
			self.move_y = speed
		else:
			self.move_y = 0

	def render(self):
		fx = self.tilemap.fx + self.move_x
		fy = self.tilemap.fy + self.move_y
		if fx != self.tilemap.fx or fy != self.tilemap.fy:
			self.tilemap.set_focus(fx, fy)

		surf = pygame.Surface((self.tilemap.view_w, self.tilemap.view_h))
		self.tilemap.draw(surf)
		return surf

	def handle_keyboard(self, event, active_player):
		self.cursor.update(event)
		self.tilemap.set_focus(self.cursor.rect.x, self.cursor.rect.y)

		if self.move_area:
			self.update_arrow(self.cursor.coord)

		if event.key == pygame.K_SPACE:
			ret = self.select(self.cursor.coord, active_player)
			self.update_highlight()
			return ret

	def select(self, coord, active_player):
		self.curr_sel = coord
		self.arrow.path = []

		if self.prev_sel is None:
			unit = self.get_unit(coord)
			if unit is None or unit.played:
				self.move_area = []
				self.attack_area = []
			else:
				self.update_move_area(coord)
				self.update_attack_area(coord)
			self.prev_sel = self.curr_sel
		else:
			prev_unit = self.get_unit(self.prev_sel)
			curr_unit = self.get_unit(self.curr_sel)

			if prev_unit is not None and curr_unit is not None:
				if prev_unit == curr_unit and not prev_unit.played and active_player.is_mine(prev_unit):
					enemies_nearby = len(self.nearby_units(self.curr_sel, [prev_unit.color]))
					if enemies_nearby > 0:
						return [(_("Attack"), self.attack_callback), (_("Wait"), self.wait_callback)]
					else:
						return[(_("Wait"), self.wait_callback)]
				else:
					self.prev_sel = self.curr_sel
					self.update_move_area(self.curr_sel)
					self.update_attack_area(self.curr_sel)
			elif self.can_selection_move(active_player):

				self.move(self.prev_sel, self.curr_sel)
				self.arrow.update([])
				enemies_nearby = len(self.nearby_units(self.curr_sel, [prev_unit.color]))

				if enemies_nearby > 0:
					return [(_("Attack"), self.attack_callback), (_("Wait"), self.wait_callback)]
				else:
					return[(_("Wait"), self.wait_callback)]

			else:
				self.reset_selection()
				self.curr_sel = self.prev_sel = coord

				if curr_unit is not None and not curr_unit.played:
					self.update_move_area(coord)
					self.update_attack_area(coord)
					self.update_arrow(coord)
		return []

	def wait_callback(self):
		unit = self.get_unit(self.curr_sel)
		unit.played = True
		self.reset_selection()

	def attack_callback(self):
		unit = self.get_unit(self.curr_sel)
		self.move_area = []
		self.attack_area = self.nearby_units(self.curr_sel, [unit.color])
		self.update_highlight()

	def rollback_callback(self):
		self.move(self.curr_sel, self.prev_sel)
		self.reset_selection()

	def is_attack_click(self, mouse_pos):
		try:
			x, y = self.mouse2cell(mouse_pos)
		except ValueError:
			return False

		return (x, y) in self.attack_area

	def is_enemy_cursor(self):
		return self.cursor.coord in self.attack_area

	def get_terrain(self, x, y):
		for layer in reversed(self.tilemap.layers):
			try:
				return Terrain(layer[x, y].tile)
			except (TypeError, AttributeError):
				continue

