"""

"""


import pygame

import colors as c


class CellHighlight(pygame.sprite.Sprite):
    def __init__(self, tilemap, *groups):
        super().__init__(*groups)
        self.tilemap = tilemap
        self.update()

    def update(self, selected=None, move=[], attack=[], played=[]):
        highlight_colors = dict(selected=c.SELECTED, move=c.MOVE, attack=c.ATTACK, played=c.PLAYED)
        highlight_surfaces = {}
        for highlight, color in highlight_colors.items():
            highlight_surfaces[highlight] = pygame.Surface(self.tilemap.zoom_tile_size)
            highlight_surfaces[highlight].fill(color)
            highlight_surfaces[highlight].set_alpha(color[3])

        horizontal_line = pygame.Surface((self.tilemap.zoom_px_width, 2))
        horizontal_line.fill((0, 0, 0))
        horizontal_line.set_alpha(100)
        vertical_line = pygame.Surface((2, self.tilemap.zoom_px_height))
        vertical_line.fill((0, 0, 0))
        vertical_line.set_alpha(100)

        self.rect = pygame.Rect((0, 0), self.tilemap.zoom_px_size)
        self.image = pygame.Surface(self.rect.size).convert_alpha()
        self.image.fill((0, 0, 0, 0))

        blit = self.image.blit

        if selected is not None:
            blit(highlight_surfaces['selected'], self.tilemap.pixel_at(*selected, False))

        for m in move:
            blit(highlight_surfaces['move'], self.tilemap.pixel_at(*m, False))

        for a in attack:
            blit(highlight_surfaces['attack'], self.tilemap.pixel_at(*a, False))

        for p in played:
            blit(highlight_surfaces['played'], self.tilemap.pixel_at(*p, False))

        for i in range(1, self.tilemap.width):
            blit(vertical_line, (i * self.tilemap.zoom_tile_width - 1, 0))
        for j in range(1, self.tilemap.height):
            blit(horizontal_line, (0, j * self.tilemap.zoom_tile_height - 1))
