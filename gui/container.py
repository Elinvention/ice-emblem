"""

"""


import pygame

import display
import colors as c
from .common import GUI


class Container(GUI):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bg_color = kwargs.get('bg_color', c.MENU_BG)
        self.spacing = kwargs.get('spacing', 10)
        self.align = kwargs.get('align', 'center')
        self.compute_content_size()

    def compute_content_size(self):
        size = (0, 0)
        for i, child in enumerate(self.children):
            size = (max(size[0], child.get_width()), size[1] + child.get_height() + (self.spacing if i > 0 else 0))
        self.content_size = size
        top = self.padding[1]
        for child in self.children:
            if self.align == 'center':
                child.rect.centerx = self.padding[3] + size[0] // 2
            elif self.align == 'left':
                child.rect.left = self.padding[3]
            elif self.align == 'right':
                child.rect.right = self.padding[3] + size[0]
            child.rect.top = top
            top += child.get_height() + self.spacing
        self.rect.apply()

    def add_child(self, child):
        super().add_child(child)
        self.compute_content_size()

    def add_children(self, *children):
        super().add_children(*children)
        self.compute_content_size()

    def draw(self, surface=display.window):
        container = pygame.Surface(self.rect.size).convert_alpha()
        container.fill(self.bg_color)
        super().draw(container)
        surface.blit(container, self.rect.topleft)
