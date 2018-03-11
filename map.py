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


import resources
import sounds
import tmx
import pygame
import logging
import utils
import heapq
import unit
import item
import events
import display
import colors as c


class UnitSprite(pygame.sprite.Sprite):
    """
    Encapsulates a Unit so that it can be shown on screen as a sprite.
    """
    def __init__(self, size, obj, unit, team, *groups):
        """
        size: sprite size in pixels
        obj: unit data from tmx
        unit: unit object
        groups: sprites layer
        """
        super().__init__(*groups)

        self.unit = unit
        self.team = team
        w, h = size
        x, y = (obj.px // w), (obj.py // h)
        pos = x * w, y * h

        self.image = pygame.Surface(size).convert_alpha()
        self.rect = pygame.Rect(pos, size)

        self.update()

    def reposition(self):
        self.rect.left = int(self.rect.w * self.unit.coord[0])
        self.rect.top = int(self.rect.h * self.unit.coord[1])

    def move_animation(self, delta, dest):
        delta /= 100
        x, y = dest
        normal = tuple(map(lambda x: 1 if x > 0 else -1 if x < 0 else 0, (x - self.rect.left, y - self.rect.top)))
        self.rect.left += int(self.rect.w * delta) * normal[0]
        self.rect.top += int(self.rect.h * delta) * normal[1]

        reached = False
        if (normal[0] == 1 and self.rect.left >= x) or (normal[0] == -1 and self.rect.left <= x):
            self.rect.left = x
            reached = True
        if (normal[1] == 1 and self.rect.top >= y) or (normal[1] == -1 and self.rect.left <= y):
            self.rect.top = y
            reached = True
        return reached

    def update(self):
        if not self.unit.was_modified():
            return

        logging.debug("Sprite update: %s" % self.unit.name)

        w, h = self.rect.size
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

        hp_bar_length = int(self.unit.health / self.unit.health_max * self.rect.w)
        hp_bar = pygame.Surface((hp_bar_length, 5))
        hp_bar.fill((0, 255, 0))
        self.image.blit(hp_bar, (0, self.rect.h - 5))
        if self.team.is_boss(self.unit):
            icon = pygame.Surface((3, 3))
            icon.fill(c.BLUE)
            self.image.blit(icon, (0, self.rect.h - 4))


class Terrain(object):
    def __init__(self, tile, unit):
        self.name = tile.properties.get('name', _('Unknown'))
        self.moves = float(tile.properties.get('moves', 1))  # how many moves are required to move a unit through
        self.defense = int(tile.properties.get('defense', 0))  # bonus defense
        self.avoid = int(tile.properties.get('avoid', 0))  # bonus avoid
        self.allowed = tile.properties.get('allowed', _('any')).split(',')
        self.surface = tile.surface
        self.unit = unit

class Cursor(pygame.sprite.Sprite):
    def __init__(self, tilemap, img, *groups):
        super(Cursor, self).__init__(*groups)
        self.image = img.convert_alpha()
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
            self.point((cx, cy))
        elif event.type == pygame.MOUSEMOTION:
            cx, cy = self.tilemap.index_at(*event.pos)
            if 0 <= cx < self.tilemap.width and 0 <= cy < self.tilemap.height:
                self.rect.x = cx * self.tilemap.tile_width
                self.rect.y = cy * self.tilemap.tile_height
                self.point((cx, cy))

    def point(self, coord):
        if coord != self.coord:
            sounds.play('cursor')
            self.coord = coord
            self.rect.x = coord[0] * self.tilemap.tile_width
            self.rect.y = coord[1] * self.tilemap.tile_height

class CellHighlight(pygame.sprite.Sprite):
    def __init__(self, tilemap, *groups):
        super(CellHighlight, self).__init__(*groups)

        self.w, self.h = tilemap.width, tilemap.height
        self.tile_size = self.tw, self.th = tilemap.tile_width, tilemap.tile_height

        self.highlight_colors = dict(selected=c.SELECTED, move=c.MOVE, attack=c.ATTACK, played=c.PLAYED)
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

        self.rect = pygame.Rect((0, 0), (tilemap.px_width, tilemap.px_height))
        self.update()

    def update(self, selected=None, move=[], attack=[], played=[]):
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

        for i in range(1, self.w):
            self.image.blit(self.vertical_line, (i * self.tw - 1, 0))
        for j in range(1, self.h):
            self.image.blit(self.horizontal_line, (0, j * self.th - 1))


class Arrow(pygame.sprite.Sprite):
    def __init__(self, screen_size, image, tilesize, *groups):
        super(Arrow, self).__init__(*groups)
        self.source_image = image

        self.arrow = {}

        self.path = []
        self.source = None

        self.set_tilesize(tilesize)

        self.image = pygame.Surface(screen_size).convert_alpha()
        self.image.fill((0, 0, 0, 0))
        self.rect = pygame.Rect((0, 0), screen_size)

    def update(self, path, source=None):
        if self.path == path:
            return
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
    """Cached pathfinder"""
    def __init__(self, _map):
        self.map = _map
        self.w, self.h = self.map.w, self.map.h
        self.reset()

    def reset(self):
        self.source = None  # int tuple: dijkstra executed with this node as source
        self.target = None  # int tuple: shortest path target
        self.shortest = None  # list: shortest path output
        self.max_distance = None  # float
        self.dist = None  # dict: results of dijkstra
        self.prev = None
        self.enemies = None  # bool: treat enemies as obstacles

    def __set_source(self, source, enemies=True):
        """
        Implementation of Dijkstra's Algorithm.
        See https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm for
        reference.
        This method computes the distance of every node of the map from
        a given source node.
        """
        self.shortest = None
        self.source = source
        self.enemies = enemies

        # Unknown distance function from source to v
        self.dist = {(x, y): float('inf') for y in range(self.h) for x in range(self.w)}
        # Previous node in optimal path from source initialization
        self.prev = {(x, y): None for y in range(self.h) for x in range(self.w)}

        self.dist[source] = 0  # Distance from source to source

        # All nodes initially in Q (unvisited nodes)
        Q = [v for v in self.dist]

        source_unit = self.map[source].unit if enemies else None

        while Q:
            min_dist = self.dist[Q[0]]
            u = Q[0]

            for el in Q:
                if self.dist[el] < min_dist:
                    min_dist = self.dist[el]
                    u = el  #  Source node in first case

            Q.remove(u)

            # where v has not yet been removed from Q.
            for v in self.map.neighbors(u):
                alt = self.dist[u] + self.map[v].moves
                if alt < self.dist[v]:
                    # A shorter path to v has been found
                    if self.map.is_obstacle(v, source_unit):
                        # v is an obstacle set infinite distance (unreachable)
                        self.dist[v] = float('inf')
                        # we still want to be able to find a path
                        if not self.prev[v]:
                            self.prev[v] = [(alt, u)]
                        else:  # keep the shortest first
                            heapq.heappush(self.prev[v], (alt, u))
                    else:
                        self.dist[v] = alt
                        self.prev[v] = u

    def __set_target(self, target, max_distance=float('inf'), enemies=True):
        """
        This method sets the target node and the maximum distance. The
        computed path total cost will not exceed the maximim distance.
        The shortest path between target and source previously specified
        with __set_source is returned as a list.
        """
        self.max_distance = max_distance
        S = []
        u = self.target = target
        self.enemies = enemies

        # Construct the shortest path with a stack S
        while self.prev[u] is not None:
            if self.dist[u] <= max_distance:
                S.insert(0, u)  # Push the vertex onto the stack
            try:
                u = self.prev[u][0][1]  # get the shorter path
            except TypeError:
                u = self.prev[u]  # Traverse from target to source

        s_unit = self.map[self.source].unit if enemies else None
        for coord in reversed(S):
            unit = self.map[coord].unit
            if unit or self.map.is_obstacle(coord, s_unit):
                del S[-1]
            else:
                break

        self.shortest = S
        return S

    def shortest_path(self, source, target, max_distance=float('inf'), enemies=True):
        if self.source != source or self.enemies != enemies:
            self.__set_source(source, enemies)
            self.__set_target(target, max_distance, enemies)
        elif self.target != target or self.max_distance != max_distance or self.enemies != enemies:
            self.__set_target(target, max_distance, enemies)
        return self.shortest

    def area(self, source, max_distance, enemies=True):
        """
        Returns a list of coords
        """
        if self.source != source or self.enemies != enemies:
            self.__set_source(source, enemies)
            self.target = None
            self.shortest = None
        h, w = range(self.h), range(self.w)
        return [(i, j) for j in h for i in w if self.dist[(i, j)] <= max_distance]


def manhattan_path(source, target):
    yield source
    if source[0] < target[0]:
        yield from manhattan_path((source[0] + 1, source[1]), target)
    elif source[0] > target[0]:
        yield from manhattan_path((source[0] - 1, source[1]), target)
    elif source[1] < target[1]:
        yield from manhattan_path((source[0], source[1] + 1), target)
    elif source[1] > target[1]:
        yield from manhattan_path((source[0], source[1] - 1), target)


class Map(object):
    """
    This class should handle every aspect related to the Map in Ice Emblem.
    """

    def __init__(self, map_path):
        """
        Loads a .tmx tilemap, initializes layers like sprites, cursor,
        arrow, highlight. It also generate a cost matrix to be used by
        the Path class.
        """
        self.tilemap = tmx.load(map_path, (display.window.get_width() - 250, display.window.get_height()))
        self.tw, self.th = self.tile_size = (self.tilemap.tile_width, self.tilemap.tile_height)
        self.w, self.h = self.tilemap.width, self.tilemap.height

        self.terrains = {}
        self.sprites = tmx.SpriteLayer()

        yaml_units = utils.parse_yaml(resources.DATA_PATH / 'units.yml', unit)
        yaml_weapons = utils.parse_yaml(resources.DATA_PATH / 'weapons.yml', item)

        teams = {}

        for layer in self.tilemap.layers:
            try:  # layer can be an ObjectLayer or a Layer
                c = layer.color
                layer.visible = False  # don't draw squares
                color = (int(c[1:3], base=16), int(c[3:5], base=16),
                        int(c[5:7], base=16))  # from '#RGB' to (R,G,B)
                units = {}
                for obj in layer.objects:
                    if obj.type == 'unit':
                        units[obj.name] = yaml_units[obj.name]
                        units[obj.name].coord = obj.px // self.tw, obj.py // self.th
                        weapon = obj.properties.get('weapon', None)
                        if weapon:
                            try:
                                units[obj.name].give_weapon(yaml_weapons[weapon])
                            except KeyError:
                                logging.warning("Weapon %s not found", weapon)
                relation = layer.properties['relation']
                ai = 'AI' in layer.properties
                boss = yaml_units[layer.properties['boss']]
                def get(key):
                    v = layer.properties.get(key, None)
                    return str(resources.MUSIC_PATH / v) if v else None
                music = {'map': get('map_music'), 'battle': get('battle_music')}
            except AttributeError:
                pass
            else:
                teams[color] = unit.Team(layer.name, color, relation, ai, list(units.values()), boss, music)

        for layer in self.tilemap.layers:
            try:
                for obj in layer.objects:
                    u = yaml_units[obj.name]
                    team = teams[u.color]
                    UnitSprite(self.tile_size, obj, u, team, self.sprites)
            except (AttributeError):
                pass

        self.units_manager = unit.UnitsManager(list(teams.values()))

        for layer in reversed(self.tilemap.layers):
            try:
                for cell in layer:
                    try:
                        coord = cell.px // self.tw, cell.py // self.th
                        units = self.units_manager.get_units(coord=coord)
                        _unit = units[0] if units else None
                        if coord not in self.terrains:
                            self.terrains[coord] = Terrain(cell.tile, _unit)
                    except AttributeError:
                        pass
            except TypeError:
                pass

        cursor_layer = tmx.SpriteLayer()
        self.cursor = Cursor(self.tilemap, resources.load_image('cursor.png'), cursor_layer)

        arrow_layer = tmx.SpriteLayer()
        self.arrow = Arrow((self.tilemap.px_width, self.tilemap.px_height), resources.load_image('arrow.png'), self.tile_size, arrow_layer)

        highlight_layer = tmx.SpriteLayer()
        self.highlight = CellHighlight(self.tilemap, highlight_layer)

        self.tilemap.layers.append(highlight_layer)
        self.tilemap.layers.append(self.sprites)
        self.tilemap.layers.append(arrow_layer)
        self.tilemap.layers.append(cursor_layer)

        self.tilemap.set_focus(self.tilemap.view_w // 2, self.tilemap.view_h // 2)

        self.prev_sel = None
        self.curr_sel = None
        self.move_area = []
        self.attack_area = []

        self.move_x, self.move_y = 0, 0
        self.path = Pathfinder(self)
        self.return_path = None  # stores the path to undo a move

    @property
    def curr_unit(self):
        return self.terrains[self.curr_sel].unit

    @curr_unit.setter
    def curr_unit(self, unit):
        self.curr_sel = unit.coord

    @property
    def prev_unit(self):
        return self.terrains[self.prev_sel].unit

    @prev_unit.setter
    def prev_unit(self, unit):
        self.prev_sel = unit.coord

    def __getitem__(self, coord):
        return self.terrains[coord]

    def simulate_move(self, target):
        path = manhattan_path(self.cursor.coord, target)
        for next in path:
            self.cursor.point(next)
            yield 10

    def is_obstacle(self, coord, unit=None):
        terrain = self.terrains[coord]
        try:
            return self.units_manager.are_enemies(unit, terrain.unit)
        except AttributeError:
            if unit is None:
                return False
            unit_allowed = unit.get_allowed_terrains()
            for allowed in terrain.allowed:
                if allowed == _('any'):
                    return False
                elif allowed == _('none'):
                    return True
                if allowed in unit_allowed:
                    return False
            return True

    def check_coord(self, coord):
        x, y = coord
        return 0 <= x < self.w and 0 <= y < self.h

    def neighbors(self, coord):
        """
        Returns a list containing all existing neighbors of a node.
        coord must be a valid coordinate i.e. self.check_coord(coord).
        """
        if not self.check_coord(coord):
            raise ValueError("Invalid coordinates")
        x, y = coord
        n = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
        ret = [c for c in n if self.check_coord(c)]

        return ret

    def mouse2cell(self, cursor_coord):
        """mouse position to map index."""
        x, y = cursor_coord
        map_index = self.tilemap.index_at(x, y)
        if self.check_coord(map_index):
            return map_index
        else:
            raise ValueError('(%d:%d) Cursor out of map')

    def move_animation(self, unit, target, path=None):
        events.new_context("move")
        if not path:
            path = self.path.shortest_path(unit.coord, target, unit.movement)
        px_path = list(map(lambda x: (x[0] * self.tw, x[1] * self.th), path))
        sprite = self.find_sprite(unit=unit)

        def event_loop(_events):
            self.draw(display.window)
            pygame.display.flip()
            delta = display.tick()
            reached = sprite.move_animation(delta, px_path[0])
            if reached and len(px_path) > 1:
                px_path.pop(0)
                reached = False
            return reached

        display.tick()
        events.event_loop(event_loop, False, "move")
        return path

    def move(self, unit, new_coord):
        """
        This method moves a unit from a node to another one. If the two
        coordinates are the same no action is performed.
        """
        if unit.coord != new_coord:
            if self.get_unit(new_coord) is not None:
                raise ValueError("Destination %s is already occupied by another unit" % str(new_coord))
            self.return_path = self.move_animation(unit, new_coord)
            self.return_path.pop()
            self.return_path.reverse()
            self.return_path.append(unit.coord)
            self.terrains[unit.coord].unit = None
            self.terrains[new_coord].unit = unit
            print(_('Unit %s moved from %s to %s') % (unit.name, unit.coord, new_coord))
            unit.move(new_coord)

    def kill_unit(self, **kwargs):
        coord = kwargs['coord'] if 'coord' in kwargs else kwargs['unit'].coord
        self.terrains[coord].unit = None
        sprite = self.find_sprite(**kwargs)
        self.sprites.remove(sprite)

    def update_move_area(self):
        """
        Updates the area which will be highlighted on the map to show
        which nodes can be reached by the selected unit.
        """
        self.move_area = self.path.area(self.curr_sel, self.curr_unit.movement)

    def get_unit(self, coord):
        return self.terrains[coord].unit

    def find_sprite(self, **kwargs):
        for sprite in self.sprites:
            for attr in kwargs:
                if getattr(sprite, attr) == kwargs[attr]:
                    return sprite

    def __set_attack_area(self, coord, min_range, max_range):
        x, y = coord
        for i in range(x - max_range, x + max_range + 1):
            for j in range(y - max_range, y + max_range + 1):
                if (i, j) not in self.move_area and (i, j) not in self.attack_area:
                    if min_range <= utils.distance((x, y), (i, j)) <= max_range:
                        self.attack_area.append((i, j))

    def move_attack_area(self):
        """
        Updates the area which will be highlighted on the map to show
        how far the selected unit can move and attack.
        """
        min_range, max_range = self.curr_unit.get_weapon_range()
        self.attack_area = []
        for (x, y) in self.move_area:
            self.__set_attack_area((x, y), min_range, max_range)

    def still_attack_area(self):
        """
        Update the area which will be highlighted on the map to show
        how far the selected unit can attack with her weapon
        """
        min_range, max_range = self.curr_unit.get_weapon_range()
        self.attack_area = []
        self.move_area = []
        self.__set_attack_area(self.curr_sel, min_range, max_range)

    def update_arrow(self, target):
        if self.curr_sel and target:
            if target in self.move_area:
                path = self.path.shortest_path(self.curr_sel, target, self.curr_unit.movement)
                self.arrow.update(path, self.curr_sel)
        else:
            self.arrow.update([])

    def update_highlight(self):
        played = [u.coord for u in self.units_manager.active_team.list_played()]
        self.highlight.update(self.curr_sel, self.move_area, self.attack_area, played)

    def area(self, center, radius, hole=0):
        x, y = center
        _area = [(i, j) for i in range(x - radius, x + radius + 1)
                    for j in range(y - radius, y + radius + 1)
                    if self.check_coord((i, j))
                    and hole <= utils.distance((x, y), (i, j)) <= radius]
        return _area

    def nearby_enemies(self, unit=None):
        """
        Returns a list of near enemies that can be attacked without having to move.
        If the unit is not specified it is assumed to be the currently selected unit.
        """
        if unit is None:
            unit = self.curr_unit
        min_range, max_range = unit.get_weapon_range()
        area = self.area(unit.coord, max_range, min_range)
        nearby_list = []
        for u in area:
            c_unit = self.get_unit(u)
            if c_unit and self.units_manager.are_enemies(c_unit, unit):
                nearby_list.append(c_unit)
        return nearby_list

    def reset_selection(self):
        logging.debug('Selection reset')
        self.curr_sel = None
        self.prev_sel = None
        self.move_area = []
        self.attack_area = []
        self.arrow.update([])
        self.update_highlight()

    def can_selection_move(self):
        return (self.prev_unit is not None and not self.prev_unit.played and
            self.units_manager.active_team.is_mine(self.prev_unit) and
            self.curr_sel in self.move_area)

    def handle_click(self, event):
        ret = []
        if event.button == 1:
            try:
                coord = self.mouse2cell(event.pos)
            except ValueError:
                pass
            else:
                ret = self.select(coord)
                self.update_highlight()
        elif event.button == 3:
            self.reset_selection()
        elif event.button == 4:  # Mouse wheel up
            if self.tilemap.zoom <= 5.0:
                self.tilemap.zoom += 0.05
        elif event.button == 5:
            if self.tilemap.zoom > 0.2:
                self.tilemap.zoom -= 0.05
        return ret

    def handle_mouse_motion(self, event):
        try:
            coord = self.mouse2cell(event.pos)
            self.update_arrow(coord)
        except ValueError:
            pass
        self.cursor.update(event)

        x, y = event.pos
        border = 50
        speed = 10
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

    def handle_keyboard(self, event):
        self.cursor.update(event)
        self.update_arrow(self.cursor.coord)
        self.tilemap.set_focus(self.cursor.rect.x, self.cursor.rect.y)

        if event.key == pygame.K_SPACE:
            ret = self.select(self.cursor.coord)
            self.update_highlight()
            return ret

    def handle_videoresize(self, event):
        w, h = event.size
        viewport_size = (w - 200, h)
        self.tilemap.viewport = pygame.Rect(self.tilemap.viewport.topleft, viewport_size)
        self.tilemap.view_w, self.tilemap.view_h = viewport_size

    def draw(self, surf):
        self.sprites.update()
        fx = self.tilemap.fx + self.move_x
        fy = self.tilemap.fy + self.move_y
        min_x = self.tilemap.view_w // 2
        min_y = self.tilemap.view_h // 2
        max_x = self.tilemap.px_w_zoom - min_x
        max_y = self.tilemap.px_h_zoom - min_y

        if not min_x <= fx <= max_x:
            fx = self.tilemap.fx
            self.move_x = 0

        if not min_y <= fy <= max_y:
            fy = self.tilemap.fy
            self.move_y = 0

        self.tilemap.set_focus(fx, fy)

        self.tilemap.draw(surf)

    def select(self, coord):
        """
        Handles selection on the map. Returns whether the action menù has to be shown.
        """
        active_team = self.units_manager.active_team
        self.curr_sel = coord
        self.arrow.update([])

        if self.prev_sel is None:
            # Nothing has been previously selected
            unit = self.get_unit(coord)
            if unit is None or unit.played:
                self.move_area = []
                self.attack_area = []
            else:
                # Show the currently selected unit's move and attack area
                self.update_move_area()
                self.move_attack_area()
            self.prev_sel = self.curr_sel
        else:
            # Something has been previously selected
            if self.prev_unit is not None and self.curr_unit is not None:
                # Selected a unit two times
                if self.prev_sel == self.curr_sel and not self.prev_unit.played and active_team.is_mine(self.prev_unit):
                    # Two times on the same playable unit. Show the action menu.
                    return True
                else:
                    # Two different units
                    # show the current unit's move and attack area
                    self.prev_sel = self.curr_sel
                    self.update_move_area()
                    self.move_attack_area()
            elif self.can_selection_move():
                # Move the previously selected unit to the currently selected coordinate.
                self.move(self.prev_unit, self.curr_sel)
                return True
            else:
                # Previously something irrelevant was chosen
                self.reset_selection()
                self.curr_sel = self.prev_sel = coord

                if self.curr_unit is not None and not self.curr_unit.played:
                    # Selected a unit: show its move and attack area
                    self.update_move_area()
                    self.move_attack_area()
        return False

    def wait(self):
        self.curr_unit.played = True
        self.reset_selection()

    def prepare_attack(self, unit=None):
        if unit:
            self.curr_unit = unit
        self.move_area = []
        self.attack_area = [u.coord for u in self.nearby_enemies(unit)]
        self.update_highlight()

    def move_undo(self):
        if self.curr_sel != self.prev_sel:
            unit = self.curr_unit
            if self.return_path:
                self.move_animation(unit, self.prev_sel, self.return_path)
                self.return_path = None
            self.terrains[self.prev_sel].unit = unit
            self.terrains[self.curr_sel].unit = None
            unit.move(self.prev_sel)
        self.reset_selection()

    def is_attack_click(self, mouse_pos):
        try:
            x, y = self.mouse2cell(mouse_pos)
        except ValueError:
            return False

        return (x, y) in self.attack_area

    def is_enemy_cursor(self):
        return self.cursor.coord in self.attack_area

