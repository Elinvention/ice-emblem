"""

"""


import pygame

import gui
import colors as c


class LifeBar(gui.GUI):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.max = kwargs.get('max', 99)
        self._value = kwargs.get('value', self.max)
        self.block_size = kwargs.get('block_size', (4, 10))
        self.blocks_per_row = kwargs.get('blocks_per_row', 30)
        self._life = pygame.Surface(self.block_size)
        self._damage = self._life.copy()
        self._life.fill(kwargs.get('life_color', c.GREEN))
        self._damage.fill(kwargs.get('damage_color', c.RED))
        self.compute_content_size()

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value
        self.invalidate()

    def compute_content_size(self):
        w = self.blocks_per_row * (self.block_size[0] + 1)
        h = (self.max // self.blocks_per_row + 1) * (self.block_size[1] + 1)
        self.content_size = w, h

    def draw(self):
        self.surface.fill((0, 0, 0, 0))
        for i in range(self.max):
            x = (i % self.blocks_per_row) * (self.block_size[0] + 1)
            y = (i // self.blocks_per_row) * (self.block_size[1] + 1)
            if i < self._value % (self.max + 1):
                self.surface.blit(self._life, (x, y))
            else:
                self.surface.blit(self._damage, (x, y))
