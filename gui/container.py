"""

"""


from enum import Enum, auto

import colors as c
import gui

from .common import Gravity


class Orientation(Enum):
    VERTICAL = auto()
    HORIZONTAL = auto()


class Container(gui.GUI):
    def __init__(self, **kwargs):
        self.bg_color = kwargs.get('bg_color', c.MENU_BG)
        self.spacing = kwargs.get('spacing', 10)
        self.gravity = kwargs.get('gravity', Gravity.TOP | Gravity.CENTER_HORIZONTAL)
        self.orientation = kwargs.get('orientation', Orientation.VERTICAL)
        super().__init__(**kwargs)
        self.compute_content_size()

    def compute_content_size(self):
        size = (0, 0)
        for i, child in enumerate(self.children):
            size = (max(size[0], child.rect.w), size[1] + child.rect.h + (self.spacing if i > 0 else 0))
        self.content_size = size
        self.reflow()

    def reflow(self):
        size = self.rect.size
        if self.orientation == Orientation.VERTICAL:
            top = self.padding[0]
            nbottoms, bottom = 0, size[1] - self.padding[2]
            ncenterys, centery = 0, size[1] // 2

            for child in self.children:
                if Gravity.FILL_HORIZONTAL in child.layout_gravity:
                    child.rect.w = size[0] - self.padding[1] - self.padding[3]
                if Gravity.FILL_VERTICAL in child.layout_gravity:
                    child.rect.h = size[1] - self.padding[0] - self.padding[2]

                if Gravity.BOTTOM in child.layout_gravity:
                    bottom -= bool(nbottoms) * (child.rect.h + self.spacing)
                    nbottoms += 1
                elif Gravity.CENTER_VERTICAL in child.layout_gravity:
                    centery -= bool(ncenterys) * (child.rect.h + self.spacing) // 2
                    ncenterys += 1

            for child in self.children:
                gravity = child.layout_gravity
                if not gravity & Gravity.VERTICAL:
                    gravity |= self.gravity & Gravity.VERTICAL
                if not gravity & Gravity.HORIZONTAL:
                    gravity |= self.gravity & Gravity.HORIZONTAL

                if gravity == Gravity.NO_GRAVITY:
                    continue

                if Gravity.TOP in gravity:
                    child.rect.top = top
                    top += child.rect.h + self.spacing
                elif Gravity.CENTER_VERTICAL in gravity:
                    child.rect.centery = centery
                    centery += child.rect.h + self.spacing
                elif Gravity.BOTTOM in gravity:
                    child.rect.bottom = bottom
                    bottom += child.rect.h + self.spacing

                if Gravity.CENTER_HORIZONTAL in gravity:
                    child.rect.centerx = size[0] // 2
                elif Gravity.LEFT in gravity:
                    child.rect.left = self.padding[3]
                elif Gravity.RIGHT in gravity:
                    child.rect.right = size[0] - self.padding[1]

        self.invalidate()

    def add_child(self, child):
        super().add_child(child)
        self.compute_content_size()

    def add_children(self, *children):
        super().add_children(*children)
        self.compute_content_size()

    def remove_child(self, child):
        super().remove_child(child)
        self.compute_content_size()

    def draw(self):
        self.surface.fill(self.bg_color)
        super().draw()
