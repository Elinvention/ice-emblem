"""

"""


import pygame
import logging

import utils
import colors as c
from basictypes import Point


class UnitSprite(pygame.sprite.Sprite):
    """
    Encapsulates a Unit so that it can be shown on screen as a sprite.
    """
    def __init__(self, tilemap, unit, team, *groups):
        """
        :param tilemap:
        :param unit: unit object
        :param team:
        :param groups: sprite layers
        """
        super().__init__(*groups)

        self.tilemap = tilemap
        self.unit = unit
        self.team = team
        self.zoom = -1

        self.update()

    def reposition(self):
        self.rect.left = int(self.rect.w * self.unit.coord[0])
        self.rect.top = int(self.rect.h * self.unit.coord[1])

    def move_animation(self, delta, dest):
        if self.rect.topleft == dest:
            return True
        delta /= 200
        x, y = dest
        dist = Point((x - self.rect.left, y - self.rect.top))
        if dist.x != 0 and dist.y != 0:
            dist = Point((dist.x, 0)) if abs(dist.x) < abs(dist.y) else Point((0, dist.y))
        normal = dist.normalized()
        self.rect.left += int(self.rect.w * delta) * normal.x
        self.rect.top += int(self.rect.h * delta) * normal.y

        if (normal.x == 1 and self.rect.left >= x) or (normal.x == -1 and self.rect.left <= x):
            self.rect.left = x
        if (normal.y == 1 and self.rect.top >= y) or (normal.y == -1 and self.rect.top <= y):
            self.rect.top = y

        return self.rect.topleft == dest

    def zoom_changed(self):
        size = self.tilemap.zoom_tile_size
        pos = self.tilemap.pixel_at(*self.unit.coord, False)
        self.image = pygame.Surface(size).convert_alpha()
        self.rect = pygame.Rect(pos, size)
        self.zoom = self.tilemap.zoom

    def update(self):
        if self.zoom != self.tilemap.zoom:
            self.zoom_changed()
        elif not self.unit.was_modified():
            return

        logging.debug("Sprite update: %s" % self.unit.name)

        w, h = self.rect.size
        mw, mh = img_max_size = (w, h - 5)
        mw2, mh2 = mw // 2, mh // 2

        self.image.fill((0, 0, 0, 0))
        pygame.draw.circle(self.image, self.unit.team.color, (mw2, mh2), mh2, 3)

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
