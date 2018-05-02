'''

'''


import pygame

import sounds


class Cursor(pygame.sprite.Sprite):
    def __init__(self, tilemap, img, *groups):
        super().__init__(*groups)
        self.tilemap = tilemap
        self.img = img.convert_alpha()
        self.coord = (0, 0)
        self.callbacks = []
        self.resize()

    def update(self, event=None):
        if not event:
            coord = self.tilemap.index_at(*pygame.mouse.get_pos())
            if coord:
                self.point(*coord)
        elif event.type == pygame.KEYDOWN:
            cx, cy = self.coord
            if event.key == pygame.K_UP:
                cy = (cy - 1) % self.tilemap.height
            elif event.key == pygame.K_DOWN:
                cy = (cy + 1) % self.tilemap.height
            elif event.key == pygame.K_LEFT:
                cx = (cx - 1) % self.tilemap.width
            elif event.key == pygame.K_RIGHT:
                cx = (cx + 1) % self.tilemap.width
            self.point(cx, cy)
        self.resize()

    def resize(self):
        pos = self.tilemap.pixel_at(*self.coord, False)
        self.rect = pygame.Rect(pos, self.tilemap.zoom_tile_size)
        self.image = pygame.transform.scale(self.img, self.rect.size)

    def register_cursor_moved(self, callback):
        self.callbacks.append(callback)
        callback(self.coord)

    def point(self, cx, cy):
        if (cx, cy) != self.coord:
            sounds.play('cursor')
            self.coord = (cx, cy)
            self.rect.topleft = self.tilemap.pixel_at(cx, cy, False)
            for callback in self.callbacks:
                callback(self.coord)
