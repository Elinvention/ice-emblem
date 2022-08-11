# -*- coding: utf-8 -*-
#
#  tmx.py, Tiled TMX file parser.
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
#
# Original code under public domain:
#
# "Tiled" TMX loader/renderer and more
# Copyright 2012 Richard Jones <richard@mechanicalcat.net>
# This code is placed in the Public Domain.
#
# Changes (July 2013 by Renfred Harper):
# Ported to Python 3
# Added selective area support SpriteLayer.draw
#
# Changes (Elia Argentieri 2015):
# Tileset files have to be in the same folder of the tmx file
# Fixed: last row and last column of the map were not considered

import sys
import struct
import pygame
import os.path
import zlib
import gzip

from pygame import Rect
from xml.etree import ElementTree
from base64 import b64decode

from basictypes import Point


class Tile(object):
    def __init__(self, gid, surface, tileset):
        self.gid = gid
        self.surface = self.scaled = surface
        self.tile_width = tileset.tile_width
        self.tile_height = tileset.tile_height
        self.properties = {}
        self.zoom = 1

    @classmethod
    def from_surface(cls, surface):
        """
        Create a new Tile object straight from a pygame Surface.

        Its tile_width and tile_height will be set using the Surface dimensions.
        Its gid will be 0.
        """

        class Ts:
            tile_width, tile_height = surface.get_size()

        return cls(0, surface, Ts)

    def load_xml(self, tag):
        props = tag.find('properties')
        if props is None:
            return
        for c in props.findall('property'):
            # store additional properties.
            name = c.attrib['name']
            value = c.attrib['value']

            # TODO hax
            if value.isdigit():
                value = int(value)
            self.properties[name] = value

    def __repr__(self):
        return '<Tile %d>' % self.gid

    def set_zoom(self, zoom):
        if zoom != self.zoom:
            size = self.tile_width * zoom, self.tile_height * zoom
            self.scaled = pygame.transform.scale(self.surface, size)
            self.zoom = zoom


