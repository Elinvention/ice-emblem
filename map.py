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
from unit import Unit


def distance(p0, p1):
	return abs(p0[0] - p1[0]) + abs(p0[1] - p1[1])

def resize_keep_ratio(size, max_size):
	w, h = size
	max_w, max_h = max_size
	resize_ratio = min(max_w / w, max_h / h)
	return int(w * resize_ratio), int(h * resize_ratio)

def center(rect1, rect2, xoffset=0, yoffset=0):
	"""Center rect2 in rect1 with offset."""
	return (rect1.centerx - rect2.centerx + xoffset, rect1.centery - rect2.centery + yoffset)


class UnitSprite(pygame.sprite.Sprite):
	def __init__(self, size, font, obj, unit, *groups):
		super(UnitSprite, self).__init__(*groups)

		self.unit = unit
		self.image = pygame.Surface(size).convert_alpha()
		w, h = size
		self.x, self.y = self.coord = (obj.px // w), (obj.py // h)
		pos = self.x * w, self.y * h
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
			text = font.render(self.unit.name, 1, BLACK)
			self.image.blit(text, center(self.image.get_rect(), text.get_rect()))
		else:
			image_size = resize_keep_ratio(src_img.get_size(), img_max_size)
			resized_image = pygame.transform.smoothscale(src_img, image_size).convert_alpha()
			self.image.blit(resized_image, center(self.image.get_rect(), resized_image.get_rect()))
			
		hp_bar_length = int(self.unit.hp / self.unit.hp_max * self.rect.w)
		hp_bar = pygame.Surface((hp_bar_length, 5))
		hp_bar.fill((0, 255, 0))
		self.image.blit(hp_bar, (0, self.rect.h - 5))


class Terrain(object):
	def __init__(self, tile):
		self.name = tile.properties.get('name', 'Unknown')
		self.moves = float(tile.properties.get('moves', 1))  # how many moves are required to move a unit through
		self.defense = int(tile.properties.get('defense', 0))  # bonus defense
		self.avoid = int(tile.properties.get('avoid', 0))  # bonus avoid
		self.allowed = tile.properties.get('allowed', 'any')
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
			cx, cy = self.tilemap.index_at(event.pos)
			if 0 <= cx < self.tilemap.width and 0 <= cy < self.tilemap.height:
				self.rect.x = cx * self.tilemap.tile_width
				self.rect.y = cy * self.tilemap.tile_height
				self.coord = cx, cy


class CellHighlight(pygame.sprite.Sprite):
	def __init__(self, tilemap, highlight_colors, *groups):
		super(CellHighlight, self).__init__(*groups)

		self.w, self.h = tilemap.width, tilemap.height
		self.tile_size = self.tw, self.th = tilemap.tile_width, tilemap.tile_height

		self.highlight_colors = highlight_colors
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
		#print("Updating CellHighlight")
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
		self.first_coord = None

		self.set_tilesize(tilesize)

		self.image = pygame.Surface(screen_size).convert_alpha()
		self.image.fill((0, 0, 0, 0))
		self.rect = pygame.Rect((0, 0), screen_size)

	def update(self, path=None):
		if path is not None:
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
		a = self.path[index - 1] if index - 1 >= 0 else self.first_coord
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


class Map(object):
	"""
	
	"""

	def __init__(self, map_path, screen_size, highlight_colors, units, origin=(0,0)):
		self.tilemap = tmx.load(map_path, (screen_size[0] - 200, screen_size[1]))
		self.tile_size = (self.tilemap.tile_width, self.tilemap.tile_height)

		self.sprites_layer = tmx.SpriteLayer()
		self.sprites = []

		for obj in self.tilemap.layers['Sprites'].objects:
			if obj.type == 'unit':
				self.sprites.append(UnitSprite(self.tile_size, None, obj, units[obj.name], self.sprites_layer))

		cursor_layer = tmx.SpriteLayer()
		self.cursor = Cursor(self.tilemap, os.path.join('images', 'cursor.png'), cursor_layer)

		arrow_layer = tmx.SpriteLayer()
		self.arrow = Arrow((self.tilemap.px_width, self.tilemap.px_height), os.path.join('images', 'arrow.png'), self.tile_size, arrow_layer)

		highlight_layer = tmx.SpriteLayer()
		self.highlight = CellHighlight(self.tilemap, highlight_colors, highlight_layer)

		self.tilemap.layers.append(self.sprites_layer)
		self.tilemap.layers.append(highlight_layer)
		self.tilemap.layers.append(arrow_layer)
		self.tilemap.layers.append(cursor_layer)

		self.tilemap.set_focus(0, 0)

		self.prev_sel = None
		self.curr_sel = None
		self.move_area = []
		self.attack_area = []

		self.move_x, self.move_y = 0, 0
		self.prev_coord = None

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
		dist = [[None for _ in range(self.tilemap.height)] for _ in range(self.tilemap.width)]
		prev = [[None for _ in range(self.tilemap.height)] for _ in range(self.tilemap.width)]
		sx, sy = source
		dist[sx][sy] = 0     # Distance from source to source
		prev[sx][sy] = None  # Previous node in optimal path initialization

		Q = []
		for i in range(self.tilemap.width):  # Initialization
			for j in range(self.tilemap.height):
				if (i, j) != source:  # Where v has not yet been removed from Q (unvisited nodes)
					dist[i][j] = float('inf')  # Unknown distance function from source to v
					prev[i][j] = None  # Previous node in optimal path from source
				Q.append((i, j))  # All nodes initially in Q (unvisited nodes)

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

			source_unit_color = self.get_unit(source).color

			# where v has not yet been removed from Q.
			for v in self.neighbors(u):
				v0, v1 = v

				if self.is_obstacle(v, source_unit_color):
					dist[v0][v1] = float('inf')
					prev[v0][v1] = None
				else:
					alt = dist[u0][u1] + self.get_terrain(v).moves

					# A shorter path to v has been found
					if alt < dist[v0][v1]:  
						dist[v0][v1] = alt
						prev[v0][v1] = u

		return dist, prev

	def is_obstacle(self, coord, color):
		for sprite in self.sprites:
			if (sprite.x, sprite.y) == coord and sprite.unit.color != color:
				return True
		return self.get_terrain(coord).allowed != 'any'

	def check_coord(self, coord):
		x, y = coord
		if 0 <= x < self.tilemap.width and 0 <= y < self.tilemap.height:
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
		(old_x, old_y) = old_coord
		(x, y) = new_coord

		if old_coord != new_coord:
			for sprite in self.sprites:
				if sprite.coord == old_coord:
					sprite.update(new_coord)
					print('Unit %s moved from %d:%d to %d:%d' %
					(sprite.unit.name, old_x, old_y, x, y))

	def kill_unit(self, unit):
		"""
		Removes a unit from the map. Raises a ValueError if the unit
		couldn't be found.
		"""
		found = False
		for sprite in self.sprites:
			if sprite.unit == unit:
				self.sprites_layer.remove(sprite)
				self.sprites.remove(sprite)
				found = True
				break

		if not found:
			raise ValueError("Unit not found")

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

		for i in range(self.tilemap.width):
			for j in range(self.tilemap.height):
				if dist[i][j] <= move:
					self.move_area.append((i, j))

	def get_unit(self, a, b=None):
		if b is None:
			x, y = a
		else:
			x, y = a, b

		for sprite in self.sprites:
			if sprite.coord == (x, y):
				return sprite.unit

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
					if (i, j) not in self.move_area and (i, j) not in self.attack_area:
						if distance((x, y), (i, j)) <= weapon_range:
							self.attack_area.append((i, j))

	def update_arrow(self, target):
		if self.curr_sel is not None and self.move_area:
			dist, prev = self.dijkstra(self.curr_sel)
			self.arrow.first_coord = self.curr_sel
			shortest_path = self.shortest_path(prev, target)
			self.arrow.update(shortest_path)
		else:
			self.arrow.update([])

	def nearby_units(self, coord, colors=[]):
		"""
		Returns a list of coordinates that can be reached by the
		attacking unit to attack. If colors is empty the list will also
		contain same team units. Otherwise only units with a different
		color will be included.
		"""
		(x, y) = coord
		unit = self.get_unit(x, y)
		unit_range = unit.get_weapon_range()
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

	def reset_selection(self):
		self.curr_sel = None
		self.prev_sel = None
		self.move_area = []
		self.attack_area = []
		self.arrow.update([])
		self.highlight.update(self.curr_sel, self.move_area, self.attack_area, self.list_played())

	def can_selection_move(self, active_player):
		nx, ny = self.curr_sel
		sx, sy = self.prev_sel
		prev_unit = self.get_unit(sx, sy)
		curr_unit = self.get_unit(nx, ny)

		return (prev_unit is not None and not prev_unit.played and
			active_player.is_mine(prev_unit) and
			self.curr_sel in self.move_area)

	def sel_distance(self):
		return distance(self.curr_sel, self.prev_sel)

	def can_selection_attack(self, active_player):
		nx, ny = self.curr_sel
		sx, sy = self.prev_sel
		prev_unit = self.get_unit(sx, sy)
		curr_unit = self.get_unit(nx, ny)

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
			self.highlight.update(self.curr_sel, self.move_area, self.attack_area, self.list_played())
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
			if coord != self.prev_coord:
				self.update_arrow(coord)
				self.prev_coord = coord
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
			self.highlight.update(self.curr_sel, self.move_area, self.attack_area, self.list_played())
			return ret

	def select(self, coord, active_player):
		x, y = coord
		self.curr_sel = coord
		self.arrow.path = []

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
				self.arrow.update([])
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

	def is_enemy_cursor(self):
		return self.cursor.coord in self.attack_area

	def get_terrain(self, coord):
		for layer in reversed(self.tilemap.layers):
			try:
				return Terrain(layer[coord[0], coord[1]].tile)
			except (TypeError, AttributeError):
				continue
