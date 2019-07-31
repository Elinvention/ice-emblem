"""
Show an arrow over a path.
"""


import pygame

from basictypes import Point

from typing import Tuple, List


class Arrow(pygame.sprite.Sprite):
    """
    Class used to display an arrow over the path the unit will animate over while it's moving.
    """
    def __init__(self, tilemap, image, *groups):
        """
        To make an Arrow you need to pass a :class:`map.TileMap` and a texture.
        :param tilemap: :class:`map.TileMap`
        :param image: pygame.Surface
        :param groups: pygame.sprite.Group
        """
        super().__init__(*groups)
        self.tilemap = tilemap
        self.zoom = -1
        self.source_image = image

        self.arrow = {}

        self.path = []
        self.source = None
        self.valid = False

        self.update()

    def zoom_changed(self) -> None:
        """
        Call this when the zoom was changed by the user.
        """
        self.rect = pygame.Rect((0, 0), self.tilemap.zoom_px_size)
        self.image = pygame.Surface(self.rect.size, flags=pygame.SRCALPHA)

        w, h = self.source_image.get_size()
        rw, rh = rectsize = (w // 4, h // 4)

        arrow_parts = []
        for j in range(4):
            for i in range(4):
                pos = (i * rw, j * rh)
                rect = pygame.Rect(pos, rectsize)
                img = pygame.Surface.subsurface(self.source_image, rect)
                img = pygame.transform.scale(img, self.tilemap.zoom_tile_size)
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

        self.zoom = self.tilemap.zoom
        self.valid = False

    def update(self) -> None:
        """
        Update self.image.
        """
        if self.zoom != self.tilemap.zoom:
            self.zoom_changed()
        if not self.valid:
            self.image.fill((0, 0, 0, 0))
            for coord in self.path:
                img = self.get_arrow_part(coord)
                pos = self.tilemap.pixel_at(*coord, False)
                self.image.blit(img, pos)
            self.valid = True

    def set_path(self, path: List[Tuple[int, int]], source: Tuple[int, int] = None) -> None:
        """
        Sets a new path and optionally a new source.

        If the path or the source are actually new, invalidate.
        :param path: path the arrow has to follow.
        :param source: the source node where the arrow begins.
        """
        if source in path:
            path.remove(source)
        if source is not None:
            self.source = source
            self.valid = False
        if self.path != path:
            self.path = path
            self.valid = False
        self.update()

    def add_or_remove_coord(self, coord: Tuple[int, int]) -> None:
        """
        Adds a coordinate to the path if coord is not the source and is not already contained in self.path.

        If coord is already in path removes all elements from path until the last one is coord.
        :param coord: new selected coordinate.
        """
        if self.source == coord:
            # Arrow starts where it ends
            self.path = []
        elif coord not in self.path:
            # Add to path if the new one is adjacent to the last one
            prev = self.path[-1] if self.path else self.source
            if (Point(prev) - Point(coord)).norm() == 1:
                self.path.append(coord)
        else:
            # The new one is a cell we already passed on.
            while self.path[-1] != coord:
                self.path.pop()
        self.valid = False
        self.update()

    def get_arrow_part(self, coord: Tuple[int, int]) -> pygame.Surface:
        """
        Returns the image, part of the arrow, to blit on the cell at coord.
        :param coord: map coordinates.
        :return: a pygame.Surface containing the part of the arrow to render at coord.
        """
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

        raise ValueError(f"ArrowError: {str((a, b, c))} {self.source} {self.path}")
