"""

"""


import pygame


class Arrow(pygame.sprite.Sprite):
    def __init__(self, tilemap, image, *groups):
        super().__init__(*groups)
        self.tilemap = tilemap
        self.zoom = -1
        self.source_image = image

        self.arrow = {}

        self.path = []
        self.source = None
        self.valid = False

        self.update()

    def zoom_changed(self):
        self.rect = pygame.Rect((0, 0), self.tilemap.zoom_px_size)
        self.image = pygame.Surface(self.rect.size).convert_alpha()

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

    def update(self):
        if self.zoom != self.tilemap.zoom:
            self.zoom_changed()
        if not self.valid:
            self.image.fill((0, 0, 0, 0))
            for coord in self.path:
                img = self.get_arrow_part(coord)
                pos = self.tilemap.pixel_at(*coord, False)
                self.image.blit(img, pos)
            self.valid = True

    def set_path(self, path, source=None):
        if source is not None:
            self.source = source
            self.valid = False
        if self.path != path:
            self.path = path
            self.valid = False
        self.update()

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