class Tileset(object):
    def __init__(self, name, tile_width, tile_height, firstgid):
        self.name = name
        self.tile_width = tile_width
        self.tile_height = tile_height
        self.firstgid = firstgid
        self.tiles = []
        self.properties = {}

    @classmethod
    def fromxml(cls, tag, pwd, firstgid=None):
        if 'source' in tag.attrib:
            firstgid = int(tag.attrib['firstgid'])
            with open(os.path.join(pwd, tag.attrib['source'])) as f:
                tileset = ElementTree.fromstring(f.read())
            return cls.fromxml(tileset, pwd, firstgid)

        name = tag.attrib['name']
        if firstgid is None:
            firstgid = int(tag.attrib['firstgid'])
        tile_width = int(tag.attrib['tilewidth'])
        tile_height = int(tag.attrib['tileheight'])

        tileset = cls(name, tile_width, tile_height, firstgid)

        for c in list(tag):
            if c.tag == "image":
                # create a tileset
                filename = os.path.join(pwd, c.attrib['source'])
                tileset.add_image(filename)
            elif c.tag == 'tile':
                gid = tileset.firstgid + int(c.attrib['id'])
                tileset.get_tile(gid).load_xml(c)
        return tileset

    def add_image(self, file):
        image = pygame.image.load(file).convert_alpha()
        if not image:
            sys.exit("Error creating new Tileset: file %s not found" % file)
        gid = self.firstgid
        for line in range(image.get_height() // self.tile_height):
            for column in range(image.get_width() // self.tile_width):
                pos = Rect(column * self.tile_width, line * self.tile_height,
                           self.tile_width, self.tile_height)
                self.tiles.append(Tile(gid, image.subsurface(pos), self))
                gid += 1

    def get_tile(self, gid):
        return self.tiles[gid - self.firstgid]


class Tilesets(dict):
    def add(self, tileset):
        for i, tile in enumerate(tileset.tiles):
            i += tileset.firstgid
            self[i] = tile


class Cell(object):
    """
    Layers are made of Cells (or empty space).

    Cells have some basic properties:

    x, y - the cell's index in the layer
    px, py - the cell's pixel position
    left, right, top, bottom - the cell's pixel boundaries

    Additionally the cell may have other properties which are accessed using
    standard dictionary methods:

       cell['property name']

    You may assign a new value for a property to or even delete an existing
    property from the cell - this will not affect the Tile or any other Cells
    using the Cell's Tile.
    """

    def __init__(self, x, y, px, py, tile):
        self.x, self.y = x, y
        self.px, self.py = px, py
        self.tile = tile
        self.topleft = (px, py)
        self.left = px
        self.right = px + tile.tile_width
        self.top = py
        self.bottom = py + tile.tile_height
        self.center = (px + tile.tile_width // 2, py + tile.tile_height // 2)
        self._added_properties = {}
        self._deleted_properties = set()

    def __repr__(self):
        return '<Cell %s,%s %d>' % (self.px, self.py, self.tile.gid)

    def __contains__(self, key):
        if key in self._deleted_properties:
            return False
        return key in self._added_properties or key in self.tile.properties

    def __getitem__(self, key):
        if key in self._deleted_properties:
            raise KeyError(key)
        if key in self._added_properties:
            return self._added_properties[key]
        if key in self.tile.properties:
            return self.tile.properties[key]
        raise KeyError(key)

    def __setitem__(self, key, value):
        self._added_properties[key] = value

    def __delitem__(self, key):
        self._deleted_properties.add(key)

    def intersects(self, other):
        """
        Determine whether this Cell intersects with the other rect (which has
        .x, .y, .width and .height attributes.)
        """
        if self.px + self.tile.tile_width < other.x:
            return False
        if other.x + other.width - 1 < self.px:
            return False
        if self.py + self.tile.tile_height < other.y:
            return False
        if other.y + other.height - 1 < self.py:
            return False
        return True


class LayerIterator(object):
    """
    Iterates over all the cells in a layer in column,row order.
    """

    def __init__(self, layer):
        self.layer = layer
        self.i, self.j = 0, 0

    def __next__(self):
        if self.i == self.layer.width:
            self.j += 1
            self.i = 0
        if self.j == self.layer.height:
            raise StopIteration()
        value = self.layer[self.i, self.j]
        self.i += 1
        if value is None:
            return self.__next__()
        return value


class Layer(object):
    """
    A 2d grid of Cells.

    Layers have some basic properties:

        width, height - the dimensions of the Layer in cells
        tile_width, tile_height - the dimensions of each cell
        px_width, px_height - the dimensions of the Layer in pixels
        tilesets - the tilesets used in this Layer (a Tilesets instance)
        properties - any properties set for this Layer
        cells - a dict of all the Cell instances for this Layer, keyed off
                (x, y) index.

    Additionally you may look up a cell using direct item access:

       layer[x, y] is layer.cells[x, y]

    Note that empty cells will be set to None instead of a Cell instance.
    """

    def __init__(self, name, visible, position, tmap):
        self.name = name
        self.visible = visible
        self.position = position
        self.px_width = tmap.px_width
        self.px_height = tmap.px_height
        self.tile_width = tmap.tile_width
        self.tile_height = tmap.tile_height
        self.width = tmap.width
        self.height = tmap.height
        self.tilesets = tmap.tilesets
        self.group = pygame.sprite.Group()
        self.properties = {}
        self.cells = {}
        self.view_x, self.view_y = 0, 0
        self.view_w, self.view_h = 0, 0
        self.zoom = 1

    def __repr__(self):
        return '<Layer "%s" at 0x%x>' % (self.name, id(self))

    def __getitem__(self, pos):
        return self.cells.get(pos)

    def __setitem__(self, pos, tile):
        x, y = pos
        px = x * self.tile_width
        py = y * self.tile_width
        self.cells[pos] = Cell(x, y, px, py, tile)

    def __iter__(self):
        return LayerIterator(self)

    @classmethod
    def fromxml(cls, tag, tmap):
        offset = (int(tag.attrib.get('offsetx', 0)), int(tag.attrib.get('offsety', 0)))
        layer = cls(tag.attrib['name'], int(tag.attrib.get('visible', 1)), offset, tmap)

        data_tag = tag.find('data')
        if data_tag is None:
            raise ValueError('layer %s does not contain <data>' % layer.name)

        data = data_tag.text.strip()
        data = data.encode()  # Convert to bytes
        # Decode from base 64 and decompress via zlib
        data = b64decode(data)
        if data_tag.attrib["compression"] == "gzip":
            data = gzip.decompress(data)
        elif data_tag.attrib["compression"] == "zlib":
            data = zlib.decompress(data)
        data = struct.unpack('<%di' % (len(data) / 4,), data)
        assert len(data) == layer.width * layer.height
        for i, gid in enumerate(data):
            if gid < 1:
                continue  # not set
            tile = tmap.tilesets[gid]
            x = i % layer.width
            y = i // layer.width
            layer.cells[x, y] = Cell(x, y, x * tmap.tile_width, y * tmap.tile_height, tile)

        return layer

    def update(self, dt, *args):
        pass

    def set_view(self, x, y, w, h, zoom):
        self.view_x, self.view_y = x, y
        self.view_w, self.view_h = w, h
        self.position = (x, y)
        self.zoom = zoom
        for cell in self:
            cell.tile.set_zoom(zoom)

    def draw(self, surface):
        """
        Draw this layer, limited to the current viewport, to the Surface.
        """
        ox, oy = self.view_x, self.view_y
        w, h = self.view_w, self.view_h
        tw, th = self.tile_width * self.zoom, self.tile_height * self.zoom
        for x in range(ox, ox + w + tw, tw):
            i = x // tw
            for y in range(oy, oy + h + th, th):
                j = y // th
                if (i, j) not in self.cells:
                    continue
                cell = self.cells[i, j]
                surface.blit(cell.tile.scaled, (cell.px * self.zoom - ox, cell.py * self.zoom - oy))

    def find(self, *properties):
        """
        Find all cells with the given properties set.
        """
        r = []
        for propname in properties:
            for cell in list(self.cells.values()):
                if cell and propname in cell:
                    r.append(cell)
        return r

    def match(self, **properties):
        """
        Find all cells with the given properties set to the given values.
        """
        r = []
        for propname in properties:
            for cell in list(self.cells.values()):
                if propname not in cell:
                    continue
                if properties[propname] == cell[propname]:
                    r.append(cell)
        return r

    def collide(self, rect, propname):
        """
        Find all cells the rect is touching that have the indicated property
        name set.
        """
        r = []
        for cell in self.get_in_region(rect.left, rect.top, rect.right,
                                       rect.bottom):
            if not cell.intersects(rect):
                continue
            if propname in cell:
                r.append(cell)
        return r

    def get_in_region(self, x1, y1, x2, y2):
        """
        Return cells (in [column][row]) that are within the map-space
        pixel bounds specified by the bottom-left (x1, y1) and top-right
        (x2, y2) corners.

        Return a list of Cell instances.
        """
        i1 = max(0, x1 // self.tile_width)
        j1 = max(0, y1 // self.tile_height)
        i2 = min(self.width, x2 // self.tile_width + 1)
        j2 = min(self.height, y2 // self.tile_height + 1)
        return [self.cells[i, j]
                for i in range(int(i1), int(i2))
                for j in range(int(j1), int(j2))
                if (i, j) in self.cells]

    def get_at(self, x, y):
        """
        Return the cell at the nominated (x, y) coordinate.

        Return a Cell instance or None.
        """
        i = x // self.tile_width
        j = y // self.tile_height
        return self.cells.get((i, j))

    def neighbors(self, index):
        """
        Return the indexes of the valid (ie. within the map) cardinal (ie.
        North, South, East, West) neighbors of the nominated cell index.

        Returns a list of 2-tuple indexes.
        """
        i, j = index
        n = []
        if i < self.width - 1:
            n.append((i + 1, j))
        if i > 0:
            n.append((i - 1, j))
        if j < self.height - 1:
            n.append((i, j + 1))
        if j > 0:
            n.append((i, j - 1))
        return n


class Object(object):
    """
    An object in a TMX object layer.
    name: The name of the object. An arbitrary string.
    type: The type of the object. An arbitrary string.
    x: The x coordinate of the object in pixels.
    y: The y coordinate of the object in pixels.
    width: The width of the object in pixels (defaults to 0).
    height: The height of the object in pixels (defaults to 0).
    gid: An reference to a tile (optional).
    visible: Whether the object is shown (1) or hidden (0). Defaults to 1.
    """

    def __init__(self, _type, x, y, width=0, height=0, name=None,
                 gid=None, tile=None, visible=1):
        self.type = _type
        self.px = x
        self.left = x
        if tile:
            y -= tile.tile_height
            width = tile.tile_width
            height = tile.tile_height
        self.py = y
        self.top = y
        self.width = width
        self.right = x + width
        self.height = height
        self.bottom = y + height
        self.name = name
        self.gid = gid
        self.tile = tile
        self.visible = visible
        self.properties = {}

        self._added_properties = {}
        self._deleted_properties = set()

    def __repr__(self):
        if self.tile:
            return '<Object %s,%s %s,%s tile=%d>' % (self.px, self.py, self.width, self.height, self.gid)
        else:
            return '<Object %s,%s %s,%s>' % (self.px, self.py, self.width, self.height)

    def __contains__(self, key):
        if key in self._deleted_properties:
            return False
        if key in self._added_properties:
            return True
        if key in self.properties:
            return True
        return self.tile and key in self.tile.properties

    def __getitem__(self, key):
        if key in self._deleted_properties:
            raise KeyError(key)
        if key in self._added_properties:
            return self._added_properties[key]
        if key in self.properties:
            return self.properties[key]
        if self.tile and key in self.tile.properties:
            return self.tile.properties[key]
        raise KeyError(key)

    def __setitem__(self, key, value):
        self._added_properties[key] = value

    def __delitem__(self, key):
        self._deleted_properties.add(key)

    def draw(self, surface, view_x, view_y, zoom):
        if not self.visible:
            return
        x, y = (self.px * zoom - view_x, self.py * zoom - view_y)
        if self.tile:
            surface.blit(self.tile.surface, (x, y))
        else:
            r = pygame.Rect((x, y), (self.width * zoom, self.height * zoom))
            pygame.draw.rect(surface, (255, 100, 100), r, 2)

    @classmethod
    def fromxml(cls, tag, tmap):
        if 'gid' in tag.attrib:
            gid = int(tag.attrib['gid'])
            tile = tmap.tilesets[gid]
            w = tile.tile_width
            h = tile.tile_height
        else:
            gid = None
            tile = None
            w = int(float(tag.attrib['width']))
            h = int(float(tag.attrib['height']))

        o = cls(tag.attrib.get('type', 'rect'), int(float(tag.attrib['x'])),
                int(float(tag.attrib['y'])), w, h, tag.attrib.get('name'), gid, tile,
                int(float(tag.attrib.get('visible', 1))))

        props = tag.find('properties')
        if props is None:
            return o

        for c in props.findall('property'):
            # store additional properties.
            name = c.attrib['name']
            value = c.attrib['value']

            # TODO hax
            if value.isdigit():
                value = int(value)
            o.properties[name] = value
        return o

    def intersects(self, x1, y1, x2, y2):
        if x2 < self.px:
            return False
        if y2 < self.py:
            return False
        if x1 > self.px + self.width:
            return False
        if y1 > self.py + self.height:
            return False
        return True


class ObjectLayer(object):
    """
    A layer composed of basic primitive shapes.

    Actually encompasses a TMX <objectgroup> but even the TMX documentation
    refers to them as object layers, so I will.

    ObjectLayers have some basic properties:

        position - ignored (cannot be edited in the current Tiled editor)
        name - the name of the object group.
        color - the color used to display the objects in this group.
        opacity - the opacity of the layer as a value from 0 to 1.
        visible - whether the layer is shown (1) or hidden (0).
        objects - the objects in this Layer (Object instances)
    """

    def __init__(self, name, color, objects, opacity=1.0,
                 visible=1, position=(0, 0)):
        self.name = name
        self.color = color
        self.objects = objects
        self.opacity = opacity
        self.visible = visible
        self.position = position
        self.properties = {}
        self.view_x, self.view_y = 0, 0
        self.view_w, self.view_h = 0, 0
        self.zoom = 1

    def __repr__(self):
        return '<ObjectLayer "%s" at 0x%x>' % (self.name, id(self))

    def __getitem__(self, item):
        return self.objects[item]

    @classmethod
    def fromxml(cls, tag, tmap):
        layer = cls(tag.attrib['name'], tag.attrib.get('color'), [],
                    float(tag.attrib.get('opacity', 1)),
                    int(tag.attrib.get('visible', 1)))
        for obj in tag.findall('object'):
            layer.objects.append(Object.fromxml(obj, tmap))
        for c in tag.find('properties').findall('property'):
            # store additional properties.
            name = c.attrib['name']
            value = c.attrib['value']

            # TODO hax
            if value.isdigit():
                value = int(value)
            layer.properties[name] = value
        return layer

    def update(self, dt, *args):
        pass

    def set_view(self, x, y, w, h, zoom):
        self.view_x, self.view_y = x, y
        self.view_w, self.view_h = w, h
        self.position = (x, y)
        self.zoom = zoom

    def draw(self, surface):
        """
        Draw this layer, limited to the current viewport, to the Surface.
        """
        if not self.visible:
            return
        for obj in self.objects:
            obj.draw(surface, self.view_x, self.view_y, self.zoom)

    def find(self, *properties):
        """
        Find all cells with the given properties set.
        """
        r = []
        for propname in properties:
            for obj in self.objects:
                if obj and propname in obj or propname in self.properties:
                    r.append(obj)
        return r

    def match(self, **properties):
        """
        Find all objects with the given properties set to the given values.
        """
        r = []
        for propname in properties:
            for obj in self.objects:
                if propname in obj:
                    val = obj[propname]
                elif propname in self.properties:
                    val = self.properties[propname]
                else:
                    continue
                if properties[propname] == val:
                    r.append(obj)
        return r

    def collide(self, rect, propname):
        """
        Find all objects the rect is touching that have the indicated
        property name set.
        """
        r = []
        for obj in self.get_in_region(rect.left, rect.top, rect.right, rect.bottom):
            if propname in obj or propname in self.properties:
                r.append(obj)
        return r

    def get_in_region(self, x1, y1, x2, y2):
        """
        Return objects that are within the map-space
        pixel bounds specified by the bottom-left (x1, y1) and top-right
        (x2, y2) corners.

        Return a list of Object instances.
        """
        return [obj for obj in self.objects if obj.intersects(x1, y1, x2, y2)]

    def get_at(self, x, y):
        """
        Return the first object found at the nominated (x, y) coordinate.

        Return an Object instance or None.
        """
        for obj in self.objects:
            if obj.contains(x, y):
                return obj


class SpriteLayer(pygame.sprite.AbstractGroup):
    def __init__(self):
        super().__init__()
        self.visible = True
        self.view_x, self.view_y = 0, 0
        self.view_w, self.view_h = 0, 0
        self.position = 0, 0
        self.zoom = 1

    def set_view(self, x, y, w, h, zoom):
        self.view_x, self.view_y = x, y
        self.view_w, self.view_h = w, h
        self.position = (x, y)
        self.zoom = zoom

    def draw(self, screen):
        ox, oy = self.position
        for sprite in self.sprites():
            sx, sy = sprite.rect.topleft
            # Only the sprite's defined width and height will be drawn
            area = pygame.Rect((0, 0),
                               (int(sprite.rect.width),
                                int(sprite.rect.height)))
            screen.blit(sprite.image, (sx - ox, sy - oy), area)


class Layers(list):
    def __init__(self):
        super().__init__()
        self.by_name = {}

    def add_named(self, layer, name):
        self.append(layer)
        self.by_name[name] = layer

    def __getitem__(self, item):
        if isinstance(item, int):
            return self[item]
        return self.by_name[item]


class TileMap(object):
    """
    A TileMap is a collection of Layers which contain gridded maps or sprites
    which are drawn constrained by a viewport.

    And breathe.

    TileMaps are loaded from TMX files which sets the .layers and .tilesets
    properties. After loading additional SpriteLayers may be added.

    A TileMap's rendering is restricted by a viewport which is defined by the
    size passed in at construction time and the focus set by set_focus() or
    force_focus().

    TileMaps have a number of properties:

        width, height - the dimensions of the tilemap in cells
        tile_width, tile_height - the dimensions of the cells in the map
        px_width, px_height - the dimensions of the tilemap in pixels
        properties - any properties set on the tilemap in the TMX file
        layers - all layers of this tilemap as a Layers instance
        tilesets - all tilesets of this tilemap as a Tilesets instance
        fx, fy - viewport focus point
        view_w, view_h - viewport size
        view_x, view_y - viewport offset (origin)
        viewport - a Rect instance giving the current viewport specification

    """

    def __init__(self, size, origin=(0, 0)):
        self.px_width = 0
        self.px_height = 0
        self.px_size = Point((0, 0))
        self.tile_width = 0
        self.tile_height = 0
        self.tile_size = Point((0, 0))
        self.width = 0
        self.height = 0
        self.properties = {}
        self.layers = Layers()
        self.tilesets = Tilesets()
        self.fx, self.fy = 0, 0  # viewport focus point
        self.view_w, self.view_h = size  # viewport size
        self.view_x, self.view_y = origin  # viewport offset
        self.viewport = Rect(origin, size)
        self.zoom = 1
        self.restricted_fx, self.restricted_fy = 0, 0
        self.childs_ox, self.childs_oy = 0, 0
        self.set_focus(self.view_w // 2, self.view_h // 2)

    def set_zoom(self, zoom, fx, fy):
        self.zoom = zoom
        self.set_focus(fx, fy)

    def __getattr__(self, attr):
        if attr.startswith('zoom'):
            real_attr = attr.split('_', 1)[1]
            return getattr(self, real_attr) * self.zoom
        else:
            raise AttributeError

    def update(self, dt, *args):
        for layer in self.layers:
            layer.update(dt, *args)

    def draw(self, screen):
        for layer in self.layers:
            if layer.visible:
                layer.draw(screen)
        horizontal_line = pygame.Surface((self.zoom_px_width, 2))
        horizontal_line.set_alpha(100)
        vertical_line = pygame.Surface((2, self.zoom_px_height))
        vertical_line.set_alpha(100)
        for i in range(1, self.width):
            screen.blit(vertical_line, (-self.childs_ox + i * self.zoom_tile_width - 1, -self.childs_oy))
        for j in range(1, self.height):
            screen.blit(horizontal_line, (-self.childs_ox, -self.childs_oy + j * self.zoom_tile_height - 1))

    @classmethod
    def load(cls, filename, viewport, origin=(0, 0)):
        with open(filename) as f:
            tmap = ElementTree.fromstring(f.read())

        # get most general map informations and create a surface
        tilemap = TileMap(viewport, origin)
        tilemap.width = int(tmap.attrib['width'])
        tilemap.height = int(tmap.attrib['height'])
        tilemap.tile_width = int(tmap.attrib['tilewidth'])
        tilemap.tile_height = int(tmap.attrib['tileheight'])
        tilemap.tile_size = Point((tilemap.tile_width, tilemap.tile_height))
        tilemap.px_width = tilemap.width * tilemap.tile_width
        tilemap.px_height = tilemap.height * tilemap.tile_height
        tilemap.px_size = Point((tilemap.px_width, tilemap.px_height))

        for tag in tmap.findall('tileset'):
            tilemap.tilesets.add(Tileset.fromxml(tag, os.path.dirname(filename)))

        for tag in tmap.findall('layer'):
            layer = Layer.fromxml(tag, tilemap)
            tilemap.layers.add_named(layer, layer.name)

        for tag in tmap.findall('objectgroup'):
            layer = ObjectLayer.fromxml(tag, tilemap)
            tilemap.layers.add_named(layer, layer.name)

        return tilemap

    def set_focus(self, fx, fy):
        """
        Determine the viewport based on a desired focus pixel in the
        Layer space (fx, fy) and honoring any bounding restrictions of
        child layers.

        The focus will always be shifted to ensure no child layers display
        out-of-bounds data, as defined by their dimensions px_width and px_height.
        """
        # The result is that all chilren will have their viewport set, defining
        # which of their pixels should be visible.
        fx, fy = int(fx), int(fy)
        self.fx, self.fy = fx, fy

        # get our viewport information, scaled as appropriate
        w, h = self.view_w, self.view_h
        w2, h2 = w // 2, h // 2

        px_w_zoom, px_h_zoom = self.zoom_px_width, self.zoom_px_height

        if px_w_zoom <= w:
            # this branch for centered view and no view jump when
            # crossing the center; both when world width <= view width
            restricted_fx = px_w_zoom / 2
        else:
            if (fx - w2) < 0:
                restricted_fx = w2  # hit minimum X extent
            elif (fx + w2) > px_w_zoom:
                restricted_fx = px_w_zoom - w2  # hit maximum X extent
            else:
                restricted_fx = fx
        if px_h_zoom <= h:
            # this branch for centered view and no view jump when
            # crossing the center; both when world height <= view height
            restricted_fy = px_h_zoom / 2
        else:
            if (fy - h2) < 0:
                restricted_fy = h2  # hit minimum Y extent
            elif (fy + h2) > px_h_zoom:
                restricted_fy = px_h_zoom - h2  # hit maximum Y extent
            else:
                restricted_fy = fy

        # ... and this is our focus point, center of screen
        self.restricted_fx = int(restricted_fx)
        self.restricted_fy = int(restricted_fy)

        # determine child view bounds to match that focus point
        x, y = int(restricted_fx - w2), int(restricted_fy - h2)
        self.viewport.x = x
        self.viewport.y = y

        self.childs_ox = x - self.view_x
        self.childs_oy = y - self.view_y

        for layer in self.layers:
            layer.set_view(x, y, w, h, self.zoom)

    def can_scroll(self, vx, vy):
        x_axis, y_axis = True, True
        if ((vx == 0) or (self.zoom_px_width <= self.view_w) or (self.viewport.x == 0 and vx < 0)
                or (self.viewport.x == self.zoom_px_width - self.view_w and vx > 0)):
            x_axis = False
        if ((vy == 0) or (self.zoom_px_height <= self.view_h) or (self.viewport.y == 0 and vy < 0)
                or (self.viewport.y == self.zoom_px_height - self.view_h and vy > 0)):
            y_axis = False
        return x_axis or y_axis

    def scroll(self, vx, vy):
        self.set_focus(self.restricted_fx + vx, self.restricted_fy + vy)

    def force_focus(self, fx, fy):
        """
        Force the manager to focus on a point, regardless of any managed layer
        visible boundaries.

        """
        # This calculation takes into account the scaling of this Layer (and
        # therefore also its children).
        # The result is that all chilren will have their viewport set, defining
        # which of their pixels should be visible.
        fx, fy = int(fx), int(fy)
        self.fx, self.fy = fx, fy

        # get our view size
        w = int(self.view_w)
        h = int(self.view_h)
        w2, h2 = w // 2, h // 2

        # bottom-left corner of the viewport
        x, y = fx - w2, fy - h2
        self.viewport.x = x
        self.viewport.y = y

        self.childs_ox = x - self.view_x
        self.childs_oy = y - self.view_y

        for layer in self.layers:
            layer.set_view(x, y, w, h, self.zoom)

    def pixel_from_screen(self, x, y):
        """Look up the Layer-space pixel matching the screen-space pixel.
        """
        vx, vy = self.childs_ox, self.childs_oy
        return Point((vx + x, vy + y))

    def pixel_to_screen(self, x, y):
        """
        Look up the screen-space pixel matching the Layer-space pixel.
        """
        screen_x = x - self.childs_ox
        screen_y = y - self.childs_oy
        return Point((screen_x, screen_y))

    def index_at(self, x, y):
        """
        Return the map index at the (screen-space) pixel position.
        """
        sx, sy = self.pixel_from_screen(x, y)
        cx, cy = sx // self.zoom_tile_width, sy // self.zoom_tile_height
        if 0 <= cx < self.width and 0 <= cy < self.height:
            return Point((cx, cy))

    def pixel_at(self, x, y, screen=True):
        """
        Return the top left (screen space) pixel position of map index.
        """
        sx, sy = x * self.zoom_tile_width, y * self.zoom_tile_height
        if screen:
            return self.pixel_to_screen(sx, sy)
        return Point((sx, sy))


def load(filename, viewport, origin=(0, 0)):
    return TileMap.load(filename, viewport, origin)


def main():
    pygame.init()
    screen_size = (1280, 720)
    screen = pygame.display.set_mode(screen_size)
    size = (200, 200)
    t = load(sys.argv[1], size)
    surf = pygame.Surface(size)
    pos = surf.get_rect(center=screen.get_rect().center)
    vx, vy = 0, 0
    border, speed = 50, 10
    done = False
    while not done:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                done = True
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:
                    t.zoom = min(t.zoom + 1, 5)
                elif event.button == 5:
                    t.zoom = max(t.zoom - 1, 1)
            elif event.type == pygame.MOUSEMOTION:
                x, y = event.pos
                if pos.collidepoint(event.pos):
                    if x - pos.left < border:
                        vx = -speed * (1 - ((x - pos.left) / border))
                    elif pos.right - x < border:
                        vx = speed * (1 - ((pos.right - x) / border))
                    else:
                        vx = 0
                    if y - pos.top < border:
                        vy = -speed * (1 - ((y - pos.top) / border))
                    elif pos.bottom - y < border:
                        vy = speed * (1 - ((pos.bottom - y) / border))
                    else:
                        vy = 0
                else:
                    vx = vy = 0
        t.scroll(vx, vy)
        surf.fill((255, 255, 255))
        t.draw(surf)
        screen.blit(surf, pos)
        pygame.display.flip()
        pygame.time.wait(17)
    pygame.quit()


if __name__ == '__main__':
    main()
