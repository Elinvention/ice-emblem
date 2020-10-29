"""

"""


import pygame

import tmx

import colors as c


class CellHighlight(pygame.sprite.Sprite):
    def __init__(self, image, rect):
        super().__init__()
        self.image = image
        self.rect = rect


class CellHighlightLayer(tmx.SpriteLayer):
    def __init__(self, tilemap: tmx.TileMap):
        super().__init__()
        self.tilemap = tilemap
        self.update()

    def cell_rect_at(self, coord):
        return pygame.Rect(self.tilemap.pixel_at(*coord, False), self.tilemap.zoom_tile_size)

    def update(self, selected=None, move=None, attack=None, played=None):
        if move is None:
            move = []
        if attack is None:
            attack = []
        if played is None:
            played = []

        self.empty()

        highlight_surfaces = {}
        for highlight, color in c.highlight.items():
            highlight_surfaces[highlight] = pygame.Surface(self.tilemap.zoom_tile_size)
            highlight_surfaces[highlight].fill(color[:3])
            highlight_surfaces[highlight].set_alpha(color[3])

        if selected is not None:
            self.add(CellHighlight(highlight_surfaces['selected'], self.cell_rect_at(selected)))

        for coord in move:
            self.add(CellHighlight(highlight_surfaces['move'], self.cell_rect_at(coord)))

        for coord in attack:
            self.add(CellHighlight(highlight_surfaces['attack'], self.cell_rect_at(coord)))

        for coord in played:
            self.add(CellHighlight(highlight_surfaces['played'], self.cell_rect_at(coord)))
